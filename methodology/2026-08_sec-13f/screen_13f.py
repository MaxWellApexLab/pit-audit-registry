"""Screen the 13F manager panel for incomplete-cross-section leakage.

Three things are run, in the order the registry requires:

1. a NOISE FLOOR — signals drawn independently of everything else, so their
   readings show what this panel's sampling noise looks like at this size;
2. a POSITIVE CONTROL — a synthetic signal coupled to the *observed* filing
   latencies by a known amount, so the screen is shown to fire when a channel
   really is present;
3. the REAL signals — portfolio characteristics computed across managers.

Everything goes through the package's public entry point, on the real
arrival dates, with the frozen protocol: fit on prior completed quarters,
freeze, apply forward.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from pit_release_gate import screen_dataframe

HERE = Path(__file__).resolve().parent
PANEL = HERE / "panel_13f.parquet"
TRAILING_K = 5
THRESHOLD = 0.10
SEED = 20260818

REAL_SIGNALS = ["concentration_hhi", "top10_share", "log_positions"]


def load():
    p = pl.read_parquet(PANEL)
    # period as days-since-epoch: an ordered integer, so quarters screen in time order
    per = p["period"].to_numpy().astype("datetime64[D]").astype(np.int64)
    cols = {c: p[c].to_numpy() for c in p.columns if c != "period"}
    cols["period"] = per
    return cols, len(np.unique(per))


def add_controls(cols):
    rng = np.random.default_rng(SEED)
    n = len(cols["period"])

    # --- noise floor: unrelated to arrival, to size, to anything ---
    for i in range(3):
        cols[f"noise_{i}"] = rng.normal(size=n)

    # --- positive control: couple the signal to OBSERVED latency ---
    # a manager that filed early gets a systematically higher disturbance, which
    # is exactly the channel the screen exists to detect. Strength is stated,
    # not tuned: two levels, one mild, one strong.
    lat = cols["arrival"].astype(float)
    lat_z = (lat - lat.mean()) / lat.std()
    for label, strength in (("planted_mild", 0.35), ("planted_strong", 1.20)):
        cols[label] = (0.5 * cols["size"] / cols["size"].std()
                       - strength * lat_z + rng.normal(size=n))
    return cols


def main():
    cols, n_periods = load()
    cols = add_controls(cols)
    print(f"panel: {len(cols['period'])} manager-quarters, {n_periods} quarters, "
          f"arrival {cols['arrival'].min():.0f}-{cols['arrival'].max():.0f} days after quarter end")

    groups = [
        ("noise floor", [f"noise_{i}" for i in range(3)]),
        ("positive control", ["planted_mild", "planted_strong"]),
        ("real signals", REAL_SIGNALS),
    ]
    records = {}
    for title, names in groups:
        rec = screen_dataframe(cols, value=names, trailing_k=TRAILING_K,
                               rho_threshold=THRESHOLD)
        records[title] = rec
        print(f"\n{title}")
        print(f"  {'signal':<22}{'periods':>8}{'flagged':>9}{'mean rho':>11}"
              f"{'max |rho|':>11}{'phi_req':>9}  verdict")
        for s in rec["signals"]:
            print(f"  {s['name']:<22}{s['periods_screened']:>8}{s['periods_flagged']:>9}"
                  f"{s['mean_rho']:>+11.4f}{s['max_abs_rho']:>11.4f}"
                  f"{s['mean_phi_req']:>9.3f}  {s['verdict']}")

    floor = max(abs(s["max_abs_rho"]) for s in records["noise floor"]["signals"])
    print(f"\nnoise floor (largest |rho| any unrelated signal reached): {floor:.4f}")
    caught = sum(1 for s in records["positive control"]["signals"]
                 if s["verdict"] == "susceptible")
    print(f"positive control: {caught}/2 planted channels detected")

    out = HERE / "screen_13f_results.json"
    out.write_text(json.dumps({k: v for k, v in records.items()}, indent=2),
                   encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
