# Public-Good Control Plane

**Evidence-bounded governance decision support for diagnosing public-good delivery failures, mapping usable existing capability, and proposing the smallest feasible intervention under explicit safety, integrity, rights, and authority gates.**

> The repository name `animal-charity` is historical lineage. The current research object is the **Public-Good Control Plane**.

## Status

| Dimension | Current state |
|---|---|
| Development stage | **Internally validated research/pilot candidate** |
| Canonical code | `main` |
| Internal verification | `make verify` and Docker build pass in GitHub Actions |
| Evidence ladder | R0 architecture + synthetic invariants; R1 retrospective public-source replay in the disaster domain |
| External validation | **Not established** — no partner adoption, prospective shadow evaluation, or independent replication is claimed |
| Deployment / outcomes | **Not established** — the repository does not claim improved real-world public-good outcomes |
| License | **Not yet declared** |

The project is intentionally conservative about maturity. Working software and internal tests are evidence of implementation quality; they are **not** substitutes for field validation, institutional authority, or demonstrated outcomes.

## What it does

The common control loop is:

```text
current evidence
    ↓
identify the failing state / transition
    ↓
diagnose the actual bottleneck
    ↓
map existing capability and access
    ↓
apply safety / integrity / rights / authority gates
    ↓
propose the smallest feasible intervention
    ↓
human or institutional authority
    ↓
execution outside the control plane
    ↓
verified outcome + longitudinal learning
```

The architecture is designed to resist several recurring errors:

- missing inventory does not automatically become scarcity;
- a service existing does not mean it is accessible;
- reported capability does not become live deployable capacity;
- activity or spending does not automatically become outcome improvement;
- a matching grant/programme does not imply current eligibility or an open call;
- a recommendation does not become authorization;
- a historical replay agreement does not become causal proof of better outcomes.

## Current domains

### 1. Animal welfare

The original lineage of the repository. It tests preventive welfare transitions, owner retention, reunification, source control, foster/adoption capacity, service-access gaps, food/logistics as a bounded actuator, structural recurrence, and verified downstream welfare outcomes.

Key docs:

- [`docs/ANIMAL_WELFARE_CONTROL_PLANE.md`](docs/ANIMAL_WELFARE_CONTROL_PLANE.md)
- [`docs/PREVENTIVE_WELFARE_RESEARCH.md`](docs/PREVENTIVE_WELFARE_RESEARCH.md)
- [`docs/TAOYUAN_SANMIN_CONTROL_EXPERIMENT.md`](docs/TAOYUAN_SANMIN_CONTROL_EXPERIMENT.md)

### 2. MBG public nutrition

A separately constituted case study for distinguishing genuine capacity shortage from access/delivery failure and resource-flow integrity uncertainty before expansion is justified.

The integrity plane preserves a hard boundary between an unexplained material variance and any allegation of fraud, corruption, or criminality.

See [`docs/MBG_CASE_STUDY.md`](docs/MBG_CASE_STUDY.md).

### 3. Disaster response

The strongest dynamic stress-test family. It adds changing need/resource state, access failure, observed vs inferred capacity shortage, upstream dependencies, safety constraints, route-state reversal, movement-specific access envelopes, bounded UAS action intents, and hindsight-safe public-source replay.

The disaster campaign is designed to test both sides of the system: it must refuse false scarcity **and** recognize sufficiently evidenced real shortages or broken dependencies.

Key docs:

- [`docs/DISASTER_CONTROL_PLANE.md`](docs/DISASTER_CONTROL_PLANE.md)
- [`docs/DISASTER_REPLAY_PROTOCOL.md`](docs/DISASTER_REPLAY_PROTOCOL.md)
- [`docs/DISASTER_R1_CAMPAIGN.md`](docs/DISASTER_R1_CAMPAIGN.md)

## Shared architecture

The repository is best understood as three layers rather than a collection of unrelated features.

### Domain-independent control core

