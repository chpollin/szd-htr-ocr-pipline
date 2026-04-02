"""Build catalog.json + data/{collection}.json from enriched result files."""

import json
import re

from config import COLLECTIONS, DATA_DIR as TEI_DIR, GROUP_LABELS, PROJECT_ROOT, RESULTS_BASE, RESULTS_DIR
from tei_context import parse_tei_for_object

DOCS_DIR = PROJECT_ROOT / "docs"
CATALOG_PATH = DOCS_DIR / "catalog.json"
DATA_DIR = DOCS_DIR / "data"
GAMS_BASE = "https://gams.uni-graz.at/"


def load_consensus(result_file) -> dict | None:
    """Load consensus data for an object if it exists."""
    consensus_file = result_file.parent / (
        result_file.stem.split("_gemini")[0].split("_claude")[0] + "_consensus.json"
    )
    if not consensus_file.exists():
        return None
    try:
        data = json.loads(consensus_file.read_text(encoding="utf-8"))
        cons = data.get("consensus", {})
        judge_pages = data.get("judge_data", {}).get("pages", [])
        # Merge transcription texts from judge_data into consensus pages
        pages = []
        for cp in cons.get("pages", []):
            page_entry = {
                "page": cp.get("page", 0),
                "cer": cp.get("cer"),
                "cer_orderless": cp.get("cer_orderless"),
                "agreement": cp.get("agreement", ""),
                "type": cp.get("type", "content"),
            }
            # Find matching judge page for transcription texts
            jp = next((j for j in judge_pages if j.get("page") == cp.get("page")), None)
            if jp:
                page_entry["transcription_a"] = jp.get("transcription_a", "")
                page_entry["transcription_b"] = jp.get("transcription_b", "")
            pages.append(page_entry)
        return {
            "category": cons.get("category", ""),
            "effective_cer": cons.get("effective_cer", 0),
            "overall_cer": cons.get("overall_cer", 0),
            "word_overlap": cons.get("word_overlap", 0),
            "content_pages": cons.get("content_pages", 0),
            "skipped_pages": cons.get("skipped_pages", 0),
            "model_a": data.get("model_a", ""),
            "model_b": data.get("model_b", ""),
            "pages": pages,
        }
    except (json.JSONDecodeError, KeyError):
        return None


def extract_signature(title: str) -> tuple[str, str]:
    """Extract signature from title. Returns (title_clean, signature)."""
    parts = title.rsplit(",", 1)
    if len(parts) == 2 and parts[1].strip().startswith("SZ-"):
        return parts[0].strip(), parts[1].strip()
    return title, ""


def compute_verification(pages: list[dict]) -> dict:
    """Compute verification metrics from transcription text."""
    uncertain = 0
    illegible = 0
    total_chars = 0
    empty_pages = 0

    for page in pages:
        text = page.get("transcription", "")
        if not text.strip():
            empty_pages += 1
            continue
        total_chars += len(text)
        uncertain += len(re.findall(r"\[\?\]", text))
        illegible += len(re.findall(r"\[\.\.\..*?\]", text))

    non_empty = len(pages) - empty_pages
    return {
        "uncertainCount": uncertain,
        "illegibleCount": illegible,
        "totalChars": total_chars,
        "emptyPages": empty_pages,
        "avgCharsPerPage": round(total_chars / non_empty) if non_empty else 0,
    }


