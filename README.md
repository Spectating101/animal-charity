# Animal Welfare Control Plane / AFRN

**Evidence-bounded preventive welfare infrastructure for regional companion-animal systems.**

The project has evolved from a feed-relief matcher into a research/pilot stack for asking a harder question:

> **Where is a local animal-welfare system allowing preventable deterioration, why is that transition happening, what existing capability could stop it, and when does repeated failure justify creating new public-good infrastructure?**

The project does **not** try to replace shelters, vets, foster networks, TNVR programmes, food banks, adoption organizations, municipal animal control or assistance/therapy-dog specialists. It tests whether a persistent bounded control layer can help a region use those capabilities more coherently, expose access failures, and learn which preventive interventions actually work.

> **Status:** stacked v0 research/pilot candidate. No live animal-welfare outcome is claimed yet.

## Consolidated six-layer stack

1. **Preventive Welfare Systems Layer** — One Welfare + social/service determinants + welfare-desert/access reasoning. Models affordability, geography, transport, information and capacity without promoting area context into individual causal claims.
2. **Animal Welfare Lifecycle Control Plane** — identifies the failing animal transition and routes toward emergency stabilization, reunification, owner retention, source control, foster/adoption, responsible community care or specialist referral.
3. **Welfare Landscape Engine** — distinguishes condition evidence from capability/context evidence, detects credible welfare problems and refuses to invent missing facts.
4. **Structural Initiative Planners** — detect repeated transition failures and compare existing-service extension, reversible periodic/mobile pilots and permanent infrastructure.
5. **Actuators** — concrete execution modules such as feed allocation, transport, owner-support referrals, source-control outreach, foster recruitment and rescue escalation. AFRN feed matching is one actuator, not the thesis.
6. **Outcome + Population Evaluation** — verifies downstream welfare states, preserves longitudinal history, rejects unverified handoff as success, and guards against apparent improvement caused by reduced observation coverage.

Research foundations and transfer doctrine:

- [`docs/PREVENTIVE_WELFARE_RESEARCH.md`](docs/PREVENTIVE_WELFARE_RESEARCH.md)
- [`config/research/preventive_welfare_framework.json`](config/research/preventive_welfare_framework.json)
- [`docs/ANIMAL_WELFARE_CONTROL_PLANE.md`](docs/ANIMAL_WELFARE_CONTROL_PLANE.md)

## Common public-good loop

`observe → identify bad-state transition → verify driver/access barrier → prefer existing service → select smallest feasible intervention → human/professional authority → verify outcome → detect recurrence → propose reversible structural fix → evaluate landscape`

The central research abstraction is the **preventable bad-state transition**.

Examples:

```text
stable owner → household/vet/housing shock → surrender risk → shelter or abandonment
```

```text
reproductively active roaming animals → unmanaged reproduction → new unmanaged animals
```

```text
placement-ready animal → no foster capacity → prolonged unstable care → delayed/failed integration
```

The system aims to intervene as early as credible evidence allows rather than merely responding after the expensive bad state is fully realized.

## One Welfare + service-access reasoning

The preventive layer represents social and service determinants such as:

- income and affordability;
- housing instability;
- transportation;
- veterinary access;
- food access;
- information/language access;
- social support;
- service/foster capacity;
- population-control access;
- owner health/time capacity;
- public-safety and ecological context.

Service access is decomposed into:

`availability · affordability · geography · transport · information · capacity`

This prevents a common reasoning error:

`service exists` **does not imply** `service is accessible`.

Likewise:

`low-income area` **does not imply** `specific owner caused neglect`.

Causal status is explicit:

- `context` — prioritizes investigation only;
- `hypothesis` — plausible case-linked driver requiring verification;
- `established` — sufficiently direct evidence for operational reasoning.

## Preventive welfare systems experiment

```bash
python scripts/assess_preventive_welfare.py examples/zhongli_sanmin_synthetic_preventive_system.json
```

The fixture is entirely synthetic at the animal/determinant level. It tests repeated source-control cases plus suspected access friction and a structured service-access gap.

Correct behavior:

- source-control is recognized as a repeated structural candidate;
- geography/transport/capacity failures appear as access gaps;
- the suspected determinant remains `hypothesis`, not asserted cause;
- the output explicitly states that only the architecture—not animal-policy rules—may later generalize to human welfare.

Authenticated equivalent:

`POST /v1/welfare/system/assess`

## Lifecycle priority

`acute stabilization → prevent new unmanaged recruitment → reunify/retain safe homes → stabilize basic welfare → foster/adoption/community/sanctuary pathway → optional specialist role for a small suitable subset`

A dog never needs to become a therapy/assistance/working animal to justify rescue or care. Specialist roles are **referral-only**, require independent qualified assessment, and must stop if welfare deteriorates.

Machine-readable welfare constitution:

- [`config/missions/animal_welfare_integration.json`](config/missions/animal_welfare_integration.json)

## Taoyuan / Zhongli Sanmin experiment

Taiwan MOA's 2026 priority-area list identifies Zhongli Sanmin Li as a Level-1 roaming-dog public-safety-priority area. The repository uses that **only as area policy context**.

```bash
python scripts/assess_animal_welfare.py examples/zhongli_sanmin_policy_baseline.json
python scripts/assess_animal_welfare.py examples/zhongli_sanmin_synthetic_lifecycle.json
```

The policy-only fixture contains zero animal-level condition observations and therefore must produce zero animal-level interventions.

The separate synthetic lifecycle fixture tests:

