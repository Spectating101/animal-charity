from __future__ import annotations

import unittest
from pathlib import Path

from app.public_good_control import assess_public_good_case, load_public_good_case


ROOT = Path(__file__).resolve().parents[1]


class PublicGoodCoordinationIntegrationTests(unittest.TestCase):
    def test_reef_coordination_case_uses_shared_evidence_and_domain_constitution(self):
        case = load_public_good_case(
            ROOT / "examples" / "public_good_coordination_indonesia_reef_landscape.json"
        )
        result = assess_public_good_case(case)

        self.assertEqual(result.domain.value, "public_good_coordination")
        self.assertEqual(result.constitution_ref, "config/missions/public_good_coordination.json")
        self.assertEqual(result.evidence_manifest.status, "complete")
        self.assertIn("thematic fit is not eligibility", [gate.lower() for gate in result.hard_gates])

        matches = result.domain_result["matches"]
        by_key = {
            (item["initiative_id"], item["resource_id"]): item
            for item in matches
        }
        self.assertEqual(
            by_key[("synthetic-lesser-sunda-community-reef-probe", "tfcca-cycle-1-2026")]["status"],
            "blocked",
        )
        self.assertEqual(
            by_key[("synthetic-savu-reef-positive-business-probe", "koralestari-gfcr-finance")]["status"],
            "requires_verification",
        )
        classes = [finding.problem_class for finding in result.normalized_findings]
        self.assertIn("resource_match_requires_verification", classes)
        self.assertNotIn("qualified_resource_match_candidate", classes)
        self.assertIn("does not transfer domain authority", result.non_transfer_rule.lower())


if __name__ == "__main__":
    unittest.main()
