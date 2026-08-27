from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.animal_welfare_control import AnimalObservation, EvidenceTier, WelfareLandscape
from app.preventive_welfare import (
    DeterminantKind,
    DeterminantObservation,
    PreventiveWelfareSnapshot,
    ServiceAccessObservation,
    assess_preventive_system,
    load_preventive_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]


class PreventiveWelfareTests(unittest.TestCase):
    def test_synthetic_source_control_cluster_is_structural_but_not_causally_overclaimed(self):
        snapshot = load_preventive_snapshot(ROOT / "examples" / "zhongli_sanmin_synthetic_preventive_system.json")
        result = assess_preventive_system(snapshot)
        source = [x for x in result.prevention_opportunities if x.intervention_class == "source_control"]
        self.assertEqual(len(source), 3)
        self.assertTrue(all(x.structural_candidate for x in source))
        self.assertTrue(all(x.causal_status == "hypothesis" for x in source))
        self.assertTrue(any(g["service_kind"] == "sterilization_registration_outreach" for g in result.access_gaps))
        self.assertTrue(any("service-access" in x.lower() for x in result.research_signals))

    def test_area_context_does_not_become_supported_cause(self):
        landscape = WelfareLandscape(
            area_id="a",
            area_name="A",
            observations=[
                AnimalObservation(
                    observation_id="state",
                    area_id="a",
                    subject_ref="dog-1",
                    species="dog",
                    signal="welfare_state",
                    value="owned_at_risk",
                    source_ref="partner:state",
                    source_tier=EvidenceTier.partner,
                ),
                AnimalObservation(
                    observation_id="risk",
                    area_id="a",
                    subject_ref="dog-1",
                    species="dog",
                    signal="owner_retention_risk",
                    value=True,
                    source_ref="partner:risk",
                    source_tier=EvidenceTier.partner,
                ),
                AnimalObservation(
                    observation_id="crisis",
                    area_id="a",
                    subject_ref="dog-1",
                    species="dog",
                    signal="owner_crisis_type",
                    value="medical_cost",
                    source_ref="partner:crisis",
                    source_tier=EvidenceTier.partner,
                ),
            ],
        )
        snapshot = PreventiveWelfareSnapshot(
            area_id="a",
            area_name="A",
            landscape=landscape,
            determinants=[
                DeterminantObservation(
                    observation_id="income-context",
                    area_id="a",
                    determinant=DeterminantKind.income,
                    value="low area median income",
                    source_ref="official:area-income",
                    source_tier=EvidenceTier.official,
                    scope="area",
                    relationship="context",
                )
            ],
        )
        result = assess_preventive_system(snapshot)
        self.assertEqual(result.prevention_opportunities[0].causal_status, "context_only")
        self.assertTrue(any("causal" in gap.lower() for gap in result.data_gaps))

    def test_subject_level_established_barrier_can_support_prevention(self):
        landscape = WelfareLandscape(
            area_id="a",
            area_name="A",
            observations=[
                AnimalObservation(
                    observation_id="state",
                    area_id="a",
                    subject_ref="dog-1",
                    species="dog",
                    signal="welfare_state",
                    value="owned_at_risk",
                    source_ref="partner:state",
                    source_tier=EvidenceTier.partner,
                ),
                AnimalObservation(
                    observation_id="risk",
                    area_id="a",
                    subject_ref="dog-1",
                    species="dog",
                    signal="owner_retention_risk",
                    value=True,
                    source_ref="partner:risk",
                    source_tier=EvidenceTier.partner,
                ),
                AnimalObservation(
                    observation_id="crisis",
                    area_id="a",
                    subject_ref="dog-1",
                    species="dog",
                    signal="owner_crisis_type",
                    value="medical_cost",
                    source_ref="partner:crisis",
                    source_tier=EvidenceTier.partner,
                ),
            ],
        )
        snapshot = PreventiveWelfareSnapshot(
            area_id="a",
            area_name="A",
            landscape=landscape,
            determinants=[
                DeterminantObservation(
                    observation_id="vet-cost",
                    area_id="a",
                    determinant=DeterminantKind.veterinary_access,
                    value="quoted treatment unaffordable without assistance",
                    source_ref="professional:quote-and-owner-assessment",
                    source_tier=EvidenceTier.professional,
                    scope="subject",
                    subject_ref="dog-1",
                    relationship="established",
                )
            ],
            service_access=[
                ServiceAccessObservation(
                    observation_id="vet-access",
                    area_id="a",
                    service_kind="veterinary_care",
                    source_ref="professional:vet-access",
                    source_tier=EvidenceTier.professional,
                    available=True,
                    affordable=False,
                    geographically_accessible=True,
                    transport_feasible=True,
                    information_accessible=True,
                    capacity_available=True,
                )
            ],
        )
        result = assess_preventive_system(snapshot)
        opp = result.prevention_opportunities[0]
        self.assertEqual(opp.causal_status, "supported")
        self.assertEqual({x.value for x in opp.one_welfare_domains}, {"animal", "human"})
        self.assertIn("stable_owned_to_relinquishment_or_abandonment", opp.transition_type)
        self.assertTrue(result.access_gaps)

    def test_human_transfer_boundary_is_explicit(self):
        snapshot = PreventiveWelfareSnapshot(
            area_id="a",
            area_name="A",
            landscape=WelfareLandscape(area_id="a", area_name="A"),
        )
        result = assess_preventive_system(snapshot)
        self.assertIn("rights", result.transfer_boundary)
        self.assertIn("autonomy", result.transfer_boundary)
        self.assertIn("must not be transferred", result.transfer_boundary)


if __name__ == "__main__":
    unittest.main()
