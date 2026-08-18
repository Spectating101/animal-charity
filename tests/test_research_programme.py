import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAMME = ROOT / "config" / "research" / "public_good_research_programme.json"


class ResearchProgrammeTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(PROGRAMME.read_text(encoding="utf-8"))

    def test_hypotheses_are_unique_and_falsifiable(self):
        hypotheses = self.data["hypotheses"]
        ids = [row["id"] for row in hypotheses]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 7)
        for row in hypotheses:
            self.assertTrue(row["question"])
            self.assertTrue(row["required_evidence"])
            self.assertTrue(row["supporting_metrics"])
            self.assertTrue(row["falsification"])

    def test_human_transfer_is_architecture_only(self):
        boundary = " ".join(self.data["claims_boundary"]).lower()
        self.assertIn("animal-specific", boundary)
        self.assertIn("human", boundary)
        h6 = next(row for row in self.data["hypotheses"] if row["id"] == "H6_public_good_control_plane")
        self.assertIn("separate human-domain constitution", h6["required_evidence"])
        self.assertIn("app/mbg_case_study.py", h6["primary_modules"])
        self.assertEqual(self.data["secondary_testbed"], "indonesia_mbg_public_nutrition_case_study")

    def test_social_integration_does_not_require_productivity(self):
        construct = self.data["constructs"]["capability_based_social_integration"].lower()
        self.assertIn("productivity is never a condition of care", construct)

    def test_access_hypothesis_requires_more_than_service_existence(self):
        h1 = next(row for row in self.data["hypotheses"] if row["id"] == "H1_access_not_scarcity")
        required = set(h1["required_evidence"])
        self.assertIn("service availability", required)
        self.assertIn("access dimensions", required)
        self.assertIn("condition observation", required)

    def test_integrity_hypothesis_cannot_promote_variance_to_corruption(self):
        h7 = next(row for row in self.data["hypotheses"] if row["id"] == "H7_integrity_before_scarcity")
        self.assertIn("app/integrity_plane.py", h7["primary_modules"])
        construct = self.data["constructs"]["integrity_chain"].lower()
        self.assertIn("does not itself establish fraud or corruption", construct)
        boundary = " ".join(self.data["claims_boundary"]).lower()
        self.assertIn("do not call an mbg variance", boundary)


if __name__ == "__main__":
    unittest.main()