def build():
    objects = []

    # Scan all result directories: results/test/, results/lebensdokumente/, etc.
    result_files = sorted(RESULTS_DIR.glob("*.json"))
    for subdir in sorted(RESULTS_BASE.iterdir()):
        if subdir.is_dir() and subdir != RESULTS_DIR:
            result_files.extend(sorted(subdir.glob("*.json")))

    for result_file in result_files:
        # Skip consensus files — they are not transcription results
        if result_file.stem.endswith("_consensus"):
            continue

        data = json.loads(result_file.read_text(encoding="utf-8"))

        # Skip non-enriched legacy results (no "collection" key)
        if "collection" not in data:
            continue

        group_key = data.get("group", "")
        group_letter, group_label = GROUP_LABELS.get(group_key, ("?", group_key))

        meta = data.get("metadata", {})
        result = data.get("result", {})
        pid = data["object_id"].replace("o_szd.", "o:szd.")

        # Determine which GAMS images to use per page
        all_images = meta.get("images", [])
        pages = result.get("pages", [])
        page_images = all_images[:len(pages)] if all_images else []

        full_title = meta.get("title", "")
        title_clean, signature = extract_signature(full_title)

        # Get classification + objecttyp from TEI
        collection = data["collection"]
        tei_file = TEI_DIR / COLLECTIONS[collection]["tei"]
        tei_meta = parse_tei_for_object(tei_file, pid) or {}
        classification = tei_meta.get("classification", "")
        objecttyp = tei_meta.get("objecttyp", "")
        # Fallback for Korrespondenzen (no TEI classification) — parse title
        if not objecttyp and collection == "korrespondenzen":
            tl = full_title.lower()
            if "ansichtspostkarte" in tl:
                objecttyp = "Ansichtspostkarte"
            elif "postkarte" in tl:
                objecttyp = "Postkarte"
            elif "telegramm" in tl:
                objecttyp = "Telegramm"
            else:
                objecttyp = "Brief"
        if not classification and collection == "korrespondenzen":
            classification = "Korrespondenz"

        verification = compute_verification(pages)
        verification["vlmConfidence"] = result.get("confidence", "")

        # quality_signals from enriched JSON (added by transcribe.py or backfill)
        qs = data.get("quality_signals", {})

        # Consensus data (from verify.py)
        consensus = load_consensus(result_file)

        obj = {
            "id": result_file.stem,
            "collection": data["collection"],
            "label": title_clean[:40],
            "group": group_letter,
            "groupLabel": group_label,
            "pid": pid,
            "title": full_title,
            "titleClean": title_clean,
            "signature": signature,
            "classification": classification,
            "objecttyp": objecttyp,
            "lang": meta.get("language", ""),
            "model": data.get("model", ""),
            "thumbnail": GAMS_BASE + pid + "/THUMBNAIL",
            "images": page_images,
            "pages": pages,
            "confidence": result.get("confidence", ""),
            "confidenceNotes": result.get("confidence_notes", ""),
            "pageCount": len(pages),
            "verification": verification,
            "needsReview": qs.get("needs_review", False),
            "needsReviewReasons": qs.get("needs_review_reasons", []),
            "blankPages": qs.get("blank_pages", 0),
            "contentPages": qs.get("content_pages", 0),
            "quality_signals": {
                "total_chars": qs.get("total_chars", 0),
                "total_words": qs.get("total_words", 0),
                "total_pages": qs.get("total_pages", 0),
                "empty_pages": qs.get("empty_pages", 0),
                "blank_pages": qs.get("blank_pages", 0),
                "content_pages": qs.get("content_pages", 0),
                "color_chart_pages": qs.get("color_chart_pages", 0),
                "chars_per_page": qs.get("chars_per_page", []),
                "chars_per_page_median": qs.get("chars_per_page_median", 0),
                "marker_uncertain_count": qs.get("marker_uncertain_count", 0),
                "marker_illegible_count": qs.get("marker_illegible_count", 0),
                "marker_density": qs.get("marker_density", 0),
                "dwr_score": qs.get("dwr_score", 0),
                "duplicate_page_pairs": qs.get("duplicate_page_pairs", []),
                "language_expected": qs.get("language_expected", ""),
                "language_detected": qs.get("language_detected", ""),
                "language_match": qs.get("language_match", True),
                "page_length_anomalies": qs.get("page_length_anomalies", []),
                "needs_review": qs.get("needs_review", False),
                "needs_review_reasons": qs.get("needs_review_reasons", []),
            },
            "consensus": consensus,  # None if no consensus file exists
        }
        objects.append(obj)

    # Sort: by collection, then by group
    objects.sort(key=lambda o: (o["collection"], o["group"]))

    collections = sorted(set(o["collection"] for o in objects))

    # --- catalog.json: lightweight metadata only ---
    catalog_objects = []
    for obj in objects:
        catalog_objects.append({
            "id": obj["id"],
            "collection": obj["collection"],
            "label": obj["label"],
            "group": obj["group"],
            "groupLabel": obj["groupLabel"],
            "pid": obj["pid"],
            "title": obj["title"],
            "titleClean": obj["titleClean"],
            "signature": obj["signature"],
            "classification": obj["classification"],
            "objecttyp": obj["objecttyp"],
            "lang": obj["lang"],
            "model": obj["model"],
            "confidence": obj["confidence"],
            "pageCount": obj["pageCount"],
            "thumbnail": obj["thumbnail"],
            "verification": obj["verification"],
            "needsReview": obj["needsReview"],
            "needsReviewReasons": obj["needsReviewReasons"],
            "blankPages": obj.get("blankPages", 0),
            "contentPages": obj.get("contentPages", 0),
            "dwrScore": obj.get("quality_signals", {}).get("dwr_score", 0),
            "consensusCategory": obj["consensus"]["category"] if obj.get("consensus") else None,
            "consensusCer": obj["consensus"]["effective_cer"] if obj.get("consensus") else None,
        })

    catalog = {"objects": catalog_objects, "collections": collections}
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Katalog: {CATALOG_PATH} ({len(catalog_objects)} Objekte)")

    # --- data/{collection}.json: full objects with transcription text ---
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for col in collections:
        col_objects = []
        for obj in objects:
            if obj["collection"] != col:
                continue
            col_objects.append({
                "id": obj["id"],
                "images": obj["images"],
                "pages": obj["pages"],
                "confidence": obj["confidence"],
                "confidenceNotes": obj["confidenceNotes"],
                "verification": obj["verification"],
                "quality_signals": obj.get("quality_signals", {}),
                "consensus": obj.get("consensus"),
            })
        col_path = DATA_DIR / f"{col}.json"
        col_path.write_text(
            json.dumps({"objects": col_objects}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  {col}: {col_path} ({len(col_objects)} Objekte)")

    # --- groundtruth.json: GT drafts for expert review ---
    gt_dir = RESULTS_BASE / "groundtruth"
    gt_objects = []
    if gt_dir.exists():
        for gt_file in sorted(gt_dir.glob("*_gt_draft.json")):
            gt_data = json.loads(gt_file.read_text(encoding="utf-8"))
            oid = gt_data.get("object_id", "")
            # Find the matching result ID
            result_id = None
            for obj in objects:
                if obj["id"].startswith(oid + "_"):
                    result_id = obj["id"]
                    break
            gt_objects.append({
                "id": result_id or oid,
                "object_id": oid,
                "collection": gt_data.get("collection", ""),
                "group": gt_data.get("group", ""),
                "title": gt_data.get("title", ""),
                "models": gt_data.get("models", {}),
                "pages": gt_data.get("pages", []),
                "merge_stats": gt_data.get("merge_stats", {}),
                "expert_verified": gt_data.get("expert_verified", False),
                "reviewed_by": gt_data.get("reviewed_by"),
                "reviewed_at": gt_data.get("reviewed_at"),
            })

    if gt_objects:
        gt_path = DATA_DIR / "groundtruth.json"
        gt_path.write_text(
            json.dumps({"objects": gt_objects}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  Ground Truth: {gt_path} ({len(gt_objects)} Objekte)")

        # Add GT status to catalog
        gt_ids = {g["id"] for g in gt_objects}
        for cat_obj in catalog_objects:
            cat_obj["hasGT"] = cat_obj["id"] in gt_ids

        # Re-write catalog with GT flags
        CATALOG_PATH.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  Katalog mit GT-Flags aktualisiert")

    print(f"Gesamt: {len(objects)} Objekte, {len(collections)} Sammlungen, {len(gt_objects)} GT-Drafts")


if __name__ == "__main__":
    build()
