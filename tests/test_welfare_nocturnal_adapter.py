from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.animal_welfare_control import InterventionDecision, Species, WelfareState
from app.welfare_nocturnal_adapter import decision_to_nocturnal_claim, outcome_to_nocturnal_claim
from app.welfare_outcomes import WelfareOutcome


class WelfareNocturnalAdapterTests(unittest.TestCase):
    def test_decision_export_is_private_and_review_required(self):
        decision = InterventionDecision(
            decision_id="d1", area_id="a1", subject_ref="dog1", species=Species.dog,
            current_state=WelfareState.lost, problem_type="lost_or_roaming_owned", priority="urgent",
            intervention_class="reunification", actuator="reunification.owner_handoff",
            intended_transition=WelfareState.owned_stable, rationale=["test"], evidence_refs=["test://e"],
            confidence=1.0
        )
        claim = decision_to_nocturnal_claim(decision)
        self.assertTrue(claim["review_required"])
        self.assertFalse(claim["public_release_allowed"])
        self.assertEqual(claim["payload"]["actuator"], "reunification.owner_handoff")

    def test_failed_specialist_outcome_is_preserved_as_failure(self):
        outcome = WelfareOutcome(
            outcome_id="o1", decision_id="d1", subject_ref="dog1", intervention_class="specialist_referral",
            from_state=WelfareState.foster, to_state=WelfareState.specialist_program,
            occurred_at=datetime.now(timezone.utc), verified=True, source_ref="test://outcome",
            specialist_program=True, animal_showed_sustained_stress=True
        )
        claim = outcome_to_nocturnal_claim(outcome)
        self.assertEqual(claim["payload"]["classification"], "failed")
        self.assertTrue(claim["payload"]["animal_showed_sustained_stress"])
        self.assertFalse(claim["public_release_allowed"])


if __name__ == "__main__":
    unittest.main()
