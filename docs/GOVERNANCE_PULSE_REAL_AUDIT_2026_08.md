# Real-data audit — dual-frontier governance pulse (August 2026)

## Audit question

Does the proposed monthly `stress + progress` governance pulse actually help decision-making when applied to messy real public disaster reporting, or does it merely produce a balanced-looking dashboard?

This audit uses two current Indonesian disaster topics:

1. August 2026 wildfire / karhutla management;
2. the August 2026 M7.7 NTT/Flores earthquake response and early recovery.

The audit deliberately uses public reporting rather than a live EOC/incident-command feed. This is a harder provenance/interpretation test but cannot validate operational allocation effectiveness.

## External reference logic

The design is consistent with established learning practice, but is not claimed as a replacement for it.

- WHO After Action Review asks what actually happened, what went well, what went less well, why, and how to improve. It is a continuous-learning mechanism rather than a simplistic performance score.
- UNDRR monitoring/reporting commonly surfaces progress, persistent gaps and good practices together and emphasizes implementation and monitoring rather than strategy announcements alone.
- Positive-deviance logic motivates studying unexpectedly successful cases, but only after identifying a meaningful comparison group and examining what differs under comparable constraints.

Reference starting points:

- https://www.who.int/emergencies/operations/emergency-response-reviews/after-action-review
- https://www.who.int/publications/i/item/WHO-WHE-CPI-2019.4
- https://www.undrr.org/publication/documents-and-publications/global-synthesis-report-comprehensive-risk-management
- https://www.undrr.org/2025-global-status-national-DRR-strategies

## Initial v0 hypothesis

The initial pulse had three intuitive lanes:

```text
adverse / unresolved stress
verified progress
response activity
```

and prohibited a net positive-minus-negative governance score.

That basic idea survived. Four material flaws did not.

## Finding 1 — activity and operational output must be separated from target-state progress

### Real test

NTT public reporting includes all of the following at the same time:

- more than 5,000 people displaced and extensive facility damage;
- the Larantuka–Maumere land route reported connected/passable;
- the Ende–Nagekeo land connection still cut;
- a field hospital established and operating in Reok;
- relief supplies physically arriving on Palue;
- major air-logistics flights carrying emergency supplies;
- electricity infrastructure approaching restoration.

The first implementation correctly separated deployment activity, but still allowed an `output` marked improvement into the progress frontier.

That is too permissive.

`field hospital opened` is important implementation evidence, but it is not yet equivalent to `patients have adequate emergency-care access`.

`aid arrived on island` is important implementation evidence, but it is not yet equivalent to `affected households received adequate aid`.

### Correction

The pulse now has separate lanes:

```text
response_activity
operational_outputs
progress_frontier (outcome/system only)
```

In the NTT audit fixture:

- road reconnection and electricity restoration enter target-state progress;
- field-hospital operation and Palue logistics arrival remain operational outputs;
- large aid flights remain response activity;
- deaths/displacement and the still-cut Ende–Nagekeo route remain adverse.

This prevents announcement/delivery theater from becoming welfare success.

## Finding 2 — publication time is not condition time

### Real test

A Reuters report published on 18 August describes nearly 95,000 hectares burned during **July**.

That is important new information learned in August, but it does not by itself prove that the same national condition is current on 18 August.

Conversely, Reuters reporting on 21 August describes a **recent rise in Kalimantan hotspots** and current prioritization of the region.

### Correction

Signals may now carry an effective condition period separately from `observed_at` / report time.

A report whose effective condition period ended before the pulse starts is routed to:

```text
lagged_context
```

rather than the current stress/progress frontier.

The July burned-area surge therefore remains highly relevant historical/risk context while the current August wildfire frontier uses August evidence such as the priority-province burden and current hotspot rise.

## Finding 3 — direction and significance were too editorial

The first implementation accepted manually supplied:

```text
direction = adverse / improvement
significance = major / critical
```

without forcing an explicit evidence rationale.

That could quietly turn the control plane into an opinionated headline ranker.

### Correction

- adverse/improvement signals require a `direction_basis`;
- major/critical signals require a `significance_basis`;
- response activity must use `direction=ambiguous` because activity alone cannot establish state improvement.

This does not make classification objective, but it makes the judgment attributable and reviewable.

A future production implementation should replace free-form significance with domain-specific severity rubrics where suitable.

## Finding 4 — local successes and national failures are not direct comparators

Wildfire reporting can simultaneously contain:

- national/multi-region severe burned-area/haze pressure;
- a small district fire extinguished;
- several local incidents extinguished without fatalities.

All are relevant, but a small accessible surface fire is not a valid performance control for a large peat fire under different weather/access/exposure conditions.

### Correction

Each signal now declares a geographic scope. Mixed scopes trigger an explicit warning.

Paired learning may use the frontiers to identify candidate questions, but practice transfer requires matching/normalizing at least:

- hazard/fire class;
- exposure and threatened population/assets;
- terrain/peat conditions;
- initial incident scale;
- weather;
- detection latency;
- access;
- available resources and commitments;
- command/authority context.

