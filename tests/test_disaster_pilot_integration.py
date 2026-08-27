from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.disaster_control import DisasterSnapshot
from app.public_good_control import PublicGoodCase
from app.replay import ReplayPacket, ReplayReference, run_replay, score_replay


ROOT = Path(__file__).resolve().parents[1]


class DisasterPilotIntegrationTests(unittest.TestCase):
    def _snapshot(self) -> DisasterSnapshot:
        return DisasterSnapshot.model_validate_json(
            (ROOT / "examples" / "disaster_ntt_synthetic.json").read_text(encoding="utf-8")
        )

    def _case(self) -> PublicGoodCase:
        snapshot = self._snapshot()
        return PublicGoodCase(
            case_id="synthetic-disaster-pilot-case",
            domain="disaster_response",
            payload=snapshot.model_dump(mode="json"),
        )

    def _client(self, tmp: str):
        for key in ("AFRN_ACTOR_REGISTRY", "AFRN_OPERATOR_TOKEN"):
            os.environ.pop(key, None)
        os.environ["AFRN_DB_PATH"] = str(Path(tmp) / "disaster-api.db")
        os.environ["AFRN_DEMO_MODE"] = "1"

        import importlib
        import app.main as main_module

        importlib.reload(main_module)
        from fastapi.testclient import TestClient

        return TestClient(main_module.app)

    def test_unified_api_accepts_disaster_domain_and_audits_summary_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(tmp)
            case = self._case()
            response = client.post(
                "/v1/public-good/assess",
                json=case.model_dump(mode="json"),
                headers={"X-Actor": "disaster-shadow-analyst"},
            )
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["domain"], "disaster_response")
            self.assertTrue(any(f["stage"] == "safety" for f in body["normalized_findings"]))
            self.assertTrue(body["audit_event_id"])

            events = client.get(
                "/v1/audit/events",
                headers={"X-Actor": "disaster-shadow-analyst"},
            ).json()
            event = next(event for event in events if event["event_id"] == body["audit_event_id"])
            self.assertEqual(event["event_type"], "public_good.assessed")
            self.assertEqual(event["payload"]["domain"], "disaster_response")
            self.assertIn("input_sha256", event["payload"])
            self.assertNotIn("payload", event["payload"])
            serialized = str(event["payload"])
            self.assertNotIn("synthetic:field-report:trapped-a", serialized)

    def test_disaster_replay_hides_reference_and_enforces_cutoff(self):
        packet = ReplayPacket(
            replay_id="synthetic-disaster-replay",
            decision_cutoff="2026-08-20T07:00:00Z",
            case=self._case(),
            reference=ReplayReference(
                expected_primary_stages=["safety"],
                historical_action="hidden synthetic reference action",
                historical_outcome_summary="hidden synthetic reference outcome",
                reference_refs=["synthetic:later:reference"],
            ),
            require_evidence_timestamps=True,
        )
        run = run_replay(packet)
        self.assertTrue(run.reference_hidden)
        self.assertEqual(run.assessment.domain.value, "disaster_response")
        self.assertEqual(run.assessment.normalized_findings[0].stage, "safety")
        self.assertNotIn("historical_action", run.model_dump(mode="json"))

        score = score_replay(packet)
        self.assertTrue(score.primary_stage_match)
        self.assertEqual(score.historical_action, "hidden synthetic reference action")

        packet.case.payload["needs"][0]["observed_at"] = "2026-08-20T07:05:00Z"
        with self.assertRaises(ValueError):
            run_replay(packet)


if __name__ == "__main__":
    unittest.main()
