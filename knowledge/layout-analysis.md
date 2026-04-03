---
title: "Layout-Analyse"
created: 2026-04-02
updated: 2026-04-02
type: spec
status: stable
---

# Layout-Analyse und PAGE XML Export

Dokumentiert den VLM-basierten Layout-Analyse-Ansatz und die PAGE XML-Erzeugung fuer das SZD-HTR-Projekt.

## 1. Motivation

Die HTR-Pipeline (`transcribe.py`) erzeugt seitenweisen Fliesstext ohne Strukturinformation. Fuer zwei nachgelagerte Ziele wird jedoch strukturiertes Layout benoetigt:

1. **Strukturierte Ausgabe:** Braucht `heading`, `paragraph`, `list`, `table` — also die Unterscheidung zwischen Ueberschriften, Absaetzen, Listen und Tabellen.
2. **DIA-XAI Expert-in-the-Loop:** Braucht raeumliche Verortung von Textregionen auf dem Faksimile fuer die visuelle Validierung (Bild↔Text-Sync).

PAGE XML (PRImA Lab, 2019) ist der etablierte Standard fuer Dokumentlayout-Daten und wird von Transkribus, OCR-D und Larex unterstuetzt.

### 1.1 Bisherige Abgrenzung

Das [[htr-interchange-format]] (Page-JSON) loest dieses Problem durch progressive Anreicherung: Das Format funktioniert ohne Koordinaten (nur Text), kann aber Layout-Regionen nachtraeglich aufnehmen. Ein **separater Layout-Analyse-Schritt** erzeugt die fehlenden Koordinaten und fuegt sie als `regions[]` in das bestehende Page-JSON ein.

## 2. Ansatz: VLM-basierte Layout-Analyse

### 2.1 Entscheidung

| Option | Bewertung | Gewaehlt |
|---|---|---|
| **VLM-only (Gemini Flash Lite)** | Keine neue Dependency, nutzt bestehende Infrastruktur, approximierte Koordinaten (~80%) | **Ja** |
| Hybrid (VLM + DocTR/LayoutParser) | Genauere Koordinaten, aber neue Dependency (torch), komplexes Alignment | Nein (Phase 2 moeglich) |
| Heuristisch (synthetische Koordinaten) | Schnell, aber Koordinaten nicht bildbasiert | Nein |

**Begruendung:** Das Projekt arbeitet bereits mit der Gemini API. Ein zusaetzlicher VLM-Call pro Seite ist kostenguenstig und erfordert keine neue Infrastruktur. Die approximierten Koordinaten reichen fuer den TEI-Export und die visuelle Verortung — pixelgenaue Segmentierung ist nicht erforderlich.

### 2.2 Kern-Prinzip

Layout-Analyse ist ein **separater Pipeline-Schritt** nach der Transkription:

```
transcribe.py          layout_analysis.py         export_pagexml.py
  (VLM-Call 1)            (VLM-Call 2)              (deterministisch)
  → OCR-Text              → Regionen + Bbox         → PAGE XML
  → *_gemini-*.json       → *_layout.json           → *_page/page_NNN.xml
```

Die PAGE XML-Erzeugung (`export_pagexml.py`) ist rein deterministisch — sie merged die zwei JSON-Dateien ohne API-Aufruf.

## 3. Strukturelemente (Kern-Set)

Fuenf Regionentypen, abgestimmt auf den Stefan-Zweig-Nachlass:

| Typ | PAGE XML type | Beschreibung | Typische Dokumente |
|---|---|---|---|
| `paragraph` | paragraph | Fliesstext-Absatz | Alle Gruppen |
| `heading` | heading | Ueberschrift, Titel, Datumzeile, Anrede | Briefe (I), Werke (A), Formulare (C) |
| `list` | list-label | Aufzaehlung, nummerierte Liste | Vertraege, Register |
| `table` | other | Tabelle, tabellarische Struktur | Register (E), Kontorbuecher |
| `marginalia` | marginalia | Randnotiz, Annotation | Manuskripte (A), Korrekturfahnen (F) |

Erweiterung (Phase 2): Seitenzahl (`page-number`), Briefkopf (`letterhead`), Stempel (`stamp`), Kolumnentitel (`running-header`), Spalten (`column`).

## 4. Koordinatensystem

**Prozent der Seitengroesse (0-100):** Aufloesungsunabhaengig, da die Originalbilder unterschiedliche Dimensionen haben (~4912x7360, aber nicht einheitlich).

```
bbox: [x%, y%, breite%, hoehe%]

Beispiel: [12, 3, 76, 5]
→ Region beginnt bei 12% vom linken Rand, 3% vom oberen Rand
→ Ist 76% der Seitenbreite breit und 5% der Seitenhoehe hoch
```

**Konversion zu Pixeln:** `export_pagexml.py` rechnet automatisch um:
```
x_px = x% / 100 * image_width
y_px = y% / 100 * image_height
```

**Konversion zu PAGE XML Polygon:**
```xml
<Coords points="x1,y1 x2,y1 x2,y2 x1,y2"/>
```
Vier Eckpunkte (Rechteck), kein echtes Polygon — ausreichend fuer VLM-approximierte Regionen.

### 4.1 Koordinaten-Qualitaet

Das VLM liefert Schaetzungen, keine pixelgenauen Segmentierungen. Beobachtungen aus ersten Tests (o_szd.100, Typoskript):

