from __future__ import annotations

import unittest
from pathlib import Path

from app.governance_pulse import GovernancePulseInput, build_governance_pulse


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "governance_pulse_indonesia_wildfire_aug_2026.json"


class GovernancePulseTests(unittest.TestCase):
    def _pulse(self):
        payload = GovernancePulseInput.model_validate_json(FIXTURE.read_text(encoding="utf-8"))
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

    def test_verified_local_success_becomes_learning_candidate_without_causal_claim(self):
        pulse = self._pulse()
        topic = next(item for item in pulse.topic_pulses if item.topic == "wildfire_management")
        self.assertIn("paser-fire-extinguished", topic.learning_candidate_ids)
        self.assertIn("multi-region-fires-extinguished-no-fatalities", topic.learning_candidate_ids)
        self.assertIn("investigate why outcomes differ", topic.interpretation)
        self.assertIn("does not establish", pulse.safe_conclusion)

    def test_large_adverse_state_survives_alongside_local_improvements(self):
        pulse = self._pulse()
        adverse_ids = {signal.signal_id for signal in pulse.adverse_frontier}
        progress_ids = {signal.signal_id for signal in pulse.progress_frontier}
        self.assertIn("wildfire-national-july-burn-surge", adverse_ids)
        self.assertIn("wildfire-priority-provinces-burden", adverse_ids)
        self.assertIn("paser-fire-extinguished", progress_ids)
        self.assertTrue(adverse_ids and progress_ids)


if __name__ == "__main__":
    unittest.main()
