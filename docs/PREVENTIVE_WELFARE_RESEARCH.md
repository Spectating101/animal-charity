# Preventive Welfare Research Foundations

## Research programme

This repository uses companion-animal welfare as a bounded domain for testing **persistent evidence-bounded public-good intervention**.

The research hypothesis is not that animal policy can be copied to human poverty. The hypothesis is that a reusable systems architecture can be tested here:

`observe → identify a bad-state transition → verify its drivers → repair the smallest access/resource/institutional gap → verify outcome → detect recurrence → build prevention only when justified`

The project therefore moves beyond isolated rescue or feed relief toward **preventive welfare infrastructure**.

## 1. One Welfare

One Welfare treats animal, human and environmental well-being as connected rather than independent objectives. A 2025 bibliometric review identified 111 substantive One Welfare publications from 2013–2024 and described the field as growing but still emerging.

Project implication:

- do not optimize animal throughput while ignoring household stability, public safety or ecological harm;
- preserve separate outcome families rather than one magic score;
- where an intervention crosses domains, measure coupled effects.

Reference:
- Platto S, Normando S, Serres A, Manteca X, Temple D. *One welfare: bibliometric review of world literature* (2025). https://pmc.ncbi.nlm.nih.gov/articles/PMC12427028/

## 2. Social determinants of companion-animal welfare

Companion-animal welfare is affected by human-side determinants including income, housing, transport, access to veterinary care, education/information and community support. The literature explicitly connects the Social Determinants of Health framework with One Health/One Welfare and preventive support.

Project implication:

A welfare transition such as:

`stable owner → financial/housing/health shock → surrender risk → shelter/unmanaged displacement`

must not automatically be interpreted as an animal or owner-behaviour problem. The control plane should test whether a small household or access intervention can preserve the stable relationship.

