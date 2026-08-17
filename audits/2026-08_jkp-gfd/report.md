# Incomplete-cross-section leakage screen — JKP Global Factor Data

| | |
|---|---|
| **Target** | [Global Factor Data](https://jkpfactors.com/) (Jensen, Kelly, and Pedersen) — the dataset's **accounting-availability convention**, as documented |
| **What was screened** | The release convention stated in `Documentation.pdf`, not the delivered data. No Global Factor Data was accessed, downloaded, or analysed for this report. |
| **Version / vintage** | `Documentation.pdf` (55 pp.), retrieved 2026-08 from `jkpfactors-data.s3.amazonaws.com/documents/Documentation.pdf` |
| **Screened on** | 2026-08 |
| **Screened by** | Kuan-Ta Wu, Max Well Apex LLC |
| **Screen version** | inline implementation, see §6 — same estimator as `pit-release-gate` 0.1.1 |
| **Verdict** | **`benign (by construction)`** |

**Finding.** The Global Factor Data documentation states a single release convention that applies to
every accounting variable in the dataset: values are treated as available a uniform four months
after the accounting period ends. That convention **closes the arrival-selection channel this screen
measures**, and it does so structurally rather than incidentally: when every firm's value becomes
usable at the same offset from its own period end, arrival ordering no longer carries information
about *how fast a firm filed*, which is the variable that carries the disturbance. A planted-truth
control (§3) demonstrates the closure directly — the same planted leakage that the screen detects at
ρ̂ = −0.324 under as-filed release reads ρ̂ = +0.017 under the uniform four-month release. **The cost
is a uniform timeliness tax**, paid by all 406 characteristics alike, including those that would
screen benign and need no protection; this is the blanket penalty a graded gate exists to avoid, and
it is a deliberate, documented, conservative choice rather than an oversight. **The limitation that
matters most: this cannot be verified from outside.** The documentation describes no
per-observation arrival or availability field, so a reader cannot confirm the convention against
delivered data, and per-characteristic susceptibility cannot be graded. This report therefore
records and analyses a stated convention; it is not a measurement of the dataset.

---

## 1. Data context

**What the cross-section is.** For a same-period cross-sectional characteristic — an
industry-relative ratio, a within-group z-score, the residual of a cross-sectional regression — the
relevant group is the set of firms whose accounting values for that period are usable at the moment
the characteristic is computed. Whether that set is complete, and whether its incompleteness is
related to what the characteristic measures, is the entire question this registry screens.

**The convention, quoted.** From `Documentation.pdf`, §6.2 *General Information* (spelling as
printed in the source):

> "We assume that accounting variables are publically available 4 months after the end of the
> accounting period."

And, in the factor-portfolio construction section:

> "We update characteristics with the most recent accounting data (which could be either annual or
> quarterly) starting four months after the end of the fiscal period."

The same section documents how annual and quarterly inputs are combined:

> "We create characteristics for annual and quarterly accounting data separately. We then take the
> most recent characteristics value from each dataset to create the final dataset."

**Scale of the object the convention governs.** From `Documentation.pdf`:

> "The Global Factor Data includes 406 characteristics and their associated factor portfolios. This
> is a superset of the 153 factors analyzed in Jensen, Kelly, and Pedersen (2023)."

The country count is stated on the project's website rather than in the documentation:
jkpfactors.com describes the data as covering "93 countries", grouped into 13 themes. Where the
website's summary phrasing and the documentation differ, this report follows `Documentation.pdf`,
which distinguishes the **406 characteristics** in the dataset from the **153 factors** analysed in
the published paper.

**Where arrival times come from — they do not.** A text search of all 55 pages of
`Documentation.pdf` returns **no occurrence** of the terms *availability*, *arrival*, *timestamp*,
or *filing date*. The four-month figure is an assumption applied uniformly, not a per-observation
observed quantity. This is stated as a fact about the document, and it is what makes the verdict
`by construction` rather than `measured`: there is nothing in the delivered data for an outside
reader to estimate ρ̂ from.

## 2. Method

For a `by construction` verdict the screen is not run on the target's data — there is no arrival
column to run it on. Instead the claim is made precise and then tested on planted truth:

> **Claim.** Under a release rule that makes every firm's value usable at a fixed offset from its
> own period end, the partial correlation between arrival latency and the complete-cross-section
> residual, conditional on an observable, is zero regardless of how strongly filing speed depends
> on the disturbance.

| parameter | value |
|---|---|
| Estimator | ρ̂ = partial corr(arrival latency, complete-cross-section residual \| size) |
| Conditioner | a firm-level observable, standing in for size |
| Flagging threshold | \|ρ̂\| > 0.10 |
| Graded rule | φ_req = min(1, φ_min + κ·\|ρ̂\|), φ_min = 0.35, κ = 1.0 |
| Synthetic scale | 20 cross-sections × 400 firms per case |
| Uniform lag modelled | 122 days |

