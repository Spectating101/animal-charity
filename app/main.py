from __future__ import annotations

import hmac
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.domain import AnimalGroup, InventoryLot, Recipient, ResolutionEvidence, SupplyBatch
from app.nocturnal_adapter import event_to_nocturnal_claim
from app.service import ReliefService

BASE = Path(__file__).resolve().parents[1]
DB_PATH = os.getenv("AFRN_DB_PATH", str(BASE / "data" / "relief.db"))
RULEPACK = os.getenv("AFRN_RULEPACK", str(BASE / "config" / "rulepacks" / "tw_dog_cat_pilot.json"))
MISSION = os.getenv("AFRN_MISSION", str(BASE / "config" / "missions" / "animal_feed_security.json"))
OPERATOR_TOKEN = os.getenv("AFRN_OPERATOR_TOKEN", "")
DEMO_MODE = os.getenv("AFRN_DEMO_MODE", "0") == "1"

app = FastAPI(
    title="Animal Feed Relief Network",
    version="0.1.0",
    description="Validation-first coordination for safe, traceable animal-feed relief.",
)
service = ReliefService(DB_PATH, RULEPACK, MISSION)


def require_operator(
    authorization: str | None = Header(default=None),
    x_actor: str | None = Header(default=None, alias="X-Actor"),
) -> str:
    if DEMO_MODE and not OPERATOR_TOKEN:
        return x_actor or "demo-operator"
    if not OPERATOR_TOKEN:
        raise HTTPException(503, "operator token not configured")
    expected = f"Bearer {OPERATOR_TOKEN}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(401, "operator authorization required")
    if not x_actor or len(x_actor.strip()) < 2:
        raise HTTPException(400, "X-Actor is required for attributable human actions")
    return x_actor.strip()


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return (BASE / "app" / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    ok, count, bad = service.store.verify_ledger()
    return {"ok": ok, "ledger_events": count, "bad_event": bad, "rulepack": service.rules.version, "mission": service.mission.version}


@app.get("/v1/summary")
def summary():
    cases = service.store.list("case")
    proposals = service.store.list("proposal")
    return {
        "recipients": len(service.store.list("recipient")),
        "animal_groups": len(service.store.list("group")),
        "supply_batches": len(service.store.list("supply")),
        "open_cases": sum(1 for c in cases if c["status"] != "resolved"),
        "resolved_cases": sum(1 for c in cases if c["status"] == "resolved"),
        "pending_proposals": sum(1 for p in proposals if p["review_state"] == "pending"),
        **service.impact_summary(),
        "mission_id": service.mission.mission_id,
        "agent_authority": sorted(service.mission.autonomous_actions),
        "human_only_authority": sorted(service.mission.human_only_actions),
        "prohibited_agent_actions": sorted(service.mission.prohibited_actions),
    }


@app.post("/v1/recipients")
def create_recipient(recipient: Recipient, actor: str = Depends(require_operator)):
    return service.save(recipient, actor=actor, event_type="recipient.recorded", source_ref=recipient.source_ref)


@app.post("/v1/groups")
def create_group(group: AnimalGroup, actor: str = Depends(require_operator)):
    return service.save(group, actor=actor, event_type="animal_group.recorded", source_ref=group.source_ref)


@app.post("/v1/inventory")
def create_inventory(item: InventoryLot, actor: str = Depends(require_operator)):
    return service.save(item, actor=actor, event_type="inventory.observed", source_ref=item.source_ref)


@app.post("/v1/supplies")
def create_supply(batch: SupplyBatch, actor: str = Depends(require_operator)):
    return service.save(batch, actor=actor, event_type="supply.observed", source_ref=batch.source_ref)


@app.get("/v1/cases")
def cases(actor: str = Depends(require_operator)):
    return service.store.list("case")


@app.get("/v1/proposals")
def proposals(actor: str = Depends(require_operator)):
    return service.store.list("proposal")


@app.post("/v1/agent/tick")
def agent_tick(
    horizon_days: float = Query(default=7, gt=0, le=30),
    target_buffer_days: float = Query(default=14, gt=0, le=60),
    actor: str = Depends(require_operator),
):
    try:
        return service.agent_tick(actor=f"public-welfare-agent:{actor}", horizon_days=horizon_days, target_buffer_days=target_buffer_days)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc


@app.post("/v1/proposals/{proposal_id}/review")
def review_proposal(proposal_id: str, approve: bool, note: str | None = None, actor: str = Depends(require_operator)):
    try:
        return service.review_proposal(proposal_id, approve=approve, actor=actor, note=note)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/v1/cases/{case_id}/resolve")
def resolve_case(case_id: str, evidence: ResolutionEvidence, actor: str = Depends(require_operator)):
    if evidence.case_id != case_id:
        raise HTTPException(400, "case id mismatch")
    evidence.actor = actor
    try:
        return service.resolve_case(evidence)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/v1/audit/events")
def audit_events(actor: str = Depends(require_operator)):
    return service.store.events()


@app.get("/v1/audit/nocturnal-export")
def nocturnal_export(actor: str = Depends(require_operator)):
    return [event_to_nocturnal_claim(event) for event in service.store.events()]
