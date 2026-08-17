# Incomplete-cross-section leakage screen — SEC Form 13F institutional manager panel

| | |
|---|---|
| **Target** | [SEC Form 13F structured data sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) — institutional manager holdings |
| **Version / vintage** | quarterly zips `2020q1`–`2023q4`, downloaded 2026-08-18 |
| **Screened on** | 2026-08-18 |
| **Screened by** | Max Well Apex LLC |
| **Screen version** | `pit-release-gate` 0.1.1 (`screen_dataframe`) |
| **Verdict** | **`susceptible (details)`** — all three screened manager characteristics flagged in **11 of 11** quarters |

**One-paragraph finding.** Institutional managers file Form 13F on genuinely
staggered dates inside the statutory 45-day window — a tenth file within two
weeks, the median waits about 39 days, and a fifth arrive on the deadline
itself. Across 16 quarters and 85,036 manager-quarters, three standard
cross-manager characteristics — portfolio concentration (HHI), top-10 share,
and log position count — each read **|ρ̂| ≈ 0.13–0.18** against a noise floor of
**0.015** measured on this same panel, and each was flagged in every one of the
11 screened quarters. The direction is internally consistent: managers holding
more positions than their size predicts file **earlier**, and more concentrated
managers file **later**. Permuting arrival order within each quarter collapses
the reading to 0.000–0.007, so it is arrival order that carries the
information, not any artifact of the characteristics. **Prior work already documents that active and larger managers delay** (§1a);
what is measured here is what that delay does to a cross-sectional feature.
**What this does not show:** any downstream return or performance consequence. This is a
measurement that the arrival-selection channel is open on this panel, at a
magnitude an order of magnitude above its own noise floor — not an estimate of
what it costs anyone.

---

## 1. Data context

**The cross-section.** All managers filing Form 13F-HR for one report quarter.
Section 13(f) requires an institutional investment manager exercising
discretion over more than $100M in Section 13(f) securities to report holdings
within 45 days of quarter end. The cross-section is therefore the set of
managers describing the *same* quarter, and a quantity computed across managers
before day 45 uses whichever managers have filed so far.

**Where arrival times come from — observed, not reconstructed.** The
`SUBMISSION.tsv` member of each quarterly data set carries `FILING_DATE` and
`PERIODOFREPORT` per accession. Arrival latency is their difference in days.
This is the actual date SEC received the filing; nothing is inferred, which is
the main respect in which this panel is stronger evidence than a
reconstruction-based screen.

**Filters, and what they cost.**

- 13F-HR only. Amendments (`13F-HR/A`) arrive later by construction, so
  including them would confound arrival timing with revision behaviour — a
  different question.
- One filing per (manager, quarter): the earliest, i.e. the original report.
- Latency kept to `[0, 45]` days. Filings stamped outside the statutory window
  are late or mis-stamped; **15,152 manager-quarters sit exactly on day 45**,
  and §5 shows the finding survives dropping all of them.
- Positions with non-positive reported value dropped before aggregation.

**Scale.** 85,036 manager-quarters; 16 report quarters (2019-12-31 through
2023-09-30); 4,069–6,572 managers per quarter; 11 quarters screened after the
5-quarter trailing window is spent on fitting.

**Arrival distribution** (days after quarter end): p10 ≈ 13–19, median ≈ 36–41,
p90 ≈ 43–45. The window is used, not ignored.


## 1a. What is already known, and what this adds

**The pattern is documented.** Christoffersen, Danesh and Musto, *Why Do
Institutions Delay Reporting Their Shareholdings? Evidence from Form 13F*
(2015 draft, [Rodney White Center WP 13-15](https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/13-15.musto_.pdf))
study 14 years of filings and find, in their words, that "more active
institutions delay their holdings longer" — where activeness is measured by,
among other things, "a portfolio normalized herfindahl measure of
concentration" — and that larger institutions delay as well. Their explanation
is strategic: protection from front-runners and concealment of voting power.

