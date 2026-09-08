# Public-Good × Problem Commons Interoperability Freeze V0.1

Status: **experimental interoperability freeze**

The Public-Good Control Plane remains an independent specialist system. Problem Commons may consume reviewed projections from it, and Public-Good may consume bounded project/resource needs from Commons, but neither system inherits the other's authority or source-of-truth responsibilities.

## Public-Good remains authoritative for

- public-good failure/bottleneck diagnosis;
- domain constitutions and domain-specific safety/professional rules;
- capability/access/capacity/dependency distinctions;
- integrity and rights constraints;
- external funding/resource-program qualification;
- current-opportunity freshness, deadline and eligibility checks;
- smallest-feasible-intervention reasoning;
- consequential handoff reasoning;
- outcome interpretation under public-good claim boundaries.

## Problem Commons remains authoritative for

- living Problem identity/lifecycle;
- subproblem/work decomposition;
- solver/project opportunity packaging;
- contribution stages and work-mode classification;
- attempts, submissions, reviews and contributor credit;
- project effort/compensation/funding-need state;
- cross-problem work/reuse relationships.

## Export contracts

### Public-Good CoordinationMatch → Commons

Export only:

- resource ID;
- status: `qualified_candidate`, `requires_verification`, or `blocked`;
- matched/unresolved/blocking dimensions;
- evidence refs;
- reasons.

Never export a candidate as:

- eligible/approved applicant;
- submitted application;
- awarded grant;
- funding commitment;
- procurement decision;
- intervention authorization.

### Public-Good NormalizedFinding → Commons

Export only as **candidate work** for curator review. Preserve the Public-Good control stage and problem class. Do not map it automatically to a Commons Observe/Measure/Explain/Design/Build/Test/Deploy/Monitor/Generalize stage.

### Public-Good intervention reasoning → Commons Governance Envelope

The envelope is a reviewed projection for work orchestration only. Public-Good/domain professionals and the competent external actor retain consequential authority.

## Import contracts

### Commons FundingNeed → Public-Good CoordinationNeed

Treat as evidence that a project claims a resource requirement, not as proof that:

- the amount is correct;
- a funding program fits;
- the applicant is eligible;
- a call is open;
- an application can be submitted;
- funding is committed.

Public-Good's normal verification, freshness, eligibility, geography, actor-type, amount and source-evidence gates still apply.

## Frozen semantic distinction: two kinds of stage

Public-Good stages such as `safety`, `access`, `capacity`, `integrity`, `route`, `outcome`, and `evidence` describe the **control/problem condition**.

Problem Commons stages such as `Measure`, `Explain`, `Design`, `Build`, and `Test` describe the **work being performed**.

They are deliberately orthogonal and must not be unified without repeated real-case evidence.

## Frozen non-transfer rules

- Shared architecture does not transfer domain constitutions.
- Resource match does not transfer funding authority.
- Solver work does not transfer professional authority.
- Test success does not transfer deployment authority.
- Public-Good recommendation does not create a Commons project until human curation accepts it.
- Commons project status does not change Public-Good diagnosis or intervention validity.

## Reopen criteria

Revisit this freeze only after repeated real cases show a stable need for a stronger shared primitive, duplicated implementation produces divergent semantics, or an external partner requires a durable interoperable contract that cannot be represented by the current projections.
