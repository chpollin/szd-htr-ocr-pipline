# SZD-HTR-OCR-Pipeline — Implementierungsplan

## Übersicht

VLM-basierte HTR/OCR-Pipeline fuer den Stefan-Zweig-Nachlass (Literaturarchiv Salzburg). 4 Sammlungen, ~2107 Objekte, 4-schichtiges Prompt-System (System → Gruppe/Objekt → Kontext).

---

## Phase 1: Grundlagen (erledigt)

- [x] Repository angelegt, .gitignore, README.md
- [x] TEI-Metadaten aller 4 Sammlungen heruntergeladen und analysiert
- [x] Dreischichtiges Prompt-System entwickelt (System → Gruppe → Objekt-Kontext)
- [x] 5 Gruppen-Prompts: A Handschrift, B Typoskript, C Formular, D Kurztext, E Tabellarisch
- [x] Test-Script (Gemini Vision API, migriert nach `transcribe.py`)
- [x] Erste Tests: 4 Objekte aus Lebensdokumenten, alle high confidence
- [x] Viewer `docs/index.html` — responsive Faksimile↔Transkription-Vergleich
- [x] Knowledge-Vault mit Datenanalysen

## Phase 2: Alle Sammlungen (erledigt)

- [x] Neue Gruppen-Prompts: F Korrekturfahne, H Zeitungsausschnitt, I Korrespondenz
- [x] Multi-Collection-Support (lebensdokumente, werke, aufsatzablage, korrespondenzen)
- [x] TEI-Parser `pipeline/tei_context.py` für automatische Kontext-Generierung
- [x] Enriched JSON-Output mit Metadaten und GAMS-URLs
- [x] `pipeline/build_viewer_data.py` — baut catalog.json + data/{collection}.json
- [x] Test-Objekte aus allen 4 Sammlungen transkribiert (7/7 high confidence)
- [x] Viewer mit Sammlungs-Tabs und dynamischem Laden aus data.json
- [x] Frontend-Refactoring: Single-Page-App mit Katalog + Viewer + Edit-Modus
- [x] SZD-Design-System (Burgundy/Gold, Source Serif/Sans)
- [x] Daten-Split: catalog.json + data/{collection}.json
- [x] GAMS-Thumbnails im Katalog
- [x] 3-Ebenen-Verifikation statt naiver VLM-Konfidenz

## Phase 3: Pipeline-Automatisierung (erledigt)

- [x] Objekt-Kontext automatisch aus TEI-XML generieren (`resolve_context()` in transcribe.py)
- [x] Batch-Transkription: `pipeline/transcribe.py` mit CLI für Einzel-/Batch-/Sammlungs-Modus
- [x] Gruppenzuordnung automatisch aus TEI-Metadaten (`resolve_group()` mit Formular-Fix)
- [x] Ergebnisse strukturiert abspeichern: `results/{collection}/{object_id}_{model}.json`
- [x] Object Discovery aus Backup-Verzeichnissen (2107 Objekte über 4 Sammlungen)
- [x] Rate-Limiting, Skip-Logik, Fehlertoleranz
- [x] Erster Batch-Lauf: 5 Lebensdokumente, alle high confidence
- [x] Gruppe G (Konvolut) erstellt: Prompt, resolve_group(), 1 Test-Objekt
- [x] Gezieltes Sample: 87 Objekte transkribiert (10/Gruppe, alle 4 Sammlungen)
- [x] JSON-Parsing gehaertet: Codeblock-Strip, Escape-Fix, Retry, leere Antworten
- [x] Chunking: Objekte mit >20 Bildern automatisch in Chunks aufteilen + mergen (Session 17)
- [x] Objekt-Prompts: 4. Prompt-Schicht (`prompts/objects/{id}.md`) fuer Spezialfaelle (Session 17)
- [x] `quality_signals.py`: 6 Signale + needs_review-Flag, integriert in transcribe.py + build_viewer_data.py
- [x] Backfill: alle 87 Ergebnis-JSONs mit quality_signals angereichert
- [x] quality_signals v1.1: Schwellenwerte rekalibriert (68% → 44% needs_review)
- [x] `evaluate.py`: CER/WER-Berechnung mit Normalisierung per Annotationsprotokoll
- [x] `quality_report.py`: Aggregierte Qualitaetsstatistiken pro Gruppe/Sammlung
- [x] `build_viewer_data.py`: qualitySignals (charsPerPage, duplicatePagePairs etc.) an Frontend durchgereicht
- [x] Exponential Backoff (429/Rate-Limit-Retry) in transcribe.py fuer parallele Batch-Laeufe

