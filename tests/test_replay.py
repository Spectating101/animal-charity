from __future__ import annotations

import copy
import unittest
from pathlib import Path

from app.replay import ReplayPacket, run_replay, score_replay


ROOT = Path(__file__).resolve().parents[1]


class ReplayTests(unittest.TestCase):
    def _packet(self, name: str) -> ReplayPacket:
        return ReplayPacket.model_validate_json((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_animal_replay_hides_reference_until_scoring(self):
        packet = self._packet("replay_animal_owner_retention.json")
        run = run_replay(packet)
        self.assertEqual(run.assessment.domain.value, "animal_welfare")
        self.assertEqual(run.assessment.normalized_findings[0].stage, "prevent")
        self.assertTrue(run.reference_hidden)
        self.assertNotIn("historical_action", run.model_dump(mode="json"))

        score = score_replay(packet)
        self.assertTrue(score.primary_stage_match)
        self.assertEqual(score.predicted_primary_stage, "prevent")
        self.assertIn("veterinary", (score.historical_action or "").lower())

    def test_mbg_replay_preserves_integrity_before_scarcity(self):
        packet = self._packet("replay_mbg_integrity.json")
        run = run_replay(packet)
        stages = [finding.stage for finding in run.assessment.normalized_findings]
        self.assertEqual(stages[0], "integrity")
        self.assertNotIn("capacity", stages)
        self.assertTrue(score_replay(packet).primary_stage_match)

    def test_future_evidence_is_rejected(self):
        packet = self._packet("replay_animal_owner_retention.json")
        raw = packet.model_dump(mode="json")
        raw["case"]["payload"]["observations"][0]["observed_at"] = "2026-07-11T09:00:00+08:00"
        future = ReplayPacket.model_validate(raw)
        with self.assertRaisesRegex(ValueError, "after the decision cutoff"):
            run_replay(future)

    def test_untimestamped_evidence_is_rejected_in_strict_mode(self):
        packet = self._packet("replay_animal_owner_retention.json")
        raw = copy.deepcopy(packet.model_dump(mode="json"))
        del raw["case"]["payload"]["observations"][0]["observed_at"]
        missing = ReplayPacket.model_validate(raw)
        with self.assertRaisesRegex(ValueError, "requires timestamps"):
            run_replay(missing)


if __name__ == "__main__":
    unittest.main()
