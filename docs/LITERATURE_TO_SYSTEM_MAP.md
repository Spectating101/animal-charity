# Literature → System Map

This document connects the research literature to the repository's concrete constructs, code paths, hypotheses and claim boundaries. It is not a novelty claim or a substitute for a formal systematic review.

## Why this exists

The project began as feed-relief coordination and expanded into a regional welfare control plane. The literature indicates that the useful research object is broader: companion-animal welfare failures often sit inside coupled human-animal-service systems involving poverty, housing, transport, information, care access, local population dynamics and fragmented institutions.

The project therefore treats animal welfare as a bounded testbed for **preventive public-good systems methods**.

## 1. One Welfare

**Literature construct**

One Welfare connects animal welfare, human wellbeing and environmental conditions rather than treating them as isolated domains.

**System translation**

- keep animal, human and environmental outcome channels separate;
- allow one intervention to affect multiple domains;
- never hide an adverse domain inside one composite score;
- use cross-domain effects to change intervention choice when evidence supports it.

**Code**

- `app/preventive_welfare.py` — `OneWelfareDomain`
- `app/population_metrics.py` — separate population/safety/ecology/welfare indicators
- `config/missions/animal_welfare_integration.json` — `one_welfare_domains`

**Research question**

`H4_coupled_one_welfare`

## 2. Social determinants of companion-animal welfare

**Literature construct**

Human income, housing, transportation, owner health, information access and access to veterinary/behavioral/food support can affect companion-animal welfare and relinquishment risk.

**System translation**

Area-level deprivation is **context**, not proof that a particular owner caused a welfare failure. Determinants are tracked with explicit causal status:

- `context`
- `hypothesis`
- `established`

Household/subject evidence can support bounded case reasoning; area context can prioritize investigation only.

**Code**

- `app/preventive_welfare.py` — `DeterminantObservation`, `DeterminantKind`
- `config/missions/animal_welfare_integration.json` — causal-status and anti-culpability rules

**Research question**

`H2_prevention_beats_downstream_rescue`, `H4_coupled_one_welfare`

## 3. Welfare deserts / access-to-care barriers

**Literature construct**

A service can exist yet remain functionally inaccessible because of affordability, distance, transport, information, language, operating capacity or other practical barriers.

**System translation**

The engine must distinguish:

```text
service exists
    ≠
service accessible
    ≠
service used
    ≠
problem resolved
```

Access is therefore represented dimension-by-dimension rather than as a binary service-present flag.

**Code**

- `app/preventive_welfare.py` — `ServiceAccessObservation`
- access dimensions: availability, affordability, geography, transport, information, capacity
- `app/welfare_landscape.py` — distinguish capability evidence from condition evidence

**Research question**

`H1_access_not_scarcity`

## 4. Shelter diversion and owner retention

**Literature construct**

Not every threatened relinquishment needs to become shelter intake. Supported self-rehoming, temporary support and targeted owner assistance can preserve stable relationships or divert animals from shelters.

**System translation**

The control plane prefers repairing a safe existing home when the barrier is concrete and solvable.

Examples:

```text
vet bill gap → veterinary assistance
short food crisis → temporary food support
owner hospitalization → temporary foster
lost owned animal → reunification
housing/time issue → targeted retention or rehoming support
```

**Code**

- `app/animal_welfare_control.py` — owner-retention and reunification routes
- `app/preventive_welfare.py` — bad-state transition mapping
- `app/welfare_outcomes.py` — stable follow-up rather than transaction counting

**Research question**

`H2_prevention_beats_downstream_rescue`

## 5. Dog population management as a system

**Literature construct**

Humane dog population management uses combinations of sterilization, registration, responsible ownership, adoption/rehoming, vaccination, community engagement and local adaptation. Intervention mixes should reflect local dog ecology and human behavior and should be evaluated over time.

**System translation**

Do not encode one universal intervention such as TNR/TNVR, sheltering or removal. Diagnose which transition is generating unmanaged animals in the actual area.