**Our measurements reproduce their pattern independently.** Conditional on
portfolio value, concentration reads +0.143 and position count −0.160 against
filing latency; unconditionally, +0.128 and −0.127. Day-45 filers are larger
(mean log value 16.2 vs 14.7), more concentrated (HHI 0.151 vs 0.096) and hold
fewer positions (log 3.99 vs 4.62). That an independent statistic on
independent data recovers a published pattern is a check this screen had to
pass, and did.

**What this report adds is not the pattern but its consequence.** The prior
work asks *why* institutions delay. It does not ask what the delay does to a
cross-sectional quantity computed before the window closes: the words
"researcher" and "incomplete" do not appear in that paper at all, and "bias"
appears only inside a citation. This report supplies the missing half — the
susceptibility ρ̂ that the delay pattern implies for anyone building
cross-manager features, and the required completeness that follows from it.

**Stated plainly, so it cannot be overread:** we did not discover that 13F
filing timing is related to manager type. We measured what that known
relationship costs a cross-sectional feature, on a frozen honest protocol,
and published the number.

## 2. Method

> ρ̂ = partial correlation between arrival latency and the complete-cross-section
> residual, conditional on an observable — fitted on prior *completed* quarters,
> frozen, then applied to the quarter being graded.

- **Conditioner**: log total reported portfolio value. It is a property of the
  manager's own filing, known once the quarter closes, and it is the obvious
  driver of both filing speed and portfolio structure — which is exactly why it
  must be partialled out rather than left to explain the result.
- **Threshold**: |ρ̂| > 0.10, the value used in the method paper and the other
  registry entries. On this panel it sits about 7× the measured noise floor.
- **Trailing window** K = 5 quarters; **evaluation quarters** 11; **minimum
  entities** 6 (never binding here).
- **Signals screened**: `concentration_hhi` (Herfindahl of position values),
  `top10_share`, `log_positions`. All three are scale-free or count-based, so
  none is mechanically identical to the conditioner.
- Method references:
  [doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955)
  (screen),
  [doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615)
  (release controller).

## 3. Positive control

Planted truth on the **real** 13F arrival dates: the coupling strength is a knob,
the answer is known by construction, and the screen never sees the knob.

| planted case | ρ̂ | φ_req | screen says | should say | correct |
|---|---|---|---|---|---|
| clean (no coupling) | −0.0022 | 0.35 | benign | benign | ✅ |
| composition only: signal ~ 3× size | +0.0000 | 0.35 | benign | benign | ✅ |
| composition only: signal ~ 6× size | −0.0023 | 0.36 | benign | benign | ✅ |
| mild leak (0.35 × latency) | −0.3008 | 0.65 | susceptible | susceptible | ✅ |
| strong leak (1.20 × latency) | −0.7162 | 1.00 | susceptible | susceptible | ✅ |
| leak + composition together | −0.3020 | 0.65 | susceptible | susceptible | ✅ |

**6 / 6 correct.** The two composition rows are the ones that matter: a signal
coupled to the conditioner at six times the leak strength still reads benign,
so the screen is not a completeness threshold with extra steps — it responds to
selection on the part of the signal the conditioner cannot explain.

## 4. Result

Frozen protocol, K = 5, threshold 0.10, 11 screened quarters:

| signal | mean ρ̂ | max \|ρ̂\| | cycles flagged | mean φ_req | verdict |
|---|---|---|---|---|---|
| `log_positions` | −0.1789 | 0.2158 | **11 / 11** | 0.529 | susceptible |
| `top10_share` | +0.1474 | 0.1886 | **11 / 11** | 0.497 | susceptible |
| `concentration_hhi` | +0.1446 | 0.1617 | **11 / 11** | 0.495 | susceptible |

**Noise floor on this panel: 0.0152** — the largest |ρ̂| reached by any of three
signals drawn independently of everything else. The real readings are roughly
**ten times** that.

