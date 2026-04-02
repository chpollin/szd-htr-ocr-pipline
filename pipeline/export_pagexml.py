"""SZD-HTR PAGE XML Export: Merged OCR-Transkription + Layout-Regionen → PAGE XML 2019."""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from config import COLLECTIONS, MODEL, RESULTS_BASE, results_dir_for
from transcribe import discover_objects

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
ET.register_namespace("", PAGE_NS)


# --- Data Loading ---

def _find_ocr_file(results_dir: Path, object_id: str) -> Path | None:
    """Find the OCR result file for an object."""
    candidates = sorted(results_dir.glob(f"{object_id}_gemini*.json"))
    if candidates:
        return candidates[0]
    # Fallback: any non-layout, non-consensus JSON
    for f in sorted(results_dir.glob(f"{object_id}_*.json")):
        if "_layout" not in f.stem and "_consensus" not in f.stem:
            return f
    return None


def load_ocr_and_layout(object_id: str, collection: str) -> tuple[dict | None, dict | None]:
    """Load OCR result and layout analysis for an object."""
    results_dir = results_dir_for(collection)

    ocr_path = _find_ocr_file(results_dir, object_id)
    layout_path = results_dir / f"{object_id}_layout.json"

    ocr_data = None
    if ocr_path and ocr_path.exists():
        ocr_data = json.loads(ocr_path.read_text(encoding="utf-8"))

    layout_data = None
    if layout_path.exists():
        layout_data = json.loads(layout_path.read_text(encoding="utf-8"))

    return ocr_data, layout_data


# --- Text Alignment ---

def _split_text_to_regions(transcription: str, regions: list[dict]) -> dict[str, str]:
    """Split OCR transcription text across layout regions by estimated line count.

    Returns dict mapping region id → text.
    """
    if not regions or not transcription:
        return {}

    # Sort by reading order
    sorted_regions = sorted(regions, key=lambda r: r.get("reading_order", 0))

    lines = transcription.split("\n")
    total_estimated = sum(r.get("lines", 1) for r in sorted_regions)
    if total_estimated == 0:
        total_estimated = len(sorted_regions)

    result = {}
    line_idx = 0
    for region in sorted_regions:
        est_lines = region.get("lines", 1)
        # Proportional allocation based on estimated lines
        if total_estimated > 0:
            share = max(1, round(len(lines) * est_lines / total_estimated))
        else:
            share = max(1, len(lines) // len(sorted_regions))

        region_lines = lines[line_idx : line_idx + share]
        result[region["id"]] = "\n".join(region_lines)
        line_idx += share

    # Assign remaining lines to last region
    if line_idx < len(lines) and sorted_regions:
        last_id = sorted_regions[-1]["id"]
        remaining = "\n".join(lines[line_idx:])
        if result.get(last_id):
            result[last_id] += "\n" + remaining
        else:
            result[last_id] = remaining

    return result


# --- Coordinate Conversion ---

def _bbox_to_coords(bbox: list[float], img_w: int, img_h: int) -> str:
    """Convert [x%, y%, w%, h%] to PAGE XML polygon points string."""
    x_pct, y_pct, w_pct, h_pct = bbox
    x1 = round(x_pct / 100 * img_w)
    y1 = round(y_pct / 100 * img_h)
    x2 = round((x_pct + w_pct) / 100 * img_w)
    y2 = round((y_pct + h_pct) / 100 * img_h)
    # Clamp to image bounds
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img_w, x2), min(img_h, y2)
    return f"{x1},{y1} {x2},{y1} {x2},{y2} {x1},{y2}"


# --- Region Type Mapping ---

REGION_TYPE_MAP = {
    "paragraph": "paragraph",
    "heading": "heading",
    "list": "list-label",
    "table": "other",
    "marginalia": "marginalia",
}


# --- PAGE XML Generation ---

