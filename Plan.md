# SZD-HTR-OCR-Pipeline — Implementierungsplan

## Übersicht

VLM-basierte HTR/OCR-Pipeline fuer den Stefan-Zweig-Nachlass (Literaturarchiv Salzburg). 4 Sammlungen, ~2107 Objekte, dreischichtiges Prompt-System.

---

## Phase 1: Grundlagen (erledigt)

- [x] Repository angelegt, .gitignore, README.md
- [x] TEI-Metadaten aller 4 Sammlungen heruntergeladen und analysiert
- [x] Dreischichtiges Prompt-System entwickelt (System → Gruppe → Objekt-Kontext)
- [x] 5 Gruppen-Prompts: A Handschrift, B Typoskript, C Formular, D Kurztext, E Tabellarisch
- [x] Test-Script `pipeline/test_single.py` — Gemini Vision API
- [x] Erste Tests: 4 Objekte aus Lebensdokumenten, alle high confidence
- [x] Viewer `docs/viewer.html` — responsive Faksimile↔Transkription-Vergleich
- [x] Knowledge-Vault mit Datenanalysen

## Phase 2: Alle Sammlungen (erledigt)

- [x] Neue Gruppen-Prompts: F Korrekturfahne, H Zeitungsausschnitt, I Korrespondenz
- [x] Multi-Collection-Support in test_single.py (lebensdokumente, werke, aufsatzablage, korrespondenzen)
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

- [x] Objekt-Kontext automatisch aus TEI-XML generieren (`resolve_context()` in test_single.py und transcribe.py)
- [x] Batch-Transkription: `pipeline/transcribe.py` mit CLI für Einzel-/Batch-/Sammlungs-Modus
- [x] Gruppenzuordnung automatisch aus TEI-Metadaten (`resolve_group()` mit Formular-Fix)
- [x] Ergebnisse strukturiert abspeichern: `results/{collection}/{object_id}_{model}.json`
- [x] Object Discovery aus Backup-Verzeichnissen (2107 Objekte über 4 Sammlungen)
- [x] Rate-Limiting, Skip-Logik, Fehlertoleranz
- [x] Erster Batch-Lauf: 5 Lebensdokumente, alle high confidence

## Phase 4: Qualität & Vergleich (nächster Schritt)

### 4a: Pilot & Ground Truth
- [ ] **Pilot**: 5 Seiten manuell prüfen (→ `knowledge/pilot-design.md`)
- [ ] Pilot-Ergebnisse auswerten, CER pro Gruppe bestimmen
- [ ] Annotationsprotokoll ggf. anpassen (→ `knowledge/annotation-protocol.md`)
- [ ] Ground-Truth-Sample: 30 Objekte manuell transkribieren (→ `knowledge/verification-concept.md` §1)
- [ ] CER-Berechnungsscript (Lane 3)

### 4b: Quality Signals & Batch
- [ ] `quality_signals` implementieren (→ `verification-concept.md` §2.5, Lane 3)
- [ ] `needs_review`-Indikator im Viewer (Lane 1)
- [ ] Alle Sammlungen komplett transkribieren (2107 Objekte)
- [ ] quality_signals-Schwellenwerte anhand GT kalibrieren

### 4c: Prompt-Experiment & Provider-Vergleich
- [ ] Prompt-Wirksamkeit: 3 Varianten × 30 GT-Objekte (→ `verification-concept.md` §3)
- [ ] Cross-Model-Verification: Gemini + Claude Sonnet auf GT-Sample (→ `verification-concept.md` §4)
- [ ] Provider-Vergleich: Gemini vs. Claude vs. GPT-4o
- [ ] Diff-Ansicht im Viewer (Lane 1)
- [ ] Optimale Bildgröße testen (Resizing vor API-Call)

## Phase 5: TEI-Integration

### 5a: Interchange-Format und teiCrafter-Integration (Spezifikation fertig)
- [x] L2: HTR-Interchange-Format spezifizieren (JSON Schema v0.1) → `knowledge/htr-interchange-format.md`
- [x] L2: teiCrafter-Integrationskonzept → `knowledge/teiCrafter-integration.md` (JSON-Import, 3 Mapping-Templates, Sprach-/Epochen-Erweiterung, DTABf-Schema-Erweiterungen)
- [x] L2: TEI-Zielstruktur → `knowledge/tei-target-structure.md` (DTABf-Profil, Markup→TEI-Mapping, NER-Strategie)
- [ ] L3: szd-htr-Output auf Interchange-Format abbilden (`export_interchange.py`)
- [ ] teiCrafter-Repo: JSON-Import in Step 1 einbauen
- [ ] teiCrafter-Repo: Sprachen (en/fr/it/es) und Epoche (20c) ergaenzen
- [ ] teiCrafter-Repo: DTABf-Schema um gap/del/add/stamp/table/cb erweitern
- [ ] teiCrafter-Repo: SZD-Mapping-Templates einfuegen (3 Templates)

### 5b: TEI-Annotation & Integration
- [ ] teiCrafter: HTR-JSON → TEI-XML (LLM-gestuetzte Annotation mit DTABf-Schema)
- [ ] NER auf transkribierten Texten (Phase 1: Personen, Orte, Daten)
- [ ] Integration in SZD-Datenmodell (separate TEI-Dateien pro Objekt, verknuepft via PID)

## Phase 6: DIA-XAI-Bewertung (ab Oktober 2026)

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
