from __future__ import annotations

import unittest
from pathlib import Path

from app.animal_welfare_control import (
    AnimalObservation,
    EvidenceTier,
    Species,
    WelfareLandscape,
    assess_area,
    load_landscape,
    route_subject,
)

ROOT = Path(__file__).resolve().parents[1]


class AnimalWelfareControlTests(unittest.TestCase):
    def test_policy_priority_alone_does_not_create_animal_case(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_policy_baseline.json")
        assessment = assess_area(landscape)
        self.assertEqual(assessment.decisions, [])
        self.assertIn("No animal-level intervention", assessment.safe_conclusion)
        self.assertTrue(assessment.data_gaps)

    def test_synthetic_lost_owned_dog_routes_to_reunification(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json")
        decisions = route_subject(landscape, "synthetic-dog-lost")
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].intervention_class, "reunification")
        self.assertEqual(decisions[0].actuator, "reunification.owner_handoff")
        self.assertEqual(decisions[0].intended_transition.value, "owned_stable")

    def test_owner_crisis_prefers_retention_over_shelter_intake(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json")
        decision = route_subject(landscape, "synthetic-dog-owner-crisis")[0]
        self.assertEqual(decision.intervention_class, "owner_retention")
        self.assertEqual(decision.actuator, "owner_support.veterinary_gap")
        self.assertEqual(decision.intended_transition.value, "owned_stable")

    def test_reproductive_roaming_dogs_create_source_control_signal(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json")
        assessment = assess_area(landscape)
        source = [d for d in assessment.decisions if d.intervention_class == "source_control"]
        self.assertEqual(len(source), 3)
        structural = [s for s in assessment.structural_signals if s["intervention_class"] == "source_control"]
        self.assertEqual(len(structural), 1)
        self.assertIn("sterilization", structural[0]["proposal"].lower())

    def test_ecology_sensitive_roaming_dog_is_not_auto_returned(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json")
        decisions = route_subject(landscape, "synthetic-dog-r3")
        source = [d for d in decisions if d.intervention_class == "source_control"][0]
        self.assertIsNone(source.intended_transition)
        self.assertTrue(any("ecologically" in g for g in source.welfare_guardrails))

    def test_foster_path_is_available_before_building_more_shelter(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json")
        decisions = route_subject(landscape, "synthetic-dog-foster")
        foster = [d for d in decisions if d.intervention_class == "foster_to_adoption"]
        self.assertEqual(len(foster), 1)
        self.assertEqual(foster[0].actuator, "placement.foster_match")
        self.assertEqual(foster[0].intended_transition.value, "foster")

    def test_specialist_work_is_referral_only(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json")
        decisions = route_subject(landscape, "synthetic-dog-specialist")
        specialist = [d for d in decisions if d.intervention_class == "specialist_referral"]
        self.assertEqual(len(specialist), 1)
        self.assertTrue(specialist[0].specialist_referral_only)
        self.assertEqual(specialist[0].actuator, "specialist.referral_only")
        self.assertTrue(any("never needs to work" in g for g in specialist[0].welfare_guardrails))

    def test_injury_preempts_specialist_or_population_optimization(self):
        landscape = load_landscape(ROOT / "examples" / "zhongli_sanmin_synthetic_lifecycle.json")
        decisions = route_subject(landscape, "synthetic-dog-emergency")
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].intervention_class, "rescue_stabilize")
        self.assertEqual(decisions[0].priority, "critical")

    def test_specialist_candidate_requires_all_observed_traits(self):
        area = "test-area"
        subject = "dog-partial"
        rows = [
            AnimalObservation(observation_id="s", area_id=area, subject_ref=subject, species=Species.dog, signal="welfare_state", value="foster", source_ref="test://state", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="m", area_id=area, subject_ref=subject, species=Species.dog, signal="medical_stable", value=True, source_ref="test://m", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="h", area_id=area, subject_ref=subject, species=Species.dog, signal="human_social", value=True, source_ref="test://h", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="f", area_id=area, subject_ref=subject, species=Species.dog, signal="low_fear_in_public", value=True, source_ref="test://f", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="r", area_id=area, subject_ref=subject, species=Species.dog, signal="low_reactivity", value=False, source_ref="test://r", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="t", area_id=area, subject_ref=subject, species=Species.dog, signal="enjoys_training", value=True, source_ref="test://t", source_tier=EvidenceTier.synthetic, synthetic=True),
        ]
        decisions = route_subject(WelfareLandscape(area_id=area, area_name="Test", observations=rows), subject)
        self.assertFalse(any(d.intervention_class == "specialist_referral" for d in decisions))

    def test_cat_source_control_uses_cat_specific_policy(self):
        area = "cat-area"
        subject = "cat-1"
        rows = [
            AnimalObservation(observation_id="s", area_id=area, subject_ref=subject, species=Species.cat, signal="welfare_state", value="community_cared", source_ref="test://state", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="r", area_id=area, subject_ref=subject, species=Species.cat, signal="reproductively_active", value=True, source_ref="test://repro", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="c", area_id=area, subject_ref=subject, species=Species.cat, signal="responsible_community_caretaker", value=True, source_ref="test://care", source_tier=EvidenceTier.synthetic, synthetic=True),
            AnimalObservation(observation_id="e", area_id=area, subject_ref=subject, species=Species.cat, signal="ecology_sensitive_location", value=False, source_ref="test://eco", source_tier=EvidenceTier.synthetic, synthetic=True),
        ]
        decision = route_subject(WelfareLandscape(area_id=area, area_name="Test", observations=rows), subject)[0]
        self.assertEqual(decision.actuator, "community_cat.tnvr_managed_care")


if __name__ == "__main__":
    unittest.main()
