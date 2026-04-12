---
title: "Research Journal"
aliases: ["Journal"]
created: 2026-03-30
updated: 2026-04-03
type: log
status: stable
related:
  - "[[data-overview]]"
  - "[[verification-concept]]"
  - "[[annotation-protocol]]"
  - "[[evaluation-results]]"
---

# SZD-HTR — Research Journal

Chronologisches Log aller Arbeitssessions, Erkenntnisse und Entscheidungen.

---

## 2026-03-30 — Session 1: Projektplanung

### Was wurde gemacht
- CLAUDE.md gelesen und Projektanforderungen verstanden
- Implementierungsplan erstellt (→ [Plan.md](../Plan.md))
- Knowledge-Ordner als Research-Vault angelegt

### Entscheidungen
- **Gemini 3.1 Flash-Lite** als Transkriptions-Provider
  - Guenstig ($0.25/1M input), schnell, 1M-Token-Kontext, multimodal
  - Ermoeglicht Kosten-/Qualitaetsvergleich zwischen Providern
- **Kategoriale Konfidenz** (sicher/pruefenswert/problematisch) statt numerischer Scores
  - Erfahrung aus coOCR HTR: LLMs koennen Qualitaet nicht zuverlaessig numerisch einschaetzen

### Offene Fragen
- [x] Wie gut erkennt Gemini Kurrentschrift? → high confidence bei Zweigs Handschrift (Session 2)
- [ ] Optimale Bildgroesse fuer API-Calls? Originale 4912x7360 (~1.4MB)
- [ ] Lizenz klaeren: MIT fuer Code, CC-BY fuer Daten?

---

## 2026-03-30 — Session 2: Pipeline aufgebaut, erste Tests, alle Sammlungen analysiert

### TEI-Metadaten heruntergeladen und analysiert

Vier TEI-XML-Dateien von stefanzweig.digital heruntergeladen. Detaillierte Analyse: [[data-overview]].

| Sammlung | TEI-Eintraege | mit PID | Groesse |
|---|---|---|---|
| Lebensdokumente | 143 | 120 | 666 KB |
| Werke | 352 | 162 | 1.6 MB |
| Aufsatzablage | 624 | 624 | 2.5 MB |
| Korrespondenzen | 723 | 0 (TEI) | 1.5 MB |

Backup-Daten (lokal): 1186 Korrespondenzen, 625 Aufsaetze, 169 Faksimiles. **Gesamtbestand: ~2107 digitalisierte Objekte.**

### Dreischichtiges Prompt-System entwickelt

System-Prompt (global) → Gruppen-Prompt (A-E) → Objekt-Kontext (aus TEI). Prompts unter `pipeline/prompts/`.

### Erste Transkriptionstests

| Objekt | Gruppe | Sprache | Confidence | Beobachtung |
|---|---|---|---|---|
| Theaterkarte Jeremias (o:szd.161) | D | DE | high | Gedruckter + handschriftl. Text korrekt |
| Certified Copy of Marriage (o:szd.160) | C | EN | high | Formularfelder korrekt |
| Verlagsvertrag Grasset (o:szd.78) | B | FR | high | Franz. Vertragstext, Durchstreichungen erkannt |
| Tagebuch 1918 (o:szd.72) | A | DE | high | Zweigs Handschrift fluessig gelesen |

**Kernbefund:** Gemini 3.1 Flash Lite liefert auf allen 4 Gruppen (A-D) high confidence. Zweigs Handschrift wird fluessig transkribiert.

### Neue Prompt-Gruppen aus Sammlungsanalyse

| Gruppe | Quelle | Objekte | Besonderheit |
|---|---|---|---|
| F: Korrekturfahne | Werke + Aufsatz | ~55 | Gedruckter Text + handschriftliche Korrekturen |
| G: Konvolut | Werke | 24 | Gemischte Materialien |
| H: Zeitungsausschnitt | Aufsatzablage | 312 | Gedruckt, oft Fraktur |
| I: Korrespondenz | Korrespondenzen | ~1186 | Handschriftliche Briefe |

### Erkenntnisse

1. **GAMS-URLs funktionieren als direkte Bildquellen** — kein Download/Hosting noetig.
2. **Korrespondenzen-TEI** hat nur Verzeichnis-Charakter. Metadaten aus Backup-metadata.json.
3. **Erwin Rieger** zweithaeufigste Hand in Aufsatzablage (225x) — eigene Handschrift.
4. **Zeitungsausschnitte (312)** brauchen eigenen Fraktur-Prompt.
5. **Lotte Zweig** zweithaeufigste Hand in Werken (83x).

---

## 2026-03-30 — Session 3: Phase 2 abgeschlossen, alle Sammlungen integriert

### Neue Gruppen-Prompts

- `group_f_korrekturfahne.md` — Gedruckter Text + Korrekturen
- `group_h_zeitungsausschnitt.md` — Zeitungsdruck, Fraktur-Hinweise
- `group_i_korrespondenz.md` — Briefstruktur, Postkarten-Doppelseiten

Gruppe G (Konvolut) bewusst aufgeschoben — zu wenige Objekte, zu heterogen.

### Pipeline auf Multi-Collection erweitert

`test_single.py` refactored mit `COLLECTIONS`-Dict, Enriched JSON-Output, `--list`. Neue Module: `tei_context.py`, `build_viewer_data.py`.

### Drei neue Test-Objekte

| Objekt | Sammlung | Gruppe | Confidence | Beobachtung |
|---|---|---|---|---|
| Der Bildner (o:szd.287) | Werke | F | high | Rodin-Gedicht fehlerfrei, Stempel erkannt |
| Aus der Werkstatt (o:szd.2215) | Aufsatzablage | H | high | Antiqua (kein Fraktur-Test) |
| Brief an Fleischer (o:szd.1079) | Korrespondenzen | I | high | Jugendhandschrift (1901) |

**Gesamtstand: 7/7 high confidence, alle 4 Sammlungen abgedeckt.**

### Erkenntnisse

1. Gemini meistert alle Dokumenttypen — kein einziges Objekt unter high.
2. Fraktur noch nicht getestet (Antiqua-Zeitungsausschnitt).
3. Enriched JSON-Format vereinfacht den Viewer-Build.

---

## 2026-03-31 — Session 4: Cleanup und Refactoring vor Phase 3

### Kernarbeiten

- `pipeline/config.py` — Gemeinsame Konfiguration (Pfade, Collections, Groups, API-Keys via .env)
- `requirements.txt` — Formale Dependencies
- Auto-Kontext aus TEI: `resolve_context()` ersetzt ~100 Zeilen manuelle Context-Strings
- Bug-Fix `resolve_group()`: Formular-Checks vor generischen Typoskript-Check

### Erkenntnisse

1. **Auto-Kontext funktioniert zuverlaessig**: 6/7 direkt aus TEI, 1/7 ueber Backup-Fallback.
2. **resolve_group() braucht semantische Ordnung**: Klassifikation vor Objekttyp pruefen.
3. **Gemeinsame config.py eliminiert Drift** zwischen Scripts.

---

## 2026-03-31 — Session 5: Phase 3 abgeschlossen, Batch-CLI und erster Lauf

### pipeline/transcribe.py

CLI-Modi: Einzelobjekt, Sammlung, `--all`, `--group`, `--limit`, `--force`, `--delay`, `--max-images`, `--dry-run`.

### Object Discovery

Primaerquelle: Backup-Verzeichnisse (TEI lueckenhaft bei PIDs).

| Sammlung | Backup-Objekte | PIDs in TEI |
|---|---|---|
| Lebensdokumente | 127 | 121 (85%) |
| Werke | 169 | 163 (46%) |
| Aufsatzablage | 625 | 625 (100%) |
| Korrespondenzen | 1186 | 0 |
| **Gesamt** | **2107** | |

### Erster Batch-Lauf: 5 Lebensdokumente

o_szd.100-104, alle Typoskript, alle high confidence. Skip-Logik funktioniert. **Gesamtstand: 12 Objekte.**

### Erkenntnisse

1. **Backup-Dirs zuverlaessiger als TEI** fuer Object Discovery.
2. **2s Delay reicht** fuer Rate-Limiting.
3. **Windows-Encoding (cp1252)**: Unicode-Zeichen verursachen Fehler → ASCII-Alternativen.

---

## 2026-04-01 — Session 6: Frontend-Refactoring, Verifikationskonzept

### CLAUDE.md ueberarbeitet

Veraltete Objektzahlen, Modell-Widerspruch (Claude als primaer, nur Gemini implementiert), Phasen inkonsistent. Komplett neu geschrieben, Plan.md als einzige Wahrheitsquelle.

### Frontend: Zwei Dateien → Single-Page-App

Vorher: `index.html` (Scroll-Dump) + `viewer.html` (Side-by-Side). Nachher:

| Datei | Funktion |
|---|---|
| `docs/index.html` | HTML-Skelett, Help-Modal |
| `docs/app.css` | SZD-Design-System (Burgundy/Gold, Source Serif/Sans) |
| `docs/app.js` | Routing, Katalog, Viewer, Edit, Export |

**Daten-Split:** `catalog.json` (~6 KB Metadaten) + `data/{collection}.json` (on-demand). Features: Sortierbare Tabelle, Hash-Routing (`#view/{id}/{page}`), Side-by-Side Viewer, GAMS-Thumbnails, Inline-Edit, JSON-Export.

**Design-System:** Burgundy `#631a34`, Gold `#C2A360`, Cream `#FAF8F3`, Source Serif 4, Source Sans 3, JetBrains Mono.

### Verifikationskonzept: 3 Ebenen

| Ebene | Signal | Staerke |
|---|---|---|
| 1 | Unsicherheits-Marker (`[?]`, `[...]`) | Stark |
| 2 | VLM-Selbsteinschaetzung | Schwach |
| 3 | Textstatistik (Zeichenzahl, Leerseiten) | Mittel |

Befund: 12/12 "high confidence", fast keine Marker. VLMs ueberschaetzen systematisch ihre Leistung → staerkere Metriken noetig.

### Lane 1 Bericht

**Katalog:** Typ-Spalte zeigt TEI `classification` (Verlagsvertraege, Tagebuecher) statt Prompt-Gruppe. Tooltip zeigt `objecttyp`.

**quality_signals-UI vorbereitet:** Review-Spalte (Burgundy/Gruen-Badge, sortierbar, Toggle-Filter), Qualitaets-Panel im Viewer, Seiten-Anomalie-Marker. Graceful Degradation wenn Felder fehlen.

**Neue Felder in catalog.json:** `titleClean`, `signature`, `classification`, `objecttyp`, `thumbnail`, `pageCount`, `verification`.

**Interface-Vertrag fuer L3:** `obj.needsReview` (boolean), `obj.needsReviewReasons` (string[]), `obj.quality_signals` (ganzes Objekt), `obj.quality_signals.page_length_anomalies` (int[]).

**Befunde fuer L2:** 12/16 Objekte haben 0 Marker. Marker-Dichte ist kein negatives, nur positives Signal. TEI-Klassifikation nutzbar fuer Sampling-Strategie.

Geloeschte Dateien: `docs/viewer.html`, `docs/data.json`.

---

