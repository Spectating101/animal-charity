from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.disaster_access import DisasterAccessEnvelope, DisasterMovementRequest, VehicleAccessRule, assess_disaster_payload
from app.disaster_control import DisasterNeed, DisasterSnapshot
from app.interoperability import ExternalRecord, InteroperabilityBundle


AS_OF = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


class DisasterSafetyAccessCompositionTests(unittest.TestCase):
    def _payload(self, *, safety_verification: str, trigger_status: str) -> dict:
        snapshot = DisasterSnapshot(
            incident_id="synthetic-safety-access-composition",
            as_of=AS_OF,
            phase="response",
            interoperability=InteroperabilityBundle(
                bundle_id="synthetic-safety-access-live",
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
        payload = snapshot.model_dump(mode="json")
        payload["safety_constraints"] = [
            {
                "constraint_id": "rain-rule",
                "need_id": "food-need",
                "trigger": "heavy_rain",
                "trigger_status": trigger_status,
                "effect": "suspend_use",
                "source_ref": "synthetic:rain-rule",
                "verification_status": safety_verification,
                "observed_at": AS_OF.isoformat(),
            }
        ]
        payload["access_envelopes"] = [
            DisasterAccessEnvelope(
                envelope_id="route-a-envelope",
                need_id="food-need",
                source_ref="synthetic:route-envelope",
                verification_status="verified",
                observed_at=AS_OF,
                traffic_control="normal",
                rules=[
                    VehicleAccessRule(
                        rule_id="four-wheel",
                        vehicle_class="four_wheel",
                        effect="allow",
                    )
                ],
            ).model_dump(mode="json")
        ]
        payload["movement_requests"] = [
            DisasterMovementRequest(
                movement_id="movement-a",
                need_id="food-need",
                vehicle_class="four_wheel",
            ).model_dump(mode="json")
        ]
        return payload

    def test_unknown_verified_safety_trigger_downgrades_specific_movement_to_verification(self):
        result = assess_disaster_payload(
            self._payload(safety_verification="verified", trigger_status="unknown")
        )
        self.assertEqual(result.movement_admissibility[0].status, "requires_verification")
        classes = [finding.problem_class for finding in result.findings]
        self.assertIn("safety_trigger_state_requires_monitoring", classes)
        self.assertIn("movement_specific_access_requires_verification", classes)
        self.assertTrue(any(f.stage == "route" for f in result.findings))
        self.assertEqual(len(result.proposed_reservations), 1)

    def test_reported_safety_rule_keeps_generic_route_but_specific_movement_requires_verification(self):
        result = assess_disaster_payload(
            self._payload(safety_verification="reported", trigger_status="active")
        )
        self.assertEqual(result.movement_admissibility[0].status, "requires_verification")
        classes = [finding.problem_class for finding in result.findings]
        self.assertIn("reported_safety_constraint_requires_verification", classes)
        self.assertIn("movement_specific_access_requires_verification", classes)
        self.assertTrue(any(f.stage == "route" for f in result.findings))
        self.assertEqual(len(result.proposed_reservations), 1)

    def test_verified_inactive_safety_rule_makes_otherwise_admissible_movement_conditional(self):
        result = assess_disaster_payload(
            self._payload(safety_verification="verified", trigger_status="inactive")
        )
        self.assertEqual(result.movement_admissibility[0].status, "conditionally_admissible")
        classes = [finding.problem_class for finding in result.findings]
        self.assertIn("conditional_operational_safety_constraint", classes)
        self.assertIn("conditional_movement_admissibility", classes)
        self.assertTrue(any(f.stage == "route" for f in result.findings))
        self.assertEqual(len(result.proposed_reservations), 1)

    def test_source_backed_aceh_unknown_rain_state_blocks_admissibility_claim_not_route_state(self):
        payload = json.loads(
            (ROOT / "examples" / "disaster_aceh_access_envelope_2025_12_31.json").read_text(encoding="utf-8")
        )
        source_ref = payload["access_envelopes"][0]["source_ref"]
        payload["safety_constraints"] = [
            {
                "constraint_id": "aceh-heavy-rain-rule",
                "need_id": "aceh-middle-corridor-functional-access",
                "trigger": "heavy_rain_at_vulnerable_points",
                "trigger_status": "unknown",
                "effect": "suspend_use",
                "source_ref": source_ref,
                "verification_status": "corroborated",
                "observed_at": "2025-12-31T23:59:00+07:00",
                "notes": "The operator source states temporary closure may be applied at vulnerable points during heavy rain, but the publication does not establish the trigger state at the decision timestamp.",
            }
        ]

        result = assess_disaster_payload(payload)
        self.assertTrue(result.movement_admissibility)
        self.assertTrue(all(item.status == "requires_verification" for item in result.movement_admissibility))
        classes = [finding.problem_class for finding in result.findings]
        self.assertIn("safety_trigger_state_requires_monitoring", classes)
        self.assertIn("movement_specific_access_requires_verification", classes)


if __name__ == "__main__":
    unittest.main()
