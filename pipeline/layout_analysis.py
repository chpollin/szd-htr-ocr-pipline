"""SZD-HTR Layout-Analyse v4: Ensemble-Pipeline (Docling + Surya + VLM).

Stufe 1a: Docling  (Block-Level)     -> Regionen mit Typen + Bbox
Stufe 1b: Surya    (Line-Level)      -> Einzelne Textzeilen + Bbox
Stufe 2:  Gemini   (VLM Merger)      -> Finale Regionen (merged, klassifiziert)
Stufe 3:  Gemini   (VLM Verifikation)-> Layout-Qualitaetssignal
"""

import argparse
import io
import json
import re
import struct
import sys
import tempfile
import time
from pathlib import Path

from google import genai

from config import (
    BATCH_DELAY, COLLECTIONS, GROUP_LABELS, GOOGLE_API_KEY,
    LAYOUT_MAX_REGION_PCT, LAYOUT_MIN_REGION_HEIGHT_PCT,
    LAYOUT_MIN_REGION_WIDTH_PCT, LAYOUT_MODEL, PROMPTS_DIR,
    results_dir_for,
)
from transcribe import (
    discover_objects, find_ocr_file, load_images, parse_api_response,
    resolve_context,
)


# --- Prompts ---

def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    return blocks[0].strip() if blocks else text.strip()


ENSEMBLE_PROMPT = _load_prompt("layout_ensemble.md")
VERIFY_PROMPT = _load_prompt("layout_verify.md")

LAYOUT_GROUP_PROMPTS = {
    "handschrift":        _load_prompt("layout_group_a_handschrift.md"),
    "typoskript":         _load_prompt("layout_group_b_typoskript.md"),
    "formular":           _load_prompt("layout_group_c_formular.md"),
    "kurztext":           _load_prompt("layout_group_d_kurztext.md"),
    "tabellarisch":       _load_prompt("layout_group_e_tabellarisch.md"),
    "korrekturfahne":     _load_prompt("layout_group_f_korrekturfahne.md"),
    "konvolut":           _load_prompt("layout_group_g_konvolut.md"),
    "zeitungsausschnitt": _load_prompt("layout_group_h_zeitungsausschnitt.md"),
    "korrespondenz":      _load_prompt("layout_group_i_korrespondenz.md"),
}


# --- Type Mappings ---

DOCLING_TYPE_MAP = {
    "title": "heading", "section_header": "heading", "section-header": "heading",
    "page_header": "heading", "page-header": "heading",
    "text": "paragraph", "caption": "paragraph", "footnote": "paragraph",
    "formula": "paragraph",
    "list_item": "list", "list-item": "list",
    "table": "table",
}
DOCLING_SKIP = {"picture", "page_footer", "page-footer"}


# --- Image Dimensions ---

def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        if marker == 0xD9:
            break
        if marker in (0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0x01):
            i += 2
            continue
        if i + 3 >= len(data):
            break
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            if i + 9 <= len(data):
                height = struct.unpack(">H", data[i + 5 : i + 7])[0]
                width = struct.unpack(">H", data[i + 7 : i + 9])[0]
                return width, height
        i += 2 + length
    return 0, 0


# --- VLM Call ---

def _call_vlm(image_data: bytes, user_prompt: str) -> dict | None:
    parts = [
        genai.types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
        user_prompt,
    ]
    client = genai.Client(api_key=GOOGLE_API_KEY)
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=LAYOUT_MODEL,
                contents=parts,
                config=genai.types.GenerateContentConfig(temperature=0.1),
            )
            if response and response.text:
                parsed, log = parse_api_response(response.text, "vlm")
                for msg in log:
                    print(f"    {msg}")
                return parsed
            return None
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str or "rate" in err_str:
                wait = (2 ** attempt) * 5
                print(f"    RATE LIMIT ({attempt + 1}/4): warte {wait}s...")
                time.sleep(wait)
            else:
                print(f"    VLM-FEHLER: {e}")
                return None
    return None


# =============================================================================
# STUFE 1a: Docling (Block-Level)
# =============================================================================

def _init_docling():
    from docling.document_converter import DocumentConverter
    return DocumentConverter()


