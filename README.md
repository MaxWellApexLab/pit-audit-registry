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

**[Tool](https://github.com/MaxWellApexLab/pit-release-gate) ·
[Pledge](https://github.com/MaxWellApexLab/pit-hygiene) ·
[Methodology](#methodology) ·
[Request a screen](#requesting-or-contributing-a-screen)**

---

## The wild flags

Run the screen on data that has **no** publication calendar protecting it — a US panel
rebuilt from as-filed SEC EDGAR filings, on **observed** filing dates — and **7 of 14
standard fundamental signals are flagged: 28 of 84 signal-cycles**, while `ROA` passes
cleanly at 0 of 6.

![Per-signal susceptibility on the as-filed SEC EDGAR panel: 7 of 14 signals exceed the 0.10 threshold, led by RnD/assets and OpProfit/assets at 6 of 6 cycles; ROA is clean at 0 of 6](https://raw.githubusercontent.com/MaxWellApexLab/pit-audit-registry/main/assets/edgar_flags.png)

→ [**SEC EDGAR as-filed US panel — full report, panel and scripts included**](methodology/2026-08_sec-edgar/report.md)

That is the baseline the curated datasets below are measured against. Their green
entries are not "nothing to see here" — they are evidence that **a publication calendar
is doing real protective work**, and that the protection **does not travel** when a user
rebuilds the same signals from as-filed sources.

Reproduce the first registry entry end-to-end — free public data, no account, ~2 minutes:

```bash
pip install openassetpricing pit-release-gate numpy pandas scipy matplotlib jupyter
git clone https://github.com/MaxWellApexLab/pit-audit-registry
jupyter lab pit-audit-registry/audits/2026-08_osap/osap_predictor_completeness_screen.ipynb  # Run All
# expected: |rho_hat| <= 0.036 across all 18 predictor-cycles (threshold 0.10)
```

## The registry

### Open Source Asset Pricing (OSAP) — Chen & Zimmermann

[![PIT audit](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2Fosap.json)](audits/2026-08_osap/report.md)

`Accruals`, `AssetGrowth`, `BM` · panel via `openassetpricing`, stamps `200401`–`202610` · screened 2026-08

The uniform annual update calendar closes the arrival-selection channel;
measured \|ρ̂\| ≤ 0.036 across 18 predictor-cycles, an order of magnitude under
the 0.10 threshold.

**[Report](audits/2026-08_osap/report.md) ·
[Notebook](audits/2026-08_osap/osap_predictor_completeness_screen.ipynb) ·
[Badge snippet](audits/2026-08_osap/report.md#badge)**

### JKP Global Factor Data — Jensen, Kelly & Pedersen

[![PIT audit](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2Fjkp-gfd.json)](audits/2026-08_jkp-gfd/report.md)

Documented accounting-availability convention · `Documentation.pdf` (55 pp.), retrieved 2026-08

A uniform four-month availability assumption removes filing speed from arrival
ordering — structurally immune. Verified on planted truth: the same leakage read
−0.324 under as-filed release, +0.017 under uniform release. Cost: a blanket
timeliness tax on all 406 characteristics; not externally verifiable, as no
arrival field is documented.

**[Report](audits/2026-08_jkp-gfd/report.md) ·
[Control script](audits/2026-08_jkp-gfd/jkp_construction_control.py) ·
[Badge snippet](audits/2026-08_jkp-gfd/report.md#badge)**

## Reading a verdict

The verdict on a report takes exactly three values:

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

## If you maintain a project listed here

The badge next to your entry is a **live endpoint served from this repository**, and you
are welcome to display it:

```markdown
[![PIT audit](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2F<target>.json)](link-to-your-report)
```

Displaying it claims exactly one thing: that this screen was run on the stated version
with the stated result. It is not a certification, an award, or an endorsement — the
[report](#the-registry) behind it is the claim. The exact snippet for your project is at
the foot of your report.

If you believe a finding is wrong, open an issue with the reproduction that shows it.
Findings are corrected in place with a dated note explaining what changed, and the
correction stays visible in the report; nothing is silently edited.

---

## Methodology

Not every screen grades a project. These pages demonstrate the mechanism the registry exists to
measure. They carry **no badge, no verdict on anyone, and no entry above** — there is no
project under test.

| page | what it demonstrates |
|---|---|
| [SEC EDGAR as-filed US panel](methodology/2026-08_sec-edgar/report.md) | What an as-filed rebuild costs. On **observed** SEC filing dates, the raw latency–signal correlation for industry-adjusted ROA is −0.296 and conditions down to +0.097; across 14 signals, 28 of 84 signal-cycles are flagged and 7 of 14 signals are clean. |
| [SEC Form 13F institutional manager panel](methodology/2026-08_sec-13f/report.md) | What **observed** filing dates cost when the arrival window is 45 days wide. Across 16 quarters and 85,036 manager-quarters, three standard cross-manager characteristics each read \|ρ̂\| ≈ 0.13–0.18 against a noise floor of 0.015 measured on the same panel, flagged in 11 of 11 screened quarters. Permuting arrival order within quarters collapses the reading to ~0.00. The delay pattern itself is documented in the literature; what is measured here is its consequence for a cross-sectional feature. |
| [As-of join semantics in feature stores](methodology/2026-08_feast-pit-join/report.md) | Why a point-in-time-correct join is not enough. On synthetic planted truth, a correct as-of join still yields an offline rank IC inflated by +0.0390 (+10.7%) once the evaluation sample is held fixed. A property of the mechanism, not a defect in any one implementation. |

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

## Requesting or contributing a screen

Open an issue. Include a link to the public data or pipeline, and how a reader would obtain
it without a licence. If you have run a screen yourself and want it listed, open a pull
request with a report following [AUDIT_TEMPLATE.md](AUDIT_TEMPLATE.md) — including the
positive control.

---

Maintained by Max Well Apex LLC.

## Licensing

Copyright (c) 2026 Max Well Apex LLC.

- **Audit reports, methodology pages, and prose** (`audits/`, `methodology/`,
  `README.md`, `AUDIT_TEMPLATE.md`) — [CC BY 4.0](LICENSE): share and adapt
  freely, with attribution to this registry.
- **Code** (`tools/`, and any scripts inside report folders) —
  [MIT](LICENSE-CODE).