This is closer to positive-deviance logic: identify better outcomes, then determine whether the comparison group is genuinely meaningful before inferring a practice worth testing.

## Finding 5 — incomplete source coverage makes “best/worst of month” too strong

Neither the wildfire nor NTT public audit fixture is an exhaustive source census.

A pulse assembled from a few BNPB/Reuters reports cannot honestly claim:

> the worst event of the month

or

> the best government success of the month.

### Correction

Pulse inputs now state:

```text
coverage_status
selection_protocol
known_gaps
```

Unless the corpus is genuinely complete under the stated protocol, the system must use language such as:

> highest-priority adverse signal observed in this bounded corpus

rather than an objective monthly superlative.

This is one of the most important safeguards against source-selection bias.

## Finding 6 — verified gain does not prove which practice should be preserved

A successful outcome can justify:

- regression watch;
- preservation of the **gain/state** from accidental deterioration;
- investigation of associated practices.

It does not justify asserting that an associated intervention caused the success.

The pulse therefore treats intervention-associated successes as learning/preservation-review candidates, not established best practices. The next action explicitly says to avoid removing associated capability without review while mechanism evidence is collected.

## Finding 7 — the audit exposed an unrelated replay-time bug

During the stricter audit, the inherited wildfire-UAS actuator test began failing because a synthetic historical action intent was evaluated against real wall-clock time and had now expired.

Earlier CI had passed only because the test was run before the synthetic expiry time.

That means historical/shadow actuator evaluation was not fully deterministic.

The evaluator now accepts an explicit timezone-aware `as_of` time. Historical tests use the incident snapshot time; live operation may continue to default to current time.

This is an example of the governance-review layer improving another subsystem rather than merely reporting on it.

## What works after the audit

The pulse is useful for **problem selection and learning discipline** because it can hold contradictory-looking facts without collapsing them:

```text
NTT:
severe deaths/displacement/damage       -> stress
Ende–Nagekeo route still cut            -> stress
Larantuka–Maumere route reopened        -> progress
field hospital operational              -> output
Palue aid arrival                        -> output
40.6 t air logistics                     -> activity
electricity near restoration             -> progress
```

and:

```text
WILDFIRE:
current multi-region burden/haze         -> stress
current Kalimantan hotspot rise          -> stress
July burned-area surge learned in Aug    -> lagged context
Kubu Raya ground + air suppression       -> activity
local fires actually extinguished        -> progress / learning candidates
```

The value is not balance. The value is that each lane asks a different governance question.

## Questions generated for action/research

For current stress:

> Which broken edge keeps this condition open?

For activity:

> What output/outcome evidence should this action produce, and did it?

For output:

> Did the operational product actually reach/change the target condition?

For progress:

> Is the gain durable, what must not regress, and which comparable cases can test why it occurred?

For lagged context:

> Is there current evidence that the prior-period problem persists?

## Remaining weaknesses before governance-grade use

### 1. Source-selection pipeline is not automated/validated

Coverage metadata makes incompleteness explicit but does not solve it. A real monthly system needs a documented source universe, query/collection coverage, deduplication and missing-jurisdiction checks.

### 2. Significance remains judgmental

An explicit basis is better than an unexplained label, but domain-specific severity rubrics are still needed for more reproducible triage.

### 3. Comparability is warned about, not yet calculated

The current model detects mixed geographic scope, but does not yet construct risk-adjusted/matched cohorts. A later paired-learning evaluator should compare like with like before generating transfer hypotheses.

### 4. Causal inference remains intentionally weak

The system can produce learning candidates, not intervention-effect estimates. Replay, longitudinal comparison, shadow operation or stronger quasi-experimental designs are required before causal claims.

### 5. Public reporting is not an operational feed

The pulse is appropriate for strategic/monthly review from public evidence. It is not a substitute for live EOC resource state, incident command or field reporting.

### 6. Domain desired-state definitions matter

`improvement` only makes sense relative to an explicit domain constitution/desired state. This must remain domain-specific rather than becoming universal political sentiment analysis.

## Current verdict

**Concept validity: strong.**

The dual-frontier idea survived real wildfire and earthquake evidence and maps well to established after-action / continuous-learning practice.

**Implementation validity: promising R0/R1 governance-learning primitive, not yet validated decision authority.**

The real audit materially changed the model in ways that reduce propaganda, pessimism, temporal confusion and implementation-theater risk.

**Best current use:**

- monthly/operational governance review;
- problem prioritization;
- preservation/regression watch;
- identifying unverified response outputs;
- generating matched learning/replay hypotheses;
- producing evidence requests for the next period.

**Not yet justified:**

- government performance scoring;
- objective best/worst-of-month claims from partial sources;
- automatic policy replication from a positive case;
- causal claims that an intervention produced an observed improvement;
- live autonomous resource allocation.

The next highest-value validation is not another dashboard feature. It is a **matched paired-case evaluator**: choose an adverse case and a better-performing case under sufficiently similar hazard/exposure constraints, enumerate material differences, then test those hypotheses across the replay corpus before any transfer recommendation.
