from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from app.action_intents import GateState, build_wildfire_uas_intent, evaluate_wildfire_uas_intent


class ActionIntentTests(unittest.TestCase):
    def test_public_governance_intent_is_not_execution_ready_without_operator_gates(self):
        intent = build_wildfire_uas_intent(
            intent_id="intent-fire-observe-a",
            incident_id="fire-a",
            intent_type="wildfire.observe_hotspot",
            priority="urgent",
            evidence_refs=["official:hotspot:a"],
        )
        result = evaluate_wildfire_uas_intent(intent, GateState())
        self.assertFalse(result.execution_ready)
        self.assertTrue(result.missing_gates)
        self.assertEqual(result.intent.status.value, "awaiting_authority")
        self.assertIn("not a flight plan", " ".join(intent.notes).lower())

    def test_all_external_gates_can_mark_intent_authorized_without_creating_flight_command(self):
        intent = build_wildfire_uas_intent(
            intent_id="intent-fire-map-a",
            incident_id="fire-a",
            intent_type="wildfire.map_perimeter",
            priority="urgent",
            evidence_refs=["operator:fire:a"],
        )
        result = evaluate_wildfire_uas_intent(
            intent,
            GateState(
                incident_command_authority=True,
                airspace_operator_authorization=True,
                live_platform_verification=True,
                aviation_deconfliction=True,
                site_safety_review=True,
            ),
        )
        self.assertTrue(result.execution_ready)
        self.assertEqual(result.intent.status.value, "authorized")
        self.assertIn("not an autonomous flight", result.safe_conclusion)

    def test_suppression_intent_requests_operator_evaluation_not_drop_tactics(self):
        intent = build_wildfire_uas_intent(
            intent_id="intent-fire-suppression-a",
            incident_id="fire-a",
            intent_type="wildfire.request_suppression_support",
            priority="critical",
            evidence_refs=["official:fire:a"],
            source_finding_class="fire_suppression_observed_capacity_shortage",
        )
        self.assertEqual(intent.capability_class, "uas_suppression_support")
        self.assertIn("request evaluation", intent.goal.lower())
        serialized = intent.model_dump_json().lower()
        self.assertNotIn("drop point", serialized)
        self.assertNotIn("altitude", serialized)
        self.assertNotIn("flight path", serialized)

    def test_expired_intent_fails_closed(self):
        now = datetime.now(timezone.utc)
        intent = build_wildfire_uas_intent(
            intent_id="intent-fire-old-a",
            incident_id="fire-a",
            intent_type="wildfire.verify_access_edge",
            priority="urgent",
            evidence_refs=["official:old:a"],
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        result = evaluate_wildfire_uas_intent(intent, GateState(
            incident_command_authority=True,
            airspace_operator_authorization=True,
            live_platform_verification=True,
            aviation_deconfliction=True,
            site_safety_review=True,
        ))
        self.assertFalse(result.execution_ready)
        self.assertEqual(result.intent.status.value, "blocked")


if __name__ == "__main__":
    unittest.main()
