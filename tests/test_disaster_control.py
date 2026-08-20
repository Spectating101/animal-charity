from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.disaster_control import DisasterSnapshot, RecurrenceSignal, assess_disaster
from app.public_good_control import PublicGoodCase, assess_public_good_case


ROOT = Path(__file__).resolve().parents[1]


class DisasterControlTests(unittest.TestCase):
    def _load(self, name: str) -> DisasterSnapshot:
        return DisasterSnapshot.model_validate_json((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_critical_report_is_escalated_without_silent_rejection(self):
        result = assess_disaster(self._load("disaster_ntt_synthetic.json"))
        findings = [finding for finding in result.findings if finding.need_id == "trapped-a"]
        self.assertTrue(any(f.problem_class == "critical_need_requires_verification_and_escalation" for f in findings))
        self.assertTrue(any(f.stage == "route" for f in findings))

    def test_resource_is_not_double_booked_inside_one_assessment(self):
        result = assess_disaster(self._load("disaster_ntt_synthetic.json"))
        sar_reservations = [
            reservation for reservation in result.proposed_reservations if reservation.resource_record_id == "sar-team-a"
        ]
        self.assertEqual(len(sar_reservations), 1)
        life_safety = [finding for finding in result.findings if finding.need_id in {"trapped-a", "trapped-b"}]
        self.assertTrue(any(f.stage == "capacity" for f in life_safety))

    def test_committed_water_resource_is_not_treated_as_spare(self):
        result = assess_disaster(self._load("disaster_ntt_synthetic.json"))
        water = [finding for finding in result.findings if finding.need_id == "water-a"]
        self.assertTrue(any(f.problem_class == "potable_water_capacity_gap" for f in water))
        self.assertFalse(any("water-truck-a" in f.resource_refs for f in water))

    def test_isolated_need_requires_access_capability_before_routing(self):
        result = assess_disaster(self._load("disaster_ntt_synthetic.json"))
        isolated = [finding for finding in result.findings if finding.need_id == "isolated-medical-a"]
        self.assertTrue(any(f.stage == "access" for f in isolated))

    def test_existing_reachable_service_beats_new_mobile_capacity(self):
        result = assess_disaster(self._load("disaster_kalimantan_synthetic.json"))
        medical = [finding for finding in result.findings if finding.need_id == "smoke-medical-a"]
        self.assertTrue(any(f.problem_class == "medical_existing_service_route" for f in medical))
        self.assertFalse(any(f.stage == "capacity" for f in medical))

    def test_reported_aircraft_requires_verification(self):
        result = assess_disaster(self._load("disaster_kalimantan_synthetic.json"))
        suppression = [finding for finding in result.findings if finding.need_id == "suppression-b"]
        self.assertTrue(any(f.problem_class == "reported_resource_requires_verification" for f in suppression))
        self.assertFalse(any("aircraft-candidate-a" == r.resource_record_id for r in result.proposed_reservations))

    def test_public_good_router_uses_disaster_constitution(self):
        snapshot = self._load("disaster_ntt_synthetic.json")
        case = PublicGoodCase(
            case_id="synthetic-public-good-disaster",
            domain="disaster_response",
            payload=snapshot.model_dump(mode="json"),
        )
        assessment = assess_public_good_case(case)
        self.assertEqual(assessment.domain.value, "disaster_response")
        self.assertIn("disaster_response_control.json", assessment.constitution_ref)
        self.assertTrue(any(f.stage == "safety" for f in assessment.normalized_findings))
        self.assertIn("aid-deservingness", assessment.safe_conclusion)

    def test_no_needs_does_not_infer_relief_requirement_from_hazard_alone(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        snapshot.needs = []
        result = assess_disaster(snapshot)
        self.assertEqual(result.findings, [])
        self.assertTrue(any("hazard presence alone" in gap for gap in result.data_gaps))

    def test_unknown_need_status_requests_evidence_instead_of_inventing_capacity_gap(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        snapshot.needs[1].status = "unknown"
        result = assess_disaster(snapshot)
        findings = [finding for finding in result.findings if finding.need_id == "suppression-b"]
        self.assertTrue(any(f.problem_class == "need_status_not_established" for f in findings))
        self.assertFalse(any(f.stage in {"route", "capacity", "access"} for f in findings))
        self.assertFalse(any(r.need_id == "suppression-b" for r in result.proposed_reservations))

    def test_structural_candidate_requires_non_response_phase_and_recurrence(self):
        snapshot = self._load("disaster_kalimantan_synthetic.json")
        snapshot.phase = "mitigation"
        snapshot.recurrence_signals = [
            RecurrenceSignal(
                signal_id="repeat-fire-a",
                location_ref="synthetic-peat-zone-a",
                problem_class="hazard_recurrence",
                event_count=4,
                span_days=365,
                source_refs=["synthetic:history:fire-a"],
            )
        ]
        result = assess_disaster(snapshot)
        finding = next(f for f in result.findings if f.need_id == "suppression-a" and f.stage == "route")
        self.assertTrue(finding.structural_candidate)


if __name__ == "__main__":
    unittest.main()
