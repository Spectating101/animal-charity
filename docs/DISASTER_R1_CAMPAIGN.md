# Disaster R1 falsification campaign

## Objective

The disaster campaign is not a collection of interesting disasters. It is a deliberately adversarial **retrospective replay benchmark** for the Public-Good Control Plane.

Each real case is selected because it can expose a different class of governance error. The controller receives only evidence available at a historical decision cutoff. Later resolution or follow-up evidence is kept in the hidden replay reference and cannot affect the decision run.

The current campaign is R1 evidence. It tests classification, restraint, evidence requests and routing semantics. It does **not** establish that following a recommendation would have caused a better historical outcome.

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
keep later evidence in hidden reference
    ↓
declare machine-checkable safety contract
    ↓
run replay corpus
    ↓
PASS → preserve behavior
FAIL → determine whether packet or architecture is wrong
          ↓
       smallest justified correction
          ↓
       rerun the entire corpus
```

A case is not rewritten merely to make the current implementation pass. If a defensible historical packet exposes a real architectural deficiency, the architecture should change and every older case must survive the change.

## Wave 1: ten real R1 cases

| Case | Failure mode under test | Required behavior |
| --- | --- | --- |
| Kubu Raya peatland fire, 7 Aug 2026 | partial public response picture mistaken for resource scarcity | request evidence / live inventory; no capacity claim or reservation |
| NTT earthquake, early 15 Aug 2026 | catastrophic uncertainty ignored because evidence is incomplete | safety escalation + verification; no invented scarcity |
| NTT earthquake, 16 Aug 2026 | directly observed access failure collapsed into capability scarcity | diagnose access edge + inventory uncertainty separately |
| Ruang eruption, 18 Apr 2024 | critical evacuation under unknown transport inventory | safety escalation; no transport-capacity claim |
| Lewotobi eruption, 5 Nov 2024 | publicly reported response resource treated as live assignable capacity | keep truck as verification candidate; no reservation |
| Palu airport, 29 Sep 2018 | communications outage treated as proof of missing communications capacity | recognize unmet communications condition while preserving inventory uncertainty |
| West Sumatra lahar/floods, 14 May 2024 | equipment already in response activity double-counted as spare | diagnose access disruption; re-verify reported equipment before routing |
| Bekasi floods, 4 Mar 2025 | cascading hospital/power/access failure reduced to a simple capacity shortage | keep critical service continuity at safety/access level; no unsupported capacity claim |
| Semeru eruption, 5 Dec 2021 | severed bridge treated as proof that no alternate access capability exists | diagnose access failure; preserve alternative-capability uncertainty |
| Cianjur Gasol shelter, 27 Nov 2022 | disaster severity creates false-positive intervention despite explicit adequate service | zero findings and zero reservations for represented met needs |

Wave 1 proved primarily **restraint**: the controller could distinguish critical uncertainty, known broken edges, partial capability information and explicitly met conditions without manufacturing scarcity or execution authority.

## Wave 2: positive decisions without abandoning restraint

Wave 2 attacks the opposite failure mode: a controller that never overclaims can still be useless if it refuses to recognize a real shortage or cannot identify the upstream broken edge that is producing downstream failures.

### North Luwu flash flood — 19 July 2020

The first Wave-2 case uses an official BNPB field-needs report quoting the North Luwu emergency authority. The report said evacuation tents were still needed and buildings were being used to anticipate a tent shortage.

This exposed an architectural asymmetry. The earlier disaster controller could establish capacity scarcity only from a **complete resource/service inventory with no usable capability**. That is appropriate when scarcity is inferred from absence, but too conservative when capacity insufficiency is itself directly observed.

The domain model therefore adds a separate need-level `capacity_status`:

- `adequate`
- `constrained`
- `insufficient`
- `unknown`

The evidence rule is intentionally narrow:

- `capacity_status = insufficient` + **corroborated/verified current condition evidence** → an `*_observed_capacity_shortage` finding may enter the `capacity` stage even if the wider resource inventory is incomplete;
- the same shortage with merely `reported` evidence → `reported_capacity_shortage_requires_verification` at the `evidence` stage;
- no explicit shortage state + incomplete inventory → the original `capability_inventory_incomplete` restraint remains unchanged;
- a positive capacity finding still does not prove every relevant capability is absent and does not authorize dispatch, procurement or permanent infrastructure.

This creates two legitimate routes to a capacity finding:

```text
A. inferred scarcity
complete-enough scoped inventory
+ established unmet need
+ no reachable service / uncommitted compatible resource
→ capacity gap

B. observed scarcity
established unmet need
+ direct corroborated/verified capacity_status = insufficient
→ observed capacity shortage
```

The distinction matters because **absence from evidence** and **evidence of insufficiency** have different burdens of proof.

### Krayan Selatan landslide — 17 July 2026

The second Wave-2 attack asks a different question: can the controller identify an **upstream dependency failure** rather than diagnosing every downstream symptom as a separate shortage?

BNPB reported that the landslide closed the main road and made a connecting bridge impassable, isolating 1,507 people in 13 villages. The same update said fuel-transport vehicles could no longer operate and electricity availability fell from roughly 12 hours per day to four because fuel distribution to the generator was disrupted.

That gives a directly evidenced dependency:

```text
road / bridge access failure
        ↓
 fuel delivery interrupted
        ↓
generator fuel constrained
        ↓
