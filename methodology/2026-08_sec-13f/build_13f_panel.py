"""Build an institution-level panel from SEC Form 13F structured data sets.

One row per (institutional manager, report quarter):

    period    the quarter the holdings describe (PERIODOFREPORT)
    entity    the manager's CIK
    arrival   days from the quarter end to the filing date -- OBSERVED, not
              assumed: 13F-HR is due within 45 days, and managers use that
              window very differently
    size      log total reported portfolio value (the conditioning covariate)
    <signals> portfolio characteristics computed across that manager's holdings

Every characteristic here is a *cross-sectional* quantity in the sense the
screen cares about: its cross-manager distribution at any moment before the
45-day deadline is built from whichever managers have filed so far.

Source: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
Free, official, no account. Each zip holds one quarter of received filings.
Zips are streamed and discarded; only the aggregated panel is kept.
"""
from __future__ import annotations

import io
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import polars as pl

UA = "Max Well Apex LLC research maxwellapexlab@proton.me"
BASE = "https://www.sec.gov/files/structureddata/data/form-13f-data-sets"
HERE = Path(__file__).resolve().parent
OUT = HERE / "panel_13f.parquet"

QUARTERS = [f"{y}q{q}" for y in range(2020, 2024) for q in range(1, 5)]


def fetch(quarter: str) -> bytes:
    url = f"{BASE}/{quarter}_form13f.zip"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def _read_member(zf: zipfile.ZipFile, name: str, columns) -> pl.DataFrame:
    with zf.open(name) as fh:
        return pl.read_csv(fh.read(), separator="\t", columns=columns,
                           infer_schema_length=0, truncate_ragged_lines=True)


def quarter_rows(blob: bytes) -> pl.DataFrame:
    """Aggregate one quarter's filings into one row per manager."""
    zf = zipfile.ZipFile(io.BytesIO(blob))
    names = {n.split("/")[-1].upper(): n for n in zf.namelist()}

    sub = _read_member(zf, names["SUBMISSION.TSV"],
                       ["ACCESSION_NUMBER", "CIK", "SUBMISSIONTYPE",
                        "FILING_DATE", "PERIODOFREPORT"])
    # 13F-HR only: amendments arrive later by construction and would confound
    # arrival timing with revision behaviour, which is a different question.
    sub = sub.filter(pl.col("SUBMISSIONTYPE") == "13F-HR")

    info = _read_member(zf, names["INFOTABLE.TSV"],
                        ["ACCESSION_NUMBER", "CUSIP", "VALUE"])
    info = info.with_columns(pl.col("VALUE").cast(pl.Float64, strict=False))
    info = info.filter(pl.col("VALUE") > 0)

    # per-manager portfolio characteristics
    agg = (info.group_by("ACCESSION_NUMBER")
           .agg(total=pl.col("VALUE").sum(),
                n_positions=pl.len(),
                hhi=(pl.col("VALUE") / pl.col("VALUE").sum()).pow(2).sum(),
                top10=(pl.col("VALUE").top_k(10).sum() / pl.col("VALUE").sum())))

    df = sub.join(agg, on="ACCESSION_NUMBER", how="inner")
    df = df.with_columns(
        pl.col("FILING_DATE").str.to_date("%d-%b-%Y", strict=False)
          .fill_null(pl.col("FILING_DATE").str.to_date("%Y-%m-%d", strict=False))
          .alias("filed"),
        pl.col("PERIODOFREPORT").str.to_date("%d-%b-%Y", strict=False)
          .fill_null(pl.col("PERIODOFREPORT").str.to_date("%Y-%m-%d", strict=False))
          .alias("qend"),
    ).drop_nulls(["filed", "qend"])

    return df.select(
        pl.col("qend").alias("period"),
        pl.col("CIK").alias("entity"),
        (pl.col("filed") - pl.col("qend")).dt.total_days().cast(pl.Float64).alias("arrival"),
        pl.col("total").log().alias("size"),
        pl.col("hhi").alias("concentration_hhi"),
        pl.col("top10").alias("top10_share"),
        pl.col("n_positions").log().alias("log_positions"),
        pl.col("total").log().alias("log_portfolio_value"),
    )


def main():
    frames = []
    for i, q in enumerate(QUARTERS, 1):
        t0 = time.time()
        try:
            rows = quarter_rows(fetch(q))
        except Exception as exc:                       # a missing quarter is not fatal
            print(f"[{i:2}/{len(QUARTERS)}] {q}: SKIPPED ({type(exc).__name__}: {exc})",
                  flush=True)
            continue
        frames.append(rows)
        print(f"[{i:2}/{len(QUARTERS)}] {q}: {rows.height:>6} managers, "
              f"periods {sorted(set(rows['period'].to_list()))[:3]}, "
              f"{time.time() - t0:.0f}s", flush=True)
        time.sleep(1)                                  # be polite to SEC

    if not frames:
        sys.exit("no quarters downloaded")
    panel = pl.concat(frames)

    # one filing per (manager, period): keep the earliest, which is the
    # original report -- later ones for the same period are re-files
    panel = (panel.sort("arrival")
             .unique(subset=["entity", "period"], keep="first")
             .sort(["period", "entity"]))
    # 13F-HR is due 45 days after quarter end; anything outside is a late or
    # mis-stamped filing and is dropped rather than silently stretching the window
    panel = panel.filter((pl.col("arrival") >= 0) & (pl.col("arrival") <= 45))

    panel.write_parquet(OUT)
    print(f"\nwrote {OUT}  rows={panel.height}  periods={panel['period'].n_unique()}")
    print(panel.group_by("period").agg(
        managers=pl.len(),
        median_days=pl.col("arrival").median(),
        p10=pl.col("arrival").quantile(0.1),
        p90=pl.col("arrival").quantile(0.9),
    ).sort("period"))


if __name__ == "__main__":
    main()
