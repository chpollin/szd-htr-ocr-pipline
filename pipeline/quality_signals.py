"""Quality signals: automatische Qualitätsprüfung von Transkriptionsergebnissen.

Berechnet 6 Signale gemäß verification-concept.md §2.3–2.5 und aggregiert
sie zu einem needs_review-Flag.
"""

import re
from statistics import median

# Stoppwort-Listen für Spracherkennung (Top-20 pro Sprache)
STOPWORDS = {
    "de": {"der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich",
           "des", "auf", "für", "ist", "im", "dem", "nicht", "ein", "eine", "als"},
    "fr": {"de", "la", "le", "et", "les", "des", "en", "un", "une", "du",
           "que", "est", "dans", "qui", "ne", "pas", "sur", "au", "ce", "il"},
    "en": {"the", "and", "of", "to", "in", "a", "is", "that", "for", "it",
           "with", "was", "on", "are", "as", "at", "be", "this", "have", "from"},
}

# Mapping von Metadaten-Sprachangaben auf Stoppwort-Keys
LANG_MAP = {
    "deutsch": "de", "german": "de", "de": "de",
    "französisch": "fr", "franzoesisch": "fr", "french": "fr", "fr": "fr",
    "englisch": "en", "english": "en", "en": "en",
}


def _detect_language(text: str) -> str:
    """Detect dominant language via stopword counting. Returns 'de'/'fr'/'en'/''."""
    words = set(re.findall(r"[a-zäöüàâéèêëïîôùûç]+", text.lower()))
    scores = {}
    for lang, stops in STOPWORDS.items():
        scores[lang] = len(words & stops)
    if not scores or max(scores.values()) < 3:
        return ""
    return max(scores, key=scores.get)


def _normalize_lang(raw: str) -> str:
    """Normalize metadata language string to stopword key."""
    if not raw:
        return ""
    first = raw.split(",")[0].split("(")[0].strip().lower()
    return LANG_MAP.get(first, "")


def _jaccard(words_a: set, words_b: set) -> float:
    """Jaccard similarity between two word sets."""
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def compute_signals(result_json: dict, metadata: dict, input_image_count: int) -> dict:
    """Compute quality signals from transcription result and metadata.

    Args:
        result_json: The "result" dict from the enriched JSON (has "pages", "confidence", etc.)
        metadata: The "metadata" dict (has "language", "title", "images")
        input_image_count: Number of images sent to the API

    Returns:
        quality_signals dict per verification-concept.md §2.5
    """
    pages = result_json.get("pages", [])
    all_text = ""
    chars_per_page = []
    page_words = []  # list of word-sets per page, for duplicate detection

    for page in pages:
        text = page.get("transcription", "")
        chars_per_page.append(len(text))
        words = set(text.lower().split())
        page_words.append(words)
        all_text += text + "\n"

    total_chars = sum(c for c in chars_per_page)
    non_empty = [c for c in chars_per_page if c > 0]
    empty_pages = len(chars_per_page) - len(non_empty)
    total_words = len(all_text.split())
    med = median(non_empty) if non_empty else 0.0

    # Signal 1: Seitenlängen-Anomalie
    page_length_anomalies = []
    if med > 0:
        for i, c in enumerate(chars_per_page):
            if 0 < c < 0.2 * med:
                page_length_anomalies.append(i)

    # Signal 2: Seiten-Bild-Abgleich
    n_pages = len(pages)
    page_image_mismatch = (
        n_pages != input_image_count
        or (input_image_count > 0 and empty_pages > input_image_count * 0.5)
    )

    # Signal 3: Duplikaterkennung (Jaccard > 0.8, beide > 100 Zeichen)
    duplicate_page_pairs = []
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            if chars_per_page[i] > 100 and chars_per_page[j] > 100:
                sim = _jaccard(page_words[i], page_words[j])
                if sim > 0.8:
                    duplicate_page_pairs.append([i, j])

    # Signal 4: Sprachkonsistenz
    expected_lang = _normalize_lang(metadata.get("language", ""))
    detected_lang = _detect_language(all_text)
    language_match = (
        not expected_lang  # Keine erwartete Sprache → kein Mismatch
        or not detected_lang  # Nicht genug Text → kein Mismatch
        or expected_lang == detected_lang
    )

    # Signal 5: Marker-Dichte
    n_uncertain = len(re.findall(r"\[\?\]", all_text))
    n_illegible = len(re.findall(r"\[\.\.\..*?\]", all_text))
    marker_density = (n_uncertain + n_illegible) / total_words if total_words > 0 else 0.0

    # Signal 6: Textdichte relativ zur Gruppe — erst ab 10 Objekten sinnvoll,
    # wird beim Backfill/Batch berechnet. Hier null setzen.
    # (group_text_density wird extern berechnet, weil es Gruppenstatistik braucht)

    # needs_review: Zusammengesetztes Flag (§2.4)
    reasons = []
    if page_length_anomalies:
        reasons.append("page_length_anomaly")
    if page_image_mismatch:
        reasons.append("page_image_mismatch")
    if duplicate_page_pairs:
        reasons.append("duplicate_pages")
    if not language_match:
        reasons.append("language_mismatch")
    if marker_density > 0.05:
        reasons.append("marker_density")

    return {
        "version": "1.0",
        "total_chars": total_chars,
        "total_words": total_words,
        "total_pages": len(non_empty),
        "empty_pages": empty_pages,
        "input_images": input_image_count,
        "chars_per_page": chars_per_page,
        "chars_per_page_median": round(med, 1),
        "marker_uncertain_count": n_uncertain,
        "marker_illegible_count": n_illegible,
        "marker_density": round(marker_density, 4),
        "duplicate_page_pairs": duplicate_page_pairs,
        "language_expected": expected_lang,
        "language_detected": detected_lang,
        "language_match": language_match,
        "page_length_anomalies": page_length_anomalies,
        "needs_review": len(reasons) > 0,
        "needs_review_reasons": reasons,
    }
