# Audit report template

Copy this file to `audits/<YYYY-MM>_<target>/report.md` and fill every section.
**A report with an empty or failing positive control is not published.**

---

# Incomplete-cross-section leakage screen — `<TARGET NAME>`

| | |
|---|---|
| **Target** | `<project / dataset name>` + link |
| **Version / vintage** | `<tag, release, or the exact data vintage screened>` |
| **Screened on** | `<YYYY-MM-DD>` |
| **Screened by** | `<name>` |
| **Screen version** | `pit-release-gate <version>` (or: inline implementation, see §Reproduce) |
| **Verdict** | `benign (by construction)` / `benign (measured)` / `susceptible (details)` |

**One-paragraph finding.** *State the result before the method. What was screened, what came
out, and the single most important caveat. A reader who stops after this paragraph should not
end up with a wrong impression.*

---

## 1. Data context

- **What the cross-section is** — the entities, the period, and what makes them one group.
- **Where arrival times come from** — the target rarely ships them, so say exactly how they
  were reconstructed and from which fields.
- **How good that reconstruction is** — is it *filing* staggering or only *availability*
  staggering? Which direction does the error go? State the bound explicitly.
- **Scale** — rows, entities, periods, and the period range actually screened.

## 2. Method

The screen is one statistic, estimated honestly:

> ρ̂ = partial correlation between arrival latency and the complete-cross-section residual,
> conditional on an observable known before the period opens — fitted on prior *completed*
> periods, frozen, then applied to the period being graded.

- **Conditioner used** and why it is legitimate (must be knowable before the period opens).
- **Threshold** — the |ρ̂| above which a signal is flagged, and where it comes from.
- **Trailing window** K, **evaluation periods**, **minimum entities per period**.
- **Method references** — [doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955)
  (screen), [doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615)
  (release controller).

## 3. Positive control

*Mandatory. Run the identical screen on planted-truth cross-sections where the selection
strength is a knob you set, and show it classifies all of them correctly. Include at least one
**benign-but-strongly-selected-on-observables** case — that is the one that distinguishes a
real screen from a completeness threshold with extra steps.*

| planted case | ρ̂ | φ_req | screen says | should say | correct |
|---|---|---|---|---|---|
| clean (c_a=0.0, c_x=0.3) | | | | benign | |
| composition (c_a=0.0, c_x=2.0) | | | | benign | |
| mild leak (c_a=0.3, c_x=0.7) | | | | susceptible | |
| strong leak (c_a=1.0, c_x=0.7) | | | | susceptible | |

**Control result: `<n>/<n>` correct.** *If this is not all-correct, stop — the screen is
miscalibrated for this data shape and the findings below mean nothing.*

## 4. Results

**Per-signal summary**

| signal | mean ρ̂ | max \|ρ̂\| | periods flagged / screened | mean φ_req | verdict |
|---|---|---|---|---|---|

**Per-period detail** — one row per (signal, period). Aggregates hide dispersion; show it.

| signal | period | n | ρ̂ (frozen) | flagged | φ_req | release point | completeness at release |
|---|---|---|---|---|---|---|---|

## 5. Conclusion and limitations

**What was found.** *The finding, restated with the numbers behind it.*

**Why.** *The mechanism. If the verdict is `benign (by construction)`, name the construction —
this is the most useful sentence in the report, because it tells a reader exactly which change
to their own pipeline would remove the protection.*

**What this does not license.** *Be specific about what the reader must NOT conclude. Scope
of the screen, of the arrival reconstruction, of the period covered.*

**Limitations, honestly.**

- *Coverage: how many signals, how many periods, one arrival proxy?*
- *The conditioner: is it the one you would have chosen with unlimited data access?*
- *Conservative choices made and which direction they bias the result.*

**Suggestion for the target.** *Optional, and only if there is a concrete, small change that
would let users check this themselves — usually an arrival/availability column. Offer help;
do not lecture.*

## 6. Reproduce

Every number above must come out of this command.

```bash
<exact commands, from a clean checkout, including how to get the data without a licence>
```

- **Runtime:** `<approx>`
- **Requires a licence or account:** `<no — or say exactly what>`
- **Artifacts in this directory:** `<notebook / script / cached inputs>`

---

*Report: CC BY 4.0. Screening code: MIT.*
