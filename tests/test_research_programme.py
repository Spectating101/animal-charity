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
        self.assertGreaterEqual(len(ids), 6)
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

    def test_social_integration_does_not_require_productivity(self):
        construct = self.data["constructs"]["capability_based_social_integration"].lower()
        self.assertIn("productivity is never a condition of care", construct)

    def test_access_hypothesis_requires_more_than_service_existence(self):
        h1 = next(row for row in self.data["hypotheses"] if row["id"] == "H1_access_not_scarcity")
        required = set(h1["required_evidence"])
        self.assertIn("service availability", required)
        self.assertIn("access dimensions", required)
        self.assertIn("condition observation", required)


if __name__ == "__main__":
    unittest.main()