Reference:
- Card et al. *The Impact of the Social Determinants of Human Health on Companion Animal Welfare* (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10044303/

## 3. Animal welfare deserts and service access

Spatial research has identified **animal welfare deserts**: places where the distribution of veterinary and pet-support resources does not match need. Access barriers include affordability, geography, transport, information/language and practical service capacity.

A broader scoping review of veterinary-care access found financial limitations, geography and limited personnel/equipment among the most frequently reported barriers.

Project implication:

The system must distinguish:

`resource does not exist`

from:

`resource exists but is unaffordable / too far away / unreachable / unknown / full`.

This is why service access is represented by separate dimensions rather than a single `service_available` boolean.

References:
- Ly LH. *Animal welfare deserts: human and nonhuman animal inequities* (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10368398/
- LaVallee et al. *Access to veterinary care: evaluating working definitions, barriers, and implications for animal welfare* (2024). https://pmc.ncbi.nlm.nih.gov/articles/PMC10830634/

## 4. Prevention before shelter intake

Supported self-rehoming research shows that many animals can be diverted from shelter intake when owners receive alternative pathways. In one large analysis, 87.1% of dogs and 85.7% of cats using the studied platform were diverted from shelters; more than one-third remained with the original owner.

Project implication:

The unit of optimization should often be the **preventable transition**, not the bad state after it occurs.

Examples:

- vet-cost shock → targeted assistance before surrender;
- temporary owner hospitalization → temporary foster before relinquishment;
- lost owned animal → owner tracing/reunification before treating as unowned;
- repeated intact roaming animals → source-control access before new litters enter the unmanaged population.

Reference:
- Duffy et al. *Predictors of successful diversion of cats and dogs away from animal shelter intake* (2024). https://pmc.ncbi.nlm.nih.gov/articles/PMC10936303/

## 5. Dog population management is a system problem

Modern dog population management combines reproduction control, identification/registration, shelter/adoption, vaccination/community work and other measures rather than assuming one universal intervention.

A 2025 socio-economic scoping review screened more than 7,200 records but identified only 14 studies meeting its criteria for socio-economic assessment of dog-population-management systems. It highlighted weak standardized data, limited cost/benefit evaluation and the need for better tools and reporting.

Project implication:

This repo should become good at recording:

- intervention cost and operating burden;
- which population/transition was targeted;
- service/access context;
- non-monetary welfare and social outcomes;
- counterfactual/additionality notes;
- whether a cheaper existing service could have produced the same effect.

Reference:
- Ghimire R et al. *Socio-economic assessment of dog population management systems: a scoping review* (2025). https://www.frontiersin.org/journals/veterinary-science/articles/10.3389/fvets.2025.1519913/full

## 6. Bad-state transitions

The project uses **preventable bad-state transitions** as a common research abstraction.

Examples:

```text
owned_stable
  → owner shock
  → owned_at_risk
  → relinquishment
  → shelter / abandonment
```

```text
reproductively active roaming animals
  → unmanaged reproduction
  → new litters
  → unmanaged population growth
```

```text
placement-ready animal
  → no foster capacity
  → prolonged unstable care
  → welfare deterioration / delayed integration
```

The highest-value intervention may be the smallest verified action immediately before the transition becomes costly or difficult to reverse.

## 7. Prevention hierarchy

The control plane should prefer, subject to rights/safety/professional review:

1. prevent a bad transition;
2. repair access to an existing service;
3. resolve the case with the smallest feasible intervention;
4. extend an existing institution if failures recur;
5. run a reversible pilot if existing capacity cannot solve the pattern;
6. create permanent infrastructure only after sustained evidence;
7. verify that the landscape improves rather than merely producing more transactions.

This is the common logic linking owner retention, food relief, transport, sterilization, foster capacity, rescue response and other future actuators.

## 8. Stable welfare integration as the destination

The desired outcome is not simply `animal removed from street`, `adoption transaction`, or `working animal produced`.

The destination is **stable welfare integration**: a durable welfare-positive state appropriate to the individual animal, including reunification, retained safe ownership, companionship, foster-to-home placement, sanctuary, responsible community care where appropriate, or specialist social/working participation for a small suitable subset.

Social contribution never becomes a condition of care.

## 9. Research questions enabled by the consolidated architecture

### RQ1 — Transition diagnosis
Can an evidence-bounded system correctly distinguish absolute scarcity from access, information, transport, capacity, household and coordination failures?

### RQ2 — Preventive leverage
Which verified interventions prevent the most severe welfare deterioration per unit of cost/operating burden?

### RQ3 — Structural recurrence
When do repeated case-level failures justify a new local service rather than better routing into existing capacity?

### RQ4 — One Welfare effects
Do interventions that improve animal outcomes also preserve human-animal relationships, reduce household burden, improve public safety, or reduce ecological conflict?

### RQ5 — Stable integration
Which pathways produce durable welfare-positive social membership rather than repeated cycling through street/shelter/foster/return states?

### RQ6 — Evaluation and additionality
Can the system establish that an intervention caused or plausibly contributed to improvement rather than merely documenting activity that would have happened anyway?

## 10. Why this can be a public-good-agent testbed

Animal welfare provides a bounded environment in which the system can test:

- evidence ingestion and provenance;
- geographic/service-access reasoning;
- causal discipline;
- intervention routing;
- reversible structural planning;
- rights/authority gates;
- longitudinal outcome tracking;
- multi-objective evaluation;
- anti-gaming safeguards.

The testbed claim is architectural, not moral or policy equivalence.

## 11. Human-welfare transfer boundary

If the architecture later informs food insecurity, homelessness, elderly support or poverty intervention, only the abstract machinery may transfer:

`evidence → transition → driver/access diagnosis → intervention → authority → outcome → recurrence learning`.

Animal-specific policy rules must **not** transfer.

Human welfare requires a separate constitutional layer for at least:

- human rights and legal entitlements;
- autonomy and informed consent;
- political agency;
- anti-discrimination/equality;
- labor and housing law;
- privacy and due process;
- cash/credit/benefit systems;
- family/household complexity;
- self-determination and dignity.

The animal-welfare domain is therefore a **systems-method testbed**, not a proxy population for human-policy experiments.

## 12. Evidence doctrine

- Area deprivation is not proof that a specific owner cannot care for an animal.
- Service scarcity is not proof that it caused a specific welfare event.
- Correlation/area context remains `context`.
- Plausible but unverified drivers remain `hypothesis`.
- Subject/household or stronger evidence is needed before a driver becomes `established` for operational reasoning.
- Public policy priority is not individual-animal evidence.
- No intervention should be presented as successful until the downstream welfare state is verified.

This causal discipline is a core research artifact, not a documentation preference.
