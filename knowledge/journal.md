---
title: "Research Journal"
aliases: ["Journal"]
created: 2026-03-30
updated: 2026-04-02
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

- **htr-interchange-format.md** geschrieben — JSON Schema v0.1, teiCrafter-Mapping, SZD-HTR-Mapping, Abgrenzung ALTO/PAGE/hOCR, Beispiel basierend auf o_szd.100.
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

## 2026-04-01 — Session 10: teiCrafter-Integration und TEI-Zielstruktur

### L2: Schritt 3+4 abgeschlossen

**tei-target-structure.md** (7 Abschnitte):
- DTABf als TEI-Profil, SZD-Erweiterungen via `szdg:`-Namespace
- Vollstaendiges XML-Beispiel basierend auf o_szd.1079 (Brief an Fleischer)
- Markup→TEI-Mapping-Tabelle: 7 Pipeline-Marker → TEI-Elemente
- NER-Strategie: Phase 1 Personen/Orte/Daten, Phase 2 Werke/Organisationen
- Empfehlung: Separate TEI-Dateien pro Objekt (nicht in Metadaten-TEI einbetten)
- 5 offene Entscheidungen dokumentiert (lb, NER-Tiefe, Confidence-Attribute, Mehrsprachigkeit, Umschlaege)

**teiCrafter-integration.md** (8 Abschnitte):
- JSON-Import-Spec fuer teiCrafter Step 1 (neuer Dateityp .json)
- Auto-Vorbelegung von Step 2 aus JSON-Metadaten
- 3 Mapping-Templates: szd-correspondence, szd-manuscript, szd-print
- Sprach-Erweiterung (en/fr/it/es) + Epoche 20c
- DTABf-Schema: 8 neue Elemente (gap, del, add, stamp, table, row, cell, cb)
- Seitentrenner korrigiert: `|{n}|` statt `\n\n---\n\n`
- Alle 5 offenen Punkte aus htr-interchange-format.md §8 geloest

### Erkenntnisse

1. **Seitentrenner-Konvention**: teiCrafter verwendet `|{n}|` in allen Demo-Mappings — das Interchange-Format muss sich anpassen, nicht umgekehrt.
2. **DTABf-Schema-Luecken**: Diplomatische Transkriptionselemente (gap, del, add) fehlen im aktuellen Schema — muessen vor Nutzung ergaenzt werden.
3. **Zwei TEI-Schichten**: Metadaten-TEI (bestehend, Katalog) und Transkriptions-TEI (neu, pro Objekt) bleiben getrennt, verknuepft via PID.
4. **Bestehendes SZD-TEI hat keine Transkriptionsinhalte** — es ist ein reines Metadaten-Register, kein Editionsformat.

### Refactoring

CLAUDE.md, Plan.md und journal.md auf aktuellen Stand gebracht.

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
- L2: Schritt 3+4 als erledigt (teiCrafter, TEI-Zielstruktur), neue Schritte 5-7
- L3: Status auf ~62 Objekte, Interchange-Export als Schritt 6

### Erkenntnisse

1. **Verification-by-Vision funktioniert** — actionable Fehler in ~2 Min/Objekt, kein API-Cost fuer Claude-Kanal.
2. **Muster:** Drucktext korrekt, Handschrift gut, Korrekturen/Vermerke schwach (~60-70%).
3. **Pipeline-Bug:** Objekte mit vielen Bildern (o_szd.147: 64 Bilder) erzeugen leere Ergebnisse.
4. **Methodischer Beitrag:** VbV ist der staerkste Verifikationsansatz im Projekt — direkter Bild↔Text-Vergleich statt nur Textvergleich. Fuer den Aufsatz relevant.

---

## 2026-04-01 — Session 12: Mapping-Templates, JSON-Schema, DIA-XAI-Integration

### L2: 3 Bonus-Deliverables

