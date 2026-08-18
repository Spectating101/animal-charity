from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ControlPlaneApiTests(unittest.TestCase):
    def test_lifecycle_assessment_api_in_demo_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["AFRN_DB_PATH"] = str(Path(tmp) / "api.db")
            os.environ["AFRN_DEMO_MODE"] = "1"
            os.environ.pop("AFRN_OPERATOR_TOKEN", None)

            import importlib
            import app.main as main_module
            importlib.reload(main_module)
            from fastapi.testclient import TestClient

            client = TestClient(main_module.app)
            payload = json.loads((ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json").read_text(encoding="utf-8"))
            response = client.post("/v1/welfare/assess", json=payload, headers={"X-Actor": "api-test"})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["assessed_by"], "api-test")
            kinds = [x["intervention_class"] for x in body["decisions"]]
            self.assertIn("reunification", kinds)
            self.assertIn("owner_retention", kinds)
            self.assertIn("specialist_referral", kinds)


if __name__ == "__main__":
    unittest.main()
