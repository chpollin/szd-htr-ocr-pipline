# SZD-HTR-OCR-Pipeline

VLM-basierte Handschriften- und Texterkennung fuer den Stefan-Zweig-Nachlass am Literaturarchiv Salzburg. Die Pipeline erzeugt maschinenlesbaren Text aus 2.107 digitalisierten Faksimiles (Manuskripte, Korrespondenzen, Typoskripte, Lebensdokumente) mittels Googles Gemini 3.1 Flash Lite.

Teilprojekt von [Stefan Zweig Digital](https://stefanzweig.digital/). Die Transkriptionen fliessen in den Expert-in-the-Loop-Workflow des [DIA-XAI](https://github.com/chpollin/dia-xai)-Projekts (PLUS Early Career Grant).

**[Viewer & Katalog](https://chpollin.github.io/szd-htr-ocr-pipeline/)** — alle Transkriptionen mit Faksimile-Vergleich, Qualitaetssignalen und Suchfunktion.

## Ansatz

Die Pipeline kombiniert ein 4-schichtiges Prompt-System mit automatischer Qualitaetsbewertung:

1. **Kontext-Aufloesung** — TEI-XML-Metadaten liefern Titel, Sprache, Objekttyp. Daraus wird automatisch eine von 9 Prompt-Gruppen zugeordnet (Handschrift, Typoskript, Formular, Kurztext, Tabelle, Korrekturfahne, Konvolut, Zeitungsausschnitt, Korrespondenz).
2. **VLM-Transkription** — Alle Faksimile-Bilder + angepasster Prompt gehen an Gemini 3.1 Flash Lite. Grosse Objekte (>20 Bilder) werden automatisch in Chunks aufgeteilt.
3. **Quality Signals** — 7 automatische Signale (Seitentyp-Klassifikation, Marker-Dichte, Duplikaterkennung, Sprachkonsistenz u.a.) flaggen Objekte fuer manuelles Review.
4. **Verifikation** — Modellkonsensus (Flash Lite + Flash + Claude Judge) und Agent-basierte Pruefung gegen die Faksimile-Bilder.

Diplomatische Transkription ohne Normalisierung. Markup: `[?]` unsicher, `[...]` unleserlich, `~~...~~` durchgestrichen, `{...}` Einfuegung.

## Datengrundlage

2.107 digitalisierte Objekte mit 18.719 Faksimile-Scans (~23 GB), vollstaendig im lokalen Backup mit Metadaten.

| Sammlung | Objekte | Bilder | Bilder/Obj (Median) | TEI-Quelle |
|---|---|---|---|---|
| Lebensdokumente | 127 | 2.879 | 3 | [TEI](https://stefanzweig.digital/o:szd.lebensdokumente/TEI_SOURCE) |
| Werke (Manuskripte) | 169 | 7.842 | 21 | [TEI](https://stefanzweig.digital/o:szd.werke/TEI_SOURCE) |
| Aufsatzablage | 625 | 3.844 | 5 | [TEI](https://stefanzweig.digital/o:szd.aufsatzablage/TEI_SOURCE) |
| Korrespondenzen | 1.186 | 4.154 | 3 | Backup-Metadaten |

Sprachen: Deutsch (96%), Englisch, Franzoesisch, Italienisch, Spanisch. Bildformat: JPEG, ca. 4800 x 7200 px.

## Setup

Python 3.10+ (getestet mit 3.11). Benoetigt einen [Google AI API-Key](https://ai.google.dev/).

```bash
pip install -r requirements.txt
# .env anlegen mit: GOOGLE_API_KEY=AIza...
```

Die Faksimile-Bilder werden ueber GAMS (Geisteswissenschaftliches Asset Management System) der Uni Graz bezogen und muessen nicht lokal vorliegen.

## Nutzung

```bash
# Einzelnes Objekt transkribieren
python pipeline/transcribe.py o_szd.161 -c lebensdokumente

# Ganze Sammlung
python pipeline/transcribe.py -c lebensdokumente

# Alle Objekte
python pipeline/transcribe.py --all

# Vorschau ohne API-Calls
python pipeline/transcribe.py --all --dry-run

# Viewer-Daten aktualisieren
python pipeline/build_viewer_data.py

# Lokaler Dev-Server mit Review-API
python pipeline/serve.py
```

Ergebnisse landen als JSON in `results/{sammlung}/`. Dokumentation der Pipeline-Scripts: [`pipeline/README.md`](pipeline/README.md). Dokumentation der Ergebnis-Dateitypen: [`results/README.md`](results/README.md).

## Verwandte Projekte

- [zbz-ocr-tei](https://github.com/DigitalHumanitiesCraft/zbz-ocr-tei) — LLM-OCR-Pipeline fuer gedruckte Texte
- [coOCR HTR](https://github.com/DigitalHumanitiesCraft/co-ocr-htr) — Browser-basiertes HTR-Tool mit Expert-in-the-Loop
- [teiCrafter](https://github.com/DigitalHumanitiesCraft/teiCrafter) — TEI-Annotation als nachgelagerte Pipeline-Stufe (separates Repo)

## Lizenz

MIT
