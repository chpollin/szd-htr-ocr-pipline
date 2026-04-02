# SZD-HTR — Textextraktion aus digitalisierten Nachlassfaksimiles

## Projektziel

VLM-basierte HTR/OCR-Pipeline für den Stefan-Zweig-Nachlass (Literaturarchiv Salzburg). Erzeugt maschinenlesbaren Text aus digitalisierten Faksimiles. Teilprojekt von [Stefan Zweig Digital](https://stefanzweig.digital/), liefert Textdaten für den Expert-in-the-Loop-Workflow im [DIA-XAI](https://github.com/chpollin/dia-xai)-Projekt (PLUS Early Career Grant, ab Mai 2026).

- GitHub: https://github.com/chpollin/szd-htr-ocr-pipeline
- Python 3.10+ (getestet mit 3.11)
- Lizenz: MIT

## Aktueller Stand (2. April 2026)

Phasen 1–3 erledigt, Phase 4 laufend. Details, offene Aufgaben und Entscheidungslog → `Plan.md`.

### Transkriptionsfortschritt

**601 / 2107 Objekte** im Katalog (29%), **3588 Seiten** im Viewer (color_chart-Seiten gefiltert):

| Sammlung | Objekte | Seiten | Content | Blank | Farbskala | Abdeckung |
|---|---:|---:|---:|---:|---:|---:|
| Lebensdokumente | 112 / 127 | 992 | 614 | 289 | 46 | 88% |
| Korrespondenzen | 290 / 1186 | 923 | 740 | 138 | 34 | 24% |
| Aufsatzablage | 117 / 625 | 583 | 470 | 106 | 2 | 19% |
| Werke | 56 / 169 | 965 | 551 | 352 | 52 | 33% |

Werke haben den hoechsten Leerseiten-Anteil (42%) — Manuskripte wurden recto+verso gescannt, Zweig schrieb primaer auf Recto-Seiten, gelegentlich Notizen auf Verso.

### Pipeline-Status

- **Alle 9 Prompt-Gruppen** aktiv (A-I), alle getestet
- **quality_signals v1.4**: 8 Signale + `page.type` als First-Class-Feld auf jedem Page-Objekt (`content`/`blank`/`color_chart`) + DWR (Dictionary Word Ratio). Duplikat-Schwelle gesenkt fuer Halluzinationserkennung. needs_review bei ~41%.
- **Multi-Model-Konsensus** (`verify.py`): Gemini Flash Lite + Gemini 3 Flash + Claude Judge. 29 Konsensus-Dateien. Blank-Seiten werden bei CER uebersprungen. Erste Tests: ~5% CER bei Typoskripten, hoeher bei Handschrift. Siehe `verification-concept.md` §7.
- **CER/WER-Evaluierung**: `evaluate.py` mit Normalisierung per Annotationsprotokoll, `quality_report.py` fuer Aggregatstatistiken
- **JSON-Parsing gehaertet**: Codeblock-Strip, Escape-Fix (`\j`, `\w`), Retry, Absicherung gegen leere API-Antworten
- **System-Prompt**: Explizites JSON-Schema, Blank-Page-Handling, Konfidenz-Kriterien
- **Expert-Review Write-Back** (`import_reviews.py`): Importiert Frontend-Exporte (GT-Reviews + regulaere Edits) zurueck in Pipeline-JSONs. Schreibt `review`-Objekt mit `status`, `reviewed_by`, `reviewed_at`. Unterstuetzt Approve ohne Edit (`reviewed: true`).
- **Lokaler Dev-Server** (`serve.py`): Ersetzt VS Code Live Server. API-Endpunkte fuer Approve/Edit schreiben direkt in Pipeline-JSONs — kein manueller JSON-Export noetig. Frontend erkennt lokalen Server via `GET /api/status`.
- **Chunking**: Objekte mit >20 Bildern werden automatisch in Chunks aufgeteilt (konfigurierbar via `--chunk-size`). Ergebnisse werden gemergt, Seitennummerierung bleibt durchgehend. Getestet mit Hauptbuch (249 Bilder, 13 Chunks).
- **Objekt-Prompts**: Optionaler 4. Prompt-Layer (`prompts/objects/{object_id}.md`) ueberschreibt den Gruppen-Prompt fuer Spezialfaelle (z.B. Bankkontoauszuege mit Tabellenstruktur).
- **3-stufiger Review-Status**: `needs_review: true` (rot), kein Review (LLM OK, orange), `review.status: "approved"` (gruen). `gtVerified` fuer GT-Objekte.
- **Katalog-Bereinigung**: Test-Daten, Layout-JSONs, GT-Drafts, Pro-Zwischenergebnisse aus Viewer-Daten gefiltert (627 → 601). Color-Chart-Seiten (158) aus Viewer entfernt.

### Naechste Schritte

1. **Expert-Review**: 18 GT-Objekte im Frontend pruefen und approven (localhost, GT Review-Modus)
2. **Batch weiterfahren**: v.a. Korrespondenzen (24%) und Aufsatzablage (19%)
3. **Prompt-Ablation**: V1/V2/V3 × 18 GT-Objekte nach Expert-Review
4. **Layout-Analyse ausweiten**: Stratifizierter Test (1 Objekt/Gruppe), dann Batch-Lauf
5. **TEI-Export**: `export_interchange.py` (Phase 5)

Erledigt (Session 14): Konsensus-Metriken v2, GT-Pipeline, Frontend GT-Review, Layout-Analyse + PAGE XML.
Erledigt (Session 15): Knowledge Vault im Frontend, Projekt-Seite, README aktualisiert.
Erledigt (Session 16): Expert-Review Write-Back (`import_reviews.py`), 3-stufiger Review-Status, Katalog-Bereinigung, Color-Chart-Filter, Knowledge Vault Konsolidierung (13 → 11 Docs), Frontmatter vereinheitlicht, Claude Code Banner.
Erledigt (Session 17): Chunking fuer grosse Objekte, Objekt-Prompts (`prompts/objects/`), lokaler Dev-Server (`serve.py`) mit Review-API, Hauptbuch (249 Bilder) transkribiert, Batch Korrespondenzen.

## Quelldaten

Lokales Backup unter `SZD_BACKUP_ROOT` (Default: `C:/Users/Chrisi/Documents/PROJECTS/szd-backup/data/`):

| Unterverzeichnis | Sammlung (intern) | Objekte im Backup | TEI-Datei |
|---|---|---|---|
| `lebensdokumente/` | `lebensdokumente` | ~127 | `szd_lebensdokumente_tei.xml` |
| `korrespondenzen/` | `korrespondenzen` | ~1186 | `szd_korrespondenzen_tei.xml` |
| `aufsatz/` | `aufsatzablage` | ~625 | `szd_aufsatzablage_tei.xml` |
| `facsimiles/` | `werke` | ~169 | `szd_werke_tei.xml` |

Jedes Objekt: `o_szd.{nr}/metadata.json` + `o_szd.{nr}/mets.xml` + `o_szd.{nr}/images/IMG_*.jpg` (ca. 4912x7360px). Gesamt: **18719 Bilder** ueber alle 4 Sammlungen. TEI-XML enthält mehr Objekte als im Backup vorhanden sind. METS-Dateien enthalten Bildreihenfolge und EXIF-Dimensionen, aber keine Seitentyp-Annotation (0/1222 Labels leer).

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
 │  2. Prompt-System (4 Schichten)      │
 │     • System-Prompt (Rolle, Regeln, │
 │       JSON-Schema, Blank-Handling)  │
 │     • Gruppen-Prompt (1 von 9)      │
 │       ODER Objekt-Prompt (Override) │
 │     • Objekt-Kontext (aus TEI)      │
 └──────────────┬──────────────────────┘
                ▼
 ┌─────────────────────────────────────┐
 │  3. VLM-Transkription               │
 │     Gemini 3.1 Flash Lite (t=0.1)  │
 │     Input: Alle Bilder + Prompt     │
 │     Output: JSON {pages[], conf.}   │
 │     • Chunking: >20 Bilder → auto   │
 │       Split + Merge                 │
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
        ┌───────┼────────────────────┐
        ▼       ▼                    ▼
   verify.py  layout_analysis.py   build_viewer_data.py
   Konsensus  VLM-Layout (1/Seite) → catalog.json
   (3 Modelle) → *_layout.json     → data/{collection}.json
        │               │           → docs/ Viewer
        │               ▼                    │
        │       export_pagexml.py            │ Expert-Review
        │       (deterministisch)            ▼
        │       → *_page/page_NNN.xml  serve.py (lokaler Dev-Server)
        │         (PAGE XML 2019)      POST /api/approve → JSON
        └───────────────────────────┘  POST /api/edit → JSON
                                       (review.status, edits)
```

### Prompt-System (4 Schichten)

1. **System-Prompt** (`prompts/system.md`): Rolle, diplomatische Transkriptionsregeln, JSON-Output-Format, Blank-Page-Handling
2. **Gruppen-Prompt** (`prompts/group_*.md`): Spezifische Anweisungen pro Dokumenttyp (9 Gruppen)
3. **Objekt-Prompt** (`prompts/objects/{object_id}.md`, optional): Ueberschreibt Gruppen-Prompt fuer Spezialfaelle
4. **Objekt-Kontext** (automatisch aus TEI-XML via `tei_context.py`): Titel, Signatur, Datum, Sprache, Objekttyp etc.

Objekt-Prompts greifen automatisch, wenn eine Datei `prompts/objects/{object_id}.md` existiert. Aktuell: `o_szd.1056` (Bankkontoauszuege).

### 9 Prompt-Gruppen

| Kürzel | Gruppe | Prompt-Datei |
|---|---|---|
| A | Handschrift | `group_a_handschrift.md` |
| B | Typoskript | `group_b_typoskript.md` |
| C | Formular | `group_c_formular.md` |
| D | Kurztext | `group_d_kurztext.md` |
| E | Tabellarisch | `group_e_tabellarisch.md` |
| F | Korrekturfahne | `group_f_korrekturfahne.md` |
| G | Konvolut | `group_g_konvolut.md` |
| H | Zeitungsausschnitt | `group_h_zeitungsausschnitt.md` |
| I | Korrespondenz | `group_i_korrespondenz.md` |

Gruppenzuordnung automatisch via `resolve_group()` in `tei_context.py`: Korrespondenzen → immer I, Konvolute → G, sonst Entscheidungsbaum über `objecttyp` und `classification` aus TEI. Fallback: Handschrift.

## Projektstruktur

```
szd-htr/
├── CLAUDE.md
├── Plan.md                          ← Phasen-Status, Aufgaben, Entscheidungslog
├── requirements.txt                 ← google-genai, python-dotenv, markdown, pyyaml
├── .env                             ← API Keys (nicht committet)
├── schemas/
│   ├── htr-interchange-v0.1.json    ← Validierbares JSON-Schema (Interchange-Format)
│   └── layout-regions-v0.1.json     ← JSON-Schema fuer Layout-Analyse-Output
├── pipeline/
│   ├── config.py                    ← Pfade, API-Key, Sammlungs-Mapping, Konstanten
│   ├── transcribe.py                ← Batch-CLI: Einzel-/Sammlungs-/Gesamtmodus
│   ├── quality_signals.py           ← 8 Signale + page.type + DWR (v1.4)
│   ├── verify.py                    ← Multi-Model-Konsensus (Flash Lite + Flash + Claude Judge)
│   ├── evaluate.py                  ← CER/WER-Berechnung + normalize_for_consensus
│   ├── quality_report.py            ← Aggregierte Qualitaetsstatistiken ueber alle Ergebnisse
│   ├── backfill_page_types.py       ← Backfill: page.type auf bestehende JSONs stempeln
│   ├── run_sample_batch.py          ← Gezielter Batch: fuellt jede Gruppe auf 10 auf
│   ├── test_single.py               ← Testskript mit 7 hardcodierten Testobjekten
│   ├── tei_context.py               ← TEI-Parser, resolve_group(), format_context()
│   ├── layout_analysis.py            ← VLM-basierte Layout-Analyse (Regionen + Bounding Boxes)
│   ├── export_pagexml.py             ← Merged OCR + Layout → PAGE XML 2019
│   ├── generate_gt.py               ← 3-Modell-GT-Pipeline (Flash Lite + Flash + Pro)
│   ├── import_reviews.py            ← Expert-Review Write-Back (Frontend-Export → Pipeline-JSON)
│   ├── serve.py                     ← Lokaler Dev-Server mit Review-API (ersetzt Live Server)
│   ├── build_viewer_data.py         ← Baut catalog.json + data/*.json + knowledge.json
│   └── prompts/                     ← System-Prompt + 9 Gruppen-Prompts + Layout-Prompt
│       └── objects/                 ← Objekt-spezifische Prompt-Overrides (optional)
├── data/                            ← TEI-XML-Metadaten (4 Sammlungen)
├── results/
│   ├── test/                        ← 7 Legacy-Testergebnisse (nicht im Katalog)
│   ├── groundtruth/                 ← 18 GT-Drafts + Pro-Transkriptionen
│   ├── lebensdokumente/             ← 112 Ergebnisse + 18 Konsensus-JSONs
│   ├── werke/                       ← 56 Ergebnisse + 5 Konsensus-JSONs
│   ├── aufsatzablage/               ← 117 Ergebnisse + 3 Konsensus-JSONs
│   └── korrespondenzen/             ← 290 Ergebnisse + 3 Konsensus-JSONs
├── docs/
│   ├── index.html                   ← SPA: Katalog + Viewer + Knowledge Vault + Projekt
│   ├── app.css                      ← SZD-Design-System, Accessibility, Diff, Edit, Knowledge
│   ├── app.js                       ← Routing, Katalog, Viewer, Edit, Diff, Knowledge, About
│   ├── catalog.json                 ← Leichtgewichtige Metadaten fuer Katalog-Tabelle
│   └── data/                        ← Transkriptionsdaten + Knowledge (on-demand)
│       ├── lebensdokumente.json
│       ├── werke.json
│       ├── aufsatzablage.json
│       ├── korrespondenzen.json
│       ├── groundtruth.json         ← GT-Drafts fuer Expert-Review
│       └── knowledge.json           ← Knowledge Vault (10 Docs + About, pre-rendered HTML)
└── knowledge/                       ← Research Vault (Methodik, Datenanalyse, Journal)
    ├── index.md                     ← Map of Content (MOC)
    ├── data-overview.md             ← Datengrundlage (4 Sammlungen, 9 Gruppen)
    ├── verification-concept.md      ← GT, quality_signals, Cross-Model, VbV, GT-Pipeline
    ├── annotation-protocol.md       ← Transkriptionskonventionen
    ├── pilot-design.md              ← 5-Seiten-Pilot (historisch, nicht ausgefuehrt)
    ├── htr-interchange-format.md    ← JSON-Schema: szd-htr → teiCrafter
    ├── tei-target-structure.md      ← TEI-Zielformat (DTABf-Profil)
    ├── teiCrafter-integration.md    ← teiCrafter-Integration
    ├── layout-analysis.md           ← Layout-Analyse + PAGE XML Export
    ├── dia-xai-integration.md       ← DIA-XAI-Integration
    └── journal.md                   ← Session-Log (Sessions 1–17)
```

## CLI-Nutzung

```bash
# Setup
pip install -r requirements.txt
# .env braucht: GOOGLE_API_KEY=AIza...

# Einzelobjekt
python pipeline/transcribe.py o_szd.161 -c lebensdokumente

# Ganze Sammlung
python pipeline/transcribe.py -c werke

# Alle 4 Sammlungen
python pipeline/transcribe.py --all

# Nur bestimmte Gruppe
python pipeline/transcribe.py -c lebensdokumente --group handschrift

# Dry-Run (auflisten ohne API-Call)
python pipeline/transcribe.py --all --dry-run

# Weitere Optionen: --limit N, --max-images N, --delay 2.0, --force

# Grosse Objekte (>20 Bilder) werden automatisch in Chunks aufgeteilt
python pipeline/transcribe.py o_szd.143 -c lebensdokumente --chunk-size 20
```

Ergebnisse landen in `results/{collection}/{object_id}_{model}.json`. Bereits transkribierte Objekte werden übersprungen (außer `--force`).

```bash
# Lokaler Dev-Server (ersetzt VS Code Live Server)
python pipeline/serve.py                # Port 8000
python pipeline/serve.py --port 5501    # Anderer Port
python pipeline/serve.py --rebuild      # Viewer-Daten beim Start neu bauen

# API: Approve/Edit werden direkt vom Frontend an den Server geschickt
# POST /api/approve  → review.status = "approved" ins Pipeline-JSON
# POST /api/edit     → editierte Seiten + review ins Pipeline-JSON
# POST /api/rebuild  → Viewer-Daten neu bauen
# GET  /api/status   → {"local": true} (Frontend erkennt lokalen Server)
```

```bash
# Expert-Review importieren (CLI-Alternative, z.B. fuer Batch-Import)
python pipeline/import_reviews.py path/to/export.json [--dry-run] [--reviewer "Name"]

# Viewer-Daten neu bauen (nach Import oder Transkription)
python pipeline/build_viewer_data.py
```

## Umgebungsvariablen (.env)

| Variable | Pflicht | Default | Beschreibung |
|---|---|---|---|
| `GOOGLE_API_KEY` | Ja | — | Gemini API Key |
| `HTR_MODEL` | Nein | `gemini-3.1-flash-lite-preview` | Modell-ID |
| `SZD_BACKUP_ROOT` | Nein | `C:/Users/Chrisi/.../szd-backup/data` | Pfad zum lokalen Backup |
| `HTR_BATCH_DELAY` | Nein | `2.0` | Sekunden zwischen API-Calls |

## Output-Format (Ergebnis-JSON)

```json
{
  "object_id": "o_szd.100",
  "collection": "lebensdokumente",
  "group": "typoskript",
  "model": "gemini-3.1-flash-lite-preview",
  "metadata": {
    "title": "Agreement Longmans, Green u. Co. Inc.",
    "language": "Englisch",
    "images": ["https://gams.uni-graz.at/o:szd.100/IMG.1", "..."]
  },
  "context": "## Dieses Dokument\n- Titel: ...\n- Signatur: ...",
  "result": {
    "pages": [
      {"page": 1, "transcription": "...", "notes": "...", "type": "content"},
      {"page": 2, "transcription": "", "notes": "Rueckseite, leer.", "type": "blank"},
      {"page": 3, "transcription": "", "notes": "Farbskala fuer Archivierung.", "type": "color_chart"}
    ],
    "confidence": "high | medium | low",
    "confidence_notes": "..."
  },
  "quality_signals": {
    "version": "1.4",
    "total_chars": 2057,
    "total_words": 356,
    "total_pages": 1,
    "empty_pages": 2,
    "blank_pages": 1,
    "color_chart_pages": 1,
    "content_pages": 1,
    "input_images": 3,
    "page_types": ["content", "blank", "color_chart"],
    "chars_per_page": [2057, 0, 0],
    "chars_per_page_median": 2057.0,
    "marker_uncertain_count": 0,
    "marker_illegible_count": 0,
    "marker_density": 0.0,
    "dwr_score": 0.42,
    "duplicate_page_pairs": [],
    "language_expected": "de",
    "language_detected": "de",
    "language_match": true,
    "page_length_anomalies": [],
    "needs_review": false,
    "needs_review_reasons": []
  }
}
```

Optional nach Expert-Review (geschrieben von `import_reviews.py`):

```json
{
  "review": {
    "status": "approved",
    "edited_pages": [1],
    "reviewed_by": "Christopher Pollin",
    "reviewed_at": "2026-04-02T14:00:00Z"
  }
}
```

`page.type` ist ein First-Class-Feld auf jedem Page-Objekt (seit v1.3). Wird von `_classify_page()` in `quality_signals.py` gesetzt basierend auf Transkriptionslaenge (<10 Zeichen) und Notes-Keywords. Alle bestehenden JSONs sind backfilled via `backfill_page_types.py`. Downstream-Nutzung:
- `verify.py`: Blank/color_chart-Seiten werden bei CER-Berechnung uebersprungen (`"agreement": "skipped"`)
- `build_viewer_data.py`: `page.type` fliesst in Viewer-Daten, `blankPages`/`contentPages` im Katalog. Color-Chart-Seiten werden aus Viewer-Daten gefiltert. `reviewStatus` und `gtVerified` im catalog.json.
- Schema: `schemas/htr-interchange-v0.1.json` enthaelt `type` als optionales enum-Feld

## Technische Entscheidungen

- **Gemini 3.1 Flash Lite** als primaeres VLM (guenstig, schnell, multimodal). Claude Vision und GPT-4o als Vergleichskandidaten fuer Phase 4, aber noch nicht implementiert.
- **Kein Preprocessing** — Bilder gehen unveraendert an die API. Optimale Bildgroesse ist ein offener Punkt.
- **Alle Bilder an die API** — auch Leerseiten, weil Stefan Zweigs Schreibpraxis unregelmaessig ist (Verso-Seiten haben manchmal wichtige Notizen). Seitentyp-Klassifikation erfolgt post-hoc, nicht als Pre-Filter.
- **3-Ebenen-Verifikation** statt naiver Konfidenz:
  1. **Unsicherheits-Marker** (stark): Zaehlung von `[?]` und `[...]` im Transkriptionstext
  2. **VLM-Selbsteinschaetzung** (schwach): high/medium/low aus dem Gemini-Output — LLMs ueberschaetzen ihre Leistung
  3. **Textstatistik** (mittel): Zeichenzahl, Leerseiten, Zeichen/Seite als Plausibilitaets-Check
- **Diplomatische Transkription** — keine Normalisierung, keine Korrektur. Markup: `[?]` unsicher, `[...]` unleserlich, `~~...~~` durchgestrichen, `{...}` Einfuegung.
- **Bilder direkt von GAMS** im Viewer — kein lokaler Image-Store im Repo, GAMS-URLs als `<img src>`.
- **Multi-Model-Konsensus statt manuellem GT** — Zhang et al. 2025 (ICLR 2026): 3 Modelle + Judge skalierbarer als 30 Objekte manuell. Gemini Flash Lite (Modell A) + Gemini 3 Flash (Modell B), Claude als Judge fuer divergente Faelle.

## Verwandte Projekte

Methodische Referenzen — dort nach Patterns suchen, wenn die Pipeline erweitert wird:

- **[zbz-ocr-tei](https://github.com/DigitalHumanitiesCraft/zbz-ocr-tei)**: LLM-OCR für gedruckte Texte, Batch-Verarbeitung, Qualitätsscreening
- **[coOCR HTR](https://github.com/DigitalHumanitiesCraft/co-ocr-htr)**: Browser-HTR mit VLM + Expert-in-the-Loop-Validierung
- **[teiCrafter](https://github.com/DigitalHumanitiesCraft/teiCrafter)**: TEI-Annotation als nachgelagerte Pipeline-Stufe (relevant für Phase 5)
