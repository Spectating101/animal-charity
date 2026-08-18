from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ControlPlaneApiTests(unittest.TestCase):
    def _client(self, tmp: str):
        os.environ["AFRN_DB_PATH"] = str(Path(tmp) / "api.db")
        os.environ["AFRN_DEMO_MODE"] = "1"
        os.environ.pop("AFRN_OPERATOR_TOKEN", None)

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


if __name__ == "__main__":
    unittest.main()
