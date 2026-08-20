# Public-Good Control Plane: interoperability architecture

## Positioning

This repository should not become a monolithic replacement for emergency-management systems, social registries, procurement platforms, service directories, hazard sensors or journalism.

Its narrow role is the **decision/control layer between evidence and authorized intervention**:

`evidence → establish condition → identify broken edge → map usable capability → apply integrity/safety/rights gates → propose smallest feasible intervention → hand off to competent authority → observe outcome → reassess recurrence`

Everything around that loop should be composed from mature external systems where possible.

## Five operational planes + public memory

```text
1. EVIDENCE PLANE
   hazard sensors · official reports · local observations · outcomes
   FIRMS · GDACS · Copernicus · government/partner sources
                    ↓
2. CAPABILITY PLANE
   typed resources · organizations · services · facilities · availability
   NIMS-inspired resource typing · OCHA 3W · Open Referral · operations systems
                    ↓
3. INTEGRITY PLANE
   resource promise vs financial/physical/service reality
   OCDS-compatible contracting/implementation references
                    ↓
4. PUBLIC-GOOD CONTROL PLANE   ← this repository's core ownership
   condition → broken edge → smallest intervention → recurrence
                    ↓
5. AUTHORITY + EXECUTION PLANE
   EOC / incident command / statutory authorities / operators
   WHO PHEOC/NIMS doctrine · Sahana/OpenSPP/GovStack-style execution building blocks
                    ↓
                 outcome
                    ↓
6. PUBLIC MEMORY / ACCOUNTABILITY
   Nocturnal: what happened, what was promised, what happened next
```

Nocturnal may supply historical evidence to the control plane and receive outcome/audit-safe exports after intervention. It does not become the intervention optimizer.

## What we should borrow, not reinvent

### FEMA NIMS / incident resource management

Use NIMS as a doctrine and vocabulary reference for **typed resources, capability, inventory, mutual aid, operational priorities and resource status**. Do not interpret a NIMS classification as proof that a particular resource is currently available or as authority for this software to deploy it.

Reference: https://www.fema.gov/emergency-managers/nims

### WHO emergency operations centre doctrine

Use WHO PHEOC/EOC guidance for the principle that emergency operations centres coordinate information and resources under designated authority. The control plane may support an EOC; it does not replace the EOC or create authority by inference.

Reference: https://www.who.int/publications/i/item/framework-for-a-public-health-emergency-operations-centre

### OCHA 3W / Open Referral

Use service/capability registries to answer **who does what where** and what services/facilities exist. Preserve the repository's existing rule:

`service exists ≠ service accessible ≠ spare capacity ≠ successful outcome`

References:
- https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/214499412
- https://docs.openreferral.org/

### Open Contracting Data Standard (OCDS)

Use OCDS identifiers and contracting stages to link planning/tender/award/contract/implementation/payment evidence into the Integrity Plane. A contracting discrepancy remains an evidence/reconciliation signal; it is not a corruption finding.

Reference: https://standard.open-contracting.org/latest/en/

### NASA FIRMS / GDACS / Copernicus EMS

Use mature hazard systems as evidence inputs. Do not build a replacement satellite fire detector or multi-hazard alert network.

Hazard evidence establishes observations and uncertainty. It does **not** establish ignition cause, negligence, ownership culpability or legal liability.

References:
- https://firms.modaps.eosdis.nasa.gov/
- https://www.gdacs.org/
- https://mapping.emergency.copernicus.eu/

### Sahana / OpenSPP / GovStack-style building blocks

Treat mature operational and digital-public-infrastructure components as execution targets: registries, workflows, facilities, inventories, payments, messaging and programme administration should remain modular. The control plane should expose bounded recommendations and machine-readable handoffs rather than cloning each platform.

References:
- https://sahanafoundation.org/
- https://openspp.org/
- https://specs.govstack.global/

## Interoperability contract

`app/interoperability.py` intentionally defines a **small adapter contract**, not copies of every external schema.

An `ExternalRecord` declares:

- source system and source reference;
- role (`evidence_source`, `capability_registry`, `integrity_standard`, `authority_framework`, `operations_platform`, `memory_archive`);
- record kind;
- observed/valid time;
- verification status;
- sensitivity;
- optional content hash;
- source-specific attributes.

`build_control_plane_packet()` then creates a normalized packet containing:

- hazard signals;
- verified deployable resources;
- reportedly available resources that still require verification;
- service presence/access/capacity signals;
- contracting/integrity process references;
- command/authority context;
- outcome references;
- stale-record warnings;
- evidence-manifest entries reusable by the governance API.

This intentionally prevents several category errors:

1. an **authority framework cannot masquerade as a live resource inventory**;
2. a **reported resource is not dispatchable until sufficiently verified**;
3. a **committed resource is not counted as available**;
4. stale evidence may remain useful historically but cannot establish current operational state;
5. an OCDS/contracting record never becomes a machine corruption verdict;
6. no command context means analysis may continue, but consequential action remains unauthorized.

## Disaster case-study packaging

The first two disaster fixtures are deliberately synthetic:

- `examples/interop_kalimantan_synthetic.json`
- `examples/interop_ntt_synthetic.json`

They are not claims about the real Kalimantan fires or NTT earthquake. They demonstrate how real external data *would be shaped* before a future disaster-domain adapter is allowed to make intervention recommendations.

Run:

```bash
python scripts/build_control_plane_packet.py examples/interop_kalimantan_synthetic.json
python scripts/build_control_plane_packet.py examples/interop_ntt_synthetic.json
```

Expected wildfire behavior:

- a fresh fire observation remains hazard evidence only;
- a verified available peat/fire team is dispatch-capable input;
- a merely reported aircraft remains a candidate requiring verification;
- a clinic appears as service capability, not proof that smoke-health needs are covered;
- command context identifies where authorized response decisions belong.

Expected earthquake behavior:

- the SAR team can be considered deployable if verified and available;
- an already committed water tanker is not double-counted as spare capacity;
- a constrained hospital remains capability with an access/capacity warning for later domain reasoning;
- a stale road-status observation is explicitly rejected as current operational state.

## The next domain boundary

A future `disaster_response` domain should consume `ControlPlaneInteropPacket` rather than create bespoke connectors for every source.

The domain should own hazard-to-welfare transitions such as:

`hazard → exposure → life-safety condition → access/critical-service failure → resource gap → stabilization → recovery → resilience`

It should **not** own:

- earthquake/fire prediction;
- legal causation or blame;
- incident-command authority;
- professional structural/medical determinations;
- automatic rescue deservingness;
- unrestricted location/identity disclosure;
- autonomous irreversible dispatch under uncertainty.

## Data responsibility

Interoperability is not permission to centralize every available datum.

For humanitarian/person-level deployment:

- minimize personal data;
- separate public, internal, sensitive and restricted sources;
- preserve purpose limitation;
- use pseudonymous references where possible;
- define an information-sharing policy before partner exchange;
- expose only the information required for the decision at hand.

Reference: https://centre.humdata.org/revised-ocha-data-responsibility-guidelines/

## Research claim

The project should not claim novelty for incident command, humanitarian logistics, digital government building blocks, hazard sensing, social registries or procurement standards.

The candidate contribution is narrower:

> **An evidence-bounded control layer that composes existing public-good capabilities, distinguishes condition/access/capacity/integrity failures before spending, routes only through domain-specific constitutional authority, and escalates repeated failures into reversible structural intervention candidates.**

That claim now has animal-welfare and MBG R0 implementations. Disaster interoperability is the next stress test; real superiority remains unproven until hindsight-safe replay and prospective shadow evaluation succeed.
