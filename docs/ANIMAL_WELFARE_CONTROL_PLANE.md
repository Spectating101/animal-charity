# Regional Animal-Welfare Control Plane

## Thesis

The product is **not** a shelter database, foster marketplace, food bank, TNR app, or working-dog programme.

Those functions already exist in the animal-welfare ecosystem. The control-plane hypothesis is narrower and more systemic:

> Given evidence about an area's animals, people, services and outcomes, can a persistent bounded agent identify which welfare transition is failing, route cases into existing interventions first, detect recurring structural gaps, and propose the smallest missing public-good initiative without optimizing away animal welfare?

## Lifecycle model

```text
prevent new unmanaged animals
        ↓
owner support / identification / sterilization
        ↓
lost / roaming / surrendered / unowned animal
        ↓
acute safety + health stabilization
        ↓
ownership / ecology / behaviour / reproductive assessment
        ↓
┌──────────────┬──────────────┬──────────────┬─────────────────┐
│ reunification│ owner-retain │ foster/adopt │ managed community│
└──────────────┴──────────────┴──────────────┴─────────────────┘
                         ↓
              stable welfare integration
                         ↓
         specialist referral for a small suitable subset
```

The specialist branch is deliberately last. A dog does not need a social/working role to justify rescue or care.

## Intervention priority

1. **Acute welfare / immediate public safety** — authorized rescue and stabilization overrides optimization.
2. **Prevent new stray recruitment** — reproductive source control, registration/responsible ownership and locally appropriate community management.
3. **Reunify or retain safe homes** — avoid unnecessary shelter intake when a lawful safe owner relationship can be preserved.
4. **Stabilize basic welfare** — health, food, safe custody and required recovery.
5. **Foster / adoption / sanctuary / appropriate community pathway** — choose a stable welfare-positive life, not merely removal from the street.
6. **Specialist social/working referral** — only for animals with positive longitudinal evidence and independent professional acceptance.

Machine-readable policy lives at `config/missions/animal_welfare_integration.json`.

## Evidence rules

Area policy context is not animal-level evidence. A priority zone may justify monitoring and programme eligibility, but cannot establish that any particular animal is unowned, aggressive, intact, sick, adoptable or suitable for return/placement.

The v0 router therefore consumes explicit observations such as:

- `welfare_state`
- `ownership_known` / `owner_contactable`
- `owner_retention_risk` / `owner_crisis_type`
- `acute_distress` / `injured` / `immediate_public_safety_risk`
- `sterilized` / `reproductively_active`
- `responsible_community_caretaker`
- `ecology_sensitive_location`
- `adoption_suitable` / `foster_available`
- `medical_stable`
- specialist-referral observations (`human_social`, `low_fear_in_public`, `low_reactivity`, `enjoys_training`)

Unknown facts remain unknown.

## Existing field precedents

This architecture intentionally composes existing practice rather than claiming to invent it:

- Taiwan MOA's 2026 roaming-dog community-management programme emphasizes risk hotspots, female source control, community participation, responsible ownership and accountable community care: https://animal.moa.gov.tw/Frontend/News/Detail/N0000000002234
- HASS develops lost-pet reunification, intake triage, supported self-rehoming, foster-centric programming, community-cat programmes and ecosystem mapping: https://resources.humananimalsupportservices.org/
- Shelterluv already provides organization-level field/community-service software for animal control, TNR, food pantries, medical services, behaviour, transport and rehoming: https://www.shelterluv.com/product/field-services/
- Taiwan Heart Assistance Dog Training Team already selects and trains suitable former stray dogs for animal-assisted education/social support and uses structured assessment/training: https://startup.sme.gov.tw/sitaiwan/Home/Org?Fid=684

The opportunity, if validated, is the **cross-organization regional diagnosis + control layer**, not duplicating those programmes.

## Control decisions currently implemented

| Observed situation | v0 route |
|---|---|
| injury / acute distress / immediate safety risk | `rescue.authorized_dispatch` |
| lost or roaming owned animal + contactable owner | `reunification.owner_handoff` |
| safe owner relationship at risk from solvable hardship | targeted `owner_support.*` |
| reproductively active free-roaming dog | `population.sterilize_register_manage` |
| community cat reproduction | cat-specific managed TNVR/site assessment |
| placement-suitable animal + foster available | `placement.foster_match` |
| placement-suitable animal + no foster | `placement.recruit_foster` |
| highly suitable dog for specialist work | `specialist.referral_only` |
| insufficient evidence | `evidence.request` |

## Structural learning

`assess_area()` aggregates repeated transition failures across subjects. Three or more observed failures in the same intervention class produce a **structural signal**, for example repeated `source_control` cases -> evaluate a targeted sterilization/registration/community-management initiative.

A structural signal is not permission to launch. Temporal recurrence, service coverage, host/capacity evidence and human authority still pass through the structural initiative planner.

## Success metric

The control plane should eventually optimize **stable welfare integration**, not raw intake, removal, adoption, sterilization or working-dog counts.

Useful outcome families include:

- new unmanaged-animal recruitment;
- owner relinquishment prevented;
- lost animals reunited;
- intact breeding animals in priority landscapes;
- unresolved welfare time;
- shelter length of stay;
- foster capacity and successful placements;
- return/relinquishment after placement;
- responsibly managed community animals where appropriate;
- human-safety and wildlife-conflict events;
- specialist referrals accepted and completed **without animal-welfare compromise**.

## v0 limitation

This is decision-support and programme-planning software. It is not a veterinary system, legal authority, animal-control officer, dangerousness evaluator, adoption authority or assistance-dog certifier.
