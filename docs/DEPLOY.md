# Deploy

## Local container

```bash
cp .env.example .env
# set a long AFRN_OPERATOR_TOKEN
docker compose up --build
```

Open `http://localhost:8080` and `http://localhost:8080/docs`.

## Small pilot deployment

AFRN v0 is a **single-instance** service using SQLite/WAL. Any host that runs a persistent Docker container plus a persistent volume is sufficient.

Required runtime settings:

- `AFRN_OPERATOR_TOKEN`: long random secret; mandatory outside demo mode.
- `AFRN_DB_PATH=/data/relief.db` on a persistent volume.
- `AFRN_RULEPACK=/code/config/rulepacks/tw_dog_cat_pilot.json` or a locally reviewed replacement.
- `AFRN_MISSION=/code/config/missions/animal_feed_security.json`.
- Optional scheduler: run `python scripts/run_agent_loop.py` as one controlled background process, with `AFRN_AGENT_INTERVAL_SECONDS>=60`.
- TLS/HTTPS must be terminated by the hosting platform or reverse proxy.

Before a live partner pilot:

1. replace the demonstration rule pack with a locally reviewed version;
2. configure backup/restore for the persistent volume;
3. run `make verify` and `GET /health`;
4. seed no real PII into a public environment;
5. keep one application replica until the persistence layer is migrated beyond SQLite;
6. document named human approvers and incident contacts.

FastAPI's current official deployment guidance recommends building a container from the official Python base rather than using the deprecated old FastAPI base image; this repository follows that shape.
