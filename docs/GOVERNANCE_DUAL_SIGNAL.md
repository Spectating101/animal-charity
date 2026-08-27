# Dual-signal governance: stress and progress frontiers

## Why

A governance system that only ingests adverse reporting becomes structurally pessimistic: every month looks like accumulating failure even when some interventions, institutions or local operating practices are working.

A system that only highlights success stories has the opposite failure: it can erase unresolved harm and encourage premature claims that a programme or response is working.

The control plane therefore maintains two parallel evidence frontiers:

```text
UNRESOLVED STRESS                 VERIFIED PROGRESS
what is worsening?                what measurably improved?
what remains unmet?               where did the state get better?
what repeatedly fails?            what practice is worth studying?
        |                                  |
        +---------------+------------------+
                        |
                 governance learning
                        |
              preserve / correct / test
```

They are **not combined into a net sentiment or moral score**.

A successful local response cannot cancel deaths, burned area, unmet water need or another unresolved failure elsewhere. Likewise, a severe national problem does not make a genuinely successful local outcome irrelevant.

## Relationship to "worst news" / "good news"

The colloquial monthly question can be useful:

- What is the worst evidence this month telling us?
- What is the best evidence this month telling us?

But the control plane should not rank journalism by emotional tone or popularity. It translates source material into state-change evidence:

- `adverse`: deterioration, unresolved need, recurrence, failure or elevated risk;
- `improvement`: verified movement toward a desired state;
- `ambiguous`: evidence whose direction cannot yet be established.

Each signal also has an evidence level:

- `activity`: something was attempted/deployed/spent;
- `output`: a direct operational product was delivered;
- `outcome`: the target condition measurably improved;
- `system`: a wider or persistent condition changed.

**Activity is not progress.**

`540 personnel deployed`, `a helicopter arrived`, `a grant was announced`, `a supplier was contracted` and `a drone flew` can all be important evidence while still failing to establish that the public-good state improved.

## Current August 2026 wildfire example

The fixture `examples/governance_pulse_indonesia_wildfire_aug_2026.json` deliberately contains both sides of the same domain/topic.

### Stress frontier

Public August reporting includes severe system-level fire conditions: national July burned area was reported near 95,000 hectares, while BNPB reported roughly 48,889.69 hectares burned across six priority provinces through 9 August, alongside air-quality and cross-border haze concerns.

Those remain adverse governance signals even though many individual fires were successfully handled.

### Progress frontier

BNPB also reported multiple local incidents being extinguished, including a Paser incident and several 8-10 August fires with no fatalities.

These outcomes matter because they create **learning candidates**:

> What was different in the places that contained the incident successfully?

But the system must not jump from correlation to causation. A local outcome accompanied by `ground response + water bombing` does not establish that one component caused containment.

### Response activity

Kubu Raya's documented simultaneous ground suppression and helicopter water bombing is kept in a separate activity lane.

That activity may later become part of a causal or operational explanation, but it is not itself a success outcome.

## Governance learning loop

The intended monthly/intra-action loop is:

```text
adverse frontier
    -> what is failing / worsening / recurring?

progress frontier
    -> where did the target state actually improve?

matched topic review
    -> what differs between failure and improvement cases?

hypothesis
    -> access? staffing? timing? equipment? authority? terrain? prevention?

replay / shadow test
    -> does the proposed explanation survive more cases?

action
    -> preserve effective practice / correct failing edge / test transfer

next period
    -> did the state improve?
```

This is aligned with the logic of WHO Action Reviews: identify what worked, what worked less well, why, and how to improve. It also fits UNDRR monitoring logic that considers promising trends and persistent gaps together.

## Nocturnal boundary

Nocturnal should not become a cheerleader or outrage ranker.

Its job remains coverage and longitudinal public memory:

```text
source -> event -> matter -> later development
```

The governance control plane can then consume those developments and classify their **public-good state direction** for a specific domain constitution.

Example:

```text
Nocturnal:
"BNPB reports fire contained in Paser"

Governance control plane:
improvement / outcome / wildfire_management
```

or:

```text
Nocturnal:
"hotspots rise and Kalimantan becomes priority region"

Governance control plane:
adverse / system / wildfire_management
```

The journalism layer preserves what happened. The governance layer asks what that development means for the desired state and what should be learned or changed.

## Safety / claim boundaries

- progress does not offset unresolved harm;
- response activity is not outcome success;
- a successful outcome does not establish which intervention caused it;
- a practice seen in one location is a study candidate, not automatically a replication recommendation;
- source coverage is incomplete, so absence from the pulse is not proof that no adverse/progress signal exists;
- monthly frontiers should remain domain/topic-scoped rather than becoming a universal score of whether a government is "good" or "bad";
- consequential policy/action still follows the domain constitution and authority gates.

## Next research step

Use the paired frontiers to generate deliberately testable questions.

For wildfire response, examples include:

- Are local fires being contained faster where detection latency is lower?
- Does combined ground/aerial capability improve containment only under certain terrain/fire classes?
- Are successful cases associated with accessible water sources or better local staging?
- Which recurring failures remain even where suppression capacity appears adequate?
- Which local successes survive the next dry-season recurrence test?

The control plane should answer these through replay, longitudinal evidence and eventually shadow operations rather than by reading positive headlines and declaring a best practice.
