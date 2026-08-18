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


if __name__ == "__main__":
    unittest.main()
