# Incomplete-cross-section leakage screen — as-of join semantics in feature stores

| | |
|---|---|
| **Target** | **As-of (point-in-time) join semantics in feature stores** — the mechanism, not any one project. Worked example: [Feast](https://github.com/feast-dev/feast), via a twelve-line stand-in for `store.get_historical_features(...)` |
| **Page kind** | **Mechanism audit.** Not a registry entry — no scoreboard row, no badge, no table row. Its job is to answer "why does this screen need to exist?" |
| **Version / vintage** | Not applicable: no project version is under test. Synthetic panel, seed `20260601` |
| **Screened on** | 2026-08 |
| **Screened by** | Kuan-Ta Wu, Max Well Apex LLC |
| **Screen version** | Inline implementation (numpy / pandas / scipy, a few dozen lines), see §6 |
| **Verdict** | **`susceptible (by construction)`** |

**Finding.** An as-of join guarantees one thing, exactly, and guarantees it correctly: **this
value was not read early.** It does not guarantee the second thing that cross-sectional feature
engineering silently assumes — **the cross-section behind this derived value was complete.** On
synthetic data with planted ground truth, a point-in-time-correct join over staggered arrivals
returned a value for **9,631 of 24,000** requested entity rows (cross-section completeness at
the cutoff: mean **40.1%**, min 40.0%, max 40.2%). The standard "residualise against a known
driver" recipe, run on exactly those rows, reports a rank IC of **0.4052** against a
complete-cross-section truth of **0.4074** — a rounding error apart, which is the comparison a
reviewer would make and pass. Hold the evaluation sample fixed and change only the recipe, and
the same rows deliver **0.3662**: the offline report is inflated by **+0.0390 rank IC
(+10.7%)**, and the fitted coefficient on the conditioning variable comes out **0.336** where
the planted truth is **0.600**. **This is a property of as-of join semantics in general — not a
defect in Feast.** Every feature store's as-of join has these semantics; Feast's does exactly
what it says it does, and there is nothing in it to repair. What is missing is a documented
boundary: point-in-time correctness is *per row*, not *per cross-section*. **This page runs on
synthetic data with planted ground truth, and therefore licenses no claim whatsoever about
anyone's production pipeline** — only a claim about what the mechanism can and cannot promise.

*Registry note: by design this page does not go on the scoreboard, does not receive a badge,
and does not occupy a row in the registry table. It grades a mechanism, not a project, so there
is no project to grade.*

---

## 1. Data context

**The cross-section.** A payments platform with **400 merchants**. Every week each merchant's
settlement file lands and reports a `chargeback_rate`; one week's settlement files are one
cross-section. The panel is **60 weekly periods**, **24,000 rows**, generated from seed
`20260601`.

**Where arrival times come from.** They are *planted*, not reconstructed. That is the entire
reason to use synthetic data here: on a real target the arrival timestamps are the hard part,
and on this one they are a knob. A merchant settles earlier when `C_DISTURBANCE · z(shock) +
C_VOLUME · z(log_volume)` is large, plus noise, with

| knob | value | meaning |
|---|---|---|
| `C_DISTURBANCE` | **0.3** | arrival order depends on the merchant's **unobserved** chargeback shock |
| `C_VOLUME` | **0.7** | arrival order depends on **observed** volume (big merchants settle first) |

Arrivals are spread across the week that follows the period close; measured latency runs p10 =
0.10, p50 = 0.50, p90 = 0.90 of the window.

**The planted truth.** `chargeback_rate = 0.6 · log_volume + shock`, so the **true coefficient
on `log_volume` is 0.600**. `log_volume` is on the payments stream and is known for everyone at
every moment; `chargeback_rate` is knowable only from its own arrival timestamp onward. The
label, `loss_next_week`, is driven by both the shock and volume.

**The join.** Entity rows are stamped **`CUTOFF_FRAC = 0.40`** of the way through the arrival
window — scoring every merchant partway through settlement is exactly the timeliness the
operator is buying. The source is registered the Feast-idiomatic way: `event_timestamp` is
**when the value became knowable**, not the period it describes. The `TTL` reaches back only to
the start of the current period, so a merchant that has not settled gets *no* value rather than
last period's stale one. (Widen the TTL and the join returns the stale row instead — still
point-in-time correct, and everything below applies either way; the missing-value version is
simply easier to see.)

**What the join returns.**

```
entity rows requested    : 24,000
rows with a feature value: 9,631
cross-section completeness at the cutoff: mean 40.1%, min 40.0%, max 40.2%
```

