from __future__ import annotations

from typing import Any

from app.animal_welfare_control import InterventionDecision
from app.welfare_outcomes import WelfareOutcome, classify_outcome


def decision_to_nocturnal_claim(decision: InterventionDecision) -> dict[str, Any]:
    """Export a proposed welfare transition as a review-required operational claim.

    No physical action is implied by this envelope. It is designed for longitudinal
    memory so later outcomes/corrections can supersede the proposal without erasing history.
    """
    return {
        "claim": f"Welfare route proposed: {decision.intervention_class} for {decision.subject_ref}",
        "matter_id": f"animal-welfare:{decision.area_id}:{decision.subject_ref}",
        "event_id": decision.decision_id,
        "substance": "welfare_intervention_proposal",
        "risk_level": "high",
        "review_required": True,
        "review_reason": "consequential_animal_welfare_decision",
        "themes": ["animal_welfare", "regional_control", decision.intervention_class],
        "evidence_refs": list(decision.evidence_refs),
        "confidence": decision.confidence,
        "synthetic": decision.synthetic,
        "public_release_allowed": False,
        "payload": {
            "current_state": decision.current_state.value,
            "intended_transition": decision.intended_transition.value if decision.intended_transition else None,
            "actuator": decision.actuator,
            "human_authority_required": decision.human_authority_required,
            "specialist_referral_only": decision.specialist_referral_only,
            "unknowns": list(decision.unknowns),
        },
    }


def outcome_to_nocturnal_claim(outcome: WelfareOutcome) -> dict[str, Any]:
    classification = classify_outcome(outcome)
    return {
        "claim": f"Welfare outcome recorded: {outcome.from_state.value} -> {outcome.to_state.value}",
        "matter_id": f"animal-welfare:subject:{outcome.subject_ref}",
        "event_id": outcome.outcome_id,
        "substance": "welfare_transition_outcome",
        "risk_level": "high",
        "review_required": True,
        "review_reason": "animal_welfare_outcome_verification",
        "themes": ["animal_welfare", "outcome", outcome.intervention_class],
        "source_url": outcome.source_ref,
        "public_release_allowed": False,
        "payload": {
            "decision_id": outcome.decision_id,
            "classification": classification,
            "verified": outcome.verified,
            "stable_days_observed": outcome.stable_days_observed,
            "serious_welfare_incident": outcome.serious_welfare_incident,
            "returned_to_bad_state": outcome.returned_to_bad_state,
            "specialist_program": outcome.specialist_program,
            "animal_showed_sustained_stress": outcome.animal_showed_sustained_stress,
        },
    }
