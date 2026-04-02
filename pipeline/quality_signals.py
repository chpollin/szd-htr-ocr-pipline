"""Quality signals: automatische Qualitätsprüfung von Transkriptionsergebnissen.

Berechnet Signale gemäß verification-concept.md §2.3–2.5 und aggregiert
sie zu einem needs_review-Flag.

v1.2: Leerseiten-Klassifikation.
v1.4: Duplikat-Schwelle gesenkt (50 statt 200 Zeichen) fuer Halluzinationserkennung.
v1.5: DWR entfernt (rho=0.05, wertlos), marker_density aus needs_review entfernt.
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


# DWR (Dictionary Word Ratio) was removed in v1.5 — evaluated against 68 verified
# objects: Spearman rho=0.05, F1=0.20. It measured prose density, not quality.
# See evaluation-results.md §5.1 for full analysis.


def _classify_page(page: dict) -> str:
    """Classify page as 'content', 'blank', or 'color_chart' from notes + text."""
    notes = (page.get("notes", "") or "").lower()
    text = (page.get("transcription", "") or "").strip()
    # Color chart detection first — VLMs sometimes transcribe text even when a
    # color chart is visible, so check notes regardless of text length.
    if any(kw in notes for kw in ("farbskala", "farb-", "grauskala", "farbkeil",
                                   "color chart", "grey scale", "graustuf",
                                   "farbkarte", "color patches", "kodak",
                                   "farbkontroll", "farbkalibrier",
                                   "color control")):
        return "color_chart"
    if len(text) < 10:
        if any(kw in notes for kw in ("rückseite", "rueckseite", "leer", "blank",
                                       "keine beschriftung", "kein text")):
            return "blank"
        if not text:
            return "blank"
    return "content"


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
    content_text = ""  # Only content pages (no blanks/color charts)
    chars_per_page = []
    page_words = []
    page_types = []  # 'content', 'blank', 'color_chart'

    for page in pages:
        text = page.get("transcription", "")
        ptype = _classify_page(page)
        page["type"] = ptype
        page_types.append(ptype)
        chars_per_page.append(len(text))
        words = set(text.lower().split())
        page_words.append(words)
        all_text += text + "\n"
        if ptype == "content":
            content_text += text + "\n"

    total_chars = sum(c for c in chars_per_page)
    content_chars = [c for i, c in enumerate(chars_per_page) if page_types[i] == "content"]
    non_empty = [c for c in content_chars if c > 0]
    blank_pages = sum(1 for t in page_types if t == "blank")
    color_chart_pages = sum(1 for t in page_types if t == "color_chart")
    content_page_count = sum(1 for t in page_types if t == "content")
    empty_pages = len(chars_per_page) - len([c for c in chars_per_page if c > 0])
    total_words = len(all_text.split())
    med = median(non_empty) if non_empty else 0.0

    # Signal 1: Seitenlängen-Anomalie (nur content pages, Schwelle: <10% des Median)
    page_length_anomalies = []
    if med > 0:
        for i, c in enumerate(chars_per_page):
            if page_types[i] == "content" and 0 < c < 0.1 * med:
                page_length_anomalies.append(i)

    # Signal 2: Seiten-Bild-Abgleich (nur content pages vs. input images)
    # Blank/color chart pages are expected and don't count as mismatch
    n_pages = len(pages)
    effective_empty = sum(1 for i, c in enumerate(chars_per_page)
                         if c == 0 and page_types[i] == "content")
    page_image_mismatch = (
        n_pages != input_image_count
        or (content_page_count > 0 and effective_empty > content_page_count * 0.75)
    )

    # Signal 3: Duplikaterkennung (nur content pages, Jaccard > 0.9, beide > 50 Zeichen)
    duplicate_page_pairs = []
    for i in range(len(pages)):
        if page_types[i] != "content":
            continue
        for j in range(i + 1, len(pages)):
            if page_types[j] != "content":
                continue
            if chars_per_page[i] > 50 and chars_per_page[j] > 50:
                sim = _jaccard(page_words[i], page_words[j])
                if sim > 0.9:
                    duplicate_page_pairs.append([i, j])

    # Signal 4: Sprachkonsistenz
    # Nur flaggen wenn beide Seiten eine klare Sprache erkennen —
    # Zweig schrieb multilingual, leere/kurze Texte sollen nicht triggern
    expected_lang = _normalize_lang(metadata.get("language", ""))
    detected_lang = _detect_language(all_text)
    language_match = (
        not expected_lang  # Keine erwartete Sprache → kein Mismatch
        or not detected_lang  # Nicht genug Text → kein Mismatch
        or expected_lang == detected_lang
        or total_words < 50  # Zu wenig Text für verlässliche Erkennung
    )

    # Signal 5: Marker-Dichte
    n_uncertain = len(re.findall(r"\[\?\]", all_text))
    n_illegible = len(re.findall(r"\[\.\.\..*?\]", all_text))
    marker_density = (n_uncertain + n_illegible) / total_words if total_words > 0 else 0.0

    # Signal 6: Dictionary Word Ratio (DWR) — Anteil Wörterbuchwörter
    # Korreliert mit CER (Springmann 2016, Ströbel 2022)
    dwr_lang = detected_lang or expected_lang or "de"
    dwr_score = _compute_dwr(content_text, dwr_lang)

    # Signal 7: Textdichte relativ zur Gruppe — extern berechnet
    # (group_text_density braucht Gruppenstatistik, wird beim Backfill gesetzt)

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
    # low_dwr removed from needs_review (Session 20): Spearman rho=0.05,
    # F1=0.20 — no correlation with actual accuracy. DWR measures prose
    # density, not transcription quality. Kept as informational field.

    return {
        "version": "1.4",
        "total_chars": total_chars,
        "total_words": total_words,
        "total_pages": len(non_empty),
        "empty_pages": empty_pages,
        "blank_pages": blank_pages,
        "color_chart_pages": color_chart_pages,
        "content_pages": content_page_count,
        "input_images": input_image_count,
        "page_types": page_types,
        "chars_per_page": chars_per_page,
        "chars_per_page_median": round(med, 1),
        "marker_uncertain_count": n_uncertain,
        "marker_illegible_count": n_illegible,
        "marker_density": round(marker_density, 4),
        "dwr_score": round(dwr_score, 4),
        "duplicate_page_pairs": duplicate_page_pairs,
        "language_expected": expected_lang,
        "language_detected": detected_lang,
        "language_match": language_match,
        "page_length_anomalies": page_length_anomalies,
        "needs_review": len(reasons) > 0,
        "needs_review_reasons": reasons,
    }
