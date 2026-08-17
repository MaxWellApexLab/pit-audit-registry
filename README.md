# PIT Audit Registry

[![PIT Hygiene](https://img.shields.io/badge/PIT%20Hygiene-pledged-2ea44f)](https://github.com/MaxWellApexLab/pit-hygiene)
[![audits](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2Faudits.json)](https://github.com/MaxWellApexLab/pit-audit-registry)
[![screened with pit-release-gate](https://img.shields.io/badge/screened%20with-pit--release--gate-blue)](https://github.com/MaxWellApexLab/pit-release-gate)
[![signal-cycles screened](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2Fscreened.json)](#the-registry)

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
| [Open Source Asset Pricing (OSAP)](https://github.com/OpenSourceAP/CrossSection) — `Accruals`, `AssetGrowth`, `BM` | panel retrieved via `openassetpricing`, stamps `200401`–`202610` | 2026-08 | Uniform annual update calendar closes the arrival-selection channel; completeness steps ~7% → ~88% in June. Measured \|ρ̂\| ≤ 0.036 across 18 predictor-cycles, an order of magnitude under the 0.10 threshold. | [![PIT audit](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2Fosap.json)](audits/2026-08_osap/report.md) | [audits/2026-08_osap/](audits/2026-08_osap/report.md) |
| [JKP Global Factor Data](https://jkpfactors.com/) — the documented accounting-availability convention | `Documentation.pdf` (55 pp.), retrieved 2026-08 | 2026-08 | A uniform four-month availability assumption applied to every accounting variable removes filing speed from arrival ordering, closing the channel structurally. Demonstrated on planted truth: the same leakage read −0.324 under as-filed release and +0.017 under uniform release. Cost: a blanket timeliness tax on all 406 characteristics. Not externally verifiable — no arrival field is documented. | [![PIT audit](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2Fjkp-gfd.json)](audits/2026-08_jkp-gfd/report.md) | [audits/2026-08_jkp-gfd/](audits/2026-08_jkp-gfd/report.md) |

Each badge above is a live endpoint served from this repository, and **the audited project is
welcome to display it** — see the snippet at the foot of each report.

## Why screen? The wild flags.

Both entries above came out benign, and a reasonable reader should ask whether this screen is
capable of saying anything else. It is. Run it on data that has **no** publication calendar
protecting it — a panel rebuilt from as-filed SEC EDGAR filings, on observed filing dates — and
**7 of 14 signals are flagged, 28 of 84 signal-cycles**, while `ROA` passes cleanly at **0 of 6**.

→ [**SEC EDGAR as-filed US panel**](methodology/2026-08_sec-edgar/report.md) — the measured version
of the caution the OSAP entry closes on: a dataset's protection belongs to its publication
calendar, and **it does not travel** to a rebuild from as-filed sources.

---

## Methodology

Not every screen grades a project. These pages demonstrate the mechanism the registry exists to
measure. They carry **no badge, no verdict on anyone, and no row in the table above** — there is no
project under test.

| page | what it demonstrates |
|---|---|
| [SEC EDGAR as-filed US panel](methodology/2026-08_sec-edgar/report.md) | What an as-filed rebuild costs. On **observed** SEC filing dates, the raw latency–signal correlation for industry-adjusted ROA is −0.296 and conditions down to +0.097; across 14 signals, 28 of 84 signal-cycles are flagged and 7 of 14 signals are clean. |
| [As-of join semantics in feature stores](methodology/2026-08_feast-pit-join/report.md) | Why a point-in-time-correct join is not enough. On synthetic planted truth, a correct as-of join still yields an offline rank IC inflated by +0.0390 (+10.7%) once the evaluation sample is held fixed. A property of the mechanism, not a defect in any one implementation. |

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

## Licensing

Copyright (c) 2026 Max Well Apex LLC.

- **Audit reports, methodology pages, and prose** (`audits/`, `methodology/`,
  `README.md`, `AUDIT_TEMPLATE.md`) — [CC BY 4.0](LICENSE): share and adapt
  freely, with attribution to this registry.
- **Code** (`tools/`, and any scripts inside report folders) —
  [MIT](LICENSE-CODE).