**1. teiCrafter Mapping-Templates extrahiert**
3 eigenstaendige .md-Dateien aus teiCrafter-integration.md §4, abgelegt in `teiCrafter/data/demo/mappings/`:
- `correspondence-szd.md` — Gruppen I, D (Briefstruktur, diplomatisches Markup, HTR-Pipeline-Konvertierung)
- `manuscript-szd.md` — Gruppen A, E, G (Tagebuecher, Register, Konvolute, Tabellen)
- `print-szd.md` — Gruppen B, C, F, H (Typoskripte, Formulare, Korrekturfahnen, Zeitungsausschnitte)

**2. JSON-Schema als validierbare Datei**
`schemas/htr-interchange-v0.1.json` — das Schema aus htr-interchange-format.md §3 als eigenstaendige Datei. Aenderungen gegenueber Codeblock: `$id` auf GitHub Pages URL, `source.language` mit Regex-Pattern (`^[a-z]{2,3}$`), `source.document_type` als kontrolliertes Vokabular (14 Enum-Werte). Validiert mit `python -m json.tool`.

**3. DIA-XAI-Integrationskonzept**
`knowledge/dia-xai-integration.md` — 5 Abschnitte:
- Pipeline-Diagramm SZD-HTR → teiCrafter → DIA-XAI
- EQUALIS-Mapping: 5 Dimensionen (E/QUA/L/I/S) auf konkrete SZD-HTR-Datenquellen
- Metriken-Export (`dia-xai-metrics-v1` JSON) mit 2 Export-Punkten (nach HTR/VbV, nach teiCrafter-Review)
- Zeitplan: Was muss vor DIA-XAI Phase 1 (Mai 2026) fertig sein
- UC3 (HTR-Verifikation) und UC4 (TEI-Annotation) als Ziel-Use-Cases

### Erkenntnisse

1. **DIA-XAI ist Aggregator, nicht Verifikationstool** — importiert Metriken-JSON, macht keine eigene Analyse. Die Verifikation passiert in SZD-HTR (VbV) und teiCrafter (Expert-Review).
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

## Offene Fragen (Stand 2026-04-02)

- [ ] Optimale Bildgroesse: Resizing vor API-Call?
- [ ] Lizenz klaeren: MIT fuer Code, CC-BY fuer Daten?
- [ ] Korrektur-Markup: Erweitertes Markup noetig?
- [x] Fraktur-Erkennung: o_szd.2232 high confidence (Session 7)
- [x] Batch-Modus: transcribe.py (Session 5)
- [x] Konvolut: Gruppe G erstellt, o_szd.277 medium (Session 7)
- [ ] Provider-Vergleich: Claude Vision, GPT-4o (Phase 4)
- [~] Alle 2107 Objekte transkribieren — ~639/2107 fertig, Chunking fuer grosse Objekte eingebaut (Session 17)
- [x] quality_signals kalibrieren: v1.1, datengetrieben rekalibriert (Session 13)
- [ ] Prompt-Wirksamkeit: Vorsichts-Guidance ignoriert — Experiment noetig (Session 8)
- [x] o_szd.143 nur 20 Zeichen auf 3 Seiten — geloest: fehlende Bilder wegen API-Limit, Chunking eingebaut (Session 17)
- [x] Verification-by-Vision: Proof of Concept erfolgreich, Spec geschrieben (Session 11)
- [x] Pipeline-Bug: o_szd.147 repariert, 41 Bilder transkribiert (Session 13)
- [ ] VbV-Konfidenz gegen Ground Truth kalibrieren (nach Modellkonsensus-Validierung)
- [x] Modellkonsensus: 27 Objekte validiert, 18 Objekte GT-Pipeline mit 3 Modellen (Session 14)
- [x] Statistik-Dashboard im Frontend — Enhanced Stats + Diff mit echten Daten (Session 14)
- [~] Expert-Review: 26/2107 Objekte verifiziert (14 human + 12 agent), CER-Baseline steht (Session 18)
- [ ] Prompt-Ablation: V1/V2/V3 gegen GT messen (18 Objekte × 3 Varianten)
- [ ] Agent-Verifikation auf weitere Objekte ausweiten (v.a. Korrespondenzen)
- [ ] Fraktur-Post-Processing evaluieren (f/s-Verwechslungen automatisch korrigieren)
