# SZD-HTR-OCR-Pipeline — Implementierungsplan

## Übersicht

VLM-basierte HTR/OCR-Pipeline für den Stefan-Zweig-Nachlass (Literaturarchiv Salzburg). 4 Sammlungen, 2305+ Objekte, dreischichtiges Prompt-System.

---

## Phase 1: Grundlagen (erledigt)

- [x] Repository angelegt, .gitignore, README.md
- [x] TEI-Metadaten aller 4 Sammlungen heruntergeladen und analysiert
  - Lebensdokumente (143), Werke (352), Aufsatzablage (624), Korrespondenzen (1186)
- [x] Dreischichtiges Prompt-System entwickelt (System → Gruppe → Objekt-Kontext)
- [x] 5 Gruppen-Prompts: A Handschrift, B Typoskript, C Formular, D Kurztext, E Tabellarisch
- [x] Test-Script `pipeline/test_single.py` — Gemini Vision API
- [x] Erste Tests: 4 Objekte, alle high confidence
- [x] Viewer `docs/viewer.html` — responsive Faksimile↔Transkription-Vergleich
- [x] Knowledge-Vault mit Datenanalysen

## Phase 2: Sammlungen erweitern (aktuell)

- [ ] Neue Gruppen-Prompts entwickeln:
  - F: Korrekturfahne (Druck + handschriftliche Korrekturen)
  - H: Zeitungsausschnitt (Fraktur, Spalten-Layout)
  - I: Korrespondenz (Briefstruktur, Anrede/Grußformel)
- [ ] Test-Objekte aus Werken transkribieren (Clarissa, Montaigne, Korrekturfahne)
- [ ] Test-Objekte aus Aufsatzablage (Zeitungsausschnitt)
- [ ] Test-Objekt aus Korrespondenzen (Brief)
- [ ] Viewer um Sammlungs-Navigation erweitern

## Phase 3: Pipeline-Automatisierung

- [ ] Objekt-Kontext automatisch aus TEI-XML generieren (statt manuell)
- [ ] Batch-Transkription: mehrere Objekte nacheinander
- [ ] Gruppenzuordnung automatisch aus TEI-Metadaten ableiten
- [ ] Ergebnisse strukturiert abspeichern (JSON pro Objekt)

## Phase 4: Qualität & Vergleich

- [ ] Provider-Vergleich: Gemini vs. Claude Vision vs. GPT-4o
- [ ] Prompt-Iteration basierend auf Ergebnissen
- [ ] Fraktur-Erkennung testen (Zeitungsausschnitte)
- [ ] Schwierige Handschriften identifizieren (low confidence)

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
| Bilder | Direkt von GAMS (keine lokalen Kopien nötig) |
| Output | JSON pro Objekt |
| Viewer | Statisches HTML (GitHub Pages) |
