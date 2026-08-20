from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.interoperability import ExternalRecord, InteroperabilityBundle, build_control_plane_packet


ROOT = Path(__file__).resolve().parents[1]


class InteroperabilityTests(unittest.TestCase):
    def _load(self, name: str) -> InteroperabilityBundle:
        payload = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
        return InteroperabilityBundle.model_validate(payload)

    def test_wildfire_bundle_separates_verified_resources_from_reported_candidates(self):
        packet = build_control_plane_packet(self._load("interop_kalimantan_synthetic.json"))
        self.assertEqual(packet.hazards[0].hazard_type, "wildfire")
        self.assertEqual(len(packet.deployable_resources), 1)
        self.assertEqual(packet.deployable_resources[0].resource_type, "ground_fire_suppression_team")
        self.assertEqual(len(packet.resource_candidates_requiring_verification), 1)
        self.assertEqual(packet.resource_candidates_requiring_verification[0].resource_type, "water_bombing_aircraft")
        self.assertEqual(len(packet.command_contexts), 1)
        self.assertTrue(any("requires verification" in warning for warning in packet.warnings))

    def test_earthquake_bundle_does_not_treat_committed_resource_as_available(self):
        packet = build_control_plane_packet(self._load("interop_ntt_synthetic.json"))
        resource_types = [resource.resource_type for resource in packet.deployable_resources]
        self.assertIn("urban_search_and_rescue_team", resource_types)
        self.assertNotIn("potable_water_tanker", resource_types)
        self.assertIn("stale-road-report", packet.stale_record_ids)
        self.assertTrue(any("stale" in warning for warning in packet.warnings))

    def test_stale_hazard_and_command_context_are_not_current_operational_state(self):
        bundle = InteroperabilityBundle.model_validate(
            {
                "bundle_id": "stale-test",
                "as_of": "2026-08-20T07:00:00Z",
                "records": [
                    {
                        "record_id": "old-hazard",
                        "system_id": "nasa_firms",
                        "integration_role": "evidence_source",
                        "kind": "hazard_observation",
                        "source_ref": "synthetic:old-hazard",
                        "source_kind": "sensor",
                        "observed_at": "2026-08-20T01:00:00Z",
                        "valid_until": "2026-08-20T03:00:00Z",
                        "attributes": {"hazard_type": "wildfire", "location_ref": "zone-a"}
                    },
                    {
                        "record_id": "old-command",
                        "system_id": "nims",
                        "integration_role": "authority_framework",
                        "kind": "command_context",
                        "source_ref": "synthetic:old-command",
                        "source_kind": "official",
                        "observed_at": "2026-08-20T01:00:00Z",
                        "valid_until": "2026-08-20T03:00:00Z",
                        "attributes": {"incident_id": "incident-a", "authority_ref": "eoc-a"}
                    }
                ]
            }
        )
        packet = build_control_plane_packet(bundle)
        self.assertEqual(packet.hazards, [])
        self.assertEqual(packet.command_contexts, [])
        self.assertIn("old-hazard", packet.stale_record_ids)
        self.assertIn("old-command", packet.stale_record_ids)
        self.assertTrue(any("No current command/authority context" in warning for warning in packet.warnings))

    def test_contracting_process_is_integrity_reference_not_corruption_finding(self):
        bundle = InteroperabilityBundle.model_validate(
            {
                "bundle_id": "contract-test",
                "as_of": "2026-08-20T07:00:00Z",
                "records": [
                    {
                        "record_id": "contract-1",
                        "system_id": "ocds",
                        "integration_role": "integrity_standard",
                        "kind": "contracting_process",
                        "source_ref": "synthetic:ocds:ocid-1",
                        "source_kind": "transaction",
                        "observed_at": "2026-08-20T06:00:00Z",
                        "verification_status": "verified",
                        "sensitivity": "internal",
                        "attributes": {
                            "ocid": "ocds-test-1",
                            "stage": "implementation",
                            "implementation_status": "active"
                        }
                    }
                ]
            }
        )
        packet = build_control_plane_packet(bundle)
        self.assertEqual(packet.integrity_processes[0].ocid, "ocds-test-1")
        self.assertTrue(any("cannot by itself establish corruption" in warning for warning in packet.warnings))
        self.assertTrue(any("No current command/authority context" in warning for warning in packet.warnings))

    def test_authority_framework_cannot_masquerade_as_resource_inventory(self):
        with self.assertRaises(ValidationError):
            ExternalRecord.model_validate(
                {
                    "record_id": "bad-resource",
                    "system_id": "nims",
                    "integration_role": "authority_framework",
                    "kind": "capability_resource",
                    "source_ref": "synthetic:nims:bad",
                    "observed_at": "2026-08-20T06:00:00Z",
                    "attributes": {"resource_type": "helicopter", "availability": "available"}
                }
            )

    def test_packet_exports_evidence_manifest_without_upgrading_source_strength(self):
        packet = build_control_plane_packet(self._load("interop_kalimantan_synthetic.json"))
        by_ref = {entry.source_ref: entry for entry in packet.evidence_manifest}
        candidate = by_ref["synthetic:mutual-aid:aircraft-a"]
        self.assertEqual(candidate.verification_status, "reported")
        self.assertEqual(candidate.source_kind, "partner")

    def test_duplicate_source_refs_are_deduplicated_in_manifest(self):
        bundle = InteroperabilityBundle.model_validate(
            {
                "bundle_id": "dedupe-test",
                "as_of": "2026-08-20T07:00:00Z",
                "records": [
                    {
                        "record_id": "outcome-1",
                        "system_id": "nocturnal",
                        "integration_role": "memory_archive",
                        "kind": "outcome_observation",
                        "source_ref": "synthetic:shared-source",
                        "observed_at": "2026-08-20T06:00:00Z"
                    },
                    {
                        "record_id": "outcome-2",
                        "system_id": "nocturnal",
                        "integration_role": "memory_archive",
                        "kind": "outcome_observation",
                        "source_ref": "synthetic:shared-source",
                        "observed_at": "2026-08-20T06:10:00Z"
                    }
                ]
            }
        )
        packet = build_control_plane_packet(bundle)
        self.assertEqual(len(packet.evidence_manifest), 1)
        self.assertTrue(any("deduplicated" in warning for warning in packet.warnings))

    def test_bundle_requires_timezone_aware_as_of(self):
        bundle = self._load("interop_kalimantan_synthetic.json")
        bundle.as_of = datetime(2026, 8, 20, 7, 0, 0)
        with self.assertRaises(ValueError):
            build_control_plane_packet(bundle)


if __name__ == "__main__":
    unittest.main()