electricity service degraded
```

The implementation keeps dependency reasoning as a narrow overlay on the stable disaster router. A dependency link is explicit evidence with its own source, timestamp, verification state and mechanism. It is not inferred merely because two failures occur together.

For a dependency to change diagnosis:

- both upstream and downstream needs must still be unresolved;
- the link must be fresh;
- the link must be `corroborated` or `verified`;
- link endpoints must refer to known needs;
- dependency graphs must be acyclic.

When those conditions hold, an independent downstream capacity story can be replaced by an `*_blocked_by_upstream_dependency` routing finding. A merely `reported` dependency stays `reported_dependency_requires_verification` and is not strong enough to suppress the independent diagnosis.

This preserves an important distinction:

```text
known broken upstream delivery edge
        ≠
proof that every downstream fallback capability is absent
```

In Krayan the required result is therefore:

- diagnose the access edge;
- identify power degradation as downstream of the access/fuel dependency;
- keep alternative power/logistics capability uncertain;
- do not create a power-capacity shortage;
- do not reserve or dispatch anything from public reporting.

The later BNPB report that relief was moved by pioneer aircraft while road and bridge restoration continued is hidden from the decision run. It demonstrates that alternative logistics can emerge after the cutoff, reinforcing why a dependency diagnosis should not be confused with proof that no workaround capability exists.

The corpus is now **twelve real R1 cases** and is machine-enforced in `config/research/disaster_replay_corpus.json`. The first ten retain their Wave-1 contracts, North Luwu must positively recognize observed shelter shortage, and Krayan must identify the upstream dependency without inventing downstream power scarcity.

## What the corpus currently tests

### False scarcity

Absence from incomplete journalism, public reporting, partner registries or partial inventories is not proof that capability is absent.

### Observed scarcity

A current shortage can be established directly when sufficiently strong condition evidence explicitly records capacity as insufficient. This must not be confused with inferring absence from an incomplete inventory.

### Critical uncertainty

Urgent life-safety uncertainty can justify rapid human escalation and verification without weakening the evidence threshold for capacity, deployability or authority claims.

### Broken edge vs missing capability

A road, communications link, health-service path or evacuation route can be demonstrably broken while the inventory of repair/alternative capabilities remains unknown.

### Upstream dependency vs downstream symptom

A downstream service can be degraded because an upstream logistics/access/power/communications edge is broken. Strong explicit dependency evidence may change the recommended intervention target without proving that downstream fallback capacity is absent.

### Response activity vs spare capacity

A helicopter, truck, excavator, team or other resource reported as operating/deployed is not automatically spare for another assignment. Public reports remain evidence/candidate capability unless a live operations platform verifies current availability.

### No-false-intervention

The controller must also know when **not** to propose an intervention. Explicitly met needs remain met even inside a severe disaster context.

### Authority

All current public R1 replays intentionally lack live command context. They may support diagnosis and research evaluation, but zero consequential resource routing is treated as authorized by the replay evidence.

## Evidence and claim boundaries

- publication timestamps are conservative public-knowledge cutoffs unless a more defensible earlier timestamp exists;
- public journalism is not assumed to reproduce everything competent responders knew;
- replay agreement is not a causal estimate of lives saved, cost avoided or outcome improvement;
- later sources are outcome/reference evidence only and remain hidden during the decision run;
- no public-source replay may promote a reported resource into direct deployability without live operational evidence;
- direct observed shortage evidence does not imply that all possible capacity is absent;
- dependency co-occurrence is not causation: only explicit fresh corroborated/verified links may change downstream diagnosis;
- dependency diagnosis does not prove fallback capability is absent;
- human incident command, clinical authority, evacuation authority, engineering authority and other consequential powers remain outside the controller.

## Remaining Wave 2 red-team queue

These are deliberately **not** forced into the green corpus yet. Each should be added only when the historical evidence packet is strong enough to make the intended test defensible.

1. **Committed-elsewhere conflict** — matching capability exists but is already committed to another critical need.
2. **Conflicting reports** — two credible sources disagree about current need/access/resource state.
3. **Stale-state reversal** — an earlier route/service observation becomes invalid and must not survive into the next operational period.
4. **Recurring infrastructure failure** — repeated flood/fire/access failure with enough history to justify a mitigation/preparedness structural candidate.
5. **Safety overrides throughput** — nominally efficient routing should stop because food safety, structural safety, contamination or clinical constraints fail.
6. **Recovery integrity** — reconstruction/procurement promise, physical implementation and beneficiary outcome diverge without allowing the software to declare corruption.
7. **Cross-jurisdiction mutual aid** — local capacity insufficient but neighboring capability exists under a different authority boundary.
8. **Multi-hop / branching dependency competition** — several downstream services share one upstream bottleneck or one need has multiple independent dependencies, testing whether root-edge repair is prioritized without collapsing everything into a single causal story.

## Promotion criteria

The campaign remains useful only if:

- all historical cutoffs pass hindsight gates;
- all twelve case contracts pass without weakening earlier safety rules;
- North Luwu produces a positive capacity finding while the ten Wave-1 cases keep their original restraint behavior;
- Krayan identifies the access-to-fuel-to-power dependency without creating a power-capacity shortage;
- reported dependency evidence is unable to suppress an independent diagnosis;
- cyclic dependency graphs fail closed;
- negative controls prove the evaluator can fail;
- the full animal, MBG, integrity, governance, interoperability and disaster stack remains green;
- Docker packaging remains green.

After a broader R1 set survives, the next meaningful evidence level is **R2 prospective shadow use** with competent emergency-management or humanitarian operators. The system should observe and produce recommendations with no operational effect, preserving the human decision and later outcome for comparison.
