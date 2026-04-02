"""Diagnose truncated transcriptions by comparing result JSONs against actual image counts.

Scans all result files and flags objects where the transcription covers fewer
pages than the backup directory contains images.

Usage:
    python pipeline/diagnose_truncation.py [--json manifest.json] [--verbose]
"""

import argparse
import json
import sys
from pathlib import Path

from config import BACKUP_ROOT, COLLECTIONS, RESULTS_BASE


def count_backup_images(object_id: str, collection: str) -> int:
    """Count actual JPG images in the backup directory for an object."""
    subdir = COLLECTIONS[collection]["subdir"]
    img_dir = BACKUP_ROOT / subdir / object_id / "images"
    if not img_dir.exists():
        return -1
    return len(list(img_dir.glob("IMG_*.jpg")))


def diagnose_all() -> list[dict]:
    """Scan all result JSONs and compare against backup image counts.

    Returns list of issue dicts with keys:
        object_id, collection, group, issue_type, input_images,
        result_pages, actual_images, result_file
    """
    issues = []

    for collection in COLLECTIONS:
        col_dir = RESULTS_BASE / collection
        if not col_dir.exists():
            continue
        for result_file in sorted(col_dir.glob("*.json")):
            # Skip layout, groundtruth, and other non-transcription files
            if "_layout" in result_file.name or "_page" in result_file.name:
                continue

            try:
                data = json.loads(result_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            object_id = data.get("object_id")
            if not object_id:
                continue

            col = data.get("collection", collection)
            group = data.get("group", "?")

            # Pages in the result
            result_obj = data.get("result", {})
            pages = result_obj.get("pages", [])
            result_pages = len(pages)

            # Input images recorded by quality_signals
            qs = data.get("quality_signals", {})
            input_images = qs.get("input_images", 0)

            # Total images from metadata (new field, may not exist yet)
            meta = data.get("metadata", {})
            total_images_meta = meta.get("input_image_count_total", None)

            # Actual images in backup
            actual_images = count_backup_images(object_id, col)

            if actual_images <= 0:
                continue  # Can't diagnose without backup

            issue_type = None

            if input_images > 0 and input_images <= 5 and actual_images > 5:
                issue_type = "max5_truncated"
            elif result_pages == 0:
                issue_type = "zero_pages"
            elif input_images > 5 and result_pages < input_images:
                # VLM returned fewer pages than images sent
                issue_type = "vlm_mismatch"
            elif input_images <= 5 and actual_images > input_images and actual_images <= 5:
                # Mild truncation but not the max-5 bug
                pass

            if issue_type:
                issues.append({
                    "object_id": object_id,
                    "collection": col,
                    "group": group,
                    "issue_type": issue_type,
                    "input_images": input_images,
                    "result_pages": result_pages,
                    "actual_images": actual_images,
                    "result_file": str(result_file.name),
                })

    return issues


def print_summary(issues: list[dict]) -> None:
    """Print a human-readable summary table."""
    if not issues:
        print("Keine Truncation-Probleme gefunden.")
        return

    # Count by type
    type_counts = {}
    for issue in issues:
        t = issue["issue_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print("=" * 80)
    print("TRUNCATION DIAGNOSE")
    print("=" * 80)

    print(f"\nGefundene Probleme: {len(issues)}")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")

    print(f"\n{'Object-ID':20s} {'Sammlung':18s} {'Gruppe':16s} {'Typ':18s} "
          f"{'Sent':>5s} {'Pages':>5s} {'Actual':>6s} {'Diff':>5s}")
    print("-" * 98)

    for issue in sorted(issues, key=lambda x: (x["issue_type"], x["object_id"])):
        diff = issue["actual_images"] - issue["result_pages"]
        print(f"{issue['object_id']:20s} {issue['collection']:18s} "
              f"{issue['group']:16s} {issue['issue_type']:18s} "
              f"{issue['input_images']:5d} {issue['result_pages']:5d} "
              f"{issue['actual_images']:6d} {diff:+5d}")


def main():
    parser = argparse.ArgumentParser(description="Diagnose truncated transcriptions")
    parser.add_argument("--json", type=str, default=None,
                        help="Write JSON manifest of affected objects to this path")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all objects, not just problematic ones")
    args = parser.parse_args()

    issues = diagnose_all()
    print_summary(issues)

    if args.json:
        manifest = {
            "generated_by": "diagnose_truncation.py",
            "total_issues": len(issues),
            "issues": issues,
        }
        out_path = Path(args.json)
        out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nManifest geschrieben: {out_path}")

    # Exit with error code if issues found
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
