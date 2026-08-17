"""Re-verify that every number this registry publishes still reproduces.

A registry that grades other people's data has to be checkable itself. This
harness runs the scripts committed alongside each report and compares what
they print to what the report claims. It re-derives nothing independently —
a second implementation would only test itself — so a drift here means the
published report and its own shipped code have parted ways.

Scope: the checks that run on committed data. The OSAP screen downloads a
live third-party release whose later vintages legitimately move the numbers,
so it is not asserted here; its report states that, and the notebook is the
reproduction path.

Run:  python tools/verify_published_numbers.py
Exit: 0 if every published figure still reproduces, 1 otherwise.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGAR = ROOT / "methodology" / "2026-08_sec-edgar"

failures: list[str] = []
checks = 0


def check(label, got, want, tol=0.0):
    global checks
    checks += 1
    if isinstance(want, (int, float)) and isinstance(got, (int, float)):
        ok = abs(got - want) <= tol
    else:
        ok = got == want
    print(f"  {'ok   ' if ok else 'DRIFT'} {label}: {got}"
          + ("" if ok else f"   (published: {want})"))
    if not ok:
        failures.append(f"{label}: published {want}, reproduced {got}")


def run(script: Path, timeout=1800) -> str:
    r = subprocess.run([sys.executable, script.name], cwd=script.parent,
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"{script.name} exited {r.returncode}: {r.stderr[-400:]}")
    return r.stdout


def num(text: str, pattern: str) -> float:
    m = re.search(pattern, text)
    if not m:
        raise RuntimeError(f"{pattern!r} not found in output — the script's "
                           "print format changed without this check being updated")
    return float(m.group(1))


def verify_size_path():
    """The three correlations the EDGAR report's headline rests on."""
    print("\nEDGAR: latency / signal / size correlations  (verify_size_path.py)")
    out = run(EDGAR / "verify_size_path.py")
    check("panel firm-years", num(out, r"panel after filters: (\d+) firm-years"), 8118)
    check("panel firms", num(out, r"firm-years, (\d+) firms"), 856)
    check("corr(latency, log size)", num(out, r"corr\(latency rank, log size\)\s*=\s*([-+\d.]+)"), -0.688, 0.001)
    check("corr(signal, log size)", num(out, r"corr\(signal, log size\)\s*=\s*([-+\d.]+)"), 0.508, 0.001)
    check("corr(latency, signal) raw", num(out, r"corr\(latency rank, signal\) = raw\s*=\s*([-+\d.]+)"), -0.296, 0.001)
    check("size-mediated path", num(out, r"size-mediated path = product\s*=\s*([-+\d.]+)"), -0.349, 0.001)


def verify_frozen_protocol():
    """The verdict itself: 28 of 84 signal-cycles flagged, 7 of 14 signals clean."""
    print("\nEDGAR: frozen-protocol verdict  (edgar_frozen.py)")
    out = run(EDGAR / "edgar_frozen.py")
    check("signal-cycles flagged", num(out, r"TOTAL: (\d+) flagged of"), 28)
    check("signal-cycles screened", num(out, r"flagged of (\d+) signal-cycles"), 84)
    check("signals screened", num(out, r"signal-cycles across (\d+) signals"), 14)
    check("signals with zero flagged cycles", num(out, r"zero flagged cycles: (\d+) /"), 7)


def verify_positive_control():
    """A screen that never fires is worthless unless it is shown that it can."""
    print("\nEDGAR: planted-truth positive control  (edgar_control.py)")
    out = run(EDGAR / "edgar_control.py")
    ok = num(out, r"Control result: (\d+)/")
    total = num(out, r"Control result: \d+/(\d+)")
    check("positive-control cases correct", ok, total)


def verify_badges():
    """Badge endpoints are generated, never hand-edited."""
    print("\nBadge endpoints")
    before = {p.name: p.read_text(encoding="utf-8")
              for p in sorted((ROOT / "badge-data").glob("*.json"))}
    r = subprocess.run([sys.executable, "tools/update_badges.py"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        failures.append(f"update_badges.py exited {r.returncode}: {r.stderr[-300:]}")
    after = {p.name: p.read_text(encoding="utf-8")
             for p in sorted((ROOT / "badge-data").glob("*.json"))}
    check("regenerating badges is a no-op on committed state", after == before, True)

    audits = json.loads((ROOT / "badge-data" / "audits.json").read_text(encoding="utf-8"))
    entries = len(list((ROOT / "audits").glob("*/report.md")))
    check("audits badge matches the number of audit reports", str(audits["message"]), str(entries))


def verify_report_arithmetic():
    """Totals stated in prose must agree with the table that produces them."""
    print("\nInternal arithmetic of the EDGAR report")
    text = (EDGAR / "report.md").read_text(encoding="utf-8")
    pairs = re.findall(r"\*\*(\d+) / (\d+)\*\*", text)
    flagged = [int(a) for a, _ in pairs]
    screened = [int(b) for _, b in pairs]
    check("per-signal flag counts sum to the stated total", sum(flagged), 28)
    check("per-signal cycle counts sum to the stated total", sum(screened), 84)
    check("signals flagged at least once", sum(1 for f in flagged if f), 7)
    check("signals clean", sum(1 for f in flagged if not f), 7)


def main():
    print("Re-verifying published registry numbers against the committed code")
    for fn in (verify_report_arithmetic, verify_badges, verify_size_path,
               verify_frozen_protocol, verify_positive_control):
        try:
            fn()
        except Exception as exc:
            failures.append(f"{fn.__name__}: {type(exc).__name__}: {exc}")
            print(f"  ERROR {fn.__name__}: {type(exc).__name__}: {exc}")

    print(f"\n{checks} checks run")
    if failures:
        print(f"{len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("every published number still reproduces from the committed code")


if __name__ == "__main__":
    main()
