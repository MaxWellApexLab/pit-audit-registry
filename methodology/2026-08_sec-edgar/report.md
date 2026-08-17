# Incomplete-cross-section leakage screen — SEC EDGAR as-filed US panel

| | |
|---|---|
| **Target** | SEC EDGAR as-filed US equity panel, assembled from the free [`companyfacts`](https://data.sec.gov/api/xbrl/companyfacts/) and [`submissions`](https://data.sec.gov/submissions/) endpoints — 14 industry-adjusted cross-sectional signals |
| **Page kind** | **Methodology page.** Not a registry entry — no scoreboard row, no badge, no table row. Its job is to answer "what happens when a dataset's publication calendar is *not* there to protect you?" |
| **Signals screened** | `ROA`, `CFO/assets`, `GrossProfit/assets`, `OpProfit/assets`, `NetMargin`, `Accruals`, `AssetGrowth`, `SalesGrowth`, `Inventory/assets`, `PPE/assets`, `Leverage`, `Equity/assets`, `RnD/assets`, `CurrentRatio` |
| **Version / vintage** | Panel built from SEC XBRL; 8,657 firm-years / 871 firms on the widest filter, 8,118 firm-years / 856 firms / 62 SIC2 industries on the ROA-complete filter; fiscal years 2009–2026, per-year coverage 2011–2025 |
| **Screened on** | 2026-08 |
| **Screened by** | Kuan-Ta Wu, Max Well Apex LLC |
| **Screen version** | inline implementation (`V2/compute/edgar_*.py`), same estimator as `pit-release-gate` 0.1.1; see §6 |
| **Verdict** | **`susceptible (details)`** — 7 of 14 signals flagged in at least one graded cycle; 28 of 84 signal-cycles flagged. `ROA`, the signal behind the published headline, is **benign** at 0/6 |

**Finding.** This is the only entry in the registry screened on **observed** filing timestamps rather
than reconstructed ones: SEC EDGAR records the date each 10-K was filed, so arrival latency is
measured, not inferred. Two things come out, and reporting only the first would leave a wrong
impression. **First, the published headline reproduces exactly.** The raw within-industry
correlation between filing latency and industry-adjusted `ROA` is **−0.296**, which looks alarming,
and it is almost entirely an *observable size* channel: large firms file earlier
(corr = **−0.688**) and are more profitable (corr = **+0.508**), a size-mediated path of **−0.349**
that accounts for the whole raw figure. Condition on size and the susceptibility the theory
identifies is **+0.097** — slightly positive, the opposite sign to leakage. Under the registry's
graded protocol `ROA` is flagged in **0 of 6** cycles. **Second, that result does not generalise
across the panel.** Applying the identical protocol to all 14 signals flags **28 of 84
signal-cycles**, with 7 signals clean and 7 flagged at least once — `RnD/assets` (6/6) and
`OpProfit/assets` (6/6) in every graded cycle. **As-filed data has no uniform publication lag to
close the arrival-selection channel**, which is precisely the warning the OSAP entry in this
registry ends on: that dataset's protection comes from its update calendar and *does not travel* to
a panel rebuilt from real filing dates. This report is the measured version of that warning.

*Registry note: by design this page does not go on the scoreboard, does not receive a badge, and
does not occupy a row in the registry table. It is the empirical companion to the OSAP entry's
closing caution, and its subject is what an as-filed rebuild costs you — not a grade on SEC EDGAR,
which is the source of truth for the filing dates that made the measurement possible at all.*

---

## 1. Data context

**The cross-section.** One fiscal year of one signal within one 2-digit SIC industry: all firms in
that industry carrying a value for that signal in that year. Industry-adjustment is demeaning
within the (SIC2 × fiscal-year) group, which is the standard construction and the one that requires
the peer group to be complete.

**Where arrival times come from — observed, not reconstructed.** Each fiscal year's value is taken
from the **earliest-filed** 10-K (the original annual report, not a later amendment), and the
`submissions` endpoint supplies that filing's date directly. Arrival latency is
`filed − fiscal period end`, in days. This removes the identification limit that governs every
other entry in this registry, where latency has to be reconstructed from a carry-forward panel.

**Filters, and which way each one biases the result.**

| filter | reason | direction of the bias it introduces |
|---|---|---|
| `Assets > 0` | ratios need a positive denominator | none material |
| `0 < latency < 200` days | drops mis-stamped filings and late amendments | trims the tail that would *increase* measured staggering — conservative |
| group ≥ 20 firms | the partial correlation is unstable in tiny industries | drops thin industries; no directional effect on ρ̂ |
| firms present in the 2015 reporting set | how the panel was assembled | **tilts to larger, longer-lived firms** — see §5 |

**Scale actually screened.**

| filter used | firm-years | firms | industries | groups (SIC2 × year, ≥20) |
|---|---|---|---|---|
| widest (`Assets > 0`, latency) | 8,657 | 871 | — | — |
| ROA-complete | 8,118 | 856 | 62 | 108 |

Estimation-group sizes for `ROA`: **min 20, median 35, max 102** firms. Per-year coverage runs
2011–2025; fiscal-year stamps extend to 2026 because some fiscal years close mid-calendar.

## 2. Method

> ρ̂ = partial correlation between arrival latency and the complete-cross-section residual,
> conditional on an observable — pooled over (SIC2 × fiscal-year) groups, each standardised within
> group before pooling.

| parameter | value |
|---|---|
| Conditioner | **log book assets** (size), demeaned within group |
| Flagging threshold | \|ρ̂\| > 0.10 |
| Trailing window K | 5 completed fiscal years |
| Evaluation cycles | 6 most recent per signal |
| Minimum entities | 20 per (SIC2 × year) group |
| Completeness floor φ_min | 0.35 |
| Graded rule | φ_req = min(1, φ_min + κ·\|ρ̂\|), κ = 1.0 |
| Uncertainty | cluster bootstrap over (SIC2 × year) groups, 1,000–2,000 draws |

**Two estimators are reported, and they answer different questions.** The distinction matters
enough that conflating them would change the verdict:

- **Ex post, full sample** — ρ̂ fitted on all years at once. This is the statistic the method
  preprint publishes, and it is a *measurement* of the panel, not a gate decision. It corresponds
  to the `ρ̂ (ex post)` column in the OSAP entry, which never entered a decision there either.
- **Frozen** — ρ̂ for year *Y* fitted on years *Y−5 … Y−1*, frozen, then applied to *Y*. This is
  the registry's graded protocol and the only one a verdict may rest on. Nothing from a cycle
  enters its own gate.

**On the conditioner, stated plainly.** Size here is *contemporaneous* book assets, matching the
published specification. The registry's template asks for a conditioner knowable before the period
opens; log assets is highly persistent, so a one-year-lagged version would be close, but it is not
identical and this report does not claim it is. Anyone re-running with lagged size should expect
small movements in ρ̂.

**Method references:**
[doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) (preprint) defines
ρ̂ and the matched-placebo design;
[doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615) (preprint) defines
the release controller.

## 3. Positive control

The identical size-partialled estimator, run on planted-truth cross-sections shaped like this panel
— the same 108 groups, the same group-size distribution — where selection strength is a knob
(`c_a` = selection on the unobserved disturbance, the true leakage knob; `c_x` = selection on the
observable, the benign kind):

| planted case | ρ̂ | φ_req | screen says | should say | correct |
|---|---|---|---|---|---|
| clean (c_a=0.0, c_x=0.3) | +0.017 | 0.37 | benign | benign | ✅ |
| composition (c_a=0.0, c_x=2.0) | +0.023 | 0.37 | benign | benign | ✅ |
| mild leak (c_a=0.3, c_x=0.7) | −0.499 | 0.85 | susceptible | susceptible | ✅ |
| strong leak (c_a=1.0, c_x=0.7) | −0.864 | 1.00 | susceptible | susceptible | ✅ |

**Control result: 4/4 correct.**

The `composition` row is the one that earns the screen its keep: selection there is more than six
times stronger than in `clean`, but it runs entirely through the **observable**, and the screen
still calls it benign. The measured noise floor on this data shape is about **0.02**, so the
flagged values reported in §4 — 0.10 to 0.20 — sit well clear of it and are not noise.

## 4. Results

### 4.1 The headline decomposition (`ROA`, ex post, full sample)

| quantity | estimate | 95% CI |
|---|---|---|
| corr(latency, signal) — **raw** | **−0.296** | [−0.323, −0.269] |
| corr(latency, log size) | −0.688 | — |
| corr(signal, log size) | +0.508 | — |
| size-mediated path (product) | **−0.349** | — |
| ρ̂ = corr(latency, signal \| size) — **conditional** | **+0.097** | [+0.047, +0.143] |

The raw −0.30 and the conditional +0.09 differ in both magnitude and sign, and the size path
accounts for the gap. Three independent runs of the estimator on this panel gave the same interval
for the conditional figure ([+0.047, +0.143], [+0.048, +0.145], [+0.050, +0.143]).

**The matched control agrees.** Decile-reassignment excess for `ROA`, early-35% versus complete:

| control | excess | 95% CI |
|---|---|---|
| size-only control (`xi_size`) | **+23.28 pp** | [+14.97, +31.24] |
| covariate-matched control (`xi_match`) | **−0.71 pp** | [−6.56, +2.63] |

The size-only control reads a large excess; the matched control, which holds composition fixed,
reads zero within its interval. That gap **is** the size channel, measured a second way.

### 4.2 Per-signal map, ex post (full sample)

`rho_raw` = as-traded susceptibility; `rho_size` = residual after removing observable size.

| signal | rho_raw | rho_size | 95% CI (rho_size) | φ_req |
|---|---|---|---|---|
| `ROA` | −0.296 | +0.097 | [+0.047, +0.143] | 0.45 |
| `CFO/assets` | −0.297 | +0.120 | [+0.070, +0.166] | 0.47 |
| `GrossProfit/assets` | −0.005 | −0.105 | [−0.156, −0.055] | 0.45 |
| `OpProfit/assets` | −0.310 | +0.182 | [+0.137, +0.226] | 0.53 |
| `NetMargin` | −0.258 | +0.028 | [−0.016, +0.070] | 0.38 |
| `Accruals` | −0.222 | +0.131 | [+0.091, +0.168] | 0.48 |
| `AssetGrowth` | +0.094 | +0.068 | [+0.037, +0.102] | 0.42 |
| `SalesGrowth` | +0.053 | +0.025 | [−0.021, +0.067] | 0.37 |
| `Inventory/assets` | +0.172 | +0.039 | [−0.035, +0.100] | 0.39 |
| `PPE/assets` | −0.005 | −0.053 | [−0.085, −0.023] | 0.40 |
| `Leverage` | +0.254 | −0.086 | [−0.136, −0.040] | 0.44 |
| `Equity/assets` | −0.256 | +0.115 | [+0.071, +0.160] | 0.47 |
| `RnD/assets` | +0.251 | −0.168 | [−0.211, −0.125] | 0.52 |
| `CurrentRatio` | −0.126 | −0.066 | [−0.104, −0.029] | 0.42 |

Full-sample Spearman(`rho_raw`, matched excess) over the 14 signals = **+0.525** (p = 0.0537).

**How to read this table.** `rho_raw` ranks *as-traded composition sensitivity* — which signals a
size-aware release most affects — not irreducible leakage. Profitability ratios dominate it
(`OpProfit/assets` −0.310, `CFO/assets` −0.297, `ROA` −0.296, `NetMargin` −0.258,
`Equity/assets` −0.256, `Accruals` −0.222) because they are the ratios most correlated with size.
Partialling size out shrinks every one of them, in most cases to near zero. It does not shrink all
of them below the threshold.

### 4.3 Per-signal summary under the graded protocol (frozen)

This is the table the verdict rests on. `*` marks a signal flagged in at least one cycle.

| signal | mean ρ̂ | max \|ρ̂\| | cycles flagged / screened | mean φ_req | verdict |
|---|---|---|---|---|---|
| `ROA` | +0.0701 | 0.0935 | **0 / 6** | 0.42 | benign |
| `NetMargin` | +0.0366 | 0.0571 | **0 / 6** | 0.39 | benign |
| `AssetGrowth` | +0.0811 | 0.0981 | **0 / 6** | 0.43 | benign |
| `SalesGrowth` | +0.0598 | 0.0777 | **0 / 6** | 0.41 | benign |
| `Inventory/assets` | +0.0442 | 0.0715 | **0 / 6** | 0.40 | benign |
| `PPE/assets` | −0.0557 | 0.0774 | **0 / 6** | 0.41 | benign |
| `CurrentRatio` | −0.0539 | 0.0770 | **0 / 6** | 0.40 | benign |
| `Leverage`\* | −0.0707 | 0.1251 | **2 / 6** | 0.42 | susceptible |
| `CFO/assets`\* | +0.0964 | 0.1568 | **3 / 6** | 0.45 | susceptible |
| `Equity/assets`\* | +0.0936 | 0.1572 | **3 / 6** | 0.44 | susceptible |
| `GrossProfit/assets`\* | −0.1075 | 0.1237 | **4 / 6** | 0.46 | susceptible |
| `Accruals`\* | +0.1074 | 0.1420 | **4 / 6** | 0.46 | susceptible |
| `OpProfit/assets`\* | +0.1443 | 0.1593 | **6 / 6** | 0.49 | susceptible |
| `RnD/assets`\* | −0.1613 | 0.2018 | **6 / 6** | 0.51 | susceptible |

**Totals: 28 of 84 signal-cycles flagged; 7 of 14 signals clean.**

### 4.4 Per-cycle detail — `ROA`

`ρ̂ (frozen)` is the estimate the gate used, fitted on the five prior fiscal years. `ρ̂ (ex post)`
is the same-year value, shown for reporting only; it never entered a decision.

| cycle | n | ρ̂ (frozen) | flagged | φ_req | ρ̂ (ex post) |
|---|---|---|---|---|---|
| 2020 | 500 | +0.0935 | no | 0.44 | +0.0087 |
| 2021 | 479 | +0.0831 | no | 0.43 | +0.0650 |
| 2022 | 460 | +0.0745 | no | 0.42 | +0.0706 |
| 2023 | 415 | +0.0522 | no | 0.40 | +0.1366 |
| 2024 | 374 | +0.0520 | no | 0.40 | +0.0652 |
| 2025 | 341 | +0.0654 | no | 0.42 | +0.2319 |

**The frozen-vs-ex-post spread is larger here than on OSAP, and in the honest direction.** Two
`ROA` ex-post cycles (2023 +0.1366, 2025 +0.2319) exceed the threshold that the frozen estimate
never crosses. Pooling five years is what keeps the frozen figure stable; a single-year estimator
would have flagged `ROA` twice. This is dispersion, not a finding — but it is why the screen pools,
and it is a caution against reading any single ex-post cycle as a verdict.

### 4.5 Per-year raw susceptibility — `ROA`

Negative in every year of coverage, which is what makes the raw figure look like a finding until
size is partialled out.

| year | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rho_raw | −0.285 | −0.213 | −0.289 | −0.229 | −0.212 | −0.316 | −0.287 | −0.367 | −0.356 | −0.299 | −0.340 | −0.349 | −0.349 | −0.307 | −0.337 |

### 4.6 Out-of-sample structure

Estimating on 2011–2017 and testing on 2018–2025, across the 14 signals:

| relationship | Spearman | p |
|---|---|---|
| train `rho_raw` → test `rho_raw` | **+0.947** | 0.0000 |
| train `rho_raw` → test matched excess | +0.200 | 0.4930 |

The first is high because the US size/filing structure is a stable firm characteristic — it says the
composition channel persists, not that an irreducible-leakage screen reproduces. The second, the
economically meaningful test, is insignificant. **Neither result should be read as validating the
screen out of sample**; they bound what the as-traded map can be used for.

## 5. Conclusion and limitations

**What was found.** On observed filing timestamps, the visible distortion of profitability signals
is an observable size channel that conditioning removes: `ROA` goes from a raw −0.296 to a
conditional +0.097 and is flagged in 0 of 6 graded cycles, with the matched control reading
−0.71 pp [−6.56, +2.63]. But the panel as a whole is not uniformly clean. Under the same graded
protocol, 28 of 84 signal-cycles are flagged and 7 of 14 signals are flagged at least once, two of
them (`OpProfit/assets`, `RnD/assets`) in every cycle.

**Why — the construction, or rather its absence.** The OSAP entry in this registry is benign
*because* the dataset applies a conventional uniform annual lag before publishing, which closes the
arrival-selection channel before any user can be exposed to it. An as-filed EDGAR panel has no such
lag: it carries real filing dates, which is the whole point of using it, and therefore carries real
arrival staggering. **The protection that makes a published dataset benign is a property of its
publication calendar, and it is gone the moment you rebuild from as-filed sources.** That is the
single most useful sentence in this report, and this panel is the measurement behind it.

**What this does not license.**

- It does not license the claim that as-filed US data is unsafe. Seven of fourteen signals are
  clean under the graded protocol, and the flagged ones are flagged at ρ̂ of 0.10–0.20, not 0.5.
  The graded gate's answer to them is a required completeness of 0.42–0.51, not a deadline wait.
- It does not extend to signals outside the 14 tested, nor to quarterly cycles, nor to markets with
  more dispersed reporting calendars than the US.
- It is not an assessment of SEC EDGAR, of XBRL data quality, or of any vendor's product. EDGAR is
  the *source of truth* for filing dates here, not the subject of a finding.
- It says nothing about whether any of this costs money in a live strategy — see below.

**Limitations, honestly.**

- **Survivorship.** The panel is assembled from firms present in the 2015 reporting set, so it
  tilts toward larger, longer-lived names — exactly the size dimension the signals load on. This
  is the most serious limitation in the report.
- **The economic question is unresolved, and was not resolvable here.** Free price histories exist
  only for surviving firms (about 236 names). On that universe the completeness-only long-short on
  `ROA` has ΔSharpe(naive − complete) = +0.11, 95% CI [−0.21, +0.27] — an interval including zero
  — and *both* arms have net-negative absolute Sharpe (−0.72 and −0.82), so the difference is
  between two losing strategies. Survivorship selects on the very size–profitability dimension the
  signal trades. This test is uninformative and is reported only so nobody re-runs it expecting
  more.
- **The conditioner is contemporaneous size**, not a strictly pre-period observable (§2).
- **Ex post ≠ frozen.** The per-signal map in §4.2 is a measurement; only §4.3 grades. Readers
  comparing this entry to OSAP should compare frozen to frozen.
- **Group minimum of 20 firms** drops thin industries entirely; `RnD/assets` and
  `Inventory/assets` rest on the fewest groups (48 and 42) and their estimates are correspondingly
  noisier.

**Suggestion for the target.** None applies — EDGAR already publishes the filing dates that make
this measurable, which is why this panel could be screened at all. If anything, this entry is an
argument for other datasets to ship the same thing: an arrival column costs the publisher almost
nothing and turns every downstream question here from reconstruction into measurement.

## 6. Reproduce

Every number above comes out of these commands. The data is free: SEC XBRL has no licence and no
account.

Everything needed is in this directory, including the panel itself. Run from here:

```bash
pip install numpy pandas scipy pyarrow

python verify_size_path.py    # §4.1 decomposition: -0.688, +0.508, -0.296, -0.349
python edgar_lever1b.py       # ROA raw vs size-partialled, bootstrap CIs, per-year series
python edgar_lever1.py        # ROA matched vs size-only control, bootstrap CIs
python edgar_lever23.py       # §4.2 14-signal map + §4.6 out-of-sample structure
python edgar_ci.py            # §4.2 per-signal bootstrap CIs
python edgar_control.py       # §3 positive control + the signal-cycle count
python edgar_frozen.py        # §4.3 and §4.4 graded protocol, frozen estimates
```

To rebuild the panel from scratch instead of using the copy shipped here — for a later vintage,
or simply to check that it is what it claims to be:

```bash
# edit the User-Agent first: the SEC asks every caller to identify themselves
python edgar_build.py         # ~900 firms sampled from the CY2015Q4 Assets frame, seed 11
```

- **Runtime:** the screens run in seconds to a few minutes each on the shipped panel;
  `edgar_lever1.py` is the slowest (1,000 cluster-bootstrap draws). `edgar_build.py` is the only
  slow step, and it is optional — it crawls `data.sec.gov` at a deliberately polite rate.
- **Requires a licence or account:** **no.** Free SEC XBRL and submissions endpoints only — no
  WRDS, no Compustat, no vendor feed, no key.
- **Determinism:** every bootstrap and the positive control are seeded (`20260601`) and reproduce
  exactly on the shipped panel. A freshly built panel will differ slightly at the recent edge as
  filings accumulate.
- **Artifacts in this directory:** [`edgar_panel.parquet`](edgar_panel.parquet) — the exact panel
  every number above was computed on (8,657 firm-years; free SEC data only);
  [`edgar_build.py`](edgar_build.py), [`edgar_lever1.py`](edgar_lever1.py),
  [`edgar_lever1b.py`](edgar_lever1b.py), [`edgar_lever23.py`](edgar_lever23.py) — the scripts
  behind the method preprint, copied here with the panel path pointed at this directory;
  [`verify_size_path.py`](verify_size_path.py), [`edgar_ci.py`](edgar_ci.py),
  [`edgar_control.py`](edgar_control.py), [`edgar_frozen.py`](edgar_frozen.py) — written for this
  report.

---

**The rest of this ecosystem**

| | |
|---|---|
| Tool | [`pit-release-gate`](https://github.com/MaxWellApexLab/pit-release-gate) — MIT, pip-installable; the reference implementation of the screen and the graded gate |
| Registry | [`pit-audit-registry`](https://github.com/MaxWellApexLab/pit-audit-registry) — the registry this page belongs to; every *entry* is a measurement with a command attached |
| Pledge | [`pit-hygiene`](https://github.com/MaxWellApexLab/pit-hygiene) — five self-declared commitments for your own pipeline; no outside body involved |
| Papers | [doi:10.6084/m9.figshare.32952482](https://doi.org/10.6084/m9.figshare.32952482) (engine) · [doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) (screen) · [doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615) (release control) — all preprints |

*Report: CC BY 4.0. Screening code: MIT.*
