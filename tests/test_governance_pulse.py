from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from app.governance_pulse import GovernancePulseInput, GovernanceSignal, build_governance_pulse


ROOT = Path(__file__).resolve().parents[1]
WILDFIRE_FIXTURE = ROOT / "examples" / "governance_pulse_indonesia_wildfire_aug_2026.json"
NTT_FIXTURE = ROOT / "examples" / "governance_pulse_ntt_earthquake_aug_2026.json"


class GovernancePulseTests(unittest.TestCase):
    def _pulse(self, fixture: Path = WILDFIRE_FIXTURE):
        payload = GovernancePulseInput.model_validate_json(fixture.read_text(encoding="utf-8"))
        return build_governance_pulse(payload)

    def test_adverse_and_progress_frontiers_are_parallel_not_netted(self):
        pulse = self._pulse()
        self.assertGreaterEqual(len(pulse.adverse_frontier), 2)
        self.assertGreaterEqual(len(pulse.progress_frontier), 2)
        self.assertIn("not positive and negative points in a net score", pulse.safe_conclusion)

    def test_response_activity_is_not_misclassified_as_progress(self):
        pulse = self._pulse()
        progress_ids = {signal.signal_id for signal in pulse.progress_frontier}
        activity_ids = {signal.signal_id for signal in pulse.response_activity}
        self.assertIn("kubu-raya-ground-air-response", activity_ids)
        self.assertNotIn("kubu-raya-ground-air-response", progress_ids)

    def test_verified_local_success_becomes_learning_and_preservation_candidate(self):
        pulse = self._pulse()
        topic = next(item for item in pulse.topic_pulses if item.topic == "wildfire_management")
        self.assertIn("paser-fire-extinguished", topic.learning_candidate_ids)
        self.assertIn("multi-region-fires-extinguished-no-fatalities", topic.learning_candidate_ids)
        self.assertIn("paser-fire-extinguished", topic.preservation_candidate_ids)
        self.assertIn("paser-fire-extinguished", topic.regression_watch_ids)
        self.assertIn("making the cases comparable", topic.interpretation)
        self.assertTrue(any("Protect the verified gain" in action for action in topic.next_review_actions))
        self.assertTrue(any("Compare learning candidates" in action for action in topic.next_review_actions))
        self.assertIn("does not establish", pulse.safe_conclusion)

    def test_current_adverse_state_survives_alongside_local_improvements(self):
        pulse = self._pulse()
        adverse_ids = {signal.signal_id for signal in pulse.adverse_frontier}
        progress_ids = {signal.signal_id for signal in pulse.progress_frontier}
        self.assertIn("wildfire-priority-provinces-burden", adverse_ids)
        self.assertIn("kalimantan-hotspots-rising-current", adverse_ids)
        self.assertIn("paser-fire-extinguished", progress_ids)
        self.assertTrue(adverse_ids and progress_ids)

    def test_july_state_reported_in_august_is_lagged_context_not_current_stress(self):
        pulse = self._pulse()
        adverse_ids = {signal.signal_id for signal in pulse.adverse_frontier}
        lagged_ids = {signal.signal_id for signal in pulse.lagged_context}
        self.assertIn("wildfire-national-july-burn-surge", lagged_ids)
        self.assertNotIn("wildfire-national-july-burn-surge", adverse_ids)
        topic = next(item for item in pulse.topic_pulses if item.topic == "wildfire_management")
        self.assertIn("wildfire-national-july-burn-surge", topic.lagged_signal_ids)
        self.assertTrue(any("lagged reports" in action for action in topic.next_review_actions))

    def test_mixed_scope_is_explicitly_not_directly_comparable(self):
        pulse = self._pulse()
        topic = next(item for item in pulse.topic_pulses if item.topic == "wildfire_management")
        self.assertIsNotNone(topic.scope_warning)
        self.assertIn("do not treat local and broader signals as direct performance comparators", topic.scope_warning)

    def test_partial_public_coverage_cannot_claim_objective_monthly_extremes(self):
        pulse = self._pulse()
        self.assertEqual(pulse.coverage_status.value, "partial")
        self.assertFalse(pulse.extreme_claim_allowed)
        self.assertIn("Do not call", pulse.ranking_note)
        self.assertTrue(pulse.known_gaps)

    def test_ntt_operational_outputs_do_not_masquerade_as_target_state_progress(self):
        pulse = self._pulse(NTT_FIXTURE)
        progress_ids = {signal.signal_id for signal in pulse.progress_frontier}
        output_ids = {signal.signal_id for signal in pulse.operational_outputs}
        activity_ids = {signal.signal_id for signal in pulse.response_activity}

        self.assertIn("larantuka-maumere-road-reconnected", progress_ids)
        self.assertIn("ntt-electricity-near-restoration", progress_ids)
        self.assertIn("reok-field-hospital-operational", output_ids)
        self.assertIn("palue-logistics-arrived", output_ids)
        self.assertNotIn("reok-field-hospital-operational", progress_ids)
        self.assertNotIn("palue-logistics-arrived", progress_ids)
        self.assertIn("ntt-large-scale-aid-flights", activity_ids)

    def test_ntt_can_hold_access_failure_and_access_restoration_in_parallel(self):
        pulse = self._pulse(NTT_FIXTURE)
        adverse_ids = {signal.signal_id for signal in pulse.adverse_frontier}
        progress_ids = {signal.signal_id for signal in pulse.progress_frontier}
        self.assertIn("ende-nagekeo-road-still-cut", adverse_ids)
        self.assertIn("larantuka-maumere-road-reconnected", progress_ids)
        self.assertIn("ntt-deaths-displacement-damage", adverse_ids)

    def test_activity_cannot_be_labeled_as_improvement(self):
        with self.assertRaises(ValueError):
            GovernanceSignal.model_validate({
                "signal_id": "bad-activity",
                "domain": "test",
                "topic": "test",
                "geography": "test",
                "observed_at": "2026-08-21T12:00:00Z",
                "source_ref": "synthetic:test",
                "direction": "improvement",
                "level": "activity",
                "condition_class": "deployment",
                "summary": "Team deployed."
            })

    def test_major_state_claim_requires_significance_and_direction_basis(self):
        with self.assertRaises(ValueError):
            GovernanceSignal.model_validate({
                "signal_id": "unjustified-major",
                "domain": "test",
                "topic": "test",
                "geography": "test",
                "observed_at": "2026-08-21T12:00:00Z",
                "source_ref": "synthetic:test",
                "direction": "adverse",
                "level": "outcome",
                "significance": "major",
                "condition_class": "test",
                "summary": "Claim without explicit basis."
            })

    def test_effective_period_rejects_reverse_time(self):
        with self.assertRaises(ValueError):
            GovernanceSignal.model_validate({
                "signal_id": "reverse-period",
                "domain": "test",
                "topic": "test",
                "geography": "test",
                "observed_at": "2026-08-21T12:00:00Z",
                "effective_period_start": "2026-08-20T12:00:00Z",
                "effective_period_end": "2026-08-19T12:00:00Z",
                "source_ref": "synthetic:test",
                "direction": "ambiguous",
                "level": "output",
                "condition_class": "test",
                "summary": "Reverse period."
            })

    def test_cli_emits_machine_readable_dual_frontier(self):
        proc = subprocess.run(
            [sys.executable, "scripts/build_governance_pulse.py", str(WILDFIRE_FIXTURE)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["pulse_id"], "indonesia-wildfire-2026-08-public-v2")
        self.assertGreaterEqual(len(payload["adverse_frontier"]), 2)
        self.assertGreaterEqual(len(payload["progress_frontier"]), 2)
        self.assertEqual(len(payload["response_activity"]), 1)
        self.assertEqual(len(payload["lagged_context"]), 1)
        self.assertFalse(payload["extreme_claim_allowed"])
        self.assertTrue(payload["topic_pulses"][0]["next_review_actions"])


if __name__ == "__main__":
    unittest.main()
