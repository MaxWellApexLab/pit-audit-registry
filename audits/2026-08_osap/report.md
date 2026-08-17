# Incomplete-cross-section leakage screen — Open Source Asset Pricing (OSAP)

| | |
|---|---|
| **Target** | [Open Source Asset Pricing](https://github.com/OpenSourceAP/CrossSection) (Chen & Zimmermann), accessed through [`open-asset-pricing-download`](https://pypi.org/project/openassetpricing/) |
| **Signals screened** | `Accruals`, `AssetGrowth`, `BM` (three accounting predictors) |
| **Version / vintage** | Panel retrieved live via `OpenAP.dl_signal`; 1,340,368 rows, 12,493 permnos, stamps `200401`–`202610` |
| **Screened on** | 2026-08 |
| **Screened by** | Kuan-Ta Wu, Max Well Apex LLC |
| **Screen version** | `pit-release-gate` 0.1.0 (notebook falls back to an inline copy of the same estimator if the package is absent; both paths produce identical numbers) |
| **Verdict** | **`benign (by construction)`** |

**Finding.** On the OSAP panel *as shipped*, all three predictors screen benign: the frozen
susceptibility estimate |ρ̂| stayed at or below **0.036** in every one of 18 predictor-cycles,
an order of magnitude under the 0.10 flagging threshold, so the graded gate asked for barely
more than its floor (mean φ_req 0.36–0.37) and never bound. **This is a property of OSAP's
update calendar, not a null result.** OSAP applies the conventional uniform annual lag before
publishing an annual accounting predictor, so the cross-section is already ~88% complete the
month a value first appears — the arrival-selection channel is closed before a user can be
exposed to it. **The protection does not travel:** a user who rebuilds these predictors from
as-filed / point-in-time Compustat replaces the uniform lag with real filing dates, and ρ̂ has
to be re-estimated on the rebuilt panel.

---

## 1. Data context

**The cross-section.** One annual cycle of one predictor: all firms carrying a value for that
predictor in that year. OSAP ships a *carry-forward* firm-month panel — a firm's value is
repeated every month until its next annual refresh.

**Where arrival times come from.** OSAP does not ship arrival timestamps, so they were
reconstructed from the panel itself: a firm's **arrival month** in a cycle is the first month
whose value differs from the value it carried out of the previous December. Firms that never
change are assigned the deadline month (12).

**How good that reconstruction is — stated as a bound.** This is *availability* staggering,
not *filing* staggering. OSAP has already applied a uniform annual lag, so most firms refresh
in the same month and the residual spread comes from off-calendar fiscal year ends. Measured
staggering is therefore a **lower bound** on true as-filed staggering. Assigning
never-changing firms to month 12 is conservative in the same direction: it pushes measured
completeness down, never up.

**Scale actually screened.**

| predictor | firm-cycles | cycles available | usable cycles (≥200 firms) | median n per cycle |
|---|---|---|---|---|
| `Accruals` | 86,907 | 2005–2025 | 21 | 4,043 |
| `AssetGrowth` | 87,017 | 2005–2025 | 21 | 4,044 |
| `BM` | 55,402 | 2005–2024 | 20 | 2,698 |

Six evaluation cycles per predictor were graded (18 predictor-cycles total), each with ρ̂ fitted
on the 5 completed cycles before it.

**Measured completeness by calendar month** (mean over cycles 2020–2025) — this table is the
whole mechanism:

| month | `Accruals` | `AssetGrowth` | `BM` |
|---|---|---|---|
| 3 | 6.0% | 6.0% | 8.7% |
| 5 | 7.4% | 7.4% | 10.0% |
| **6** | **88.2%** | **88.2%** | **87.0%** |
| 9 | 94.9% | 94.9% | 93.8% |
| 12 | 100.0% | 100.0% | 100.0% |

The cross-section is **not** complete through the first half of the cycle; it steps from ~7%
to ~88% in June.

## 2. Method

> ρ̂ = partial correlation between arrival latency and the complete-cross-section residual,
> conditional on an observable known before the cycle opens — fitted on prior *completed*
> cycles, frozen, then applied to the cycle being graded.

| parameter | value |
|---|---|
| Conditioner | the predictor's **prior-cycle closing value**, standardised — known to everyone before the cycle opens, so conditioning on it is legitimate |
| Flagging threshold | \|ρ̂\| > 0.10 |
| Trailing window K | 5 completed cycles |
| Evaluation cycles | 6 most recent per predictor |
| Minimum entities | 200 per cycle |
| Completeness floor φ_min | 0.35 |
| Graded rule | φ_req = min(1, φ_min + κ·\|ρ̂\|), κ = 1.0 |

Nothing from a cycle enters its own gate: ρ̂ for cycle *Y* is fitted on cycles *Y−5 … Y−1*,
whose complete-cross-section residuals legitimately exist ex post, and then frozen.

**Method references:**
[doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) defines ρ̂ and
the matched-placebo design;
[doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615) defines the
release controller.

## 3. Positive control

The identical screen, run on planted-truth cross-sections where the selection strength is a
knob (`c_a` = selection on the disturbance, the true leakage knob; `c_x` = selection on the
observable, the benign kind):

| planted case | ρ̂ | φ_req | screen says | should say | correct |
|---|---|---|---|---|---|
| clean (c_a=0.0, c_x=0.3) | −0.011 | 0.36 | benign | benign | ✅ |
| composition (c_a=0.0, c_x=2.0) | −0.015 | 0.37 | benign | benign | ✅ |
| mild leak (c_a=0.3, c_x=0.7) | −0.461 | 0.81 | susceptible | susceptible | ✅ |
| strong leak (c_a=1.0, c_x=0.7) | −0.862 | 1.00 | susceptible | susceptible | ✅ |

**Control result: 4/4 correct.**

The `composition` row is the one that matters. Its selection is more than six times stronger
than `clean`'s, but it acts entirely through an **observable**, so the screen correctly calls
it benign and imposes no timeliness penalty — where a raw completeness threshold would have
withheld it. That discrimination is what distinguishes this screen from "wait until the
cross-section is X% full".

The graded gate on the same planted data, showing the timeliness–bias dial (released at
completeness):

| planted case | κ=0.5 | κ=1.0 | κ=2.0 |
|---|---|---|---|
| clean | 40% | 40% | 40% |
| composition | 40% | 40% | 45% |
| mild leak | 60% | 85% | 100% |
| strong leak | 80% | 100% | 100% |

Benign rows sit at the floor for every κ; susceptible rows climb toward the deadline. Only
susceptible signals pay for their own risk.

## 4. Results

**Per-signal summary** (threshold |ρ̂| > 0.10)

| predictor | mean ρ̂ | max \|ρ̂\| | cycles flagged / screened | mean φ_req | mean release month | verdict |
|---|---|---|---|---|---|---|
| `Accruals` | −0.0096 | 0.0184 | **0 / 6** | 0.36 | 6.0 | benign |
| `AssetGrowth` | −0.0062 | 0.0192 | **0 / 6** | 0.36 | 6.0 | benign |
| `BM` | +0.0203 | 0.0357 | **0 / 6** | 0.37 | 6.0 | benign |

**Per-cycle detail.** `ρ̂ (frozen)` is the estimate the gate actually used, fitted on the five
prior cycles. `ρ̂ (ex post)` is the same-cycle value, shown for reporting only — it never
entered a decision.

### `Accruals`

| cycle | n | ρ̂ (frozen) | flagged | φ_req | release month | completeness at release | ρ̂ (ex post) |
|---|---|---|---|---|---|---|---|
| 2020 | 3,881 | −0.0184 | no | 0.37 | 6 | 87.2% | −0.0415 |
| 2021 | 3,928 | −0.0165 | no | 0.37 | 6 | 87.6% | −0.0003 |
| 2022 | 4,013 | −0.0106 | no | 0.36 | 6 | 87.7% | +0.0480 |
| 2023 | 4,043 | +0.0010 | no | 0.35 | 6 | 87.7% | −0.0320 |
| 2024 | 4,127 | −0.0065 | no | 0.36 | 6 | 87.4% | −0.0052 |
| 2025 | 4,239 | −0.0062 | no | 0.36 | 6 | 91.9% | +0.0069 |

### `AssetGrowth`

| cycle | n | ρ̂ (frozen) | flagged | φ_req | release month | completeness at release | ρ̂ (ex post) |
|---|---|---|---|---|---|---|---|
| 2020 | 3,883 | −0.0192 | no | 0.37 | 6 | 87.2% | +0.0584 |
| 2021 | 3,930 | −0.0015 | no | 0.35 | 6 | 87.6% | +0.0162 |
| 2022 | 4,015 | +0.0069 | no | 0.36 | 6 | 87.7% | −0.0643 |
| 2023 | 4,044 | −0.0080 | no | 0.36 | 6 | 87.7% | −0.0379 |
| 2024 | 4,129 | −0.0099 | no | 0.36 | 6 | 87.4% | +0.0010 |
| 2025 | 4,240 | −0.0053 | no | 0.36 | 6 | 91.9% | +0.0054 |

### `BM`

| cycle | n | ρ̂ (frozen) | flagged | φ_req | release month | completeness at release | ρ̂ (ex post) |
|---|---|---|---|---|---|---|---|
| 2019 | 2,333 | +0.0255 | no | 0.38 | 6 | 86.3% | +0.0049 |
| 2020 | 2,341 | +0.0193 | no | 0.37 | 6 | 86.8% | +0.0938 |
| 2021 | 2,394 | +0.0357 | no | 0.39 | 6 | 86.6% | −0.1125 |
| 2022 | 2,453 | +0.0083 | no | 0.36 | 6 | 87.1% | +0.1143 |
| 2023 | 2,492 | +0.0281 | no | 0.38 | 6 | 87.1% | −0.0761 |
| 2024 | 2,693 | +0.0049 | no | 0.35 | 6 | 87.4% | −0.0069 |

**Gated release month on the real cycles, across the κ dial** (12 = wait for the deadline):

| predictor | κ=0.5 | κ=1.0 | κ=2.0 |
|---|---|---|---|
| `Accruals` | 6.0 | 6.0 | 6.0 |
| `AssetGrowth` | 6.0 | 6.0 | 6.0 |
| `BM` | 6.0 | 6.0 | 6.0 |

Flat across κ because ρ̂ is near zero everywhere: the gate imposes no timeliness penalty where
it cannot justify one. **Read the "month 6" carefully** — June is where OSAP's own update
calendar puts the cross-section over any threshold the gate could plausibly set. The binding
constraint is the dataset's uniform lag, not the gate.

**Note on the frozen-vs-ex-post spread.** The frozen estimates are all under 0.04, but three
individual ex-post cycle values sit near ±0.11 (`BM` 2021 −0.1125, `BM` 2022 +0.1143, `BM`
2020 +0.0938). Pooling five cycles is what keeps the frozen estimate stable; a single-cycle
estimator on `BM` would have crossed the 0.10 threshold twice. This is dispersion, not a
finding — but it is the reason the screen pools, and anyone re-running with K=1 should expect
noisier verdicts.

## 5. Conclusion and limitations

**What was found.** All three predictors are benign on the OSAP panel as shipped: 0 of 18
predictor-cycles flagged, max |ρ̂| = 0.036 against a 0.10 threshold, mean φ_req 0.36–0.37 —
barely above the 0.35 floor. The gate never bound.

**Why — the construction that produces this.** OSAP applies the conventional uniform annual
lag before publishing an annual accounting predictor. By the time a value appears, ~88% of the
cross-section has appeared with it, so arrival ordering carries almost no information about
the disturbance. A uniform lag is a blunt instrument — it costs timeliness on every predictor,
benign or not, which is exactly the blanket penalty a graded gate exists to avoid — but it
does close the channel this screen measures. **That is a compliment to the dataset, not a
finding against it.**

**What this does not license.**

- It does not license the conclusion that *these predictors* are immune. The immunity belongs
  to OSAP's publication calendar, and it is gone the moment a user rebuilds a predictor from
  as-filed / point-in-time Compustat with real filing dates — which is precisely what you do
  if you care about tradeability. ρ̂ must be re-estimated on the rebuilt panel.
- It does not extend to markets whose reporting calendars are more dispersed than the US one.
- It says nothing about any other OSAP predictor, or about any non-accounting predictor.
- It is not an assessment of OSAP's data quality, replication fidelity, or usefulness.

**Limitations, honestly.**

- **Three predictors, annual cycles, one arrival proxy.** This is a screen, not a survey of
  the OSAP predictor set.
- **The conditioner is the predictor's own prior-cycle value.** Market cap would be the
  natural choice, but OSAP's `Size` requires WRDS and this screen stays free-data-only. A
  reader with WRDS should swap it in and re-run.
- **Arrival times are reconstructed, not observed** — availability staggering, a lower bound
  on filing staggering (see §1).
- **Firms with genuinely unchanged values are assigned the deadline month.** Conservative: it
  pushes measured completeness down, never up.
- **Panel stamps run to `202610`**, beyond the screening date, because OSAP carries values
  forward past the last refresh. Cycles are only screened when all 12 months are present, so
  incomplete recent cycles drop out — visible in `BM` ending at 2024 while the other two reach
  2025. No forward-looking data enters any estimate.

**Cross-check against an independent replication audit.** Separately graded for how far each
predictor can be rebuilt outside CRSP/Compustat:

| predictor | category | replication grade | susceptibility |
|---|---|---|---|
| `Accruals` | Accounting | low approximation | benign |
| `AssetGrowth` | Accounting | close approximation | benign |
| `BM` | Accounting | close approximation | benign |

The two audits answer different questions — *can this be rebuilt at all* versus *if you rebuild
it from as-filed data, does early release bias it* — and a predictor can be trivially
replicable and highly susceptible, or the reverse. `Accruals` is the interesting cell: it
grades only a *low* approximation outside Compustat, which means users rebuild it with
substitutions, and rebuilt versions are exactly the ones that no longer inherit OSAP's uniform
update calendar.

**Suggestion for the target.** The single change that would let users check this themselves is
an optional per-observation **arrival column** — the date the underlying filing became
available, alongside the `yyyymm` the value is stamped with. Everything reconstructed in §1
would become unnecessary, and it would let users distinguish "this value is stamped 2020-06"
from "this value was knowable on 2020-06". We would be glad to help specify or implement it.

## 6. Reproduce

```bash
pip install openassetpricing numpy pandas scipy matplotlib pit-release-gate
jupyter lab osap_predictor_completeness_screen.ipynb   # then: Run All
```

- **Runtime:** ~2 minutes, of which ~25 s is the OSAP download.
- **Requires a licence or account:** **no.** Free public OSAP release only; no WRDS, no
  proprietary inputs.
- **Determinism:** the positive control is seeded (`20260601`) and reproduces exactly. The
  OSAP figures track the live panel, so a later run will show the same mechanism with cycles
  extended.
- **Artifacts in this directory:** [`osap_predictor_completeness_screen.ipynb`](osap_predictor_completeness_screen.ipynb)
  — the full run, with outputs, that every number above was taken from.

---

*Report: CC BY 4.0. Screening code: MIT.*
