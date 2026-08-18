from __future__ import annotations

import unittest
from pathlib import Path

from app.mbg_case_study import assess_mbg_case, load_mbg_snapshot


ROOT = Path(__file__).resolve().parents[1]


class MBGCaseStudyTests(unittest.TestCase):
    def test_public_banten_context_does_not_invent_local_failure(self):
        snapshot = load_mbg_snapshot(ROOT / "examples" / "mbg_banten_public_context.json")
        result = assess_mbg_case(snapshot)
        self.assertEqual(result.findings, [])
        self.assertTrue(result.data_gaps)
        self.assertIn("insufficient", result.safe_conclusion.lower())

    def test_integrity_discrepancy_blocks_naive_capacity_story(self):
        snapshot = load_mbg_snapshot(ROOT / "examples" / "mbg_synthetic_integrity_case.json")
        result = assess_mbg_case(snapshot)
        kinds = [x.problem_class for x in result.findings]
        self.assertEqual(result.integrity_assessment.overall_status, "audit_referral_recommended")
        self.assertEqual(kinds[0], "integrity_uncertainty")
        self.assertNotIn("capacity_gap", kinds)
        self.assertIn("cause_unresolved", kinds)
        rationale = " ".join(result.findings[0].rationale).lower()
        self.assertIn("does not itself establish fraud or corruption", rationale)

    def test_reconciled_chain_allows_genuine_capacity_gap(self):
        snapshot = load_mbg_snapshot(ROOT / "examples" / "mbg_synthetic_capacity_case.json")
        result = assess_mbg_case(snapshot)
        kinds = [x.problem_class for x in result.findings]
        self.assertEqual(result.integrity_assessment.overall_status, "normal")
        self.assertIn("capacity_gap", kinds)
        capacity = next(x for x in result.findings if x.problem_class == "capacity_gap")
        self.assertTrue(capacity.structural_candidate)
        self.assertIn("adjacent SPPG", capacity.recommended_action)
        self.assertNotIn("integrity_uncertainty", kinds)

    def test_delivery_output_is_not_nutrition_outcome(self):
        snapshot = load_mbg_snapshot(ROOT / "examples" / "mbg_synthetic_capacity_case.json")
        result = assess_mbg_case(snapshot)
        self.assertIn("outcome_evidence_gap", [x.problem_class for x in result.findings])

    def test_governance_boundary_reserves_punitive_authority(self):
        snapshot = load_mbg_snapshot(ROOT / "examples" / "mbg_synthetic_integrity_case.json")
        result = assess_mbg_case(snapshot)
        self.assertIn("supplier exclusion", result.governance_boundary)
        self.assertIn("formal audit/investigation", result.governance_boundary)
        self.assertIn("public accusations", result.governance_boundary)


if __name__ == "__main__":
    unittest.main()
