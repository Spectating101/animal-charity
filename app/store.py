from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from pydantic import BaseModel

from app.domain import Event


def _json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def conn(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def _init_db(self) -> None:
        with self.conn() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS records (
                    kind TEXT NOT NULL,
                    id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(kind, id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    subject_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    source_ref TEXT,
                    payload TEXT NOT NULL,
                    prev_hash TEXT,
                    event_hash TEXT NOT NULL UNIQUE
                );
                CREATE INDEX IF NOT EXISTS idx_records_kind ON records(kind);
                CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject_type, subject_id, seq);
                """
            )

    def put(self, kind: str, obj: BaseModel, *, id_field: str) -> None:
        payload = obj.model_dump(mode="json")
        obj_id = str(payload[id_field])
        now = datetime.now(timezone.utc).isoformat()
        with self.conn() as db:
            existing = db.execute(
                "SELECT created_at FROM records WHERE kind=? AND id=?", (kind, obj_id)
            ).fetchone()
            created = existing["created_at"] if existing else now
            db.execute(
                """INSERT INTO records(kind,id,payload,created_at,updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(kind,id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at""",
                (kind, obj_id, _json(payload), created, now),
            )

    def get(self, kind: str, obj_id: str) -> dict[str, Any] | None:
        with self.conn() as db:
            row = db.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, obj_id)).fetchone()
        return json.loads(row["payload"]) if row else None

    def list(self, kind: str) -> list[dict[str, Any]]:
        with self.conn() as db:
            rows = db.execute("SELECT payload FROM records WHERE kind=? ORDER BY created_at,id", (kind,)).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def append_event(self, event: Event) -> str:
        body = event.model_dump(mode="json")
        with self.conn() as db:
            prev = db.execute("SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            prev_hash = prev["event_hash"] if prev else None
            digest = hashlib.sha256((prev_hash or "GENESIS").encode() + _json(body).encode()).hexdigest()
            db.execute(
                """INSERT INTO events(event_id,event_type,subject_type,subject_id,actor,occurred_at,
                   source_ref,payload,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    event.event_id,
                    event.event_type,
                    event.subject_type,
                    event.subject_id,
                    event.actor,
                    body["occurred_at"],
                    event.source_ref,
                    _json(event.payload),
                    prev_hash,
                    digest,
                ),
            )
        return digest

    def events(self, *, subject_type: str | None = None, subject_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM events"
        args: list[Any] = []
        clauses: list[str] = []
        if subject_type:
            clauses.append("subject_type=?")
            args.append(subject_type)
        if subject_id:
            clauses.append("subject_id=?")
            args.append(subject_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY seq"
        with self.conn() as db:
            rows = db.execute(sql, args).fetchall()
        return [dict(row) | {"payload": json.loads(row["payload"])} for row in rows]

    def verify_ledger(self) -> tuple[bool, int, str | None]:
        with self.conn() as db:
            rows = db.execute("SELECT * FROM events ORDER BY seq").fetchall()
        prev_hash: str | None = None
        for index, row in enumerate(rows, start=1):
            event_body = {
                "event_id": row["event_id"],
                "event_type": row["event_type"],
                "subject_type": row["subject_type"],
                "subject_id": row["subject_id"],
                "actor": row["actor"],
                "occurred_at": row["occurred_at"],
                "source_ref": row["source_ref"],
                "payload": json.loads(row["payload"]),
            }
            expected = hashlib.sha256((prev_hash or "GENESIS").encode() + _json(event_body).encode()).hexdigest()
            if row["prev_hash"] != prev_hash or row["event_hash"] != expected:
                return False, index, row["event_id"]
            prev_hash = row["event_hash"]
        return True, len(rows), None
