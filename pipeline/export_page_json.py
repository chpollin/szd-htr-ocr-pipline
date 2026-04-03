"""SZD-HTR Page-JSON Export: Pipeline-JSON + Layout-JSON + TEI → Page-JSON v0.2.

Merges pipeline outputs (transcription + optional layout + descriptive metadata)
into a single Page-JSON file per object, conforming to schemas/page-json-v0.2.json.

Specification: knowledge/htr-interchange-format.md
Schema:        schemas/page-json-v0.2.json

Usage:
    python pipeline/export_page_json.py o_szd.100 -c lebensdokumente
    python pipeline/export_page_json.py -c werke
    python pipeline/export_page_json.py --all
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import BACKUP_ROOT, COLLECTIONS, DATA_DIR, MODEL, RESULTS_BASE
from export_pagexml import load_ocr_and_layout
from tei_context import parse_tei_full_metadata

# --- Language normalization ---

LANG_MAP = {
    "deutsch": "de", "deutsch?": "de", "german": "de",
    "englisch": "en", "english": "en",
    "französisch": "fr", "franzoesisch": "fr", "french": "fr",
    "italienisch": "it", "italian": "it",
    "spanisch": "es", "spanish": "es",
    "jiddisch": "yi", "yiddish": "yi",
    "unbekannt": "und", "unknown": "und",
}


def _normalize_lang(lang_str: str) -> str:
    """Normalize language string to ISO 639-1/3 code."""
    if not lang_str:
        return "und"
    key = lang_str.strip().lower()
    return LANG_MAP.get(key, key[:3].lower())


# --- Document type mapping ---

OBJECTTYP_MAP = {
    "manuskript": "manuscript", "notizbuch": "notebook", "tagebuch": "diary",
    "typoskript": "typescript", "typoskriptdurchschlag": "typescript",
    "karte": "postcard", "postkarte": "postcard",
    "kalender": "calendar", "register": "register", "kontorbuch": "ledger",
    "korrekturfahne": "proof_sheet", "druckfahne": "proof_sheet",
    "zeitungsausschnitt": "newspaper_clipping",
    "konvolut": "mixed_materials", "briefumschlag": "letter",
}


def _map_document_type(objecttyp: str, classification: str, collection: str) -> str:
    """Map TEI objecttyp to Page-JSON document_type enum."""
    if collection == "korrespondenzen":
        return "letter"
    otyp = (objecttyp or "").lower()
    for key, val in OBJECTTYP_MAP.items():
        if key in otyp:
            return val
    classif = (classification or "").lower()
    if "rechtsdokumente" in classif or "finanzen" in classif:
        return "form"
    if "verlagsvertr" in classif:
        return "certificate"
    return "manuscript"


def _build_descriptive_metadata(full_meta: dict, backup_meta: dict) -> dict:
    """Build the descriptive_metadata block from full TEI + backup metadata."""
    dm = {}

    if full_meta.get("creators"):
        dm["creator"] = full_meta["creators"]

    if full_meta.get("subject"):
        dm["subject"] = full_meta["subject"]

    if full_meta.get("origin_place"):
        dm["origin_place"] = full_meta["origin_place"]

    if full_meta.get("extent"):
        dm["extent"] = full_meta["extent"]

    # Rights from backup metadata
    rights = backup_meta.get("rights", "")
    if rights:
        dm["rights"] = rights

    if full_meta.get("holding"):
        dm["holding"] = full_meta["holding"]

    if full_meta.get("provenance"):
        dm["provenance"] = full_meta["provenance"]

    # Physical description
    phys = {}
    if full_meta.get("writing_instrument"):
        phys["writing_instrument"] = full_meta["writing_instrument"]
    if full_meta.get("writing_material"):
        phys["writing_material"] = full_meta["writing_material"]
    if full_meta.get("hands"):
        phys["hands"] = full_meta["hands"]
    if full_meta.get("dimensions"):
        phys["dimensions"] = full_meta["dimensions"]
    if full_meta.get("binding"):
        phys["binding"] = full_meta["binding"]
    if full_meta.get("inscriptions"):
        phys["inscriptions"] = full_meta["inscriptions"]
    if phys:
        dm["physical_description"] = phys

    if full_meta.get("notes"):
        dm["notes"] = full_meta["notes"]

    return dm


def export_object(object_id: str, collection: str, force: bool = False) -> Path | None:
    """Export a single object to Page-JSON v0.2."""
    results_dir = RESULTS_BASE / collection
    out_path = results_dir / f"{object_id}_page.json"

    if out_path.exists() and not force:
        return None

    ocr_data, layout_data = load_ocr_and_layout(object_id, collection)
    if not ocr_data:
        print(f"  {object_id}: kein OCR-Ergebnis", file=sys.stderr)
        return None

    # Load backup metadata
    subdir = COLLECTIONS[collection]["subdir"]
    backup_meta_path = BACKUP_ROOT / subdir / object_id / "metadata.json"
    backup_meta = {}
    if backup_meta_path.exists():
        backup_meta = json.loads(backup_meta_path.read_text(encoding="utf-8"))

    # Load full TEI metadata
    pid = object_id.replace("o_szd.", "o:szd.")
    tei_file = DATA_DIR / COLLECTIONS[collection]["tei"]
    full_meta = parse_tei_full_metadata(tei_file, pid) or {}

    meta = ocr_data.get("metadata", {})
    result = ocr_data.get("result", {})
    qs = ocr_data.get("quality_signals", {})
    review = ocr_data.get("review")

    # --- Build source ---
    source = {
        "id": object_id,
        "title": full_meta.get("title") or meta.get("title", ""),
        "language": _normalize_lang(full_meta.get("language") or meta.get("language", "")),
        "collection": collection,
        "shelfmark": full_meta.get("signature", ""),
        "images": meta.get("images", []),
    }
    if full_meta.get("date"):
        source["date"] = full_meta["date"]

    doc_type = _map_document_type(
        full_meta.get("objecttyp", ""),
        full_meta.get("classification", ""),
        collection,
    )
    source["document_type"] = doc_type

    if full_meta.get("holding", {}).get("repository"):
        source["repository"] = full_meta["holding"]["repository"]

    # Descriptive metadata (v0.2)
    dm = _build_descriptive_metadata(full_meta, backup_meta)
    if dm:
        source["descriptive_metadata"] = dm

    # Project-specific
    source["additional"] = {"group": ocr_data.get("group", "")}
    ctx = ocr_data.get("context", "")
    if ctx:
        source["additional"]["context"] = ctx

    # --- Build provenance ---
    provenance = {
        "model": ocr_data.get("model", MODEL),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "google",
        "pipeline": "szd-htr",
        "prompt_layers": ["system", f"group_{ocr_data.get('group', 'handschrift')}",
                          "object_context"],
        "parameters": {"temperature": 0.1},
    }

    # --- Build pages ---
    pages = []
    ocr_pages = result.get("pages", [])
    layout_pages = {}
    if layout_data:
        for lp in layout_data.get("pages", []):
            layout_pages[lp.get("page", 0)] = lp

    for p in ocr_pages:
        page_num = p.get("page", 1)
        page_obj = {
            "page": page_num,
            "type": p.get("type", "content"),
            "text": p.get("transcription", ""),
        }
        if p.get("notes"):
            page_obj["notes"] = p["notes"]

        # Merge layout
        lp = layout_pages.get(page_num)
        if lp:
            if lp.get("image_filename"):
                page_obj["image"] = lp["image_filename"]
            if lp.get("image_width_px"):
                page_obj["image_width"] = lp["image_width_px"]
            if lp.get("image_height_px"):
                page_obj["image_height"] = lp["image_height_px"]
            if lp.get("regions"):
                page_obj["regions"] = lp["regions"]

        pages.append(page_obj)

    # --- Assemble Page-JSON ---
    page_json = {
        "page_json": "0.2",
        "source": source,
        "provenance": provenance,
        "pages": pages,
    }

    if result.get("confidence"):
        page_json["confidence"] = result["confidence"]
    if result.get("confidence_notes"):
        page_json["confidence_notes"] = result["confidence_notes"]

    # Quality signals
    if qs:
        page_json["quality"] = {
            "needs_review": qs.get("needs_review", False),
            "needs_review_reasons": qs.get("needs_review_reasons", []),
            "total_chars": qs.get("total_chars", 0),
            "total_words": qs.get("total_words", 0),
            "language_detected": qs.get("language_detected", ""),
            "language_match": qs.get("language_match", True),
        }

    # Review
    if review:
        page_json["review"] = review

    # Write
    out_path.write_text(
        json.dumps(page_json, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Export Page-JSON v0.2")
    parser.add_argument("object_id", nargs="?", help="Object ID (e.g. o_szd.100)")
    parser.add_argument("-c", "--collection", help="Collection name")
    parser.add_argument("--all", action="store_true", help="Export all collections")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    if args.object_id and args.collection:
        path = export_object(args.object_id, args.collection, args.force)
        if path:
            print(f"Exported: {path}")
        else:
            print(f"Skipped or failed: {args.object_id}")
    elif args.collection or args.all:
        collections = list(COLLECTIONS.keys()) if args.all else [args.collection]
        total = 0
        for coll in collections:
            results_dir = RESULTS_BASE / coll
            for f in sorted(results_dir.glob(f"o_szd.*_{MODEL}.json")):
                obj_id = f.stem.replace(f"_{MODEL}", "")
                path = export_object(obj_id, coll, args.force)
                if path:
                    total += 1
                    print(f"  {path.name}")
        print(f"\n{total} Page-JSON files exported.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