## 2026-04-01 — Session 7: Forschungsleitstelle, 3 Lanes, Gruppenabdeckung 9/9

### Lane-System initialisiert

Drei parallele Claude-Code-Agents: L1 (Frontend), L2 (Methodik), L3 (Backend). Koordination ueber [Lane.md](../Lane.md).

### L3: Gruppenabdeckung vervollstaendigt

| Objekt | Sammlung | Gruppe | Confidence | Beobachtung |
|---|---|---|---|---|
| o_szd.143 (Kontorbuch) | Lebensdokumente | E | high | Pipe-getrennte Spalten |
| o_szd.174 (Adressbuch) | Lebensdokumente | E | high | Tabellarisch |
| o_szd.2232 (Fraktur 1901) | Aufsatzablage | H | high | **Fraktur funktioniert** |
| o_szd.277 (Der Fall von Byzanz) | Werke | G | medium | Erstes non-high — heterogene Korrekturen |

**Alle 9 Gruppen A-I haben mindestens ein Testobjekt. Gesamtstand: 16 Objekte (15x high, 1x medium).**

### L2: Methodische Deliverables

- [[verification-concept]] v2 (5 Abschnitte, Literatur-Review mit 6 Papers)
- [[annotation-protocol]] (8 Abschnitte, Normalisierung, Beispiele)
- [[verification-concept]] (5 Seiten, Pruefprotokoll, Eskalationsschwellen)

### L1: quality_signals-UI vorbereitet

Review-Spalte, Qualitaets-Panel, Seiten-Anomalie-Marker im Code, wartet auf L3-Daten.

### Entscheidungen

- Pilot vor vollem GT-Sample (CER unbekannt)
- quality_signals sofort implementieren (kostenlos, kein GT noetig)
- Cross-Model: Agreement-First-Strategie
- Claude Sonnet als zweites Modell

---

## 2026-04-01 — Session 8: Interchange-Format, Selbstkritik, Korrekturen

### L2: Deliverables abgeschlossen

- **htr-interchange-format.md** geschrieben — JSON Schema v0.1, Abgrenzung ALTO/PAGE/hOCR, Beispiel basierend auf o_szd.100.
- **verification-concept.md §1.9** geprueft und bestaetigt — keine Aenderungen noetig.
- Schritt 1 + 2 der L2-Auftraege erledigt. Schritt 3+4 blockiert (warten auf Pilot-Durchfuehrung durch Operator).

### Selbstkritische Review aller knowledge-Dokumente

Systematische Pruefung aller 6 knowledge-Dateien + Lane.md auf Konsistenz, Korrektheit und empirische Fundierung.

**Korrekturen durchgefuehrt:**
- **verification-concept.md**: Objektzahlen 12→16, Konfidenz "alle high" → "15 high + 1 medium", Gruppe G ins Sample-Design aufgenommen (31 statt 30), Anachronismus direkt in Fehlertaxonomie-Tabelle §1.5, empirische Einordnung der quality_signals ergaenzt (10/16 flagged = zu aggressiv)
- **journal.md**: Session 8 nachgetragen

**Kritische Befunde:**
1. **Marker-Problem bestaetigt:** 57.000 Zeichen, 2 Marker. marker_density ist kein funktionierendes Signal.
2. **quality_signals zu aggressiv:** 10/16 (63%) als needs_review geflaggt — hauptsaechlich page_image_mismatch bei normalen Leerseiten.
3. **Gruppen-Prompts:** Strukturelle Guidance (Briefformat) wirkt. Vorsichts-Guidance (Marker setzen bei Kurrent-Ambiguitaeten) wird ignoriert.
4. **Interchange-Format moeglicherweise verfrueeht:** Sinnvoll als Analyse, aber Schema vor CER-Kenntnis wenig dringend.
5. **30-Objekt-Sample:** Konkretes Design ist Platzhalter — haengt komplett vom Pilot ab.

### Entscheidungen

- Pilot bleibt der kritische naechste Schritt — alles andere ist Theorie
- quality_signals-Schwellenwerte muessen nach Pilot kalibriert werden (page_image_mismatch braucht Leerseiten-Toleranz)
- Prompt-Experiment ist wichtiger als gedacht (Evidenz fuer Wirkungslosigkeit der Vorsichts-Prompts)

---

## 2026-04-01 — Session 9: Selbstkritische Review

### Systematische Pruefung aller knowledge-Dokumente

Alle 6 knowledge-Dateien + Lane.md auf Konsistenz, empirische Fundierung und Redundanz geprueft.

### Korrekturen

- **verification-concept.md**: Objektzahlen 12→16, Konfidenz 15h+1m, Gruppe G ins Sample (31 statt 30), Anachronismus in Fehlertaxonomie-Tabelle §1.5, empirische Einordnung der quality_signals in §2.3
- **verification-concept.md §1.9**: Prompt-Wirksamkeit als neue Frage in §3.1

### Empirische Befunde (aus 16 Ergebnis-JSONs)

1. **Marker-Problem**: 57.000 Zeichen, 2 Marker. marker_density ist kein Signal.
2. **quality_signals**: 10/16 (63%) als needs_review — zu aggressiv, hauptsaechlich page_image_mismatch.
3. **Gruppen-Prompts**: Strukturelle Guidance wirkt (Briefformat), Vorsichts-Guidance ignoriert (0 [?]-Marker bei Kurrent).
4. **o_szd.143**: Nur 20 Zeichen — moeglicherweise Pipeline-Problem (ungeklaert).

---

## 2026-04-01 — Session 11: Verification-by-Vision, Build, Lane-Updates

### Forschungsleitstelle: Verification-by-Vision getestet

8 Objekte via Claude Code Vision verifiziert (Bild lesen + Transkription vergleichen). 8 von 9 Gruppen abgedeckt:
- o_szd.161 (D Kurztext): `llm_verified` — null Fehler
- o_szd.72 (A Handschrift/Kurrent): `llm_error_suggestion` — Kurrent-Ambiguitaeten, keine Halluzinationen
- o_szd.277 (G Konvolut): `llm_error_suggestion` — klare Fehler ("entbalten", "Ictreesten") in Korrekturschicht
- o_szd.139 (C Formular): `llm_error_suggestion` — minor ("Datum:"-Label inkonsistent)
- o_szd.1887 (F Korrekturfahne): `llm_error_suggestion` — Drucktext OK, handschriftl. Vermerke problematisch
- o_szd.2232 (H Zeitungsausschnitt/Fraktur): `llm_error_suggestion` — 3 typische Fraktur-Fehler (fl-Ligatur, langes s, u/n)
- o_szd.1079 (I Korrespondenz): `llm_error_suggestion` — "Gerichte"→"Gedichte" (d/r), Ortsname "Klard" existiert nicht
- o_szd.147 (C Formular): **BROKEN** — 64 Bilder, 0 Seiten transkribiert (Pipeline-Bug)

Spec geschrieben: [[verification-by-vision]] (10 Abschnitte, JSON-Schema, empirische Befunde).

### Build ausgefuehrt

`build_viewer_data.py`: 62 Objekte im Frontend (46 Lebensdokumente, 13 Werke, 2 Aufsatzablage, 1 Korrespondenz).

### Lane.md aktualisiert (v0.5)

- Forschungsleitstelle als eigene Sektion mit Auftraegen
- L1: Schritt 3+4 als erledigt (Dashboard, Diff-Prototyp)
- L2: neue Schritte 5-7
- L3: Status auf ~62 Objekte, Interchange-Export als Schritt 6

### Erkenntnisse

1. **Verification-by-Vision funktioniert** — actionable Fehler in ~2 Min/Objekt, kein API-Cost fuer Claude-Kanal.
2. **Muster:** Drucktext korrekt, Handschrift gut, Korrekturen/Vermerke schwach (~60-70%).
3. **Pipeline-Bug:** Objekte mit vielen Bildern (o_szd.147: 64 Bilder) erzeugen leere Ergebnisse.
4. **Methodischer Beitrag:** VbV ist der staerkste Verifikationsansatz im Projekt — direkter Bild↔Text-Vergleich statt nur Textvergleich. Fuer den Aufsatz relevant.

---

## 2026-04-01 — Session 12: Mapping-Templates, JSON-Schema, DIA-XAI-Integration

### L2: 3 Bonus-Deliverables

**1. JSON-Schema als validierbare Datei**
`schemas/htr-interchange-v0.1.json` — das Schema aus htr-interchange-format.md §3 als eigenstaendige Datei. Aenderungen gegenueber Codeblock: `$id` auf GitHub Pages URL, `source.language` mit Regex-Pattern (`^[a-z]{2,3}$`), `source.document_type` als kontrolliertes Vokabular (14 Enum-Werte). Validiert mit `python -m json.tool`.

**2. DIA-XAI-Integrationskonzept**
`knowledge/dia-xai-integration.md` — 5 Abschnitte:
- Pipeline-Diagramm SZD-HTR → DIA-XAI
- EQUALIS-Mapping: 5 Dimensionen (E/QUA/L/I/S) auf konkrete SZD-HTR-Datenquellen
- Metriken-Export (`dia-xai-metrics-v1` JSON)
- Zeitplan: Was muss vor DIA-XAI Phase 1 (Mai 2026) fertig sein
- UC3 (HTR-Verifikation) als Ziel-Use-Case

### Erkenntnisse

1. **DIA-XAI ist Aggregator, nicht Verifikationstool** — importiert Metriken-JSON, macht keine eigene Analyse. Die Verifikation passiert in SZD-HTR (VbV und Expert-Review).
2. **EQUALIS-Scalability (S-Dimension)** profitiert besonders von SZD-HTR: 9 Gruppen × 4 Sprachen × 6+ Haende = natuerliche Varianz.
3. **Kritischer Pfad unveraendert:** Pilot (5 Seiten) muss vor DIA-XAI Phase 1 fertig sein.

---

## 2026-04-01 — Session 13: Quality Infrastructure, Batch-Lauf, Modellkonsensus

**Schwerpunkt:** Pipeline-Qualitaetsinfrastruktur aufgebaut, parallelen Batch gestartet, Forschung zu GT-freier Qualitaetsbewertung.

**Neue Pipeline-Module:**
- `evaluate.py`: CER/WER-Berechnung mit vollstaendiger Normalisierung (annotation-protocol.md §5)
- `quality_report.py`: Aggregierte Qualitaetsstatistiken pro Gruppe/Sammlung
- quality_signals v1.1: Schwellenwerte rekalibriert basierend auf Datenanalyse (68% → 44% needs_review)
- Exponential Backoff (429-Retry) in transcribe.py fuer parallele Batch-Laeufe

**Rekalibrierungsergebnisse (87 Objekte):**
- duplicate_pages: 25 → 17 (Jaccard 0.9 + min 200 chars)
- page_image_mismatch: 21 → 7 (75% statt 50% empty threshold)
- page_length_anomaly: 12 → 5 (10% statt 20% median)
- Kerninsight: Signale fingen Sammlungseigenschaften (leere Rueckseiten, Cover), nicht Fehler

**Batch-Lauf:** 4 parallele Prozesse (Korrespondenzen, Aufsatzablage, Lebensdokumente, Werke), delay 4s. ~360+ Objekte fertig und wachsend. Keine Rate-Limit-Probleme bei ~60 RPM effektiv.

