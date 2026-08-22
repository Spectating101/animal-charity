from __future__ import annotations

import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.disaster_access import (
    DisasterAccessEnvelope,
    DisasterAccessPacket,
    DisasterMovementRequest,
    VehicleAccessRule,
    apply_disaster_access_envelopes,
    assess_disaster_payload,
)
from app.disaster_control import DisasterNeed, DisasterSnapshot
from app.disaster_safety import assess_disaster_payload as assess_safety_payload
from app.interoperability import ExternalRecord, InteroperabilityBundle


AS_OF = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)


class DisasterAccessEnvelopeTests(unittest.TestCase):
    def _routable_snapshot(self) -> DisasterSnapshot:
        return DisasterSnapshot(
            incident_id="synthetic-access-envelope",
            as_of=AS_OF,
            phase="response",
            interoperability=InteroperabilityBundle(
                bundle_id="synthetic-access-operations",
                as_of=AS_OF,
                resource_inventory_scope="partial",
                service_registry_scope="unknown",
                records=[
                    ExternalRecord(
                        record_id="food-truck-a",
                        system_id="synthetic-eoc",
                        integration_role="operations_platform",
                        kind="capability_resource",
                        source_ref="synthetic:food-truck-a",
                        source_kind="operator",
                        observed_at=AS_OF,
                        verification_status="verified",
                        sensitivity="internal",
                        attributes={
                            "resource_type": "relief_truck",
                            "capabilities": ["food_distribution"],
                            "availability": "available",
                            "deployment_state": "staged",
                            "location_ref": "base-a",
                        },
                    )
                ],
            ),
            needs=[
                DisasterNeed(
                    need_id="food-need",
                    location_ref="route-a",
                    category="food",
                    priority="urgent",
                    status="unmet",
                    source_ref="synthetic:food-need",
                    verification_status="verified",
                    observed_at=AS_OF,
                    access_status="open",
                    required_capabilities=["food_distribution"],
                )
            ],
        )

    def _envelope(self, verification: str = "verified") -> DisasterAccessEnvelope:
        return DisasterAccessEnvelope(
            envelope_id="route-a-envelope",
            need_id="food-need",
            source_ref="synthetic:route-envelope",
            verification_status=verification,
            observed_at=AS_OF,
            traffic_control="controlled",
            rules=[
                VehicleAccessRule(
                    rule_id="six-wheel-10t",
                    vehicle_class="six_wheel",
                    effect="conditional_allow",
                    max_gross_weight_tons=10,
                    conditions=["movement remains subject to local traffic supervision"],
                ),
                VehicleAccessRule(
                    rule_id="four-wheel",
                    vehicle_class="four_wheel",
                    effect="allow",
                ),
            ],
        )

    def _movement(self, *, weight: float | None = 9, vehicle_class: str = "six_wheel") -> DisasterMovementRequest:
        return DisasterMovementRequest(
            movement_id="movement-a",
            need_id="food-need",
            vehicle_class=vehicle_class,
            gross_weight_tons=weight,
        )

    def test_verified_weight_limit_can_invalidate_otherwise_valid_route(self):
        snapshot = self._routable_snapshot()
        base = assess_safety_payload(snapshot.model_dump(mode="json"))
        self.assertTrue(any(f.stage == "route" for f in base.findings))
        self.assertEqual(len(base.proposed_reservations), 1)

        packet = DisasterAccessPacket(
            snapshot=snapshot,
            envelopes=[self._envelope()],
            movement_requests=[self._movement(weight=12)],
        )
        result = apply_disaster_access_envelopes(packet, base)

        self.assertEqual(result.movement_admissibility[0].status, "inadmissible")
        self.assertFalse(any(f.stage == "route" and f.need_id == "food-need" for f in result.findings))
        self.assertFalse(any(r.need_id == "food-need" for r in result.proposed_reservations))
        self.assertEqual(result.findings[0].problem_class, "movement_not_admissible_under_access_envelope")

    def test_compliant_vehicle_is_conditional_under_controlled_traffic(self):
        snapshot = self._routable_snapshot()
        base = assess_safety_payload(snapshot.model_dump(mode="json"))
        result = apply_disaster_access_envelopes(
            DisasterAccessPacket(
                snapshot=snapshot,
                envelopes=[self._envelope()],
                movement_requests=[self._movement(weight=9)],
            ),
            base,
        )

        self.assertEqual(result.movement_admissibility[0].status, "conditionally_admissible")
        self.assertTrue(any(f.stage == "route" and f.need_id == "food-need" for f in result.findings))
        self.assertTrue(any(r.need_id == "food-need" for r in result.proposed_reservations))
        self.assertIn("conditional_movement_admissibility", [f.problem_class for f in result.findings])

    def test_reported_envelope_cannot_cancel_verified_route(self):
        snapshot = self._routable_snapshot()
        base = assess_safety_payload(snapshot.model_dump(mode="json"))
        result = apply_disaster_access_envelopes(
            DisasterAccessPacket(
                snapshot=snapshot,
                envelopes=[self._envelope(verification="reported")],
                movement_requests=[self._movement(weight=12)],
            ),
            base,
        )

        self.assertEqual(result.movement_admissibility[0].status, "requires_verification")
        self.assertTrue(any(f.stage == "route" and f.need_id == "food-need" for f in result.findings))
        self.assertTrue(any(r.need_id == "food-need" for r in result.proposed_reservations))
        self.assertIn("movement_specific_access_requires_verification", [f.problem_class for f in result.findings])

    def test_missing_weight_is_unknown_not_permission_or_denial(self):
        snapshot = self._routable_snapshot()
        base = assess_safety_payload(snapshot.model_dump(mode="json"))
        result = apply_disaster_access_envelopes(
            DisasterAccessPacket(
                snapshot=snapshot,
                envelopes=[self._envelope()],
                movement_requests=[self._movement(weight=None)],
            ),
            base,
        )
        self.assertEqual(result.movement_admissibility[0].status, "requires_verification")
        self.assertTrue(any(f.stage == "route" for f in result.findings))

    def test_unlisted_vehicle_class_is_unknown_not_denied(self):
        snapshot = self._routable_snapshot()
        base = assess_safety_payload(snapshot.model_dump(mode="json"))
        result = apply_disaster_access_envelopes(
            DisasterAccessPacket(
                snapshot=snapshot,
                envelopes=[self._envelope()],
                movement_requests=[self._movement(weight=8, vehicle_class="eight_wheel")],
            ),
            base,
        )
        self.assertEqual(result.movement_admissibility[0].status, "requires_verification")
        self.assertTrue(any(f.stage == "route" for f in result.findings))

    def test_active_safety_gate_outranks_vehicle_compatibility(self):
        payload = self._routable_snapshot().model_dump(mode="json")
        payload["safety_constraints"] = [
            {
                "constraint_id": "rain-gate",
                "need_id": "food-need",
                "trigger": "heavy_rain",
                "trigger_status": "active",
                "effect": "suspend_use",
                "source_ref": "synthetic:rain-gate",
                "verification_status": "verified",
                "observed_at": AS_OF.isoformat(),
            }
        ]
        payload["access_envelopes"] = [self._envelope().model_dump(mode="json")]
        payload["movement_requests"] = [
            DisasterMovementRequest(
                movement_id="movement-four-wheel",
                need_id="food-need",
                vehicle_class="four_wheel",
            ).model_dump(mode="json")
        ]

        result = assess_disaster_payload(payload)
        self.assertEqual(result.movement_admissibility[0].status, "inadmissible")
        self.assertEqual(result.findings[0].problem_class, "operational_safety_constraint_triggered")
        self.assertFalse(any(f.stage == "route" for f in result.findings))
        self.assertEqual(result.proposed_reservations, [])

    def test_duplicate_vehicle_class_rules_are_rejected(self):
        with self.assertRaises(ValidationError):
            DisasterAccessEnvelope(
                envelope_id="bad",
                need_id="food-need",
                source_ref="synthetic:bad",
                verification_status="verified",
                observed_at=AS_OF,
                traffic_control="normal",
                rules=[
                    VehicleAccessRule(rule_id="a", vehicle_class="four_wheel", effect="allow"),
                    VehicleAccessRule(rule_id="b", vehicle_class="four_wheel", effect="deny"),
                ],
            )


if __name__ == "__main__":
    unittest.main()
