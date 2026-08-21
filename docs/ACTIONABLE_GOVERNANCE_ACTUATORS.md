# Actionable governance actuator boundary

## Purpose

The Public-Good Control Plane may identify an unmet condition, determine the smallest justified intervention class, and emit a bounded **action intent**. It must not silently convert analysis into physical execution.

The actuator boundary separates four states:

```text
assessment -> action intent -> human/operator authorization -> execution -> outcome evidence
```

An action intent is not an order, dispatch, flight plan, procurement award, or physical command.

## Forest-fire drone pilot

Wildfire/peat-fire response is the first actuator case because the same incident can require several distinct capabilities:

- observation / hotspot verification;
- perimeter or inaccessible-area mapping;
- communications relay / situational awareness;
- suppression-support request where an authorized fire/UAS operator has an appropriate platform;
- post-action outcome verification.

The control plane chooses the **capability class and reason**, not flight parameters or suppression tactics.

## Required gates

Before an action intent can become execution-ready, an external authorized operator must verify:

1. current incident-command authority;
2. legal/airspace authorization and operator/pilot eligibility;
3. platform capability and current availability;
4. conflict/deconfliction with crewed aircraft and other emergency operations;
5. site-specific weather, terrain, visibility, people/property and fire-behavior safety;
6. mission feasibility and abort criteria;
7. downstream outcome-reporting path.

The control plane is intentionally unable to satisfy these gates from public reporting alone.

## No-go behaviors

The control plane must not:

- arm, launch, navigate, retask or land an aircraft;
- create autonomous fire-suppression tactics;
- choose ignition, incendiary or hazardous payload use;
- infer airspace clearance from disaster urgency;
- route a public/registry drone report as a live available aircraft;
- issue a water-drop or suppression command;
- override incident command, aviation safety, fire-behavior or exclusion-zone decisions;
- count mission acceptance, launch or payload delivery as success without outcome evidence.

## Intent lifecycle

```text
proposed
  -> awaiting_authority
  -> awaiting_operator_verification
  -> authorized
  -> accepted_by_operator
  -> executing
  -> completed_unverified
  -> outcome_verified
```

Any safety, legality, stale-state, command-context or capability change may move the intent to `blocked`, `cancelled` or `superseded`.

## Research claim boundary

This layer tests whether governance reasoning can hand off a bounded, auditable intervention request to an external execution system. It does not demonstrate autonomous drone operation, field effectiveness, legal authorization, or superior suppression outcomes.