**Broken Objects:** 3/5 repariert (o_szd.147, o_szd.223, o_szd.245). 2 bleiben kaputt: o_szd.267 (107 Bilder, zu gross) und o_szd.2230 (leere API-Antwort).

**Forschung GT-freie Qualitaetsbewertung:**
- Gemini logprobs: NICHT verfuegbar fuer Flash Lite Preview (getestet, 400 INVALID_ARGUMENT). Verfuegbar fuer gemini-2.0-flash.
- Aktuellste Literatur recherchiert: Zhang et al. 2025 (Consensus Entropy, ICLR 2026), Risk-Controlled VLM OCR (arXiv 2026), Beyene & Dancy 2026 (Survey)
- Kernentscheidung: **Modellkonsensus statt manuellem GT** — 3 Modelle (Flash Lite + Flash + Claude Judge) als automatische GT-Generierung
- verification-concept.md um Abschnitt 7 (Modellkonsensus) erweitert

**Entscheidungen:**
- DWR (Dictionary Word Ratio) als ergaenzendes Signal — einfach, bewaehrt, aber nicht primaer
- PPPL (Pseudo-Perplexity) auf spaeter verschoben — zu schwere Dependency (transformers+torch)
- Modellkonsensus-Ansatz als naechster Schritt statt manuellem Pilot

---

## 2026-04-02 — Session 14: Modellkonsensus-Metriken v2, GT-Pipeline, Frontend Review

**Schwerpunkt:** Modellkonsensus-Validierung mit verbesserten Metriken, GT-Erzeugung mit 3 Modellen, Frontend-Erweiterung fuer Expert-Review.

### Modellkonsensus-Metriken v2

- **Problem identifiziert:** Alte CER-only-Metrik produzierte 74% "divergent" — hauptsaechlich wegen Reading-Order-Divergenz (Marginalia, Spalten) und Seiten-Halluzination, nicht wegen Lesefehler.
- **Neue Metriken in evaluate.py:**
  - `normalize_for_consensus_orderless()`: Sortiert Zeilen vor Vergleich
  - `word_overlap()`: Jaccard-Aehnlichkeit auf Wortmengen (order-invariant)
  - `effective_cer`: Minimum aus ordered und orderless CER
- **4-Tier-Klassifikation:** verified / moderate / review / divergent (statt 3-Tier)
  - word_overlap >= 0.90 begrenzt Kategorie auf maximal "moderate"
  - word_overlap >= 0.75 ergibt "review" (neues Zwischenniveau)
- **Ergebnis (27 Objekte, 3/Gruppe):** 26% verified, 33% moderate, 15% review, 26% divergent (vorher: 11% verified, 74% divergent)

### Kernerkenntnisse aus Modellkonsensus-Analyse

1. **Reading-Order-Divergenz**: o_szd.142 hat CER 55% aber word_overlap 100% — identische Woerter in anderer Reihenfolge.
2. **Seiten-Halluzination**: Flash Lite dupliziert gelegentlich Seiten (o_szd.101, Seiten 3/4). quality_signals v1.4: Duplikat-Schwelle 200→50 Zeichen.
3. **Bleed-Through**: VLM transkribiert durchscheinenden Rueckseiten-Text. System-Prompt Regel 9 eingefuegt.
4. **Korrekturfahnen geloest**: 3/3 verified, <1% CER. Gedruckter Text mit Korrekturen ist kein Problem.
5. **Korrespondenzen bleiben schwer**: 3/3 divergent, 59-104% CER. Zweigs Handschrift in Briefen ist genuinely ambig.

### GT-Pipeline (generate_gt.py)

- 18 Objekte (stratifiziert, 2/Gruppe + 3 Korrespondenzen) mit Gemini 3.1 Pro transkribiert
- 3-Modell-Merge: Flash Lite (A) + Flash (B, aus Modellkonsensus) + Pro (C)
- Merge-Logik: consensus_3of3 (CER <2% paarweise) / majority_2of3 (CER <5%) / pro_only
- **Ergebnis (46 Content-Seiten):** 15 Modellkonsensus (33%), 20 Mehrheit (43%), 11 Pro-only (24%)
- Korrekturfahne o_szd.1888: 3/3 Modellkonsensus auf allen Content-Seiten
- GT-Drafts in `results/groundtruth/{object_id}_gt_draft.json`

### Frontend: GT Review-Modus

- "GT Review"-Button im Viewer (nur localhost)
- 3-Varianten-Panel: Flash Lite / Flash / Pro mit Click-to-Select
- Source-Badges: gruen (3/3), gelb (2/3), rot (Pro only)
- Approve-Button pro Seite, localStorage-Persistenz
- JSON-Export als `{object_id}_gt.json` mit Expert-Metadaten
- `build_viewer_data.py` erzeugt `docs/data/groundtruth.json` (18 Objekte)

### Neue Dateien

- `pipeline/generate_gt.py` — GT-Erzeugung mit 3 Modellen
- `pipeline/evaluate.py` — erweitert um `normalize_for_consensus_orderless()`, `word_overlap()`
- `docs/data/groundtruth.json` — GT-Drafts fuer Frontend

### Entscheidungen

| Entscheidung | Begruendung |
|---|---|
| word_overlap als order-invariante Metrik | CER bestraft Reading-Order-Divergenz unfair; Jaccard auf Wortmengen ist robust |
| 4-Tier statt 3-Tier Klassifikation | "review" als Zwischenstufe fuer Objekte mit 75-90% word_overlap |
| Gemini Pro statt Claude als 3. GT-Modell | Gleiche API, kein Provider-Wechsel, staerkstes Gemini-Modell |
| 5-Seiten-Pilot uebersprungen | Modellkonsensus-Validierung + GT-Pipeline beantworten die Pilot-Fragen empirisch |
| Bleed-Through im System-Prompt | Effizienter als Post-Processing; VLM soll es gar nicht erst transkribieren |

### Frontend-Upgrade (Lane 1, parallel)

- **build_viewer_data.py Bug-Fixes:** Consensus-Dateien aus Katalog entfernt (583→564 Objekte), quality_signals Naming-Mismatch behoben (camelCase→snake_case), alle 20 QS-Felder inkl. dwr_score exportiert
- **Modellkonsensus-Daten im Frontend:** 29 Objekte mit consensus category/CER im Katalog, volle Modellkonsensus-Daten (transcription_a/b) in Collection-JSONs fuer Diff-View
- **Diff-Ansicht:** DIFF_PLACEHOLDER durch echte Modellkonsensus-Daten ersetzt, CER im Header, dynamische Modell-Namen, Button disabled ohne Modellkonsensus
- **Enhanced Stats Dashboard:** Seiten-Stats, Zeichen-Summen, Konfidenz-Verteilung, Review-%, DWR-Durchschnitt, Modellkonsensus-Uebersicht
- **Neue Anzeigen:** DWR-Badge im Viewer, Page-Type-Badges (Leer/Farbskala), Modellkonsensus-Status V/M/R/D im Katalog + Viewer, per-Page Agreement-Dots, Modellkonsensus-Filter
- **Mobile:** Card-Layout fuer Katalog unter 600px
- **Refactoring (7x):** Modellkonsensus-Konstanten extrahiert, redundante Aufrufe entfernt, Inline-Styles→CSS, clearFilters vereinfacht, Feature-Flags gecacht, CSS-Fallback fuer Thumbnails

### Layout-Analyse + PAGE XML (neu)

- **`layout_analysis.py`:** VLM-basierte Layout-Analyse (Gemini Flash Lite, 1 Call/Seite), erkennt 5 Regionentypen (paragraph, heading, list, table, marginalia) mit Bounding Boxes in Prozent-Koordinaten
- **`export_pagexml.py`:** Deterministischer PAGE XML 2019 Export — merged OCR-Text + Layout-Regionen, proportionales Text-Alignment nach Zeilenschaetzung
- **`prompts/layout_system.md`:** Eigener System-Prompt fuer Layout-Analyse
- **`schemas/layout-regions-v0.1.json`:** Validierbares JSON-Schema
- **Test:** o_szd.100 (Typoskript, Vertrag) — 15 Regionen erkannt, PAGE XML valide
- **Dokumentation:** `knowledge/layout-analysis.md` erstellt, `htr-interchange-format.md` §7 aktualisiert

---

## 2026-04-02 — Session 15: Knowledge Vault Frontend + Projekt-Seite

**Schwerpunkt:** Knowledge Vault (12 Markdown-Dokumente) als navigierbare Ansicht ins Frontend bringen. Projekt-Seite aus README.md. README aktualisieren.

### Knowledge Vault im Frontend

- **Build-Pipeline:** `build_knowledge()` in `build_viewer_data.py` — liest `knowledge/*.md`, parst YAML-Frontmatter, loest `[[wiki-links]]` zur Build-Zeit auf, konvertiert Markdown zu HTML (Python `markdown` mit `tables`, `fenced_code`, `toc`), extrahiert TOC-Headings
- **Output:** `docs/data/knowledge.json` — 12 Dokumente + About-Seite (aus README.md), Sektions-Struktur aus `index.md`
- **Neue Python-Dependencies:** `markdown>=3.5`, `pyyaml>=6.0` in `requirements.txt`
- **Frontend-Routing:** 3 neue Hash-Routes:
  - `#knowledge` — Index mit Card-Layout, gruppiert nach Leseordnung / Spezifikationen / Projektlog
  - `#knowledge/{slug}` — Einzeldokument mit Sidebar (TOC, Metadaten, Related Links, Prev/Next)
  - `#about` — Projekt-Seite (gerendert aus README.md)
- **CSS:** View-Toggles fuer 5 Views, Knowledge-Cards, Knowledge-Doc Grid (Sidebar + Content), Markdown-Content-Styles (Headings, Tabellen, Code-Bloecke, Wiki-Links, Blockquotes), About-Seite, responsive Breakpoints (900px, 600px)
- **Navigation:** "Methodik" + "Projekt" Links im Header (alle Views sichtbar), Escape-Key zurueck, Wiki-Links als `<a href="#knowledge/...">` direkt via Hash-Routing

### README.md aktualisiert

- 575/2107 Objekte (27%), 3463/18719 Seiten (18%)
- Quality Signals v1.3 → v1.4
- Pipeline-Architektur: verify.py, generate_gt.py, build_viewer_data.py Downstream ergaenzt
- Projektstruktur: generate_gt.py, layout_analysis.py, export_pagexml.py, groundtruth/ ergaenzt
- Farbskala-Spalte in Statistik-Tabelle

### Designentscheidung

| Entscheidung | Begruendung |
|---|---|
| Pre-rendered HTML statt Client-Side Markdown | App hat null Runtime-Dependencies, kein Flicker, Wiki-Links zur Build-Zeit aufgeloest |
| Eine knowledge.json statt 12 Einzeldateien | Gesamtgroesse ~200-300 KB, einmal laden, sofort navigieren |
| Header-Nav statt eigener Sidebar-Navigation | Minimal-invasiv, folgt bestehendem Pattern, keine Mobile-Hamburger noetig |