def _analyze_page_docling(converter, image_data: bytes, img_w: int, img_h: int) -> list[dict]:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(image_data)
        tmp_path = f.name
    try:
        result = converter.convert(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    regions = []
    for item in result.document.texts:
        label = item.label.lower().replace(" ", "_")
        if label in DOCLING_SKIP:
            continue
        prov = item.prov[0] if item.prov else None
        if not (prov and prov.bbox):
            continue
        b = prov.bbox
        regions.append({
            "id": f"d{len(regions) + 1}",
            "type": DOCLING_TYPE_MAP.get(label, "paragraph"),
            "bbox": [
                round(max(0, min(100, b.l / img_w * 100)), 1),
                round(max(0, min(100, (1 - b.t / img_h) * 100)), 1),
                round(max(0, min(100, (b.r - b.l) / img_w * 100)), 1),
                round(max(0, min(100, (b.t - b.b) / img_h * 100)), 1),
            ],
            "label": (item.text[:40] if item.text else item.label).strip(),
            "docling_label": item.label,
        })
    for table in result.document.tables:
        prov = table.prov[0] if table.prov else None
        if not (prov and prov.bbox):
            continue
        b = prov.bbox
        regions.append({
            "id": f"d{len(regions) + 1}",
            "type": "table",
            "bbox": [
                round(max(0, min(100, b.l / img_w * 100)), 1),
                round(max(0, min(100, (1 - b.t / img_h) * 100)), 1),
                round(max(0, min(100, (b.r - b.l) / img_w * 100)), 1),
                round(max(0, min(100, (b.t - b.b) / img_h * 100)), 1),
            ],
            "label": "Tabelle",
            "docling_label": "table",
        })
    return regions


# =============================================================================
# STUFE 1b: Surya (Line-Level Detection)
# =============================================================================

def _init_surya():
    from surya.detection import DetectionPredictor
    return DetectionPredictor()


def _analyze_page_surya(predictor, image_data: bytes, img_w: int, img_h: int) -> list[dict]:
    from PIL import Image
    image = Image.open(io.BytesIO(image_data))
    preds = predictor([image])[0]

    lines = []
    for i, bbox_obj in enumerate(preds.bboxes):
        x1, y1, x2, y2 = bbox_obj.bbox
        lines.append({
            "id": f"s{i + 1}",
            "bbox": [
                round(max(0, min(100, x1 / img_w * 100)), 1),
                round(max(0, min(100, y1 / img_h * 100)), 1),
                round(max(0, min(100, (x2 - x1) / img_w * 100)), 1),
                round(max(0, min(100, (y2 - y1) / img_h * 100)), 1),
            ],
            "confidence": round(bbox_obj.confidence, 3) if hasattr(bbox_obj, 'confidence') else 0,
        })
    return lines


# --- Region ID Normalisierung ---

def _normalize_region_ids(regions: list[dict]) -> list[dict]:
    """Renumber region IDs to r1, r2, ... (schema expects ^r\\d+$)."""
    for i, r in enumerate(regions):
        r["id"] = f"r{i + 1}"
    return regions


# =============================================================================
# STUFE 2: VLM Ensemble-Merger
# =============================================================================

def _merge_and_classify(
    image_data: bytes,
    docling_regions: list[dict],
    surya_lines: list[dict],
    group_prompt: str,
    context_hint: str,
) -> tuple[list[dict], dict | None]:
    """Ensemble-Merger + Verifikation in einem VLM-Call.

    Returns (regions, quality_dict_or_None).
    """
    docling_json = json.dumps(docling_regions, ensure_ascii=False, indent=2) if docling_regions else "[]"
    surya_json = json.dumps(surya_lines, ensure_ascii=False, indent=2) if surya_lines else "[]"

    prompt = ""
    if group_prompt:
        prompt += f"{group_prompt}\n\n"
    prompt += f"{context_hint}\n\n"
    prompt += ENSEMBLE_PROMPT.replace("{docling_regions}", docling_json).replace("{surya_lines}", surya_json)

    result = _call_vlm(image_data, prompt)
    if not result or "regions" not in result:
        # Fallback: return Docling regions + ungrouped Surya lines as paragraphs
        print(f"      WARNUNG: VLM-Merger fehlgeschlagen, Fallback: "
              f"{len(docling_regions)} Docling + {len(surya_lines)} Surya")
        fallback = list(docling_regions)
        for line in surya_lines:
            fallback.append({
                "id": line["id"], "type": "paragraph", "bbox": line["bbox"],
                "reading_order": len(fallback) + 1, "lines": 1,
                "label": "Textzeile", "source": "surya",
            })
        return _normalize_region_ids(fallback), None

    # Extract quality from combined response
    quality = None
    raw_quality = result.get("quality")
    if isinstance(raw_quality, dict):
        quality = {
            "coverage": raw_quality.get("coverage", "unknown"),
            "coverage_note": raw_quality.get("coverage_note", ""),
            "position_accuracy": raw_quality.get("position_accuracy", "unknown"),
            "type_accuracy": raw_quality.get("type_accuracy", "unknown"),
            "reading_order_ok": raw_quality.get("reading_order_ok", True),
            "missing_regions": raw_quality.get("missing_regions", []),
            "issues": raw_quality.get("issues", []),
            "overall": raw_quality.get("overall", "unknown"),
        }

    # Validate VLM regions
    regions = []
    for r in result.get("regions", []):
        # Bbox is required — skip regions without valid bbox
        raw_bbox = r.get("bbox")
        if not isinstance(raw_bbox, list) or len(raw_bbox) != 4:
            continue
        try:
            bbox = [round(max(0, min(100, float(v))), 1) for v in raw_bbox]
        except (ValueError, TypeError):
            continue

        x, y, w, h = bbox
        # Reject tiny regions (noise)
        if w <= LAYOUT_MIN_REGION_WIDTH_PCT or h <= LAYOUT_MIN_REGION_HEIGHT_PCT:
            print(f"      WARNUNG: Region '{r.get('id', '?')}' zu klein "
                  f"({w:.1f}% x {h:.1f}%), ignoriert")
            continue
        # Reject full-page hallucinations
        if w > LAYOUT_MAX_REGION_PCT and h > LAYOUT_MAX_REGION_PCT:
            print(f"      WARNUNG: Region '{r.get('id', '?')}' full-page "
                  f"({w:.1f}% x {h:.1f}%), Halluzination ignoriert")
            continue

        region = {
            "id": r.get("id", f"r{len(regions) + 1}"),
            "type": r.get("type", "paragraph"),
            "bbox": bbox,
            "reading_order": r.get("reading_order", len(regions) + 1),
            "lines": r.get("lines", 1),
            "label": r.get("label", ""),
            "source": r.get("source", "unknown"),
        }
        if region["type"] not in ("paragraph", "heading", "list", "table", "marginalia"):
            region["type"] = "paragraph"
        regions.append(region)

    if not regions:
        print(f"      WARNUNG: VLM lieferte keine gueltigen Regionen, Fallback auf Docling")
        return _normalize_region_ids(list(docling_regions)), quality
    return _normalize_region_ids(regions), quality


# =============================================================================
# STUFE 2.5: Deterministische Post-Processing-Filter
# =============================================================================

def _iou(a: list, b: list) -> float:
    """Intersection over Union fuer zwei Bboxen [x, y, w, h] in Prozent."""
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def _contains(outer: list, inner: list) -> bool:
    """Prueft ob inner vollstaendig in outer liegt (mit 1% Toleranz)."""
    ox, oy, ow, oh = outer
    ix, iy, iw, ih = inner
    return (ix >= ox - 1 and iy >= oy - 1
            and ix + iw <= ox + ow + 1 and iy + ih <= oy + oh + 1)


def _area(bbox: list) -> float:
    return bbox[2] * bbox[3]


def _postprocess_regions(regions: list[dict]) -> list[dict]:
    """Deterministische Post-Processing-Filter nach dem VLM-Merger.

    Filter 1: Scan-Hintergrund-Regionen (am aeusseren Bildrand, sehr flach)
    Filter 2: Ueberlappende Regionen gleichen Typs (IoU > 50% -> merge)
    Filter 3: Spurious Zwischen-Regionen (sehr flach, innerhalb groesserer Region)
    """
    if len(regions) <= 1:
        return regions

    removed = set()

    # --- Filter 1: Scan-Hintergrund-Regionen ---
    # Regionen die am aeusseren Bildrand liegen UND sehr flach/schmal sind
    for i, r in enumerate(regions):
        x, y, w, h = r["bbox"]
        # Sehr flache Region (h < 2%) am oberen/unteren Rand
        if h < 2.0 and (y < 8.0 or y + h > 92.0):
            # Aber Seitenzahlen (heading, klein) behalten
            if r["type"] != "heading" or w > 15.0:
                print(f"      FILTER: '{r.get('label', r['id'])}' entfernt "
                      f"(Scan-Hintergrund, y={y:.1f}%, h={h:.1f}%)")
                removed.add(i)
        # Sehr schmale Region (w < 3%) am linken/rechten Rand
        if w < 3.0 and (x < 8.0 or x + w > 92.0) and h > 20.0:
            print(f"      FILTER: '{r.get('label', r['id'])}' entfernt "
                  f"(schmaler Scan-Rand, x={x:.1f}%, w={w:.1f}%, h={h:.1f}%)")
            removed.add(i)

    # --- Filter 2: Ueberlappende Regionen gleichen Typs ---
    for i, a in enumerate(regions):
        if i in removed:
            continue
        for j, b in enumerate(regions):
            if j <= i or j in removed:
                continue
            if a["type"] == b["type"] and _iou(a["bbox"], b["bbox"]) > 0.5:
                # Kleinere entfernen, groessere behalten
                if _area(a["bbox"]) >= _area(b["bbox"]):
                    print(f"      FILTER: '{b.get('label', b['id'])}' gemerged in "
                          f"'{a.get('label', a['id'])}' (IoU-Ueberlappung)")
                    removed.add(j)
                else:
                    print(f"      FILTER: '{a.get('label', a['id'])}' gemerged in "
                          f"'{b.get('label', b['id'])}' (IoU-Ueberlappung)")
                    removed.add(i)
                    break

    # --- Filter 3: Spurious Zwischen-Regionen ---
    for i, r in enumerate(regions):
        if i in removed:
            continue
        x, y, w, h = r["bbox"]
        if h < 1.5:
            # Pruefen ob diese Region vollstaendig in einer groesseren liegt
            for j, outer in enumerate(regions):
                if j == i or j in removed:
                    continue
                if _area(outer["bbox"]) > _area(r["bbox"]) * 3 and _contains(outer["bbox"], r["bbox"]):
                    print(f"      FILTER: '{r.get('label', r['id'])}' entfernt "
                          f"(spurious, h={h:.1f}%, innerhalb '{outer.get('label', outer['id'])}')")
                    removed.add(i)
                    break

    if removed:
        result = [r for i, r in enumerate(regions) if i not in removed]
        # Reading-Order neu vergeben
        for idx, r in enumerate(result):
            r["reading_order"] = idx + 1
        return _normalize_region_ids(result)
    return regions


# =============================================================================
# STUFE 3: VLM Verifikation
# =============================================================================

def _verify_layout(image_data: bytes, regions: list[dict], context_hint: str) -> dict:
    regions_json = json.dumps(regions, ensure_ascii=False, indent=2)
    prompt = f"{context_hint}\n\n" + VERIFY_PROMPT.replace("{regions_json}", regions_json)
    result = _call_vlm(image_data, prompt)
    if not result:
        return {"overall": "unknown"}
    return {
        "coverage": result.get("coverage", "unknown"),
        "coverage_note": result.get("coverage_note", ""),
        "position_accuracy": result.get("position_accuracy", "unknown"),
        "type_accuracy": result.get("type_accuracy", "unknown"),
        "reading_order_ok": result.get("reading_order_ok", True),
        "missing_regions": result.get("missing_regions", []),
        "issues": result.get("issues", []),
        "overall": result.get("overall", "unknown"),
    }


# =============================================================================
# Orchestration
# =============================================================================

def analyze_object_layout(
    object_id: str,
    collection: str,
    max_images: int = 0,
    force: bool = False,
    cv_only: bool = False,
) -> tuple[bool, Path | None]:
    results_dir = results_dir_for(collection)
    out_path = results_dir / f"{object_id}_layout.json"

    if out_path.exists() and not force:
        return True, out_path

    group, context, _ = resolve_context(object_id, collection)
    context_hint = f"Dokumenttyp: {group}. Sammlung: {collection}."
    group_prompt = LAYOUT_GROUP_PROMPTS.get(group, "")
    group_letter = GROUP_LABELS.get(group, ("?", group))[0]
    print(f"  Gruppe {group_letter}: {group}")

    try:
        images = load_images(object_id, collection, max_images)
    except FileNotFoundError as e:
        print(f"  FEHLER: {e}")
        return False, None

    # Load page types from transcription result (skip blank/color_chart pages)
    page_types = {}
    ocr_file = find_ocr_file(results_dir, object_id)
    if ocr_file:
        try:
            ocr_data = json.loads(ocr_file.read_text(encoding="utf-8"))
            for p in ocr_data.get("result", {}).get("pages", []):
                page_num = p.get("page")
                if page_num and page_num > 0:
                    page_types[page_num] = p.get("type", "content")
            print(f"  Seitentypen aus {ocr_file.name} geladen")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARNUNG: {ocr_file.name} nicht lesbar: {e}")
    else:
        print(f"  WARNUNG: Keine OCR-Ergebnisse, alle Seiten als 'content' behandelt")

    print(f"  {len(images)} Bilder")

    # Init both CV engines once
    print("  Docling initialisieren...", end=" ", flush=True)
    docling_conv = _init_docling()
    print("OK")
    print("  Surya initialisieren...", end=" ", flush=True)
    surya_pred = _init_surya()
    print("OK")

    pages = []
    page_qualities = []

    for i, (img_name, img_bytes) in enumerate(images):
        page_num = i + 1
        page_type = page_types.get(page_num, "content")

        # Skip blank and color_chart pages — no layout analysis needed
        if page_type in ("blank", "color_chart"):
            print(f"    Seite {page_num}/{len(images)}: {img_name} — {page_type}, uebersprungen")
            width, height = _jpeg_dimensions(img_bytes)
            pages.append({
                "page": page_num,
                "image_filename": img_name,
                "image_width_px": width,
                "image_height_px": height,
                "regions": [],
            })
            continue

        print(f"    Seite {page_num}/{len(images)}: {img_name}")
        width, height = _jpeg_dimensions(img_bytes)

        # PIL-Fallback bei fehlenden/ungueltigen JPEG-Dimensionen
        if width <= 0 or height <= 0:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(img_bytes))
                width, height = img.size
                print(f"      WARNUNG: JPEG-Header unlesbar, PIL-Fallback: {width}x{height}")
            except Exception:
                print(f"      FEHLER: Bildgroesse nicht ermittelbar, uebersprungen")
                pages.append({
                    "page": page_num, "image_filename": img_name,
                    "image_width_px": 0, "image_height_px": 0, "regions": [],
                })
                continue

        try:
            # Stufe 1a: Docling
            print(f"      Docling...", end=" ", flush=True)
            try:
                docling_regions = _analyze_page_docling(docling_conv, img_bytes, width, height)
            except Exception as e:
                print(f"FEHLER ({e}), Fallback: 0 Bloecke")
                docling_regions = []
            else:
                print(f"{len(docling_regions)} Bloecke")

            # Stufe 1b: Surya
            print(f"      Surya...", end=" ", flush=True)
            try:
                surya_lines = _analyze_page_surya(surya_pred, img_bytes, width, height)
            except Exception as e:
                print(f"FEHLER ({e}), Fallback: 0 Zeilen")
                surya_lines = []
            else:
                print(f"{len(surya_lines)} Zeilen")

            if cv_only:
                # Combine as-is for debugging
                final_regions = []
                for r in docling_regions:
                    final_regions.append({**r, "reading_order": len(final_regions) + 1, "lines": 1, "source": "docling"})
                for l in surya_lines:
                    final_regions.append({
                        "id": l["id"], "type": "paragraph", "bbox": l["bbox"],
                        "reading_order": len(final_regions) + 1, "lines": 1,
                        "label": "Textzeile", "source": "surya",
                    })
                page_quality = None
            else:
                # Stufe 2+3: VLM Ensemble-Merger + Verifikation (kombiniert)
                print(f"      VLM Merge+Verify...", end=" ", flush=True)
                final_regions, page_quality = _merge_and_classify(
                    img_bytes, docling_regions, surya_lines, group_prompt, context_hint)
                q_label = page_quality.get("overall", "?") if page_quality else "no-quality"
                print(f"{len(final_regions)} Regionen, {q_label}")

                # Stufe 2.5: Deterministische Post-Processing-Filter
                before_count = len(final_regions)
                final_regions = _postprocess_regions(final_regions)
                if len(final_regions) < before_count:
                    print(f"      Post-Filter: {before_count} -> {len(final_regions)} Regionen")

                time.sleep(BATCH_DELAY)

        except Exception as e:
            print(f"      FEHLER Seite {page_num}: {e}")
            final_regions = []
            page_quality = None

        pages.append({
            "page": page_num,
            "image_filename": img_name,
            "image_width_px": width,
            "image_height_px": height,
            "regions": final_regions,
        })
        if page_quality:
            page_qualities.append({"page": page_num, **page_quality})

    # Aggregate quality
    layout_quality = None
    if page_qualities:
        vals = [q["overall"] for q in page_qualities]
        agg = "needs_correction" if "needs_correction" in vals else ("acceptable" if "acceptable" in vals else "good")
        layout_quality = {
            "overall": agg,
            "pages": page_qualities,
            "pages_needing_review": [q["page"] for q in page_qualities if q["overall"] == "needs_correction"],
        }

    output = {
        "object_id": object_id,
        "collection": collection,
        "group": group,
        "model": f"docling+surya+{LAYOUT_MODEL}" if not cv_only else "docling+surya",
        "pages": pages,
    }
    if layout_quality:
        output["layout_quality"] = layout_quality

    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Gespeichert: {out_path}")
    return True, out_path


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Ensemble Layout-Analyse: Docling + Surya + VLM Merger"
    )
    parser.add_argument("object_id", nargs="?", help="Einzelnes Objekt (z.B. o_szd.100)")
    parser.add_argument("-c", "--collection", help="Sammlung", choices=COLLECTIONS.keys())
    parser.add_argument("--all", action="store_true", help="Alle Sammlungen")
    parser.add_argument("--group", "-g", choices=list(LAYOUT_GROUP_PROMPTS.keys()),
                        help="Nur Objekte dieser Prompt-Gruppe")
    parser.add_argument("--limit", type=int, default=0, help="Max. Objekte pro Sammlung")
    parser.add_argument("--max-images", type=int, default=0, help="Max. Bilder pro Objekt")
    parser.add_argument("--force", action="store_true", help="Bestehende ueberschreiben")
    parser.add_argument("--dry-run", action="store_true", help="Nur auflisten")
    parser.add_argument("--cv-only", action="store_true",
                        help="Nur CV-Stufen (Docling+Surya), ohne VLM")
    parser.add_argument("--delay", type=float, default=None, help="Delay zwischen API-Calls (Sek.)")
    args = parser.parse_args()

    if args.delay is not None:
        import config
        config.BATCH_DELAY = args.delay

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

    if args.group:
        filtered = []
        for obj in objects:
            grp, _, _ = resolve_context(obj["object_id"], obj["collection"])
            if grp == args.group:
                filtered.append(obj)
        print(f"Gruppe '{args.group}' Filter: {len(filtered)}/{len(objects)} Objekte")
        objects = filtered

    if args.limit:
        objects = objects[:args.limit]

    if args.dry_run:
        print(f"{'Object-ID':<20} {'Sammlung':<20} {'Gruppe':<20}")
        print("-" * 60)
        for obj in objects:
            grp, _, _ = resolve_context(obj["object_id"], obj["collection"])
            lbl = GROUP_LABELS.get(grp, ("?", grp))[0]
            print(f"{obj['object_id']:<20} {obj['collection']:<20} {lbl}: {grp}")
        print(f"\n{len(objects)} Objekte")
        return

    mode = "Docling+Surya (CV-only)" if args.cv_only else f"Docling+Surya+{LAYOUT_MODEL}"
    print(f"Layout-Analyse: {len(objects)} Objekte ({mode})")
    print("=" * 60)

    done, skipped, failed = 0, 0, 0
    for i, obj in enumerate(objects):
        oid, col = obj["object_id"], obj["collection"]
        out_path = results_dir_for(col) / f"{oid}_layout.json"

        if out_path.exists() and not args.force:
            skipped += 1
            print(f"[{i + 1}/{len(objects)}] {oid} -- uebersprungen")
            continue

        print(f"[{i + 1}/{len(objects)}] {oid}")
        success, _ = analyze_object_layout(oid, col, args.max_images, args.force, args.cv_only)
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