`merge_asof(direction="backward")` structurally cannot select a row stamped after the entity
timestamp, and because each row carries its own arrival time, "before the entity timestamp"
means "had actually landed". **There is no look-ahead here. There is nothing to fix in the
join.** And yet only ~40% of each week's cross-section is present when the derived feature is
computed.

## 2. Method

Three things are measured, in order: the size of the error, the statistic that predicts it, and
the policy that contains it.

**The error.** A cross-sectional feature is built the ordinary way — residualise
`chargeback_rate` on `log_volume` **within each period** — and evaluated by mean per-period
Spearman rank IC against `loss_next_week`. Three numbers, not one, because the naive comparison
hides the problem:

1. **the offline report** — the early-join rows, with the recipe fitted on those same early
   rows;
2. **the truth** — the complete cross-section, everyone settled;
3. **a same-sample control** — the *complete-data* recipe scored on *exactly the same early
   rows* as (1), so the evaluation sample is held fixed and only the recipe differs.

(1) against (2) is the comparison that gets made in review. (1) against (3) is the one that
isolates the leakage.

**The screen.** One statistic, estimated honestly:

> ρ̂ = partial correlation between arrival latency and the complete-cross-section residual,
> conditional on an observable known before the period opens — fitted on prior *completed*
> periods, frozen, then applied to the period being graded.

| parameter | value |
|---|---|
| Conditioner | `log_volume`, observed for everyone regardless of arrival — legitimate because it is knowable before the period opens |
| Flagging threshold | \|ρ̂\| > **0.10** |
| Trailing window K | **8** completed periods (weeks 0–7), then frozen |
| Periods available | 60 weekly cross-sections, 400 entities each |

Conditioning on the observable is what separates the two kinds of incompleteness. **Benign:**
big merchants settle first, so the arrived sample is unrepresentative on an *observable* —
composition shifts, but an estimator that already controls for that observable is not biased,
and ρ̂ sits near zero. **Malignant:** merchants with an unusual shock settle late, so the
arrived sample is unrepresentative on the *estimand itself* — no reweighting on observables
repairs it, only more of the cross-section does, and ρ̂ is large. The contract to respect is
that ρ̂ needs the complete-cross-section residual, which by definition does not exist yet for
the period being gated, so it is never estimated on that period.

**The gate.** φ_req = min(1, φ_min + κ·\|ρ̂\|), with **φ_min = 0.35** and **κ = 1.0**. A benign
feature releases at the floor; a susceptible one waits until enough of its cross-section has
arrived to suppress the bias. κ is the timeliness-versus-bias dial.

