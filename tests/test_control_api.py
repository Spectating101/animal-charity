from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ControlPlaneApiTests(unittest.TestCase):
    def _reset_auth_env(self):
        for key in (
            "AFRN_ACTOR_REGISTRY",
            "AFRN_TOKEN_ANALYST_1",
            "AFRN_TOKEN_OPERATOR_1",
            "AFRN_TOKEN_REVIEWER_1",
            "TEST_API_ANALYST_TOKEN",
        ):
            os.environ.pop(key, None)

    def _client(self, tmp: str):
        self._reset_auth_env()
        os.environ["AFRN_DB_PATH"] = str(Path(tmp) / "api.db")
        os.environ["AFRN_DEMO_MODE"] = "1"
        os.environ.pop("AFRN_OPERATOR_TOKEN", None)

        import importlib
        import app.main as main_module
        importlib.reload(main_module)
        from fastapi.testclient import TestClient
        return TestClient(main_module.app)

    def _registry_client(self, tmp: str):
        self._reset_auth_env()
        registry = Path(tmp) / "actors.json"
        registry.write_text(
            """{
  "version": "api-test-v1",
  "roles": {
    "analyst": ["summary.read", "public_good.assess", "welfare.assess", "replay.run"],
    "operator": ["summary.read", "public_good.assess", "welfare.assess", "operations.write"]
  },
  "actors": {
    "api-analyst": {
      "actor_id": "api-analyst",
      "roles": ["analyst"],
      "token_env": "TEST_API_ANALYST_TOKEN",
      "active": true
    }
  }
}""",
            encoding="utf-8",
        )
        os.environ["AFRN_DB_PATH"] = str(Path(tmp) / "api-registry.db")
        os.environ["AFRN_DEMO_MODE"] = "0"
        os.environ.pop("AFRN_OPERATOR_TOKEN", None)
        os.environ["AFRN_ACTOR_REGISTRY"] = str(registry)
        os.environ["TEST_API_ANALYST_TOKEN"] = "analyst-secret"

        import importlib
        import app.main as main_module
        importlib.reload(main_module)
        from fastapi.testclient import TestClient
        return TestClient(main_module.app)

    def test_lifecycle_assessment_api_in_demo_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(tmp)
            payload = json.loads((ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json").read_text(encoding="utf-8"))
            response = client.post("/v1/welfare/assess", json=payload, headers={"X-Actor": "api-test"})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["assessed_by"], "api-test")
            kinds = [x["intervention_class"] for x in body["decisions"]]
            self.assertIn("reunification", kinds)
            self.assertIn("owner_retention", kinds)
            self.assertIn("specialist_referral", kinds)

    def test_preventive_system_api_preserves_causal_discipline(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(tmp)
            payload = json.loads((ROOT / "examples" / "zhongli_sanmin_synthetic_preventive_system.json").read_text(encoding="utf-8"))
            response = client.post("/v1/welfare/system/assess", json=payload, headers={"X-Actor": "systems-test"})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["assessed_by"], "systems-test")
            source = [x for x in body["prevention_opportunities"] if x["intervention_class"] == "source_control"]
            self.assertEqual(len(source), 3)
            self.assertTrue(all(x["causal_status"] == "hypothesis" for x in source))
            self.assertTrue(body["access_gaps"])
            self.assertIn("rights", body["transfer_boundary"])

    def test_unified_public_good_api_is_audited_without_raw_case_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(tmp)
            payload = json.loads((ROOT / "examples" / "public_good_mbg_integrity.json").read_text(encoding="utf-8"))
            response = client.post("/v1/public-good/assess", json=payload, headers={"X-Actor": "governance-test"})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["domain"], "mbg_public_nutrition")
            self.assertEqual(body["normalized_findings"][0]["stage"], "integrity")
            self.assertEqual(body["assessed_by"], "governance-test")
            self.assertTrue(body["audit_event_hash"])

            events = client.get("/v1/audit/events", headers={"X-Actor": "governance-test"}).json()
            event = [x for x in events if x["event_id"] == body["audit_event_id"]][0]
            self.assertEqual(event["event_type"], "public_good.assessed")
            self.assertEqual(event["payload"]["domain"], "mbg_public_nutrition")
            self.assertIn("input_sha256", event["payload"])
            self.assertNotIn("payload", event["payload"])

    def test_registry_analyst_can_assess_but_cannot_operate(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self._registry_client(tmp)
            headers = {"X-Actor": "api-analyst", "Authorization": "Bearer analyst-secret"}
            payload = json.loads((ROOT / "examples" / "public_good_animal_owner_retention.json").read_text(encoding="utf-8"))

            assess = client.post("/v1/public-good/assess", json=payload, headers=headers)
            self.assertEqual(assess.status_code, 200)
            self.assertEqual(assess.json()["auth_mode"], "actor_registry")

            me = client.get("/v1/access/me", headers=headers)
            self.assertEqual(me.status_code, 200)
            self.assertIn("public_good.assess", me.json()["permissions"])
            self.assertNotIn("operations.write", me.json()["permissions"])

            recipient = {
                "name": "should-not-write",
                "region": "test",
                "source_ref": "synthetic:test"
            }
            denied = client.post("/v1/recipients", json=recipient, headers=headers)
            self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()
