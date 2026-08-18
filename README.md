# Animal Feed Relief Network

**Validation-first coordination for safe, traceable animal-feed relief.**

AFRN is a bounded public-welfare agent that turns verified shelter inventory + verified feed supply into accountable intervention proposals. Its job is not to formulate diets or decide who "deserves" help. Its job is to make preventable feed gaps hard to ignore and easy to resolve safely.

> **Status:** v0 implementation candidate on `feat/public-welfare-agent-v0`. Dogs/cats + sealed commercial complete feed only. Not yet a live charity operation and not veterinary/legal authorization.

## What the autonomous agent can do

`observe → forecast → open NeedCase → apply hard gates → rank eligible supply → propose → escalate`

It **cannot** approve recipient eligibility, approve a diet, dispatch feed, close an incident, or mark a case resolved. Those are named-human transitions backed by evidence.

## Why this exists

Animal-care organizations can run short of appropriate feed while commercial surplus, transport, storage, volunteer effort and targeted funding remain disconnected. AFRN tests whether a cheap coordination and accountability layer can convert those fragmented resources into **verified animal-days of appropriate feeding**.

The software is intentionally cheap. The hard problem is operational trust.

## v0 architecture

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

The current tests prove that the unattended agent can open cases and propose eligible feed **without auto-approving it**, prepared/expired feed fails the autonomous path, a supply lot cannot be double-booked, resolution requires human approval plus evidence, confirmed delivery updates inventory/impact accounting, and the append-only hash ledger verifies.

## Persistent agent

Run one cycle with `AFRN_AGENT_ONCE=1 python scripts/run_agent_loop.py`, or leave it running with `AFRN_AGENT_INTERVAL_SECONDS` (minimum 60 seconds). The mission manifest still prevents the scheduler from crossing human-only authority boundaries.

## API surface

| Surface | Purpose | Authority |
|---|---|---|
| `POST /v1/recipients` | record verified partner | operator |
| `POST /v1/groups` | record animal demand | operator |
| `POST /v1/inventory` | record current feed | operator |
| `POST /v1/supplies` | record candidate supply | operator |
| `POST /v1/agent/tick` | run bounded welfare cycle | agent/operator |
| `GET /v1/cases` | unresolved/resolved need | operator read |
| `GET /v1/proposals` | pending matches | operator read |
| `POST /v1/proposals/{id}/review` | approve/reject | **human only** |
| `POST /v1/cases/{id}/resolve` | close with delivery evidence | **human only** |
| `GET /v1/audit/events` | append-only operational history | operator read |
| `GET /v1/audit/nocturnal-export` | map events to Nocturnal-style claims | operator read |

## Launch gate

Do not call this a successful charity because the container runs. The first credible external claim is much smaller and harder:

> **At least one verified feed stockout was prevented, with a traceable batch, named human approval, delivery evidence, zero serious safety incidents and a counterfactual note explaining why the outcome was additional.**

## Taiwan pilot note

The included Taiwan rule pack is deliberately labeled **NON-LEGAL DEMONSTRATION**. Current Ministry of Agriculture rules designate dog/cat food within the pet-food regime and prohibit expired/unsafe/non-compliant products. A real deployment requires locally reviewed veterinary, animal-feed, food-handling, insurance and data rules before any physical material is accepted.
