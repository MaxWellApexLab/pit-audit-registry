"""Robustness of the 13F finding, before it is allowed to be a finding.

The headline screen reads |rho| ~ 0.15 on three manager characteristics, an
order of magnitude above this panel's noise floor. Four ways it could be an
artifact instead of a channel, each tested:

  shuffle      permute arrival WITHIN each quarter. If the reading survives,
               it was never about arrival and the finding is dead.
  deadline     drop managers filing on day 45. A pile-up at the statutory
               deadline creates a mass of tied latencies; the reading must
               not depend on it.
  size2        add a quadratic size term to the conditioning set. A nonlinear
               size effect could otherwise masquerade as arrival selection.
  trailing_k   refit on 3 and 8 prior quarters. A result that only exists at
               k=5 is a tuning artifact.
"""
from __future__ import annotations

import numpy as np
import polars as pl
from pathlib import Path

from pit_release_gate import screen_dataframe
from pit_release_gate.frame import stores_from_frame
from pit_release_gate.gate import SusceptibilityGate

HERE = Path(__file__).resolve().parent
SIGNALS = ["concentration_hhi", "top10_share", "log_positions"]
THRESHOLD = 0.10
SEED = 20260818


def load():
    p = pl.read_parquet(HERE / "panel_13f.parquet")
    cols = {c: p[c].to_numpy() for c in p.columns if c != "period"}
    cols["period"] = p["period"].to_numpy().astype("datetime64[D]").astype(np.int64)
    return cols


def summarise(label, cols, **kw):
    rec = screen_dataframe(cols, value=SIGNALS, rho_threshold=THRESHOLD,
                           **{"trailing_k": 5, **kw})
    line = f"  {label:<26}"
    for s in rec["signals"]:
        line += f"{s['name'][:12]:>14}={s['mean_rho']:+.4f}({s['periods_flagged']}/{s['periods_screened']})"
    print(line)
    return {s["name"]: (s["mean_rho"], s["periods_flagged"]) for s in rec["signals"]}


def main():
    base = load()
    print(f"13F robustness — {len(base['period'])} manager-quarters\n")
    print("baseline")
    ref = summarise("as published", base)

    print("\nshuffle control (arrival permuted within each quarter)")
    rng = np.random.default_rng(SEED)
    for rep in range(3):
        sh = dict(base)
        arr = base["arrival"].copy()
        for q in np.unique(base["period"]):
            m = base["period"] == q
            arr[m] = rng.permutation(arr[m])
        sh["arrival"] = arr
        summarise(f"shuffled #{rep + 1}", sh)

    print("\ndeadline pile-up removed")
    m = base["arrival"] < 45
    print(f"  (drops {(~m).sum()} of {len(m)} manager-quarters filed on day 45)")
    summarise("arrival < 45 days", {k: v[m] for k, v in base.items()})

    print("\nnonlinear size control")
    sq = dict(base)
    z = (base["size"] - base["size"].mean()) / base["size"].std()
    # screen against a size variable that already carries the quadratic term,
    # so any curvature in the size-signal relation cannot pass as arrival selection
    sq["size"] = z + 0.5 * (z ** 2 - 1.0)
    summarise("size + quadratic", sq)

    print("\ntrailing window")
    for k in (3, 8):
        summarise(f"trailing_k = {k}", base, trailing_k=k)

    print("\nper-quarter dispersion of the frozen estimate (concentration_hhi)")
    stores, kept = stores_from_frame(base, value="concentration_hhi")
    for i in range(5, len(stores)):
        g = SusceptibilityGate(threshold=THRESHOLD)
        rho = g.fit_trailing(stores[i - 5:i])
        q = np.datetime64(int(kept[i]), "D")
        print(f"  quarter ending {q}  n={stores[i].n:>5}  rho_frozen={rho:+.4f}"
              f"  {'FLAGGED' if abs(rho) > THRESHOLD else 'clean'}")


if __name__ == "__main__":
    main()
