from __future__ import annotations

import unittest
from pathlib import Path

from pydantic import ValidationError

from app.public_good_control import PublicGoodCase, assess_public_good_case, load_public_good_case


ROOT = Path(__file__).resolve().parents[1]


class PublicGoodControlTests(unittest.TestCase):
    def test_animal_case_uses_animal_constitution_and_prevention_path(self):
        case = load_public_good_case(ROOT / "examples" / "public_good_animal_owner_retention.json")
        result = assess_public_good_case(case)
        self.assertEqual(result.domain.value, "animal_welfare")
        self.assertEqual(result.constitution_ref, "config/missions/animal_welfare_integration.json")
        self.assertEqual(result.normalized_findings[0].stage, "prevent")
        self.assertEqual(result.normalized_findings[0].domain_detail["intervention_class"], "owner_retention")
        self.assertIn("owner_support.veterinary_gap", result.normalized_findings[0].recommended_action)
        self.assertIn("decisions", result.domain_result)
        self.assertEqual(result.evidence_manifest.status, "not_supplied")

    def test_mbg_case_uses_human_constitution_and_integrity_before_capacity(self):
        case = load_public_good_case(ROOT / "examples" / "public_good_mbg_integrity.json")
        result = assess_public_good_case(case)
        self.assertEqual(result.domain.value, "mbg_public_nutrition")
        self.assertEqual(result.constitution_ref, "config/missions/mbg_public_nutrition_case_study.json")
        stages = [x.stage for x in result.normalized_findings]
        self.assertEqual(stages[0], "integrity")
        self.assertNotIn("capacity", stages)
        self.assertIn("human", result.non_transfer_rule.lower())
        self.assertIn("integrity_assessment", result.domain_result)

    def test_mbg_clean_reconciliation_allows_capacity_problem(self):
        case = load_public_good_case(ROOT / "examples" / "public_good_mbg_capacity.json")
        result = assess_public_good_case(case)
        stages = [x.stage for x in result.normalized_findings]
        self.assertIn("capacity", stages)
        self.assertNotIn("integrity", stages)
        capacity = next(x for x in result.normalized_findings if x.stage == "capacity")
        self.assertTrue(capacity.structural_candidate)
        self.assertIn("adjacent SPPG", capacity.recommended_action)

    def test_evidence_manifest_reports_complete_and_incomplete_coverage(self):
        base = load_public_good_case(ROOT / "examples" / "public_good_animal_owner_retention.json").model_dump(mode="json")
        base["evidence_manifest"] = [
            {
                "source_ref": "synthetic:owner-interview",
                "source_kind": "synthetic",
                "verification_status": "corroborated",
                "sensitivity": "internal"
            },
            {
                "source_ref": "synthetic:verified-case-note",
                "source_kind": "synthetic",
                "verification_status": "verified",
                "sensitivity": "internal"
            }
        ]
        complete = assess_public_good_case(PublicGoodCase.model_validate(base))
        self.assertEqual(complete.evidence_manifest.status, "complete")
        self.assertEqual(complete.evidence_manifest.missing_refs, [])
        self.assertEqual(complete.evidence_manifest.verified_ref_count, 1)

        base["evidence_manifest"] = base["evidence_manifest"][:1]
        incomplete = assess_public_good_case(PublicGoodCase.model_validate(base))
        self.assertEqual(incomplete.evidence_manifest.status, "incomplete")
        self.assertIn("synthetic:verified-case-note", incomplete.evidence_manifest.missing_refs)
        self.assertTrue(any("Evidence manifest" in gap for gap in incomplete.data_gaps))

    def test_shared_loop_is_shared_but_domain_rules_are_not(self):
        animal = assess_public_good_case(load_public_good_case(ROOT / "examples" / "public_good_animal_owner_retention.json"))
        mbg = assess_public_good_case(load_public_good_case(ROOT / "examples" / "public_good_mbg_integrity.json"))
        self.assertEqual(animal.shared_loop, mbg.shared_loop)
        self.assertNotEqual(animal.constitution_ref, mbg.constitution_ref)
        self.assertNotEqual(animal.unit_of_concern, mbg.unit_of_concern)
        self.assertNotEqual(animal.hard_gates, mbg.hard_gates)

    def test_unknown_domain_fails_closed(self):
        with self.assertRaises(ValidationError):
            PublicGoodCase.model_validate({"case_id": "bad", "domain": "generic_people", "payload": {}})

    def test_duplicate_manifest_refs_fail_closed(self):
        with self.assertRaises(ValidationError):
            PublicGoodCase.model_validate({
                "case_id": "bad-manifest",
                "domain": "animal_welfare",
                "payload": {},
                "evidence_manifest": [
                    {"source_ref": "dup"},
                    {"source_ref": "dup"}
                ]
            })


if __name__ == "__main__":
    unittest.main()
