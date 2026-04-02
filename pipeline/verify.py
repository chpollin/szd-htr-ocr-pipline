"""Multi-Model-Konsensus-Verifikation für SZD-HTR.

Verifiziert existierende Transkriptionen (Gemini Flash Lite) durch:
- Modell B: Gemini 3 Flash (unabhängige Zweittranskription)
- Judge: Claude Code Subagent mit Vision (manuell, nicht in diesem Skript)

Basiert auf Zhang et al. 2025 (Consensus Entropy, ICLR 2026).
Siehe knowledge/verification-concept.md §7.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from google import genai

from config import (
    BACKUP_ROOT, COLLECTIONS, GOOGLE_API_KEY, GROUP_LABELS,
    PROMPTS_DIR, PROJECT_ROOT, RESULTS_BASE,
)
from evaluate import (
    cer, normalize_text, normalize_for_consensus,
    normalize_for_consensus_orderless, word_overlap,
)
from tei_context import parse_tei_for_object, context_from_backup_metadata, format_context, resolve_group
from transcribe import load_prompt, load_images, SYSTEM_PROMPT, GROUP_PROMPTS

# Model B for independent re-transcription
VERIFY_MODEL = "gemini-3-flash-preview"


def load_existing_result(object_id: str, collection: str) -> dict | None:
    """Load existing transcription result (Model A: Flash Lite)."""
    results_dir = RESULTS_BASE / collection
    # Find the result file
    for f in results_dir.glob(f"{object_id}_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("result", {}).get("pages"):
            return data
    return None


def extract_transcription_text(result: dict) -> str:
    """Extract full transcription text from result JSON."""
    pages = result.get("result", {}).get("pages", [])
    return "\n\n".join(p.get("transcription", "") for p in pages)


def extract_page_texts(result: dict) -> list[str]:
    """Extract per-page transcription texts."""
    pages = result.get("result", {}).get("pages", [])
    return [p.get("transcription", "") for p in pages]


def transcribe_with_flash(
    object_id: str, collection: str, max_images: int = 0,
) -> dict | None:
    """Transcribe with Gemini 3 Flash (Model B) — independent re-transcription."""
    from transcribe import resolve_context, parse_api_response

    group, context, _ = resolve_context(object_id, collection)
    group_prompt = GROUP_PROMPTS.get(group)
    if not group_prompt:
        print(f"  FEHLER: Kein Prompt für Gruppe '{group}'")
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
                model=VERIFY_MODEL,
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


def compute_consensus(
    text_a: str, text_b: str, pages_a: list[str], pages_b: list[str],
    page_types: list[str] | None = None,
) -> dict:
    """Compute consensus metrics between two transcriptions.

    Uses both ordered CER and order-invariant CER to handle reading-order
    divergence (e.g., marginalia, multi-column layouts). The effective CER
    is the minimum of both, so documents with same content in different
    order are not penalized.

    Args:
        page_types: Optional list of page types ('content', 'blank', 'color_chart').
            Non-content pages are skipped in CER calculation.
    """
    # Per-page CER (skip non-content pages)
    page_results = []
    content_texts_a = []
    content_texts_b = []

    for i, (pa, pb) in enumerate(zip(pages_a, pages_b)):
        ptype = page_types[i] if page_types and i < len(page_types) else "content"
        if ptype != "content":
            page_results.append({
                "page": i,
                "cer": None,
                "cer_orderless": None,
                "agreement": "skipped",
                "type": ptype,
                "chars_a": len(pa),
                "chars_b": len(pb),
            })
            continue

        na = normalize_for_consensus(pa)
        nb = normalize_for_consensus(pb)
        na_ol = normalize_for_consensus_orderless(pa)
        nb_ol = normalize_for_consensus_orderless(pb)
        page_cer = cer(nb, na) if na else (0.0 if not nb else 1.0)
        page_cer_ol = cer(nb_ol, na_ol) if na_ol else (0.0 if not nb_ol else 1.0)
        effective_cer = min(page_cer, page_cer_ol)
        agreement = "high" if effective_cer < 0.03 else ("moderate" if effective_cer < 0.10 else "low")
        page_results.append({
            "page": i,
            "cer": round(page_cer, 4),
            "cer_orderless": round(page_cer_ol, 4),
            "agreement": agreement,
            "type": ptype,
            "chars_a": len(na),
            "chars_b": len(nb),
        })
        content_texts_a.append(pa)
        content_texts_b.append(pb)

    # Overall CER from content pages only (both ordered and orderless)
    joined_a = " ".join(content_texts_a)
    joined_b = " ".join(content_texts_b)
    norm_a = normalize_for_consensus(joined_a)
    norm_b = normalize_for_consensus(joined_b)
    norm_a_ol = normalize_for_consensus_orderless(joined_a)
    norm_b_ol = normalize_for_consensus_orderless(joined_b)

    overall_cer = cer(norm_b, norm_a) if norm_a else (0.0 if not norm_b else 1.0)
    overall_cer_ol = cer(norm_b_ol, norm_a_ol) if norm_a_ol else (0.0 if not norm_b_ol else 1.0)
    overall_word_overlap = word_overlap(joined_a, joined_b)
    effective_cer = min(overall_cer, overall_cer_ol)

    # Consensus category: use both CER and word overlap
    # Word overlap handles reading-order divergence (marginalia, columns)
    # High word overlap (>=0.90) means content is essentially the same despite order/CER
    if effective_cer < 0.03 or (overall_word_overlap >= 0.95 and effective_cer < 0.10):
        category = "consensus_verified"
    elif effective_cer < 0.10 or overall_word_overlap >= 0.90:
        category = "consensus_moderate"
    elif overall_word_overlap >= 0.75:
        category = "consensus_review"
    else:
        category = "consensus_divergent"

    content_count = sum(1 for pr in page_results if pr["agreement"] != "skipped")
    skipped_count = len(page_results) - content_count

    return {
        "overall_cer": round(overall_cer, 4),
        "overall_cer_orderless": round(overall_cer_ol, 4),
        "effective_cer": round(effective_cer, 4),
        "word_overlap": round(overall_word_overlap, 4),
        "category": category,
        "content_pages": content_count,
        "skipped_pages": skipped_count,
        "pages": page_results,
    }


def prepare_judge_data(
    object_id: str, collection: str, result_a: dict, result_b: dict, consensus: dict,
) -> dict:
    """Prepare data package for Claude Code Subagent judge."""
    meta = result_a.get("metadata", {})
    gams_images = meta.get("images", [])

    pages_a = result_a.get("result", {}).get("pages", [])
    pages_b = result_b.get("pages", [])

    judge_pages = []
    for i in range(max(len(pages_a), len(pages_b))):
        pa = pages_a[i] if i < len(pages_a) else {}
        pb = pages_b[i] if i < len(pages_b) else {}
        img_url = gams_images[i] if i < len(gams_images) else ""
        page_consensus = consensus["pages"][i] if i < len(consensus["pages"]) else {}

        judge_pages.append({
            "page": i,
            "image_url": img_url,
            "transcription_a": pa.get("transcription", ""),
            "transcription_b": pb.get("transcription", ""),
            "cer": page_consensus.get("cer", None),
            "agreement": page_consensus.get("agreement", "unknown"),
        })

    return {
        "object_id": object_id,
        "collection": collection,
        "group": result_a.get("group", ""),
        "title": meta.get("title", ""),
        "model_a": result_a.get("model", ""),
        "model_b": VERIFY_MODEL,
        "consensus": consensus,
        "pages": judge_pages,
    }


def verify_object(
    object_id: str, collection: str, max_images: int = 0, force: bool = False,
) -> dict | None:
    """Verify a single object: load Model A result, run Model B, compute consensus."""
    out_dir = RESULTS_BASE / collection
    out_path = out_dir / f"{object_id}_consensus.json"

    if out_path.exists() and not force:
        print(f"  Konsensus existiert bereits: {out_path.name}")
        return json.loads(out_path.read_text(encoding="utf-8"))

    # Load existing result (Model A)
    result_a = load_existing_result(object_id, collection)
    if result_a is None:
        print(f"  FEHLER: Keine existierende Transkription für {object_id}")
        return None

    if "raw" in result_a.get("result", {}):
        print(f"  ÜBERSPRUNGEN: {object_id} hat broken result (raw)")
        return None

    # Match image count from Model A to ensure fair comparison
    n_pages_a = len(result_a.get("result", {}).get("pages", []))
    effective_max = max_images if max_images else n_pages_a
    print(f"  Modell A: {result_a.get('model', '?')} ({n_pages_a} Seiten)")

    # Run Model B (Gemini 3 Flash) with same image count
    print(f"  Modell B: {VERIFY_MODEL} (transkribiere, max {effective_max} Bilder...)")
    result_b = transcribe_with_flash(object_id, collection, effective_max)
    if result_b is None or "raw" in result_b:
        print(f"  FEHLER: Modell B konnte nicht transkribieren")
        return None

    # Compute consensus (skip blank/color_chart pages)
    text_a = extract_transcription_text(result_a)
    text_b = "\n\n".join(p.get("transcription", "") for p in result_b.get("pages", []))
    pages_a = extract_page_texts(result_a)
    pages_b = [p.get("transcription", "") for p in result_b.get("pages", [])]
    page_types = [p.get("type", "content") for p in result_a.get("result", {}).get("pages", [])]

    consensus = compute_consensus(text_a, text_b, pages_a, pages_b, page_types=page_types)
    cer_ordered = consensus['overall_cer']
    cer_orderless = consensus.get('overall_cer_orderless', cer_ordered)
    effective = consensus.get('effective_cer', cer_ordered)
    w_overlap = consensus.get('word_overlap', 0)
    print(f"  CER: {cer_ordered:.2%} (ordered) / {cer_orderless:.2%} (orderless) -> {effective:.2%} effective, word_overlap={w_overlap:.2%}")
    print(f"  Kategorie: {consensus['category']}")

    # Prepare judge data (for Claude Code Subagent)
    judge_data = prepare_judge_data(object_id, collection, result_a, result_b, consensus)

    # Save consensus result
    output = {
        "object_id": object_id,
        "collection": collection,
        "group": result_a.get("group", ""),
        "model_a": result_a.get("model", ""),
        "model_b": VERIFY_MODEL,
        "consensus": consensus,
        "judge_data": judge_data,
        "judge_result": None,  # Filled by Claude Code Subagent
    }

    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {out_path.name}")
    return output


def select_sample(n_per_group: int = 3) -> list[dict]:
    """Select stratified sample for consensus validation."""
    from collections import defaultdict
    group_objects = defaultdict(list)

    for col in COLLECTIONS:
        results_dir = RESULTS_BASE / col
        if not results_dir.exists():
            continue
        for f in sorted(results_dir.glob("*.json")):
            if "_consensus" in f.name:
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            if "collection" not in data or "raw" in data.get("result", {}):
                continue
            group = data.get("group", "?")
            qs = data.get("quality_signals", {})
            group_objects[group].append({
                "object_id": data["object_id"],
                "collection": data["collection"],
                "group": group,
                "needs_review": qs.get("needs_review", False),
                "total_chars": qs.get("total_chars", 0),
            })

    sample = []
    for group, objects in sorted(group_objects.items()):
        # Mix: take some needs_review and some clean
        review = [o for o in objects if o["needs_review"]]
        clean = [o for o in objects if not o["needs_review"]]
        selected = []
        # Alternate between review and clean
        for src in [clean, review, clean, review]:
            if src and len(selected) < n_per_group:
                selected.append(src.pop(0))
        # Fill remaining from any
        remaining = clean + review
        while len(selected) < n_per_group and remaining:
            selected.append(remaining.pop(0))
        sample.extend(selected)

    return sample


def main():
    parser = argparse.ArgumentParser(
        description="SZD-HTR: Multi-Model-Konsensus-Verifikation",
    )
    parser.add_argument("object_id", nargs="?", help="Object-ID (z.B. o_szd.161)")
    parser.add_argument("--collection", "-c", choices=list(COLLECTIONS.keys()))
    parser.add_argument("--sample", type=int, default=0,
                        help="Stratifiziertes Sample: N Objekte pro Gruppe")
    parser.add_argument("--max-images", type=int, default=0)
    parser.add_argument("--force", "-f", action="store_true")
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.object_id and not args.sample:
        parser.error("Entweder object_id oder --sample N angeben")
    if args.object_id and not args.collection:
        parser.error("--collection erforderlich bei object_id")

    if not GOOGLE_API_KEY and not args.dry_run:
        print("FEHLER: GOOGLE_API_KEY nicht gesetzt.")
        sys.exit(1)

    # Single object
    if args.object_id:
        print(f"Verifiziere {args.object_id} ({args.collection})...")
        result = verify_object(args.object_id, args.collection, args.max_images, args.force)
        sys.exit(0 if result else 1)

    # Sample mode
    sample = select_sample(args.sample)
    print(f"Stratifiziertes Sample: {len(sample)} Objekte")
    print()

    if args.dry_run:
        print(f"{'Object-ID':20s} {'Sammlung':20s} {'Gruppe':15s} {'Review':>6s}")
        print("-" * 65)
        for obj in sample:
            _, label = GROUP_LABELS.get(obj["group"], ("?", obj["group"]))
            review = "JA" if obj["needs_review"] else ""
            print(f"{obj['object_id']:20s} {obj['collection']:20s} {label:15s} {review:>6s}")
        return

    # Run verification
    print(f"Starte Konsensus-Verifikation: {len(sample)} Objekte, Modell B: {VERIFY_MODEL}")
    print("=" * 60)

    results = {"verified": 0, "moderate": 0, "review": 0, "divergent": 0, "failed": 0}
    for i, obj in enumerate(sample, 1):
        print(f"[{i}/{len(sample)}] {obj['object_id']} ({obj['collection']})")
        result = verify_object(obj["object_id"], obj["collection"], args.max_images, args.force)
        if result:
            cat = result["consensus"]["category"]
            key = cat.replace("consensus_", "")
            results[key] = results.get(key, 0) + 1
        else:
            results["failed"] += 1

        if i < len(sample):
            time.sleep(args.delay)

    print("=" * 60)
    print(f"Ergebnis: {results}")
    total = sum(results.values())
    if total > 0:
        verified_pct = results.get("verified", 0) / total * 100
        print(f"Konsensus-Rate: {verified_pct:.0f}% consensus_verified")


if __name__ == "__main__":
    main()
