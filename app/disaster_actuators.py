from __future__ import annotations

from datetime import timedelta
from pydantic import BaseModel, Field

from app.action_intents import ActionIntent, build_wildfire_uas_intent
from app.disaster_control import DisasterAssessment, DisasterNeedCategory, DisasterSnapshot


class DisasterActuatorPlan(BaseModel):
    incident_id: str
    actuator_family: str = "wildfire_uas"
    proposed_intents: list[ActionIntent] = Field(default_factory=list)
    skipped_reasons: list[str] = Field(default_factory=list)
    safe_conclusion: str = (
        "Actuator plans contain non-binding action intents only. They do not launch, navigate, dispatch, retask or operate aircraft and do not authorize fire-suppression action."
    )


def _is_wildfire_context(snapshot: DisasterSnapshot) -> bool:
    for record in snapshot.interoperability.records:
        if record.kind.value != "hazard_observation":
            continue
        hazard = str(record.attributes.get("hazard_type", "")).lower()
        if any(token in hazard for token in ("wildfire", "forest_fire", "peat_fire", "karhutla")):
            return True
    return False


def propose_wildfire_uas_intents(
    snapshot: DisasterSnapshot,
    assessment: DisasterAssessment,
) -> DisasterActuatorPlan:
    plan = DisasterActuatorPlan(incident_id=snapshot.incident_id)
    if not _is_wildfire_context(snapshot):
        plan.skipped_reasons.append("No wildfire/forest-fire/peat-fire hazard context is established in the supplied incident evidence.")
        return plan

    needs = {need.need_id: need for need in snapshot.needs}
    emitted: set[tuple[str, str]] = set()

    for finding in assessment.findings:
        if finding.need_id is None or finding.need_id not in needs:
            continue
        need = needs[finding.need_id]

        if (
            need.category == DisasterNeedCategory.fire_suppression
            and finding.problem_class == "need_status_not_established"
            and need.priority in {"urgent", "critical"}
        ):
            key = (need.need_id, "wildfire.observe_hotspot")
            if key not in emitted:
                emitted.add(key)
                plan.proposed_intents.append(
                    build_wildfire_uas_intent(
                        intent_id=f"{snapshot.incident_id}:{need.need_id}:observe",
                        incident_id=snapshot.incident_id,
                        intent_type="wildfire.observe_hotspot",
                        priority=need.priority,
                        evidence_refs=finding.evidence_refs,
                        source_finding_class=finding.problem_class,
                        expires_at=snapshot.as_of + timedelta(hours=2),
                    )
                )

        if (
            need.category == DisasterNeedCategory.fire_suppression
            and finding.stage == "capacity"
            and finding.problem_class in {
                "fire_suppression_capacity_gap",
                "fire_suppression_observed_capacity_shortage",
            }
        ):
            key = (need.need_id, "wildfire.request_suppression_support")
            if key not in emitted:
                emitted.add(key)
                plan.proposed_intents.append(
                    build_wildfire_uas_intent(
                        intent_id=f"{snapshot.incident_id}:{need.need_id}:suppression-support",
                        incident_id=snapshot.incident_id,
                        intent_type="wildfire.request_suppression_support",
                        priority=need.priority,
                        evidence_refs=finding.evidence_refs,
                        source_finding_class=finding.problem_class,
                        expires_at=snapshot.as_of + timedelta(hours=1),
                    )
                )

    if not plan.proposed_intents:
        plan.skipped_reasons.append(
            "No current wildfire finding met the v0 actuator threshold. A fire's existence alone is not enough to propose UAS action."
        )
    return plan
