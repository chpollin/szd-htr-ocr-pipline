"""CER/WER-Berechnung für SZD-HTR Qualitätsevaluierung.

Vergleicht Pipeline-Output mit manueller Referenztranskription.
Normalisierung gemäß annotation-protocol.md §5.
"""

import argparse
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


def normalize_text(text: str) -> str:
    """Normalize text for CER comparison per annotation-protocol.md §5.

    Steps: Unicode NFC, whitespace, hyphenation join, linebreaks → spaces,
    markup removal.
    """
    # §5.1 Unicode NFC
    text = unicodedata.normalize("NFC", text)
    # §5.1 CRLF → LF
    text = text.replace("\r\n", "\n")
    # §5.1 Trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    # §5.1 Multiple spaces → single space
    text = re.sub(r"[^\S\n]+", " ", text)

    # §5.2 Hyphenation join: hyphen + newline → join
    text = text.replace("-\n", "")

    # §5.3 Linebreaks → spaces (preserve paragraph breaks)
    text = text.replace("\n\n", "\x00")
    text = text.replace("\n", " ")
    text = text.replace("\x00", "\n")

    # §5.4 Markup removal (order matters)
    text = re.sub(r"~~(.*?)~~", r"\1", text)         # Streichung: keep content
    text = re.sub(r"\{(.*?)\}", r"\1", text)          # Einfügung: keep content
    text = re.sub(r"\[Stempel:\s*(.+?)\]", r"\1", text)  # Stempel: keep content
    text = re.sub(r"\[Marginalie:\]", "", text)        # Marginalie: remove
    text = re.sub(r"\[\.\.\.(\d+\.\.\.)?\]", "", text)  # Unleserlich: remove
    text = re.sub(r"\[\?\]", "", text)                 # Unsicher: remove

    # Final whitespace cleanup
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)  # Strip spaces around paragraph breaks
    text = text.strip()
    return text


def normalize_for_consensus(text: str) -> str:
    """Aggressive normalization for inter-model CER comparison.

    Ignores layout differences (indentation, numbering format) that are
    not transcription errors but formatting choices between models.
    """
    text = normalize_text(text)
    # Collapse all whitespace (spaces + paragraph breaks) to single space
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing spaces around punctuation
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def normalize_for_consensus_orderless(text: str) -> str:
    """Order-invariant normalization: sort lines before comparison.

    Handles reading-order divergence between models (e.g., marginalia
    read before/after main text, different column ordering).
    """
    text = normalize_text(text)
    # Split into lines, normalize each, remove very short fragments (<5 chars)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    lines = [l for l in lines if len(l) >= 5]
    lines.sort()
    result = " ".join(lines)
    result = re.sub(r"\s+([.,;:!?])", r"\1", result)
    return result.strip()


def word_overlap(text_a: str, text_b: str) -> float:
    """Jaccard word overlap: |intersection| / |union|. Order-invariant."""
    words_a = set(normalize_for_consensus(text_a).lower().split())
    words_b = set(normalize_for_consensus(text_b).lower().split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def cer(hypothesis: str, reference: str) -> float:
    """Character Error Rate: edit distance / len(reference).

    Uses SequenceMatcher for edit operations (substitutions + insertions + deletions).
    Returns 0.0 for identical strings, >1.0 if hypothesis is very different.
    """
    if not reference:
        return 0.0 if not hypothesis else 1.0
    sm = SequenceMatcher(None, reference, hypothesis)
    edits = 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            edits += max(i2 - i1, j2 - j1)
    return edits / len(reference)


def wer(hypothesis: str, reference: str) -> float:
    """Word Error Rate: edit distance on word tokens / len(reference words)."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    sm = SequenceMatcher(None, ref_words, hyp_words)
    edits = 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            edits += max(i2 - i1, j2 - j1)
    return edits / len(ref_words)


def error_breakdown(hypothesis: str, reference: str) -> dict:
    """Classify edit operations into substitutions, insertions, deletions."""
    sm = SequenceMatcher(None, reference, hypothesis)
    subs, ins, dels = 0, 0, 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "replace":
            subs += max(i2 - i1, j2 - j1)
        elif op == "insert":
            ins += j2 - j1
        elif op == "delete":
            dels += i2 - i1
    return {"substitutions": subs, "insertions": ins, "deletions": dels}


def extract_page_text(result_json: dict, page: int | None = None) -> str:
    """Extract transcription text from result JSON, optionally for a specific page."""
    pages = result_json.get("result", {}).get("pages", [])
    if page is not None:
        if 0 <= page < len(pages):
            return pages[page].get("transcription", "")
        return ""
    return "\n\n".join(p.get("transcription", "") for p in pages)


def evaluate(hypothesis: str, reference: str) -> dict:
    """Full evaluation: normalize both texts, compute CER, WER, and breakdown."""
    norm_hyp = normalize_text(hypothesis)
    norm_ref = normalize_text(reference)
    return {
        "cer": round(cer(norm_hyp, norm_ref), 4),
        "wer": round(wer(norm_hyp, norm_ref), 4),
        "errors": error_breakdown(norm_hyp, norm_ref),
        "ref_chars": len(norm_ref),
        "hyp_chars": len(norm_hyp),
        "ref_words": len(norm_ref.split()),
        "hyp_words": len(norm_hyp.split()),
    }


def main():
    parser = argparse.ArgumentParser(
        description="CER/WER-Berechnung: Pipeline-Output vs. Referenztranskription",
    )
    parser.add_argument("result", help="Pfad zur Ergebnis-JSON-Datei")
    parser.add_argument("reference", help="Pfad zur Referenz-Textdatei")
    parser.add_argument("--page", type=int, default=None,
                        help="Nur diese Seite vergleichen (0-basiert)")
    parser.add_argument("--json", action="store_true", help="Output als JSON")
    args = parser.parse_args()

    result_path = Path(args.result)
    ref_path = Path(args.reference)

    if not result_path.exists():
        print(f"FEHLER: {result_path} nicht gefunden")
        sys.exit(1)
    if not ref_path.exists():
        print(f"FEHLER: {ref_path} nicht gefunden")
        sys.exit(1)

    result_data = json.loads(result_path.read_text(encoding="utf-8"))
    reference_text = ref_path.read_text(encoding="utf-8")
    hypothesis_text = extract_page_text(result_data, args.page)

    result = evaluate(hypothesis_text, reference_text)
    result["object_id"] = result_data.get("object_id", result_path.stem)
    result["page"] = args.page

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Objekt:  {result['object_id']}")
        if args.page is not None:
            print(f"Seite:   {args.page}")
        print(f"CER:     {result['cer']:.2%}")
        print(f"WER:     {result['wer']:.2%}")
        print(f"Zeichen: {result['ref_chars']} (Ref) / {result['hyp_chars']} (HTR)")
        print(f"Wörter:  {result['ref_words']} (Ref) / {result['hyp_words']} (HTR)")
        e = result["errors"]
        print(f"Fehler:  {e['substitutions']} Sub, {e['insertions']} Ins, {e['deletions']} Del")


if __name__ == "__main__":
    main()