Per-quarter frozen estimate for `concentration_hhi`, showing this is not one
bad quarter:

| quarter ending | n | ρ̂ (frozen) | |
|---|---|---|---|
| 2021-03-31 | 4,395 | +0.1617 | flagged |
| 2021-06-30 | 4,436 | +0.1538 | flagged |
| 2021-09-30 | 4,149 | +0.1452 | flagged |
| 2021-12-31 | 6,135 | +0.1271 | flagged |
| 2022-03-31 | 4,895 | +0.1400 | flagged |
| 2022-06-30 | 4,917 | +0.1366 | flagged |
| 2022-09-30 | 6,339 | +0.1341 | flagged |
| 2022-12-31 | 6,519 | +0.1381 | flagged |
| 2023-03-31 | 6,546 | +0.1526 | flagged |
| 2023-06-30 | 6,568 | +0.1464 | flagged |
| 2023-09-30 | 6,572 | +0.1549 | flagged |

Range 0.127–0.162 across eleven independent quarters.

**Reading the sign.** `log_positions` is negative and the two concentration
measures are positive: conditional on portfolio value, managers running *more*
positions file *earlier*, and *more concentrated* managers file *later*. The two
statements are the same statement, which is a weak internal consistency check
the screen did not have to pass.

## 5. Robustness

| test | why it could have killed the finding | result |
|---|---|---|
| **arrival permuted within quarter**, 3 reps | if the reading survives, it was never about arrival | ρ̂ = +0.007, −0.004, +0.002 → **0 / 11 flagged in all three reps** |
| **drop day-45 filers** (15,152 rows) | a deadline pile-up creates tied latencies that could drive the rank correlation | 0.107–0.134; 11/11, 11/11, **7/11** for `top10_share` |
| **quadratic size control** | curvature in the size–signal relation could pass as arrival selection | 0.122–0.147; 11/11, 11/11, 10/11 |
| **trailing K = 3** | a result that only exists at K = 5 is a tuning artifact | 0.148–0.186, 13/13 |
| **trailing K = 8** | as above | 0.143–0.176, 8/8 |

The shuffle control is the decisive one and it is decisive in the right
direction: permuting arrival order inside each quarter collapses every reading
into the noise floor.

The honest weak spot: `top10_share` drops to 7 of 11 flagged once deadline-day
filers are removed. The other two signals do not move materially. A reader
should treat `top10_share` as the least robust of the three.

## 6. Reproduce

```bash
pip install pit-release-gate polars
python build_13f_panel.py     # downloads 16 quarterly zips from sec.gov, ~1.1 GB streamed
python screen_13f.py          # noise floor, positive control, real signals
python robustness_13f.py      # the five robustness tests in §5
```

- **Runtime**: ~2 minutes for the download and panel build, ~4 minutes for the
  screens.
- **Requires a licence or account**: **no.** SEC structured data sets are free
  and unauthenticated; the only requirement is a User-Agent identifying the
  requester, which the script sets.
- **Determinism**: the controls are seeded (`20260818`). The real-signal
  readings depend only on the downloaded data, which is a fixed historical
  release.
- **Artifacts kept**: `panel_13f.parquet` (85,036 rows, the aggregated panel —
  the raw zips are streamed and discarded), `screen_13f_results.json`.

## 7. Scope and what this is not

- **Not a finding about anyone's product.** SEC publishes filings; it does not
  publish a cross-manager characteristic panel. The channel measured here opens
  when *a user* computes cross-manager quantities before the window closes.
- **Not an economic magnitude.** No return, alpha, or performance consequence is
  estimated. The registry's standing rule applies: a susceptibility measurement
  is not a claim about money.
- **Not a claim about any individual manager.** Every number is a
  cross-sectional property of the manager population in a quarter.
- **The obvious remedy is already available and free**: wait for day 45. The
  graded alternative is what φ_req in §4 quantifies — the mean required
  completeness of ~0.50 says these signals should not be released on a
  half-arrived cross-section.
