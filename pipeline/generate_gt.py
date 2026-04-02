"""Ground-Truth-Erzeugung: 3-Modell-Konsensus + Expert-Review-Draft.

Transkribiert GT-Objekte mit Gemini 3.1 Pro, vergleicht mit Flash Lite
(existierend) und Flash (aus Konsensus), erzeugt merged GT-Draft fuer
Expert-Review im Frontend.

Workflow:
  1. Gemini Pro transkribiert (3. Modell)
  2. Vergleich aller 3 Transkriptionen pro Seite
  3. Merge: 3/3 Konsensus → auto, 2/3 Mehrheit → Mehrheit, sonst Pro
  4. GT-Draft in results/groundtruth/{object_id}_gt_draft.json
  5. Expert reviewed im Frontend → _gt.json (expert_verified: true)
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from google import genai

from config import (
    COLLECTIONS, GOOGLE_API_KEY, PROMPTS_DIR, PROJECT_ROOT, RESULTS_BASE,
)
from evaluate import cer, normalize_for_consensus
from transcribe import load_prompt, load_images, SYSTEM_PROMPT, GROUP_PROMPTS
from verify import load_existing_result, extract_page_texts

# Gemini 3.1 Pro as third, strongest model
GT_MODEL = "gemini-3.1-pro-preview"

# The 18 GT objects (stratified across 9 groups)
GT_OBJECTS = [
    # Handschrift
    ("o_szd.139", "lebensdokumente"),
    ("o_szd.141", "lebensdokumente"),
    # Typoskript
    ("o_szd.102", "lebensdokumente"),
    ("o_szd.100", "lebensdokumente"),
    # Formular
    ("o_szd.145", "lebensdokumente"),
    ("o_szd.146", "lebensdokumente"),
    # Kurztext
    ("o_szd.142", "lebensdokumente"),
    ("o_szd.148", "lebensdokumente"),
    # Tabellarisch
    ("o_szd.149", "lebensdokumente"),
    ("o_szd.195", "lebensdokumente"),
    # Korrekturfahne
    ("o_szd.1887", "werke"),
    ("o_szd.1888", "werke"),
    # Konvolut
    ("o_szd.127", "lebensdokumente"),
    # Zeitungsausschnitt
    ("o_szd.2213", "aufsatzablage"),
    ("o_szd.2217", "aufsatzablage"),
    # Korrespondenz
    ("o_szd.1079", "korrespondenzen"),
    ("o_szd.1081", "korrespondenzen"),
    ("o_szd.1088", "korrespondenzen"),
]

GT_DIR = RESULTS_BASE / "groundtruth"


def transcribe_with_pro(object_id: str, collection: str, max_images: int = 0) -> dict | None:
    """Transcribe with Gemini 3.1 Pro — strongest model for GT draft."""
    from transcribe import resolve_context, parse_api_response

    group, context, _ = resolve_context(object_id, collection)
    group_prompt = GROUP_PROMPTS.get(group)
    if not group_prompt:
        print(f"  FEHLER: Kein Prompt fuer Gruppe '{group}'")
        return None

    try:
        images = load_images(object_id, collection, max_images)
    except FileNotFoundError as e:
        print(f"  FEHLER: {e}")
        return None

    user_prompt = (
        f"{group_prompt}\n\n{context}\n\n"
        f"Transkribiere die folgenden {len(images)} Faksimile-Scans."
    )

    parts = []
    for name, img_bytes in images:
        parts.append(genai.types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        parts.append(f"[{name}]")
    parts.append(user_prompt)

    client = genai.Client(api_key=GOOGLE_API_KEY)
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=GT_MODEL,
                contents=parts,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                ),
            )
            break
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str:
                wait = (2 ** attempt) * 5
                print(f"  RATE LIMIT (Versuch {attempt + 1}/4): warte {wait}s...")
                time.sleep(wait)
            else:
                print(f"  FEHLER bei API-Aufruf: {e}")
                return None
    else:
        print(f"  FEHLER: Rate Limit nach 4 Versuchen")
        return None

    result_text = response.text or ""
    result_json, parse_log = parse_api_response(result_text, object_id)
    for msg in parse_log:
        print(f"  {msg}")

    return result_json


def load_flash_from_consensus(object_id: str, collection: str) -> list[str] | None:
    """Extract Model B (Flash) page texts from consensus JSON."""
    cpath = RESULTS_BASE / collection / f"{object_id}_consensus.json"
    if not cpath.exists():
        return None
    data = json.loads(cpath.read_text(encoding="utf-8"))
    judge_pages = data.get("judge_data", {}).get("pages", [])
    return [p.get("transcription_b", "") for p in judge_pages]


def merge_page(text_a: str, text_b: str, text_c: str) -> tuple[str, str]:
    """Merge 3 transcriptions for a single page.

    Returns (merged_text, source) where source is one of:
      "consensus_3of3" — all 3 agree (CER <2% pairwise)
      "majority_2of3"  — 2 of 3 agree, take majority
      "pro_only"       — all diverge, take Pro (strongest model)
    """
    na = normalize_for_consensus(text_a)
    nb = normalize_for_consensus(text_b)
    nc = normalize_for_consensus(text_c)

    # Handle empty pages
    if not na and not nb and not nc:
        return "", "consensus_3of3"

    # Pairwise CER
    cer_ab = cer(nb, na) if na else (0.0 if not nb else 1.0)
    cer_ac = cer(nc, na) if na else (0.0 if not nc else 1.0)
    cer_bc = cer(nc, nb) if nb else (0.0 if not nc else 1.0)

    threshold = 0.02  # 2% CER for "agreement"

    # All 3 agree
    if cer_ab < threshold and cer_ac < threshold and cer_bc < threshold:
        return text_c, "consensus_3of3"  # Use Pro version (best quality)

    # 2 of 3 agree — take the pair with lowest CER
    pairs = [
        (cer_ab, text_a, text_b, "A+B"),
        (cer_ac, text_a, text_c, "A+C"),
        (cer_bc, text_b, text_c, "B+C"),
    ]
    best_pair = min(pairs, key=lambda x: x[0])
    if best_pair[0] < 0.05:  # 5% CER for majority
        # Prefer the version from the stronger model in the pair
        # C (Pro) > B (Flash) > A (Flash Lite)
        if "C" in best_pair[3]:
            return text_c, "majority_2of3"
        elif "B" in best_pair[3]:
            return text_b, "majority_2of3"
        else:
            return text_a, "majority_2of3"

    # All diverge — use Pro
    return text_c, "pro_only"


def generate_gt_for_object(
    object_id: str, collection: str, force: bool = False,
) -> dict | None:
    """Generate GT draft for a single object."""
    GT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = GT_DIR / f"{object_id}_gt_draft.json"

    if out_path.exists() and not force:
        print(f"  GT-Draft existiert: {out_path.name}")
        return json.loads(out_path.read_text(encoding="utf-8"))

    # Load Model A (Flash Lite) — existing result
    result_a = load_existing_result(object_id, collection)
    if result_a is None:
        print(f"  FEHLER: Keine Flash-Lite-Transkription fuer {object_id}")
        return None

    pages_a = extract_page_texts(result_a)
    page_types = [p.get("type", "content") for p in result_a.get("result", {}).get("pages", [])]
    n_pages = len(pages_a)

    # Load Model B (Flash) from consensus
    pages_b = load_flash_from_consensus(object_id, collection)
    if pages_b is None:
        print(f"  WARNUNG: Kein Konsensus fuer {object_id}, nur A+C")
        pages_b = [""] * n_pages

    # Transcribe with Model C (Pro)
    print(f"  Modell C: {GT_MODEL} (transkribiere, {n_pages} Bilder...)")
    result_c = transcribe_with_pro(object_id, collection, n_pages)
    if result_c is None or "raw" in result_c:
        print(f"  FEHLER: Pro konnte nicht transkribieren")
        return None

    pages_c = [p.get("transcription", "") for p in result_c.get("pages", [])]

    # Save Pro result separately
    pro_path = RESULTS_BASE / collection / f"{object_id}_{GT_MODEL.replace('-preview', '')}.json"
    pro_output = {
        "object_id": object_id,
        "collection": collection,
        "group": result_a.get("group", ""),
        "model": GT_MODEL,
        "result": result_c,
        "metadata": result_a.get("metadata", {}),
    }
    pro_path.write_text(json.dumps(pro_output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {pro_path.name}")

    # Merge page by page
    gt_pages = []
    stats = {"consensus_3of3": 0, "majority_2of3": 0, "pro_only": 0, "skipped": 0}

    for i in range(max(n_pages, len(pages_c))):
        pa = pages_a[i] if i < len(pages_a) else ""
        pb = pages_b[i] if i < len(pages_b) else ""
        pc = pages_c[i] if i < len(pages_c) else ""
        ptype = page_types[i] if i < len(page_types) else "content"

        if ptype != "content":
            gt_pages.append({
                "page": i + 1,
                "transcription": "",
                "type": ptype,
                "source": "skipped",
                "notes": result_a.get("result", {}).get("pages", [{}])[i].get("notes", "") if i < n_pages else "",
                "variants": {"flash_lite": pa, "flash": pb, "pro": pc},
            })
            stats["skipped"] += 1
            continue

        merged_text, source = merge_page(pa, pb, pc)
        gt_pages.append({
            "page": i + 1,
            "transcription": merged_text,
            "type": ptype,
            "source": source,
            "notes": "",
            "variants": {"flash_lite": pa, "flash": pb, "pro": pc},
        })
        stats[source] += 1

    print(f"  Merge: {stats}")

    # Build GT draft
    gt_draft = {
        "object_id": object_id,
        "collection": collection,
        "group": result_a.get("group", ""),
        "title": result_a.get("metadata", {}).get("title", ""),
        "models": {
            "a": result_a.get("model", ""),
            "b": "gemini-3-flash-preview",
            "c": GT_MODEL,
        },
        "pages": gt_pages,
        "merge_stats": stats,
        "expert_verified": False,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    out_path.write_text(json.dumps(gt_draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {out_path.name}")
    return gt_draft


def main():
    parser = argparse.ArgumentParser(
        description="SZD-HTR: Ground-Truth-Erzeugung mit 3-Modell-Konsensus",
    )
    parser.add_argument("--force", "-f", action="store_true",
                        help="Bestehende GT-Drafts ueberschreiben")
    parser.add_argument("--delay", type=float, default=4.0,
                        help="Sekunden zwischen API-Calls")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur auflisten, nicht transkribieren")
    parser.add_argument("--object", type=str, default=None,
                        help="Nur ein bestimmtes Objekt (z.B. o_szd.139)")
    args = parser.parse_args()

    if not GOOGLE_API_KEY and not args.dry_run:
        print("FEHLER: GOOGLE_API_KEY nicht gesetzt.")
        sys.exit(1)

    # Filter to single object if specified
    objects = GT_OBJECTS
    if args.object:
        objects = [(oid, col) for oid, col in GT_OBJECTS if oid == args.object]
        if not objects:
            print(f"FEHLER: {args.object} nicht in GT-Objektliste")
            sys.exit(1)

    print(f"GT-Erzeugung: {len(objects)} Objekte, Modell C: {GT_MODEL}")
    print("=" * 60)

    if args.dry_run:
        print(f"{'Object-ID':20s} {'Sammlung':20s} {'Seiten':>6s}")
        print("-" * 50)
        for oid, col in objects:
            result = load_existing_result(oid, col)
            n = len(result.get("result", {}).get("pages", [])) if result else 0
            print(f"{oid:20s} {col:20s} {n:>6d}")
        return

    results = {"ok": 0, "failed": 0}
    for i, (oid, col) in enumerate(objects, 1):
        print(f"\n[{i}/{len(objects)}] {oid} ({col})")
        gt = generate_gt_for_object(oid, col, args.force)
        if gt:
            results["ok"] += 1
        else:
            results["failed"] += 1

        if i < len(objects):
            time.sleep(args.delay)

    print("\n" + "=" * 60)
    print(f"Ergebnis: {results['ok']} OK, {results['failed']} fehlgeschlagen")


if __name__ == "__main__":
    main()