### Neue/Geaenderte Dateien

- `pipeline/build_viewer_data.py` — `build_knowledge()`, `parse_frontmatter()`, `parse_index_sections()`
- `docs/index.html` — Nav-Links + 3 `<main>` Elemente
- `docs/app.css` — Sektionen 15-20 (Knowledge, Knowledge-Doc, Markdown, About, Responsive)
- `docs/app.js` — `ensureKnowledgeData()`, `showKnowledgeIndex()`, `renderKnowledgeIndex()`, `showKnowledgeDoc()`, `renderKnowledgeDoc()`, `showAbout()`
- `docs/data/knowledge.json` — generiert (12 Docs + About)
- `requirements.txt` — +markdown, +pyyaml
- `README.md` — Statistiken + Struktur aktualisiert

---

## 2026-04-02 — Session 16: Expert-Review Write-Back, 3-Tier Review, Katalog-Bereinigung

**Schwerpunkt:** Bidirektionaler Expert-Review-Workflow, 3-stufiger Review-Status, Katalog-Bereinigung, Knowledge Vault Konsolidierung.

### Ergebnisse

- **`import_reviews.py`**: Importiert Frontend-Exporte (GT-Reviews + regulaere Edits) zurueck in Pipeline-JSONs. Schreibt `review`-Objekt mit `status`, `reviewed_by`, `reviewed_at`.
- **3-stufiger Review-Status**: `needs_review: true` (rot), kein Review (LLM OK, orange), `review.status: "approved"` (gruen). `gtVerified` fuer GT-Objekte.
- **Katalog-Bereinigung**: Test-Daten, Layout-JSONs, GT-Drafts, Pro-Zwischenergebnisse aus Viewer-Daten gefiltert (627 → 601). Color-Chart-Seiten (158) aus Viewer entfernt.
- **Knowledge Vault Konsolidierung**: 13 → 11 Docs, Frontmatter vereinheitlicht, Claude Code Banner im Frontend.
- **3 GT-Objekte verifiziert**: o_szd.153, o_szd.137, o_szd.194.

---

## 2026-04-02 — Session 17: Chunking, Objekt-Prompts, Review-Server

**Schwerpunkt:** Pipeline-Readiness fuer Gesamtdurchlauf. Chunking fuer grosse Objekte, Objekt-Prompt-Overrides, lokaler Dev-Server mit Review-API, erste Expert-Verifikationen.

### Chunking fuer grosse Objekte

- **Problem:** 44 Objekte hatten weniger Bilder verarbeitet als vorhanden (z.B. Hauptbuch o_szd.143: 3 statt 249 Bilder). Ursache: API-Kontextlimit bei vielen hochaufloesenden Bildern.
- **Loesung:** Automatisches Chunking in `transcribe.py`: Objekte mit >20 Bildern werden in Chunks aufgeteilt, separat transkribiert, Ergebnisse gemergt. Seitennummerierung bleibt durchgehend.
- **CLI:** `--chunk-size N` (Default: 20)
- **Test:** Hauptbuch (249 Bilder, 13 Chunks) → 249/249 Seiten, ~197.000 Zeichen. Erster Durchlauf: Chunk 2 scheiterte (JSON nicht parsebar), Bug gefixt (Platzhalter-Seiten fuer fehlgeschlagene Chunks). Zweiter Durchlauf: komplett.
- **Refactoring:** `transcribe_object()` aufgeloest in `_call_api()`, `_parse_with_retry()`, `_transcribe_single_call()`, `_transcribe_chunked()`.

### Objekt-Prompts (4. Prompt-Schicht)

- **Motivation:** Bankkontoauszuege (o_szd.1056) — tabellarische Struktur ging im Formular-Prompt verloren.
- **Loesung:** Optionaler Objekt-Prompt in `prompts/objects/{object_id}.md` ueberschreibt Gruppen-Prompt.
- **Ergebnis:** o_szd.1056 neu transkribiert — 11 statt 3 Seiten, Tabellenstruktur teilweise als Markdown.
- **Erkenntnis:** VLM wendet Tabellenanweisung inkonsistent an (Seite 1 ja, Folgeseiten nein). Strukturrekonstruktion besser in Layout-Analyse / TEI-Export.

### Lokaler Dev-Server (`serve.py`)

- **Problem:** Edit/Approve im Frontend speicherte nur in localStorage, nicht in Pipeline-JSONs. Workflow: Export-JSON herunterladen → CLI → Import. Zu umstaendlich.
- **Loesung:** `pipeline/serve.py` — Python HTTP-Server, der Frontend ausliefert + API-Endpunkte hat:
  - `GET /api/status` → `{"local": true}` (Frontend erkennt lokalen Server)
  - `POST /api/approve` → schreibt `review.status: "approved"` direkt ins Pipeline-JSON
  - `POST /api/edit` → schreibt editierte Seiten + Review
  - `POST /api/rebuild` → fuehrt `build_viewer_data.py` aus
- **Architektur-Entscheidung:** Kein localStorage als Datenquelle. Pipeline-JSONs sind die einzige Quelle der Wahrheit. Frontend-Claude muss `fetch('/api/...')` Calls einbauen.
- **Nutzung:** `python pipeline/serve.py --port 5501 --rebuild`

### Erste Expert-Verifikationen (GT-Workflow)

- 3 Objekte approved: o_szd.153 (Briefkarte blanko), o_szd.137 (At Home Card), o_szd.194 (Briefregister)
- o_szd.194: Seite 4 manuell geleert — durchscheinende Schrift (bleed-through) war faelschlich transkribiert worden
- GT-Kandidatenliste: 18 Objekte stratifiziert ueber alle 9 Gruppen, 4 Sammlungen

### Katalog-Bereinigung

- **Duplikat-Fix:** 18 Duplikate im Katalog (Pro-Modell-Zwischenergebnisse). SKIP_SUFFIXES erweitert um `_gemini-3.1-pro` und `_judge_data`. Katalog: 657 → 639 Objekte.
- **.gitignore:** `*.bak` Backup-Dateien ausgeschlossen.

### Batch-Ergebnisse

- ~63 neue Korrespondenzen (o_szd.1454–1543), Abdeckung 24% → ~30%
- Hauptbuch komplett (249/249 Seiten)
- o_szd.1056 mit Objekt-Prompt neu transkribiert (11 Seiten)

### Identifizierter Refactoring-Bedarf

| Bereich | Problem | Prioritaet |
|---|---|---|
| `build_viewer_data.py` | Blacklist-Ansatz (SKIP_SUFFIXES) fragil — Whitelist-Ansatz besser | hoch |
| `serve.py` | File-Writes ohne try-except, Content-Length ohne Obergrenze | hoch |
| `serve.py` + `import_reviews.py` | Duplizierte Logik (Datei-Suche, Backup-Write, Page-Update) | mittel |
| `config.py` | CHUNK_SIZE, DEFAULT_REVIEWER, VERIFY_MODEL nicht zentralisiert | mittel |
| Datenintegritaet | ~44 Objekte mit unvollstaendigen Seiten, ~20 mit parse-Fehlern | hoch |
| Prompt-Loading | `load_prompt()` Regex fragil bei Codeblock-Varianten (`json` etc.) | niedrig |

### Neue/Geaenderte Dateien

- `pipeline/transcribe.py` — Chunking, Objekt-Prompts, Refactoring
- `pipeline/serve.py` — NEU: Lokaler Dev-Server mit Review-API
- `pipeline/build_viewer_data.py` — SKIP_SUFFIXES erweitert
- `pipeline/prompts/objects/o_szd.1056.md` — NEU: Erster Objekt-Prompt
- `.gitignore` — `*.bak` hinzugefuegt
- `CLAUDE.md` — Chunking, serve.py, Objekt-Prompts, Session 17
- `README.md` — 4-Schicht-Prompt, Chunking, serve.py

---

## 2026-04-02 — Session 18: Expert-Review, Agent-Verifikation, CER-Baseline

**Schwerpunkt:** 26 Objekte verifiziert (12 Agent + 14 Mensch), neuer Review-Tier `agent_verified`, CER-Baseline ueber alle 9 Gruppen, Knowledge Vault Refactoring.

### Expert-Review (Human)

- 7 kurze Objekte (Siegelstempel, Ex Libris, Briefumschlaege) approved
- o_szd.1888 (Korrekturfahne, Hans Carossa): 2 Fehler gefunden und korrigiert — fehlendes "nicht", Wortgrenze "erhobene Hand"
- Weitere 4 Objekte ueber serve.py approved (Frontend → API jetzt korrekt verdrahtet)
- **Insgesamt 14 human-approved Objekte**

### Agent-Verifikation (NEU)

Neuer Review-Tier zwischen Human Approved und LLM OK: Claude Code Sub-Agents (Opus 4.6 mit Vision) vergleichen Faksimile-Bilder gegen VLM-Transkription.

- **Batch 1 (4 Objekte):** Typoskript, Zeitungsausschnitt, Konvolut, Formular. Schwere Fraktur-Fehler gefunden: "selbstfeligen" → "selbstseligen", "gereiste" → "gereifte" (f/s-Verwechslung).
- **Batch 2 (8 Objekte):** Korrespondenz, Handschrift, Korrekturfahne, Zeitungsausschnitt. Strukturfehler bei tabellarischen Daten (o_szd.1475: Betraege falscher Zeile zugeordnet).
- **Insgesamt 12 agent-verified Objekte**, Fehler direkt korrigiert.

Implementierung: `serve.py` akzeptiert `status: "agent_verified"` mit Metadaten (`agent_model`, `errors_found`, `estimated_accuracy`). Frontend: blauer Badge "Agent ✓".

### CER-Baseline (→ [[evaluation-results]])

| Dokumenttyp | Genauigkeit |
|---|---|
| Gedruckter Text (Antiqua) | 99.6–99.9% |
| Fraktur | 99.7–99.8% (aber systematische f/s-Fehler) |
| Handschrift (sauber) | 99.1–99.4% |
| Tabellarisch/Struktur | ~90% |

### Bugfixes

- **Farbkarten-Klassifikation:** `_classify_page()` pruefte Keywords nur bei <10 Zeichen. Fix: Keywords vor Laengencheck, +5 neue Keywords (kodak, farbkontroll, etc.). 10 Seiten korrigiert.
- **Frontend API:** Approve- und Edit-Buttons schrieben nur in localStorage, nicht an `/api/approve`/`/api/edit`. Fix: `fetch()` in `toggleObjectApproval()` und `saveCurrentEdit()`.
- **Test-Daten entfernt:** `results/test/` (7 Dateien) + `pipeline/test_single.py` geloescht.

### Knowledge Vault Refactoring

- **NEU: `evaluation-results.md`** — CER-Baseline, Fehlertypen, Methodik
- **MERGE: `pilot-design.md`** → `verification-concept.md` §1.9 (Adaptive Sampling-Anpassung)
- **NEU: `verification-concept.md` §8** — Agent-Verifikation (4-Tier-Modell, technische Umsetzung)
- Journal: Session 16 nachgetragen, Session 18 dokumentiert.

### Statistiken

