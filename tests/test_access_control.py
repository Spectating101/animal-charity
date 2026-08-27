from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.access_control import authenticate_actor, load_actor_registry


class AccessControlTests(unittest.TestCase):
    def _registry(self, tmp: str):
        path = Path(tmp) / "actors.json"
        path.write_text(
            """{
  "version": "test-v1",
  "roles": {
    "analyst": ["public_good.assess", "summary.read"],
    "reviewer": ["review.write", "audit.read"]
  },
  "actors": {
    "alice": {"actor_id": "alice", "roles": ["analyst"], "token_env": "TEST_ALICE_TOKEN", "active": true},
    "bob": {"actor_id": "bob", "roles": ["reviewer"], "token_env": "TEST_BOB_TOKEN", "active": false}
  }
}""",
            encoding="utf-8",
        )
        return load_actor_registry(path)

    def test_registry_derives_permissions_server_side(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            os.environ["TEST_ALICE_TOKEN"] = "alice-secret"
            actor = authenticate_actor(
                authorization="Bearer alice-secret",
                actor_id="alice",
                demo_mode=False,
                registry=registry,
            )
            self.assertEqual(actor.actor_id, "alice")
            self.assertTrue(actor.can("public_good.assess"))
            self.assertFalse(actor.can("review.write"))
            self.assertEqual(actor.auth_mode, "actor_registry")

    def test_wrong_token_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            os.environ["TEST_ALICE_TOKEN"] = "alice-secret"
            with self.assertRaises(PermissionError):
                authenticate_actor(
                    authorization="Bearer wrong",
                    actor_id="alice",
                    demo_mode=False,
                    registry=registry,
                )

    def test_inactive_actor_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            os.environ["TEST_BOB_TOKEN"] = "bob-secret"
            with self.assertRaises(PermissionError):
                authenticate_actor(
                    authorization="Bearer bob-secret",
                    actor_id="bob",
                    demo_mode=False,
                    registry=registry,
                )


if __name__ == "__main__":
    unittest.main()
