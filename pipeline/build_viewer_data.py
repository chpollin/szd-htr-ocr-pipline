"""Build catalog.json + data/{collection}.json from enriched result files."""

import json
import re

from config import COLLECTIONS, DATA_DIR as TEI_DIR, GROUP_LABELS, PROJECT_ROOT, RESULTS_BASE, RESULTS_DIR
from tei_context import parse_tei_for_object

DOCS_DIR = PROJECT_ROOT / "docs"
CATALOG_PATH = DOCS_DIR / "catalog.json"
DATA_DIR = DOCS_DIR / "data"
GAMS_BASE = "https://gams.uni-graz.at/"


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
            })
        col_path = DATA_DIR / f"{col}.json"
        col_path.write_text(
            json.dumps({"objects": col_objects}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  {col}: {col_path} ({len(col_objects)} Objekte)")

    print(f"Gesamt: {len(objects)} Objekte, {len(collections)} Sammlungen")


if __name__ == "__main__":
    build()
