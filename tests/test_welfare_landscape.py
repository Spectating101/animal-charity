from __future__ import annotations

import unittest
from pathlib import Path

from app.welfare_landscape import (
    Capability,
    EvidenceClass,
    LandscapeSnapshot,
    Observation,
    SourceTier,
    assess_landscape,
    load_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


class WelfareLandscapeTests(unittest.TestCase):
    def test_public_capabilities_do_not_create_fake_crisis(self):
        snapshot = load_snapshot(ROOT / "examples" / "taoyuan_public_baseline.json")
        result = assess_landscape(snapshot)
        self.assertEqual(result.cases, [])
        self.assertTrue(any("No live condition evidence" in x for x in result.data_gaps))
        self.assertIn("does not justify asserting an active welfare crisis", result.safe_conclusion)

    def test_synthetic_taoyuan_incident_diagnoses_transport_not_feed(self):
        snapshot = load_snapshot(ROOT / "examples" / "taoyuan_synthetic_incident.json")
        result = assess_landscape(snapshot)
        nutrition = [x for x in result.cases if x.problem_type == "nutrition_risk"]
        self.assertEqual(len(nutrition), 1)
        case = nutrition[0]
        self.assertEqual(case.bottleneck, "last_mile_logistics")
        self.assertEqual(case.actuator, "logistics.dispatch_request")
        self.assertNotEqual(case.actuator, "afrn.feed_matcher")
        self.assertTrue(case.synthetic)

    def test_feed_matcher_only_selected_when_supply_and_transport_exist(self):
        snapshot = LandscapeSnapshot(
            area_id="test",
            area_name="Test Area",
            observations=[
                Observation(area_id="test", subject_ref="s1", signal="feed_coverage_days", value=2, unit="days", evidence_class=EvidenceClass.condition, source_ref="partner://inventory", source_tier=SourceTier.partner),
                Observation(area_id="test", subject_ref="s1", signal="compatible_supply_kg_nearby", value=40, unit="kg", evidence_class=EvidenceClass.condition, source_ref="partner://supply", source_tier=SourceTier.partner),
                Observation(area_id="test", subject_ref="s1", signal="transport_available", value=True, evidence_class=EvidenceClass.condition, source_ref="partner://transport", source_tier=SourceTier.partner),
            ],
        )
        case = assess_landscape(snapshot).cases[0]
        self.assertEqual(case.bottleneck, "coordination")
        self.assertEqual(case.actuator, "afrn.feed_matcher")

    def test_unknown_cause_requests_evidence_instead_of_guessing(self):
        snapshot = LandscapeSnapshot(
            area_id="test",
            area_name="Test Area",
            observations=[
                Observation(area_id="test", subject_ref="s1", signal="feed_coverage_days", value=0.5, unit="days", evidence_class=EvidenceClass.condition, source_ref="partner://inventory", source_tier=SourceTier.partner),
            ],
        )
        case = assess_landscape(snapshot).cases[0]
        self.assertEqual(case.severity, "critical")
        self.assertEqual(case.bottleneck, "cause_unresolved")
        self.assertEqual(case.actuator, "evidence.request")
        self.assertEqual(case.actionability, "needs_evidence")

    def test_budget_gap_selects_precise_funding_intervention(self):
        snapshot = LandscapeSnapshot(
            area_id="test",
            area_name="Test Area",
            observations=[
                Observation(area_id="test", subject_ref="s1", signal="feed_coverage_days", value=2, evidence_class=EvidenceClass.condition, source_ref="partner://inventory", source_tier=SourceTier.partner),
                Observation(area_id="test", subject_ref="s1", signal="budget_gap_twd", value=1800, unit="TWD", evidence_class=EvidenceClass.condition, source_ref="partner://invoice", source_tier=SourceTier.partner),
            ],
        )
        case = assess_landscape(snapshot).cases[0]
        self.assertEqual(case.bottleneck, "funding_procurement")
        self.assertEqual(case.actuator, "funding.precise_gap_request")
        self.assertIn("1800", case.explanation)

    def test_capacity_pressure_is_separate_problem(self):
        snapshot = LandscapeSnapshot(
            area_id="test",
            area_name="Test Area",
            observations=[
                Observation(area_id="test", subject_ref="s1", signal="shelter_capacity_ratio", value=1.05, evidence_class=EvidenceClass.condition, source_ref="partner://capacity", source_tier=SourceTier.partner),
            ],
        )
        result = assess_landscape(snapshot)
        self.assertEqual(len(result.cases), 1)
        self.assertEqual(result.cases[0].problem_type, "capacity_pressure")
        self.assertEqual(result.cases[0].actuator, "capacity.relief_plan")

    def test_rescue_delay_routes_to_authorized_escalation(self):
        snapshot = LandscapeSnapshot(
            area_id="test",
            area_name="Test Area",
            observations=[
                Observation(area_id="test", subject_ref="case-1", signal="unresolved_rescue_age_hours", value=30, unit="hours", evidence_class=EvidenceClass.condition, source_ref="partner://rescue-log", source_tier=SourceTier.partner),
            ],
            capabilities=[
                Capability(area_id="test", kind="official_rescue_channel", provider_ref="authority", source_ref="official://rescue")
            ],
        )
        case = assess_landscape(snapshot).cases[0]
        self.assertEqual(case.problem_type, "rescue_delay")
        self.assertEqual(case.severity, "critical")
        self.assertEqual(case.actuator, "rescue.escalate")


if __name__ == "__main__":
    unittest.main()
