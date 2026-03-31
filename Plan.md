# SZD-HTR-OCR-Pipeline — Implementierungsplan

## Übersicht

VLM-basierte HTR/OCR-Pipeline für den Stefan-Zweig-Nachlass (Literaturarchiv Salzburg). 4 Sammlungen, 2305+ Objekte, dreischichtiges Prompt-System.

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
- [x] `pipeline/build_viewer_data.py` — baut docs/data.json aus Ergebnissen
- [x] Test-Objekte aus allen 4 Sammlungen transkribiert (7/7 high confidence)
- [x] Viewer mit Sammlungs-Tabs und dynamischem Laden aus data.json

## Phase 3: Pipeline-Automatisierung (erledigt)

- [x] Objekt-Kontext automatisch aus TEI-XML generieren (`resolve_context()` in test_single.py und transcribe.py)
- [x] Batch-Transkription: `pipeline/transcribe.py` mit CLI für Einzel-/Batch-/Sammlungs-Modus
- [x] Gruppenzuordnung automatisch aus TEI-Metadaten (`resolve_group()` mit Formular-Fix)
- [x] Ergebnisse strukturiert abspeichern: `results/{collection}/{object_id}_{model}.json`
- [x] Object Discovery aus Backup-Verzeichnissen (2107 Objekte über 4 Sammlungen)
- [x] Rate-Limiting, Skip-Logik, Fehlertoleranz
- [x] Erster Batch-Lauf: 5 Lebensdokumente, alle high confidence

## Phase 4: Qualität & Vergleich (nächster Schritt)

- [ ] Alle Sammlungen komplett transkribieren (2107 Objekte)
- [ ] Provider-Vergleich: Gemini vs. Claude Vision vs. GPT-4o
- [ ] Prompt-Iteration basierend auf Ergebnissen
- [ ] Fraktur-Erkennung testen (echte Fraktur-Zeitungsausschnitte finden)
- [ ] Schwierige Handschriften identifizieren (Objekte mit low confidence suchen)
- [ ] Optimale Bildgröße testen (Resizing vor API-Call)

## Phase 5: TEI-Integration

- [ ] Rohtext → TEI-XML via teiCrafter-Pipeline
- [ ] NER auf transkribierten Texten
- [ ] Integration in SZD-Datenmodell

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
| Viewer | Statisches HTML + data.json (GitHub Pages) |
