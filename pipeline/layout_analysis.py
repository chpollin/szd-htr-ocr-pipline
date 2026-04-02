"""SZD-HTR Layout-Analyse: VLM-basierte Erkennung von Textregionen und Bounding Boxes."""

import argparse
import json
import re
import struct
import sys
import time
from pathlib import Path

from google import genai

from config import (
    BACKUP_ROOT, BATCH_DELAY, COLLECTIONS, GOOGLE_API_KEY,
    MODEL, PROMPTS_DIR, results_dir_for,
)
from transcribe import (
    discover_objects, load_images, parse_api_response, resolve_context,
)


# --- Layout Prompt ---

def _load_layout_prompt() -> str:
    """Load the layout analysis system prompt."""
    path = PROMPTS_DIR / "layout_system.md"
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    if not blocks:
        return text.strip()
    return blocks[0].strip()


LAYOUT_SYSTEM_PROMPT = _load_layout_prompt()


# --- Image Dimensions ---

def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Extract width and height from JPEG data without PIL."""
    i = 2  # skip SOI marker
    while i < len(data) - 1:
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        if marker == 0xD9:  # EOI
            break
        if marker in (0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0x01):
            i += 2
            continue
        if i + 3 >= len(data):
            break
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        # SOF markers (baseline, progressive, etc.)
        if marker in (0xC0, 0xC1, 0xC2):
            if i + 9 <= len(data):
                height = struct.unpack(">H", data[i + 5 : i + 7])[0]
                width = struct.unpack(">H", data[i + 7 : i + 9])[0]
                return width, height
        i += 2 + length
    return 0, 0


# --- Layout Analysis ---

def analyze_page_layout(
    image_data: bytes,
    image_name: str,
    context_hint: str,
) -> dict:
    """Analyze layout of a single page image via VLM.

    Returns dict with 'regions' list or 'raw' on parse failure.
    """
    user_prompt = (
        f"{context_hint}\n\n"
        f"Analysiere das Layout dieses Dokumentbilds ({image_name}). "
        "Identifiziere alle Textregionen mit Typ, Position und Lesereihenfolge."
    )

    parts = [
        genai.types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
        user_prompt,
    ]

    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = None
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=parts,
                config=genai.types.GenerateContentConfig(
                    system_instruction=LAYOUT_SYSTEM_PROMPT,
                    temperature=0.1,
                ),
            )
            break
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str or "rate" in err_str:
                wait = (2 ** attempt) * 5
                print(f"    RATE LIMIT (Versuch {attempt + 1}/4): warte {wait}s...")
                time.sleep(wait)
            else:
                print(f"    FEHLER bei API-Aufruf: {e}")
                return {"raw": str(e)}

    if response is None:
        return {"raw": "Rate limit nach 4 Versuchen"}

    result_text = response.text
    if not result_text:
        return {"regions": []}

    parsed, log = parse_api_response(result_text, image_name)
    for msg in log:
        print(f"    {msg}")

    return parsed


def _validate_regions(regions: list[dict], img_w: int = 0, img_h: int = 0) -> list[dict]:
    """Validate and normalize region data. Assign IDs if missing.

    If bbox values exceed 100, assume pixel coordinates and convert to percent.
    """
    valid = []
    for i, r in enumerate(regions):
        region = {
            "id": r.get("id", f"r{i + 1}"),
            "type": r.get("type", "paragraph"),
            "bbox": r.get("bbox", [0, 0, 100, 100]),
            "reading_order": r.get("reading_order", i + 1),
            "lines": r.get("lines", 0),
            "label": r.get("label", ""),
        }
        # Normalize bbox
        bbox = region["bbox"]
        if isinstance(bbox, list) and len(bbox) == 4:
            vals = [float(v) for v in bbox]
            # Detect pixel coordinates: if any position/size value > 100, convert
            if any(v > 100 for v in vals) and img_w > 0 and img_h > 0:
                # Assume [x_px, y_px, w_px, h_px]
                vals = [
                    vals[0] / img_w * 100,
                    vals[1] / img_h * 100,
                    vals[2] / img_w * 100,
                    vals[3] / img_h * 100,
                ]
            region["bbox"] = [round(max(0, min(100, v)), 1) for v in vals]
        else:
            region["bbox"] = [0, 0, 100, 100]
        # Validate type
        if region["type"] not in ("paragraph", "heading", "list", "table", "marginalia"):
            region["type"] = "paragraph"
        valid.append(region)
    return valid


def analyze_object_layout(
    object_id: str,
    collection: str,
    max_images: int = 0,
    force: bool = False,
) -> tuple[bool, Path | None]:
    """Analyze layout for all pages of an object. Returns (success, output_path)."""
    results_dir = results_dir_for(collection)
    out_path = results_dir / f"{object_id}_layout.json"

    if out_path.exists() and not force:
        return True, out_path

    # Context hint for the VLM
    group, context, _ = resolve_context(object_id, collection)
    context_hint = f"Dokumenttyp: {group}. Sammlung: {collection}."

    # Load images
    try:
        images = load_images(object_id, collection, max_images)
    except FileNotFoundError as e:
        print(f"  FEHLER: {e}")
        return False, None

    print(f"  {len(images)} Bilder, Gruppe: {group}")

    pages = []
    for i, (img_name, img_bytes) in enumerate(images):
        print(f"    Seite {i + 1}/{len(images)}: {img_name} ...", end=" ", flush=True)

        width, height = _jpeg_dimensions(img_bytes)
        result = analyze_page_layout(img_bytes, img_name, context_hint)

        regions_raw = result.get("regions", [])
        regions = _validate_regions(regions_raw, width, height)

        pages.append({
            "page": i + 1,
            "image_filename": img_name,
            "image_width_px": width,
            "image_height_px": height,
            "regions": regions,
        })

        print(f"{len(regions)} Regionen")

        # Delay between pages (same image = same rate limit)
        if i < len(images) - 1:
            time.sleep(BATCH_DELAY)

    output = {
        "object_id": object_id,
        "collection": collection,
        "model": MODEL,
        "pages": pages,
    }

    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Gespeichert: {out_path}")
    return True, out_path


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="VLM-basierte Layout-Analyse fuer SZD-HTR Objekte"
    )
    parser.add_argument("object_id", nargs="?", help="Einzelnes Objekt (z.B. o_szd.100)")
    parser.add_argument("-c", "--collection", help="Sammlung", choices=COLLECTIONS.keys())
    parser.add_argument("--all", action="store_true", help="Alle Sammlungen")
    parser.add_argument("--limit", type=int, default=0, help="Max. Objekte pro Sammlung")
    parser.add_argument("--max-images", type=int, default=0, help="Max. Bilder pro Objekt")
    parser.add_argument("--force", action="store_true", help="Bestehende Ergebnisse ueberschreiben")
    parser.add_argument("--dry-run", action="store_true", help="Nur auflisten, nichts ausfuehren")
    parser.add_argument("--delay", type=float, default=None, help="Delay zwischen Objekten (Sekunden)")
    args = parser.parse_args()

    if args.delay is not None:
        import config
        config.BATCH_DELAY = args.delay

    # Build object list
    objects = []
    if args.object_id:
        if not args.collection:
            print("FEHLER: --collection erforderlich bei Einzelobjekt")
            sys.exit(1)
        objects = [{"object_id": args.object_id, "collection": args.collection}]
    elif args.all:
        for col in COLLECTIONS:
            objects.extend(discover_objects(col))
    elif args.collection:
        objects = discover_objects(args.collection)
    else:
        parser.print_help()
        sys.exit(1)

    if args.limit:
        objects = objects[:args.limit]

    if args.dry_run:
        print(f"{'Object-ID':<20} {'Sammlung':<20}")
        print("-" * 40)
        for obj in objects:
            print(f"{obj['object_id']:<20} {obj['collection']:<20}")
        print(f"\n{len(objects)} Objekte")
        return

    print(f"Layout-Analyse: {len(objects)} Objekte")
    print("=" * 60)

    done, skipped, failed = 0, 0, 0
    for i, obj in enumerate(objects):
        oid = obj["object_id"]
        col = obj["collection"]
        out_path = results_dir_for(col) / f"{oid}_layout.json"

        if out_path.exists() and not args.force:
            skipped += 1
            print(f"[{i + 1}/{len(objects)}] {oid} -- uebersprungen")
            continue

        print(f"[{i + 1}/{len(objects)}] {oid}")
        success, _ = analyze_object_layout(oid, col, args.max_images, args.force)
        if success:
            done += 1
        else:
            failed += 1

        if i < len(objects) - 1:
            time.sleep(BATCH_DELAY)

    print("=" * 60)
    print(f"Fertig: {done} analysiert, {skipped} uebersprungen, {failed} fehlgeschlagen")


if __name__ == "__main__":
    main()
