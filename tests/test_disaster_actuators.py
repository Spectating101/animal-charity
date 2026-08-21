from __future__ import annotations

import unittest
from pathlib import Path

from app.disaster_actuators import propose_wildfire_uas_intents
from app.disaster_control import DisasterSnapshot, assess_disaster


ROOT = Path(__file__).resolve().parents[1]


class DisasterActuatorTests(unittest.TestCase):
    def _load(self, name: str) -> DisasterSnapshot:
        return DisasterSnapshot.model_validate_json((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_wildfire_presence_alone_does_not_emit_drone_intent(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        assessment = assess_disaster(snapshot)
        plan = propose_wildfire_uas_intents(snapshot, assessment)
        self.assertEqual(plan.proposed_intents, [])
        self.assertTrue(plan.skipped_reasons)

    def test_uncertain_urgent_fire_condition_emits_observation_intent_only(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        target = next(need for need in snapshot.needs if need.category.value == "fire_suppression")
        target.status = "unknown"
        target.priority = "urgent"
        assessment = assess_disaster(snapshot)
        plan = propose_wildfire_uas_intents(snapshot, assessment)
        matching = [intent for intent in plan.proposed_intents if intent.intent_type == "wildfire.observe_hotspot"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].source_finding_class, "need_status_not_established")
        self.assertFalse(any(intent.intent_type == "wildfire.request_suppression_support" for intent in plan.proposed_intents))

    def test_corrob_observed_fire_capacity_shortage_can_request_operator_suppression_evaluation(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        target = next(need for need in snapshot.needs if need.category.value == "fire_suppression")
        target.status = "unmet"
        target.capacity_status = "insufficient"
        target.verification_status = "corroborated"
        assessment = assess_disaster(snapshot)
        plan = propose_wildfire_uas_intents(snapshot, assessment)
        matching = [intent for intent in plan.proposed_intents if intent.intent_type == "wildfire.request_suppression_support"]
        self.assertEqual(len(matching), 1)
        intent = matching[0]
        self.assertEqual(intent.source_finding_class, "fire_suppression_observed_capacity_shortage")
        self.assertIn("request evaluation", intent.goal.lower())
        self.assertEqual(intent.status.value, "proposed")

    def test_actionable_synthetic_case_produces_one_nonbinding_suppression_intent(self):
        snapshot = self._load("disaster_wildfire_actionable_synthetic.json")
        assessment = assess_disaster(snapshot)
        plan = propose_wildfire_uas_intents(snapshot, assessment)
        self.assertEqual(len(plan.proposed_intents), 1)
        intent = plan.proposed_intents[0]
        self.assertEqual(intent.intent_type, "wildfire.request_suppression_support")
        self.assertEqual(intent.status.value, "proposed")
        self.assertIn("not a flight plan", " ".join(intent.notes).lower())

    def test_non_wildfire_disaster_never_enters_wildfire_uas_mapper(self):
        snapshot = self._load("disaster_ntt_synthetic.json")
        assessment = assess_disaster(snapshot)
        plan = propose_wildfire_uas_intents(snapshot, assessment)
        self.assertEqual(plan.proposed_intents, [])
        self.assertTrue(any("No wildfire" in reason for reason in plan.skipped_reasons))


if __name__ == "__main__":
    unittest.main()
