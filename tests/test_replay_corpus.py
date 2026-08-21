from __future__ import annotations

import unittest
from pathlib import Path

from app.replay_corpus import ReplayCorpusCaseSpec, ReplayCorpusSpec, evaluate_corpus, load_corpus


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "config" / "research" / "disaster_replay_corpus.json"


class ReplayCorpusTests(unittest.TestCase):
    def test_disaster_r1_campaign_passes_safety_contracts(self):
        spec = load_corpus(CORPUS)
        result = evaluate_corpus(spec, ROOT)

        self.assertEqual(result.corpus_id, "disaster-public-r1-v5")
        self.assertEqual(result.case_count, 12)
        self.assertEqual(result.by_evidence_level, {"R1": 12})
        self.assertEqual(result.passed_count, 12)
        self.assertEqual(result.failed_count, 0)

        by_id = {case.case_id: case for case in result.results}
        expected_stages = {
            "kubu-raya-karhutla-2026-08-07-public": "evidence",
            "ntt-earthquake-2026-08-15-early-public": "safety",
            "ntt-earthquake-2026-08-16-access-public": "access",
            "ruang-eruption-2024-04-18-public": "safety",
            "lewotobi-eruption-2024-11-05-public": "safety",
            "palu-airport-comms-2018-09-29-public": "evidence",
            "sumbar-lahar-2024-05-14-access-public": "access",
            "bekasi-flood-hospital-2025-03-04-public": "safety",
            "semeru-eruption-2021-12-05-access-public": "access",
            "cianjur-gasol-2022-11-27-adequate-service": None,
            "luwu-utara-flood-2020-07-19-capacity-public": "capacity",
            "krayan-landslide-2026-07-17-dependency-public": "access",
        }
        for case_id, expected_stage in expected_stages.items():
            with self.subTest(case_id=case_id):
                self.assertEqual(by_id[case_id].predicted_primary_stage, expected_stage)
                self.assertEqual(by_id[case_id].resource_reservation_count, 0)
                self.assertFalse(by_id[case_id].command_context_present)

        for case_id in expected_stages:
            if case_id != "luwu-utara-flood-2020-07-19-capacity-public":
                self.assertNotIn("capacity", by_id[case_id].stages)

        self.assertIn(
            "critical_need_requires_verification_and_escalation",
            by_id["ruang-eruption-2024-04-18-public"].problem_classes,
        )
        self.assertIn(
            "reported_resource_requires_verification",
            by_id["lewotobi-eruption-2024-11-05-public"].problem_classes,
        )
        self.assertIn(
            "confirmed_access_disruption",
            by_id["sumbar-lahar-2024-05-14-access-public"].problem_classes,
        )
        self.assertIn(
            "capability_inventory_incomplete",
            by_id["palu-airport-comms-2018-09-29-public"].problem_classes,
        )

        cianjur = by_id["cianjur-gasol-2022-11-27-adequate-service"]
        self.assertEqual(cianjur.finding_count, 0)
        self.assertEqual(cianjur.problem_classes, [])
        self.assertEqual(cianjur.stages, [])

        luwu = by_id["luwu-utara-flood-2020-07-19-capacity-public"]
        self.assertIn("shelter_observed_capacity_shortage", luwu.problem_classes)
        self.assertIn("capacity", luwu.stages)
        self.assertNotIn("capability_inventory_incomplete", luwu.problem_classes)

        krayan = by_id["krayan-landslide-2026-07-17-dependency-public"]
        self.assertIn("confirmed_access_disruption", krayan.problem_classes)
        self.assertIn("power_blocked_by_upstream_dependency", krayan.problem_classes)
        self.assertNotIn("power_capacity_gap", krayan.problem_classes)
        self.assertNotIn("power_observed_capacity_shortage", krayan.problem_classes)
        self.assertNotIn("capacity", krayan.stages)

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
                    max_findings=0,
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
        self.assertTrue(any("findings" in v and "exceed maximum" in v for v in violations))
        self.assertTrue(any("command-context expectation mismatch" in v for v in violations))
        self.assertTrue(any("resource-inventory scope mismatch" in v for v in violations))
        self.assertTrue(any("service-registry scope mismatch" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
