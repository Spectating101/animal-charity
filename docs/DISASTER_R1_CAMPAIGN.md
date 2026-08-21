# Disaster R1 falsification campaign

## Objective

The disaster campaign is a deliberately adversarial **retrospective replay benchmark** for the Public-Good Control Plane, not a collection of interesting disasters.

Each real case is selected because it can expose a different governance error. The controller receives only evidence available at a historical decision cutoff. Later resolution/follow-up evidence stays hidden in the replay reference and cannot affect the decision run.

R1 tests classification, restraint, evidence requests, routing semantics and structural-candidate discipline. It does **not** establish that following a recommendation would have caused a better historical outcome.

## Campaign loop

```text
candidate failure mode
    ↓
source a historical incident
    ↓
freeze decision cutoff
    ↓
encode only then-available evidence
    ↓
keep later evidence hidden
    ↓
declare machine-checkable contract
    ↓
run entire corpus
    ↓
PASS → preserve behavior
FAIL → packet wrong or architecture wrong?
          ↓
       smallest justified correction
          ↓
       rerun entire corpus
```

A defensible historical case is not weakened merely to make the implementation pass.

## Wave 1 — restraint baseline

The first ten real R1 cases established conservative boundaries:

| Case | Failure mode | Required behavior |
| --- | --- | --- |
| Kubu Raya peatland fire, 7 Aug 2026 | partial public response picture mistaken for scarcity | evidence/live inventory; no capacity claim/reservation |
| NTT earthquake, early 15 Aug 2026 | catastrophic uncertainty ignored | safety escalation + verification; no invented scarcity |
| NTT earthquake, 16 Aug 2026 | access failure collapsed into capability scarcity | access edge + inventory uncertainty separately |
| Ruang eruption, 18 Apr 2024 | critical evacuation under unknown transport inventory | safety escalation; no transport-capacity claim |
| Lewotobi eruption, 5 Nov 2024 | reported response resource treated as assignable | candidate only; no reservation |
| Palu airport, 29 Sep 2018 | communications outage treated as missing capacity | unmet condition + inventory uncertainty |
| West Sumatra lahar/flood, 14 May 2024 | equipment in use double-counted as spare | access diagnosis; re-verify before routing |
| Bekasi floods, 4 Mar 2025 | hospital/power/access cascade reduced to simple scarcity | safety/access; no unsupported capacity claim |
| Semeru eruption, 5 Dec 2021 | severed bridge treated as proof no alternative exists | access failure + alternative-capability uncertainty |
| Cianjur Gasol shelter, 27 Nov 2022 | disaster context creates false intervention | zero findings/reservations for represented met needs |

## Wave 2 — positive reasoning without abandoning restraint

### Observed scarcity: North Luwu, 19 July 2020

The North Luwu field-needs report exposed an asymmetry: scarcity can be established either by a sufficiently complete inventory or by sufficiently strong direct condition evidence that capacity is insufficient.

`DisasterNeed.capacity_status` therefore distinguishes:

- `adequate`
- `constrained`
- `insufficient`
- `unknown`

Two legitimate capacity paths now exist:

```text
A. inferred scarcity
complete-enough scoped inventory
+ established unmet need
+ no reachable service / uncommitted compatible resource
→ capacity gap

B. observed scarcity
established unmet need
+ corroborated/verified capacity_status = insufficient
→ observed capacity shortage
```

A merely reported shortage remains an evidence/verification finding.

### Upstream dependency: Krayan Selatan, 17 July 2026

BNPB reported a road/bridge closure that stopped fuel-truck operation and reduced electricity availability because generator-fuel distribution was disrupted.

The explicit dependency is:

```text
road / bridge access failure
        ↓
fuel delivery interrupted
        ↓
generator fuel constrained
        ↓
electricity service degraded
```

Dependency reasoning remains a narrow overlay on the stable disaster router. Links carry explicit source, time, verification state and mechanism. Only fresh corroborated/verified links between unresolved known needs can change diagnosis. Reported-only links require verification. Cycles and unknown endpoints fail closed.

An established dependency can replace an independent downstream scarcity story with `*_blocked_by_upstream_dependency`, without claiming fallback downstream capability is absent.

### Pre-event structural signal: Nunukan, 2 June 2026

The thirteenth case asks whether repeated access/infrastructure disruption could support a **regional mitigation/preparedness review before the next severe event**.

Visible at the cutoff:

- 25 Jul 2024: Krayan Selatan flood/landslide impacts included bridge and provincial-road damage; a damaged bridge cut Long Layu access toward Krayan Tengah.
- 3 Jun 2025: flooding across nine Nunukan districts including the Krayan districts damaged four bridges and seven road points.
- 2 Jun 2026: another Nunukan flood/landslide episode left a landslide-affected road still passable during recovery.

The replay unit is deliberately broad: **Nunukan regional access network**. It does not assert that the same bridge failed repeatedly.

