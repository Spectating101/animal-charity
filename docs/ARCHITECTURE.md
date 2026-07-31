# Architecture

The validation build intentionally uses a dependency-free Node.js application.

```text
Browser dashboard
      |
      v
Node HTTP API
      |
      +--> deterministic rule engine
      +--> workflow and task state machine
      +--> evidence-gated impact calculator
      +--> append-only audit events
      |
      v
JSON runtime store (synthetic only)
```

## Why this architecture

The first question is whether the workflow and controls make sense to partners, not whether the system can scale nationally. A compact build is easier to inspect, deploy and discard. PostgreSQL, object storage, authentication, queues and messaging adapters can be added only after external validation.

## API routes

- `GET /api/dashboard`
- `GET /api/state`
- `POST /api/reset`
- `POST /api/matches`
- `POST /api/matches/:id/approve`
- `POST /api/tasks/:id/complete`
- `POST /api/matches/:id/impact`
- `POST /api/batches/:id/suspend`
