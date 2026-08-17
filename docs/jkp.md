---
title: "Does JKP Global Factor Data have look-ahead bias from staggered filings? Audit verdict: benign (by construction)"
description: >-
  Verdict: benign (by construction). The documented uniform four-month
  availability convention removes filing speed from arrival ordering. On
  planted truth the same leakage reads -0.324 as-filed vs +0.017 uniform.
---

# Does JKP Global Factor Data have look-ahead bias from staggered filings?

**Verdict: `benign (by construction)`** — screened 2026-08 against the
dataset's own documentation (`Documentation.pdf`, 55 pp.).

## The convention

The documentation states the rule directly:

> "We assume that accounting variables are publically available 4 months after
> the end of the accounting period."

Applied uniformly to every accounting variable, this removes filing speed from
arrival ordering — a fast filer and a slow filer become visible at the same
time. Arrival order can then no longer select on the disturbance, which closes
the incomplete-cross-section channel **structurally**.

## The demonstration

Because the published data carry no per-record arrival field, the verdict is
established on planted truth rather than measured on the panel: the same
planted leakage reads **ρ̂ = −0.324 under as-filed release** and **+0.017 under
uniform four-month release** (positive control 7/7). The convention works; what
cannot be done from the outside is verify the assumption against actual filing
dates, since none are documented.

## The cost, stated honestly

Structural protection via a blanket lag is a **timeliness tax paid by all 406
characteristics** — including signals a per-signal screen would release months
earlier. That trade-off (uniform lag vs. graded release) is the subject of the
[release-control method paper](https://doi.org/10.6084/m9.figshare.33158615).

And as with [OSAP](osap): the protection belongs to the convention. Rebuilding
JKP-style characteristics from [as-filed sources](edgar) at observed filing
dates re-opens the channel — there, 7 of 14 standard signals flag.

**[Full report](https://github.com/MaxWellApexLab/pit-audit-registry/blob/main/audits/2026-08_jkp-gfd/report.md)** ·
[Control script](https://github.com/MaxWellApexLab/pit-audit-registry/blob/main/audits/2026-08_jkp-gfd/jkp_construction_control.py) ·
[Registry](index)