A recurrence signal records three documented access/infrastructure disruption episodes across 677 days. Because the current phase is recovery, this is sufficient under the existing recurrence gate to mark the access finding `structural_candidate=true`.

Hidden future reference:

- July 2026: a separate severe Krayan Selatan landslide closed the main Krayan Barat–Krayan Selatan road and made a connecting bridge impassable, isolating 1,507 people;
- later BNPB used air logistics while coordinating road reopening and bridge repair.

The July event cannot create the structural flag. It only tests whether a structural review signal existed before the later recurrence.

`structural_candidate=true` means **review recurring access resilience as a mitigation/preparedness problem**. It does not:

- select a bridge/road project;
- establish engineering causation;
- prove the same asset repeatedly failed;
- prove a proposed mitigation would have prevented July;
- authorize spending or construction.

## Replay hindsight hardening

The structural replay exposed a historical-evidence loophole: strict replay previously enforced timestamps inside `case.payload`, but evidence-manifest entries were not independently checked against the decision cutoff.

Strict replay now:

- requires `observed_at` on every evidence-manifest entry;
- rejects manifest entries after the cutoff;
- preserves the existing payload timestamp/future-evidence gate.

This matters especially for recurrence signals, where historical source references could otherwise be accompanied by future-dated manifest evidence.

## Corpus contract

The corpus is now **13 real R1 cases** (`disaster-public-r1-v6`). It is machine-enforced in `config/research/disaster_replay_corpus.json`.

Case contracts can enforce:

- required/forbidden problem classes;
- forbidden stages;
- required authority/data-gap text;
- maximum findings/reservations;
- expected command context;
- resource/service inventory coverage;
- expected structural-candidate state.

The evaluator's negative control proves these contracts can fail.

## Current reasoning modes under test

### False scarcity

Absence from incomplete journalism/public reporting/partial registries is not proof capability is absent.

### Observed scarcity

Strong direct condition evidence may establish insufficiency without pretending the wider inventory is complete.

### Critical uncertainty

Potentially catastrophic uncertainty can justify rapid human escalation and verification without weakening capacity/deployability/authority thresholds.

### Broken edge vs missing capability

An access/service edge can be demonstrably broken while repair/alternative capability remains unknown.

### Upstream dependency vs downstream symptom

Strong explicit dependency evidence may change the intervention target without proving downstream fallback scarcity.

### Response activity vs spare capacity

A resource reported as operating/deployed is not automatically spare for another assignment.

### Structural recurrence

Repeated documented failures may justify mitigation/preparedness review only when the recurrence gate is satisfied in a non-response phase. Structural candidacy is not a causal or procurement conclusion.

### No-false-intervention

The controller must know when no intervention finding is warranted.

### Authority

All public R1 replays lack live command authority. Diagnosis is not execution.

## Evidence and claim boundaries

- publication timestamps are conservative public-knowledge cutoffs unless a more defensible earlier timestamp exists;
- strict replay checks both payload evidence and evidence-manifest timestamps;
- public journalism is not treated as an exhaustive EOC picture;
- replay agreement is not a causal estimate of lives saved, cost avoided or outcome improvement;
- later sources remain hidden during decision runs;
- reported resources never become deployable without live operational evidence;
- observed shortage does not prove every possible resource is absent;
- dependency co-occurrence is not causation;
- structural recurrence does not identify a responsible asset/person or prove prevention;
- consequential authority remains with competent humans/institutions.

## Remaining Wave 2 red-team queue

1. **Committed-elsewhere conflict** — matching capability exists but is already committed to another critical need.
2. **Conflicting reports** — credible contemporaneous sources disagree about current state.
3. **Stale-state reversal** — an earlier valid route/service state becomes invalid and must not survive into the next operational period.
4. **Safety overrides throughput** — nominally efficient routing stops because safety constraints fail.
5. **Recovery integrity** — reconstruction/procurement promise, implementation and beneficiary outcome diverge without software declaring corruption.
6. **Cross-jurisdiction mutual aid** — local capacity is insufficient but neighboring capability exists under another authority.
7. **Multi-hop/branching dependency competition** — shared upstream bottlenecks or multiple independent dependencies.

## Promotion criteria

The campaign remains useful only if:

- all historical cutoffs pass hindsight gates;
- all 13 contracts pass without weakening older safety rules;
- North Luwu positively recognizes observed scarcity while Wave 1 retains restraint;
- Krayan identifies dependency without inventing downstream power scarcity;
- Nunukan produces a pre-July structural candidate without consuming July evidence;
- reported dependency evidence cannot suppress an independent diagnosis;
- cyclic dependency graphs fail closed;
- negative controls prove evaluator failure modes;
- the full animal, MBG, integrity, governance, interoperability and disaster stack remains green;
- Docker packaging remains green.

After a broader R1 set survives, the next meaningful evidence level is **R2 prospective shadow use** with competent emergency-management or humanitarian operators. Recommendations should have no operational effect; human decisions and later outcomes should be preserved independently for comparison.
