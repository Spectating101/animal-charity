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

## Condition diagnosis is not capability-scarcity diagnosis

A public or field source can directly establish that a delivery edge is broken without establishing that no suitable resource exists to repair it.

Example:

```text
landslide blocks road
        ↓
ACCESS DISRUPTION ESTABLISHED

but

public report lists no engineering team / helicopter
        ↓
CAPABILITY STATE UNKNOWN
not
CAPABILITY ABSENT
```

The controller therefore treats these as separate propositions:

1. **condition proposition:** is access actually constrained or isolated?
2. **capability proposition:** is there a verified live resource that can restore or bypass access?
3. **scarcity proposition:** does a complete-enough current inventory establish that no suitable capability is available?

When the condition is established but the capability inventory is partial/unknown, the correct output is an `access` diagnosis plus an `evidence` gap. It is not a capacity diagnosis.

This principle generalizes beyond roads. A service may be inaccessible, a communications link down, a utility distribution edge broken or a delivery route unusable while the wider repair/resource inventory remains unknown.

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

### East Nusa Tenggara access disruption — 16 August 2026

Decision source: Reuters public report published 03:33:35 UTC / 10:33:35 WIB.

What the cutoff establishes:

- roads were blocked and landslides were present;
- landslides and aftershocks were impeding rescue;
- the operational access edge was therefore directly constrained.

What it does not establish:

- an exhaustive engineering/air/off-road capability inventory;
- that no alternative access resource existed;
- current dispatch availability;
- live incident-command authority.

Expected control behavior: **diagnose access disruption while preserving capability uncertainty**.

The hidden later reference reports planes being readied for aid and helicopter aerial monitoring, which is compatible with the distinction: a broken access edge did not imply that alternative access capability was nonexistent.

## Replay corpus gate

The real replays are registered in `config/research/disaster_replay_corpus.json` and evaluated by `app/replay_corpus.py` / `scripts/evaluate_replay_corpus.py`.

Each corpus case declares a machine-checkable safety contract:

- problem classes that must appear;
- problem classes that must never appear;
- stages that must never appear;
- required authority/data-gap conditions;
- exact expected inventory scope where relevant;
- a maximum number of proposed resource reservations;
- the expected primary replay stage when a hidden reference exists.

The evaluator returns non-zero when any case violates its contract, and `make verify` includes the corpus gate. Later routing changes therefore cannot silently convert partial public evidence into scarcity, imply public reporting is command authority, suppress critical uncertainty escalation, or hide an established access failure behind inventory uncertainty without breaking CI.

The corpus is deliberately small at first. Its value is not the number of cases but the fact that each new historical case can become a permanent falsification/regression test rather than an anecdote.

## Replay metrics

A disaster replay should record more than whether the predicted primary stage matches a later reference.

Useful safety/research metrics include:

- hindsight-evidence violations;
- false scarcity promotions;
- false deployability promotions;
- false resolution promotions;
- critical-uncertainty misses;
- established-condition misses;
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

The disaster domain is currently at R0 plus a small public-source R1 corpus. It is not validated for autonomous or live consequential disaster allocation.
