# Security policy

Do not submit real beneficiary, donor, shelter-access, veterinary, credential, procurement, audit, or location-sensitive data in public issues or committed fixtures.

## Pilot deployment

For a bounded pilot:

- use pseudonymous operational IDs where practical;
- expose the service only through HTTPS;
- keep bearer tokens and actor secrets outside source control;
- prefer `AFRN_ACTOR_REGISTRY` with per-actor token environment variables over one shared operator token;
- keep the local actor registry out of git (`config/access/actors.local.json` is ignored);
- give analysts, operators and reviewers only the permissions they need;
- treat source attachments/photos/invoices/beneficiary material as private partner data unless explicitly cleared;
- use the public-good evidence manifest for provenance metadata rather than embedding sensitive source contents in the case envelope;
- use `strict_evidence=true` when a governance decision must cite only registered evidence sources;
- back up the SQLite volume and test restore;
- verify `/health` ledger integrity after restore;
- preserve audit exports separately from the mutable application host.

Unified public-good assessment events record a SHA-256 case hash and decision/provenance summary; they intentionally do **not** copy the raw case payload into the audit ledger.

The API provides no unauthenticated mutation endpoints outside explicit demo mode. Consequential review/resolve paths require review permission when actor-registry mode is enabled.

## Current security boundary

The actor registry is pilot IAM, not enterprise identity infrastructure. It does not replace institutional SSO, MFA, managed device policy, centralized credential revocation, HSM/KMS-backed secrets, or organization-wide access governance.

SQLite/WAL is intentionally single-instance pilot persistence. Do not represent it as a national-scale highly available datastore.

Before production public-sector deployment, require a domain-specific privacy/security review covering at least:

- legal basis and data minimization;
- retention/deletion policy;
- encryption at rest and managed secrets;
- database high availability and tested disaster recovery;
- institutional identity provider + MFA;
- separation of duties and approval policy;
- rate limiting and abuse controls;
- structured observability/security logging;
- evidence-store authorization and data residency;
- incident response and credential rotation.

See `docs/GOVERNANCE_PILOT.md` for the operating boundary.
