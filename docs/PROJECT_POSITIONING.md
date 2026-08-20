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

### Case 3 — Disaster response

Tests rapidly changing multi-agency state:

- hazard evidence;
- life-safety urgency under incomplete verification;
- humanitarian minimum floors;
- stale data;
- resource availability and commitment;
- route/access constraints;
- existing service capacity;
- incident-command authority;
- resource reservation / double-booking prevention;
- repeated structural resilience failures;
- operational-period reassessment.

Research question:

> Can the same architecture remain useful under urgency and uncertainty while resource and command state changes underneath it, without converting decision support into autonomous life-and-death authority?

The disaster domain now has R0 synthetic stress fixtures plus initial R1 public-source replays for Kubu Raya peatland fire and the early NTT earthquake. Those replays test evidence discipline and escalation behavior; they do not establish real-world outcome superiority.

## Why the third case matters

Animal and MBG cases can largely be evaluated as snapshots. Disaster response forces **dynamic control**:

`state(t0) → recommendation → new evidence → state(t1) → invalidate/reroute → outcome`

The current implementation now tests:

- freshness/expiry of evidence;
- verified vs merely reported resources;
- committed vs spare resources;
- current-service-first routing;
- explicit inventory-coverage semantics before negative scarcity claims;
- resource reservation and double-booking prevention;
- urgency under incomplete evidence;
- humanitarian minimum floors;
- isolation / access compatibility;
- continuous reassessment;
- explicit outcome vs missing follow-up;
- clear incident-command handoff;
- hindsight-safe public-source replay.

See `docs/DISASTER_CONTROL_PLANE.md` and `docs/DISASTER_REPLAY_PROTOCOL.md`.

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

Current domain implementations:

- animal welfare;
- MBG public nutrition;
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

> The repository contains a tested R0 Public-Good Control Plane across animal welfare, MBG public nutrition and disaster response, a typed interoperability contract for external evidence/capability/integrity/authority systems, a multi-period disaster reassessment model, and initial hindsight-safe R1 public-source disaster replays that exercise false-scarcity restraint and critical-uncertainty escalation.

Not yet supported:

- that it improves real government outcomes;
- that it outperforms emergency managers;
- that it can safely allocate national disaster resources;
- that it detects real corruption;
- that it can autonomously administer welfare rights;
- that replay-stage agreement predicts real field performance;
- that following its historical recommendations would have caused better outcomes.

The next evidence upgrades are a broader R1 replay corpus, then prospective shadow mode (R2), then supervised reversible intervention (R3).
