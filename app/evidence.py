from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceManifestEntry(BaseModel):
    source_ref: str
    source_kind: Literal[
        "official",
        "partner",
        "professional",
        "operator",
        "public",
        "transaction",
        "sensor",
        "synthetic",
        "other",
    ] = "other"
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    sensitivity: Literal["public", "internal", "sensitive", "restricted"] = "internal"
    observed_at: datetime | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    notes: str | None = None
