#!/usr/bin/env python3
"""update_badges.py — regenerate every shields endpoint in badge-data/ from registry.json.

Run by hand after adding or re-screening an entry:

    python tools/update_badges.py          # rewrite badge-data/*.json
    python tools/update_badges.py --check   # verify only, non-zero exit if stale (for CI)

Why a manifest instead of parsing the reports: the counts that appear on the scoreboard must
not be able to run ahead of the reports that justify them. registry.json lists an entry only
when its report is live, and every published number is derived from that list, so the aggregate
badges cannot be inflated without adding a report first.

Methodology pages are listed in registry.json but deliberately carry no badge and do not
contribute to the aggregate counts.

Standard library only; no network access of any kind.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BADGE_DIR = ROOT / "badge-data"
MANIFEST = BADGE_DIR / "registry.json"

LABEL = "PIT audit"
# Colours are fixed by the registry's verdict vocabulary. A verdict outside this map is an
# error rather than a default, so a new verdict type cannot be published by accident.
COLOR_BY_VERDICT = {
    "benign (measured)": "2ea44f",
    "benign (by construction)": "blue",
}


def endpoint(label: str, message: str, color: str) -> dict:
    return {"schemaVersion": 1, "label": label, "message": message, "color": color}


def build(manifest: dict) -> dict[str, dict]:
    """Return {filename: endpoint-json} for everything derived from the manifest."""
    out: dict[str, dict] = {}
    total_cycles = 0

    for entry in manifest["entries"]:
        verdict = entry["verdict"]
        if verdict not in COLOR_BY_VERDICT:
            raise SystemExit(
                f"{entry['slug']}: verdict {verdict!r} is not one the registry publishes. "
                f"Known: {sorted(COLOR_BY_VERDICT)}"
            )
        if entry["signalCyclesFlagged"] > entry["signalCycles"]:
            raise SystemExit(f"{entry['slug']}: flagged exceeds screened")
        out[f"{entry['slug']}.json"] = endpoint(
            LABEL, entry["badgeMessage"], COLOR_BY_VERDICT[verdict]
        )
        total_cycles += entry["signalCycles"]

    n_entries = len(manifest["entries"])
    # label kept as the already-published "audits" so regenerating this file does
    # not silently restyle a badge that is already live
    out["audits.json"] = endpoint("audits", str(n_entries), "blue")
    out["screened.json"] = endpoint("signal-cycles screened", str(total_cycles), "blue")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the files on disk match the manifest; write nothing")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    wanted = build(manifest)

    stale = []
    for name, payload in sorted(wanted.items()):
        path = BADGE_DIR / name
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        stale.append(name)
        if not args.check:
            path.write_text(text, encoding="utf-8")

    n_pages = len(manifest.get("methodologyPages", []))
    if args.check:
        if stale:
            print("stale badge files: " + ", ".join(stale), file=sys.stderr)
            return 1
        print(f"badge-data/ is current ({len(manifest['entries'])} entries, "
              f"{n_pages} methodology pages, no badge)")
        return 0

    print(f"wrote {len(stale)} file(s); {len(manifest['entries'])} registry entries, "
          f"{wanted['screened.json']['message']} signal-cycles cumulative, "
          f"{n_pages} methodology pages carry no badge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
