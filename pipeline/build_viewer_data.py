"""Build docs/data.json from enriched result files for the viewer."""

import json

from config import GROUP_LABELS, PROJECT_ROOT, RESULTS_BASE, RESULTS_DIR

OUTPUT_PATH = PROJECT_ROOT / "docs" / "data.json"


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

        # Filter out calibration card pages (page 3 of 3 is often a color chart)
        # Keep all pages from the result but match to available images
        page_images = all_images[:len(pages)] if all_images else []

        obj = {
            "id": result_file.stem,
            "collection": data["collection"],
            "label": meta.get("title", "").split(",")[0][:40],
            "group": group_letter,
            "groupLabel": group_label,
            "pid": pid,
            "title": meta.get("title", ""),
            "lang": meta.get("language", ""),
            "model": data.get("model", ""),
            "images": page_images,
            "pages": pages,
            "confidence": result.get("confidence", ""),
            "confidenceNotes": result.get("confidence_notes", ""),
        }
        objects.append(obj)

    # Sort: by collection, then by group
    objects.sort(key=lambda o: (o["collection"], o["group"]))

    collections = sorted(set(o["collection"] for o in objects))

    output = {
        "objects": objects,
        "collections": collections,
    }

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Geschrieben: {OUTPUT_PATH} ({len(objects)} Objekte, {len(collections)} Sammlungen)")


if __name__ == "__main__":
    build()