## Phase 4: Qualitaet & Vergleich (laufend)

### 4a: Ground Truth
- [x] CER-Berechnungsscript (`pipeline/evaluate.py`)
- [x] Modellkonsensus-Metriken v2: `word_overlap()`, `effective_cer`, 4-Tier-Klassifikation (Session 14)
- [x] GT-Pipeline: `generate_gt.py` — 3-Modell-Merge (Flash Lite + Flash + Pro), 18 Objekte, 46 Content-Seiten (Session 14)
- [x] GT-Drafts in `results/groundtruth/` — consensus_3of3 (33%), majority_2of3 (43%), pro_only (24%)
- [x] Pilot uebersprungen — Modellkonsensus-Validierung + GT-Pipeline beantworten Pilotfragen empirisch
- [~] **Expert-Review**: 3/18 GT-Objekte verifiziert (o_szd.153, o_szd.137, o_szd.194). 15 ausstehend.
- [ ] quality_signals-Schwellenwerte anhand GT kalibrieren

### 4b: Quality Signals & Batch
- [x] `quality_signals` implementieren (8 Signale + page.type + DWR, v1.4)
- [x] `needs_review`-Indikator im Viewer
- [x] quality_signals v1.1–v1.4: Rekalibrierung, Leerseiten-Klassifikation, DWR, Duplikat-Schwelle 200→50
- [x] System-Prompt: JSON-Schema, Blank-Page-Handling, Konfidenz-Kriterien, Bleed-Through-Regel
- [~] Alle Sammlungen transkribieren (~646/2107 Objekte, 31%). Lebensdokumente 100%.
- [ ] quality_signals-Schwellenwerte anhand GT kalibrieren

### 4c: Modellkonsensus & Vergleich
- [x] `verify.py`: Modellkonsensus (Flash Lite + Flash + Claude Judge)
- [x] Modellkonsensus-Validierung: 29 Objekte (3/Gruppe), 4-Tier-Ergebnis: 26% verified, 33% moderate, 15% review, 26% divergent
- [x] Diff-Ansicht im Viewer (echte Modellkonsensus-Daten, CER, Modell-Namen)
- [x] Statistik-Dashboard im Frontend (Seiten, Konfidenz, DWR, Modellkonsensus, Review)
- [x] GT Review-Modus: 3-Varianten-Panel, Approve, localStorage, JSON-Export
### 4d: Frontend & Dokumentation
- [x] Knowledge Vault im Frontend: 12 Markdown-Dokumente als navigierbare Ansicht (`#knowledge`, `#knowledge/{slug}`) (Session 15)
- [x] Projekt-Seite aus README.md (`#about`) (Session 15)
- [x] `build_viewer_data.py`: `build_knowledge()` — Markdown → HTML → knowledge.json (Session 15)
- [x] Layout-Analyse (`layout_analysis.py`) + PAGE XML Export (`export_pagexml.py`) (Session 14)
- [x] Lokaler Dev-Server (`serve.py`) mit Review-API: POST /api/approve, /api/edit (Session 17)
- [x] Expert-Review Write-Back (`import_reviews.py`) + 3-stufiger Review-Status (Session 16)
- [x] Katalog-Bereinigung: Duplikate (Pro-Modell), Color-Chart-Seiten, Test-Daten gefiltert (Session 16-17)

