from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal
import json

from pydantic import BaseModel, Field, model_validator


ROOT = Path(__file__).resolve().parents[1]
WILDFIRE_UAS_REGISTRY = ROOT / "config" / "actuators" / "wildfire_uas_intents.json"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActionIntentStatus(str, Enum):
    proposed = "proposed"
    awaiting_authority = "awaiting_authority"
    awaiting_operator_verification = "awaiting_operator_verification"
    authorized = "authorized"
    accepted_by_operator = "accepted_by_operator"
    executing = "executing"
    completed_unverified = "completed_unverified"
    outcome_verified = "outcome_verified"
    blocked = "blocked"
    cancelled = "cancelled"
    superseded = "superseded"


class ActionIntent(BaseModel):
    intent_id: str
    incident_id: str
    intent_type: str
    capability_class: str
    goal: str
    priority: Literal["watch", "urgent", "critical"]
    status: ActionIntentStatus = ActionIntentStatus.proposed
    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    required_authorization_gates: list[str] = Field(default_factory=list)
    requested_outcome_evidence: str
    source_finding_class: str | None = None
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_times(self) -> "ActionIntent":
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None:
                raise ValueError("expires_at must be timezone-aware")
            if self.expires_at < self.created_at:
                raise ValueError("expires_at cannot precede created_at")
        return self


class ActionIntentEvaluation(BaseModel):
    intent: ActionIntent
    execution_ready: bool
    missing_gates: list[str] = Field(default_factory=list)
    safe_conclusion: str


class GateState(BaseModel):
    incident_command_authority: bool = False
    airspace_operator_authorization: bool = False
    live_platform_verification: bool = False
    aviation_deconfliction: bool = False
    site_safety_review: bool = False


def _registry() -> dict[str, Any]:
    return json.loads(WILDFIRE_UAS_REGISTRY.read_text(encoding="utf-8"))


def build_wildfire_uas_intent(
    *,
    intent_id: str,
    incident_id: str,
    intent_type: str,
    priority: Literal["watch", "urgent", "critical"],
    evidence_refs: list[str],
    source_finding_class: str | None = None,
    expires_at: datetime | None = None,
) -> ActionIntent:
    registry = _registry()
    spec = registry["intent_types"].get(intent_type)
    if spec is None:
        raise ValueError(f"unsupported wildfire UAS intent_type: {intent_type}")
    return ActionIntent(
        intent_id=intent_id,
        incident_id=incident_id,
        intent_type=intent_type,
        capability_class=spec["capability_class"],
        goal=spec["allowed_goal"],
        priority=priority,
        expires_at=expires_at,
        evidence_refs=evidence_refs,
        required_authorization_gates=list(registry["hard_blocks"]),
        requested_outcome_evidence=spec["outcome_required"],
        source_finding_class=source_finding_class,
        notes=[
            "This is a non-binding governance intent, not a flight plan, dispatch, launch or payload-release command.",
            f"Execution authority: {spec['execution_authority']}.",
        ],
    )


def evaluate_wildfire_uas_intent(intent: ActionIntent, gates: GateState) -> ActionIntentEvaluation:
    if intent.expires_at is not None and intent.expires_at < utcnow():
        return ActionIntentEvaluation(
            intent=intent.model_copy(update={"status": ActionIntentStatus.blocked}),
            execution_ready=False,
            missing_gates=["intent expired; current condition and capability must be reassessed"],
            safe_conclusion="Expired intents cannot become execution-ready from stale governance state.",
        )

    gate_map = {
        "current incident-command authority": gates.incident_command_authority,
        "airspace/operator authorization": gates.airspace_operator_authorization,
        "live platform verification": gates.live_platform_verification,
        "aviation deconfliction": gates.aviation_deconfliction,
        "site-specific safety review": gates.site_safety_review,
    }
    missing = [name for name, value in gate_map.items() if not value]
    ready = not missing
    status = ActionIntentStatus.authorized if ready else ActionIntentStatus.awaiting_operator_verification
    return ActionIntentEvaluation(
        intent=intent.model_copy(update={"status": status}),
        execution_ready=ready,
        missing_gates=missing,
        safe_conclusion=(
            "Execution-ready means the external authorization gates represented here are satisfied; it is still not an autonomous flight or fire-suppression command."
            if ready
            else "The control plane may preserve the intent and missing gates, but physical execution remains blocked."
        ),
    )
