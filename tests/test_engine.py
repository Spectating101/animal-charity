from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.domain import AnimalGroup, InventoryLot, Recipient, ResolutionEvidence, SupplyBatch
from app.rules import RulePack, evaluate_match
from app.service import ReliefService

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "config" / "rulepacks" / "tw_dog_cat_pilot.json"


class ReliefEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = ReliefService(str(Path(self.tmp.name) / "test.db"), RULES)
        self.recipient = self.service.save(Recipient(name="Shelter", region="Taoyuan", status="active", reliability=0.8, welfare_review_ref="test://review"), actor="test", event_type="recipient.recorded")
        self.group = self.service.save(AnimalGroup(recipient_id=self.recipient.recipient_id, species="dog", count=20, daily_feed_kg=5), actor="test", event_type="animal_group.recorded")
        self.service.save(InventoryLot(recipient_id=self.recipient.recipient_id, group_id=self.group.group_id, product_name="Feed", quantity_kg=5), actor="test", event_type="inventory.observed")

    def tearDown(self):
        self.tmp.cleanup()

    def batch(self, **overrides):
        data = dict(
            donor_name="Donor",
            product_name="Complete Dog Feed",
            quantity_kg=50,
            species=["dog"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            location="Taoyuan",
        )
        data.update(overrides)
        return SupplyBatch(**data)

    def test_agent_opens_case_and_proposes_but_does_not_approve(self):
        batch = self.service.save(self.batch(), actor="test", event_type="supply.observed")
        result = self.service.agent_tick(actor="agent")
        self.assertEqual(len(result.opened_cases), 1)
        self.assertEqual(len(result.proposals_created), 1)
        proposal = self.service.store.list("proposal")[0]
        self.assertEqual(proposal["review_state"], "pending")
        case = self.service.store.list("case")[0]
        self.assertEqual(case["status"], "proposal_ready")
        self.assertEqual(proposal["batch_id"], batch.batch_id)

    def test_pending_recipient_is_not_auto_matchable(self):
        rules = RulePack.load(RULES)
        pending = Recipient(name="Pending", region="Taoyuan")
        gate = evaluate_match(recipient=pending, group=self.group, batch=self.batch(), rules=rules)
        self.assertFalse(gate.passed)
        self.assertIn("recipient_not_active", gate.reasons)

    def test_recipient_activation_is_human_only_and_audited(self):
        pending = self.service.save(Recipient(name="Pending", region="Taoyuan"), actor="intake", event_type="recipient.recorded")
        self.assertEqual(pending.status, "pending")
        reviewed = self.service.review_recipient(pending.recipient_id, approve=True, actor="welfare-reviewer", review_ref="review://1")
        self.assertEqual(reviewed.status, "active")
        self.assertEqual(reviewed.welfare_review_ref, "review://1")

    def test_prepared_food_is_not_auto_matchable(self):
        rules = RulePack.load(RULES)
        gate = evaluate_match(recipient=self.recipient, group=self.group, batch=self.batch(source_class="prepared"), rules=rules)
        self.assertFalse(gate.passed)
        self.assertIn("source_class_requires_professional_review", gate.reasons)

    def test_expired_food_is_rejected(self):
        rules = RulePack.load(RULES)
        gate = evaluate_match(recipient=self.recipient, group=self.group, batch=self.batch(expires_at=datetime.now(timezone.utc) - timedelta(hours=1)), rules=rules)
        self.assertFalse(gate.passed)
        self.assertIn("expired", gate.reasons)

    def test_resolution_requires_human_approval_and_evidence(self):
        self.service.save(self.batch(), actor="test", event_type="supply.observed")
        self.service.agent_tick(actor="agent")
        case = self.service.store.list("case")[0]
        proposal = self.service.store.list("proposal")[0]
        with self.assertRaises(ValueError):
            self.service.resolve_case(ResolutionEvidence(case_id=case["case_id"], evidence_ref="receipt://1", actor="operator", delivered_kg=10))
        self.service.review_proposal(proposal["proposal_id"], approve=True, actor="vet-reviewer")
        resolved = self.service.resolve_case(ResolutionEvidence(case_id=case["case_id"], evidence_ref="receipt://1", actor="operator", delivered_kg=10))
        self.assertEqual(resolved.status, "resolved")

    def test_hash_ledger_verifies(self):
        self.service.save(self.batch(), actor="test", event_type="supply.observed")
        self.service.agent_tick(actor="agent")
        ok, count, bad = self.service.store.verify_ledger()
        self.assertTrue(ok)
        self.assertGreater(count, 0)
        self.assertIsNone(bad)

    def test_supply_is_not_double_booked(self):
        second = self.service.save(
            AnimalGroup(recipient_id=self.recipient.recipient_id, species="dog", count=20, daily_feed_kg=5),
            actor="test", event_type="animal_group.recorded"
        )
        self.service.save(InventoryLot(recipient_id=self.recipient.recipient_id, group_id=second.group_id, product_name="Feed", quantity_kg=0), actor="test", event_type="inventory.observed")
        self.service.save(self.batch(quantity_kg=10), actor="test", event_type="supply.observed")
        self.service.agent_tick(actor="agent", target_buffer_days=14)
        proposals = self.service.store.list("proposal")
        self.assertLessEqual(sum(p["proposed_kg"] for p in proposals), 10.0)

    def test_fully_consumed_batch_can_reload_at_zero_balance(self):
        self.service.save(self.batch(quantity_kg=10), actor="test", event_type="supply.observed")
        self.service.agent_tick(actor="agent", target_buffer_days=3)
        case = self.service.store.list("case")[0]
        proposal = self.service.store.list("proposal")[0]
        self.service.review_proposal(proposal["proposal_id"], approve=True, actor="vet-reviewer")
        delivered = proposal["proposed_kg"]
        self.service.resolve_case(ResolutionEvidence(case_id=case["case_id"], evidence_ref="receipt://full", actor="operator", delivered_kg=delivered))
        batch_id = proposal["batch_id"]
        reloaded = self.service.get_model("supply", batch_id, SupplyBatch)
        self.assertIsNotNone(reloaded)
        self.assertEqual(delivered, 10)
        self.assertEqual(reloaded.quantity_kg, 0)

    def test_resolution_updates_inventory_and_impact(self):
        self.service.save(self.batch(quantity_kg=50), actor="test", event_type="supply.observed")
        self.service.agent_tick(actor="agent")
        case = self.service.store.list("case")[0]
        proposal = self.service.store.list("proposal")[0]
        self.service.review_proposal(proposal["proposal_id"], approve=True, actor="vet-reviewer")
        delivered = min(10.0, proposal["proposed_kg"])
        self.service.resolve_case(ResolutionEvidence(case_id=case["case_id"], evidence_ref="receipt://impact", actor="operator", delivered_kg=delivered))
        impact = self.service.impact_summary()
        self.assertEqual(impact["verified_deliveries"], 1)
        self.assertGreater(impact["verified_animal_days_supported"], 0)
        received = [x for x in self.service.store.list("inventory") if x.get("source_ref") == "receipt://impact"]
        self.assertEqual(len(received), 1)


if __name__ == "__main__":
    unittest.main()