| Metrik | Wert |
|---|---|
| Reviewed Objekte (gesamt) | 26 (14 human + 12 agent) |
| Gruppen-Abdeckung | 9/9 |
| Korrekturen (Agent) | 15 Fehler in 12 Objekten |
| Korrekturen (Human) | 2 Fehler in 1 Objekt |
| Commits | 6 |

---

## 2026-04-02 — Session 19: Korrespondenz-Batch + Agent-Verifikation Batch 3

**Schwerpunkt:** 100 neue Korrespondenz-Transkriptionen, Agent-Verifikation von 8 Objekten (Korrespondenzen an Max Fleischer), systematische Fehlermuster bei Kurrent dokumentiert.

### Batch-Transkription

- **100 neue Korrespondenzen** (o_szd.1545–o_szd.1666), laeuft aktuell
- Abdeckung Korrespondenzen steigt von 350/1186 (30%) auf ~450/1186 (~38%)
- Batch-Steuerung: `--limit 450` noetig, weil `--limit 100` nur die ersten 100 sortierten Objekte nimmt (alle bereits erledigt). Erste 350 werden in Sekunden uebersprungen.

### Agent-Verifikation Batch 3 (8 Objekte, Korrespondenzen)

4 Sub-Agents parallel, jeweils 2 Objekte. Alle Objekte sind Korrespondenzen an Max Fleischer (~1901-1902).

| Objekt | Fehler | Genauigkeit | Editiert | Hauptprobleme |
|---|---:|---:|---|---|
| o_szd.1079 | 3 | 99.7% | 3, 4 | Kurrent h/I-Verwechslung, "nicht"/"auch" |
| o_szd.1081 | 2 | 97.9% | 1, 2 | "Stud. iur." → "Hud. inr." (Kurrent St/H) |
| o_szd.1088 | 3 | 97% | 1, 2 | "Dein" → "H[?]", halluziniertes "An" |
| o_szd.1090 | 8 | 90% | 1, 2 | Nonsens-Halluzination bei hastiger Kurrent |
| o_szd.1093 | 13 | 94% | 1, 2 | Kurrent massiv verlesen (Postkarte 1902) |
| o_szd.1096 | 0 | ~98% | — | Fehlerfrei, False-Positive bei Duplikat-Flag |
| o_szd.1097 | 2 | 99% | 2 | Fehlende Buchstaben in Komposita |
| o_szd.1100 | 2 | 95% | 2 | Kurrent L/B-Verwechslung, Grussformel |

**Aggregat: 33 Fehler in 8 Objekten, Durchschnitt ~96.3% Genauigkeit.**

### Systematische Fehlermuster (NEU)

**1. Kurrent-Buchstabenverwechslungen** (haeufigste Fehlerquelle):
- h ↔ I, n ↔ u, r ↔ v, L ↔ B, St ↔ H, f ↔ s
- Ursache: Kurrent-Minuskeln unterscheiden sich systematisch von Antiqua. Gemini kennt die Unterschiede nicht zuverlaessig.
- Besonders betroffen: hastige Schrift, kleine Postkarten, rote Tinte auf Bildhintergrund

**2. Nonsens-Halluzination statt Unsicherheitsmarker**:
- Gemini erfindet echte Woerter statt `[?]` zu setzen: "Langentour Kantgewalt" statt "Laufenden" (o_szd.1090)
- Bereits in Session 8 beobachtet (Vorsichts-Guidance wird ignoriert), hier erstmals quantifiziert
- Konsequenz: `marker_density` ist als Quality-Signal nahezu wertlos

**3. Systematisches "An" auf Adressseiten**:
- In 3 von 8 Objekten halluziniert Gemini ein "An" vor dem Adressaten
- Auf den Originalen steht kein "An" — die Adresse beginnt direkt mit dem Namen
- Fix: Hinweis im Gruppen-Prompt I (Korrespondenz) oder Post-Processing

**4. Grussformel-Fehler**:
- Zeilenumbrueche in Schlussformeln werden falsch zugeordnet
- "Liebsten Gruss" → "Besten Gruss" (L/B-Verwechslung in Kurrent)
- Epistolarische Konventionen koennten als Kontexthilfe im Prompt helfen

### Quality-Signals Erkenntnisse

- **`duplicate_pages` False-Positive**: Triggert bei Color-Chart-Doppelfotografie (selbe Seite mit/ohne Farbskala). Fix: Color-Chart-Seiten von Duplikat-Erkennung ausschliessen.
- **`needs_review` korrekt bei echten Problemen**: o_szd.1090 und o_szd.1093 (die schlechtesten) waren beide geflaggt.
- **`marker_density` wertlos**: Gemini setzt auch bei 10% Fehlerrate keine `[?]`-Marker.
- **DWR als Alternative**: DWR-Score korreliert vermutlich besser mit tatsaechlicher Fehlerrate als marker_density — noch zu validieren.

### Statistiken

| Metrik | Wert |
|---|---|
| Neue Transkriptionen | ~100 (laeuft noch) |
| Agent-verifizierte Objekte (Batch 3) | 8 |
| Korrekturen (Agent Batch 3) | 33 Fehler |
| Kumulativ agent-verified | 20 (12 + 8) |
| Kumulativ reviewed gesamt | 34 (14 human + 20 agent) |

---

## 2026-04-02 — Session 20: Edit-Tracking + 24 Agent-Verifikationen

### Was wurde gemacht

**1. Edit-Tracking-System implementiert**

Problem: Agent-Korrekturen ueberschrieben den Originaltext ohne Spur — kein programmatischer Diff moeglich.

Loesung: `edit_history`-Array auf Seitenebene im Ergebnis-JSON:
```json
"edit_history": [{
  "original_transcription": "Originaltext vor Korrektur",
  "edited_by": "Claude Code Agent",
  "edited_at": "2026-04-02T...",
  "source": "agent"   // oder "human"
}]
```

Aenderungen:
- `serve.py`: Menschliche Edits speichern jetzt automatisch `edit_history` vor dem Ueberschreiben
- `backfill_edit_history.py`: Einmal-Script, hat 5 Seiten in 4 Dateien aus Git-History rekonstruiert
- Frontend: Neuer Tab "Korrekturen" neben "Modellkonsensus" in der Diff-Ansicht (gruen/amber Farbschema)
- CSS: Edit-Diff-Variablen, Tab-Styles

**2. Agent-Verifikation: 24 Objekte in 4 Batches**

| Batch | Fokus | Objekte | Fehler gesamt | Korrekturen |
|---|---|---:|---:|---:|
| 1 | 1-Seiter, diverse Gruppen | 8 | 11 | 6 Seiten |
| 2 | Alle 8 Gruppen abgedeckt | 8 | 15 | 3 Seiten |
| 3 | 3-5 Seiten, mittlere Objekte | 8 | 11 | 6 Seiten |
| 4 | Korrespondenzen-Block | 8 | 5 | 3 Seiten |
| **Gesamt** | | **24** | **42** | **18 Seiten** |

### Neue Erkenntnisse

**Truncation-Problem entdeckt**: 4 grosse Objekte (o_szd.149, o_szd.141, o_szd.175, o_szd.174) haben nur ~5 von 43-165 Bildern transkribiert. Chunking bricht nach erstem Chunk ab. Muss in `transcribe.py` geprueft werden.

**Fraktur-Fehler haeufiger als angenommen**: o_szd.2217 (Walt Whitman) hatte 11 Fehler auf einer Seite — Nonsens-Halluzinationen ("Mitgebrine" statt "Mitbringsel"), falsche Eigennamen ("Hayel" statt "Hayek"), halluzinierte Werktitel ("Demokratie Lista" statt "Democratic Vistas").

**Fremdsprachliche Typoskripte**: Italienische Vertraege (o_szd.91) haben systematische Vokal-Fehler bei Kohlekopien (titole/titolo, tiretura/tiratura).

**Genauigkeits-Spread nach Gruppe** (Session 20):
- Typoskript/Formular/Kurztext: 97-100% (zuverlaessig)
- Korrekturfahne: 98-99% (zuverlaessig)
- Korrespondenz: 85-99% (abhaengig von Handschrift-Qualitaet)
- Zeitungsausschnitt: 97% (Fraktur-Fehler, aber meist einzelne Woerter)
- Handschrift: 95-98% (Kurrent-Verwechslungen)
- Tabellarisch: 75-99% (unvollstaendige Seiten bei grossen Objekten)

### Phase A: Truncation-Fix + DWR-Analyse + Fraktur-Evaluation

**Truncation-Bug gefixt**: Root Cause war `run_sample_batch.py --max-images 5` Default, nicht das Chunking. `diagnose_truncation.py` fand 97 betroffene Objekte (24 `max5_truncated`, 18 `vlm_mismatch`, 55 `zero_pages`). Default auf 0 geaendert. `transcribe.py` speichert jetzt `metadata.input_image_count_total`. Re-Transkription laeuft — 15/24 `max5_truncated` fertig, Chunking funktioniert korrekt bis 238 Bilder.

**DWR-Signal entfernt**: Spearman rho=0.05, F1=0.20 — keine Korrelation mit Qualitaet. `low_dwr` aus `needs_review` entfernt. Wirkung: 37% → 27% needs_review.

**Fraktur-Post-Processing evaluiert**: Prototyp `fraktur_postprocess.py` mit pyspellchecker + 13 Verwechslungspaaren. Ergebnis: 38% Precision — taugt als Flagging-Tool, nicht fuer Auto-Korrektur. Hauptlimitierung: Einzelzeichen-Substitution zu eng, Komposita nicht im Woerterbuch.

**Edit-History komplettiert**: 12 Dateien aus Session 18-19 retroaktiv gepatcht (20 Seiten). Verbessertes `backfill_edit_history.py` durchsucht jetzt Git-History nach Pre-Edit-Commits.

### Statistiken

| Metrik | Wert |
|---|---|
| Agent-verifizierte Objekte (Session 20) | 24 |
| Korrekturen (Session 20) | 42 Fehler auf 18 Seiten |
| Kumulativ agent-verified | 44 (20 + 24) |
| Kumulativ reviewed gesamt | 58 (14 human + 44 agent) |
| Truncation: betroffene Objekte | 97 (68 primaere Modell-Dateien) |
| Truncation: re-transkribiert | 15/24 max5, Rest laeuft |
| Edit-Tracking: backfilled total | 16 Dateien / 25 Seiten |
| needs_review nach Kalibrierung | 27% (355/1319), vorher 37% |
| Neue Scripts | diagnose_truncation.py, backfill_quality_signals.py, fraktur_postprocess.py |

---

## 2026-04-03 — Session 24: Layout-Pipeline Refactoring + Stratifizierter Test

### Was wurde gemacht

**1. Robustness-Refactoring (Phase 1, 8 Fixes)**
- Per-Page Error Handling (try-except statt Batch-Crash)
- PIL-Fallback bei fehlenden JPEG-Dimensionen
- VLM-Fallback-Logging (statt stiller Degradation)
- Halluzinations-Filter (Full-Page-Bbox >95% ablehnen)
- Schwellenwerte nach `config.py` verschoben
- Region-ID-Normalisierung (`r1, r2, ...` statt `d1, s1, r1`)
- Shared `find_ocr_file()` in `transcribe.py` (ersetzt fragile Glob-Logik in 2 Dateien)
- Schema `layout-regions-v0.1.json`: `source` + `group` Felder ergaenzt

