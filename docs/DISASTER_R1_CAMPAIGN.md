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

The corpus is machine-enforced in `config/research/disaster_replay_corpus.json`. `make verify` fails if a case violates its declared contract.

## What the corpus currently tests

### False scarcity

Absence from incomplete journalism, public reporting, partner registries or partial inventories is not proof that capability is absent.

### Critical uncertainty

Urgent life-safety uncertainty can justify rapid human escalation and verification without weakening the evidence threshold for capacity, deployability or authority claims.

### Broken edge vs missing capability

A road, communications link, health-service path or evacuation route can be demonstrably broken while the inventory of repair/alternative capabilities remains unknown.

### Response activity vs spare capacity

A helicopter, truck, excavator, team or other resource reported as operating/deployed is not automatically spare for another assignment. Public reports remain evidence/candidate capability unless a live operations platform verifies current availability.

### No-false-intervention

The controller must also know when **not** to propose an intervention. Explicitly met needs remain met even inside a severe disaster context.

### Authority

All Wave-1 public replays intentionally lack live command context. They may support diagnosis and research evaluation, but zero consequential resource routing is treated as authorized by the replay evidence.

## Evidence and claim boundaries

- publication timestamps are conservative public-knowledge cutoffs unless a more defensible earlier timestamp exists;
- public journalism is not assumed to reproduce everything competent responders knew;
- replay agreement is not a causal estimate of lives saved, cost avoided or outcome improvement;
- later sources are outcome/reference evidence only and remain hidden during the decision run;
- no public-source replay may promote a reported resource into direct deployability without live operational evidence;
- human incident command, clinical authority, evacuation authority, engineering authority and other consequential powers remain outside the controller.

## Wave 2 red-team queue

These are deliberately **not** forced into the green corpus yet. Each should be added only when the historical evidence packet is strong enough to make the intended test defensible.

1. **True capacity shortage** — explicit contemporaneous operational evidence that a required resource/service is insufficient, testing whether the current complete-inventory gate is too conservative.
2. **Committed-elsewhere conflict** — matching capability exists but is already committed to another critical need.
3. **Conflicting reports** — two credible sources disagree about current need/access/resource state.
4. **Stale-state reversal** — an earlier route/service observation becomes invalid and must not survive into the next operational period.
5. **Recurring infrastructure failure** — repeated flood/fire/access failure with enough history to justify a mitigation/preparedness structural candidate.
6. **Safety overrides throughput** — nominally efficient routing should stop because food safety, structural safety, contamination or clinical constraints fail.
7. **Recovery integrity** — reconstruction/procurement promise, physical implementation and beneficiary outcome diverge without allowing the software to declare corruption.
8. **Cross-jurisdiction mutual aid** — local capacity insufficient but neighboring capability exists under a different authority boundary.

## Promotion criteria

Wave 1 is a useful R1 campaign only if:

- all historical cutoffs pass hindsight gates;
- all ten case contracts pass without weakening earlier safety rules;
- negative controls prove the evaluator can fail;
- the full animal, MBG, integrity, governance, interoperability and disaster stack remains green;
- Docker packaging remains green.

After a broader R1 set survives, the next meaningful evidence level is **R2 prospective shadow use** with competent emergency-management or humanitarian operators. The system should observe and produce recommendations with no operational effect, preserving the human decision and later outcome for comparison.
