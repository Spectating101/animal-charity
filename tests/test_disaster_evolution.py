from __future__ import annotations

import unittest
from pathlib import Path

from app.disaster_control import DisasterSnapshot
from app.disaster_evolution import compare_operational_periods


ROOT = Path(__file__).resolve().parents[1]


class DisasterEvolutionTests(unittest.TestCase):
    def _load(self, name: str) -> DisasterSnapshot:
        return DisasterSnapshot.model_validate_json((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_explicit_resolution_is_distinct_from_missing_followup(self):
        result = compare_operational_periods(
            self._load("disaster_ntt_synthetic.json"),
            self._load("disaster_ntt_synthetic_t1.json"),
        )
        self.assertIn("trapped-a", result.explicitly_resolved_need_ids)
        self.assertIn("water-a", result.missing_followup_need_ids)
        self.assertNotIn("water-a", result.explicitly_resolved_need_ids)

    def test_resource_and_recommendation_state_are_revalidated_each_period(self):
        result = compare_operational_periods(
            self._load("disaster_ntt_synthetic.json"),
            self._load("disaster_ntt_synthetic_t1.json"),
        )
        self.assertIn("sar-team-a", result.lost_deployable_resource_ids)
        self.assertIn("medevac-air-a", result.newly_deployable_resource_ids)
        self.assertTrue(any("sar-team-a" in item for item in result.previous_reservations_invalidated))
        self.assertIn("isolated-medical-a", result.recommendation_stage_changes)
        self.assertEqual(result.recommendation_stage_changes["isolated-medical-a"]["from"], "access")
        self.assertEqual(result.recommendation_stage_changes["isolated-medical-a"]["to"], "route")

    def test_command_context_change_is_visible(self):
        result = compare_operational_periods(
            self._load("disaster_ntt_synthetic.json"),
            self._load("disaster_ntt_synthetic_t1.json"),
        )
        self.assertTrue(result.command_context_changed)

    def test_reverse_time_is_rejected(self):
        previous = self._load("disaster_ntt_synthetic_t1.json")
        current = self._load("disaster_ntt_synthetic.json")
        with self.assertRaises(ValueError):
            compare_operational_periods(previous, current)


if __name__ == "__main__":
    unittest.main()