**Method references** (preprints):
[doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) defines ρ̂ and
the matched-placebo design;
[doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615) defines the
release controller;
[doi:10.6084/m9.figshare.32952482](https://doi.org/10.6084/m9.figshare.32952482) defines the
correct-by-construction point-in-time engine the other two sit on top of.

## 3. Positive control

Before trusting a screen that says "susceptible", check that it says "benign" when it should —
including the case built to fool it: arrival driven **hard** by an observable.

| arrival driven by | `c_disturbance` | `c_volume` | ρ̂ | screen says | should say | correct |
|---|---|---|---|---|---|---|
| nothing in particular | 0.0 | 0.7 | −0.003 | benign | benign | ✅ |
| **OBSERVED volume, hard** | 0.0 | 2.0 | −0.001 | benign | benign | ✅ |
| the shock (this page's source) | 0.3 | 0.7 | −0.496 | SUSCEPTIBLE | susceptible | ✅ |
| the shock, hard | 1.0 | 0.7 | −0.872 | SUSCEPTIBLE | susceptible | ✅ |

**Control result: 4/4 correct.**

**Row 2 is the discriminating case.** Its arrival is selected on volume almost three times as
hard as this page's own source — a violent composition shift — but it is selected *entirely* on
`log_volume`, which the recipe already controls for. The screen calls it benign and is right
to: withholding that feature would cost timeliness and buy nothing. A plain completeness
threshold cannot tell row 2 from row 3. That discrimination is the whole reason to measure ρ̂
rather than count arrivals.

## 4. Results

**The three numbers.** Same panel, same feature, three ways of evaluating it:

| | rank IC | beta on `log_volume` |
|---|---|---|
| 1. offline report (early rows, early recipe) | **0.4052** | **0.336** |
| 2. complete cross-section (the truth) | 0.4074 | 0.602 |
| 3. early rows, complete-data recipe | 0.3662 | 0.602 |

```
inflation vs the truth             : -0.0022 (-0.5%)
inflation holding the sample fixed : +0.0390 (+10.7%)   <-- this part is the leakage
true beta on log_volume is 0.600; the early join fits 0.336
```

Comparing (1) to (2), everything looks fine — 0.4052 against 0.4074, and the feature ships.
Comparing (1) to (3) — same rows, honest recipe — the feature is **10.7% weaker** than the
report claims, inflated by **+0.0390** of rank IC it does not have.

**The mechanism is in the last column.** The true coefficient is `0.600`. Fitted on the
complete cross-section, the recipe recovers `0.602`. Fitted on the merchants who settled early,
it recovers **`0.336`** — because arrival order depends on *both* volume and the shock,
selecting on early arrival induces a correlation between them, and the regression that is
supposed to project volume out projects out barely half of it. The "volume-neutral" feature
still carries a large volume exposure; volume also predicts the label; that exposure shows up
as free predictive power in the backtest, and it evaporates the moment the cross-section fills
in.

**The two errors nearly cancel in the naive comparison** — the early sample is intrinsically a
little harder, the biased recipe a little flattered — which is precisely why this survives
review. A feature whose offline IC matches its complete-data IC looks validated. It is not.

**The screen, on this panel:**

```
rho_hat (frozen, fitted on weeks 0-7) : -0.505
threshold                              : 0.10
verdict                                : SUSCEPTIBLE
```

**The gate, at five cutoffs.** ρ̂ = −0.505 → **φ_req = 86%**.

| cutoff | completeness | gate | rank IC if released | leakage (same-sample IC gap) | beta on `log_volume` |
|---|---|---|---|---|---|
| 40% | 40% | **WITHHOLD** | 0.4052 | +0.0390 | 0.336 |
| 60% | 60% | **WITHHOLD** | 0.4020 | +0.0374 | 0.389 |
| 80% | 80% | **WITHHOLD** | 0.4038 | +0.0283 | 0.467 |
| 90% | 90% | RELEASE | 0.4066 | +0.0199 | 0.515 |
| 100% | 100% | RELEASE | 0.4074 | +0.0000 | 0.602 |

complete-cross-section rank IC (what the gate is aiming at): 0.4074 · true beta on
`log_volume`: 0.600

The leakage column falls monotonically as the cross-section fills and reaches exactly zero when
it is complete; the fitted coefficient walks back to `0.600` alongside it. The gate withholds
at 40%, 60% and 80%, and **releases at 90% — before the deadline** — with the leakage cut from
`+0.0390` to `+0.0199`.

**Only the features that earn it pay.**

| feature | ρ̂ | required completeness | timeliness cost |
|---|---|---|---|
| a benign feature | −0.003 | 35% | none — releases at the floor |
| `chargeback_rate` (this page) | −0.505 | 86% | partial |
| a badly selected feature | −0.872 | 100% | full — waits for the deadline |

A blanket "always wait for the deadline" rule puts every row on the bottom line. The graded
gate charges the timeliness cost only where it can justify one.

## 5. Conclusion and limitations

**What was found.** On a panel with planted ground truth, a point-in-time-correct as-of join
returned 9,631 of 24,000 requested rows at ~40.1% cross-section completeness, and the
cross-sectional feature built on top of it reported a rank IC of 0.4052 — indistinguishable
from the complete-data 0.4074 — while actually delivering 0.3662 on the same rows. **+0.0390
rank IC (+10.7%) of the reported performance was an artifact of the incomplete cross-section**,
visible in the fitted coefficient of 0.336 against a true 0.600. The frozen screen returned ρ̂
= −0.505 against a 0.10 threshold, and the graded gate released at 90% completeness rather than
at the deadline.

**Why — the construction that produces this.** The verdict is `susceptible (by construction)`
because susceptibility here is a property of the *mechanism*, not a measurement of some
project's data. An as-of join is defined per row: for this entity, at this timestamp, what was
the latest value that had already arrived? That is a complete answer to a per-row question. A
rank, a z-score, a percentile, a group-demeaned value, an industry- or cohort-relative feature,
a "residualise against a known driver" — every one of these asks a *second*, per-cross-section
question the join was never defined to answer: how does this entity compare to the rest of its
cross-section right now? Wherever rows land on staggered schedules — settlement files, claims,
quarterly filings, partner feeds, device check-ins — the set of entities present at a moment is
a *sample*, not the population. If arrival timing is related to the thing the feature measures,
that sample is **selectively** incomplete, the cross-sectional transform is systematically
wrong, and offline evaluation will not say so, because the same incomplete cross-sections are
replayed at training time.

**Feast is the worked example, not the owner of this.** Feast's as-of join is correct and does
exactly what its documentation says it does; the demonstration above contains no look-ahead and
nothing for the project to repair. The same is true of every other feature store's as-of join —
this is what "point-in-time correct" means everywhere the term is used. What this page
documents is a **boundary that the documentation does not currently spell out**, so that a
reader who has satisfied the point-in-time requirement knows which class of features still
needs a second check. That is a documentation gap, and a small one.

**What this does not license.**

- **This is synthetic data with planted ground truth.** It licenses no claim about anyone's
  production pipeline, no claim about any real dataset's completeness, and no claim about the
  magnitude of the effect anywhere outside this generator. The knobs were set to make the
  mechanism visible, not to estimate a real-world quantity.
- It is **not** a finding against Feast, against any other feature store, or against as-of
  joins. The join is correct, and the demonstration depends on it being correct.
- The +10.7% figure is not a portable estimate. Change `C_DISTURBANCE`, the cutoff, or the
  recipe and it changes. What is portable is the *structure*: the naive comparison passes while
  the same-sample comparison does not.
- Nothing here claims that every cross-sectional feature is affected. The positive control's
  first two rows exist precisely to show that many are not.

**Limitations, honestly.**

- **One generator, one feature, one recipe.** A single linear residualisation against a single
  observed conditioner. Ranks, z-scores and percentiles fail through the same channel, but they
  are not demonstrated here.
- **The conditioner is the one variable the generator makes observable.** In a real pipeline
  the choice of conditioner is a judgement call, and a poorly chosen one weakens the screen in
  the benign direction — ρ̂ falls, and the gate under-charges.
- **ρ̂ is frozen on 8 periods.** Pooling is what keeps it stable; a single-period estimator on
  real data is noticeably noisier, and anyone re-running with K = 1 should expect less stable
  verdicts.
- **The join stand-in is a `merge_asof`, not Feast itself.** It reproduces the documented as-of
  semantics in twelve lines so the page runs with no install; it is not a test of any
  particular offline store's implementation of those semantics.
- **The TTL choice is the legible one, not the only one.** A longer TTL substitutes a quietly
  stale value for an obviously missing one, which hides the incompleteness rather than removing
  it.

**Suggestion for the target.** The mechanism has no maintainer, so the suggestion is addressed
to feature-store documentation generally, and offered to Feast as a concrete draft — one
paragraph to drop at the end of a point-in-time-joins concept page:

> **Point-in-time correctness is per row, not per cross-section.** A point-in-time join
> guarantees that no individual feature value was stamped after the timestamp it is joined to.
> It does not guarantee that every entity in a cross-section has reported by that timestamp.
> When rows arrive on staggered schedules, a feature computed *across* entities — a rank, a
> z-score, a group-demeaned or residualised value — is computed on whichever entities happen to
> have arrived, and if arrival timing is related to what the feature measures, that feature is
> systematically biased even though every value in it was legitimately available. Offline
> evaluation will not surface it, because the same incomplete cross-sections are replayed at
> training time.

Three practical notes go with it, none of which need new machinery: stamp `event_timestamp`
with **arrival**, not with the period the value describes; compute ρ̂ in the batch pipeline,
where it changes at most once per period, and store it beside the feature view's metadata; and
put the gate in front of materialisation, as a scheduler-level check, so it costs nothing on
the serving path. We would be glad to help write, cut down, or re-scope any of this for
whichever project wants it.

## 6. Reproduce

The whole demonstration is a single Python session with three dependencies:

```bash
pip install numpy pandas scipy
```

- **No Feast install.** The as-of join is a twelve-line `merge_asof` stand-in for
  `store.get_historical_features(...)`, with the same documented semantics.
- **No credentials, no cloud offline store, no licensed data.** Every row is generated locally
  from `np.random.default_rng(20260601)`.
- **Runtime:** well under a minute on a laptop.
- **Determinism:** the panel is seeded (`20260601`) and the positive control is seeded (`99`);
  both reproduce exactly. Every number on this page was taken from a run of exactly the code as
  written, executed in order in one session.
- **Artifacts in this directory:** the annotated walkthrough this page is drawn from, with
  every code block and printed output in place.

---

**The rest of this ecosystem**

| | |
|---|---|
| Tool | [`pit-release-gate`](https://github.com/MaxWellApexLab/pit-release-gate) — MIT, pip-installable; the reference implementation of the screen and the graded gate |
| Registry | [`pit-audit-registry`](https://github.com/MaxWellApexLab/pit-audit-registry) — the registry this page belongs to; every *entry* is a measurement with a command attached |
| Pledge | [`pit-hygiene`](https://github.com/MaxWellApexLab/pit-hygiene) — five self-declared commitments for your own pipeline; no outside body involved |
| Papers | [doi:10.6084/m9.figshare.32952482](https://doi.org/10.6084/m9.figshare.32952482) (engine) · [doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) (screen) · [doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615) (release control) — all preprints |

*Report: CC BY 4.0. Screening code: MIT.*
