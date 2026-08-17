# PIT Audit Registry

[![PIT Hygiene](https://img.shields.io/badge/PIT%20Hygiene-pledged-2ea44f)](https://github.com/MaxWellApexLab/pit-hygiene)
[![screened with pit-release-gate](https://img.shields.io/badge/screened%20with-pit--release--gate-blue)](https://github.com/MaxWellApexLab/pit-release-gate)

[![screened with pit-release-gate](https://img.shields.io/badge/screened%20with-pit--release--gate-blue)](https://github.com/MaxWellApexLab/pit-release-gate)

Reproducible findings on whether public datasets and pipelines are exposed to
**incomplete-cross-section leakage** — the bias that arises when a cross-sectional
quantity is computed before the group finished reporting, and reporting timing is
related to the quantity being measured.

Every entry here is a **measurement with a command attached**. Each report states what was
screened, at what version, with what result, and how to reproduce the number yourself.

---

## The registry

| target | version / vintage | date | finding | verdict | full report |
|---|---|---|---|---|---|
| [Open Source Asset Pricing (OSAP)](https://github.com/OpenSourceAP/CrossSection) — `Accruals`, `AssetGrowth`, `BM` | panel retrieved via `openassetpricing`, stamps `200401`–`202610` | 2026-08 | Uniform annual update calendar closes the arrival-selection channel; completeness steps ~7% → ~88% in June. Measured \|ρ̂\| ≤ 0.036 across 18 predictor-cycles, an order of magnitude under the 0.10 threshold. | `benign (by construction)` | [audits/2026-08_osap/](audits/2026-08_osap/report.md) |

---

## What gets screened

**In scope.** Public datasets, pipelines, and reproduction code where there is a genuine
staggered-arrival cross-section — entities that report on different dates and a quantity
computed across them.

**Explicitly out of scope**, stated up front so the boundary is not something you have to
infer:

- **Backtest engines themselves.** Whether an engine has look-ahead bugs is a different
  question, well covered by existing tooling, and not what ρ̂ measures.
- **Libraries with no arrival-time context.** A statistics or optimisation library has no
  cross-section and no arrival times; there is nothing here to measure.
- **Proprietary or licensed data.** Every report must be reproducible by a reader, so
  screens run on free public releases only.
- **Trading performance.** Nothing here is an assessment of whether a signal makes money.

## How a screen is run

1. **Reconstruct arrival times** for each entity in each cross-sectional period, from the
   target's own published data, and document the reconstruction and its limits.
2. **Estimate ρ̂** — the partial correlation between arrival latency and the
   complete-cross-section residual, conditional on an observable — on prior *completed*
   periods only, then freeze it and apply it forward. The estimate is never computed on the
   period it grades.
3. **Run a planted-truth positive control** in the same report. A screen that never fires is
   worthless unless it has been shown that it *can* fire, on data whose answer is known by
   construction. A report without a passing positive control is not published.
4. **Report per-period results**, not just an aggregate, so a reader can see the dispersion.

Method references: the screen and the release controller are defined in
[doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) and
[doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615). The
reference implementation is the MIT-licensed
[`pit-release-gate`](https://github.com/MaxWellApexLab/pit-release-gate).

## Reading a verdict

The `verdict` column takes exactly three values:

| verdict | meaning |
|---|---|
| `benign (by construction)` | The target's own design closes the arrival-selection channel — e.g. a uniform reporting lag applied before publication. Measurement confirms it, but the *reason* is structural, and it stops holding the moment a user rebuilds the data from as-filed sources. |
| `benign (measured)` | No structural reason to expect immunity, and ρ̂ came out under threshold anyway across the screened periods. |
| `susceptible (details)` | ρ̂ exceeded the threshold in one or more periods. The report says which, how large, and what required completeness the graded gate assigns. |

A verdict is a **finding about a specific version on a specific date**, not a property of the
project. Data conventions change; re-screening after a major release is the reader's job, and
the reproduction command in each report is there to make that cheap.

These are audit reports. Nothing here is an award, a ranking, or a grade of overall quality —
a `susceptible` finding on a well-built dataset is a normal and expected result, and usually
says more about the reporting calendar of the underlying filings than about the project.

## Requesting or contributing a screen

Open an issue. Include a link to the public data or pipeline, and how a reader would obtain
it without a licence. If you have run a screen yourself and want it listed, open a pull
request with a report following [AUDIT_TEMPLATE.md](AUDIT_TEMPLATE.md) — including the
positive control.

## Corrections

If you maintain a target listed here and believe a finding is wrong, open an issue with the
reproduction that shows it. Findings are corrected in place with a dated note explaining what
changed, and the correction stays visible in the report; nothing is silently edited.

---

Maintained by Max Well Apex LLC. Reports are CC BY 4.0; screening code is MIT.
