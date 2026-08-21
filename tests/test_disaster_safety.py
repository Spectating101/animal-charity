from __future__ import annotations

import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.disaster_control import DisasterNeed, DisasterSnapshot
from app.disaster_safety import (
    DisasterSafetyConstraint,
    DisasterSafetyPacket,
    apply_disaster_safety_constraints,
)
from app.disaster_dependencies import assess_disaster_payload
from app.interoperability import ExternalRecord, InteroperabilityBundle


AS_OF = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)


class DisasterSafetyTests(unittest.TestCase):
    def _routable_snapshot(self) -> DisasterSnapshot:
        return DisasterSnapshot(
            incident_id="synthetic-safety-incident",
            as_of=AS_OF,
            phase="response",
            interoperability=InteroperabilityBundle(
                bundle_id="synthetic-live-operations",
                as_of=AS_OF,
                resource_inventory_scope="partial",
                service_registry_scope="unknown",
                records=[
                    ExternalRecord(
                        record_id="rescue-a",
                        system_id="synthetic-eoc",
                        integration_role="operations_platform",
                        kind="capability_resource",
                        source_ref="synthetic:rescue-a",
                        source_kind="operator",
                        observed_at=AS_OF,
                        verification_status="verified",
                        sensitivity="internal",
                        attributes={
                            "resource_type": "urban_search_and_rescue_team",
                            "capabilities": ["search_and_rescue"],
                            "availability": "available",
                            "deployment_state": "staged",
                            "location_ref": "base-a"
                        },
                    )
                ],
            ),
            needs=[
                DisasterNeed(
                    need_id="rescue-need",
                    location_ref="zone-a",
                    category="life_safety",
                    priority="critical",
                    status="unmet",
                    source_ref="synthetic:need",
                    verification_status="corroborated",
                    observed_at=AS_OF,
                    access_status="open",
                    required_capabilities=["search_and_rescue"],
                )
            ],
        )

    def _constraint(self, *, verification: str = "verified", trigger_status: str = "active") -> DisasterSafetyConstraint:
        return DisasterSafetyConstraint(
            constraint_id="weather-gate",
            need_id="rescue-need",
            trigger="unsafe_weather",
            trigger_status=trigger_status,
            effect="suspend_use",
            source_ref="synthetic:safety-rule",
            verification_status=verification,
            observed_at=AS_OF,
        )

    def test_verified_active_safety_gate_beats_valid_route_and_reservation(self):
        snapshot = self._routable_snapshot()
        base = assess_disaster_payload(snapshot.model_dump(mode="json"))
        self.assertTrue(any(f.stage == "route" and f.need_id == "rescue-need" for f in base.findings))
        self.assertTrue(any(r.need_id == "rescue-need" for r in base.proposed_reservations))

        packet = DisasterSafetyPacket(snapshot=snapshot, constraints=[self._constraint()])
        result = apply_disaster_safety_constraints(packet, base)
        classes = [f.problem_class for f in result.findings if f.need_id == "rescue-need"]

        self.assertEqual(result.findings[0].stage, "safety")
        self.assertIn("operational_safety_constraint_triggered", classes)
        self.assertFalse(any(f.stage == "route" and f.need_id == "rescue-need" for f in result.findings))
        self.assertFalse(any(r.need_id == "rescue-need" for r in result.proposed_reservations))

    def test_reported_safety_gate_cannot_cancel_verified_route(self):
        snapshot = self._routable_snapshot()
        base = assess_disaster_payload(snapshot.model_dump(mode="json"))
        packet = DisasterSafetyPacket(snapshot=snapshot, constraints=[self._constraint(verification="reported")])
        result = apply_disaster_safety_constraints(packet, base)
        classes = [f.problem_class for f in result.findings if f.need_id == "rescue-need"]

        self.assertIn("reported_safety_constraint_requires_verification", classes)
        self.assertTrue(any(f.stage == "route" and f.need_id == "rescue-need" for f in result.findings))
        self.assertTrue(any(r.need_id == "rescue-need" for r in result.proposed_reservations))

    def test_inactive_verified_constraint_preserves_conditional_usability(self):
        snapshot = DisasterSnapshot(
            incident_id="synthetic-open-route",
            as_of=AS_OF,
            phase="response",
            interoperability=InteroperabilityBundle(
                bundle_id="synthetic-route-state",
                as_of=AS_OF,
                resource_inventory_scope="unknown",
                service_registry_scope="unknown",
                records=[],
            ),
            needs=[
                DisasterNeed(
                    need_id="open-route",
                    location_ref="route-a",
                    category="access",
                    priority="urgent",
                    status="met",
                    source_ref="synthetic:open-route",
                    verification_status="corroborated",
                    observed_at=AS_OF,
                    access_status="open",
                )
            ],
        )
        constraint = DisasterSafetyConstraint(
            constraint_id="rain-rule",
            need_id="open-route",
            trigger="rainfall_on_unstable_slope",
            trigger_status="inactive",
            effect="suspend_use",
            source_ref="synthetic:rain-rule",
            verification_status="corroborated",
            observed_at=AS_OF,
        )
        base = assess_disaster_payload(snapshot.model_dump(mode="json"))
        result = apply_disaster_safety_constraints(
            DisasterSafetyPacket(snapshot=snapshot, constraints=[constraint]),
            base,
        )

        self.assertEqual([f.problem_class for f in result.findings], ["conditional_operational_safety_constraint"])
        self.assertEqual(result.findings[0].stage, "safety")
        self.assertEqual(result.proposed_reservations, [])

    def test_safety_constraint_requires_known_need(self):
        snapshot = self._routable_snapshot()
        bad = self._constraint().model_copy(update={"need_id": "missing"})
        with self.assertRaises(ValidationError):
            DisasterSafetyPacket(snapshot=snapshot, constraints=[bad])


if __name__ == "__main__":
    unittest.main()
