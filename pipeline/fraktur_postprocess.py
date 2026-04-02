"""Fraktur post-processing: dictionary-based correction of systematic VLM errors.

Prototype for evaluating Fraktur confusion pair correction on Zeitungsausschnitt
transcriptions. Uses pyspellchecker's German word frequency list as dictionary.

Approach:
  1. Tokenize transcription text into words
  2. For each word NOT in the German dictionary:
     - Generate single-substitution variants using Fraktur confusion pairs
     - If exactly 1 variant is a known dictionary word -> suggest correction
     - If 0 or 2+ variants match -> skip (ambiguous or unknown)
  3. Report suggested corrections without auto-applying

Usage:
  python pipeline/fraktur_postprocess.py results/aufsatzablage/o_szd.2217_*.json
  python pipeline/fraktur_postprocess.py --collection aufsatzablage --group zeitungsausschnitt
  python pipeline/fraktur_postprocess.py --collection aufsatzablage --dry-run

Requires: pip install pyspellchecker
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from spellchecker import SpellChecker
except ImportError:
    print("ERROR: pyspellchecker not installed. Run: pip install pyspellchecker")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Fraktur confusion pairs
# ---------------------------------------------------------------------------
# Each pair is (wrong_substring, correct_substring).
# Applied bidirectionally where noted; order matters for multi-char patterns.
# Derived from 28 documented agent-verification errors, primarily in
# Zeitungsausschnitt group (Fraktur typeface).

FRAKTUR_CONFUSIONS = [
    # Long s (ſ) misread as f — most frequent Fraktur error
    # NOTE: f->s is high-recall but causes false positives on real f-words.
    # We apply it only in word-medial positions (see generate_variants).
    ("f", "s"),
    # ft ↔ st confusion (related to long-s ligature ſt)
    ("ft", "st"),
    # Letter confusions in Fraktur blackletter
    ("D", "W"),   # Fraktur D/W look similar
    ("W", "D"),
    ("w", "m"),   # Fraktur w/m confusion
    ("m", "w"),
    ("ih", "l"),  # Fraktur l looks like ih
    ("l", "ih"),
    ("A", "N"),   # Fraktur A/N confusion
    ("N", "A"),
    ("h", "li"),  # Fraktur h/li confusion (less common)
    # Double-letter artifacts (VLM inserts extra letters)
    ("ss", "s"),
    ("ll", "l"),
]

# Pairs where substitution should only happen word-medially (not at position 0)
# to avoid false positives like "faßt" -> "saßt", "für" -> "sür"
MEDIAL_ONLY = {"f->s"}

# Additional whole-word overrides for known nonsense hallucinations
# that confusion pairs alone cannot fix (e.g., completely garbled readings).
# Format: {wrong_word: correct_word}
KNOWN_CORRECTIONS = {
    "Mitgebrine": "Mitbringsel",
    # Add more as they are discovered
}


# ---------------------------------------------------------------------------
# Dictionary wrapper
# ---------------------------------------------------------------------------

class FrakturDictionary:
    """German dictionary backed by pyspellchecker, with caching.

    Strategy for reducing false positives:
    - Proper nouns (capitalized, not at sentence start) are skipped
    - Very short words (<=2 chars) are assumed known
    - Domain-specific names added as extras
    """

    def __init__(self):
        self._spell = SpellChecker(language="de")
        self._cache: dict[str, bool] = {}
        # Add domain-specific words that pyspellchecker might not know.
        # Proper nouns, historical names, and SZD-specific terms.
        self._extras = {
            # Stefan Zweig context — names of people/places
            "walt", "whitman", "whitmans", "withmans",
            "freiligrath", "bazalgette", "bazalgettes",
            "reisiger", "rimbaud", "verhaeren", "verlaine", "mörike",
            "heyse", "federn", "hayek", "schlaf", "desbordes",
            "valmore", "fischer",
            # German literary/historical compound words
            "neurhythmiker", "menschheitsdichter", "prosaseiten",
            "lebenselement", "existenzwärme", "urkraft",
            "breithinrollenden", "niederstürzenden",
            "lebenstrunken", "menschgedicht", "lebenskräfte",
            "geistesleben", "stimmungsgedichtes", "bildkräftigkeit",
            "durchdringungsfähigkeit",
            # Common German words missing from pyspellchecker
            "faßt", "muß", "daß", "paßt",
        }

    def is_known(self, word: str) -> bool:
        """Check if a word is in the dictionary. Case-insensitive."""
        key = word.lower()
        if key in self._cache:
            return self._cache[key]
        # Very short words: skip (too many false positives, encoding fragments)
        if len(key) <= 3:
            self._cache[key] = True
            return True
        known = (key in self._spell) or (key in self._extras)
        self._cache[key] = known
        return known


# ---------------------------------------------------------------------------
# Correction engine
# ---------------------------------------------------------------------------

def generate_variants(word: str, confusions: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Generate single-substitution variants of a word using confusion pairs.

    Returns list of (variant, description) tuples.
    Only generates variants where exactly ONE confusion pair is applied once.
    """
    variants = []
    lower = word.lower()

    for wrong, correct in confusions:
        wl = wrong.lower()
        cl = correct.lower()
        rule_key = f"{wrong}->{correct}"
        medial_only = rule_key.lower() in {k.lower() for k in MEDIAL_ONLY}

        # Find all positions where the wrong pattern occurs
        start = 0
        while True:
            pos = lower.find(wl, start)
            if pos == -1:
                break
            # Skip word-initial substitutions for medial-only rules
            if medial_only and pos == 0:
                start = pos + 1
                continue
            # Build variant preserving original case where possible
            variant = word[:pos] + correct + word[pos + len(wrong):]
            # For case: if original was uppercase at this position, uppercase the replacement
            if pos < len(word) and word[pos].isupper() and len(correct) > 0:
                variant = word[:pos] + correct[0].upper() + correct[1:] + word[pos + len(wrong):]
            desc = f"{wrong}->{correct} at pos {pos}"
            variants.append((variant, desc))
            start = pos + 1

    return variants