**Code**

- `app/animal_welfare_control.py` — source-control / reunification / placement routing
- `app/lifecycle_initiatives.py` — repeated source-control and service-gap planning
- `app/population_metrics.py` — longitudinal area comparison

**Research question**

`H3_structural_recurrence`, `H4_coupled_one_welfare`

## 6. Socio-economic evaluation gap

**Literature construct**

Published socio-economic assessment of dog-population-management systems is sparse and heterogeneous. The 2025 scoping review by Ghimire et al. identified only 14 eligible studies from more than 7,200 screened records and called for standardized cost, benefit and social-impact data.

**System translation**

Every structural initiative should eventually expose:

- implementation cost and operator burden;
- service coverage;
- welfare outcomes;
- recurrence before/after;
- safety/ecology side effects;
- utilization;
- additionality/counterfactual note;
- stop conditions.

**Code**

- `app/structural_initiatives.py`
- `app/lifecycle_initiatives.py`
- `app/population_metrics.py`
- `app/welfare_outcomes.py`

**Research question**

`H3_structural_recurrence`, `H6_public_good_control_plane`

## 7. Stable social integration and animal participation

**Literature construct**

Animal-labour ethics, working-dog selection, foster/adoption research and animal-assisted-intervention welfare all support parts of a broader idea: different animals fit different social environments and roles, and welfare/agency must constrain participation.

**System translation**

The desired endpoint is **stable welfare-positive integration**, not maximum productivity.

Possible successful endpoints include:

- safe owner reunification;
- retained existing home;
- ordinary companion home;
- foster-to-adoption;
- sanctuary;
- responsible community placement where appropriate;
- optional specialist therapy/assistance/working referral for a small suitable subset.

A working role is never required to justify care.

**Code**

- `app/animal_welfare_control.py` — specialist referral only
- `app/welfare_outcomes.py` — stress/relapse as failure signals
- deeper longitudinal capability/preference profiling remains future work

**Research question**

`H5_social_integration`

## 8. Preventable bad-state transitions

This is the project's unifying systems abstraction.

Instead of only asking **who is suffering now?**, the system asks:

> Which transition into a worse welfare state is occurring, and can it be interrupted earlier?

Examples:

```text
stable owned → crisis → relinquishment
lost owned → prolonged displacement
intact roaming → new unmanaged litter
placement-ready → prolonged unstable care
acute injury → delayed stabilization
```

The same abstract machinery may later be testable in human public-good domains, for example:

```text
stable tenancy → arrears → eviction → homelessness
stable food access → income shock → food insecurity
independent elder → service-access failure → preventable crisis
```

But only the **architecture** transfers. Human systems require their own constitution for rights, autonomy, entitlement, consent, due process, anti-discrimination and dignity.

## Current primary literature anchors

The repository's conceptual map is currently grounded in, among others:

1. Ghimire R, Mohanty P, Hiby E, Larkins A, Dürr S, Hartnack S. *Socio-economic assessment of dog population management systems: a scoping review.* Frontiers in Veterinary Science, 2025. DOI: 10.3389/fvets.2025.1519913.
2. *The Impact of the Social Determinants of Human Health on Companion Animal Welfare.* Animals, 2023. PMCID: PMC10044303.
3. *Predictors of successful diversion of cats and dogs away from animal shelter intake: Analysis of data from a self-rehoming website.* 2023. PMCID: PMC10936303.
4. World Organisation for Animal Health (WOAH), Terrestrial Animal Health Code chapter on dog population management.

These references support adjacent constructs; they do **not** establish that this repository's synthesis is novel or effective.

## Research discipline

The project should fail closed on research claims:

- no crisis from capability data alone;
- no causation from area deprivation alone;
- no welfare desert from distance alone;
- no success from handoff/transaction alone;
- no structural programme from one incident;
- no social value requirement for care;
- no human-policy transfer from animal rules.

The machine-readable hypotheses and falsification criteria live at:

`config/research/public_good_research_programme.json`
