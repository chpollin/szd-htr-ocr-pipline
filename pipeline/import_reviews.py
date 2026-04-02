"""Import expert reviews exported from the SZD-HTR frontend back into pipeline JSONs.

Handles two export formats:
  1. GT Review exports ({object_id}_gt.json) — updates GT draft files
  2. Regular edit exports (source: "szd-htr-viewer") — updates result files

Usage:
  python pipeline/import_reviews.py path/to/export1.json path/to/export2.json
  python pipeline/import_reviews.py path/to/*.json --dry-run
  python pipeline/import_reviews.py path/to/export.json --reviewer "Name"
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from config import COLLECTIONS, RESULTS_BASE

GT_DIR = RESULTS_BASE / "groundtruth"
DEFAULT_REVIEWER = "Christopher Pollin"


def detect_format(data: dict) -> str:
    """Detect whether the export is a GT review or a regular edit."""
    if "expert_verified" in data and "models" in data:
        return "gt"
    if data.get("source") == "szd-htr-viewer":
        return "edit"
    raise ValueError(
        "Unbekanntes Export-Format: weder GT-Review (expert_verified+models) "
        "noch regulaerer Edit (source='szd-htr-viewer')."
    )


def import_gt_review(data: dict, *, reviewer: str, dry_run: bool) -> None:
    """Import a GT review export into the corresponding GT draft file."""
    object_id = data.get("object_id", "")
    if not object_id:
        print(f"  FEHLER: Kein object_id im Export.")
        return

    draft_path = GT_DIR / f"{object_id}_gt_draft.json"
    if not draft_path.exists():
        print(f"  FEHLER: GT-Draft nicht gefunden: {draft_path}")
        return

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    export_pages = {p["page"]: p for p in data.get("pages", [])}

    updated = 0
    approved = 0
    for draft_page in draft.get("pages", []):
        page_num = draft_page.get("page")
        export_page = export_pages.get(page_num)
        if not export_page:
            continue

        # Update transcription if expert chose a different variant
        if export_page.get("transcription") != draft_page.get("transcription"):
            draft_page["transcription"] = export_page["transcription"]
            updated += 1

        # Write review fields
        draft_page["approved"] = export_page.get("approved", False)
        draft_page["expert_edited"] = export_page.get("expert_edited", False)
        if "source" in export_page:
            draft_page["source"] = export_page["source"]

        if export_page.get("approved"):
            approved += 1

    # Top-level review status
    draft["expert_verified"] = data.get("expert_verified", False)
    draft["reviewed_by"] = data.get("reviewed_by", reviewer)
    draft["reviewed_at"] = data.get("reviewed_at")

    total_content = sum(1 for p in draft.get("pages", []) if p.get("type") == "content")
    status = "VERIFIZIERT" if draft["expert_verified"] else "TEILWEISE"

    print(f"  {object_id}: {approved}/{total_content} Content-Seiten approved, "
          f"{updated} Transkriptionen geaendert -- {status}")

    if dry_run:
        print(f"  [DRY-RUN] Wuerde schreiben: {draft_path}")
        return

    # Backup and write
    backup_path = draft_path.with_suffix(".json.bak")
    shutil.copy2(draft_path, backup_path)
    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Geschrieben: {draft_path} (Backup: {backup_path.name})")


def import_regular_edit(data: dict, *, reviewer: str, dry_run: bool) -> None:
    """Import a regular edit export into the corresponding result file."""
    # The export's object_id may or may not include the model suffix.
    # Frontend strips it (e.g. "o_szd.100"), but model is in a separate field.
    object_id = data.get("object_id", "")
    collection = data.get("collection", "")
    model = data.get("model", "")

    if not object_id or not collection:
        print(f"  FEHLER: object_id oder collection fehlt im Export.")
        return

    if collection not in COLLECTIONS:
        print(f"  FEHLER: Unbekannte Sammlung: {collection}")
        return

    # Try exact match first, then reconstruct with model suffix
    col_dir = RESULTS_BASE / collection
    result_path = col_dir / f"{object_id}.json"
    if not result_path.exists() and model:
        result_path = col_dir / f"{object_id}_{model}.json"
    if not result_path.exists():
        # Fallback: search for any file starting with the object_id
        candidates = list(col_dir.glob(f"{object_id}_*.json"))
        candidates = [c for c in candidates if not c.stem.endswith(("_consensus", "_layout", "_gt_draft"))]
        if len(candidates) == 1:
            result_path = candidates[0]
        elif len(candidates) > 1:
            print(f"  FEHLER: Mehrere Kandidaten fuer {object_id}: {[c.name for c in candidates]}")
            return
        else:
            print(f"  FEHLER: Ergebnis-Datei nicht gefunden: {col_dir / object_id}_*.json")
            return

    result = json.loads(result_path.read_text(encoding="utf-8"))
    result_pages = result.get("result", {}).get("pages", [])

    # Build lookup by page number
    result_page_map = {}
    for rp in result_pages:
        result_page_map[rp.get("page")] = rp

    edited_pages = []
    for export_page in data.get("pages", []):
        if not export_page.get("edited"):
            continue
        page_num = export_page.get("page")
        rp = result_page_map.get(page_num)
        if not rp:
            print(f"  WARNUNG: Seite {page_num} nicht im Ergebnis-JSON gefunden, uebersprungen.")
            continue

        rp["transcription"] = export_page.get("transcription", "")
        rp["notes"] = export_page.get("notes", "")
        edited_pages.append(page_num)

    # Add review metadata
    result["review"] = {
        "status": "approved",
        "edited_pages": edited_pages,
        "reviewed_by": reviewer,
        "reviewed_at": data.get("exported_at"),
    }

    print(f"  {object_id}: {len(edited_pages)} Seite(n) aktualisiert -- APPROVED")

    if dry_run:
        print(f"  [DRY-RUN] Wuerde schreiben: {result_path}")
        return

    # Backup and write
    backup_path = result_path.with_suffix(".json.bak")
    shutil.copy2(result_path, backup_path)
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Geschrieben: {result_path} (Backup: {backup_path.name})")


def main():
    parser = argparse.ArgumentParser(
        description="Import expert reviews from frontend exports into pipeline JSONs."
    )
    parser.add_argument(
        "files", nargs="+", type=Path,
        help="Exportierte JSON-Dateien aus dem Frontend",
    )
    parser.add_argument(
        "--reviewer", default=DEFAULT_REVIEWER,
        help=f"Name des Reviewers (Default: {DEFAULT_REVIEWER})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Zeigt was passieren wuerde, ohne zu schreiben",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY-RUN Modus ===\n")

    success = 0
    errors = 0

    for filepath in args.files:
        if not filepath.exists():
            print(f"FEHLER: Datei nicht gefunden: {filepath}")
            errors += 1
            continue

        print(f"Importiere: {filepath.name}")
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            fmt = detect_format(data)

            if fmt == "gt":
                import_gt_review(data, reviewer=args.reviewer, dry_run=args.dry_run)
            else:
                import_regular_edit(data, reviewer=args.reviewer, dry_run=args.dry_run)

            success += 1
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  FEHLER: {e}")
            errors += 1

    print(f"\nFertig: {success} importiert, {errors} Fehler")
    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