def generate_page_xml(
    page_num: int,
    image_filename: str,
    img_w: int,
    img_h: int,
    regions: list[dict],
    text_map: dict[str, str],
) -> ET.Element:
    """Generate a PAGE XML tree for a single page."""
    pcgts = ET.Element(f"{{{PAGE_NS}}}PcGts")

    # Metadata
    metadata = ET.SubElement(pcgts, f"{{{PAGE_NS}}}Metadata")
    creator = ET.SubElement(metadata, f"{{{PAGE_NS}}}Creator")
    creator.text = "szd-htr-pipeline"
    created = ET.SubElement(metadata, f"{{{PAGE_NS}}}Created")
    created.text = datetime.now(timezone.utc).isoformat()

    # Page
    page = ET.SubElement(pcgts, f"{{{PAGE_NS}}}Page")
    page.set("imageFilename", image_filename)
    page.set("imageWidth", str(img_w))
    page.set("imageHeight", str(img_h))

    if not regions:
        return pcgts

    # Reading order
    sorted_regions = sorted(regions, key=lambda r: r.get("reading_order", 0))
    ro = ET.SubElement(page, f"{{{PAGE_NS}}}ReadingOrder")
    og = ET.SubElement(ro, f"{{{PAGE_NS}}}OrderedGroup")
    og.set("id", "ro")
    for i, region in enumerate(sorted_regions):
        ref = ET.SubElement(og, f"{{{PAGE_NS}}}RegionRefIndexed")
        ref.set("regionRef", region["id"])
        ref.set("index", str(i))

    # Text regions
    for region in sorted_regions:
        rid = region["id"]
        rtype = REGION_TYPE_MAP.get(region.get("type", "paragraph"), "paragraph")

        tr = ET.SubElement(page, f"{{{PAGE_NS}}}TextRegion")
        tr.set("id", rid)
        tr.set("type", rtype)
        if region.get("label"):
            tr.set("custom", f'structure {{type:{region["type"]};}} label {{{region["label"]}}};')

        # Coordinates
        coords = ET.SubElement(tr, f"{{{PAGE_NS}}}Coords")
        coords.set("points", _bbox_to_coords(region.get("bbox", [0, 0, 100, 100]), img_w, img_h))

        # Text
        text = text_map.get(rid, "")
        if text:
            te = ET.SubElement(tr, f"{{{PAGE_NS}}}TextEquiv")
            unicode_el = ET.SubElement(te, f"{{{PAGE_NS}}}Unicode")
            unicode_el.text = text

    return pcgts


def export_object_pagexml(
    object_id: str,
    collection: str,
    force: bool = False,
) -> tuple[bool, Path | None]:
    """Export PAGE XML for all pages of an object."""
    results_dir = results_dir_for(collection)
    out_dir = results_dir / f"{object_id}_page"

    if out_dir.exists() and not force:
        existing = list(out_dir.glob("*.xml"))
        if existing:
            return True, out_dir

    ocr_data, layout_data = load_ocr_and_layout(object_id, collection)

    if not layout_data:
        print(f"  FEHLER: Keine Layout-Daten gefunden fuer {object_id}")
        return False, None

    if not ocr_data:
        print(f"  WARNUNG: Keine OCR-Daten, exportiere nur Layout")

    out_dir.mkdir(parents=True, exist_ok=True)

    ocr_pages = (ocr_data or {}).get("result", {}).get("pages", [])
    layout_pages = layout_data.get("pages", [])

    exported = 0
    for lp in layout_pages:
        page_num = lp.get("page", 1)
        img_name = lp.get("image_filename", f"IMG_{page_num}.jpg")
        img_w = lp.get("image_width_px", 4912)
        img_h = lp.get("image_height_px", 7360)
        regions = lp.get("regions", [])

        # Find matching OCR page
        transcription = ""
        for op in ocr_pages:
            if op.get("page") == page_num:
                transcription = op.get("transcription", "")
                break

        # Align text to regions
        text_map = _split_text_to_regions(transcription, regions)

        # Generate PAGE XML
        pcgts = generate_page_xml(page_num, img_name, img_w, img_h, regions, text_map)

        # Write
        xml_path = out_dir / f"page_{page_num:03d}.xml"
        tree = ET.ElementTree(pcgts)
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)
        exported += 1

    print(f"  {exported} PAGE XML Dateien -> {out_dir}")
    return True, out_dir


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="PAGE XML Export: Merged OCR + Layout → PAGE XML 2019"
    )
    parser.add_argument("object_id", nargs="?", help="Einzelnes Objekt (z.B. o_szd.100)")
    parser.add_argument("-c", "--collection", help="Sammlung", choices=COLLECTIONS.keys())
    parser.add_argument("--all", action="store_true", help="Alle Sammlungen")
    parser.add_argument("--force", action="store_true", help="Bestehende ueberschreiben")
    args = parser.parse_args()

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

    # Filter to objects that have layout data
    filtered = []
    for obj in objects:
        layout_path = results_dir_for(obj["collection"]) / f"{obj['object_id']}_layout.json"
        if layout_path.exists():
            filtered.append(obj)

    if not filtered:
        print("Keine Objekte mit Layout-Daten gefunden.")
        return

    print(f"PAGE XML Export: {len(filtered)} Objekte (von {len(objects)} mit Layout-Daten)")
    print("=" * 60)

    done, skipped, failed = 0, 0, 0
    for i, obj in enumerate(filtered):
        oid = obj["object_id"]
        col = obj["collection"]
        out_dir = results_dir_for(col) / f"{oid}_page"

        if out_dir.exists() and list(out_dir.glob("*.xml")) and not args.force:
            skipped += 1
            print(f"[{i + 1}/{len(filtered)}] {oid} -- uebersprungen")
            continue

        print(f"[{i + 1}/{len(filtered)}] {oid}")
        success, _ = export_object_pagexml(oid, col, args.force)
        if success:
            done += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Fertig: {done} exportiert, {skipped} uebersprungen, {failed} fehlgeschlagen")


if __name__ == "__main__":
    main()
