from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


Species = Literal["dog", "cat"]


class ReviewState(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Recipient(BaseModel):
    recipient_id: str = Field(default_factory=lambda: new_id("rec"))
    name: str
    region: str
    status: Literal["active", "emergency_only", "suspended"] = "active"
    reliability: float = Field(default=0.5, ge=0, le=1)
    storage_classes: list[str] = Field(default_factory=lambda: ["ambient"])
    welfare_review_ref: str | None = None
    source_ref: str | None = None


class AnimalGroup(BaseModel):
    group_id: str = Field(default_factory=lambda: new_id("grp"))
    recipient_id: str
    species: Species
    count: int = Field(gt=0)
    daily_feed_kg: float = Field(gt=0)
    diet_class: str = "complete_commercial"
    restrictions: list[str] = Field(default_factory=list)
    source_ref: str | None = None


class InventoryLot(BaseModel):
    inventory_id: str = Field(default_factory=lambda: new_id("inv"))
    recipient_id: str
    group_id: str
    product_name: str
    quantity_kg: float = Field(ge=0)
    diet_class: str = "complete_commercial"
    expires_at: datetime | None = None
    source_ref: str | None = None


class SupplyBatch(BaseModel):
    batch_id: str = Field(default_factory=lambda: new_id("batch"))
    donor_name: str
    product_name: str
    quantity_kg: float = Field(gt=0)
    source_class: Literal["sealed_commercial", "prepared", "ingredient", "unknown"] = "sealed_commercial"
    species: list[Species] = Field(default_factory=lambda: ["dog", "cat"])
    diet_class: str = "complete_commercial"
    unopened: bool = True
    expires_at: datetime
    storage_class: str = "ambient"
    location: str
    source_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def expiry_must_be_timezone_aware(self) -> "SupplyBatch":
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at must include a timezone")
        return self


class NeedCase(BaseModel):
    case_id: str = Field(default_factory=lambda: new_id("case"))
    recipient_id: str
    group_id: str
    species: Species
    opened_at: datetime = Field(default_factory=utcnow)
    projected_gap_at: datetime
    coverage_days: float = Field(ge=0)
    required_kg: float = Field(gt=0)
    status: Literal["open", "proposal_ready", "approved", "resolved", "blocked"] = "open"
    urgency: Literal["watch", "urgent", "critical"] = "watch"
    source_refs: list[str] = Field(default_factory=list)


class GateResult(BaseModel):
    passed: bool
    reasons: list[str] = Field(default_factory=list)
    rulepack_version: str


class MatchProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: new_id("proposal"))
    case_id: str
    batch_id: str
    created_at: datetime = Field(default_factory=utcnow)
    proposed_kg: float = Field(gt=0)
    score: float = Field(ge=0, le=100)
    gate: GateResult
    review_state: ReviewState = ReviewState.pending
    requires_human_review: bool = True
    score_components: dict[str, float] = Field(default_factory=dict)
    score_assumptions: list[str] = Field(default_factory=list)


class ResolutionEvidence(BaseModel):
    case_id: str
    evidence_ref: str
    actor: str = "authenticated-operator"
    delivered_kg: float = Field(gt=0)
    confirmed_at: datetime = Field(default_factory=utcnow)
    note: str | None = None


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    event_type: str
    subject_type: str
    subject_id: str
    actor: str
    occurred_at: datetime = Field(default_factory=utcnow)
    source_ref: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentTickResult(BaseModel):
    opened_cases: list[str] = Field(default_factory=list)
    proposals_created: list[str] = Field(default_factory=list)
    escalations: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
