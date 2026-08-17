---
title: PIT Audit Registry
description: >-
  Reproducible answers to one question — is this public dataset safe from
  incomplete-cross-section leakage? Verdicts for OSAP, JKP Global Factor Data,
  and raw SEC EDGAR as-filed panels.
---

# PIT Audit Registry

Reproducible findings on whether public datasets and pipelines are exposed to
**incomplete-cross-section leakage** — the look-ahead risk that arises when a
cross-sectional quantity is computed before the group has finished reporting,
and reporting timing is related to the quantity being measured.

Every entry is a measurement with a command attached.

## Verdicts

- **[Is the Open Source Asset Pricing (Chen–Zimmermann) dataset point-in-time safe?](osap)**
  — `benign (by construction)`: 0 of 18 predictor-cycles flagged, max \|ρ̂\| = 0.0357.
- **[Does JKP Global Factor Data have look-ahead bias from staggered filings?](jkp)**
  — `benign (by construction)`: a uniform four-month availability convention closes
  the channel structurally.
- **[Is as-filed SEC EDGAR data safe for cross-sectional signals?](edgar)**
  — **7 of 14 standard signals flagged** (28/84 signal-cycles). ROA is clean at 0/6.
- **[Do staggered SEC Form 13F filings bias cross-manager statistics?](13f)**
  — **flagged in 11 of 11 quarters**, at ten times this panel's measured noise floor,
  on filing dates that are observed rather than reconstructed.

![Per-signal susceptibility on the as-filed SEC EDGAR panel](https://raw.githubusercontent.com/MaxWellApexLab/pit-audit-registry/main/assets/edgar_flags.png)

The pattern across the four: **a publication calendar is doing real protective
work, and the protection does not travel.** Curated releases with a uniform
update calendar come out clean; data taken at the dates it actually arrived —
as-filed EDGAR filings, or 13F filings inside their 45-day window — does not.

## Method, in one paragraph

The susceptibility statistic ρ̂ is the partial correlation between an entity's
filing latency and the complete-cross-section residual of the signal, given
observables — fitted on prior *completed* periods only, frozen, then applied
forward (threshold 0.10). Every published screen includes a planted-truth
positive control: a report where the screen never fires is not published unless
the screen has been shown to fire on data whose answer is known by
construction. Method papers:
[measurement](https://doi.org/10.6084/m9.figshare.33061955) ·
[release control](https://doi.org/10.6084/m9.figshare.33158615).

## Reproduce

```bash
pip install openassetpricing pit-release-gate numpy pandas scipy matplotlib jupyter
git clone https://github.com/MaxWellApexLab/pit-audit-registry
jupyter lab pit-audit-registry/audits/2026-08_osap/osap_predictor_completeness_screen.ipynb
```

Free public data only; no accounts, no licences. ~2 minutes.

---

Reports and registry: [github.com/MaxWellApexLab/pit-audit-registry](https://github.com/MaxWellApexLab/pit-audit-registry) ·
Screen implementation: [pit-release-gate](https://github.com/MaxWellApexLab/pit-release-gate) (MIT) ·
Maintained by Max Well Apex LLC · Reports CC BY 4.0
