from __future__ import annotations

import unittest
from pathlib import Path

from app.disaster_control import DisasterSnapshot, assess_disaster


ROOT = Path(__file__).resolve().parents[1]


class DisasterCapacityObservationTests(unittest.TestCase):
    def _load(self, name: str) -> DisasterSnapshot:
        return DisasterSnapshot.model_validate_json((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_corrobated_observed_shortage_can_establish_capacity_without_complete_inventory(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        need = snapshot.needs[1]
        need.status = "unmet"
        need.verification_status = "corroborated"
        need.capacity_status = "insufficient"
        need.access_status = "open"
        snapshot.interoperability.resource_inventory_scope = "unknown"
        snapshot.interoperability.service_registry_scope = "unknown"
        snapshot.interoperability.records = []

        result = assess_disaster(snapshot)
        findings = [finding for finding in result.findings if finding.need_id == need.need_id]
        self.assertTrue(any(f.problem_class == "fire_suppression_observed_capacity_shortage" for f in findings))
        self.assertTrue(any(f.stage == "capacity" for f in findings))
        self.assertFalse(any(f.problem_class == "capability_inventory_incomplete" for f in findings))
        self.assertFalse(any(r.need_id == need.need_id for r in result.proposed_reservations))

    def test_reported_observed_shortage_stays_verification_only(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        need = snapshot.needs[1]
        need.status = "unmet"
        need.verification_status = "reported"
        need.capacity_status = "insufficient"
        need.access_status = "open"
        snapshot.interoperability.resource_inventory_scope = "unknown"
        snapshot.interoperability.service_registry_scope = "unknown"
        snapshot.interoperability.records = []

        result = assess_disaster(snapshot)
        findings = [finding for finding in result.findings if finding.need_id == need.need_id]
        self.assertTrue(any(f.problem_class == "reported_capacity_shortage_requires_verification" for f in findings))
        self.assertFalse(any(f.stage == "capacity" for f in findings))
        self.assertFalse(any(r.need_id == need.need_id for r in result.proposed_reservations))


if __name__ == "__main__":
    unittest.main()
