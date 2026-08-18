# Animal Feed Relief Network

**Evidence-bounded public-welfare diagnosis + intervention infrastructure.**

AFRN now has two layers:

1. **Welfare Landscape Engine** — identify where a credible problem exists, distinguish condition evidence from mere service availability, diagnose the most likely bottleneck, and select the smallest feasible intervention without inventing missing facts.
2. **Feed Relief Actuator** — when the diagnosed bottleneck is genuinely feed allocation, turn verified shelter inventory + verified supply into accountable human-reviewed intervention proposals.

The project is deliberately not an AI that decides who "deserves" help, diagnoses veterinary conditions, or labels organizations negligent from weak public signals.

> **Status:** stacked v0 research/pilot candidate. Dogs/cats remain the only implemented feed actuator scope. No live charity impact is claimed yet.

## Public-welfare loop

`observe → verify → identify problem → diagnose bottleneck → choose intervention → human authority where required → act → verify outcome`

Examples of distinct bottlenecks the landscape layer can represent:

- compatible feed genuinely absent → sourcing/procurement;
- feed already exists but cannot move → last-mile logistics;
- feed and transport both exist → allocation/coordination → AFRN feed actuator;
- specific procurement shortfall → precise funding request;
- intake/capacity surge → foster/adoption/referral/capacity response;
- insufficient evidence → ask for evidence, do not guess.

See [`docs/WELFARE_LANDSCAPE_ENGINE.md`](docs/WELFARE_LANDSCAPE_ENGINE.md).

## Taoyuan landscape experiment

```bash
python scripts/scan_landscape.py examples/taoyuan_public_baseline.json
python scripts/scan_landscape.py examples/taoyuan_synthetic_incident.json
```

The first fixture contains **real, current publicly evidenced Taoyuan welfare capabilities but no claimed live crisis**. Correct output is zero active problem cases plus explicit data gaps.

The second overlays an explicitly synthetic incident: 1.8 days of feed coverage, 80 kg of compatible feed already nearby, and no transport. Correct output is `last_mile_logistics` → `logistics.dispatch_request`, **not** the feed matcher.

## Feed actuator

`observe inventory → forecast → open NeedCase → apply hard gates → rank eligible supply → propose → human approval → delivery evidence → resolution`

The autonomous feed agent **cannot** approve recipient eligibility, approve a diet, dispatch feed, close an incident, or mark a case resolved. Those remain named-human transitions backed by evidence.

## Feed actuator architecture

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

The agent constitution is machine-readable at [`config/missions/animal_feed_security.json`](config/missions/animal_feed_security.json).

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md), and [`docs/PILOT.md`](docs/PILOT.md).

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

Verification covers both layers: feed safety/authority/audit invariants **and** landscape non-hallucination/diagnosis behavior.

## Persistent feed agent

Run one cycle with `AFRN_AGENT_ONCE=1 python scripts/run_agent_loop.py`, or leave it running with `AFRN_AGENT_INTERVAL_SECONDS` (minimum 60 seconds). The mission manifest prevents the scheduler from crossing human-only authority boundaries.

## API surface

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

Do not call this a successful charity because the container runs. The first credible external claim remains smaller and harder:

> **A real welfare problem was correctly identified, its bottleneck was independently supportable, the selected intervention actually occurred, and outcome evidence shows the welfare gap improved without a serious safety incident.**

For the feed actuator specifically, at least one verified stockout-prevention case remains the minimum credible proof.

## Taiwan pilot note

The included Taiwan feed rule pack is deliberately labeled **NON-LEGAL DEMONSTRATION**. A real deployment requires locally reviewed veterinary, animal-feed, food-handling, insurance and data rules before physical material is accepted. Public web sources may map capabilities or leads; they are not sufficient by themselves to accuse an organization or assert a live welfare crisis.
