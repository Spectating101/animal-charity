# Disaster replay protocol

## Purpose

Disaster response is the first Public-Good Control Plane domain where the operational state can change materially within minutes or hours. Retrospective replay is therefore used to test whether the control layer can reason from **only what was knowable at a historical cutoff** without importing later outcomes or silently converting incomplete public reporting into an operational picture.

The replay is not a claim that public reporting contains everything responders knew. It is a test of what the control plane does when its evidence is incomplete.

## Core rule

> Urgency may lower the threshold for verification/escalation, but it must not lower the evidence threshold for declaring scarcity, deployability, resolution, causation or authority.

This creates two deliberately different behaviors:

1. **Critical uncertainty:** a potentially catastrophic life-safety report may justify rapid verification and escalation even before the condition is fully corroborated.
2. **Scarcity restraint:** absence of a resource/service from a partial or unknown inventory never proves that capacity is absent.

The system must be capable of doing both at the same time.

## Historical cutoff

Every replay has a `decision_cutoff`.

Evidence-bearing records must include a timestamp and must not be later than the cutoff. For public-source replay, the publication timestamp is used as a conservative earliest-public-knowledge timestamp unless a more defensible earlier timestamp is available from the source itself.

Later sources belong only in the hidden `reference` section.

## Public evidence is not an operational registry

A public article may establish facts such as:

- a hazard was active;
- an agency was operating in an area;
- a helicopter was performing water bombing;
- an evacuation was under way;
- roads were reported blocked;
- officials were still collecting impact data.

It normally does **not** establish:

- current spare capacity;
- current dispatch availability;
- exhaustive resource inventory;
- exhaustive service registry;
- current command authorization;
- that an unmentioned capability does not exist.

For that reason, replay bundles explicitly declare:

- `resource_inventory_scope`: `complete_for_scope`, `partial`, or `unknown`;
- `service_registry_scope`: `complete_for_scope`, `partial`, or `unknown`.

Only a complete-enough inventory can support a negative scarcity claim.

## Resource-role rule

A capability record supplied by journalism, a public evidence feed or a registry may establish that a resource exists or was observed. It does not establish that the resource is presently deployable.

Only a fresh, sufficiently verified `operations_platform` record marked available can enter the direct deployable set.

Other reported available resources remain candidates requiring live verification.

A resource already reported as committed is not spare capacity.

## Need-state rule

`status = unknown` is not treated as `unmet`.

Unknown condition state produces an evidence request. The exception is not an allocation shortcut: when the report is both critical and potentially life-safety relevant, the system may produce a parallel `verify + escalate` safety finding while still refusing to diagnose access/capacity or reserve resources until the need is established.

## Outcome rule

A need disappearing from a later report is not counted as resolved. Resolution requires explicit outcome evidence.

Likewise:

- dispatch is not delivery;
- delivery is not receipt;
- receipt is not recovery;
- response activity is not proof of improved outcome.

## Structural rule

A single response incident does not justify standing infrastructure.

Structural mitigation/preparedness becomes a candidate only outside the immediate response phase and only after recurrence evidence satisfies the domain gate.

## Current R1 public replays

### Kubu Raya peatland wildfire — 7 August 2026

Decision source: BNPB field report published 19:12 WIB.

What the cutoff establishes:

- peatland fire response was active;
- ground spraying and helicopter water bombing were operating;
- peat fire was described as difficult to extinguish below the surface;
- smoke was described as a health threat;
- two weather-modification units were on standby subject to suitable clouds.

What it does not establish:

- spare helicopter/ground-team capacity;
- a complete resource inventory;
- a complete service registry;
- a specific unmet medical-service requirement.

Expected control behavior: **evidence/coordination before scarcity**.

### Nagekeo/Sikka earthquake — 15 August 2026, 08:00 WIB

Decision source: initial BNPB update.

What the cutoff establishes:

- a magnitude 7.7 earthquake occurred;
- strong aftershocks continued;
- deaths/injury and coastal evacuation were already reported;
- BNPB explicitly stated that casualty, injury, damage and other impact data were still being updated.

What it does not establish:

- the full population impact;
- complete road/access state;
- complete rescue/service/resource state;
- which specific capacity shortage existed.

Expected control behavior: **critical uncertainty triggers rapid verification/escalation without inventing scarcity**.

## Replay metrics

A disaster replay should record more than whether the predicted primary stage matches a later reference.

Useful safety/research metrics include:

- hindsight-evidence violations;
- false scarcity promotions;
- false deployability promotions;
- false resolution promotions;
- critical-uncertainty misses;
- unsupported structural-infrastructure proposals;
- recommendations issued without command/authority context;
- primary-stage agreement;
- recommendation changes across operational periods;
- reservations invalidated by new state.

Stage agreement is diagnostic only. It does not prove that following the recommendation would have caused a better historical outcome.

## Evidence ladder

- **R0:** synthetic architecture fixtures.
- **R1:** retrospective real-case replay with historical cutoff and hidden later reference.
- **R2:** prospective shadow use alongside competent responders; recommendations have no operational effect.
- **R3:** supervised, reversible interventions under competent authority.
- **R4+:** repeated-area longitudinal evaluation and independent replication.

The disaster domain is currently at R0 plus initial public-source R1 replay. It is not validated for autonomous or live consequential disaster allocation.
