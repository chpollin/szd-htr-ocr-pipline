"""SZD-HTR Batch-Transkription: Einzelobjekte oder ganze Sammlungen transkribieren."""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from google import genai

from config import (
    BACKUP_ROOT, BATCH_DELAY, COLLECTIONS, DATA_DIR, GOOGLE_API_KEY,
    GROUP_LABELS, MODEL, PROMPTS_DIR, results_dir_for,
)
from quality_signals import compute_signals
from tei_context import (
    context_from_backup_metadata, format_context, parse_tei_for_object,
    resolve_group,
)


# --- Prompts ---

def load_prompt(filename: str) -> str:
    """Load prompt text from a markdown file, extracting content from code blocks."""
    path = PROMPTS_DIR / filename
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    if not blocks:
        print(f"WARNUNG: Kein Codeblock in {filename}, verwende gesamten Text")
        return text.strip()
    if len(blocks) > 1:
        print(f"WARNUNG: {len(blocks)} Codeblöcke in {filename}, verwende ersten")
    return blocks[0].strip()


SYSTEM_PROMPT = load_prompt("system.md")

GROUP_PROMPTS = {
    "kurztext": load_prompt("group_d_kurztext.md"),
    "handschrift": load_prompt("group_a_handschrift.md"),
    "typoskript": load_prompt("group_b_typoskript.md"),
    "formular": load_prompt("group_c_formular.md"),
    "tabellarisch": load_prompt("group_e_tabellarisch.md"),
    "korrekturfahne": load_prompt("group_f_korrekturfahne.md"),
    "konvolut": load_prompt("group_g_konvolut.md"),
    "zeitungsausschnitt": load_prompt("group_h_zeitungsausschnitt.md"),
    "korrespondenz": load_prompt("group_i_korrespondenz.md"),
}


# --- Object Discovery ---

def discover_objects(collection: str) -> list[dict]:
    """List all objects in a collection from backup directories."""
    subdir = COLLECTIONS[collection]["subdir"]
    base = BACKUP_ROOT / subdir
    if not base.exists():
        print(f"FEHLER: Backup-Verzeichnis nicht gefunden: {base}")
        return []
    objects = []
    for obj_dir in sorted(base.glob("o_szd.*")):
        if (obj_dir / "metadata.json").exists() and (obj_dir / "images").exists():
            objects.append({
                "object_id": obj_dir.name,
                "collection": collection,
            })
    return objects


# --- Context Resolution ---

def resolve_context(object_id: str, collection: str) -> tuple[str, str, dict]:
    """Resolve group, context, and metadata for an object.

    Returns (group, context_string, metadata_dict).
    """
    pid = object_id.replace("_", ":")
    tei_file = DATA_DIR / COLLECTIONS[collection]["tei"]
    metadata = parse_tei_for_object(tei_file, pid)

    if metadata is None:
        subdir = COLLECTIONS[collection]["subdir"]
        meta_path = BACKUP_ROOT / subdir / object_id / "metadata.json"
        if meta_path.exists():
            metadata = context_from_backup_metadata(meta_path)
        else:
            metadata = {}

    group = resolve_group(metadata, collection)
    context = format_context(metadata)
    return group, context, metadata


# --- Image Loading ---

def load_images(object_id: str, collection: str, max_images: int = 0) -> list[tuple[str, bytes]]:
    """Load images for an object from the backup directory."""
    subdir = COLLECTIONS[collection]["subdir"]
    img_dir = BACKUP_ROOT / subdir / object_id / "images"
    if not img_dir.exists():
        raise FileNotFoundError(f"Bildverzeichnis nicht gefunden: {img_dir}")
    img_paths = sorted(img_dir.glob("IMG_*.jpg"), key=lambda p: int(p.stem.split("_")[1]))
    if not img_paths:
        raise FileNotFoundError(f"Keine Bilder gefunden in {img_dir}")
    images = []
    for img_path in img_paths:
        images.append((img_path.name, img_path.read_bytes()))
        if max_images and len(images) >= max_images:
            break
    return images


def load_backup_metadata(object_id: str, collection: str) -> dict:
    """Load backup metadata.json for GAMS URLs."""
    subdir = COLLECTIONS[collection]["subdir"]
    meta_path = BACKUP_ROOT / subdir / object_id / "metadata.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


# --- JSON Parsing ---