## Phase 5: DIA-XAI-Bewertung (ab Oktober 2026)

- [ ] Transkriptionsergebnisse als Input für Expert-in-the-Loop-Workflow
- [ ] EQUALIS-Evaluierung

---

## Technologie

| Komponente | Aktuell |
|---|---|
| VLM | Gemini 3.1 Flash Lite (Preview) |
| SDK | google-genai |
| TEI-Parser | xml.etree.ElementTree (stdlib) |
| Bilder | Lokales Backup (4 Sammlungen, 2107 Objekte) |
| Output | Enriched JSON pro Objekt, nach Sammlung strukturiert |
| CLI | `pipeline/transcribe.py` (Einzel/Batch/Sammlung) |
| Viewer | Single-Page-App (index.html + app.js + app.css), catalog.json + data/{collection}.json |

---

## Entscheidungslog

| Datum | Entscheidung | Begruendung |
|---|---|---|
| 2026-04-01 | Pilot vor vollem GT-Sample | CER unbekannt — Sample-Design ohne Pilot ist blind |
| 2026-04-01 | quality_signals sofort | Kostet nichts, braucht kein GT, bietet Triage fuer Batch |
| 2026-04-01 | Cross-Model: Agreement-First | Unabhaengige Doppeltranskription methodisch sauberer |
| 2026-04-01 | Claude Sonnet als zweites Modell | Max. Diversitaet zu Gemini, starke Baseline, moderate Kosten |
| 2026-04-01 | Gezieltes Sample statt voller Batch | 10/Gruppe reicht fuer group_text_density und Gruppenvergleich |
| 2026-04-01 | quality_signals v1.2: Leerseiten-Klassifikation | VLM erkennt Blanks/Farbskalen in Notes — Post-Processing statt Pre-Filtering |
| 2026-04-01 | DWR statt PPPL als GT-freie Metrik | Keine schwere Dependency (transformers), wissenschaftlich fundiert (Springmann 2016) |
| 2026-04-01 | Modellkonsensus statt manuellem GT | Zhang et al. 2025 (ICLR 2026): 3 Modelle + Judge skalierbarer als 30 Objekte manuell |
| 2026-04-01 | Gemini 3 Flash als Modell B | Staerker als Flash Lite, gleiche API, kein Provider-Wechsel noetig |
| 2026-04-02 | word_overlap + effective_cer statt CER-only | CER bestraft Reading-Order-Divergenz unfair; Jaccard auf Wortmengen robust |
| 2026-04-02 | 4-Tier statt 3-Tier Modellkonsensus | "review" als Zwischenstufe fuer 75-90% word_overlap |
| 2026-04-02 | Gemini Pro als 3. GT-Modell | Gleiche API, staerkstes Gemini-Modell, kein Provider-Wechsel |
| 2026-04-02 | Pilot uebersprungen | Modellkonsensus-Validierung + GT-Pipeline beantworten Pilotfragen empirisch |
| 2026-04-02 | Pre-rendered Markdown statt Client-Side | Null Runtime-Dependencies, Wiki-Links zur Build-Zeit aufgeloest |
| 2026-04-02 | Chunking statt Downscaling | Volle Bildaufloesung beibehalten, 20 Bilder/Chunk sicher unter API-Limit |
| 2026-04-02 | Objekt-Prompts als 4. Schicht | Spezialfaelle (Tabellen, Formulare) ohne Gruppen-Prompt-Aenderung loesbar |
| 2026-04-02 | serve.py statt localStorage | Pipeline-JSONs als einzige Quelle der Wahrheit, kein manueller Export noetig |
| 2026-04-02 | Whitelist statt Blacklist fuer Katalog | SKIP_SUFFIXES-Ansatz fragil bei neuen Modellen — Whitelist robuster (TODO) |
