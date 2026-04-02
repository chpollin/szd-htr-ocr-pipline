"""Recompute quality_signals on all existing result JSONs.

Use after changing thresholds or removing signals in quality_signals.py.
Preserves review, edit_history, and all other fields — only overwrites
the quality_signals block.

Usage:
    python pipeline/backfill_quality_signals.py              # run
    python pipeline/backfill_quality_signals.py --dry-run    # preview
"""

import argparse
import json
import sys
from pathlib import Path

from quality_signals import compute_signals

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
COLLECTIONS = ["lebensdokumente", "korrespondenzen", "aufsatzablage", "werke"]


def main():
    parser = argparse.ArgumentParser(description="Recompute quality_signals on all results.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total = 0
    changed = 0
    removed_low_dwr = 0

    for col in COLLECTIONS:
        col_dir = RESULTS_DIR / col
        if not col_dir.exists():
            continue
        for f in sorted(col_dir.glob("*_gemini-*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            old_qs = data.get("quality_signals", {})
            if not old_qs:
                continue

            result = data.get("result", {})
            meta = data.get("metadata", {})
            input_images = old_qs.get("input_images", len(result.get("pages", [])))

            new_qs = compute_signals(result, meta, input_images)

            old_reasons = set(old_qs.get("needs_review_reasons", []))
            new_reasons = set(new_qs.get("needs_review_reasons", []))

            if old_qs.get("needs_review") != new_qs["needs_review"] or old_reasons != new_reasons:
                if "low_dwr" in old_reasons and "low_dwr" not in new_reasons:
                    removed_low_dwr += 1

                if not args.dry_run:
                    data["quality_signals"] = new_qs
                    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                changed += 1

            total += 1

    mode = "DRY RUN: " if args.dry_run else ""
    print(f"{mode}Scanned {total} files, {changed} changed.")
    print(f"  low_dwr removed from needs_review: {removed_low_dwr}")
    nr_before = "?"  # We don't track this precisely
    print(f"  Run build_viewer_data.py to update frontend.")


if __name__ == "__main__":
    main()
