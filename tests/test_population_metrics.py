from __future__ import annotations

import unittest
from datetime import date

from app.population_metrics import PopulationSnapshot, compare_population_snapshots


def snapshot(*, observed_on: date, coverage: float, roaming: int, intact: int, litters: int, safety: int, wildlife: int, intakes: int, reunions: int, relinquish: int, retention: int, foster: int, placements: int, returns: int):
    return PopulationSnapshot(
        area_id="a", observed_on=observed_on, observation_coverage=coverage,
        estimated_free_roaming_animals=roaming,
        estimated_intact_free_roaming_animals=intact,
        new_litters_30d=litters,
        public_safety_incidents_30d=safety,
        wildlife_conflicts_30d=wildlife,
        shelter_intakes_30d=intakes,
        verified_reunifications_30d=reunions,
        owner_relinquishments_30d=relinquish,
        verified_owner_retention_cases_30d=retention,
        verified_foster_capacity=foster,
        stable_placements_30d=placements,
        placement_returns_30d=returns,
        source_ref="test://snapshot", synthetic=True,
    )


class PopulationMetricsTests(unittest.TestCase):
    def test_improvement_is_directional_not_single_score(self):
        baseline = snapshot(observed_on=date(2026, 1, 1), coverage=0.9, roaming=100, intact=40, litters=8, safety=6, wildlife=3, intakes=30, reunions=5, relinquish=10, retention=2, foster=12, placements=14, returns=4)
        current = snapshot(observed_on=date(2026, 4, 1), coverage=0.9, roaming=80, intact=20, litters=3, safety=4, wildlife=2, intakes=22, reunions=8, relinquish=6, retention=6, foster=20, placements=21, returns=2)
        result = compare_population_snapshots(baseline, current)
        self.assertTrue(result.comparable)
        self.assertIn("estimated_free_roaming_animals", result.positive_signals)
        self.assertIn("verified_owner_retention_cases_30d", result.positive_signals)
        self.assertEqual(result.negative_signals, [])
        self.assertIn("Causal attribution", result.interpretation)

    def test_lower_observation_coverage_cannot_fake_success(self):
        baseline = snapshot(observed_on=date(2026, 1, 1), coverage=0.95, roaming=100, intact=40, litters=8, safety=6, wildlife=3, intakes=30, reunions=5, relinquish=10, retention=2, foster=12, placements=14, returns=4)
        current = snapshot(observed_on=date(2026, 4, 1), coverage=0.5, roaming=20, intact=5, litters=1, safety=1, wildlife=0, intakes=5, reunions=1, relinquish=2, retention=1, foster=5, placements=5, returns=1)
        result = compare_population_snapshots(baseline, current)
        self.assertFalse(result.comparable)
        self.assertEqual(result.positive_signals, [])
        self.assertTrue(all(d.direction == "not_interpreted" for d in result.deltas))
        self.assertIn("surveillance loss", result.interpretation)

    def test_worsened_metric_is_not_hidden_by_other_improvements(self):
        baseline = snapshot(observed_on=date(2026, 1, 1), coverage=0.9, roaming=100, intact=40, litters=8, safety=3, wildlife=3, intakes=30, reunions=5, relinquish=10, retention=2, foster=12, placements=14, returns=4)
        current = snapshot(observed_on=date(2026, 4, 1), coverage=0.9, roaming=80, intact=20, litters=3, safety=8, wildlife=2, intakes=22, reunions=8, relinquish=6, retention=6, foster=20, placements=21, returns=2)
        result = compare_population_snapshots(baseline, current)
        self.assertIn("public_safety_incidents_30d", result.negative_signals)
        self.assertIn("adverse outcome signals", result.interpretation)


if __name__ == "__main__":
    unittest.main()
