# Animal Welfare Control Plane / AFRN

**Evidence-bounded regional animal-welfare diagnosis, structural planning and intervention infrastructure.**

The project now has four stacked layers:

1. **Animal Welfare Control Plane** — model how animals enter and move through bad welfare states, identify the failing transition, and route toward reunification, owner retention, source control, foster/adoption, responsible community care, emergency rescue, or specialist referral.
2. **Welfare Landscape Engine** — distinguish condition evidence from mere service availability, identify credible problems, diagnose bottlenecks, and refuse to invent missing facts.
3. **Structural Initiative Planner** — detect repeated failures over time and ask whether an existing service should be extended or whether a reversible pop-up/mobile/new public-good initiative is justified.
4. **Feed Relief Actuator (AFRN)** — when the bottleneck is genuinely feed allocation, turn verified inventory + verified supply into accountable human-reviewed intervention proposals.

The thesis is **not** to replace shelters, vets, foster networks, TNR/TNVR programmes, food banks, adoption organizations or assistance-dog trainers. It is to test whether a persistent bounded control layer can help a region use those capabilities more coherently and reveal the smallest missing piece when they are insufficient.

> **Status:** stacked v0 research/pilot candidate. No live animal-welfare outcome is claimed yet.

## Regional welfare loop

`observe → establish animal/area state → identify failing transition → route existing intervention → verify outcome → detect recurrence → propose smallest structural fix → measure whether the landscape improves`

Lifecycle priority is deliberately welfare-first:

`acute stabilization → prevent new unmanaged recruitment → reunify/retain safe homes → stable foster/adoption/community/sanctuary path → optional specialist role for a small suitable subset`

A dog never needs to become a therapy/assistance/working animal to justify rescue or care. Specialist roles are **referral-only** and require independent qualified assessment.

See [`docs/ANIMAL_WELFARE_CONTROL_PLANE.md`](docs/ANIMAL_WELFARE_CONTROL_PLANE.md).

## Taoyuan / Zhongli Sanmin experiment

Taiwan MOA's 2026 priority-area list identifies Zhongli Sanmin Li as a Level 1 public-safety-risk roaming-dog management area. The repository uses that **only as area policy context**.

```bash
python scripts/assess_animal_welfare.py examples/zhongli_sanmin_policy_baseline.json
python scripts/assess_animal_welfare.py examples/zhongli_sanmin_synthetic_lifecycle.json
```

The policy-only fixture contains **zero animal-level condition observations**. Correct output is zero animal-level interventions plus explicit data gaps.

The synthetic lifecycle fixture tests distinct welfare pathways:

- lost owned dog → reunification;
- preventable owner surrender → targeted owner-retention support;
- repeated reproductively active roaming dogs → source-control decisions + structural signal;
- suitable foster candidate → foster placement;
- injured animal → emergency stabilization, overriding optimization;
- unusually suitable dog → specialist referral only.

See [`docs/TAOYUAN_SANMIN_CONTROL_EXPERIMENT.md`](docs/TAOYUAN_SANMIN_CONTROL_EXPERIMENT.md).

## Landscape diagnosis

```bash
python scripts/scan_landscape.py examples/taoyuan_public_baseline.json
python scripts/scan_landscape.py examples/taoyuan_synthetic_incident.json
```

The first fixture contains real publicly evidenced Taoyuan welfare capabilities but no claimed live crisis. Correct output is zero active problem cases plus explicit data gaps.

The second overlays an explicitly synthetic incident: 1.8 days of feed coverage, 80 kg of compatible feed already nearby, and no transport. Correct output is `last_mile_logistics` → `logistics.dispatch_request`, **not** the feed matcher.

## Structural initiative planning

```bash
python scripts/plan_initiative.py examples/taoyuan_public_structural_baseline.json
python scripts/plan_initiative.py examples/taoyuan_synthetic_structural_cluster.json
```

One incident can never create standing infrastructure. The current research-default gate requires repeated credible need across multiple subjects/dates/time plus evidence of a service/access gap. Existing services are preferred; reversible pop-ups/mobile routes are preferred over premature permanent infrastructure.

## Feed actuator

`observe inventory → forecast → open NeedCase → apply hard gates → rank eligible supply → propose → human approval → delivery evidence → resolution`

The autonomous feed agent **cannot** approve recipient eligibility, approve a diet, dispatch feed, close an incident, or mark a case resolved. Those remain named-human transitions backed by evidence.

```text
structured / Refinery-ready evidence
             ↓
      feed coverage forecast
             ↓
          NeedCase
             ↓
  versioned deterministic gates
       ↙ fail       pass ↘
 escalation        ranked match
                      ↓
                human approval
                      ↓
              physical operation
                      ↓
             resolution evidence
                      ↓
        append-only hash audit
                      ↓
        Nocturnal-compatible export
```

Machine-readable constitutions:

- [`config/missions/animal_welfare_integration.json`](config/missions/animal_welfare_integration.json)
- [`config/missions/animal_feed_security.json`](config/missions/animal_feed_security.json)

See [`docs/WELFARE_LANDSCAPE_ENGINE.md`](docs/WELFARE_LANDSCAPE_ENGINE.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md), and [`docs/PILOT.md`](docs/PILOT.md).

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

## Verify

```bash
make verify
```

Verification covers feed safety/authority/audit invariants, landscape non-hallucination, structural initiative gates, and lifecycle control-plane routing.

## Persistent feed agent

Run one cycle with `AFRN_AGENT_ONCE=1 python scripts/run_agent_loop.py`, or leave it running with `AFRN_AGENT_INTERVAL_SECONDS` (minimum 60 seconds). The mission manifest prevents the scheduler from crossing human-only authority boundaries.

## Feed API surface

| Surface | Purpose | Authority |
|---|---|---|
| `POST /v1/recipients` | record partner candidate | operator |
| `POST /v1/recipients/{id}/review` | activate/suspend recipient | **human only** |
| `POST /v1/groups` | record animal demand | operator |
| `POST /v1/inventory` | record current feed | operator |
| `POST /v1/supplies` | record candidate supply | operator |
| `POST /v1/agent/tick` | run bounded feed cycle | agent/operator |
| `GET /v1/cases` | unresolved/resolved need | operator read |
| `GET /v1/proposals` | pending matches | operator read |
| `POST /v1/proposals/{id}/review` | approve/reject | **human only** |
| `POST /v1/cases/{id}/resolve` | close with delivery evidence | **human only** |
| `GET /v1/audit/events` | append-only operational history | operator read |
| `GET /v1/audit/nocturnal-export` | map events to Nocturnal-style claims | operator read |

## Launch gate

Do not call this a successful welfare system because the code runs. The first credible external claim remains smaller and harder:

> **A real animal-welfare transition failure was correctly established, the selected intervention was independently supportable, the intervention actually occurred, and outcome evidence shows a more stable welfare state without a serious safety or animal-welfare incident.**

For any structural initiative, the additional claim must be that repeated unresolved burden fell enough to justify the new programme.

## Taiwan pilot note

All current policy/rule fixtures are research/demo inputs, not veterinary or legal authorization. A real deployment requires local professional and competent-authority review. Public web sources may map policy context and service capabilities; they are not sufficient by themselves to accuse an organization/person or assert an individual animal's ownership, behaviour, health or welfare state.
