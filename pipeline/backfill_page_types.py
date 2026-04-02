"""Backfill page-level 'type' field on all existing result JSONs.

Reads each result file, classifies every page via _classify_page(),
stamps page["type"], and writes back. Files with v1.1 signals (no
page_types) get a full quality_signals recomputation to v1.3.

Usage:
    python pipeline/backfill_page_types.py              # run backfill
    python pipeline/backfill_page_types.py --dry-run    # preview only
    python pipeline/backfill_page_types.py --verify     # check consistency
"""

import argparse
import json
from pathlib import Path

from quality_signals import _classify_page, compute_signals

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
COLLECTIONS = ["lebensdokumente", "korrespondenzen", "aufsatzablage", "werke"]


def find_result_files():
    """Find all Gemini result JSONs (exclude consensus files)."""
    files = []
    for col in COLLECTIONS:
        col_dir = RESULTS_DIR / col
        if col_dir.exists():
            files.extend(sorted(col_dir.glob("*_gemini-*.json")))
    return files


def backfill(dry_run=False):
    """Stamp page['type'] on all result files."""
    files = find_result_files()
    stats = {"files": 0, "pages": 0, "content": 0, "blank": 0, "color_chart": 0,
             "already_typed": 0, "recomputed": 0}

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        pages = data.get("result", {}).get("pages", [])
        qs = data.get("quality_signals", {})
        changed = False

        # Stamp type on each page
        for page in pages:
            ptype = _classify_page(page)
            if page.get("type") != ptype:
                page["type"] = ptype
                changed = True
            stats["pages"] += 1
            stats[ptype] += 1

        # Sync quality_signals.page_types with page-level types
        if qs and "page_types" in qs:
            synced_types = [p.get("type", "content") for p in pages]
            if qs["page_types"] != synced_types:
                qs["page_types"] = synced_types
                # Recount page categories
                qs["content_pages"] = synced_types.count("content")
                qs["blank_pages"] = synced_types.count("blank")
                qs["color_chart_pages"] = synced_types.count("color_chart")
                changed = True

        # v1.1 files: recompute full signals
        if qs and "page_types" not in qs:
            metadata = data.get("metadata", {})
            input_images = qs.get("input_images", len(metadata.get("images", [])))
            data["quality_signals"] = compute_signals(
                data["result"], metadata, input_images
            )
            changed = True
            stats["recomputed"] += 1
        elif qs and qs.get("version") != "1.3":
            # Update version for v1.2 files
            data["quality_signals"]["version"] = "1.3"
            changed = True

        if changed:
            stats["files"] += 1
            if not dry_run:
                f.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    return stats


def verify():
    """Check that page['type'] matches quality_signals.page_types[i]."""
    files = find_result_files()
    ok = 0
    mismatches = []

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        pages = data.get("result", {}).get("pages", [])
        page_types = data.get("quality_signals", {}).get("page_types", [])

        for i, page in enumerate(pages):
            pt = page.get("type")
            qt = page_types[i] if i < len(page_types) else None
            if pt and qt and pt == qt:
                ok += 1
            elif pt != qt:
                mismatches.append(f"{f.name} page {i}: page.type={pt}, qs={qt}")

    return ok, mismatches


def main():
    parser = argparse.ArgumentParser(description="Backfill page-level type field")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--verify", action="store_true", help="Check consistency only")
    args = parser.parse_args()

    if args.verify:
        ok, mismatches = verify()
        print(f"Consistent: {ok} pages")
        if mismatches:
            print(f"Mismatches: {len(mismatches)}")
            for m in mismatches[:20]:
                print(f"  {m}")
        else:
            print("All pages consistent.")
        return

    mode = "DRY-RUN" if args.dry_run else "BACKFILL"
    print(f"[{mode}] Scanning {RESULTS_DIR} ...")

    stats = backfill(dry_run=args.dry_run)

    print(f"Files modified: {stats['files']}")
    print(f"Pages stamped:  {stats['pages']}")
    print(f"  content:      {stats['content']}")
    print(f"  blank:        {stats['blank']}")
    print(f"  color_chart:  {stats['color_chart']}")
    print(f"  v1.1 recomputed: {stats['recomputed']}")


if __name__ == "__main__":
    main()
