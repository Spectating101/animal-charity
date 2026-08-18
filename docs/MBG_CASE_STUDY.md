# MBG as a Cross-Domain Public-Good Control-Plane Case Study

## Purpose

Indonesia's **Makan Bergizi Gratis (MBG)** programme is used here as a second, deliberately harder systems-method testbed.

The repository does **not** attempt to redesign MBG, determine beneficiary eligibility, audit state finances, investigate crimes, award procurement, or replace BGN/KPK/PPATK/BPKP/BPOM/local authorities.

The research question is narrower:

> Can the generic `evidence → bad-state transition → access/resource/integrity diagnosis → bounded intervention → authority → outcome` architecture remain useful in a large human public-nutrition programme without transferring animal-specific rules?

## Why MBG is useful

MBG exposes multiple layers that can fail independently:

```text
policy / target
    ↓
budget allocation
    ↓
disbursement
    ↓
procurement
    ↓
physical food inputs
    ↓
SPPG production
    ↓
distribution
    ↓
beneficiary receipt
    ↓
safe consumption
    ↓
nutrition / education / welfare outcomes
```

A programme can therefore have sufficient national budget or kitchen capacity while still failing locally through:

- targeting/data errors;
- delayed or failed disbursement;
- procurement problems;
- physical-input shortfalls;
- food-safety failures;
- route/schedule/access barriers;
- local capacity shortfall;
- output that never becomes a verified nutrition outcome;
- unexplained resource-flow variance that must be reconciled before scarcity is diagnosed.

## Official public anchors

### Banten public dashboard

The DJPb Banten MBG dashboard update dated **30 January 2026** reported:

- 8 kabupaten/kota with SPPG;
- 741 SPPGs;
- 1,291 suppliers;
- 2,134,335 reported beneficiaries;
- target 3,502,386 beneficiaries;
- a strategic issue involving consistent quality standardization for local egg-cooperative participation.

Source:
`https://djpb.kemenkeu.go.id/kanwil/banten/id/data-publikasi/berita-terbaru/9-uncategorised/3066-dashboard-makan-bergizi-gratis.html`

These are **capability/output/context facts**. They do not establish that any particular SPPG is failing, that the gap to the aggregate target is caused by kitchen capacity, or that any supplier/operator is culpable.

### Existing MBG monitoring/integrity infrastructure

BGN launched **Reviu MBG** in May 2026 so recipient-side PICs such as teachers and posyandu heads can report arrival-time, aroma, taste and menu-variation observations at receipt.

Source:
`https://www.bgn.go.id/news/siaran-pers/bgn-luncurkan-aplikasi-reviu-mbg-untuk-perkuat-pengawasan-kualitas-makanan-secara-real-time`

PPATK states that **DETAK MBG** performs early detection around MBG fund flows using programme-specific suspicious-transaction indicators.

Source:
`https://www.ppatk.go.id/siaran_pers/read/1594/catatan-capaian-strategis-ppatk-tahun-2025-menjaga-kedaulatan-dan-integritas-ekonomi-bangsa-jakarta-28-januari-2026-b001hm0531i2026-.html`

BPKP's 2026 field evaluations explicitly cover recipient-data accuracy, service quality/stability, financial accountability/efficiency, procurement/physical operations and programme impact.

Example source:
`https://www.bpkp.go.id/id/unitKerja/15/berita/je3V/dari-dapur-hingga-penerima-manfaat-bpkp-sumbar-evaluasi-pelaksanaan-program-mbg`

KPK has publicly identified MBG fraud/governance risk areas including SPPG/partner selection, conflicts/preferences, procurement and beneficiary-data reliability. These are **risk categories and oversight findings**, not permission for this software to call any specific actor corrupt.

Source:
`https://www.kpk.go.id/id/ruang-informasi/berita/KPK-dorong-pencegahan-korupsi-program-mbg-lewat-sinergi-pengawasan-dana-publik`

## Integrity Plane

`app/integrity_plane.py` is domain-neutral. It reconciles explicit pairs of observations across stages such as:

```text
allocation
→ disbursement
→ procurement
→ physical_input
→ service_output
→ beneficiary_receipt
→ outcome
```

Each reconciliation has an explicitly supplied tolerance. The engine can return:

- `normal`;
- `evidence_gap`;
- `variance_needs_explanation`;
- `integrity_risk`;
- `audit_referral_recommended`.

It **cannot** return `corruption`, `fraud`, `criminal`, `guilty`, or a sanction.

A material mismatch should first trigger checks for ordinary explanations such as timing differences, authorized substitutions, partial delivery, absences, measurement errors or reporting cut-offs.

## MBG Adapter

`app/mbg_case_study.py` maps MBG evidence into a bounded case assessment.

Current priority:

```text
food-safety failure
      ↓
material integrity uncertainty
      ↓
genuine capacity gap
      ↓
access/delivery or targeting/data gap
      ↓
outcome-evidence gap
```

The order is intentional.

If financial/physical/service records do not reconcile, the system should not interpret the resulting shortage as proof that more kitchens or budget are needed.

Likewise, verified food-safety failure is a hard gate: maximizing meal coverage cannot compensate for unsafe food.

## Fixtures

### Public non-hallucination baseline

```bash
python scripts/assess_mbg_case.py examples/mbg_banten_public_context.json
```

Expected:

- zero local case findings;
- explicit data gap;
- no capacity expansion recommendation;
- no integrity/corruption conclusion.

### Synthetic integrity-before-expansion case

```bash
python scripts/assess_mbg_case.py examples/mbg_synthetic_integrity_case.json
```

Synthetic facts include:

- target/capacity 3,000;
- verified recipients 2,600;
- reliable transport and reconciled beneficiary data;
- invoice for 300 kg chicken versus verified physical receipt of 225 kg;
- claimed 3,000 meals versus verified recipient receipt of 2,600.

Expected:

`integrity_uncertainty → authorized reconciliation/audit review before capacity expansion`

The fixture is wholly fictional. It does not represent a real SPPG, supplier, foundation, official, school or beneficiary group.

### Synthetic genuine-capacity case

```bash
python scripts/assess_mbg_case.py examples/mbg_synthetic_capacity_case.json
```

Synthetic facts include:

- verified target 3,500;
- verified capacity 3,000;
- ~3,000 verified actual recipients;
- procurement/physical/service/receipt checks within tolerance.

Expected:

`capacity_gap`

and the recommendation still begins with verified neighboring capacity / catchment rebalancing before a permanent new SPPG.

## Human governance boundary

Machine-readable case-study constitution:

`config/missions/mbg_public_nutrition_case_study.json`

The agent may organize/reconcile evidence and propose review questions. The following remain human/institutional authority:

- beneficiary entitlement;
- payment or disbursement holds;
- procurement awards/cancellation;
- supplier/partner exclusion;
- formal audit/investigation;
- fraud/corruption/criminal findings;
- sanctions and public accusations;
- binding budget/policy changes.

## Cross-domain research value

The MBG case adds a missing abstraction to the generic research programme:

> **allocation ≠ money flow ≠ physical input ≠ service output ≠ beneficiary receipt ≠ outcome**

Animal welfare primarily tests fragmented-service diagnosis and institution origination.

MBG tests whether the same architecture can survive a large existing state programme where service capacity, targeting, food safety, public finance, procurement, integrity and measurable human outcomes interact.

A successful synthetic/replay result is not evidence that the system improves MBG. Progress remains:

`R0 synthetic invariants → R1 retrospective public/authorized replay → R2 shadow analysis → only then any authorized prospective evaluation`.
