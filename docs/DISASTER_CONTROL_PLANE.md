# Disaster Response Control Plane v0

## Purpose

This domain tests whether the Public-Good Control Plane can remain useful when state changes quickly, information is incomplete, resources are scarce and multiple professional authorities must coordinate.

It is **decision support**, not autonomous incident command.

The domain asks:

> What unmet humanitarian condition exists now, what verified capability can actually reach it, what should be requested or verified next, and how does that answer change when the operational state changes?

## Shared loop

```text
hazard / incident evidence
        ↓
current unmet needs
        ↓
current service + resource + access state
        ↓
current command context
        ↓
life-safety / humanitarian hard gates
        ↓
existing reachable service first
        ↓
verified deployable resource
        ↓
reported candidate requiring verification
        ↓
genuine access/capacity gap
        ↓
non-binding reservation / resource request proposal
        ↓
human incident command / professional authority
        ↓
execution
        ↓
explicit outcome evidence
        ↓
next operational period
```

## What changes compared with animal welfare and MBG

Disaster response introduces several first-class requirements:

- evidence expiration and stale-state exclusion;
- rapidly changing command context;
- humanitarian minimum floors;
- critical uncertainty that cannot simply be discarded;
- physical isolation and reachability;
- resource commitment / double-booking prevention;
- multi-period reassessment;
- explicit distinction between a disappearing report and a resolved need.

## Need model

Current categories are deliberately broad:

- life safety / search and rescue;
- emergency medical;
- potable water;
- shelter;
- food;
- access/engineering;
- communications;
- power;
- fire suppression;
- sanitation/WASH;
- other evidence-bounded need.

`people_affected` is contextual evidence, not a human-value score.

The v0 router sorts by declared priority and survival category. It does **not** optimize by wealth, social status, identity, predicted productivity, political importance or aid deservingness.

## Critical uncertainty

A critical report can be weakly verified and still be operationally important.

The control plane therefore permits both outputs at once:

```text
critical reported survivor need
→ verify + escalate urgently

and, if a fresh compatible resource exists,
→ propose routing through incident command
```

This avoids two bad extremes:

- treating every unverified report as established fact;
- silently dropping potentially catastrophic reports because confidence is incomplete.

## Capability order

For an unmet need, v0 checks in this order:

1. **Existing reachable service** with current open access and spare/normal capacity.
2. **Fresh verified available mobile/operational resource** with matching capability.
3. **Fresh reported matching resource** that must be verified before use.
4. **Access gap** when isolation prevents otherwise relevant capability from reaching the location.
5. **Capacity gap** when no current reachable capability is established.

This preserves the repository-wide doctrine:

> existing capability first; new capacity only for the residual verified gap.

## Resource reservations

A v0 reservation is a recommendation record inside one assessment.

It means:

> this resource appears fresh, verified, available, compatible and not already proposed for another need in the same assessment.

It does **not** mean:

- dispatch order;
- legal commitment;
- assignment accepted by the resource owner;
- route safety clearance;
- professional approval.

One resource record is conservatively proposed at most once per assessment. Cross-period availability must be re-read from the external operational system.

## Physical access

Resource proximity is not enough.

An isolated need requires a verified access-compatible capability such as air, off-road or engineering access before the control plane may describe the resource as reachable.

This is intentionally conservative. A future geospatial/route adapter may improve reachability reasoning, but v0 does not invent route feasibility from coordinates alone.

## Existing services

OCHA/Open Referral/Sahana-style service presence is only usable when the current record establishes:

- matching service type;
- same location in the v0 fixture model;
- open access;
- spare or normal capacity.

Service presence alone is not enough.

## Structural mitigation

A single response incident cannot justify standing infrastructure.

Structural candidates are only emitted outside the active `response` phase and require recurrence evidence. The v0 recurrence gate is intentionally simple: repeated problem signal, at least three events, at least fourteen days of span.

This can later support questions such as:

- repeated road isolation → route redundancy / staging review;
- repeated communications loss → resilient communications infrastructure;
- repeated wildfire recurrence → mitigation / preparedness investigation;
- repeated water/shelter shortfall → contingency capacity.

A structural candidate remains a planning signal, not a capital authorization.

## Dynamic reassessment

`app/disaster_evolution.py` compares two operational periods.

It distinguishes:

- newly unmet needs;
- explicitly resolved needs;
- missing follow-up reports;
- still-unresolved needs;
- newly deployable resources;
- lost deployable resources;
- newly stale records;
- previous proposed reservations invalidated by changed state;
- recommendation-stage changes;
- command-context changes.

The critical rule is:

> absence from the next feed is not proof of resolution.

Only explicit outcome evidence can move a previously unmet need into the resolved set.

## Synthetic gauntlets

```bash
python scripts/assess_disaster.py examples/disaster_ntt_synthetic.json
python scripts/assess_disaster.py examples/disaster_kalimantan_synthetic.json
python scripts/compare_disaster_periods.py \
  examples/disaster_ntt_synthetic.json \
  examples/disaster_ntt_synthetic_t1.json
```

The fixtures are synthetic architecture tests. They do not assert facts about real NTT or Kalimantan incidents.

### Earthquake fixture

Tests:

- critical reported survivor need;
- verify + escalate behavior;
- one verified SAR resource;
- no double-booking;
- a committed water resource that is not counted as spare;
- an isolated medical need;
- later medevac capability;
- explicit resolution vs disappearing follow-up.

### Wildfire fixture

Tests:

- typed peat-fire suppression;
- a reported aerial resource that cannot be treated as deployable;
- an existing reachable smoke-exposure clinic before new medical capacity;
- current incident-command context.

## Authority boundary

The control plane does not autonomously:

- dispatch or reassign emergency resources;
- order evacuation or shelter-in-place;
- perform clinical triage or treatment;
- command SAR or fire suppression;
- close roads or certify engineering safety;
- exercise police/military/coercive authority;
- award emergency procurement;
- decide compensation or benefit rights;
- declare legal blame or culpability.

See `config/missions/disaster_response_control.json`.

## Research level

Current level: **R0 synthetic architecture**.

The next useful evidence upgrades are:

1. **R1 retrospective replay** — reconstruct what was knowable at real historical decision cutoffs and hide later outcomes.
2. **R2 prospective shadow mode** — run beside real emergency-management operators without influencing decisions.
3. **R3 supervised reversible use** — only after the earlier evidence shows acceptable performance and failure behavior.

Until then, the correct claim is that the domain implements and tests a bounded disaster governance architecture, not that it improves real disaster outcomes.
