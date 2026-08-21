from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.disaster_control import DisasterNeed, DisasterSnapshot
from app.disaster_evolution import compare_operational_periods, trace_operational_history
from app.interoperability import InteroperabilityBundle


ROOT = Path(__file__).resolve().parents[1]


class DisasterEvolutionTests(unittest.TestCase):
    def _load(self, name: str) -> DisasterSnapshot:
        return DisasterSnapshot.model_validate_json((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def _state_snapshot(self, hour: int, state: str, *, present: bool = True) -> DisasterSnapshot:
        as_of = datetime(2026, 1, 1, hour, 0, tzinfo=timezone.utc)
        needs = []
        if present:
            needs = [
                DisasterNeed(
                    need_id="route-a",
                    location_ref="synthetic-route-a",
                    category="access",
                    priority="urgent",
                    status="met" if state == "open" else "unmet",
                    source_ref=f"synthetic:route-a:{hour}",
                    verification_status="verified",
                    observed_at=as_of,
                    access_status=state,
                )
            ]
        return DisasterSnapshot(
            incident_id="synthetic-state-history",
            as_of=as_of,
            phase="response",
            interoperability=InteroperabilityBundle(
                bundle_id=f"synthetic-state-history-{hour}",
                as_of=as_of,
                resource_inventory_scope="unknown",
                service_registry_scope="unknown",
                records=[],
            ),
            needs=needs,
        )

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

    def test_access_transition_is_explicit_between_periods(self):
        result = compare_operational_periods(
            self._state_snapshot(1, "open"),
            self._state_snapshot(2, "isolated"),
        )
        self.assertEqual(len(result.access_state_transitions), 1)
        transition = result.access_state_transitions[0]
        self.assertEqual(transition.from_state, "open")
        self.assertEqual(transition.to_state, "isolated")
        self.assertEqual(transition.transition_class, "degradation")

    def test_open_isolated_open_is_recorded_as_real_reversal(self):
        result = trace_operational_history(
            [
                self._state_snapshot(1, "open"),
                self._state_snapshot(2, "isolated"),
                self._state_snapshot(3, "open"),
            ]
        )
        self.assertEqual(len(result.access_state_transitions), 2)
        self.assertEqual([x.transition_class for x in result.access_state_transitions], ["degradation", "recovery"])
        self.assertEqual(len(result.access_state_reversals), 1)
        reversal = result.access_state_reversals[0]
        self.assertEqual((reversal.initial_state, reversal.intermediate_state, reversal.final_state), ("open", "isolated", "open"))

    def test_real_aceh_sequence_preserves_open_isolated_open_history(self):
        result = trace_operational_history(
            [
                self._load("disaster_aceh_blangkejeren_state_t0_2025_12_31.json"),
                self._load("disaster_aceh_blangkejeren_state_t1_2026_01_06.json"),
                self._load("disaster_aceh_blangkejeren_state_t2_2026_01_10.json"),
            ]
        )
        self.assertEqual(result.snapshot_count, 3)
        self.assertEqual(
            [(x.from_state, x.to_state, x.transition_class) for x in result.access_state_transitions],
            [("open", "isolated", "degradation"), ("isolated", "open", "recovery")],
        )
        self.assertEqual(len(result.access_state_reversals), 1)
        reversal = result.access_state_reversals[0]
        self.assertEqual(reversal.need_id, "blangkejeren-gayo-lues-aceh-tenggara-access")
        self.assertEqual(
            (reversal.initial_state, reversal.intermediate_state, reversal.final_state),
            ("open", "isolated", "open"),
        )
        self.assertEqual(len(reversal.evidence_refs), 3)

    def test_unknown_middle_state_cannot_manufacture_reversal(self):
        result = trace_operational_history(
            [
                self._state_snapshot(1, "open"),
                self._state_snapshot(2, "unknown"),
                self._state_snapshot(3, "open"),
            ]
        )
        self.assertEqual(result.access_state_reversals, [])

    def test_missing_middle_observation_cannot_manufacture_reversal(self):
        result = trace_operational_history(
            [
                self._state_snapshot(1, "open"),
                self._state_snapshot(2, "unknown", present=False),
                self._state_snapshot(3, "open"),
            ]
        )
        self.assertEqual(result.access_state_transitions, [])
        self.assertEqual(result.access_state_reversals, [])

    def test_reverse_time_is_rejected(self):
        previous = self._load("disaster_ntt_synthetic_t1.json")
        current = self._load("disaster_ntt_synthetic.json")
        with self.assertRaises(ValueError):
            compare_operational_periods(previous, current)


if __name__ == "__main__":
    unittest.main()
