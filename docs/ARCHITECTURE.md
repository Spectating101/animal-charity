# Architecture

## Mission

AFRN exists to reduce **preventable unresolved feed gaps** for animals already under human care. The v0 system is deliberately narrower than a charity marketplace and narrower than a diet-planning AI.

## Constitutional agent loop

```text
verified observations
       ↓
forecast feed coverage
       ↓
open/update NeedCase
       ↓
deterministic hard gates ──fail──> escalation / human review
       ↓ pass
rank eligible supply
       ↓
MatchProposal (pending)
       ↓
NAMED HUMAN APPROVAL
       ↓
physical dispatch / delivery
       ↓
resolution evidence
       ↓
case closure + append-only audit
```

The unattended agent may **observe, forecast, open cases, propose and escalate**. These permissions are loaded from `config/missions/animal_feed_security.json`; the loop fails closed if asked to perform an undeclared autonomous action. It cannot approve recipient eligibility, diet safety, dispatch, incident closure or resolution.

## Refinery / Nocturnal relationship

AFRN is a thin domain application.

- **Refinery contract:** messy source material should become source-backed atomic observations before it changes operational state. v0 accepts structured observations and preserves `source_ref`; future adapters may ingest sheets/forms/messages, but extraction never becomes authority.
- **Nocturnal contract:** every consequential state change is emitted as an append-only event. The local SQLite hash chain is a portable pilot ledger; `app/nocturnal_adapter.py` exports compatible operational claims for a separately governed Nocturnal deployment.
- **Domain engine:** computes coverage, applies versioned deterministic gates, ranks eligible proposals and calculates outcome metrics.

This separation prevents an LLM prompt from becoming the hidden safety policy.

## Pilot persistence

SQLite + WAL is intentional for one-operator / one-pilot deployment. Do not add distributed infrastructure until a measured workload needs it. If multiple API replicas or concurrent writers are required, move the record/catalog store to PostgreSQL while keeping the event/audit contract stable.
