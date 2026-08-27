# Regional Animal-Welfare Control Plane

## Thesis

The product is **not** a shelter database, foster marketplace, food bank, TNR app, veterinary system, or working-dog programme.

Those functions already exist in the animal-welfare ecosystem. The control-plane hypothesis is more systemic:

> Given evidence about an area's animals, households, services, access barriers, environment and outcomes, can a persistent bounded agent identify which welfare transition is failing, determine whether the failure is scarcity/access/coordination/household/institutional, route existing interventions first, detect recurring structural gaps, and propose the smallest preventive public-good initiative without optimizing away welfare or human rights?

The research foundation is documented in [`PREVENTIVE_WELFARE_RESEARCH.md`](PREVENTIVE_WELFARE_RESEARCH.md).

## Consolidated model

```text
ONE WELFARE / SYSTEM CONTEXT
human household · animal state · services · environment
                    ↓
        PREVENTIVE WELFARE LAYER
What bad-state transition is becoming likely?
What determinant/access barrier is actually evidenced?
                    ↓
            LIFECYCLE ROUTER
acute rescue · reunification · owner retention · source control
foster/adoption · responsible community care · specialist referral
                    ↓
              OUTCOME EVIDENCE
Did the animal reach a more stable welfare state?
                    ↓
            RECURRENCE DETECTION
Is the same transition repeatedly failing?
                    ↓
          STRUCTURAL INITIATIVE PLANNER
existing-service extension → reversible pilot → permanent only after proof
                    ↓
            POPULATION EVALUATION
Did welfare/public-safety/ecological outcomes actually improve?
```

## Preventable bad-state transitions

The primary analytical object is increasingly the transition, not merely the current bad state.

Examples:

```text
owned_stable
  → household / vet / housing shock
  → owned_at_risk
  → relinquishment / abandonment
```

```text
reproductively active free-roaming animals
  → unmanaged reproduction
  → new unmanaged animals
```

```text
placement-ready animal
  → missing foster capacity
  → prolonged unstable care
  → delayed or failed integration
```

The control plane should prefer preventing a transition when credible evidence supports doing so, rather than waiting until the downstream crisis becomes expensive and difficult to reverse.

## Social and service determinants

`app/preventive_welfare.py` adds structured context for:

- income/affordability;
- housing;
- transportation;
- veterinary access;
- food access;
- information/language access;
- social support;
- service and foster capacity;
- population-control access;
- owner health/time capacity;
- public-safety and ecological context.

These are **not guilt variables**.

The causal vocabulary is deliberately constrained:

- `context` — area/correlational evidence; may prioritize investigation only;
- `hypothesis` — plausible case-linked driver still requiring verification;
- `established` — sufficiently direct evidence for bounded operational use.

Area deprivation can never by itself establish an individual owner's neglect, motives, ability or culpability.

## Welfare deserts / access decomposition

Service access is represented using separate dimensions:

- available?
- affordable?
- geographically accessible?
- transport feasible?
- information accessible?
- capacity available?

This allows the engine to distinguish:

`service absent`

from:

`service exists but cannot actually be used`.

That distinction applies to veterinary care, sterilization, food support, foster capacity, transport, rescue response and future actuators.

## Lifecycle priority

1. **Acute welfare / immediate public safety** — authorized rescue and stabilization overrides optimization.
2. **Prevent an evidenced bad-state transition** — intervene before avoidable surrender, unmanaged reproduction, prolonged unstable care or other severe deterioration.
3. **Prevent new stray recruitment** — reproductive source control, identification/responsible ownership and locally appropriate community management.
4. **Repair access to existing capability** — affordability, geography, transport, information or capacity may be the actual bottleneck.
5. **Reunify or retain safe homes** — avoid unnecessary shelter intake when a lawful safe relationship can be preserved.
6. **Stabilize basic welfare** — health, food, safe custody and recovery.
7. **Foster / adoption / sanctuary / appropriate community pathway** — choose a stable welfare-positive life, not merely removal from the street.
8. **Specialist social/working referral** — only for animals with positive longitudinal evidence and independent professional acceptance.
9. **Verify outcome and recurrence** — no transaction counts as success until the downstream welfare state is known.

