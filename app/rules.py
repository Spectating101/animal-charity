from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.domain import AnimalGroup, GateResult, Recipient, SupplyBatch


@dataclass(frozen=True)
class RulePack:
    version: str
    jurisdiction: str
    allowed_species: frozenset[str]
    auto_match_source_classes: frozenset[str]
    require_unopened: bool
    minimum_expiry_hours: int
    allowed_diet_classes: frozenset[str]

    @classmethod
    def load(cls, path: str | Path) -> "RulePack":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            version=data["version"],
            jurisdiction=data["jurisdiction"],
            allowed_species=frozenset(data["allowed_species"]),
            auto_match_source_classes=frozenset(data["auto_match_source_classes"]),
            require_unopened=bool(data.get("require_unopened", True)),
            minimum_expiry_hours=int(data.get("minimum_expiry_hours", 48)),
            allowed_diet_classes=frozenset(data["allowed_diet_classes"]),
        )


def evaluate_match(
    *,
    recipient: Recipient,
    group: AnimalGroup,
    batch: SupplyBatch,
    rules: RulePack,
    now: datetime | None = None,
) -> GateResult:
    """Binary safety/eligibility gates.

    This function decides only whether a batch may be *proposed* for review. It does
    not authorize feeding, dispatch, recipient eligibility, or diet formulation.
    """
    now = now or datetime.now(timezone.utc)
    reasons: list[str] = []

    if recipient.status != "active":
        reasons.append("recipient_not_active")
    if group.species not in rules.allowed_species:
        reasons.append("species_out_of_scope")
    if batch.source_class not in rules.auto_match_source_classes:
        reasons.append("source_class_requires_professional_review")
    if rules.require_unopened and not batch.unopened:
        reasons.append("package_not_verified_unopened")
    if batch.expires_at <= now:
        reasons.append("expired")
    elif (batch.expires_at - now).total_seconds() < rules.minimum_expiry_hours * 3600:
        reasons.append("expiry_window_too_short")
    if group.species not in batch.species:
        reasons.append("species_label_mismatch")
    if batch.diet_class not in rules.allowed_diet_classes:
        reasons.append("diet_class_not_approved_for_auto_match")
    if group.diet_class != batch.diet_class:
        reasons.append("diet_class_mismatch")
    if batch.storage_class not in recipient.storage_classes:
        reasons.append("storage_infeasible")

    return GateResult(passed=not reasons, reasons=reasons, rulepack_version=rules.version)
