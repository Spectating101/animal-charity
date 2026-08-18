from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.structural_initiatives import (
    CandidateSite,
    ExistingServiceNode,
    StructuralLandscape,
    StructuralNeedEvent,
    load_structural_landscape,
    plan_structural_initiative,
)

ROOT = Path(__file__).resolve().parents[1]


class StructuralInitiativePlannerTests(unittest.TestCase):
    def test_public_taoyuan_baseline_does_not_propose_new_food_bank(self):
        landscape = load_structural_landscape(ROOT / "examples" / "taoyuan_public_structural_baseline.json")
        plan = plan_structural_initiative(landscape)
        self.assertFalse(plan.structural_gap_established)
        self.assertEqual(plan.status, "insufficient_evidence")
        self.assertEqual(plan.recommended.option_type, "case_level_only")

    def test_one_incident_never_creates_standing_infrastructure(self):
        now = datetime.now(timezone.utc)
        landscape = StructuralLandscape(
            area_id="one-case",
            area_name="One case",
            need_events=[
                StructuralNeedEvent(
                    event_id="e1",
                    subject_ref="r1",
                    problem_type="nutrition_risk",
                    bottleneck="service_access_gap",
                    occurred_at=now,
                    lat=24.91,
                    lon=121.14,
                    severity="critical",
                    estimated_gap_kg=1000,
                    source_ref="test://one",
                )
            ],
            candidate_sites=[
                CandidateSite(
                    site_id="site",
                    name="Available site",
                    lat=24.91,
                    lon=121.14,
                    source_ref="test://site",
                    available=True,
                    availability_evidence_ref="test://offer",
                )
            ],
        )
        plan = plan_structural_initiative(landscape)
        self.assertFalse(plan.structural_gap_established)
        self.assertEqual(plan.recommended.option_type, "case_level_only")

    def test_synthetic_repeated_cluster_selects_reversible_pop_up_hub(self):
        landscape = load_structural_landscape(ROOT / "examples" / "taoyuan_synthetic_structural_cluster.json")
        plan = plan_structural_initiative(landscape)
        self.assertTrue(plan.structural_gap_established)
        self.assertTrue(plan.synthetic)
        self.assertEqual(plan.recommended.option_type, "weekly_pop_up_hub")
        self.assertEqual(plan.recommended.site_id, "synthetic-yangmei-host-a")
        self.assertGreater(plan.recommended.coverage_ratio, 0.9)
        permanent = [x for x in plan.alternatives if x.option_type == "permanent_microhub"]
        self.assertTrue(permanent)
        self.assertTrue(permanent[0].blockers)

    def test_existing_extension_capability_beats_new_hub_when_close_and_reusable(self):
        base = datetime(2026, 6, 1, tzinfo=timezone.utc)
        events = []
        for i in range(5):
            events.append(
                StructuralNeedEvent(
                    event_id=f"e{i}",
                    subject_ref=f"r{i % 2}",
                    problem_type="nutrition_risk",
                    bottleneck="service_access_gap",
                    occurred_at=base + timedelta(days=i * 7),
                    lat=24.91 + i * 0.001,
                    lon=121.14 + i * 0.001,
                    estimated_gap_kg=40,
                    source_ref=f"test://{i}",
                )
            )
        landscape = StructuralLandscape(
            area_id="extension",
            area_name="Extension test",
            need_events=events,
            existing_services=[
                ExistingServiceNode(
                    service_id="partner",
                    name="Existing partner",
                    kind="food_support",
                    lat=24.912,
                    lon=121.142,
                    source_ref="test://partner",
                    verified=True,
                    may_host_extension=True,
                    service_radius_km=1,
                )
            ],
            candidate_sites=[
                CandidateSite(
                    site_id="new-site",
                    name="New site",
                    lat=24.912,
                    lon=121.142,
                    source_ref="test://new",
                    available=True,
                    availability_evidence_ref="test://offer",
                    fixed_setup_cost_twd=8000,
                    weekly_operating_cost_twd=2500,
                )
            ],
        )
        plan = plan_structural_initiative(landscape)
        self.assertTrue(plan.structural_gap_established)
        self.assertEqual(plan.recommended.option_type, "partner_extension")
        self.assertEqual(plan.recommended.site_id, "partner")

    def test_repeated_need_inside_existing_service_area_does_not_justify_new_infrastructure(self):
        base = datetime(2026, 6, 1, tzinfo=timezone.utc)
        events = [
            StructuralNeedEvent(
                event_id=f"e{i}",
                subject_ref=f"r{i % 2}",
                problem_type="nutrition_risk",
                bottleneck="funding_procurement",
                occurred_at=base + timedelta(days=i * 7),
                lat=24.91,
                lon=121.14,
                estimated_gap_kg=30,
                source_ref=f"test://{i}",
            )
            for i in range(5)
        ]
        landscape = StructuralLandscape(
            area_id="covered",
            area_name="Covered test",
            need_events=events,
            existing_services=[
                ExistingServiceNode(
                    service_id="svc",
                    name="Existing service",
                    kind="food_support",
                    lat=24.91,
                    lon=121.14,
                    source_ref="test://svc",
                    verified=True,
                    service_radius_km=8,
                )
            ],
        )
        plan = plan_structural_initiative(landscape)
        self.assertFalse(plan.structural_gap_established)
        self.assertEqual(plan.recommended.option_type, "case_level_only")


if __name__ == "__main__":
    unittest.main()
