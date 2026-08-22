from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.coordination_control import (
    CoordinationLandscape,
    CoordinationNeed,
    PublicGoodInitiative,
    ResourceProgram,
    assess_coordination_landscape,
)


ROOT = Path(__file__).resolve().parents[1]


class CoordinationControlTests(unittest.TestCase):
    def _initiative(self) -> PublicGoodInitiative:
        return PublicGoodInitiative(
            initiative_id="reef-group",
            name="Synthetic reef group",
            actor_type="community_group",
            geographies=["Lesser Sunda"],
            themes=["coral_restoration"],
            needs=[CoordinationNeed(need_id="funding", kind="funding", priority="urgent")],
            source_ref="synthetic:reef-group",
            verification_status="verified",
            evidence_mode="synthetic_probe",
        )

    def _resource(self, **updates) -> ResourceProgram:
        data = dict(
            resource_id="reef-grant",
            name="Synthetic open reef grant",
            provider="Synthetic funder",
            resource_kind="grant",
            support_kinds=["funding"],
            geographies=["Lesser Sunda"],
            themes=["coral_restoration"],
            eligible_actor_types=["community_group"],
            application_status="open",
            source_ref="synthetic:reef-grant",
            verification_status="verified",
        )
        data.update(updates)
        return ResourceProgram(**data)

    def test_full_evidenced_open_fit_is_only_qualified_candidate_not_award(self):
        result = assess_coordination_landscape(
            CoordinationLandscape(
                landscape_id="synthetic",
                initiatives=[self._initiative()],
                resources=[self._resource()],
            )
        )
        self.assertEqual(result.matches[0].status, "qualified_candidate")
        self.assertEqual(result.findings[0].problem_class, "qualified_resource_match_candidate")
        self.assertIn("not an award", result.findings[0].recommended_action.lower())
        self.assertTrue(result.findings[0].human_authority_required)

    def test_perfect_fit_closed_call_is_blocked(self):
        result = assess_coordination_landscape(
            CoordinationLandscape(
                landscape_id="closed",
                initiatives=[self._initiative()],
                resources=[self._resource(application_status="closed")],
            )
        )
        match = result.matches[0]
        self.assertEqual(match.status, "blocked")
        self.assertIn("application_status", match.blocking_dimensions)
        self.assertEqual(result.findings, [])

    def test_program_exists_without_public_application_path_requires_verification(self):
        result = assess_coordination_landscape(
            CoordinationLandscape(
                landscape_id="not-public",
                initiatives=[self._initiative()],
                resources=[self._resource(application_status="not_public")],
            )
        )
        match = result.matches[0]
        self.assertEqual(match.status, "requires_verification")
        self.assertIn("application_status", match.unresolved_dimensions)
        self.assertEqual(result.findings[0].problem_class, "resource_match_requires_verification")

    def test_missing_actor_eligibility_is_unknown_not_permission(self):
        result = assess_coordination_landscape(
            CoordinationLandscape(
                landscape_id="actor-unknown",
                initiatives=[self._initiative()],
                resources=[self._resource(eligible_actor_types=[])],
            )
        )
        self.assertEqual(result.matches[0].status, "requires_verification")
        self.assertIn("actor_type", result.matches[0].unresolved_dimensions)

    def test_reported_only_resource_cannot_be_qualified(self):
        result = assess_coordination_landscape(
            CoordinationLandscape(
                landscape_id="reported",
                initiatives=[self._initiative()],
                resources=[self._resource(verification_status="reported")],
            )
        )
        self.assertEqual(result.matches[0].status, "requires_verification")
        self.assertIn("resource_verification", result.matches[0].unresolved_dimensions)

    def test_source_backed_indonesia_reef_landscape_preserves_availability_boundary(self):
        case = json.loads(
            (ROOT / "examples" / "public_good_coordination_indonesia_reef_landscape.json").read_text(encoding="utf-8")
        )
        landscape = CoordinationLandscape.model_validate(case["payload"])
        result = assess_coordination_landscape(landscape)
        by_key = {
            (item.initiative_id, item.resource_id): item
            for item in result.matches
        }

        tfcca = by_key[("synthetic-lesser-sunda-community-reef-probe", "tfcca-cycle-1-2026")]
        self.assertEqual(tfcca.status, "blocked")
        self.assertIn("application_status", tfcca.blocking_dimensions)
        self.assertIn("theme", tfcca.matched_dimensions)
        self.assertIn("geography", tfcca.matched_dimensions)

        koralestari = by_key[("synthetic-savu-reef-positive-business-probe", "koralestari-gfcr-finance")]
        self.assertEqual(koralestari.status, "requires_verification")
        self.assertIn("application_status", koralestari.unresolved_dimensions)
        self.assertIn("theme", koralestari.matched_dimensions)
        self.assertIn("geography", koralestari.matched_dimensions)
        self.assertIn("actor_type", koralestari.matched_dimensions)

        observed = [item for item in landscape.initiatives if item.evidence_mode == "observed"]
        self.assertEqual(len(observed), 2)
        self.assertTrue(all(not item.needs for item in observed))


if __name__ == "__main__":
    unittest.main()