**2. Post-Processing-Filter (Phase 2a)**
- 3 deterministische Filter in `_postprocess_regions()`: Scan-Hintergrund, Ueberlappung, Spurious
- 12 Regionen in Welle 2 korrekt entfernt (v.a. Seitenzahlen bei Korrekturfahnen)

**3. Prompt-Verfeinerung (Phase 2b)**
- 3 neue Regeln in `layout_ensemble.md`: Keine Ueberlappung, minimale Regionsgroesse, Scan-Hintergrund != Marginalie
- Wirksam: o_szd.1081 False-Positive-Region durch Prompt allein verhindert

**4. Merge+Verify kombiniert (Phase 4)**
- 1 VLM-Call statt 2 pro Seite (Regions + Quality im selben Output)
- Einsparung: ~7s/Seite = ~36h bei 18.700 Seiten
- `prompts/layout_verify.md` nicht mehr aktiv, bleibt als Referenz

**5. Stratifizierter Test (Welle 1 + 2)**
- Welle 1: 8 einfache Objekte ueber alle 9 Gruppen (21 Content-Seiten)
- Welle 2: 7 mittelschwere Objekte + 2 Re-Analysen
- Visuelle Inspektion Welle 1: 12 Seiten manuell geprueft
- Welle 2 bereit zur visuellen Verifikation

### Identifizierte Probleme (aus visueller Inspektion)

| Problem | Loesung | Status |
|---|---|---|
| Scan-Hintergrund-False-Positives | Post-Processing-Filter 1 + Prompt-Regel | Geloest |
| Ueberlappende Regionen | Post-Processing-Filter 2 + Prompt-Regel | Geloest |
| Spurious Zwischen-Regionen | Post-Processing-Filter 3 + Prompt-Regel | Geloest |
| Sachfotos statt Dokumente (o_szd.148) | `page.type=photograph` geplant | Offen |
| VLM-Nichtdeterminismus (o_szd.206) | Bekannte VLM-Eigenschaft | Akzeptiert |

### Entscheidungen

- **Merge+Verify zusammenlegen**: Laengerer Prompt hat Qualitaet nicht verschlechtert (getestet auf o_szd.148)
- **Post-Processing-Filter**: Deterministisch + guenstig, fangen systematische VLM-Schwaechen ab
- **Prompt-Verfeinerung wirkt upstream**: Reduziert Probleme bevor Filter noetig sind

### Statistiken

| Metrik | Wert |
|---|---|
| Layout-Ergebnisse gesamt | 25 Objekte |
| Gruppen abgedeckt | 9/9 (A-I) |
| Quality good | 18 (72%) |
| Quality acceptable | 3 (12%) |
| Quality needs_correction | 3 (12%) |
| Filter-Aktionen Welle 2 | 12 Regionen entfernt |
| Geaenderte Dateien | layout_analysis.py, config.py, transcribe.py, export_pagexml.py, layout_ensemble.md, layout-regions-v0.1.json |

### Naechste Schritte

- [ ] Welle 2 visuell verifizieren (9 URLs bereit)
- [ ] Phase 2c: Sachfoto-Erkennung (page.type=photograph)
- [ ] Layout-Batch ueber ~1300 transkribierte Objekte (nach visueller Verifikation)

---

## 2026-04-02 — Session 20b: Korrespondenzen-Massenbatch (Lane 3)

### Was wurde gemacht

**1. Korrespondenzen-Batch: 566 neue Objekte transkribiert**

Ausgangslage: 450/1186 Korrespondenzen transkribiert (38%).
Ergebnis: 1016/1186 (86%), 170 verbleibend. 0 Fehler im gesamten Batch.

Grosse Objekte erfolgreich via Chunking verarbeitet:
- o_szd.174: 122 Bilder (7 Chunks) — high confidence
- o_szd.75: 151 Bilder (8 Chunks) — high confidence
- o_szd.71: 54 Bilder (3 Chunks) — high confidence
- o_szd.76: 60 Bilder (3 Chunks) — medium confidence

**2. Bug-Fix: `run_batch()` Fehlerbehandlung**

Problem: `run_batch()` in `transcribe.py` hatte keinen try/except um `transcribe_object()`. Ein einzelner unbehandelter Fehler (z.B. beim API-Call eines grossen Objekts) toetete den gesamten Batch-Prozess lautlos — keine Fehlermeldung, kein Traceback.

Fix: try/except mit Logging um den `transcribe_object()`-Aufruf. Batch laeuft jetzt weiter, auch wenn einzelne Objekte fehlschlagen.

**3. Analyse: Dry-Run-Zaehlung vs. Result-Zaehlung**

Klaerung einer scheinbaren Diskrepanz (127 Backup-Objekte vs. 138 Results bei Lebensdokumenten): Die 138 entstand durch Mitzaehlung von Consensus-, Pro- und Layout-JSONs. Tatsaechlich: 127 Flash-Lite-Results = 127 Backup-Objekte (perfekt). `--dry-run` listet ALLE Objekte ohne Skip-Logik.

### Erkenntnisse

- **Chunking ist produktionsreif**: Objekte bis 151 Bilder (8 Chunks) laufen stabil durch
- **Korrespondenzen-Qualitaet**: Ueberwiegend high confidence, vereinzelt medium/low bei schwieriger Handschrift
- **JSON-Parsing-Retries**: Einige Objekte brauchen Retry wegen nicht-parseabrem Gemini-Output (z.B. o_szd.482, o_szd.564) — werden automatisch behandelt
- **Batch-Robustheit**: Mit dem try/except-Fix ist die Pipeline jetzt resilient gegen Einzelfehler

---

## 2026-04-03 — Session 21: Scope-Bereinigung, GT-Review-Workflow, Signal-Evaluation

### Scope-Bereinigung

**Entfernt aus dem Projekt:**
- Prompt-Ablation, Nondeterminismus-Test, Provider-Vergleich (nicht noetig fuer Projektziel)
- Phase 5 (TEI/teiCrafter) — TEI-Erzeugung passiert im teiCrafter-Repo, nicht hier
- `knowledge/tei-target-structure.md` und `knowledge/teiCrafter-integration.md` geloescht
- Phase 6 (DIA-XAI) → Phase 5

Beruehrte Dateien: Plan.md, CLAUDE.md, README.md, knowledge/index.md, dia-xai-integration.md, htr-interchange-format.md, layout-analysis.md, journal.md, evaluation-results.md, verification-concept.md.

### GT-Review-Workflow

**Problem:** Kein einziges Objekt hatte `gt_verified`-Status. Die CER-Zahlen in evaluation-results.md basierten auf Agent-Schaetzungen, nicht auf echtem Ground Truth. Nicht publikationsfaehig.

**Loesung:** End-to-End GT-Review-Workflow implementiert:
- `serve.py`: `gt_verified` als neuer Status (Tier 0), `ThreadingHTTPServer` (POST-Requests hingen bei Single-Threaded-Server), `find_result_file` bevorzugt primaeres Modell
- `app.js`: GT Verify Button, "Gespeichert (JSON)" statt localStorage-Anzeige
- `index.html`: GT Verify Button, Hilfe-Seite mit 4-Tier Review-Modell erklaert, verbesserte Tooltips
- `/api/edit` speichert Originaltext in `edit_history` — Grundlage fuer CER-Berechnung (Pipeline-Original vs. Human-Korrektur)

**Ergebnis:** o_szd.139 als erstes Objekt im Viewer editiert und verifiziert. edit_history bestaetigt. 14 weitere GT-Objekte definiert (15 Objekte, ~39 Content-Seiten, alle 9 Gruppen).

### Quality-Signals v1.6: Empirische Evaluation

**Methode:** 62 agent-verified Objekte mit `errors_found`-Daten als Referenz. Precision pro Signal berechnet.

| Signal | N geflaggt | Precision | Entscheidung |
|---|---|---|---|
| `page_image_mismatch` | 3 | **100%** | Behalten — bestes Signal |
| `page_length_anomaly` | 2 | **100%** | Behalten — kleine Stichprobe |
| `language_mismatch` | 8 | **50%** | Behalten — Metadaten-Signal |
| `duplicate_pages` | 1 | **0%** | Aus needs_review entfernt |
| DWR | 0 | — | Seit v1.5 entfernt |
| Marker-Density | 0 | — | Seit v1.5 entfernt |

**Aenderungen:**
- `duplicate_pages` aus `needs_review_reasons` entfernt (0% Precision, misst Dokumentstruktur statt Fehler)
- DWR, Marker-Density, Seitenduplikate aus Dashboard-Signalanalyse entfernt
- Backfill: 125 Objekte entflaggt
- `needs_review`-Quote: 25% → **19.4%**

**Begruendung `duplicate_pages`:** Korrekturfahnen enthalten physisch 2x denselben Text (Original + Korrekturversion, z.B. o_szd.1888: p0≡p7). Register haben repetitive Headers. Beides ist Dokumentstruktur, kein Transkriptionsfehler.

### Truncation Re-Transkription

5 Objekte mit extremer Truncation identifiziert (result_pages < 10% der Backup-Bilder):
- o_szd.66 (2/141), o_szd.68 (3/202), o_szd.221 (1/51), o_szd.2271 (1/25), o_szd.2234 (2/13)

Re-Transkription mit `--force --chunk-size 20` gestartet.

### Statistiken

| Metrik | Vorher | Nachher |
|---|---|---|
| needs_review-Quote | ~25% | 19.4% |
| Signale im Dashboard | 6 Spalten | 3 Spalten |
| gt_verified Objekte | 0 | 0 (Workflow bereit, 15 Objekte definiert) |
| approved (human) | 15 | 16 (+o_szd.139 mit edit_history) |
| Pipeline-Phasen | 6 (inkl. TEI) | 5 (ohne TEI) |

### Kontext

Paralleler Betrieb mit zweitem Claude (Session 20): Einer transkribiert neue Objekte (dieser Eintrag), einer verifiziert bestehende (Session 20 oben).

### Statistiken

| Metrik | Wert |
|---|---|
| Neue Transkriptionen | 566 |
| Korrespondenzen-Abdeckung | 1016/1186 (86%) |
| Fehler | 0 |
| Groesste Objekte (Bilder) | 151, 122, 60, 54 |
| Gesamtabdeckung (alle Sammlungen) | ~1308/2107 (62%) |

---

## 2026-04-03 — Session 22: UI-Redesign (Badge-System, Header, CSS/HTML-Refactoring)

**Schwerpunkt:** Komplettes Redesign des Badge-Systems im Katalog-Viewer, Projekttitel im Header, CSS/HTML-Qualitaetsrefactoring, Accessibility-Verbesserungen.

### Badge-System: 5-Stufen-Redesign

**Problem:** Badges waren visuell inkonsistent (manche Pills, manche Text+Punkt), Labels unklar fuer Expert:innen ("LLM OK", "Agent ✓"), Farben widersprachen der Semantik (gelber Punkt fuer OK-Zustand).

**Neues System — einheitliche Pills mit Vertrauens-Farbverlauf:**

