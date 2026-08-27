# Welfare Landscape Engine

## Purpose

The feed-relief runtime is one actuator. The landscape engine sits above it and asks a more important sequence:

`observe → verify → identify problem → diagnose bottleneck → choose smallest feasible intervention → route to authority/actuator → verify outcome`

Its job is **not** to search the web for emotionally compelling claims and label organizations as harmful. It separates evidence that a service exists from evidence that a welfare problem exists, keeps causal claims bounded by the supplied evidence, and requests missing evidence rather than filling gaps with model confidence.

## Evidence classes

- `condition`: evidence about an actual welfare state or operational state, e.g. current feed coverage, rescue delay, intake pressure, transport availability.
- `capability`: evidence that an intervention path exists, e.g. official rescue line, shelter/adoption service, donation channel, food bank.
- `context`: relevant background that is not itself a welfare-state claim.

**Capability evidence may never create a problem case by itself.**

## Current detectors

### Nutrition risk

Trigger: verified `feed_coverage_days < 3`.

Diagnosis order:

1. compatible supply exists + transport unavailable → `last_mile_logistics` → `logistics.dispatch_request`
2. compatible supply + transport both exist → `coordination` → `afrn.feed_matcher`
3. compatible supply exists but transport unknown → request logistics evidence
4. reported procurement budget gap → `funding_procurement` → precise funding/purchase request
5. intake surge ≥ 1.5× baseline → `capacity_surge` → capacity-relief plan
6. otherwise → `cause_unresolved` → collect evidence, do not guess

### Capacity pressure

Conservative trigger: shelter capacity ratio ≥ 90% or intake ≥ 1.5× baseline.

Output is a capacity-support hypothesis, not an accusation of neglect.

### Rescue delay

Conservative trigger: a verified rescue case unresolved ≥ 12 hours. At ≥24 hours it is marked critical and routed to authorized escalation.

These thresholds are v0 research defaults, not claims of legal or veterinary significance.

## Taoyuan test landscape — 2026-08-18

The public baseline records only publicly evidenced capabilities:

- Taoyuan City Animal Protection Office and emergency rescue channel;
- Taoyuan Animal Protection Education Park / public shelter and adoption service;
- Taoyuan animal-protection donation channel;
- 2026 rural dog/cat sterilization support programme;
- APATW 2026 Stray Animal Food Bank;
- Ministry of Agriculture daily animal-adoption open data.

The baseline deliberately contains **no live condition observations**. Expected result: zero active problem cases plus explicit data gaps. This is the correct result: those public sources establish an ecosystem, not a current starvation event.

`examples/taoyuan_synthetic_incident.json` overlays one explicitly synthetic incident on the same landscape:

- verified feed coverage: 1.8 days;
- compatible supply nearby: 80 kg;
- transport available: false.

Expected diagnosis: `last_mile_logistics`, with `logistics.dispatch_request` selected instead of `afrn.feed_matcher`.

## What this still needs for a real area scan

A useful live landscape requires condition evidence, ideally from partner-controlled or official operational feeds:

- current shelter/rescue inventory and feed burn rate;
- intake/capacity state;
- unresolved rescue queue and timestamps;
- available donor lots;
- transport/storage availability;
- invoices or procurement gaps;
- intervention acceptance/delivery/outcome events.

Public web data can discover capabilities and candidate leads. It should not be treated as sufficient evidence to accuse an organization, expose private recipients, or autonomously trigger consequential action.
