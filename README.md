# Animal Feed Relief Network

A validation-first coordination system for safe, traceable animal-feed relief.

The application demonstrates how a verified need, a traceable supply batch, deterministic safety rules, manual approval, operational tasks and evidence can produce an auditable feeding-support claim.

> **Important:** This repository is a synthetic validation environment. It is not veterinary, legal or food-safety authorization, and it intentionally blocks real-world food approval.

## What works

- recipient inventory and depletion context;
- synthetic commercial-feed intake;
- deterministic hard gates and human-readable rule trace;
- manual match approval;
- ordered pickup, delivery and feeding-evidence tasks;
- evidence-gated animal-day calculation;
- incident suspension across a batch and derived matches;
- append-only audit events;
- automated tests and CI.

## Run locally

Requires Node.js 20 or newer.

```bash
npm install
npm test
npm start
```

Open `http://localhost:3000`.

No runtime dependencies are required. `npm install` only creates the lockfile and validates the package metadata.

## Docker

```bash
docker build -t animal-feed-relief-network .
docker run --rm -p 3000:3000 animal-feed-relief-network
```

## Demo path

1. Submit the default sealed commercial-feed batch.
2. Inspect the rule trace.
3. Approve the synthetic match.
4. Complete the generated tasks in order.
5. Calculate impact.
6. Reset and try a recalled batch or anonymous household leftovers.
7. Run an incident suspension drill.

## Product boundaries

Read:

- [`docs/PRODUCT_SCOPE.md`](docs/PRODUCT_SCOPE.md)
- [`docs/SAFETY_BOUNDARIES.md`](docs/SAFETY_BOUNDARIES.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Status

V0 validation product. The next gate is partner review, not additional autonomous features.
