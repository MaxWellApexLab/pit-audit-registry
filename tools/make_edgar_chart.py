"""Regenerate assets/edgar_flags.png — per-signal susceptibility on the as-filed
SEC EDGAR US panel.

Numbers are transcribed from the per-signal table in
methodology/2026-08_sec-edgar/report.md (frozen protocol: K=5 trailing periods,
6 evaluation years, threshold 0.10). If the report is re-run and the numbers
move, update ROWS below to match the report — never the other way around.
"""
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).resolve().parents[1] / "assets"
OUT.mkdir(parents=True, exist_ok=True)

# signal, mean rho_hat, cycles flagged (of 6) — report.md section 4
ROWS = [
    ("RnD/assets", -0.1613, 6),
    ("OpProfit/assets", +0.1443, 6),
    ("GrossProfit/assets", -0.1075, 4),
    ("Accruals", +0.1074, 4),
    ("CFO/assets", +0.0964, 3),
    ("Equity/assets", +0.0936, 3),
    ("Leverage", -0.0707, 2),
    ("AssetGrowth", +0.0811, 0),
    ("ROA", +0.0701, 0),
    ("SalesGrowth", +0.0598, 0),
    ("PPE/assets", -0.0557, 0),
    ("CurrentRatio", -0.0539, 0),
    ("Inventory/assets", +0.0442, 0),
    ("NetMargin", +0.0366, 0),
]
THRESHOLD = 0.10


def main():
    rows = sorted(ROWS, key=lambda r: -abs(r[1]))
    names = [r[0] for r in rows]
    rhos = [r[1] for r in rows]
    flags = [r[2] for r in rows]
    colors = ["#c0392b" if f else "#7fb3d3" for f in flags]

    fig, ax = plt.subplots(figsize=(8.6, 5.0), dpi=150)
    y = range(len(names))
    ax.axvspan(-THRESHOLD, THRESHOLD, color="#f2f2f2", zorder=0)
    ax.axvline(-THRESHOLD, color="#999999", lw=0.8, ls="--")
    ax.axvline(+THRESHOLD, color="#999999", lw=0.8, ls="--")
    ax.axvline(0, color="black", lw=0.8)
    ax.barh(list(y), rhos, color=colors, alpha=0.9, zorder=2)
    for i, (r, f) in enumerate(zip(rhos, flags)):
        if f:
            ax.annotate(f"{f}/6 cycles flagged", (r, i),
                        textcoords="offset points",
                        xytext=(6 if r > 0 else -6, 0),
                        ha="left" if r > 0 else "right",
                        va="center", fontsize=8, color="#c0392b")
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(-0.27, 0.27)
    ax.set_xlabel("mean susceptibility ρ̂ per signal  (shaded band = |ρ̂| < 0.10 threshold)")
    ax.set_title("As-filed SEC EDGAR panel, observed filing dates:\n"
                 "7 of 14 signals flagged (28/84 signal-cycles); ROA clean at 0/6",
                 fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "edgar_flags.png", facecolor="white")
    print("wrote", OUT / "edgar_flags.png",
          "| flagged signals:", sum(1 for f in flags if f),
          "| flagged cycles:", sum(flags))


if __name__ == "__main__":
    main()
