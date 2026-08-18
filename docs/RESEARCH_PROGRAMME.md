# Research Programme Map

## Core programme

The repository treats companion-animal welfare as a bounded domain for developing and falsifying **preventive public-good systems methods**.

The project is not trying to prove that one intervention (food banks, TNVR, shelters, foster care, adoption, therapy-dog training) is universally correct. It asks whether a persistent evidence-bounded control plane can determine **which transition is failing, why, what existing capability can repair it, when new infrastructure is justified, and whether the resulting welfare state is actually more stable.**

```text
One Welfare + social/service determinants
                ↓
preventable bad-state transitions
                ↓
evidence-bounded lifecycle routing
                ↓
existing-service access repair
                ↓
smallest feasible intervention
                ↓
structural recurrence detection
                ↓
reversible public-good initiative
                ↓
verified stable welfare integration
                ↓
longitudinal / population evaluation
```

The literature-to-code crosswalk lives at [`LITERATURE_TO_SYSTEM_MAP.md`](LITERATURE_TO_SYSTEM_MAP.md).

Machine-readable hypotheses, required evidence, supporting metrics and falsification criteria live at:

[`config/research/public_good_research_programme.json`](../config/research/public_good_research_programme.json)

## Unifying abstraction: preventable bad-state transitions

The programme does not begin with a fixed charity product. It asks which transition into a worse welfare state is occurring and whether it can be interrupted earlier.

Examples:

```text
stable owned → household/service shock → surrender risk → shelter/abandonment
lost owned → failed tracing/access → prolonged unmanaged displacement
intact roaming → failed source-control access → new unmanaged animals
placement-ready → foster/service-capacity gap → prolonged unstable care
acute injury → response/transport/clinical gap → severe welfare harm
```

The hypothesis is that many apparently different charity problems can be represented as:

`state → transition risk → driver/access barrier → intervention → verified new state`

This is the architecture later considered for human public-good domains. Animal-specific rules never transfer.

## Research tracks

### Track A — Preventive welfare systems

**Question:** Which bad-state transitions can be prevented, and which access/resource/institutional failures drive them?

Literature anchors:

- One Welfare;
- social determinants of companion-animal welfare;
- animal-welfare/service deserts;
- access-to-veterinary-care research;
- owner-retention and shelter-diversion studies.

Primary artifact: `app/preventive_welfare.py`

Primary hypotheses: `H1_access_not_scarcity`, `H2_prevention_beats_downstream_rescue`, `H4_coupled_one_welfare`.

### Track B — Regional animal-welfare control plane

**Question:** Given evidence about an individual animal and area, which welfare-positive transition should be proposed without exceeding human/professional authority?

Primary artifact: `app/animal_welfare_control.py`

Key doctrine:

- emergency stabilization before optimization;
- reunification/retention before unnecessary intake when safe and lawful;
- source control before endless downstream rescue where evidence supports it;
- evidence request rather than invented diagnosis;
- specialist participation is referral-only.

### Track C — Structural initiative planning

**Question:** When do repeated case failures justify extension of an existing service or creation of a reversible new local programme?

Primary artifacts: `app/lifecycle_initiatives.py`, `app/structural_initiatives.py`

Primary hypothesis: `H3_structural_recurrence`.

The planner should be able to conclude things as simple as:

> run a weekly food-support point here;

> run a periodic sterilization/registration clinic here;

> build a foster-recruitment programme here;

but only after recurrence and service-gap evidence justify the initiative.

### Track D — Stable social integration / membership

**Question:** Which animals flourish in companionship, community, foster/adoption, sanctuary or optional specialist participation, and how should longitudinal capability/preference evidence guide matching?

Primary hypothesis: `H5_social_integration`.

The programme treats **belonging as unconditional and contribution as optional**.

A working/therapy/assistance role is not a higher welfare state than ordinary companionship. The desired outcome is the best stable welfare-positive form of membership for the individual animal.

Current status: specialist-referral guardrails and longitudinal outcome rules exist; deeper participation-profile / behavioral-assent modules remain future research work.

### Track E — Outcome / economics / additionality

**Question:** Did the intervention actually improve welfare, at what cost/burden, and would the result plausibly have happened anyway?

Primary artifacts:

- `app/welfare_outcomes.py`
- `app/population_metrics.py`
- structural initiative planners
- audit / Nocturnal adapters.

