# Governance pilot operating model

## Purpose

The current system is deployable as a **decision-support / shadow-governance control plane**, not as an autonomous government authority.

A pilot should test whether the system improves diagnosis, evidence requests, resource routing and intervention review while ordinary authorized institutions retain consequential authority.

## Recommended deployment scope

Start with one bounded programme, geography or operator team.

Suitable pilot uses:

- pre-decision review before new facilities, routes, suppliers or programme extensions;
- shadow assessment of incoming welfare/public-good cases;
- retrospective replay of historical cases;
- repeated-bottleneck detection;
- structured evidence/provenance review;
- outcome and audit comparison.

Do not initially connect automatic spending, sanctions, eligibility denial, medical decisions, procurement awards or other irreversible authority.

## Unified governance API

`POST /v1/public-good/assess`

The request declares a registered domain (`animal_welfare` or `mbg_public_nutrition`) and supplies that domain's payload. The server selects the correct constitution and normalizes only the shared control stages.

The response preserves the full domain-specific result and returns comparative stages such as:

`safety · stabilize · prevent · route · integrity · capacity · access · outcome · evidence`

Unknown domains fail closed.

### Strict evidence mode

`POST /v1/public-good/assess?strict_evidence=true`

A `PublicGoodCase` may include an `evidence_manifest` describing source references, verification status, sensitivity and optional content hashes. In strict mode every source reference cited by the resulting recommendation must exist in the manifest or the request is rejected.

The manifest is provenance metadata; it does not make a weak source true merely because it is registered.

## Actor identity and permissions

The historical single `AFRN_OPERATOR_TOKEN` remains available for bounded backwards-compatible pilots.

Preferred governance-pilot mode sets `AFRN_ACTOR_REGISTRY` to a local registry based on:

`config/access/actors.example.json`

The client provides:

- `X-Actor: <registered actor id>`
- `Authorization: Bearer <that actor's token>`

Roles and permissions are derived on the server from the registry. The client cannot assert its own role.

Example permissions:

- `summary.read`
- `public_good.assess`
- `welfare.assess`
- `replay.run`
- `operations.write`
- `review.write`
- `audit.read`

A recommended separation is:

- analyst: assess/replay only;
- operator: case/operational writes but no review authority;
- reviewer: review/audit authority but no automatic execution;
- admin: configuration and emergency maintenance.

This is pilot IAM, not a replacement for government SSO/IdP, MFA, device trust, credential lifecycle or enterprise policy enforcement.

## Audit behavior

A unified public-good assessment appends a `public_good.assessed` event to the hash-chained ledger. A service replay appends `public_good.replayed` with the replay cutoff and recommendation summary while keeping the hidden historical reference out of the response and audit payload.

The assessment audit event records:

- case id;
- domain;
- SHA-256 hash of the full submitted case envelope;
- normalized stages/problem classes;
- constitution reference;
- structural-candidate count;
- evidence-manifest status/counts;
- strict-evidence mode;
- attributable actor.

The raw case payload is deliberately not copied into the audit event. Sensitive source material should live in an authorized evidence store and be referenced through `source_ref`/content hashes.

## Historical replay

Service/API run:

`POST /v1/public-good/replay`

The API requires `replay.run` permission and deliberately performs **non-scoring replay only**. It returns the assessment and audit reference but never reveals the hidden historical reference.

CLI run:

`python scripts/replay_public_good_case.py <packet.json>`

A `ReplayPacket` contains:

- historical decision cutoff;
- the case as known at that time;
- an optional hidden reference with historical action/outcome.

Strict replay requires timestamps on evidence-bearing records and rejects evidence recorded after the decision cutoff.

The normal replay output does not expose the reference.

Only an explicit offline scoring run reveals it:

`python scripts/replay_public_good_case.py <packet.json> --score`

Current score is deliberately modest: primary normalized-stage agreement plus structural-candidate comparison. It does not claim that matching the historical stage proves causal superiority.

## Shadow-pilot protocol

For each live case:

1. Freeze the evidence available at decision time.
2. Run the control plane without allowing it to execute consequential action.
3. Record the human/operator decision independently.
4. Preserve subsequent outcome evidence.
5. Compare diagnosis, evidence requests, intervention class, cost/burden and outcome after the fact.
6. Review failures symmetrically; do not tune only to successful examples.

Useful evaluation measures include:

- failure-class agreement;
- correct evidence-gap requests;
- false scarcity / false integrity escalation rate;
- unnecessary-infrastructure avoidance;
- missed safety/integrity hard gates;
- intervention burden/cost relative to the actual path;
- stable outcome rate;
- reviewer usefulness rating.

## Operational limits

Current deployment is intentionally small-scale:

- SQLite/WAL, single service instance;
- bearer-token pilot authentication;
- local role registry rather than institutional identity provider;
- no queue/event bus for high-volume ingestion;
- no national-scale database/replication/failover;
- no automated statutory eligibility, sanctions or procurement authority;
- no claim of validated causal impact yet.

For a real production government environment, add institutional SSO/MFA, managed secrets, database HA/replication, migrations, backup/restore drills, observability, rate limits, retention policy, encrypted evidence storage, data residency/privacy review, separation of duties, and organization-specific due-process rules.

## Launch claim boundary

A successful deployment claim requires more than uptime or recommendation generation.

At minimum:

> The system was operated prospectively or replayed without hindsight leakage; it identified a supportable bottleneck or evidence gap; its recommendation stayed inside the selected domain authority; and subsequent independent review/outcome evidence showed the recommendation was useful or correctly cautious.

Until then, describe the system as a governance research/pilot control plane.