| Tier | Alt | Neu | Farbe |
|---|---|---|---|
| 0 | GT ✓ | Verifiziert | Dunkelgruen (#1a5c1a / #c8e6c8) |
| 1 | Geprueft | Geprueft | Gruen (#2d6a2d / #d4e8d4) |
| 2 | Agent ✓ | Auto-geprueft | Schiefergrau (#475569 / #e2e8f0) |
| 3a | LLM OK | Ungeprueft | Grau (#4b5563 / #e5e7eb) |
| 3b | Review | Review noetig | Amber (#b45309 / #fef3c7) |

Alle 5 Stufen bestehen WCAG AA (≥4.5:1 Kontrast). Farben nach Kontrastpruefung nachgeschaerft: "Review noetig" von #d97706 auf #b45309, "Ungeprueft" von #6b7280 auf #4b5563.

VLM-Konfidenz ("high/medium/low") aus Qualitaets-Spalte entfernt (laut eigener Evaluation unzuverlaessig). LLM-Sparkle-Icon (✦) entfernt — Labels sind selbsterklaerend.

Betrifft: `renderReviewCell()`, `renderQualityCell()`, `renderViewerContext()`, `renderStats()`, `renderReviewDonut()`, Filter-Dropdown (5 statt 3 Optionen), Help-Tabelle (5-Tier), Summary-Bar-Chips.

### Header-Redesign

- **Titel:** "SZD-HTR" → "SZD OCR/HTR Pipeline"
- **Subtitle:** "Experimentelles Teilprojekt von Stefan Zweig Digital" (italic, dezent)
- **Claude-Badge:** Vereinfacht auf "Built with Claude Code" (ohne Modell/Methode)
- **Meta-Tags:** `<title>`, OG-Tags, Description aktualisiert

### CSS/HTML-Refactoring

**Accessibility:**
- `:focus-visible` auf alle interaktiven Buttons (Katalog-Pagination, Viewer-Navigation, Action-Buttons, GT-Approve)
- `aria-label` auf 9 Icon-only-Buttons (Pfeile, Zoom, Rotate, Reset, Fit)
- Disabled-Buttons: `opacity` ersetzt durch echte Farben (WCAG AA konform)

**Inline-Styles eliminiert:**
- `.is-hidden` CSS-Klasse ersetzt 12× `style="display:none"` im HTML
- 27× `style.display` im JS → `classList.add/remove/toggle('is-hidden')`
- 5× JS-generierte Inline-Styles → CSS-Klassen (`.placeholder-message`, `.gt-review-panel__stats`, `.gt-review-panel__hint`, `.diff__provider-label--old/--new`)

**Farb-Fallbacks bereinigt:**
- 12× `var(--sz-*, #fallback)` Fallbacks in GT-Review-CSS entfernt
- Hardcodierte Farben (#888, #1a1a1a) → CSS-Variablen
- `'JetBrains Mono', monospace` → `var(--font-mono)`

**Weitere Fixes:**
- `::selection`-Style (Burgundy/Cream)
- Knowledge-Sidebar auf 600px versteckt
- Help-Links: Underline-Style konsistent mit Markdown-Content
- Umlaut-Fix: "Qualitaetsmetriken" → "Qualitaetsmetriken" (HTML-Entity)
- Diff-Beschreibung: Generisch statt hardcoded Modellnamen
- `.catalog__stats` CSS `display:none` → `.is-hidden` Klasse

### Neue/Geaenderte Dateien

- `docs/app.css` — 10 neue CSS-Variablen (Review-Tiers), Badge-Klassen, Focus-Styles, `.is-hidden`, Farb-Bereinigung
- `docs/app.js` — Badge-Rendering, classList statt style.display, Filter-Logik, Donut-Labels
- `docs/index.html` — Header, Meta-Tags, Dropdown, Help-Tabelle, aria-labels, is-hidden

### Entscheidungen

| Entscheidung | Begruendung |
|---|---|
| "Ungeprueft" statt "LLM OK" | Ehrlicher — sagt was es ist (nicht geprueft), nicht was die Maschine meint |
| VLM-Konfidenz entfernt | Eigene Evaluation zeigt: unzuverlaessig (LLMs ueberschaetzen Leistung) |
| Icons entfernt (✦, ⚙, ✓) | Labels sind selbsterklaerend, Icons waren visuell unausbalanciert |
| WCAG-Kontrastpruefung | Amber-Text und Grau-Text nachgeschaerft nach Berechnung der Kontrastverhaeltnisse |
| `!important` bei `.is-hidden` | Utility-Class muss alle anderen display-Regeln ueberschreiben |
| `!important` bei reduced-motion | Anerkanntes A11y-Pattern, stellt sicher dass keine Animation die Einstellung ueberschreibt |

---

## 2026-04-03 — Session 23: Datenbestand-Inventur, Batch 100%, Page-JSON v0.2, METS als Zielformat

**Schwerpunkt:** Rohdaten-Inventur, Batch-Transkription Richtung 100%, Stats-Dashboard als epistemische Infrastruktur, Page-JSON v0.2 mit deskriptiven Metadaten, METS/MODS + PAGE XML als Zielformat.

### Datenbestand-Inventur

Erstmals exakt dokumentiert: 2.107 Objekte, 18.719 Faksimile-Scans, 23 GB. Pro Sammlung: Lebensdokumente 127/2.879, Werke 169/7.842, Aufsatzablage 625/3.844, Korrespondenzen 1.186/4.154. Bildformat: JPEG, Median 4800x7234 px. Alle Objekte vollstaendig (metadata.json + mets.xml + Bilder). In data-overview.md, README.md, CLAUDE.md dokumentiert.

### Batch-Transkription

- Korrespondenzen auf 100% (43 fehlende einzeln transkribiert)
- Aufsatzablage ~97% (318 neue, 19 Fehler)
- Werke-Batch laeuft (85/115, viele Timeouts bei Objekten >50 Bilder)
- Problem: 5-Min-Timeout im Batch-Skript reicht nicht fuer Chunking-Objekte

### Seiten-Bild-Synchronisation

Bug entdeckt: VLM nummeriert nach Manuskriptblaettern (1,3,5,...), ueberspringt Rueckseiten. Viewer zeigt falsches Bild ab Seite 2. Fix: `_fill_missing_pages()` in quality_signals.py — fuellt Luecken mit Blank-Eintraegen. 41 Objekte backfilled. Zwei Faelle abgedeckt: Luecken in Seitennummern und weniger Seiten als Bilder.

### Stats-Dashboard: Epistemische Infrastruktur

5 Sektionen entfernt (nicht gegroundet oder transient): Fortschritt/Abdeckung, Seitenkomposition, DWR-Histogram (rho=0.05), VLM-Konfidenz-Donut (diskriminiert nicht), Modellkonsensus (Agreement ≠ Korrektheit, nur 29/1973 Objekte).

3 neue Sektionen: Verifikation (Review-Status + Review-Gruende mit Signal-Precision), Textcharakteristik (Zeichen/Seite pro Dokumenttyp — Handschrift ~50 Z/S wegen 73% Registerblaetter, Zeitungsausschnitt ~4800), Signalanalyse (Heatmap).

Provenienz-Annotationen: Jede Sektion zeigt dezent (opacity 0.35, hover 0.7) welches Pipeline-Script die Daten erzeugt.

### Page-JSON v0.2: Deskriptive Metadaten

Neuer `descriptive_metadata`-Block in `source`: Dublin Core (creator+GND, subject, origin_place, extent, rights, provenance) + materialtypologische Erweiterungen (writing_instrument, writing_material, hands[], dimensions, binding, inscriptions, correspondence). Schema: `schemas/page-json-v0.2.json`. Export: `pipeline/export_page_json.py`. TEI-Extraktion: `_extract_full_metadata()` in tei_context.py mit persName-Parsing und Whitespace-Normalisierung.

### METS/MODS als Zielformat

Architektur-Entscheidung: Page-JSON = internes Arbeitsformat, METS/MODS + PAGE XML = Archiv- und Austauschformat (Zielformat). Gruende: GAMS arbeitet mit METS, Transkribus/eScriptorium/OCR-D verstehen es, MODS ist reicher als DC fuer Archivmetadaten, kein eigenes Schema zu pflegen. Wissensdokument: `knowledge/page-xml-mets-architecture.md`. Terminologie durchgaengig in CLAUDE.md, README, Plan.md, Knowledge Vault nachgezogen.

### Knowledge Vault Audit

8 Fixes: stale Zahlen in dia-xai-integration.md (1328→1973), Session-Zaehler in index.md, DWR-Referenzen in stats-dashboard.md, Schema-Referenz v0.1→v0.2, updated-Daten.

### Entscheidungen

| Entscheidung | Begruendung |
|---|---|
| DWR aus Dashboard entfernt | rho=0.05, F1=0.20 — mass Prosadichte, nicht Qualitaet |
| VLM-Konfidenz aus Dashboard entfernt | High/Medium/Low diskriminiert nicht |
| Modellkonsensus aus Dashboard entfernt | CER zwischen Modellen = Agreement, nicht Korrektheit |
| Provenienz-Annotationen | Jede Visualisierung zeigt Datenherkunft — epistemische Transparenz |
| Page-JSON v0.2 mit descriptive_metadata | DC + Materialtypologie — alle TEI-Felder ins Arbeitsformat |
| METS/MODS als Zielformat | Etablierter Stack, GAMS-kompatibel, kein eigenes Schema noetig |
| _fill_missing_pages | Seiten-Bild-Sync als Pipeline-Schritt, nicht Viewer-Workaround |

### Neue/Geaenderte Dateien

- `pipeline/quality_signals.py` — `_fill_missing_pages()` (v1.5 Fix)
- `pipeline/tei_context.py` — `_extract_full_metadata()`, `parse_tei_full_metadata()`, persName-Parser, Whitespace-Fix
- `pipeline/export_page_json.py` — Vollstaendige Implementierung (~210 Zeilen)
- `schemas/page-json-v0.2.json` — Neues Schema mit descriptive_metadata
- `knowledge/page-xml-mets-architecture.md` — Neues Wissensdokument
- `knowledge/data-overview.md` — Physischer Bestand, TEI vs. Backup, Sprachen
- `docs/app.js` — Dashboard-Umbau (5 Sektionen entfernt, 3 neu)
- `docs/app.css` — Provenienz-Styling

## 2026-04-03 — Session 24: teiCrafter Pipeline Mode + Page-JSON Batch-Export

**Schwerpunkt:** Analyse szd-htr ↔ teiCrafter-Verbindung, Implementierung Pipeline-Modus in teiCrafter, Page-JSON-Batch-Export fuer alle 2030 Objekte, Batch-TEI-Generierung.

### Analyse der Projektverbindung

szd-htr und teiCrafter bilden eine sequentielle Pipeline: szd-htr (Bild → Text + Layout + Metadaten) → teiCrafter (Text → TEI-XML). Design-Entscheidung: TEI-Erzeugung passiert in teiCrafter, nicht in szd-htr. teiCrafter hat bereits 3 SZD-spezifische Mapping-Templates (correspondence-szd, manuscript-szd, print-szd).

### teiCrafter Pipeline-Modus (Phase P)

Neuer Modus neben dem bestehenden interaktiven Browser-Modus. Node.js-CLI (`pipeline.mjs`), 6 reine ES6-Module unter `docs/js/pipeline/`. Deterministisch wo moeglich, LLM (Gemini 3.1 Flash Lite) nur fuer div-Grenzen bei komplexen Dokumenten (noch nicht implementiert).

Module:
- `utils.js` — XML-Escaping, Element-Builder, Sprachcodes
- `mods-to-header.js` — Page-JSON Metadaten → teiHeader (100% deterministisch)
- `page-to-body.js` — Seiten + Regionen → TEI-Elementliste (Regionstyp-Mapping)
- `div-structurer.js` — Heading-Heuristik, Briefe als Single-div
- `tei-assembler.js` — Orchestriert alles
- `pipeline-validator.js` — Tag-Matching + Struktur-Check + Plaintext-Erhaltung

DTABf-Schema um 30+ Elemente erweitert (msDesc-Hierarchie, fw, table, list, Header-Elemente). Plan.md mit 9 Teilphasen erstellt.

### Page-JSON Batch-Export (szd-htr)

`python pipeline/export_page_json.py --all` — 2.030 Page-JSON-Dateien exportiert (vorher: 3). Aufgeteilt: Lebensdokumente 127, Korrespondenzen 1.186, Aufsatzablage 606, Werke 111.

### Batch-TEI-Generierung (teiCrafter)

`node pipeline.mjs --batch` ueber alle 4 Sammlungen: **2.030 TEI-Dateien, 0 Fehler**. Plaintext-Erhaltung 99-100%. Output: 21 MB in `teiCrafter/output/`. Fix fuer leere Dokumente (5 Objekte ohne Seiten → leerer div).

### Entscheidungen

| Entscheidung | Begruendung |
|---|---|
| Page-JSON-Fallback statt METS | METS-Export (`export_mets.py`) existiert noch nicht; Page-JSON v0.2 enthaelt alle benoetigten Daten |
| Kein LLM fuer teiHeader | MODS-zu-TEI ist deterministische Abbildung |
| Kein LLM fuer body-Grundstruktur | Regionstypen aus Layout-Analyse genuegen |
| Briefe als Single-div | Umschlag-Adressen und Briefkoepfe sind keine Kapitelgrenzen |
| Node.js CLI statt Browser-Pipeline | Batch-Verarbeitung braucht Dateisystem-Zugriff |

### Validierung und Tests

- XML-Well-Formedness (Python `xml.etree.ElementTree`): **2.033/2.033** Dateien fehlerfrei geparst
- Zeichengenauer Plaintext-Vergleich (Page-JSON vs. TEI body): **2.030/2.030 identisch** (0 fehlende, 0 hinzugefuegte Zeichen)
- Stichproben-Metadaten-Pruefung (20 zufaellige Objekte): Titel, PID, Sprache, Seitenzahl, GND, Signatur — alle korrekt
- 50 Unit- und Integrationstests (`tests/pipeline.test.mjs`): **50/50** bestanden
- **Nicht gemacht:** RelaxNG-Validierung gegen offizielles TEI-Schema (kein `xmllint`/`lxml` auf dem System)

### Commits

| Repo | Hash | Inhalt |
|---|---|---|
| teiCrafter | `77fd4be` | Pipeline-Modus: 6 Module, CLI, 50 Tests, Schema, Knowledge, README, CLAUDE.md |
| szd-htr | `d99a31c` | Journal + Plan (Session 24) |
| szd-htr | `631931a` | 2.030 Page-JSON-Dateien (218.813 Zeilen) |

### Naechste Schritte

- Layout-Analyse skalieren (18 → ~2000 Objekte, benoetigt API-Calls)
- `export_mets.py` in szd-htr bauen (Phase 5b)
- teiCrafter METS-Parser (Phase P.1)
- LLM-Fallback fuer komplexe div-Grenzen (P.4.2/P.4.3)
- RelaxNG-Validierung gegen offizielles TEI-Schema nachholen

---

## Offene Fragen (Stand 2026-04-03)

- [ ] Optimale Bildgroesse: Resizing vor API-Call?
- [ ] Korrektur-Markup: Erweitertes Markup noetig?
- [ ] VLM-Seitenzuordnungsfehler: VLM schreibt Text auf falsche Seite bei Typoskripten mit Rueckseiten — Erkennung und Fix?
- [ ] export_mets.py: METS-Container mit MODS + PAGE XML implementieren
- [ ] Korrespondenzen-TEI-Matching: correspDesc aus Konvolut-Eintraegen den Einzelbriefen zuordnen
- [x] Fraktur-Erkennung: o_szd.2232 high confidence (Session 7)
- [x] Batch-Modus: transcribe.py (Session 5)
- [x] Konvolut: Gruppe G erstellt, o_szd.277 medium (Session 7)
- [~] Alle 2107 Objekte transkribieren — ~2080/2107 (99%) fertig (Session 25), 27 Werke-Objekte im Batch
- [x] quality_signals kalibrieren: v1.1 rekalibriert (Session 13), low_dwr entfernt (Session 20 Phase A)
- [x] o_szd.143 nur 20 Zeichen auf 3 Seiten — geloest: fehlende Bilder wegen API-Limit, Chunking eingebaut (Session 17)
- [x] Verification-by-Vision: Proof of Concept erfolgreich, Spec geschrieben (Session 11)
- [x] Pipeline-Bug: o_szd.147 repariert, 41 Bilder transkribiert (Session 13)
- [ ] VbV-Konfidenz gegen Ground Truth kalibrieren (nach Modellkonsensus-Validierung)
- [x] Modellkonsensus: 27 Objekte validiert, 18 Objekte GT-Pipeline mit 3 Modellen (Session 14)
- [x] Statistik-Dashboard im Frontend — Enhanced Stats + Diff mit echten Daten (Session 14)
- [~] Expert-Review: 58/~875 Objekte verifiziert (14 human + 44 agent), CER-Baseline steht (Session 18–20)
- [~] Agent-Verifikation auf weitere Objekte ausweiten — 44/~875 agent-verified (Session 18–20)
- [x] Fraktur-Post-Processing evaluiert: 38% Precision, taugt als Flagging, nicht Auto-Korrektur (Session 20 Phase A)
- [ ] `duplicate_pages` False-Positive fixen: Color-Chart-Seiten von Duplikat-Erkennung ausschliessen (Session 19)
- [x] Halluziniertes "An" auf Adressseiten: Prompt-Fix in group_i_korrespondenz.md (Session 25)
- [x] DWR-Score gegen Agent-Verifikation validiert: rho=0.05, F1=0.20, Signal entfernt (Session 20 Phase A)
- [~] **Truncation fixen**: Root Cause `max_images=5` gefixt, 97 Objekte betroffen, 15/24 re-transkribiert (Session 20 Phase A)
- [x] Edit-Tracking: `edit_history` in Pipeline-JSONs + Frontend-Diff implementiert (Session 20)
- [ ] `marker_density` evaluieren: Gemini setzt keine Marker, Signal vermutlich wertlos wie DWR
- [ ] `duplicate_pages` + `language_mismatch` Precision/Recall messen (naechste Kalibrierungsrunde)

---

## 2026-04-12 — Session 25: Batch-Transkription +20 Objekte (2075/2107), Ensemble-Layout-Pipeline

### Was wurde gemacht

**1. Transkriptionsluecken geschlossen**

Ausgangslage: 2075/2107 Objekte (98,5%). Fehlend: 5 Aufsatzablage, 27 Werke.

- Aufsatzablage: 1/5 erfolgreich (o_szd.2607), 4 persistente API-Fehler (INVALID_ARGUMENT / leere Antwort)
- Werke: Batch laeuft (27 Objekte, 53-341 Bilder). Stand: ~146/169 Werke-Dateien. Chunking funktioniert, aber o_szd.227 (184 Bilder, 73% Leerseiten) hatte massive JSON-Parse-Fehler (120/184 Platzhalter-Seiten)

**2. METS/MODS Export implementiert (Phase 5b)**

Neues Script `pipeline/export_mets.py` (~280 Zeilen). METS-Container mit:
- dmdSec: MODS-Metadaten aus TEI (parse_tei_full_metadata) + Backup-Fallback fuer Korrespondenzen
- fileSec: GAMS-Bild-URLs + PAGE XML Referenzen (falls vorhanden)
- structMap PHYSICAL: Seiten-Sequenz
- structMap LOGICAL: Textseiten vs. Farbreferenz/Schluss
- structLink: Seiten-Typ-basierte Zuordnung

Batch-Export: **2074 METS-Dateien, 0 Fehler**. Alle 4 Sammlungen. GND-Verknuepfungen, Sprach-Normalisierung, Signatur-Mapping funktionieren.

**3. Bug-Fix: "An"-Halluzination**

Prompt-Fix in `group_i_korrespondenz.md`: Explizite Anweisung, kein "An" vor Empfaengernamen zu ergaenzen.

**4. JSON-Parsing und Chunking gehaertet**

Problem: Werke-Objekte mit vielen Leerseiten (49% im Schnitt, bis 73%) produzieren kaputtes JSON. Ursache: Gemini rutscht bei Chunks mit vielen leeren Seiten aus dem JSON-Format.

3 Verbesserungen in `transcribe.py`:
- `_repair_json()`: Trailing Commas entfernen, nackte Steuerzeichen in Strings escapen
- `_extract_json_object()`: JSON-Objekt aus umgebendem Text extrahieren, abgeschnittenes JSON schliessen
- `_retry_sub_chunks()`: Fehlgeschlagene 20er-Chunks automatisch in 5er-Bloecke aufteilen und erneut versuchen
- Blank-Page-Hint im Chunk-Prompt bei Objekten >30 Bilder

**5. Viewer-Daten und Page-JSON aktualisiert**

- catalog.json: 2055 → 2076 Objekte
- 46 neue Page-JSON-Dateien exportiert

**6. Knowledge Vault Audit**

Systematischer Audit aller 12 Knowledge-Dokumente. 10 Probleme in 7 Dateien gefunden und behoben:
- stats-dashboard.md: v1.4→v1.5, DWR-Referenzen entfernt, Sektionsnummern korrigiert, Objektzahl aktualisiert
- dia-xai-integration.md: ~1973→~2080 Objekte
- htr-interchange-format.md: Schema v0.1→v0.2, DWR aus Signalliste entfernt
- page-xml-mets-architecture.md: export_mets.py als implementiert markiert
- verification-concept.md: Stichprobengroesse 26→62 verifizierte Objekte

### Statistiken

| Metrik | Wert |
|---|---|
| Transkription gesamt | ~2080/2107 (99%) |
| Neue Transkriptionen (Session) | ~20 (Werke-Batch laeuft noch) |
| METS-Export | 2074 Dateien, 0 Fehler |
| Page-JSON (neu) | 46 Dateien |
| Viewer-Objekte | 2076 |
| Knowledge-Fixes | 10 Probleme in 7 Dateien |
| Neue Scripts | export_mets.py |
| Geaenderte Scripts | transcribe.py (4 neue Funktionen), group_i_korrespondenz.md |
