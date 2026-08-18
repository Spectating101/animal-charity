from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.lifecycle_initiatives import (
    CandidateWelfareHost,
    ExistingWelfareService,
    LifecycleInitiativeLandscape,
    TransitionFailureEvent,
    plan_lifecycle_initiatives,
)

ROOT = Path(__file__).resolve().parents[1]


class LifecycleInitiativePlannerTests(unittest.TestCase):
    def test_synthetic_source_control_history_selects_reversible_pop_up(self):
        landscape = LifecycleInitiativeLandscape.model_validate_json(
            (ROOT / "examples" / "zhongli_sanmin_synthetic_source_control_history.json").read_text(encoding="utf-8")
        )
        plans = plan_lifecycle_initiatives(landscape)
        self.assertEqual(len(plans), 1)
        plan = plans[0]
        self.assertTrue(plan.structural_gap_established)
        self.assertEqual(plan.intervention_class, "source_control")
        self.assertEqual(plan.recommended.mode, "periodic_pop_up")
        self.assertEqual(plan.recommended.site_id, "synthetic-sanmin-community-host")
        self.assertIn("sterilization", plan.recommended.programme_label)

    def test_one_event_cannot_create_programme(self):
        now = datetime.now(timezone.utc)
        landscape = LifecycleInitiativeLandscape(
            area_id="a", area_name="A",
            events=[TransitionFailureEvent(
                event_id="e", area_id="a", subject_ref="dog", intervention_class="source_control",
                occurred_at=now, lat=25.0, lon=121.0, source_ref="test://1", synthetic=True
            )],
            candidate_hosts=[CandidateWelfareHost(
                host_id="h", name="Host", lat=25.0, lon=121.0, supported_interventions=["source_control"],
                available=True, availability_evidence_ref="test://offer", source_ref="test://host"
            )]
        )
        plan = plan_lifecycle_initiatives(landscape)[0]
        self.assertFalse(plan.structural_gap_established)
        self.assertEqual(plan.recommended.mode, "case_level_only")

    def test_existing_expandable_service_beats_new_host(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        events = [
            TransitionFailureEvent(
                event_id=f"e{i}", area_id="a", subject_ref=f"dog{i%3}", intervention_class="owner_retention",
                occurred_at=start + timedelta(days=i * 7), lat=25.0 + i * 0.0001, lon=121.0,
                source_ref=f"test://{i}", confidence=0.9, synthetic=True
            )
            for i in range(5)
        ]
        landscape = LifecycleInitiativeLandscape(
            area_id="a", area_name="A", events=events,
            existing_services=[ExistingWelfareService(
                service_id="existing", name="Existing Partner", supported_interventions=["owner_retention"],
                lat=25.0, lon=121.0, service_radius_km=8, verified=True, may_expand=True, source_ref="test://existing"
            )],
            candidate_hosts=[CandidateWelfareHost(
                host_id="new", name="New Host", lat=25.0, lon=121.0, supported_interventions=["owner_retention"],
                available=True, availability_evidence_ref="test://offer", source_ref="test://new"
            )]
        )
        plan = plan_lifecycle_initiatives(landscape)[0]
        self.assertEqual(plan.recommended.mode, "partner_extension")
        self.assertEqual(plan.recommended.site_id, "existing")

    def test_permanent_service_remains_blocked_without_longitudinal_volume(self):
        landscape = LifecycleInitiativeLandscape.model_validate_json(
            (ROOT / "examples" / "zhongli_sanmin_synthetic_source_control_history.json").read_text(encoding="utf-8")
        )
        plan = plan_lifecycle_initiatives(landscape)[0]
        permanent = [o for o in plan.alternatives if o.mode == "permanent_service"]
        # It may rank below the top-three alternatives if clearly dominated; inspect all via a fresh host-only setup if absent.
        if permanent:
            self.assertTrue(permanent[0].blockers)
        self.assertNotEqual(plan.recommended.mode, "permanent_service")


if __name__ == "__main__":
    unittest.main()
