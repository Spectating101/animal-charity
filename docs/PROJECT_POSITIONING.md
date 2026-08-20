# Project positioning: Public-Good Control Plane

## Working name

**Public-Good Control Plane** is the current descriptive working name for the research object in this repository.

The GitHub repository name `animal-charity` is historical lineage, not the full present scope. Do not rename the repository while the stacked research branches are still being evaluated merely for branding consistency.

## One-sentence description

> An evidence-bounded governance decision layer that identifies which part of a public-good delivery chain is actually broken, maps usable existing capability, applies safety/integrity/rights/authority gates, and proposes the smallest feasible intervention before new resources or infrastructure are committed.

## What this is not

It is not:

- an AI government;
- a beneficiary deservingness engine;
- an emergency-dispatch sovereign;
- a corruption detector;
- a news publication;
- a social registry;
- a procurement platform;
- a payment rail;
- a replacement for professional or statutory authority.

## Portfolio boundary with Nocturnal

### Nocturnal

**Coverage / journalism / public memory / longitudinal accountability**

Questions:

- What happened?
- What source supports it?
- Who said or promised what?
- What changed afterward?
- Was a correction, investigation, ruling, completion or recurrence later documented?

Primary object: a sourced matter/history.

### Public-Good Control Plane

**Governance diagnosis / intervention / resource-routing support**

Questions:

- What bad state exists now?
- What transition is failing?
- Is the problem scarcity, access, capacity, integrity, safety, coordination or missing evidence?
- What relevant capability already exists?
- Is it actually available and accessible?
- What is the smallest lawful intervention?
- Who has authority to approve/execute it?
- Did the intervention improve the state?
- Does recurrence justify structural change?

Primary object: a bounded decision problem under a domain constitution.

### Composition

```text
Nocturnal / official sources / sensors
            ↓
      historical + current evidence
            ↓
   PUBLIC-GOOD CONTROL PLANE
            ↓
 diagnosis + bounded recommendation
            ↓
 human / institutional authority
            ↓
      execution system
            ↓
          outcome
            ↓
         Nocturnal
   preserves what happened next
```

Nocturnal can make the control plane less forgetful. The control plane can make public memory operationally useful. Neither should absorb the other's authority.

## Case-study ladder

### Case 1 — Animal welfare

Tests fragmented services and prevention:

- rescue vs reunification;
- owner retention vs surrender;
- source control vs repeated downstream intake;
- foster/adoption capacity;
- food/logistics as one actuator;
- social integration with unconditional welfare.

Research question:

> Can the control layer identify the preventable welfare transition and route toward the appropriate existing capability instead of applying one charity intervention to every case?

### Case 2 — MBG public nutrition

Tests a huge existing programme:

- target population;
- capacity;
- transport/access;
- procurement/resource reconciliation;
- food safety;
- beneficiary receipt;
- nutritional outcome;
- integrity before scarcity.

Research question:

> Can the control layer distinguish genuine capacity shortage from failures elsewhere in the resource-to-outcome chain before expansion spending is justified?

### Case 3 — Disaster response (Kalimantan / NTT stress-test family)

Tests rapidly changing multi-agency state:

- hazard evidence;
- geographic exposure;
- life-safety urgency;
- stale data;
- resource availability and commitment;
- route/access constraints;
- service capacity;
- incident command;
- repeated structural resilience failures.

Research question:

> Can the same architecture remain useful under urgency and uncertainty without turning uncertain observations into autonomous life-and-death authority?

The current disaster work is an interoperability layer, not yet a disaster-response domain.

## Why the third case matters

Animal and MBG cases can largely be evaluated as snapshots. Disaster response forces **dynamic control**:

`state(t0) → recommendation → new evidence → state(t1) → reroute`

That introduces requirements that should be proven before a disaster adapter is operationally serious:

- freshness/expiry of evidence;
- resource reservation and double-booking prevention;
- dependency/cascading-failure reasoning;
- urgency under incomplete evidence;
- humanitarian minimum floors;
- geography and route feasibility;
- continuous reassessment;
- clear incident-command handoff.

## Packaging model

The project should be presented as three layers, not dozens of features:

### 1. Domain-independent control core

- evidence/provenance discipline;
- normalized problem stages;
- capability/access reasoning;
- integrity plane;
- structural recurrence;
- replay/shadow evaluation;
- human authority boundaries.

### 2. Domain constitutions/adapters

Current:

- animal welfare;
- MBG public nutrition.

Next candidate after interoperability/replay validation:

- disaster response.

Future domains should only be added when they test a genuinely new failure mode rather than serving as breadth theater.

### 3. Interoperability shell

Compose rather than replace:

- NIMS / WHO EOC doctrine;
- OCHA 3W / Open Referral service presence;
- OCDS contracting evidence;
- FIRMS/GDACS/Copernicus hazard evidence;
- Sahana/OpenSPP/GovStack-style execution infrastructure;
- Nocturnal longitudinal public memory.

See `docs/INTEROPERABILITY_ARCHITECTURE.md` and `config/integrations/reference_systems.json`.

## Current claim boundary

Supported claim:

> The repository contains a tested R0 control-plane architecture across animal welfare and MBG plus a typed interoperability contract for external evidence, capability, integrity and authority systems.

Not yet supported:

- that it improves real government outcomes;
- that it outperforms emergency managers;
- that it can safely allocate national disaster resources;
- that it detects real corruption;
- that it can autonomously administer welfare rights;
- that the disaster adapter itself is complete.

The next evidence upgrades remain retrospective real-case replay (R1), prospective shadow mode (R2), then supervised reversible intervention (R3).
