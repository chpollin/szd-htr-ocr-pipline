# SZD-HTR — Textextraktion aus digitalisierten Nachlassfaksimiles

## Projektziel

VLM-basierte HTR/OCR-Pipeline für den Stefan-Zweig-Nachlass (Literaturarchiv Salzburg). Erzeugt maschinenlesbaren Text aus digitalisierten Faksimiles. Teilprojekt von [Stefan Zweig Digital](https://stefanzweig.digital/), liefert Textdaten für den Expert-in-the-Loop-Workflow im [DIA-XAI](https://github.com/chpollin/dia-xai)-Projekt (PLUS Early Career Grant, ab Mai 2026).

- GitHub: https://github.com/chpollin/szd-htr-ocr-pipeline
- Python 3.10+ (getestet mit 3.11)
- Lizenz: MIT

## Aktueller Stand

Phasen 1–3 erledigt. Details und offene Aufgaben → `Plan.md` (einzige Wahrheitsquelle für Phasen-Status).

- **~61 Objekte** transkribiert: 7 Test (`results/test/`), 42 Lebensdokumente, 11 Werke, 1 Aufsatzablage
- **Alle 9 Prompt-Gruppen** (A–I) haben mindestens ein Testobjekt — inkl. Gruppe G (Konvolut)
- **~2107 Objekte** im Backup ueber 4 Sammlungen — gezieltes Sample (~74 Objekte, 10/Gruppe) in Arbeit
- **Verifikationskonzept** fertig: Ground-Truth-Design, quality_signals-Spezifikation, Cross-Model-Verification, Literatur-Review (6 Papers)
- **TEI-Integration spezifiziert**: Interchange-Format (JSON Schema v0.1), teiCrafter-Integration (3 Mapping-Templates), TEI-Zielstruktur (DTABf-Profil)
- **Empirische Befunde**: quality_signals zu aggressiv (63% flagged), marker_density funktionslos (2/57k Zeichen), Prompt-Vorsichts-Guidance wird ignoriert
- Naechster Schritt: **Pilot** (5 Seiten manuell pruefen), dann Ground-Truth-Sample (31 Objekte), dann Phase 4

## Quelldaten

Lokales Backup unter `SZD_BACKUP_ROOT` (Default: `C:/Users/Chrisi/Documents/PROJECTS/szd-backup/data/`):

| Unterverzeichnis | Sammlung (intern) | Objekte im Backup | TEI-Datei |
|---|---|---|---|
| `lebensdokumente/` | `lebensdokumente` | ~127 | `szd_lebensdokumente_tei.xml` |
| `korrespondenzen/` | `korrespondenzen` | ~1186 | `szd_korrespondenzen_tei.xml` |
| `aufsatz/` | `aufsatzablage` | ~625 | `szd_aufsatzablage_tei.xml` |
| `facsimiles/` | `werke` | ~169 | `szd_werke_tei.xml` |

Jedes Objekt: `o_szd.{nr}/metadata.json` + `o_szd.{nr}/images/IMG_*.jpg` (ca. 4912x7360px). TEI-XML enthält mehr Objekte als im Backup vorhanden sind.

## Pipeline-Architektur

```
Faksimile (JPG) → Gemini Vision API → JSON (Transkription pro Seite + Konfidenz)
```

### Dreischichtiges Prompt-System

1. **System-Prompt** (`prompts/system.md`): Rolle, diplomatische Transkriptionsregeln, JSON-Output-Format
2. **Gruppen-Prompt** (`prompts/group_*.md`): Spezifische Anweisungen pro Dokumenttyp (9 Gruppen)
3. **Objekt-Kontext** (automatisch aus TEI-XML via `tei_context.py`): Titel, Signatur, Datum, Sprache, Objekttyp etc.

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
├── Plan.md                          ← Phasen-Status (1–6), einzige Wahrheitsquelle
├── Lane.md                          ← Lane-Koordination (Aufträge, Status, Abhängigkeiten)
├── requirements.txt                 ← google-genai, python-dotenv
├── .env                             ← API Keys (nicht committet)
├── pipeline/
│   ├── config.py                    ← Pfade, API-Key, Sammlungs-Mapping, Konstanten
│   ├── transcribe.py                ← Batch-CLI: Einzel-/Sammlungs-/Gesamtmodus
│   ├── test_single.py               ← Testskript mit 7 hardcodierten Testobjekten
│   ├── tei_context.py               ← TEI-Parser, resolve_group(), format_context()
│   ├── build_viewer_data.py         ← Baut 5 Dateien: catalog.json + 4× data/{collection}.json
│   └── prompts/                     ← System-Prompt + 9 Gruppen-Prompts (Markdown)
├── data/                            ← TEI-XML-Metadaten (4 Sammlungen)
├── results/
│   ├── test/                        ← 7 Testergebnisse (enriched JSON)
│   ├── lebensdokumente/             ← 7 Batch-Ergebnisse
│   ├── aufsatzablage/               ← 2 Ergebnisse (Zeitungsausschnitte)
│   └── werke/                       ← 2 Ergebnisse (Korrekturfahne, Konvolut)
├── docs/
│   ├── index.html                   ← Single-Page-App: Katalog + Viewer (GitHub Pages)
│   ├── app.css                      ← SZD-Design-System (Burgundy/Gold, Source Serif)
│   ├── app.js                       ← Routing, Katalog, Viewer, Edit, Export
│   ├── catalog.json                 ← Leichtgewichtige Metadaten für Katalog-Tabelle
│   └── data/                        ← Transkriptionsdaten pro Sammlung (on-demand)
│       ├── lebensdokumente.json
│       ├── werke.json
│       ├── aufsatzablage.json
│       └── korrespondenzen.json
└── knowledge/                       ← Research Vault (Methodik, Datenanalyse, Journal)
    ├── index.md                     ← Map of Content (MOC)
    ├── data-overview.md             ← Konsolidierte TEI-Analyse aller Sammlungen
    ├── verification-concept.md      ← GT-Sample, quality_signals, Cross-Model, Literatur
    ├── annotation-protocol.md       ← Transkriptionskonventionen fuer Referenz-Sample
    ├── pilot-design.md              ← 5-Seiten-Pilot vor vollem GT-Sample
    ├── htr-interchange-format.md    ← JSON-Schema: szd-htr → teiCrafter
    ├── tei-target-structure.md      ← TEI-Zielformat (DTABf-Profil, Markup→TEI-Mapping)
    ├── teiCrafter-integration.md    ← teiCrafter-Integration (JSON-Import, Mapping-Templates)
    └── journal.md                   ← Chronologisches Session-Log
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
```

Ergebnisse landen in `results/{collection}/{object_id}_{model}.json`. Bereits transkribierte Objekte werden übersprungen (außer `--force`).

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
      {"page": 1, "transcription": "...", "notes": "..."}
    ],
    "confidence": "high | medium | low",
    "confidence_notes": "..."
  }
}
```

## Technische Entscheidungen

- **Gemini 3.1 Flash Lite** als primäres VLM (günstig, schnell, multimodal). Claude Vision und GPT-4o als Vergleichskandidaten für Phase 4, aber noch nicht implementiert.
- **Kein Preprocessing** — Bilder gehen unverändert an die API. Optimale Bildgröße ist ein offener Punkt.
- **3-Ebenen-Verifikation** statt naiver Konfidenz:
  1. **Unsicherheits-Marker** (stark): Zählung von `[?]` und `[...]` im Transkriptionstext
  2. **VLM-Selbsteinschätzung** (schwach): high/medium/low aus dem Gemini-Output — LLMs überschätzen ihre Leistung
  3. **Textstatistik** (mittel): Zeichenzahl, Leerseiten, Zeichen/Seite als Plausibilitäts-Check
- **Diplomatische Transkription** — keine Normalisierung, keine Korrektur. Markup: `[?]` unsicher, `[...]` unleserlich, `~~...~~` durchgestrichen, `{...}` Einfügung.
- **Bilder direkt von GAMS** im Viewer — kein lokaler Image-Store im Repo, GAMS-URLs als `<img src>`.

## Verwandte Projekte

Methodische Referenzen — dort nach Patterns suchen, wenn die Pipeline erweitert wird:

- **[zbz-ocr-tei](https://github.com/DigitalHumanitiesCraft/zbz-ocr-tei)**: LLM-OCR für gedruckte Texte, Batch-Verarbeitung, Qualitätsscreening
- **[coOCR HTR](https://github.com/DigitalHumanitiesCraft/co-ocr-htr)**: Browser-HTR mit VLM + Expert-in-the-Loop-Validierung
- **[teiCrafter](https://github.com/DigitalHumanitiesCraft/teiCrafter)**: TEI-Annotation als nachgelagerte Pipeline-Stufe (relevant für Phase 5)