- evidence and provenance discipline;
- freshness / observed-time semantics;
- normalized problem stages;
- capability, access, scarcity, and dependency reasoning;
- integrity reconciliation;
- safety constraints;
- recurrence / structural-candidate logic;
- hindsight-safe replay;
- outcome and longitudinal evaluation;
- explicit human-authority boundaries.

### Domain constitutions and adapters

Current implemented adapters:

- animal welfare;
- MBG public nutrition;
- disaster response;
- public-good initiative/resource coordination.

Domain-specific rights, welfare rules, entitlements, professional judgments, and irreversible authority do **not** transfer merely because the shared architecture does.

### Interoperability and evidence shell

The system composes with external evidence/capability/authority systems rather than pretending to replace them. The reference model includes NIMS / WHO EOC doctrine, OCHA/Open Referral-style service presence, OCDS-style contracting evidence, hazard feeds, execution platforms, and longitudinal public memory.

See:

- [`docs/PROJECT_POSITIONING.md`](docs/PROJECT_POSITIONING.md)
- [`docs/INTEROPERABILITY_ARCHITECTURE.md`](docs/INTEROPERABILITY_ARCHITECTURE.md)
- [`config/integrations/reference_systems.json`](config/integrations/reference_systems.json)

## Nocturnal and Refinery boundaries

**Nocturnal** is treated as a separate coverage / public-memory plane: what happened, what source supports it, what changed later, and whether promises, investigations, corrections, or outcomes were subsequently documented.

The Public-Good Control Plane owns bounded diagnosis and intervention reasoning, not journalism.

**Refinery** may contribute reviewed institutional or opportunity observations through a bounded projection. It does not transfer recommendation, eligibility, funding, submission, or intervention authority into the control plane. Current coordination logic also treats deadline/status conflicts and stale `open` language conservatively.

## Governance pulse

The governance-pulse layer tracks adverse conditions and verified positive target-state movement in parallel without collapsing them into a single sentiment or performance score.

It separates:

- stress frontier;
- progress frontier;
- operational outputs;
- response activity;
- ambiguous condition evidence;
- lagged context.

Activity does not become progress, and progress does not offset unresolved harm.

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
- Health: `http://127.0.0.1:8000/health`

Or run with containers:

```bash
cp .env.example .env
# configure the documented local operator settings
docker compose up --build
```

## Representative research commands

Animal-welfare controls:

```bash
python scripts/assess_animal_welfare.py examples/zhongli_sanmin_policy_baseline.json
python scripts/assess_preventive_welfare.py examples/zhongli_sanmin_synthetic_preventive_system.json
```

Public-good / disaster controls and replay are wired into the repository verification gate; see the scripts and domain docs for the maintained case set.

## Verification

```bash
make verify
```

The canonicalization gate is also exercised in GitHub Actions together with a Docker build. The suite covers the implemented animal-welfare, MBG, public-good routing, interoperability, disaster, replay, safety/access, governance, coordination, and adapter contracts represented by the current repository state.

## Claim boundary

Supported at the current stage:

> The repository contains an implemented and internally tested Public-Good Control Plane with multiple separately constituted domains, evidence/provenance and authority boundaries, interoperability contracts, dynamic disaster reasoning, hindsight-safe public-source replay, governance-state organization, and bounded coordination/adaptation layers.

Not established:

- improved real government, humanitarian, nutrition, or animal-welfare outcomes;
- superiority to competent professionals or emergency managers;
- autonomous dispatch or coercive/public authority;
- real corruption detection;
- legal or professional authorization;
- live programme eligibility merely because an opportunity page exists;
- prospective shadow performance;
- independent replication or external adoption.

The next meaningful evidence step is **external**: prospective non-consequential shadow use with competent partners, followed only later by supervised reversible intervention where appropriate.

## Security and operating boundary

This remains a research/pilot codebase. Demo rule packs are not legal, veterinary, emergency-management, procurement, aviation, nutrition, or other professional authorization. Real deployment requires domain-specific review, named human authority, operational data controls, and an explicit pilot protocol.

See [`SECURITY.md`](SECURITY.md) and [`docs/GOVERNANCE_PILOT.md`](docs/GOVERNANCE_PILOT.md).