**Method references:**
[doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) (preprint) defines
ρ̂ and the matched-placebo design;
[doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615) (preprint) defines
the release controller.

## 3. Positive control

One underlying cross-section, released two ways, identical estimator. `c_a` is selection on the
unobserved disturbance (the true leakage knob); `c_x` is selection on the observable (the benign
kind).

| release policy | c_a | c_x | planted case | ρ̂ | φ_req | screen says | should say | correct |
|---|---|---|---|---|---|---|---|---|
| as-filed | 0.0 | 0.3 | clean, no selection on the disturbance | +0.008 | 0.36 | benign | benign | ✅ |
| as-filed | 0.0 | 2.0 | composition: filing speed set by size, hard | +0.002 | 0.35 | benign | benign | ✅ |
| as-filed | 0.3 | 0.7 | mild leak: filing speed sees the shock | −0.109 | 0.46 | susceptible | susceptible | ✅ |
| as-filed | 1.0 | 0.7 | strong leak: filing speed sees the shock | −0.324 | 0.67 | susceptible | susceptible | ✅ |
| **uniform-4m** | 0.3 | 0.7 | **same mild leak, uniform four-month release** | **−0.012** | 0.36 | benign | benign | ✅ |
| **uniform-4m** | 1.0 | 0.7 | **same strong leak, uniform four-month release** | **+0.017** | 0.37 | benign | benign | ✅ |
| uniform-4m | 1.0 | 0.7 | uniform lag **but** fiscal year-end tracks shock | **+0.690** | 1.00 | susceptible | susceptible | ✅ |

**Control result: 7/7 correct.**

Three things this table establishes, in order of importance:

1. **The screen can fire.** Rows 3–4 plant leakage and it detects it. A screen that never fires
   would make the benign rows meaningless.
2. **The convention closes the channel.** Rows 5–6 carry the *same* planted leakage as rows 3–4 —
   filing speed still depends on the shock exactly as hard — and the screen reads essentially zero.
   Nothing about the firms changed; only the release rule did. This is the by-construction claim,
   demonstrated rather than asserted.
3. **The screen is not just a completeness counter.** Row 2 selects on the observable more than six
   times harder than row 1 and is still correctly called benign.

## 4. Results

There is no per-characteristic results table in this report, and its absence is the finding rather
than a gap in the work: the dataset ships no arrival column, so ρ̂ cannot be estimated for any of
the 406 characteristics from outside.

What can be stated:

| question | answer | basis |
|---|---|---|
| Is a staggered-arrival channel present in the delivered data? | No | Uniform four-month convention, `Documentation.pdf` §6.2 |
| Does the convention close the channel this screen measures? | Yes | Positive control, rows 5–6 |
| Can that be verified against delivered data? | **No** | No arrival/availability field documented |
| Can susceptibility be graded per characteristic? | **No, not from outside** | Same reason |
| What does the closure cost? | A uniform timeliness tax on all 406 characteristics | §5 |

## 5. Conclusion and limitations

**What was found.** The Global Factor Data documentation states one uniform accounting-availability
convention, applied to every accounting variable. Under that convention the arrival-selection
channel is closed structurally, and a planted-truth control confirms that the same leakage the
screen detects under as-filed release becomes undetectable under uniform release.

**Why — name the construction.** Arrival ordering under a uniform offset is determined by **fiscal
period end**, a firm attribute, and not by **filing speed**, the behaviour that carries the
disturbance. A firm that files in thirty days and a firm that files in ninety become usable on the
same day relative to their own period ends, so the early set is no longer the fast-filing set.
Because the template asks for the sentence that tells a reader which change would remove the
protection: **the protection is removed by any release rule that lets filing speed order arrival —
for example rebuilding the same characteristics from as-filed sources with real filing dates.**

**The boundary condition, stated plainly.** The closure rests on fiscal period end being unrelated
to the disturbance. Row 7 of the control plants a violation — fiscal year-end ordering that tracks
the shock — and the screen fires at ρ̂ = +0.690 under the *same* uniform four-month lag. This is not
a claim that such a violation is present in any market; it is the assumption the convention
depends on, made explicit so a reader can judge it for their own universe. Fiscal-year-end choice
is plausibly related to industry and seasonality, and a reader working in a market where it is also
related to performance should treat the closure as an open question there.

