# Structural Initiative Planner

The landscape engine answers **what is wrong and what immediate bottleneck exists**. The structural initiative planner answers a different question:

> When repeated welfare failures form a durable pattern, is it cheaper and more effective to create or extend public-good infrastructure than to keep resolving cases one-by-one?

## Constitutional rule

A single crisis never justifies standing infrastructure, regardless of severity. v0 requires repeated credible need across multiple subjects and dates, plus evidence that existing service coverage or access is inadequate.

The current conservative recurrence gate requires at least:

- 4 need events;
- 2 distinct subjects;
- 3 distinct dates;
- 14 days of observed span;
- sufficient confidence/severity-weighted need.

These are research defaults, not legal or universal welfare thresholds.

## Structural options

The planner compares:

1. **case-level only** — keep using existing actuators;
2. **partner extension** — add the function to an existing verified welfare node;
3. **weekly pop-up hub** — reversible scheduled distribution point;
4. **mobile distribution route** — recurring route for dispersed recipients;
5. **permanent microhub** — durable fixed infrastructure.

The ranking considers estimated coverage, recurring verified volume, setup/weekly burden and implementation complexity. A permanent site is intentionally penalized until demand duration, volume and host availability are demonstrated.

## Preferred launch doctrine

`reuse existing service → reversible pilot → permanent infrastructure only after evidence`

A recommendation such as **"establish a weekly food-bank point here"** should therefore mean:

- repeated unmet need has been observed;
- the need is geographically/service-access clustered;
- current services do not already cover the same function adequately;
- a candidate host/location is actually available;
- a reversible pilot is cheaper than immediately creating a permanent operation.

## Implementation package

Every initiative plan includes:

- evidence summary and recurrence pattern;
- recommended structural form and candidate site;
- alternatives;
- setup and weekly operating-cost assumptions;
- implementation steps;
- success metrics;
- stop conditions;
- evidence gaps;
- graduation path from pilot to permanent infrastructure.

The planner does **not** create a live charity from synthetic data. Synthetic landscapes are regression tests only.

## Taoyuan experiment

`examples/taoyuan_public_structural_baseline.json` contains current public capability information but no asserted unmet-need events. Expected output: **no new food bank**.

`examples/taoyuan_synthetic_structural_cluster.json` overlays six clearly synthetic recurring nutrition/access events around a compact Yangmei-area cluster and a hypothetical verified host offer. Expected output: **weekly pop-up hub**, not a permanent microhub. The permanent option remains blocked until longer-duration and higher-volume real evidence exists.

Run:

```bash
python scripts/plan_initiative.py examples/taoyuan_public_structural_baseline.json
python scripts/plan_initiative.py examples/taoyuan_synthetic_structural_cluster.json
```
