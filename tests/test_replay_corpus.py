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

        self.assertEqual(result.corpus_id, "disaster-public-r1-v1")
        self.assertEqual(result.case_count, 2)
        self.assertEqual(result.by_evidence_level, {"R1": 2})
        self.assertEqual(result.passed_count, 2)
        self.assertEqual(result.failed_count, 0)

        by_id = {case.case_id: case for case in result.results}
        kubu = by_id["kubu-raya-karhutla-2026-08-07-public"]
        ntt = by_id["ntt-earthquake-2026-08-15-early-public"]
        self.assertEqual(kubu.predicted_primary_stage, "evidence")
        self.assertEqual(ntt.predicted_primary_stage, "safety")
        self.assertEqual(kubu.resource_reservation_count, 0)
        self.assertEqual(ntt.resource_reservation_count, 0)

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
                    max_resource_reservations=0,
                )
            ],
        )
        result = evaluate_corpus(spec, ROOT)
        self.assertEqual(result.passed_count, 0)
        self.assertEqual(result.failed_count, 1)
        self.assertTrue(any("required problem class missing" in v for v in result.results[0].violations))
        self.assertTrue(any("forbidden stage present" in v for v in result.results[0].violations))


if __name__ == "__main__":
    unittest.main()
