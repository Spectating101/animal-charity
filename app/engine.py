from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain import AnimalGroup, InventoryLot, MatchProposal, NeedCase, Recipient, SupplyBatch
from app.rules import RulePack, evaluate_match


def inventory_kg(group_id: str, inventory: list[InventoryLot]) -> float:
    return sum(x.quantity_kg for x in inventory if x.group_id == group_id)


def coverage_days(group: AnimalGroup, inventory: list[InventoryLot]) -> float:
    return inventory_kg(group.group_id, inventory) / group.daily_feed_kg


def need_case_for_group(
    *,
    group: AnimalGroup,
    inventory: list[InventoryLot],
    horizon_days: float,
    target_buffer_days: float,
    now: datetime | None = None,
) -> NeedCase | None:
    now = now or datetime.now(timezone.utc)
    coverage = coverage_days(group, inventory)
    if coverage >= horizon_days:
        return None
    gap_at = now + timedelta(days=coverage)
    required_kg = max(0.01, (target_buffer_days - coverage) * group.daily_feed_kg)
    urgency = "critical" if coverage < 1 else "urgent" if coverage < 3 else "watch"
    refs = [x.source_ref for x in inventory if x.group_id == group.group_id and x.source_ref]
    return NeedCase(
        recipient_id=group.recipient_id,
        group_id=group.group_id,
        species=group.species,
        projected_gap_at=gap_at,
        coverage_days=round(coverage, 3),
        required_kg=round(required_kg, 3),
        urgency=urgency,
        source_refs=refs,
    )


def score_match(*, case: NeedCase, recipient: Recipient, batch: SupplyBatch, now: datetime) -> tuple[float, dict[str, float]]:
    # Blueprint weights: urgency 30, fit 25, logistics 15, spoilage 10,
    # recipient reliability 10, allocation fairness 10. The pilot keeps
    # logistics/fairness conservative until real route/history data exists.
    urgency = 1.0 if case.coverage_days < 1 else 0.8 if case.coverage_days < 3 else max(0.1, 1 - case.coverage_days / 14)
    fit = min(1.0, batch.quantity_kg / case.required_kg)
    logistics = 0.5
    expiry_hours = max(0.0, (batch.expires_at - now).total_seconds() / 3600)
    spoilage = max(0.0, min(1.0, 1 - expiry_hours / (30 * 24)))
    reliability = recipient.reliability
    fairness = 0.5
    components = {
        "urgency": 30 * urgency,
        "nutritional_fit": 25 * fit,
        "logistics_efficiency": 15 * logistics,
        "spoilage_risk": 10 * spoilage,
        "recipient_reliability": 10 * reliability,
        "allocation_fairness": 10 * fairness,
    }
    return round(sum(components.values()), 3), {k: round(v, 3) for k, v in components.items()}


def propose_match(
    *,
    case: NeedCase,
    recipient: Recipient,
    group: AnimalGroup,
    batch: SupplyBatch,
    rules: RulePack,
    now: datetime | None = None,
) -> MatchProposal | None:
    now = now or datetime.now(timezone.utc)
    gate = evaluate_match(recipient=recipient, group=group, batch=batch, rules=rules, now=now)
    if not gate.passed:
        return None
    score, components = score_match(case=case, recipient=recipient, batch=batch, now=now)
    return MatchProposal(
        case_id=case.case_id,
        batch_id=batch.batch_id,
        proposed_kg=min(case.required_kg, batch.quantity_kg),
        score=score,
        score_components=components,
        score_assumptions=["logistics_efficiency_unknown_default", "allocation_fairness_unknown_default"],
        gate=gate,
    )
