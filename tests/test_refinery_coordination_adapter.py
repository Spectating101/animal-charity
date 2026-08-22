from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from app.refinery_coordination_adapter import (
    RefineryCoordinationBridgePacket,
    assess_refinery_coordination_bridge,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "refinery_coordination_bridge_indonesia_reef_2026.json"


class RefineryCoordinationAdapterTests(unittest.TestCase):
    def _payload(self) -> dict:
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_real_projection_plus_declared_needs_produces_bounded_matches(self):
        packet = RefineryCoordinationBridgePacket.model_validate(self._payload())
        result = assess_refinery_coordination_bridge(packet)
        self.assertEqual(result.refinery_case_id, "indonesia-reef-coordination-2026")
        self.assertEqual(result.refinery_source_count, 3)
        self.assertEqual(result.observed_initiative_count, 1)
        self.assertEqual(result.declared_initiative_count, 2)
        self.assertEqual(result.resource_count, 2)
        self.assertEqual(len(result.coordination.matches), 4)
        self.assertIn("cannot upgrade evidence maturity", result.bridge_boundary)

    def test_observed_telkom_activity_does_not_acquire_invented_need_or_match(self):
        packet = RefineryCoordinationBridgePacket.model_validate(self._payload())
        result = assess_refinery_coordination_bridge(packet)
        self.assertFalse(
            any(match.initiative_id == "telkom-bisa-biru-buru-2026" for match in result.coordination.matches)
        )

    def test_closed_tfcca_cycle_stays_blocked_despite_lesser_sunda_fit(self):
        packet = RefineryCoordinationBridgePacket.model_validate(self._payload())
        result = assess_refinery_coordination_bridge(packet)
        match = next(
            item
            for item in result.coordination.matches
            if item.initiative_id == "synthetic-lesser-sunda-community-reef-probe"
            and item.resource_id == "tfcca-cycle-1-2026"
        )
        self.assertEqual(match.status, "blocked")
        self.assertIn("support_kind", match.matched_dimensions)
        self.assertIn("theme", match.matched_dimensions)
        self.assertIn("geography", match.matched_dimensions)
        self.assertIn("actor_type", match.matched_dimensions)
        self.assertIn("application_status", match.blocking_dimensions)

    def test_koralestari_is_useful_lead_but_not_apply_now(self):
        packet = RefineryCoordinationBridgePacket.model_validate(self._payload())
        result = assess_refinery_coordination_bridge(packet)
        match = next(
            item
            for item in result.coordination.matches
            if item.initiative_id == "synthetic-savu-reef-positive-business-probe"
            and item.resource_id == "koralestari-gfcr-finance"
        )
        self.assertEqual(match.status, "requires_verification")
        self.assertEqual(set(match.matched_dimensions), {"support_kind", "theme", "geography", "actor_type"})
        self.assertEqual(match.unresolved_dimensions, ["application_status"])
        self.assertEqual(match.blocking_dimensions, [])

    def test_projection_cannot_smuggle_submission_or_recommendation_authority(self):
        payload = self._payload()
        payload["projection"]["projection_authority"]["external_submission"] = True
        with self.assertRaises(ValidationError):
            RefineryCoordinationBridgePacket.model_validate(payload)

        payload = self._payload()
        payload["projection"]["projection_authority"]["recommendation"] = True
        with self.assertRaises(ValidationError):
            RefineryCoordinationBridgePacket.model_validate(payload)

    def test_duplicate_observed_and_declared_initiative_ids_fail_closed(self):
        payload = self._payload()
        payload["declared_initiatives"][0]["initiative_id"] = "telkom-bisa-biru-buru-2026"
        with self.assertRaises(ValidationError):
            RefineryCoordinationBridgePacket.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
