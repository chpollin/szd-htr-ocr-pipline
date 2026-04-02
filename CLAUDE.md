# SZD-HTR — Textextraktion aus digitalisierten Nachlassfaksimiles

## Projektziel

VLM-basierte HTR/OCR-Pipeline für den Stefan-Zweig-Nachlass (Literaturarchiv Salzburg). Erzeugt maschinenlesbaren Text aus digitalisierten Faksimiles. Teilprojekt von [Stefan Zweig Digital](https://stefanzweig.digital/), liefert Textdaten für den Expert-in-the-Loop-Workflow im [DIA-XAI](https://github.com/chpollin/dia-xai)-Projekt (PLUS Early Career Grant, ab Mai 2026).

- GitHub: https://github.com/chpollin/szd-htr-ocr-pipeline
- Python 3.10+ (getestet mit 3.11)
- Lizenz: MIT

## Aktueller Stand

Phasen 1–3 erledigt, Phase 4 laufend. Aktuelle Zahlen → `python pipeline/build_viewer_data.py` oder `docs/catalog.json`. Offene Aufgaben und Entscheidungslog → `Plan.md`. Session-Log → `knowledge/journal.md`. CER-Baseline und Fehlermuster → `knowledge/evaluation-results.md`.

### 4-Tier Review-Modell

| Tier | Status im JSON | Vertrauensniveau | Quelle |
|---|---|---|---|
| 0 | `gt_verified` | Hoechstes | Mensch auf 3-Modell-GT-Draft |
| 1 | `approved` | Hoch | Mensch im Frontend-Viewer |
| 2 | `agent_verified` | Mittel-hoch | Claude Code Sub-Agent (Vision) |
| 3 | kein Review | Niedrig | Nur Pipeline-Selbsteinschaetzung |

### Bekannte Schwaechen

- **Kurrent-Handschrift**: 90–95% Genauigkeit (vs. 99%+ bei Druck). Typische Verwechslungen: h↔I, n↔u, r↔v, L↔B, St↔H, f↔s
- **Nonsens-Halluzination**: Gemini erfindet Woerter statt `[?]` zu setzen — `marker_density` daher als Signal wertlos
- **`duplicate_pages` False-Positive**: Triggert bei Color-Chart-Doppelfotografie (offener Fix)
- **Tabellarische Layouts**: VLM-Linearisierung ordnet Betraege falschen Zeilen zu (~90% Genauigkeit)

## Quelldaten

Lokales Backup unter `SZD_BACKUP_ROOT` (Default: `C:/Users/Chrisi/Documents/PROJECTS/szd-backup/data/`). 4 Sammlungen, Mapping in `config.py` (`COLLECTIONS`):

| Unterverzeichnis | Sammlung (intern) | TEI-Datei |
|---|---|---|
| `lebensdokumente/` | `lebensdokumente` | `szd_lebensdokumente_tei.xml` |
| `korrespondenzen/` | `korrespondenzen` | `szd_korrespondenzen_tei.xml` |
| `aufsatz/` | `aufsatzablage` | `szd_aufsatzablage_tei.xml` |
| `facsimiles/` | `werke` | `szd_werke_tei.xml` |

Jedes Objekt: `o_szd.{nr}/metadata.json` + `o_szd.{nr}/mets.xml` + `o_szd.{nr}/images/IMG_*.jpg`. Objektzahlen und Abdeckung → `python pipeline/transcribe.py --all --dry-run` bzw. `docs/catalog.json`.

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
   Modellkonsensus  VLM-Layout (1/Seite) → catalog.json
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
│   ├── page-json-v0.1.json          ← Page-JSON Schema (Text + Layout + Metadaten)
│   └── layout-regions-v0.1.json     ← JSON-Schema fuer Layout-Analyse-Output (Legacy)
├── pipeline/
│   ├── config.py                    ← Pfade, API-Key, Sammlungs-Mapping, Konstanten
│   ├── transcribe.py                ← Batch-CLI: Einzel-/Sammlungs-/Gesamtmodus
│   ├── quality_signals.py           ← 8 Signale + page.type + DWR (v1.4)
│   ├── verify.py                    ← Modellkonsensus (Flash Lite + Flash + Claude Judge)
│   ├── evaluate.py                  ← CER/WER-Berechnung + normalize_for_consensus
│   ├── quality_report.py            ← Aggregierte Qualitaetsstatistiken ueber alle Ergebnisse
│   ├── backfill_page_types.py       ← Backfill: page.type auf bestehende JSONs stempeln
│   ├── run_sample_batch.py          ← Gezielter Batch: fuellt jede Gruppe auf 10 auf
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
│   ├── groundtruth/                 ← GT-Drafts + Pro-Transkriptionen
│   ├── lebensdokumente/             ← Ergebnisse + Modellkonsensus-JSONs
│   ├── werke/
│   ├── aufsatzablage/
│   └── korrespondenzen/
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
    ├── verification-concept.md      ← GT, quality_signals, Cross-Model, VbV, Agent-Verifikation (§8)
    ├── evaluation-results.md        ← CER-Baseline, Fehlertypologie
    ├── annotation-protocol.md       ← Transkriptionskonventionen
    ├── htr-interchange-format.md    ← Page-JSON: Text + Layout + Metadaten
    ├── tei-target-structure.md      ← TEI-Zielformat (DTABf-Profil)
    ├── teiCrafter-integration.md    ← teiCrafter-Integration
    ├── layout-analysis.md           ← Layout-Analyse + PAGE XML Export
    ├── dia-xai-integration.md       ← DIA-XAI-Integration
    └── journal.md                   ← Session-Log
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

Jedes Ergebnis in `results/{collection}/{object_id}_{model}.json`:

```json
{
  "object_id": "o_szd.100",
  "collection": "lebensdokumente",
  "group": "typoskript",
  "model": "gemini-3.1-flash-lite-preview",
  "metadata": { "title": "...", "language": "...", "images": ["https://gams.uni-graz.at/..."] },
  "context": "## Dieses Dokument\n- Titel: ...",
  "result": {
    "pages": [
      {"page": 1, "transcription": "...", "notes": "...", "type": "content"},
      {"page": 2, "transcription": "", "notes": "Rueckseite, leer.", "type": "blank"}
    ],
    "confidence": "high | medium | low"
  },
  "quality_signals": { "version": "1.4", "needs_review": false, "..." : "..." },
  "review": { "status": "approved | agent_verified", "..." : "..." }
}
```

- `page.type`: `content` / `blank` / `color_chart` — gesetzt von `quality_signals.py`, Schema in `schemas/page-json-v0.1.json`
- `quality_signals`: 8 Signale + DWR, Details in `quality_signals.py` und `verification-concept.md` §2
- `review`: Optional, geschrieben von `serve.py` (API), `import_reviews.py` (CLI) oder Agent-Verifikation

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
- **Modellkonsensus statt manuellem GT** — Zhang et al. 2025 (ICLR 2026): 3 Modelle + Judge skalierbarer als 30 Objekte manuell. Gemini Flash Lite (Modell A) + Gemini 3 Flash (Modell B), Claude als Judge fuer divergente Faelle.

## Verwandte Projekte

Methodische Referenzen — dort nach Patterns suchen, wenn die Pipeline erweitert wird:

- **[zbz-ocr-tei](https://github.com/DigitalHumanitiesCraft/zbz-ocr-tei)**: LLM-OCR für gedruckte Texte, Batch-Verarbeitung, Qualitätsscreening
- **[coOCR HTR](https://github.com/DigitalHumanitiesCraft/co-ocr-htr)**: Browser-HTR mit VLM + Expert-in-the-Loop-Validierung
- **[teiCrafter](https://github.com/DigitalHumanitiesCraft/teiCrafter)**: TEI-Annotation als nachgelagerte Pipeline-Stufe (relevant für Phase 5)
