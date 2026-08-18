from __future__ import annotations

import unittest

from app.integrity_plane import (
    FlowObservation,
    IntegritySnapshot,
    IntegrityStage,
    ReconciliationCheck,
    VerificationStatus,
    assess_integrity,
)


class IntegrityPlaneTests(unittest.TestCase):
    def test_verified_critical_variance_recommends_audit_not_corruption_finding(self):
        snapshot = IntegritySnapshot(
            programme_id="p",
            area_id="a",
            observations=[
                FlowObservation(
                    observation_id="invoice",
                    stage=IntegrityStage.procurement,
                    metric="rice",
                    value=100,
                    unit="kg",
                    source_ref="invoice",
                    verification_status=VerificationStatus.verified,
                ),
                FlowObservation(
                    observation_id="receipt",
                    stage=IntegrityStage.physical_input,
                    metric="rice",
                    value=70,
                    unit="kg",
                    source_ref="weighed-receipt",
                    verification_status=VerificationStatus.verified,
                ),
            ],
            checks=[
                ReconciliationCheck(
                    check_id="c",
                    expected_observation_id="invoice",
                    observed_observation_id="receipt",
                    tolerance_pct=0.02,
                    critical=True,
                )
            ],
        )
        result = assess_integrity(snapshot)
        self.assertEqual(result.overall_status, "audit_referral_recommended")
        self.assertIn("does not determine fraud", result.safe_conclusion)
        self.assertNotIn("confirmed corruption", result.safe_conclusion.lower())

    def test_reported_side_keeps_variance_as_explanation_request(self):
        snapshot = IntegritySnapshot(
            programme_id="p",
            area_id="a",
            observations=[
                FlowObservation(
                    observation_id="claim",
                    stage=IntegrityStage.service_output,
                    metric="meals",
                    value=100,
                    unit="meals",
                    source_ref="self-report",
                    verification_status=VerificationStatus.reported,
                ),
                FlowObservation(
                    observation_id="receipt",
                    stage=IntegrityStage.beneficiary_receipt,
                    metric="meals",
                    value=70,
                    unit="meals",
                    source_ref="recipient-count",
                    verification_status=VerificationStatus.verified,
                ),
            ],
            checks=[
                ReconciliationCheck(
                    check_id="c",
                    expected_observation_id="claim",
                    observed_observation_id="receipt",
                    tolerance_pct=0.02,
                    critical=True,
                )
            ],
        )
        self.assertEqual(assess_integrity(snapshot).overall_status, "variance_needs_explanation")

    def test_within_tolerance_is_normal(self):
        snapshot = IntegritySnapshot(
            programme_id="p",
            area_id="a",
            observations=[
                FlowObservation(
                    observation_id="a1",
                    stage=IntegrityStage.service_output,
                    metric="meals",
                    value=1000,
                    unit="meals",
                    source_ref="a1",
                    verification_status=VerificationStatus.verified,
                ),
                FlowObservation(
                    observation_id="a2",
                    stage=IntegrityStage.beneficiary_receipt,
                    metric="meals",
                    value=990,
                    unit="meals",
                    source_ref="a2",
                    verification_status=VerificationStatus.verified,
                ),
            ],
            checks=[ReconciliationCheck(
                check_id="c",
                expected_observation_id="a1",
                observed_observation_id="a2",
                tolerance_pct=0.02,
                critical=True,
            )],
        )
        self.assertEqual(assess_integrity(snapshot).overall_status, "normal")

    def test_missing_or_incompatible_evidence_cannot_be_forced_into_variance(self):
        snapshot = IntegritySnapshot(
            programme_id="p",
            area_id="a",
            observations=[FlowObservation(
                observation_id="a1",
                stage=IntegrityStage.procurement,
                metric="food",
                value=10,
                unit="kg",
                source_ref="a1",
                verification_status=VerificationStatus.verified,
            )],
            checks=[ReconciliationCheck(
                check_id="c",
                expected_observation_id="a1",
                observed_observation_id="missing",
            )],
        )
        result = assess_integrity(snapshot)
        self.assertEqual(result.overall_status, "evidence_gap")
        self.assertTrue(result.data_gaps)


if __name__ == "__main__":
    unittest.main()
