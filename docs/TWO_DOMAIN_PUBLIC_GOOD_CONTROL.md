# Two-Domain Public-Good Control Architecture

## Purpose

The repository now treats **companion-animal welfare** and **Indonesia's MBG public-nutrition programme** as two deliberately different testbeds for the same control-plane research question:

> Can a bounded system identify the actual bad-state transition, distinguish scarcity from access/capacity/integrity failure, route the smallest justified intervention through the correct authority, and verify durable outcome improvement?

The domains share an architecture. They do **not** share substantive constitutions.

## Shared control loop

```text
condition evidence
      ↓
bad-state transition
      ↓
driver / access / integrity diagnosis
      ↓
existing capability first
      ↓
smallest feasible intervention
      ↓
domain authority gate
      ↓
verified receipt / state transition
      ↓
outcome evidence
      ↓
recurrence?
   ↙       ↘
 no         yes
 ↓           ↓
retain   structural candidate
```

This is the level at which generalization is allowed.

## Domain A — companion-animal welfare

**Unit of concern:** individual animal plus regional welfare landscape.

**Desired state:** durable welfare-positive integration.

Typical transitions:

- owned-at-risk → surrender/abandonment;
- lost owned → prolonged displacement;
- reproductively active roaming → new unmanaged population;
- placement-ready → prolonged unstable care because foster capacity is absent;
- injury/distress → severe harm because rescue response is delayed.

Typical actuators:

- emergency stabilization;
- reunification;
- owner-retention support;
- source control;
- foster/adoption routing;
- responsible community care;
- specialist referral only.

Hard rules remain animal-specific: veterinary/professional authority, welfare-first handling, ecological/public-safety gates, no productivity requirement, no automatic assistance/therapy certification, and no population-control rule transfer to humans.

### Example response

A dog remains in a safe home but the owner has a verified temporary veterinary-cost gap and is considering relinquishment.

Shared classification:

`prevent`

Animal-domain action:

`owner_support.veterinary_gap`

The system should not route this case to a food bank, shelter expansion, MBG kitchen, or generic cash optimizer merely because those are other public-good capabilities.

## Domain B — MBG public nutrition

**Unit of concern:** beneficiary cohort plus SPPG/service catchment.

**Desired state:** safe, reliable, equitable nutrition service with measurable beneficiary outcome.

Typical failure edges:

- eligible cohort → not reached because targeting/data access fails;
- available kitchen capacity → not received because route/distribution fails;
- budget/procurement claim → physical input mismatch;
- meal-output claim → beneficiary-receipt mismatch;
- verified demand → genuine residual capacity shortage;
- meal receipt → no evidence of nutritional improvement.

Typical interventions:

- data/beneficiary reconciliation;
- route or schedule repair;
- catchment rebalancing;
- supplier/physical-input reconciliation;
- authorized audit referral for material verified integrity variance;
- reversible capacity extension;
- permanent new SPPG only after verified residual need;
- outcome measurement.

Hard rules remain human/institutional: beneficiary entitlement, procurement award, payment hold, supplier exclusion, formal audit/investigation, sanction, corruption/criminal finding, budget change and public accusation remain authorized human decisions under due process.

### Example response 1 — apparent shortage with integrity uncertainty

Nominal capacity is adequate, but verified procurement-to-input and output-to-recipient records materially diverge.

Shared classification:

`integrity`

MBG-domain action:

`reconcile resource chain → authorized human audit review if unresolved`

The system must **not** infer corruption and must **not** use the apparent shortfall to justify new capacity before reconciliation.

### Example response 2 — genuine residual capacity shortage

Verified demand exceeds verified capacity, while the resource chain reconciles within tolerance.

Shared classification:

`capacity`

MBG-domain action:

`check adjacent spare capacity / rebalance catchment → reversible extension → permanent capacity only if residual need persists`

This prevents the opposite failure mode: treating every shortage as suspicious and never building needed infrastructure.

## Why the router exists

Without a router, the repository risks becoming either:

1. a pile of unrelated domain modules; or
2. one dangerously generic schema that erases differences between animals, human beneficiaries, kitchens, households, procurement and welfare rights.

`app/public_good_control.py` takes the middle path:

- validates a declared domain;
- loads that domain's constitution/profile;
- calls the domain adapter;
- normalizes only the stages needed for comparative research;
- preserves the complete domain result;
- fails closed for unknown domains.

Machine-readable registry:

`config/domains/public_good_domains.json`

CLI:

```bash
python scripts/assess_public_good_case.py examples/public_good_animal_owner_retention.json
python scripts/assess_public_good_case.py examples/public_good_mbg_integrity.json
python scripts/assess_public_good_case.py examples/public_good_mbg_capacity.json
```

## What the two cases jointly test

| Research question | Animal welfare | MBG |
|---|---|---|
| Can condition be separated from capability/context? | policy/service existence must not invent an animal crisis | aggregate SPPG/beneficiary counts must not invent a local failure |
| Can prevention beat downstream response? | retain safe home before surrender | repair targeting/route before chronic nutrition failure |
| Can existing capacity be reused first? | foster/service extension before new facility | catchment rebalance before new SPPG |
| Can resource-flow uncertainty block false scarcity? | future optional integrity use | explicit integrity plane already tested |
| Can output be separated from outcome? | adoption/handoff is not stable welfare | meal delivery is not nutrition impact |
| Can recurrence justify structure? | foster/source-control/retention programme | route/QA/capacity infrastructure |
| Are authority rules domain-specific? | vet/animal-control/owner law | entitlement/procurement/audit/due process |

## Current claim boundary

This is still **R0 architecture evidence**.

The router demonstrates that one abstract control loop can preserve two materially different domain constitutions and produce different intervention classes from different evidence patterns. It does not show that the system improves real animal welfare, detects real MBG corruption, reduces malnutrition, or outperforms existing public institutions.

The next credible cross-domain step is R1 retrospective replay:

1. acquire a documented historical animal-welfare case set;
2. acquire a documented historical MBG operational case set;
3. hide the known intervention/outcome from the router;
4. provide only evidence available at the decision time;
5. compare diagnosis and proposed intervention with qualified human judgments and known outcomes.

If both domains survive that test without weakening their constitutions, the evidence for a genuinely reusable public-good control-plane abstraction becomes much stronger.