Key rule:

> transaction completion is not impact.

An adoption that collapses, specialist role that creates sustained stress, or lower roaming count produced by lower observation coverage cannot be scored as success.

### Track F — General public-good architecture

**Question:** Which parts of evidence/transition/access/intervention/evaluation machinery generalize to human food insecurity or poverty while preserving a completely separate human-rights constitution?

Primary hypothesis: `H6_public_good_control_plane`.

Potentially transferable:

```text
evidence
→ bad-state transition
→ driver/access diagnosis
→ smallest feasible intervention
→ authority boundary
→ verified outcome
→ recurrence learning
```

Not transferable:

- animal population-control rules;
- ownership constructs;
- animal capture/return logic;
- animal-specific welfare optimization;
- any assumption that humans should be managed analogously to animals.

A human system requires explicit rights, legal entitlement, informed consent/autonomy, anti-discrimination, due process, political agency, privacy and dignity rules.

## Falsifiable programme hypotheses

### H1 — Access, not only scarcity

A meaningful share of observed welfare failures may arise because existing resources/services are unaffordable, geographically inaccessible, transport-infeasible, unknown or capacity constrained rather than absolutely absent.

**Failure condition:** verified cases mostly remain true absolute scarcity after access evidence is collected.

### H2 — Prevention before downstream rescue

Intervening at the transition into surrender, unmanaged displacement or severe instability may reduce later rescue/shelter burden while preserving or improving welfare.

**Failure condition:** preventive intervention does not reduce bad-state transitions or introduces unacceptable welfare/safety tradeoffs.

### H3 — Recurrence reveals infrastructure gaps

Repeated transition failures may reveal a missing local service that can be addressed by extending an existing provider or launching a reversible initiative.

**Failure condition:** the new/extended service does not reduce recurrence or existing services can solve the same problem more safely/cheaply.

### H4 — One Welfare coupling matters operationally

Human and environmental effects may sometimes materially change the best animal-welfare intervention.

**Failure condition:** cross-domain effects are negligible or never change intervention ranking in tested cases.

### H5 — Capability-based social integration

Longitudinal capability/preference evidence may improve welfare-positive placement/participation stability relative to binary adoptable/working labels or one-time assessments.

**Failure condition:** richer longitudinal evidence does not improve welfare or stability.

### H6 — Architecture-only transfer

The abstract control-plane machinery may remain useful in another public-good domain once rebuilt under that domain's own constitution.

**Failure condition:** the apparent architecture depends materially on animal-specific assumptions and fails in a separately constituted human domain.

## Candidate papers

1. **From Rescue to Preventive Welfare Infrastructure: A One Welfare Framework for Adaptive Companion-Animal Support**
2. **Evidence-Bounded Adaptive Intervention Planning for Regional Animal Welfare**
3. **From Rescue to Membership: Capability-Based Social Integration of Displaced Companion Animals**
4. **Socio-Economic and Additionality Evaluation of Local Animal-Welfare Interventions**
5. **Public-Good Control Planes: What Animal Welfare Can and Cannot Teach Human Welfare Systems**

These are research directions, not publication or novelty claims. Formal literature review, empirical data and external validation are required before submission.

## Evidence ladder

### R0 — architecture only
Synthetic fixtures establish logical behavior and safety invariants.

### R1 — retrospective replay
Historical/partner cases test whether the engine classifies transitions and bottlenecks plausibly without influencing intervention.

### R2 — shadow operation
The engine produces recommendations prospectively; qualified humans operate normally and independently judge whether recommendations were correct/useful.

### R3 — reversible supervised intervention
One bounded real intervention occurs with explicit authority and pre-registered outcome/stop criteria.

### R4 — repeated-area evaluation
Multiple interventions allow recurrence, cost, service access and population outcomes to be compared longitudinally.

### R5 — independent replication / second domain
Another operator or site reproduces the result; only after the animal domain is credible should architecture-only transfer be tested elsewhere.

## Development doctrine

Do not build an actuator merely because it is easy.

New engineering should be justified by one of:

- a verified recurring transition failure;
- a missing evidence/measurement capability needed to test a registered hypothesis;
- an external pilot partner's concrete workflow gap;
- an evaluation weakness that could otherwise produce false success claims.

Otherwise freeze software and acquire real evidence.
