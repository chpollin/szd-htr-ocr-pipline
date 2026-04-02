# SZD-HTR-OCR-Pipeline

Textextraktion aus digitalisierten Nachlassfaksimiles des Stefan-Zweig-Nachlasses (Literaturarchiv Salzburg). Teilprojekt von [Stefan Zweig Digital](https://stefanzweig.digital/).

## Ziel

Aufbau einer VLM-basierten HTR/OCR-Pipeline, die aus den digitalisierten Faksimiles des Zweig-Nachlasses maschinenlesbaren Text erzeugt. Die Transkriptionsergebnisse dienen als Bewertungsgrundlage für den Expert-in-the-Loop-Workflow im [DIA-XAI](https://github.com/chpollin/dia-xai)-Projekt.

## Datengrundlage

4 Sammlungen, ~2107 Objekte (im Backup), beschrieben in TEI-XML:

| Sammlung | Objekte | TEI-Quelle |
|---|---|---|
| Lebensdokumente | 143 | [TEI](https://stefanzweig.digital/o:szd.lebensdokumente/TEI_SOURCE) |
| Werke (Manuskripte) | 352 | [TEI](https://stefanzweig.digital/o:szd.werke/TEI_SOURCE) |
| Aufsatzablage | 624 | [TEI](https://stefanzweig.digital/o:szd.aufsatzablage/TEI_SOURCE) |
| Korrespondenzen | 1186 | Backup-Metadaten |

Sprachen: Deutsch (primär), Englisch, Französisch, Italienisch, Spanisch.

## Pipeline-Architektur

### Datenfluss

```
 Faksimile-Scans (JPG, ~5000x7400px)
 + TEI-XML-Metadaten + Backup-Metadaten
                │
                ▼
 ┌─────────────────────────────────────┐
 │  1. Kontext-Aufloesung              │
 │     tei_context.py                  │
 │     • TEI-XML → Titel, Datum,       │
 │       Sprache, Signatur, Objekttyp  │
 │     • resolve_group() → Prompt-     │
 │       Gruppe A-I (automatisch)      │
 └──────────────┬──────────────────────┘
                ▼
 ┌─────────────────────────────────────┐
 │  2. Dreischichtiger Prompt          │
 │     • System-Prompt (Rolle, Regeln, │
 │       JSON-Schema, Blank-Handling)  │
 │     • Gruppen-Prompt (1 von 9)      │
 │     • Objekt-Kontext (aus TEI)      │
 └──────────────┬──────────────────────┘
                ▼
 ┌─────────────────────────────────────┐
 │  3. VLM-Transkription               │
 │     Gemini 3.1 Flash Lite (t=0.1)  │
 │     Input: Alle Bilder + Prompt     │
 │     Output: JSON {pages[], conf.}   │
 │     • Exponential Backoff (429)     │
 │     • JSON-Sanitisierung (Codeblock,│
 │       Escape-Fix, Retry)            │
 └──────────────┬──────────────────────┘
                ▼
 ┌─────────────────────────────────────┐
 │  4. Enrichment & Quality Signals    │
 │     quality_signals.py v1.4         │
 │     • page.type (content/blank/     │
 │       color_chart) pro Seite        │
 │     • DWR, Marker-Dichte, Duplikate │
 │     • Sprachkonsistenz (TEI vs. det)│
 │     • needs_review + Gruende        │
 └──────────────┬──────────────────────┘
                ▼
 results/{collection}/{object_id}_{model}.json
        │
 ┌──────┼──────────────────────────────┐
 │      ▼                              ▼
 │  verify.py                   build_viewer_data.py
 │  Multi-Model-Konsensus       → catalog.json
 │  (Flash Lite + Flash         → data/{collection}.json
 │   + Claude Judge)            → data/knowledge.json
 │      │                       → docs/ Viewer
 │      ▼
 │  generate_gt.py
 │  3-Modell-GT-Pipeline
 │  (Flash Lite + Flash + Pro)
 │  → groundtruth/*_gt_draft.json
 └─────────────────────────────────────┘
```

### Dreischichtiges Prompt-System

| Schicht | Funktion |
|---|---|
| **System-Prompt** | Rolle, Regeln, JSON-Output (fuer alle Objekte gleich) |
| **Gruppen-Prompt** | Typspezifische Anweisungen (9 Gruppen, s.u.) |
| **Objekt-Kontext** | Metadaten aus TEI-XML (Sprache, Hand, Instrument, Typ) |

### Prompt-Gruppen

| Gruppe | Objekte | Hauptmerkmal |
|---|---|---|
| A: Handschrift | Tagebücher, Notizbücher, Manuskripte | Zweigs Handschrift, Kurrent |
| B: Maschinenschrift | Typoskripte, Durchschläge | Formaler Text, mehrsprachig |
| C: Formular | Rechtsdokumente, Finanzen | Druck + Handschrift gemischt |
| D: Kurztext | Diverses, Büromaterialien | Wenig Text, heterogen |
| E: Tabellarisch | Verzeichnisse, Kalender | Listen, Register |
| F: Korrekturfahne | Druckfahnen mit Korrekturen | Druck + handschriftl. Korrekturen |
| G: Konvolut | Gemischte Materialien | Heterogene Objekte in einem Konvolut |
| H: Zeitungsausschnitt | Presseausschnitte | Gedruckt, ggf. Fraktur |
| I: Korrespondenz | Briefe, Postkarten | Briefstruktur, Handschrift |

## Status

**575 / 2107 Objekte** transkribiert (27%), **3463 / 18719 Seiten** (18%). Quality Signals v1.4 mit Seitentyp-Klassifikation (`content`/`blank`/`color_chart`) und Dictionary Word Ratio (DWR). Multi-Model-Konsensus-Verifikation (Gemini Flash Lite + Gemini 3 Flash + Claude Judge) mit 4-Tier-Klassifikation (verified/moderate/review/divergent). Ground-Truth-Pipeline mit 3-Modell-Merge (18 Objekte, 46 Seiten).

| Sammlung | Objekte | Seiten | Content | Blank | Farbskala | Abdeckung |
|---|---:|---:|---:|---:|---:|---:|
| Lebensdokumente | 112 / 127 | 992 | 614 | 289 | 46 | 88% |
| Korrespondenzen | 290 / 1186 | 923 | 740 | 138 | 34 | 24% |
| Aufsatzablage | 117 / 625 | 583 | 470 | 106 | 2 | 19% |
| Werke | 56 / 169 | 965 | 551 | 352 | 52 | 33% |

Viewer & Katalog: [chpollin.github.io/szd-htr-ocr-pipeline](https://chpollin.github.io/szd-htr-ocr-pipeline/)

## Projektstruktur

```
├── pipeline/
│   ├── prompts/              ← 9 Gruppen-Prompts + System-Prompt + Layout-Prompt
│   ├── transcribe.py         ← Batch-CLI (Einzel/Sammlung/Alle)
│   ├── verify.py             ← Multi-Model-Konsensus-Verifikation
│   ├── generate_gt.py        ← 3-Modell-GT-Pipeline (Flash Lite + Flash + Pro)
│   ├── quality_signals.py    ← 8 Qualitaetssignale + Seitentyp + DWR (v1.4)
│   ├── evaluate.py           ← CER/WER + word_overlap + normalize_for_consensus
│   ├── quality_report.py     ← Aggregierte Qualitaetsstatistiken
│   ├── layout_analysis.py    ← VLM-basierte Layout-Analyse (Regionen + BBoxes)
│   ├── export_pagexml.py     ← Merged OCR + Layout → PAGE XML 2019
│   ├── tei_context.py        ← TEI-Parser, resolve_group(), format_context()
│   ├── config.py             ← Pfade, API-Key, Sammlungs-Mapping
│   ├── build_viewer_data.py  ← Baut catalog.json + data/*.json + knowledge.json
│   └── test_single.py        ← Test-Script (7 Referenz-Objekte)
├── data/                     ← TEI-Metadaten (4 Sammlungen)
├── results/                  ← Transkriptionsergebnisse (enriched JSON)
│   └── groundtruth/          ← GT-Drafts (3-Modell-Merge + Expert-Review)
├── knowledge/                ← Research Vault (Methodik, Datenanalyse, Journal)
└── docs/                     ← GitHub Pages (Single-Page-App)
    ├── index.html            ← Katalog + Viewer + Knowledge Vault + Projekt
    ├── app.css               ← SZD-Design-System
    ├── app.js                ← Routing, Rendering, Edit, Export, Knowledge
    ├── catalog.json          ← Leichtgewichtige Metadaten
    └── data/                 ← Transkriptionen + Knowledge-Daten
```

## Setup

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY=AIza...    # oder in .env eintragen
```

## Nutzung

```bash
# Einzelnes Objekt transkribieren
python pipeline/transcribe.py o_szd.161 -c lebensdokumente

# Ganze Sammlung
python pipeline/transcribe.py -c lebensdokumente

# Alle 2107 Objekte
python pipeline/transcribe.py --all

# Nur Korrekturfahnen in Werke
python pipeline/transcribe.py -c werke -g korrekturfahne

# Vorschau ohne API-Calls
python pipeline/transcribe.py --all --dry-run

# Viewer-Daten aktualisieren
python pipeline/build_viewer_data.py

# Qualitaetsreport
python pipeline/quality_report.py

# Multi-Model-Konsensus (Verifikation)
python pipeline/verify.py o_szd.100 -c lebensdokumente
python pipeline/verify.py --sample 3 --dry-run

# CER-Berechnung (gegen Referenztranskription)
python pipeline/evaluate.py results/lebensdokumente/o_szd.100_*.json reference.txt
```

## Verwandte Projekte

- [zbz-ocr-tei](https://github.com/DigitalHumanitiesCraft/zbz-ocr-tei) — LLM-OCR-Pipeline für gedruckte Texte
- [coOCR HTR](https://github.com/DigitalHumanitiesCraft/co-ocr-htr) — Browser-basiertes HTR-Tool mit Expert-in-the-Loop
- [teiCrafter](https://github.com/DigitalHumanitiesCraft/teiCrafter) — TEI-Annotation nach Transkription

## Lizenz

MIT
