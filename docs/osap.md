---
title: "Is the Open Source Asset Pricing (Chen–Zimmermann) dataset point-in-time safe? Audit verdict: benign (by construction)"
description: >-
  Verdict: benign (by construction). 0 of 18 predictor-cycles flagged, max
  |rho-hat| = 0.0357 — the uniform annual update calendar closes the
  arrival-selection channel. Reproducible screen, free public data.
---

# Is the Open Source Asset Pricing (Chen–Zimmermann) dataset point-in-time safe?

**Verdict: `benign (by construction)`** — screened 2026-08 on the public panel
(`Accruals`, `AssetGrowth`, `BM`, vintages `200401`–`202610`, retrieved via
`openassetpricing`).

**0 of 18 predictor-cycles flagged; max \|ρ̂\| = 0.0357** against a 0.10
threshold — an order of magnitude of headroom.

## Why it is safe

OSAP's uniform annual update calendar (a 6-month datadate lag, refreshed for
all firms at once) removes filing speed from arrival ordering: completeness
steps from roughly 7% to roughly 88% in a single June update. When everyone
arrives together, arrival order cannot select on the disturbance — the channel
this screen measures is closed **by the dataset's own design**, and the
measurement confirms it.

The same protocol run on data with *no* such calendar — a panel rebuilt from
[as-filed SEC EDGAR filings](edgar) — flags **7 of 14** standard signals. The
protection is real, and it belongs to the publication calendar.

## The caveat that matters

The protection **does not travel**. Rebuilding OSAP-style signals directly from
raw EDGAR at as-filed dates loses the calendar and re-opens the channel. A
verdict is a finding about a specific version on a specific date, not a
property of the signal definitions.

## Reproduce it

```bash
pip install openassetpricing pit-release-gate numpy pandas scipy matplotlib jupyter
git clone https://github.com/MaxWellApexLab/pit-audit-registry
jupyter lab pit-audit-registry/audits/2026-08_osap/osap_predictor_completeness_screen.ipynb
```

Free public OSAP release; no WRDS, no licence. ~2 minutes, ~25 s of it the
download. The report includes a planted-truth positive control (4/4): the same
screen fires at selection strengths far below what it would take to matter here.

**[Full report](https://github.com/MaxWellApexLab/pit-audit-registry/blob/main/audits/2026-08_osap/report.md)** ·
[Registry](index) · [Method paper](https://doi.org/10.6084/m9.figshare.33061955)