def _is_likely_proper_noun(word: str, text: str, pos: int) -> bool:
    """Heuristic: is this word likely a proper noun (name, place)?

    Proper nouns are capitalized but not at sentence start.
    We check if the character before the word is a sentence-ending punctuation.
    """
    if not word[0].isupper():
        return False
    if word.isupper():
        return False  # All-caps = abbreviation, not proper noun
    # Check what's before this word
    before = text[max(0, pos - 3):pos].rstrip()
    if not before:
        return True  # Start of text — could be title/name
    if before[-1] in ".!?":
        return False  # Sentence start — not necessarily a proper noun
    if before[-1] == "\n":
        # Newline: could be line break in middle of sentence, or new sentence
        # Look further back
        further = text[max(0, pos - 30):pos].rstrip()
        if further and further[-1] in ".!?":
            return False
        return True  # Mid-paragraph line break — likely capitalized = proper noun
    return True  # Mid-sentence capitalization = proper noun


def find_corrections(text: str, dictionary: FrakturDictionary,
                     confusions: list[tuple[str, str]],
                     known_corrections: dict[str, str]
                     ) -> list[dict]:
    """Find suggested Fraktur corrections in a text.

    Returns list of correction dicts:
      {word, position, suggestion, rule, context}
    """
    corrections = []
    # Pre-pass: find words that are fragments of hyphenated line breaks.
    # Pattern: "word-\n" or "word=\n" (old German typographic convention)
    # These fragments should not be corrected individually.
    _LETTER = r"[A-Za-zÄÖÜäöüßàâéèêëïîôùûç]"
    hyphen_fragments = set()
    for m in re.finditer(rf"({_LETTER}+)[-=]\s*\n\s*({_LETTER}+)", text):
        # Both the prefix and suffix are fragments
        hyphen_fragments.add(m.start(1))  # position of first part
        hyphen_fragments.add(m.start(2))  # position of second part

    # Tokenize: split on whitespace and punctuation, keeping track of positions
    for match in re.finditer(r"[A-Za-zÄÖÜäöüßàâéèêëïîôùûç]+", text):
        word = match.group()
        pos = match.start()

        # Skip hyphenated line-break fragments
        if pos in hyphen_fragments:
            continue

        # Skip very short words (fragments from encoding issues, abbreviations)
        if len(word) < 4:
            continue

        # Check known corrections first (whole-word overrides)
        if word in known_corrections:
            corrections.append({
                "word": word,
                "position": pos,
                "suggestion": known_corrections[word],
                "rule": "known_correction",
                "context": text[max(0, pos - 20):pos + len(word) + 20],
            })
            continue

        # Skip if word is already in dictionary
        if dictionary.is_known(word):
            continue

        # Skip likely proper nouns — names, places etc. that won't be in dict
        # (but not if the word looks like a mangled common word)
        if _is_likely_proper_noun(word, text, pos) and len(word) >= 3:
            continue

        # Generate variants using confusion pairs
        variants = generate_variants(word, confusions)
        # Filter to variants that ARE in the dictionary
        valid = [(v, desc) for v, desc in variants if dictionary.is_known(v)]

        # Deduplicate by variant word (different rules can produce same result)
        seen = set()
        unique_valid = []
        for v, desc in valid:
            if v.lower() not in seen:
                seen.add(v.lower())
                unique_valid.append((v, desc))

        if len(unique_valid) == 1:
            variant, desc = unique_valid[0]
            corrections.append({
                "word": word,
                "position": pos,
                "suggestion": variant,
                "rule": desc,
                "context": text[max(0, pos - 20):pos + len(word) + 20],
            })
        elif len(unique_valid) > 1:
            # Ambiguous: multiple valid corrections possible
            corrections.append({
                "word": word,
                "position": pos,
                "suggestion": None,
                "rule": "ambiguous",
                "candidates": [v for v, _ in unique_valid],
                "context": text[max(0, pos - 20):pos + len(word) + 20],
            })

    return corrections


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------

