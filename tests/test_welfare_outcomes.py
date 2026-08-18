from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.animal_welfare_control import WelfareState
from app.welfare_outcomes import WelfareOutcome, classify_outcome, summarize_outcomes


class WelfareOutcomeTests(unittest.TestCase):
    def test_unverified_outcome_never_counts_as_success(self):
        outcome = WelfareOutcome(
            outcome_id="o1", decision_id="d1", subject_ref="dog1", intervention_class="reunification",
            from_state=WelfareState.lost, to_state=WelfareState.owned_stable,
            occurred_at=datetime.now(timezone.utc), verified=False, source_ref="test://unverified"
        )
        self.assertEqual(classify_outcome(outcome), "unverified")
        summary = summarize_outcomes([outcome])
        self.assertEqual(summary.verified_outcomes, 0)
        self.assertIn("cannot claim welfare impact", summary.interpretation)

    def test_verified_stable_reunification_counts_as_stable(self):
        outcome = WelfareOutcome(
            outcome_id="o2", decision_id="d2", subject_ref="dog2", intervention_class="reunification",
            from_state=WelfareState.lost, to_state=WelfareState.owned_stable,
            occurred_at=datetime.now(timezone.utc), verified=True, source_ref="test://handoff", stable_days_observed=30
        )
        self.assertEqual(classify_outcome(outcome), "stable")

    def test_return_to_bad_state_counts_as_failure_even_after_adoption(self):
        outcome = WelfareOutcome(
            outcome_id="o3", decision_id="d3", subject_ref="dog3", intervention_class="foster_to_adoption",
            from_state=WelfareState.foster, to_state=WelfareState.stable_home,
            occurred_at=datetime.now(timezone.utc), verified=True, source_ref="test://return",
            returned_to_bad_state=True
        )
        self.assertEqual(classify_outcome(outcome), "failed")

    def test_specialist_stress_is_welfare_stop_not_success(self):
        outcome = WelfareOutcome(
            outcome_id="o4", decision_id="d4", subject_ref="dog4", intervention_class="specialist_referral",
            from_state=WelfareState.foster, to_state=WelfareState.specialist_program,
            occurred_at=datetime.now(timezone.utc), verified=True, source_ref="test://specialist",
            specialist_program=True, animal_showed_sustained_stress=True
        )
        summary = summarize_outcomes([outcome])
        self.assertEqual(summary.unstable_or_failed_outcomes, 1)
        self.assertEqual(summary.specialist_welfare_stops, 1)


if __name__ == "__main__":
    unittest.main()