- lost owned dog → reunification;
- preventable owner surrender → targeted owner-retention support;
- repeated reproductively active roaming dogs → source control + structural signal;
- placement-suitable animal → foster pathway;
- injured animal → emergency stabilization;
- unusually suitable dog → specialist referral only.

See [`docs/TAOYUAN_SANMIN_CONTROL_EXPERIMENT.md`](docs/TAOYUAN_SANMIN_CONTROL_EXPERIMENT.md).

## Landscape diagnosis

```bash
python scripts/scan_landscape.py examples/taoyuan_public_baseline.json
python scripts/scan_landscape.py examples/taoyuan_synthetic_incident.json
```

The real public-capability fixture contains no claimed live crisis. Correct output is zero active cases plus explicit data gaps.

The synthetic feed incident has 1.8 days coverage, compatible feed nearby and no transport. Correct diagnosis is:

`last_mile_logistics → logistics.dispatch_request`

not “source more food.”

## Structural planning

Food/logistics structural experiment:

```bash
python scripts/plan_initiative.py examples/taoyuan_public_structural_baseline.json
python scripts/plan_initiative.py examples/taoyuan_synthetic_structural_cluster.json
```

Generic lifecycle initiative experiment:

```bash
python scripts/plan_lifecycle_initiatives.py examples/zhongli_sanmin_synthetic_source_control_history.json
```

One incident can never create standing infrastructure. Existing-service extension is preferred; reversible periodic/mobile pilots are preferred over premature permanent facilities.

## Feed actuator (AFRN)

`observe inventory → forecast → NeedCase → hard gates → eligible supply → proposal → human approval → delivery evidence → verified resolution`

The autonomous feed agent cannot approve recipient eligibility/diet, dispatch feed, close an incident or declare resolution. Those remain named-human transitions.

Machine-readable feed mission:

- [`config/missions/animal_feed_security.json`](config/missions/animal_feed_security.json)

## Outcome and longitudinal evaluation

The project intentionally rejects transaction-count success.

- handoff without verified outcome is not success;
- an adoption/placement that collapses back into a bad state is a failure;
- specialist training with sustained stress is a welfare stop;
- lower reported roaming counts are not improvement if observation coverage collapsed;
- animal welfare, human/public-safety and ecological outcomes stay visible separately rather than being buried in one composite score.

Nocturnal-style adapters preserve proposals and outcomes as separate longitudinal events so later evidence can correct earlier conclusions.

## Human poverty / food-security transfer boundary

Animal welfare is being used as a **systems-method testbed**, not as a proxy population for human social policy.

Potentially transferable architecture:

`evidence → bad-state transition → driver/access diagnosis → intervention → authority → outcome → recurrence learning`

Animal-specific policy rules must not transfer.

Any future human-welfare system requires a separate constitution for rights, legal entitlements, autonomy/informed consent, political agency, anti-discrimination, privacy/due process, housing/labor/benefit law and self-determination.

See [`docs/PREVENTIVE_WELFARE_RESEARCH.md`](docs/PREVENTIVE_WELFARE_RESEARCH.md).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AFRN_DEMO_MODE=1
python scripts/seed_demo.py
fastapi dev app/main.py
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- Ledger health: `http://127.0.0.1:8000/health`

Or:

```bash
cp .env.example .env
# set AFRN_OPERATOR_TOKEN
docker compose up --build
```

## Operator/research API surface

| Surface | Purpose | Authority |
|---|---|---|
| `POST /v1/welfare/assess` | lifecycle transition routing | operator/agent proposal only |
| `POST /v1/welfare/system/assess` | preventive One Welfare + determinant/access assessment | operator/agent proposal only |
| `POST /v1/welfare/outcomes/summarize` | classify verified downstream outcomes | operator read/evaluation |
| `POST /v1/recipients` | record feed-relief partner candidate | operator |
| `POST /v1/recipients/{id}/review` | activate/suspend recipient | **human only** |
| `POST /v1/groups` | record animal demand | operator |
| `POST /v1/inventory` | record current feed | operator |
| `POST /v1/supplies` | record candidate supply | operator |
| `POST /v1/agent/tick` | run bounded feed cycle | agent/operator |
| `POST /v1/proposals/{id}/review` | approve/reject feed proposal | **human only** |
| `POST /v1/cases/{id}/resolve` | close feed case with evidence | **human only** |
| `GET /v1/audit/events` | append-only operational history | operator read |
| `GET /v1/audit/nocturnal-export` | Nocturnal-style longitudinal export | operator read |

## Verify

```bash
make verify
```

The gauntlet covers:

- feed safety/authority/audit invariants;
- landscape non-hallucination;
- immediate bottleneck diagnosis;
- food structural planning;
- lifecycle routing;
- generic lifecycle initiative planning;
- preventive determinant/access reasoning;
- causal-status discipline;
- authenticated API boundaries;
- verified welfare outcomes;
- longitudinal export;
- population anti-gaming safeguards;
- compilation and Docker build.

## Launch gate

Do not call this a successful welfare system because the code runs.

The first credible external claim is:

> **A real preventable welfare transition was correctly established; its driver/access bottleneck was independently supportable; the selected intervention actually occurred; and verified outcome evidence shows a more stable welfare state without a serious animal-welfare, safety, privacy or audit failure.**

For structural initiatives, repeated unresolved burden must decline enough to justify the new programme relative to existing-service alternatives.

## Taiwan pilot note

All policy/rule fixtures are research/demo inputs, not veterinary or legal authorization. Real deployment requires local professional and competent-authority review. Public web sources may map policy context and service capabilities; they are not sufficient by themselves to accuse a person/organization or assert an individual animal's ownership, behaviour, health or welfare state.