**The cost, stated without euphemism.** A uniform lag is a blunt instrument. Every one of the 406
characteristics waits four months, whether or not its own susceptibility would justify waiting. The
characteristics that would screen benign subsidise the ones that would not, and the subsidy is paid
in timeliness on every observation in 93 countries. This is precisely the blanket penalty a
susceptibility-graded gate is built to avoid — and it is also a defensible, transparent, documented
choice for a dataset whose purpose is broad comparability across markets where filing conventions
differ wildly. Recording the trade-off is not a criticism of it.

**What this does not license.**

- It does not license any statement about Global Factor Data's accuracy, replication fidelity,
  coverage, or usefulness. None of those were examined.
- It does not license the reader to conclude that any characteristic in the dataset *is* benign in
  the measured sense. The verdict is about the release convention, not about 406 individual
  susceptibilities.
- It does not evaluate whether four months is the right number for any particular country. The
  screen has nothing to say about the level; only about the uniformity.
- It is not a finding about Jensen, Kelly, and Pedersen (2023), whose 153 factors are a subset of
  the dataset and whose analysis is outside this scope.

**Limitations, honestly.**

- **Not externally verifiable.** This is the central limitation. Without a per-observation arrival
  field, the convention can be read but not checked, and no ρ̂ can be estimated for any
  characteristic.
- **The control is synthetic.** It demonstrates a mechanism under planted truth; it is not evidence
  about the delivered data.
- **The quarterly/annual merge is out of scope.** The documentation describes taking the most
  recent value across separately built annual and quarterly characteristics. Whether that merge
  interacts with the uniform lag in any way this screen would care about was not examined.
- **One document, one vintage.** Conventions change; this reads the version retrieved 2026-08.

**Suggestion for the target.** One optional column would convert everything above from a reading
into a measurement: a per-observation **availability date** — the date the underlying accounting
value became usable — shipped alongside the characteristic. With it, a user could confirm the
four-month convention directly, and per-characteristic ρ̂ could be estimated so that characteristics
which screen benign release earlier than four months while susceptible ones keep the full lag. We
would be glad to help specify it, contribute the estimation code, or run the graded table across the
406 characteristics and hand over the results — whichever is most useful, and with no expectation
attached.

## 6. Reproduce

The convention is read from a free public document; the control runs on numpy and scipy alone.

```bash
# 1. the source document (free, no account)
curl -O https://jkpfactors-data.s3.amazonaws.com/documents/Documentation.pdf

# 2. the quoted passages
pdftotext Documentation.pdf - | grep -i -A2 -B2 "publically available"
pdftotext Documentation.pdf - | grep -i "406 characteristics"

# 3. the positive control
pip install numpy scipy
python jkp_construction_control.py
```

- **Runtime:** the control runs in seconds.
- **Requires a licence or account:** **no.** The documentation is a public PDF, and no Global
  Factor Data was used.
- **Determinism:** the control is seeded (`20260601`) and reproduces exactly.
- **Artifacts in this directory:**
  [`jkp_construction_control.py`](jkp_construction_control.py) — the control, with the quoted
  convention in its docstring.

## Badge

This finding has a live endpoint badge. **It is available for the audited project to display; it
links back to the full audit.** No permission is needed, nothing is expected in return, and it can
be dropped at any time.

```markdown
[![PIT audit](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMaxWellApexLab%2Fpit-audit-registry%2Fmain%2Fbadge-data%2Fjkp-gfd.json)](https://github.com/MaxWellApexLab/pit-audit-registry/blob/main/audits/2026-08_jkp-gfd/report.md)
```

The badge label reads `PIT audit` and its message is one of the registry's verdict values. It
states what was measured and nothing more — it is not a seal, a grade, or a mark of quality, and
this registry issues no such thing.

**Re-screening.** If the convention changes, or if an availability field is added, we will re-run
this and publish a new dated version of the report. Requests to re-screen are welcome and are the
whole point of publishing the reproduction command.

---

**The rest of this ecosystem**

| | |
|---|---|
| Tool | [`pit-release-gate`](https://github.com/MaxWellApexLab/pit-release-gate) — MIT, pip-installable; the reference implementation of the screen and the graded gate |
| Registry | [`pit-audit-registry`](https://github.com/MaxWellApexLab/pit-audit-registry) — this registry; every entry is a measurement with a command attached |
| Pledge | [`pit-hygiene`](https://github.com/MaxWellApexLab/pit-hygiene) — five self-declared commitments for your own pipeline; no outside body involved |
| Papers | [doi:10.6084/m9.figshare.32952482](https://doi.org/10.6084/m9.figshare.32952482) (engine) · [doi:10.6084/m9.figshare.33061955](https://doi.org/10.6084/m9.figshare.33061955) (screen) · [doi:10.6084/m9.figshare.33158615](https://doi.org/10.6084/m9.figshare.33158615) (release control) — all preprints |

*Report: CC BY 4.0. Screening code: MIT.*
