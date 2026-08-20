from __future__ import annotations

import unittest
from pathlib import Path

from app.replay_corpus import ReplayCorpusCaseSpec, ReplayCorpusSpec, evaluate_corpus, load_corpus


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "config" / "research" / "disaster_replay_corpus.json"


class ReplayCorpusTests(unittest.TestCase):
    def test_initial_real_disaster_corpus_passes_safety_contracts(self):
        spec = load_corpus(CORPUS)
        result = evaluate_corpus(spec, ROOT)

        self.assertEqual(result.corpus_id, "disaster-public-r1-v2")
        self.assertEqual(result.case_count, 3)
        self.assertEqual(result.by_evidence_level, {"R1": 3})
        self.assertEqual(result.passed_count, 3)
        self.assertEqual(result.failed_count, 0)

        by_id = {case.case_id: case for case in result.results}
        kubu = by_id["kubu-raya-karhutla-2026-08-07-public"]
        ntt_early = by_id["ntt-earthquake-2026-08-15-early-public"]
        ntt_access = by_id["ntt-earthquake-2026-08-16-access-public"]

        self.assertEqual(kubu.predicted_primary_stage, "evidence")
        self.assertEqual(ntt_early.predicted_primary_stage, "safety")
        self.assertEqual(ntt_access.predicted_primary_stage, "access")
        self.assertEqual(kubu.resource_reservation_count, 0)
        self.assertEqual(ntt_early.resource_reservation_count, 0)
        self.assertEqual(ntt_access.resource_reservation_count, 0)
        self.assertFalse(kubu.command_context_present)
        self.assertFalse(ntt_early.command_context_present)
        self.assertFalse(ntt_access.command_context_present)
        self.assertEqual(kubu.resource_inventory_scope, "partial")
        self.assertEqual(kubu.service_registry_scope, "unknown")
        self.assertEqual(ntt_early.resource_inventory_scope, "unknown")
        self.assertEqual(ntt_early.service_registry_scope, "unknown")
        self.assertEqual(ntt_access.resource_inventory_scope, "unknown")
        self.assertEqual(ntt_access.service_registry_scope, "unknown")
        self.assertIn("confirmed_access_disruption", ntt_access.problem_classes)
        self.assertIn("capability_inventory_incomplete", ntt_access.problem_classes)
        self.assertNotIn("capacity", ntt_access.stages)

    def test_corpus_reports_unsafe_contract_violation(self):
        spec = ReplayCorpusSpec(
            corpus_id="deliberately-impossible",
            cases=[
                ReplayCorpusCaseSpec(
                    case_id="kubu-negative-control",
                    packet_path="examples/replay_disaster_kubu_raya_2026_08_07.json",
                    evidence_level="R1",
                    required_problem_classes=["nonexistent_required_class"],
                    forbidden_stages=["evidence"],
                    required_data_gap_substrings=["nonexistent authority gap"],
                    max_resource_reservations=0,
                    expected_command_context_present=True,
                    expected_resource_inventory_scope="complete_for_scope",
                    expected_service_registry_scope="complete_for_scope",
                )
            ],
        )
        result = evaluate_corpus(spec, ROOT)
        self.assertEqual(result.passed_count, 0)
        self.assertEqual(result.failed_count, 1)
        violations = result.results[0].violations
        self.assertTrue(any("required problem class missing" in v for v in violations))
        self.assertTrue(any("forbidden stage present" in v for v in violations))
        self.assertTrue(any("required data-gap text missing" in v for v in violations))
        self.assertTrue(any("command-context expectation mismatch" in v for v in violations))
        self.assertTrue(any("resource-inventory scope mismatch" in v for v in violations))
        self.assertTrue(any("service-registry scope mismatch" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
