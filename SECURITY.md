# Security policy

Do not submit real beneficiary, donor, shelter access, veterinary, credential or location-sensitive data in public issues.

For a pilot deployment:

- use pseudonymous operational IDs where practical;
- keep `AFRN_OPERATOR_TOKEN` outside source control;
- expose the service only through HTTPS;
- back up the SQLite volume and test restore;
- verify `/health` ledger integrity after restore;
- treat source attachments/photos as private partner data unless explicitly cleared for release.

The v0 API intentionally provides no unauthenticated mutation endpoints outside explicit demo mode.