- **Strukturerkennung:** Sehr gut — 15 Regionen korrekt identifiziert (Heading, Paragraph, List, Unterschriftenfelder)
- **Positionsgenauigkeit:** Mittel — relative Positionen stimmen (oben/unten, links/rechts), absolute Werte weichen ab
- **Groessengenauigkeit:** Mittel — Regionen-Proportionen plausibel, aber nicht pixelgenau

Fuer den TEI-Export reicht diese Genauigkeit, da dort nur die **logische Struktur** (welcher Text ist heading vs. paragraph) relevant ist, nicht die exakte Position. Fuer eine zeilensynoptische Ansicht (Bild↔Text-Sync) waere hoehere Genauigkeit wuenschenswert → Phase 2 mit CV-Modell.

## 5. Output-Formate

### 5.1 Layout JSON (`*_layout.json`)

```json
{
  "object_id": "o_szd.100",
  "collection": "lebensdokumente",
  "model": "gemini-3.1-flash-lite-preview",
  "pages": [
    {
      "page": 1,
      "image_filename": "IMG_1.jpg",
      "image_width_px": 4912,
      "image_height_px": 7360,
      "regions": [
        {
          "id": "r1",
          "type": "heading",
          "bbox": [12, 3, 76, 5],
          "reading_order": 1,
          "lines": 1,
          "label": "Vertragstitel"
        }
      ]
    }
  ]
}
```

Schema: `schemas/layout-regions-v0.1.json`

### 5.2 PAGE XML (`*_page/page_NNN.xml`)

PAGE XML 2019 (Namespace: `http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15`) mit:

- `<Page>` mit `imageFilename`, `imageWidth`, `imageHeight`
- `<ReadingOrder>` mit `<OrderedGroup>` und `<RegionRefIndexed>`
- `<TextRegion>` pro Region mit `type`-Attribut und `custom`-Attribut (Strukturtyp + Label)
- `<Coords>` als Rechteck-Polygon (4 Punkte, aus bbox konvertiert)
- `<TextEquiv><Unicode>` mit dem zugewiesenen OCR-Text

### 5.3 Text-Alignment (OCR → Regionen)

Der OCR-Text wird proportional auf die Layout-Regionen verteilt:

1. Sortiere Regionen nach `reading_order`
2. Splitte OCR-Text an Zeilenumbruechen
3. Verteile Zeilen proportional nach geschaetzter Zeilenzahl (`lines`) der Region
4. Rest-Zeilen gehen an die letzte Region

Das ist eine Heuristik — kein token-basiertes Alignment. Fuer die meisten Dokumente (linearer Lesefluss) funktioniert das gut. Bei komplexen Layouts (Spalten, Marginalien die im OCR-Text eingestreut sind) kann die Zuordnung fehlerhaft sein.

## 6. Pipeline-Integration

### 6.1 Dateien

| Datei | Typ | Beschreibung |
|---|---|---|
| `pipeline/layout_analysis.py` | Modul + CLI | VLM-basierte Layout-Analyse (1 API-Call/Seite) |
| `pipeline/export_pagexml.py` | Modul + CLI | Deterministischer PAGE XML Export |
| `pipeline/prompts/layout_system.md` | Prompt | System-Prompt fuer Layout-Analyse |
| `schemas/layout-regions-v0.1.json` | Schema | JSON-Schema fuer Layout-Output |

### 6.2 CLI-Nutzung

```bash
# Layout analysieren
python pipeline/layout_analysis.py o_szd.100 -c lebensdokumente
python pipeline/layout_analysis.py -c korrespondenzen --limit 10

# PAGE XML exportieren (braucht OCR + Layout)
python pipeline/export_pagexml.py o_szd.100 -c lebensdokumente
python pipeline/export_pagexml.py -c lebensdokumente
```

### 6.3 Platz in der Gesamtpipeline

```
Phase 3: Transkription
  transcribe.py → *_gemini-*.json (OCR-Text)

Phase 3b: Layout-Analyse (NEU)
  layout_analysis.py → *_layout.json (Regionen + Bbox)

Phase 3c: PAGE XML Export (NEU)
  export_pagexml.py → *_page/page_NNN.xml (merged)

Phase 4: Verifikation
  verify.py → *_consensus.json (Modellkonsensus)

Phase 5: Export
  export_page_json.py → Page-JSON
```

## 7. Offene Punkte

1. **Koordinaten-Verbesserung (Phase 2):** CV-Modell (DocTR, LayoutParser) fuer pixelgenaue Segmentierung. Voraussetzung: Evaluation der aktuellen VLM-Koordinaten auf einem Testset.
2. **TextLine-Ebene:** Aktuell nur TextRegion-Level. PAGE XML unterstuetzt auch `<TextLine>` und `<Word>` — dafuer braeuchte man feinere Segmentierung.
3. **Erweitertes Regionenset:** Seitenzahlen, Briefkoepfe, Stempel — relevant fuer Korrespondenzen und Formulare.
4. **Alignment-Verbesserung:** Token-basiertes Alignment statt zeilenproportionaler Heuristik — relevant fuer Dokumente mit Marginalien oder Spalten.
5. **Batch-Lauf:** Bisher nur Einzeltest auf o_szd.100. Stratifizierter Test (1 Objekt pro Gruppe) empfohlen.
6. **Validierung:** PAGE XML gegen das PRImA-Schema validieren (xsd). Visuell in Transkribus pruefen.

## 8. Referenzen

- PRImA PAGE XML 2019: https://www.primaresearch.org/schema/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd
- Pletschacher & Antonacopoulos (2010): The PAGE (Page Analysis and Ground-truth Elements) Format Framework
- [[htr-interchange-format]] — Page-JSON: Text + Layout + Metadaten in einem Format
