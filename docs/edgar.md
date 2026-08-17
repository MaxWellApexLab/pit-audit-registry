---
title: "Is as-filed SEC EDGAR data safe for cross-sectional signals? 7 of 14 signals flagged"
description: >-
  Measured on observed SEC filing dates (856 firms, 2011-2025): 7 of 14
  standard fundamental signals flagged for incomplete-cross-section leakage,
  28/84 signal-cycles. ROA is clean at 0/6. Free data, fully reproducible.
---

# Is as-filed SEC EDGAR data safe for cross-sectional signals?

**Not uniformly.** On a US panel rebuilt from as-filed EDGAR filings, on
**observed** filing dates (856 firms, 8,118 firm-years, coverage 2011–2025),
the screen flags **7 of 14 standard fundamental signals — 28 of 84
signal-cycles** (frozen protocol, threshold 0.10):

![Per-signal susceptibility on the as-filed SEC EDGAR panel](https://raw.githubusercontent.com/MaxWellApexLab/pit-audit-registry/main/assets/edgar_flags.png)

| flagged | clean |
|---|---|
| `RnD/assets` (6/6), `OpProfit/assets` (6/6), `GrossProfit/assets` (4/6), `Accruals` (4/6), `CFO/assets` (3/6), `Equity/assets` (3/6), `Leverage` (2/6) | `ROA` (0/6), `NetMargin`, `AssetGrowth`, `SalesGrowth`, `Inventory/assets`, `PPE/assets`, `CurrentRatio` |

`ROA` — the headline signal in the underlying method paper — is clean: its raw
latency correlation of −0.296 conditions down to +0.097 once size is
controlled, and it is flagged in 0 of 6 graded cycles. **That result does not
generalise across the panel**, which is the point: susceptibility is
signal-specific, and a per-signal screen is the instrument that tells them
apart.

## Why this page exists

Curated datasets pass this screen — [OSAP](osap) because of its uniform annual
update calendar, [JKP Global Factor Data](jkp) because of its documented
four-month availability convention. Both protections live in the **publication
calendar, not in the signal definitions**. This page is the measured baseline
of what happens without one: rebuild the same kinds of signals from raw filings
at the dates they actually arrived, and half of them carry the leakage channel.

## Reproduce it

The full panel (`edgar_panel.parquet`, 914 KB, built from free SEC
`companyfacts` and `submissions` endpoints) and every script are published with
the report; each number regenerates from the publication directory.

**[Full report, panel and scripts](https://github.com/MaxWellApexLab/pit-audit-registry/blob/main/methodology/2026-08_sec-edgar/report.md)** ·
[Registry](index) ·
[Method paper](https://doi.org/10.6084/m9.figshare.33061955) ·
[Screen implementation](https://github.com/MaxWellApexLab/pit-release-gate)