def _strip_codeblock(text: str) -> tuple[str, bool]:
    """Strip markdown code fences if present. Returns (cleaned, was_stripped)."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove opening fence (```json or ```)
        first_nl = stripped.index("\n") if "\n" in stripped else len(stripped)
        stripped = stripped[first_nl + 1:]
        # Remove closing fence
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3].rstrip()
        return stripped, True
    return text, False


def _fix_invalid_escapes(text: str) -> tuple[str, list[str]]:
    """Fix invalid JSON escape sequences like \\j, \\k etc.

    Returns (fixed_text, list of fixes applied).
    """
    valid_after_backslash = set('"\\bfnrtu/')
    fixes = []
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt in valid_after_backslash:
                result.append(text[i])
                result.append(nxt)
                i += 2
            else:
                fixes.append(f"\\{nxt}")
                result.append(nxt)
                i += 2
        else:
            result.append(text[i])
            i += 1
    return ''.join(result), fixes


def parse_api_response(text: str, object_id: str) -> tuple[dict, list[str]]:
    """Parse API response text into JSON, with sanitization.

    Returns (parsed_dict, log_messages).
    """
    log = []

    if not text:
        log.append(f"WARNUNG {object_id}: Leere API-Antwort, speichere Rohtext")
        return {"raw": ""}, log

    # Step 1: Try direct parse
    try:
        return json.loads(text), log
    except json.JSONDecodeError:
        pass

    # Step 2: Strip markdown codeblocks
    cleaned, was_stripped = _strip_codeblock(text)
    if was_stripped:
        log.append(f"FIX {object_id}: Markdown-Codeblock entfernt")
        try:
            return json.loads(cleaned), log
        except json.JSONDecodeError:
            pass
    else:
        cleaned = text

    # Step 3: Fix invalid escape sequences
    fixed, fixes = _fix_invalid_escapes(cleaned)
    if fixes:
        unique = sorted(set(fixes))
        log.append(f"FIX {object_id}: Ungueltige Escapes repariert: {', '.join(unique)}")
        try:
            return json.loads(fixed), log
        except json.JSONDecodeError:
            pass

    # Still failed
    log.append(f"WARNUNG {object_id}: JSON nicht parsebar nach Bereinigung, speichere Rohtext")
    return {"raw": text}, log


# --- Transcription ---

def transcribe_object(
    object_id: str,
    collection: str,
    max_images: int = 0,
    force: bool = False,
) -> tuple[bool, Path | None]:
    """Transcribe a single object. Returns (success, result_path)."""
    results_dir = results_dir_for(collection)
    out_path = results_dir / f"{object_id}_{MODEL}.json"

    if out_path.exists() and not force:
        return True, out_path  # Already done

    # Resolve context
    group, context, _ = resolve_context(object_id, collection)
    group_letter, group_label = GROUP_LABELS.get(group, ("?", group))

    # Load images
    try:
        images = load_images(object_id, collection, max_images)
    except FileNotFoundError as e:
        print(f"  FEHLER: {e}")
        return False, None

    print(f"  {len(images)} Bilder, Gruppe {group_letter}:{group_label}")

    # Build prompt
    group_prompt = GROUP_PROMPTS.get(group)
    if not group_prompt:
        print(f"  FEHLER: Kein Prompt für Gruppe '{group}'")
        return False, None
    user_prompt = f"{group_prompt}\n\n{context}\n\nTranskribiere die folgenden {len(images)} Faksimile-Scans."

    # Build content parts
    parts = []
    for name, img_bytes in images:
        parts.append(genai.types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        parts.append(f"[{name}]")
    parts.append(user_prompt)

    # Call Gemini
    client = genai.Client(api_key=GOOGLE_API_KEY)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
            ),
        )
    except Exception as e:
        print(f"  FEHLER bei API-Aufruf: {e}")
        return False, None

    result_text = response.text
    if not result_text:
        print(f"  FEHLER: Leere API-Antwort (response.text ist None/leer)")
        result_text = ""

    # Parse result (with sanitization and retry)
    result_json, parse_log = parse_api_response(result_text, object_id)
    for msg in parse_log:
        print(f"  {msg}")

    # Retry once if still unparseable
    if "raw" in result_json:
        print("  RETRY: Erneuter Versuch mit JSON-Hinweis...")
        retry_parts = list(parts) + ["Respond with valid JSON only, no markdown fences."]
        try:
            retry_resp = client.models.generate_content(
                model=MODEL,
                contents=retry_parts,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                ),
            )
            result_json, retry_log = parse_api_response(retry_resp.text, object_id)
            for msg in retry_log:
                print(f"  RETRY: {msg}")
        except Exception as e:
            print(f"  RETRY FEHLER: {e}")

    # Load backup metadata for GAMS URLs
    backup_meta = load_backup_metadata(object_id, collection)
    gams_images = [img["url"].replace("http://", "https://") for img in backup_meta.get("images", [])]

    # Build enriched output
    enriched = {
        "object_id": object_id,
        "collection": collection,
        "group": group,
        "model": MODEL,
        "metadata": {
            "title": backup_meta.get("title", ""),
            "language": backup_meta.get("language", ""),
            "images": gams_images,
        },
        "context": context,
        "result": result_json,
    }

    # Compute quality signals
    signals = compute_signals(result_json, enriched["metadata"], len(images))
    enriched["quality_signals"] = signals

    out_path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    confidence = result_json.get("confidence", "?")
    review = " [REVIEW]" if signals["needs_review"] else ""
    print(f"  -> {confidence}{review} -- {out_path.name}")
    return True, out_path


# --- Batch ---

def run_batch(
    objects: list[dict],
    delay: float = BATCH_DELAY,
    force: bool = False,
    max_images: int = 0,
) -> tuple[int, int, int]:
    """Transcribe multiple objects with rate limiting. Returns (done, skipped, failed)."""
    done, skipped, failed = 0, 0, 0
    total = len(objects)

    for i, obj in enumerate(objects, 1):
        oid = obj["object_id"]
        col = obj["collection"]
        results_dir = results_dir_for(col)
        out_path = results_dir / f"{oid}_{MODEL}.json"

        if out_path.exists() and not force:
            skipped += 1
            print(f"[{i}/{total}] {oid} -- uebersprungen")
            continue

        print(f"[{i}/{total}] {oid} ({col})")
        success, _ = transcribe_object(oid, col, max_images, force)
        if success:
            done += 1
        else:
            failed += 1

        # Rate limiting between API calls
        if i < total and success:
            time.sleep(delay)

    return done, skipped, failed


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="SZD-HTR: Transkription von Nachlassfaksimiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Beispiele:
  %(prog)s o_szd.161 --collection lebensdokumente   # Einzelnes Objekt
  %(prog)s --collection lebensdokumente              # Ganze Sammlung
  %(prog)s --collection werke --group korrekturfahne  # Nach Gruppe filtern
  %(prog)s --all --dry-run                            # Alle auflisten
  %(prog)s --all --limit 10                           # Erste 10 aller Sammlungen
""",
    )
    parser.add_argument("object_id", nargs="?", help="Object-ID (z.B. o_szd.161)")
    parser.add_argument("--collection", "-c", choices=list(COLLECTIONS.keys()),
                        help="Sammlung")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Alle Sammlungen")
    parser.add_argument("--group", "-g", choices=list(GROUP_PROMPTS.keys()),
                        help="Nur Objekte dieser Prompt-Gruppe")
    parser.add_argument("--limit", "-n", type=int, default=0,
                        help="Max. Anzahl Objekte")
    parser.add_argument("--max-images", type=int, default=0,
                        help="Max. Bilder pro Objekt (0=alle)")
    parser.add_argument("--delay", type=float, default=BATCH_DELAY,
                        help=f"Sekunden zwischen API-Calls (Default: {BATCH_DELAY})")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Bereits transkribierte überschreiben")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur auflisten, nicht transkribieren")
    args = parser.parse_args()

    # Validate arguments
    if args.object_id and not args.collection:
        parser.error("--collection ist erforderlich wenn ein object_id angegeben wird")
    if not args.object_id and not args.collection and not args.all:
        parser.error("Entweder object_id, --collection oder --all angeben")
    if not GOOGLE_API_KEY and not args.dry_run:
        print("FEHLER: GOOGLE_API_KEY nicht gesetzt.")
        print("  export GOOGLE_API_KEY=AIza...")
        sys.exit(1)

    # Single object mode
    if args.object_id:
        if args.dry_run:
            group, context, _ = resolve_context(args.object_id, args.collection)
            group_letter, group_label = GROUP_LABELS.get(group, ("?", group))
            print(f"{args.object_id}  {args.collection}  {group_letter}:{group_label}")
            print(f"\n{context}")
            return
        print(f"Transkribiere {args.object_id} ({args.collection})...")
        success, path = transcribe_object(
            args.object_id, args.collection, args.max_images, args.force
        )
        sys.exit(0 if success else 1)

    # Batch mode: discover objects
    collections = list(COLLECTIONS.keys()) if args.all else [args.collection]
    all_objects = []
    for col in collections:
        objects = discover_objects(col)
        # Filter by group if requested
        if args.group:
            filtered = []
            for obj in objects:
                group, _, _ = resolve_context(obj["object_id"], obj["collection"])
                if group == args.group:
                    filtered.append(obj)
            objects = filtered
        all_objects.extend(objects)

    if args.limit:
        all_objects = all_objects[:args.limit]

    # Dry run: list objects
    if args.dry_run:
        print(f"{'Object-ID':20s} {'Sammlung':20s} {'Gruppe':20s}")
        print("-" * 62)
        for obj in all_objects:
            group, _, _ = resolve_context(obj["object_id"], obj["collection"])
            group_letter, group_label = GROUP_LABELS.get(group, ("?", group))
            print(f"{obj['object_id']:20s} {obj['collection']:20s} {group_letter}:{group_label}")
        print(f"\n{len(all_objects)} Objekte")
        return

    # Run batch
    print(f"Starte Batch: {len(all_objects)} Objekte, Delay {args.delay}s")
    print("=" * 60)
    done, skipped, failed = run_batch(all_objects, args.delay, args.force, args.max_images)
    print("=" * 60)
    print(f"Fertig: {done} transkribiert, {skipped} übersprungen, {failed} fehlgeschlagen")


if __name__ == "__main__":
    main()