Machine-readable policy lives at `config/missions/animal_welfare_integration.json`.

## Evidence rules

Area policy context is not animal-level evidence. A priority zone may justify monitoring/programme eligibility, but cannot establish that a particular animal is unowned, aggressive, intact, sick, adoptable or suitable for return/placement.

Likewise:

- low-income area is not evidence of individual neglect;
- existence of a service is not evidence of access;
- one adoption is not evidence of stable placement;
- fewer reports are not evidence of fewer roaming animals if observation coverage deteriorated.

Unknown facts remain unknown.

## Existing field precedents

The project intentionally composes existing practice rather than claiming to invent it:

- Taiwan MOA roaming-dog community management emphasizes risk hotspots, source control, community participation and responsible ownership: https://animal.moa.gov.tw/Frontend/News/Detail/N0000000002234
- HASS develops reunification, intake triage/diversion, supported self-rehoming, foster-centric programming, community-cat programmes and ecosystem mapping: https://resources.humananimalsupportservices.org/
- Shelterluv provides organization-level field/community-service software for animal control, TNR, food pantries, medical services, behaviour, transport and rehoming: https://www.shelterluv.com/product/field-services/
- Taiwan Heart Assistance Dog Training Team selects/trains suitable former stray dogs for animal-assisted education/social support: https://startup.sme.gov.tw/sitaiwan/Home/Org?Fid=684

The opportunity, if validated, is the **cross-organization regional evidence/diagnosis/prevention/control layer**.

## Literature-grounded research foundations

The preventive architecture is anchored in adjacent research on:

- One Welfare;
- social determinants of companion-animal welfare;
- animal welfare deserts and veterinary-access barriers;
- shelter-intake diversion / owner retention;
- dog-population-management systems and weak socio-economic evaluation.

See [`PREVENTIVE_WELFARE_RESEARCH.md`](PREVENTIVE_WELFARE_RESEARCH.md) and `config/research/preventive_welfare_framework.json` for references and machine-readable hypotheses.

## Current decision surfaces

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

The preventive systems endpoint adds root-context/access reasoning around these routes:

`POST /v1/welfare/system/assess`

## Structural learning

`assess_area()` aggregates repeated lifecycle failures. The generic lifecycle initiative planner then requires recurrence over time, multiple subjects and service-gap evidence before proposing structural infrastructure.

The preferred sequence is:

`prevent transition → repair existing-service access → smallest case intervention → extend existing institution → reversible pilot → permanent service only after sustained proof`.

## Stable welfare integration

The final objective is **stable welfare integration**, not raw intake, removal, adoption, sterilization or working-dog counts.

Outcome families include:

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
- specialist referrals completed without animal-welfare compromise.

## Public-good-agent testbed boundary

Animal welfare is useful here because transition states, intervention units, geography and outcomes can be comparatively observable, making it a good domain for testing evidence/diagnosis/intervention/evaluation machinery.

But the transfer to human poverty or food security is **architectural only**.

Potentially reusable:

`evidence → transition → driver/access diagnosis → intervention → authority → outcome → recurrence learning`.

Not reusable without a new constitution:

- animal-specific policy rules;
- ownership/capture logic;
- animal population management.

Human welfare requires its own rights, legal-entitlement, autonomy/consent, political-agency, anti-discrimination, privacy/due-process and dignity framework.

## v0 limitation

This is decision-support and programme-planning software. It is not a veterinary system, legal authority, animal-control officer, dangerousness evaluator, adoption authority or assistance-dog certifier. Determinant and access observations are evidence inputs, not automated causal verdicts.