def process_file(filepath: Path, dictionary: FrakturDictionary,
                 use_original: bool = False) -> Optional[dict]:
    """Process a single result JSON file.

    Args:
        filepath: Path to the result JSON.
        dictionary: FrakturDictionary instance.
        use_original: If True, use edit_history[0].original_transcription
                      instead of current transcription (for testing).

    Returns:
        Dict with corrections per page, or None if no corrections found.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    object_id = data.get("object_id", filepath.stem)
    group = data.get("group", "")
    pages = data.get("result", {}).get("pages", [])

    all_corrections = []
    for page in pages:
        page_num = page.get("page", 0)
        ptype = page.get("type", "content")
        if ptype != "content":
            continue

        # Choose text source
        if use_original and page.get("edit_history"):
            text = page["edit_history"][0].get("original_transcription", "")
        else:
            text = page.get("transcription", "")

        if not text.strip():
            continue

        corrections = find_corrections(text, dictionary, FRAKTUR_CONFUSIONS,
                                       KNOWN_CORRECTIONS)
        for c in corrections:
            c["page"] = page_num

        all_corrections.extend(corrections)

    if not all_corrections:
        return None

    return {
        "object_id": object_id,
        "group": group,
        "file": str(filepath),
        "corrections": all_corrections,
        "total_suggestions": sum(1 for c in all_corrections if c.get("suggestion")),
        "total_ambiguous": sum(1 for c in all_corrections if c.get("suggestion") is None),
    }


def collect_files(collection: Optional[str] = None,
                  group: Optional[str] = None,
                  results_dir: Optional[Path] = None) -> list[Path]:
    """Collect result JSON files to process."""
    if results_dir is None:
        results_dir = Path(__file__).parent.parent / "results"

    files = []
    if collection:
        search_dirs = [results_dir / collection]
    else:
        search_dirs = [d for d in results_dir.iterdir()
                       if d.is_dir() and d.name != "groundtruth"]

    for d in search_dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*_gemini-*.json")):
            if group:
                # Quick check: read JSON to filter by group
                try:
                    with open(f, encoding="utf-8") as fh:
                        data = json.load(fh)
                    if data.get("group") != group:
                        continue
                except (json.JSONDecodeError, KeyError):
                    continue
            files.append(f)

    return files


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fraktur post-processing: suggest corrections for systematic VLM errors"
    )
    parser.add_argument("files", nargs="*", help="Specific JSON files to process")
    parser.add_argument("-c", "--collection", help="Process all files in a collection")
    parser.add_argument("--group", default=None,
                        help="Filter by group (default: all; typical: zeitungsausschnitt)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only report what would change, don't modify files")
    parser.add_argument("--use-original", action="store_true",
                        help="Use edit_history[0].original_transcription for testing")
    parser.add_argument("--apply", action="store_true",
                        help="Actually apply corrections to the JSON files (NOT YET IMPLEMENTED)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all corrections including ambiguous ones")

    args = parser.parse_args()

    if args.apply:
        print("ERROR: --apply is not yet implemented. This is a prototype.")
        sys.exit(1)

    # Collect files
    if args.files:
        files = [Path(f) for f in args.files]
    elif args.collection:
        files = collect_files(collection=args.collection, group=args.group)
    else:
        # Default: zeitungsausschnitt across all collections
        files = collect_files(group=args.group or "zeitungsausschnitt")

    if not files:
        print("No files found to process.")
        sys.exit(0)

    print(f"Fraktur post-processing: {len(files)} file(s) to check")
    print(f"  Confusion pairs: {len(FRAKTUR_CONFUSIONS)}")
    print(f"  Known corrections: {len(KNOWN_CORRECTIONS)}")
    print()

    # Initialize dictionary
    dictionary = FrakturDictionary()

    total_suggestions = 0
    total_ambiguous = 0
    files_with_corrections = 0

    for filepath in files:
        result = process_file(filepath, dictionary, use_original=args.use_original)
        if result is None:
            continue

        files_with_corrections += 1
        total_suggestions += result["total_suggestions"]
        total_ambiguous += result["total_ambiguous"]

        print(f"--- {result['object_id']} ({result['group']}) ---")
        print(f"    File: {result['file']}")
        print(f"    Suggestions: {result['total_suggestions']}, "
              f"Ambiguous: {result['total_ambiguous']}")

        for c in result["corrections"]:
            if c.get("suggestion"):
                print(f"    p{c['page']:>2}: {c['word']!r} -> {c['suggestion']!r}  "
                      f"[{c['rule']}]")
                if args.verbose:
                    print(f"         context: ...{c['context']}...")
            elif args.verbose and c.get("candidates"):
                print(f"    p{c['page']:>2}: {c['word']!r} -> AMBIGUOUS  "
                      f"candidates: {c['candidates']}")

        print()

    # Summary
    print("=" * 60)
    print(f"Summary: {len(files)} files checked, {files_with_corrections} with corrections")
    print(f"  Total suggestions: {total_suggestions}")
    print(f"  Total ambiguous: {total_ambiguous}")

    if args.dry_run:
        print("\n  (dry-run mode: no files were modified)")


if __name__ == "__main__":
    main()
