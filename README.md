# SZD-HTR-OCR-Pipeline

Textextraktion aus digitalisierten Nachlassfaksimiles des Stefan-Zweig-Nachlasses (Literaturarchiv Salzburg). Teilprojekt von [Stefan Zweig Digital](https://stefanzweig.digital/).

## Ziel

Aufbau einer VLM-basierten HTR/OCR-Pipeline, die aus den digitalisierten Faksimiles des Zweig-Nachlasses maschinenlesbaren Text erzeugt. Die Transkriptionsergebnisse dienen als Bewertungsgrundlage für den Expert-in-the-Loop-Workflow im [DIA-XAI](https://github.com/chpollin/dia-xai)-Projekt.

## Datengrundlage

- **143 Lebensdokumente** aus dem Nachlass, beschrieben in TEI-XML ([Quelle](https://stefanzweig.digital/o:szd.lebensdokumente/TEI_SOURCE))
- 10 Klassifikationen: Verlagsverträge (61), Rechtsdokumente (21), Diverses (14), Büromaterialien (13), Tagebücher (12), Verzeichnisse (9), Kalender (6), Finanzen (4), u.a.
- Sprachen: Deutsch (86), Englisch (23), Französisch (13), Italienisch (2), Spanisch (2)

## Pipeline-Architektur

Dreischichtiges Prompt-System für VLM-Transkription:

| Schicht | Funktion |
|---|---|
| **System-Prompt** | Rolle, Regeln, Output-Format (für alle Objekte gleich) |
| **Gruppen-Prompt** | Typspezifische Anweisungen (A–E, s.u.) |
| **Objekt-Kontext** | Metadaten aus TEI-XML (Sprache, Hand, Instrument, Typ) |

### Prototyp-Gruppen

| Gruppe | Objekte | Hauptmerkmal |
|---|---|---|
| A: Handschrift | Tagebücher, Notizbücher (12) | Zweigs Handschrift, Kurrent |
| B: Maschinenschrift | Typoskripte, Durchschläge (74) | Formaler Text, mehrsprachig |
| C: Formulare | Rechtsdokumente, Finanzen (25) | Druck + Handschrift gemischt |
| D: Kurztexte | Diverses, Büromaterialien (27) | Wenig Text, heterogen |
| E: Tabellarisch | Verzeichnisse, Kalender (16) | Listen, Register |

## Erste Testergebnisse

Getestet mit **Gemini 3.1 Flash Lite** (Preview). Ergebnisse unter [docs/](https://chpollin.github.io/szd-htr-ocr-pipline/).

| Objekt | Gruppe | Sprache | Confidence | Ergebnis |
|---|---|---|---|---|
| Theaterkarte Jeremias 1918 | D: Kurztext | DE | high | Gedruckter + handschriftlicher Text korrekt |
| Certified Copy of Marriage | C: Formular | EN | high | Alle Formularfelder korrekt erfasst |
| Verlagsvertrag Grasset | B: Typoskript | FR | high | Vollständiger franz. Vertragstext, Durchstreichungen erkannt |
| Tagebuch 1918 (5 Seiten) | A: Handschrift | DE | high | Zweigs Handschrift flüssig gelesen |

## Projektstruktur

```
├── pipeline/
│   ├── prompts/           ← Dreischichtiges Prompt-System
│   │   ├── system.md
│   │   ├── group_a–e_*.md
│   │   └── context_template.md
│   └── test_single.py    ← Test-Script für Einzelobjekte
├── data/
│   └── szd_lebensdokumente_tei.xml  ← TEI-Metadaten (143 Objekte)
├── results/test/          ← Transkriptionsergebnisse (JSON)
├── knowledge/             ← Research-Vault
│   ├── data.md            ← Datenanalyse
│   └── Journal.md
└── docs/                  ← GitHub Pages
```

## Setup

```bash
pip install google-generativeai pillow python-dotenv
export GOOGLE_API_KEY=...
python pipeline/test_single.py theaterkarte
```

## Verwandte Projekte

- [zbz-ocr-tei](https://github.com/DigitalHumanitiesCraft/zbz-ocr-tei) — LLM-OCR-Pipeline für gedruckte Texte
- [coOCR HTR](https://github.com/DigitalHumanitiesCraft/co-ocr-htr) — Browser-basiertes HTR-Tool mit Expert-in-the-Loop
- [teiCrafter](https://github.com/DigitalHumanitiesCraft/teiCrafter) — TEI-Annotation nach Transkription

## Lizenz

MIT
