from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.coordination_control import (
    CoordinationLandscape,
    CoordinationNeed,
    PublicGoodInitiative,
    ResourceProgram,
    assess_coordination_landscape,
)
from app.refinery_coordination_adapter import (
    RefineryCoordinationBridgePacket,
    assess_refinery_coordination_bridge,
)


ROOT = Path(__file__).resolve().parents[1]
AS_OF = datetime(2026, 8, 23, 0, 0, tzinfo=timezone.utc)


class CoordinationOpportunityFreshnessTests(unittest.TestCase):
    def _initiative(self) -> PublicGoodInitiative:
        return PublicGoodInitiative(
            initiative_id="synthetic-reef-ngo",
            name="Synthetic reef NGO",
            actor_type="ngo",
            geographies=["Viet Nam"],
            themes=["coral_conservation"],
            needs=[CoordinationNeed(need_id="funding", kind="funding", priority="urgent")],
            source_ref="synthetic:reef-ngo",
            verification_status="verified",
            evidence_mode="synthetic_probe",
        )

    def test_source_backed_gfcr_page_cannot_be_open_after_2021_deadline(self):
        payload = json.loads(
            (ROOT / "examples" / "coordination_gfcr_stale_open_conflict_2026.json").read_text(encoding="utf-8")
        )
        result = assess_coordination_landscape(CoordinationLandscape.model_validate(payload))
        self.assertEqual(len(result.matches), 1)
        match = result.matches[0]
        self.assertEqual(match.status, "blocked")
        self.assertEqual(
            set(match.matched_dimensions),
            {"support_kind", "theme", "geography", "actor_type"},
        )
        self.assertIn("application_deadline", match.blocking_dimensions)
        self.assertIn("application_status_conflict", match.unresolved_dimensions)
        self.assertNotIn("application_status", match.matched_dimensions)
        self.assertTrue(any("cannot override an expired deadline" in reason for reason in match.reasons))

    def test_time_indexed_open_claim_without_status_timestamp_requires_verification(self):
        landscape = CoordinationLandscape(
            landscape_id="synthetic-untimestamped-open",
            as_of=AS_OF,
            initiatives=[self._initiative()],
            resources=[
                ResourceProgram(
                    resource_id="open-but-untimestamped",
                    name="Open but untimestamped",
                    provider="Synthetic funder",
                    resource_kind="grant",
                    support_kinds=["funding"],
                    geographies=["Viet Nam"],
                    themes=["coral_conservation"],
                    eligible_actor_types=["ngo"],
                    application_status="open",
                    source_ref="synthetic:open-but-untimestamped",
                    verification_status="verified",
                )
            ],
        )
        match = assess_coordination_landscape(landscape).matches[0]
        self.assertEqual(match.status, "requires_verification")
        self.assertEqual(match.unresolved_dimensions, ["application_status_freshness"])
        self.assertNotIn("application_status", match.matched_dimensions)

    def test_contemporaneous_open_call_with_future_deadline_can_qualify(self):
        landscape = CoordinationLandscape(
            landscape_id="synthetic-current-open",
            as_of=AS_OF,
            initiatives=[self._initiative()],
            resources=[
                ResourceProgram(
                    resource_id="current-open",
                    name="Current open call",
                    provider="Synthetic funder",
                    resource_kind="grant",
                    support_kinds=["funding"],
                    geographies=["Viet Nam"],
                    themes=["coral_conservation"],
                    eligible_actor_types=["ngo"],
                    application_status="open",
                    application_status_observed_at=datetime(2026, 8, 22, tzinfo=timezone.utc),
                    application_deadline=datetime(2026, 9, 30, tzinfo=timezone.utc),
                    source_ref="synthetic:current-open",
                    verification_status="verified",
                )
            ],
        )
        match = assess_coordination_landscape(landscape).matches[0]
        self.assertEqual(match.status, "qualified_candidate")
        self.assertIn("application_status", match.matched_dimensions)
        self.assertEqual(match.unresolved_dimensions, [])
        self.assertEqual(match.blocking_dimensions, [])

    def test_future_status_observation_cannot_leak_into_past_assessment(self):
        landscape = CoordinationLandscape(
            landscape_id="synthetic-hindsight-open",
            as_of=AS_OF,
            initiatives=[self._initiative()],
            resources=[
                ResourceProgram(
                    resource_id="future-open-observation",
                    name="Future open observation",
                    provider="Synthetic funder",
                    resource_kind="grant",
                    support_kinds=["funding"],
                    geographies=["Viet Nam"],
                    themes=["coral_conservation"],
                    eligible_actor_types=["ngo"],
                    application_status="open",
                    application_status_observed_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
                    application_deadline=datetime(2026, 9, 30, tzinfo=timezone.utc),
                    source_ref="synthetic:future-open-observation",
                    verification_status="verified",
                )
            ],
        )
        match = assess_coordination_landscape(landscape).matches[0]
        self.assertEqual(match.status, "requires_verification")
        self.assertEqual(match.unresolved_dimensions, ["application_status_hindsight"])

    def test_time_fields_fail_closed_when_timezone_naive(self):
        with self.assertRaises(ValidationError):
            ResourceProgram(
                resource_id="bad-time",
                name="Bad time",
                provider="Synthetic",
                resource_kind="grant",
                source_ref="synthetic:bad-time",
                application_deadline=datetime(2026, 9, 1),
            )
        with self.assertRaises(ValidationError):
            CoordinationLandscape(landscape_id="bad-as-of", as_of=datetime(2026, 8, 23))

    def test_refinery_bridge_forwards_as_of_into_coordination(self):
        payload = json.loads(
            (ROOT / "examples" / "refinery_coordination_bridge_indonesia_reef_2026.json").read_text(encoding="utf-8")
        )
        payload["projection"]["as_of"] = "2026-08-23T03:15:00+08:00"
        # The existing Koralestari unknown-status result remains verification-required,
        # while the bridge now has an explicit decision timestamp available for future
        # deadline/status consistency checks.
        packet = RefineryCoordinationBridgePacket.model_validate(payload)
        result = assess_refinery_coordination_bridge(packet)
        match = next(
            item
            for item in result.coordination.matches
            if item.initiative_id == "synthetic-savu-reef-positive-business-probe"
            and item.resource_id == "koralestari-gfcr-finance"
        )
        self.assertEqual(match.status, "requires_verification")
        self.assertEqual(match.unresolved_dimensions, ["application_status"])


if __name__ == "__main__":
    unittest.main()
