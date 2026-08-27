from __future__ import annotations

import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.disaster_control import DisasterNeed, DisasterSnapshot
from app.disaster_dependencies import (
    DisasterDependencyLink,
    DisasterDependencyPacket,
    apply_disaster_dependencies,
)
from app.interoperability import InteroperabilityBundle


AS_OF = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


class DisasterDependencyTests(unittest.TestCase):
    def _snapshot(self) -> DisasterSnapshot:
        return DisasterSnapshot(
            incident_id="synthetic-dependency-incident",
            as_of=AS_OF,
            phase="response",
            interoperability=InteroperabilityBundle(
                bundle_id="synthetic-complete-inventory",
                as_of=AS_OF,
                resource_inventory_scope="complete_for_scope",
                service_registry_scope="complete_for_scope",
                records=[],
            ),
            needs=[
                DisasterNeed(
                    need_id="road",
                    location_ref="zone-a",
                    category="access",
                    priority="critical",
                    status="unmet",
                    source_ref="synthetic:road",
                    verification_status="corroborated",
                    observed_at=AS_OF,
                    access_status="isolated",
                    required_capabilities=["road_clearance"],
                ),
                DisasterNeed(
                    need_id="power",
                    location_ref="zone-a",
                    category="power",
                    priority="urgent",
                    status="partially_met",
                    source_ref="synthetic:power",
                    verification_status="corroborated",
                    observed_at=AS_OF,
                    capacity_status="constrained",
                    required_capabilities=["generator_support"],
                ),
            ],
        )

    def _link(self, verification_status: str = "corroborated") -> DisasterDependencyLink:
        return DisasterDependencyLink(
            link_id="road-fuel-power",
            upstream_need_id="road",
            downstream_need_id="power",
            relation="degrades",
            mechanism="road_closure_interrupts_generator_fuel_delivery",
            source_ref="synthetic:dependency",
            verification_status=verification_status,
            observed_at=AS_OF,
        )

    def test_established_dependency_replaces_false_downstream_capacity_story(self):
        packet = DisasterDependencyPacket(snapshot=self._snapshot(), dependencies=[self._link()])
        result = apply_disaster_dependencies(packet)
        power = [finding for finding in result.findings if finding.need_id == "power"]
        classes = [finding.problem_class for finding in power]

        self.assertIn("power_blocked_by_upstream_dependency", classes)
        self.assertNotIn("power_capacity_gap", classes)
        self.assertFalse(any(r.need_id == "power" for r in result.proposed_reservations))

    def test_reported_dependency_does_not_suppress_independent_diagnosis(self):
        packet = DisasterDependencyPacket(snapshot=self._snapshot(), dependencies=[self._link("reported")])
        result = apply_disaster_dependencies(packet)
        power = [finding for finding in result.findings if finding.need_id == "power"]
        classes = [finding.problem_class for finding in power]

        self.assertIn("power_capacity_gap", classes)
        self.assertIn("reported_dependency_requires_verification", classes)
        self.assertNotIn("power_blocked_by_upstream_dependency", classes)

    def test_dependency_graph_rejects_cycles(self):
        snapshot = self._snapshot()
        reverse = DisasterDependencyLink(
            link_id="power-road",
            upstream_need_id="power",
            downstream_need_id="road",
            relation="degrades",
            mechanism="synthetic_reverse_dependency",
            source_ref="synthetic:reverse",
            verification_status="corroborated",
            observed_at=AS_OF,
        )
        with self.assertRaises(ValidationError):
            DisasterDependencyPacket(snapshot=snapshot, dependencies=[self._link(), reverse])

    def test_dependency_requires_known_need_ids(self):
        bad = self._link().model_copy(update={"upstream_need_id": "missing"})
        with self.assertRaises(ValidationError):
            DisasterDependencyPacket(snapshot=self._snapshot(), dependencies=[bad])


if __name__ == "__main__":
    unittest.main()
