---
title: "Page-JSON Format"
aliases: ["Page-JSON", "Interchange-Format", "HTR Interchange Format"]
created: 2026-04-01
updated: 2026-04-03
type: spec
status: draft
related:
  - "[[verification-concept]]"
  - "[[data-overview]]"
  - "[[layout-analysis]]"
---

# Page-JSON — Spezifikation

Version: 0.2 (Entwurf)

---

## 1. Zweck

Page-JSON ist das **interne Arbeitsformat** der Pipeline: ein JSON-Format fuer VLM-basierte HTR/OCR-Ergebnisse, das Text, Layout und deskriptive Metadaten in einer Datei vereint. Das **Archiv- und Austauschformat** ist METS/MODS + PAGE XML (→ [[page-xml-mets-architecture]]). Page-JSON wird zuerst erzeugt, METS/MODS daraus abgeleitet.

### 1.1 Designprinzipien

1. **JSON-Serialisierung des PAGE-XML-Datenmodells:** Dokument → Seiten → Regionen → Text. Dieselbe Hierarchie, aber als JSON statt XML.
2. **Progressive Anreicherung:** Funktioniert ohne Layout-Daten (nur Text). Regionen koennen nachtraeglich hinzugefuegt werden (via `layout_analysis.py`).
3. **Bidirektionale PAGE-XML-Konvertierung:** Deterministisch und verlustfrei in beide Richtungen konvertierbar (§6).
4. **Provenienz-transparent:** Welches Modell, welcher Prompt, wann? Reproduzierbarkeit.
5. **Projektunabhaengig:** Keine SZD-spezifischen Felder auf Top-Level. Projektdaten gehoeren in `source.additional`.

### 1.2 Warum nicht PAGE XML direkt?

| Eigenschaft | PAGE XML | Page-JSON |
|---|---|---|
| Koordinaten erforderlich | Ja (Pflicht, Schema-Verletzung ohne) | Nein (`regions` optional) |
| Metadaten-Felder | Minimal (Creator, Created) | Vollstaendig (Sprache, Dokumenttyp, Signatur, Provenienz) |
| Maschinenlesbar in JS | XML-Parser noetig | Nativ (`JSON.parse()`) |
| VLM-Output-kompatibel | Nein (VLMs liefern Fliesstext) | Ja (Text-only oder Text+Layout) |
| Dateigrösse | ~3x JSON | Baseline |
| Konvertierung zu PAGE XML | — | Deterministisch (§6) |
| Interoperabilitaet | Transkribus, eScriptorium, Larex | Via PAGE-XML-Export |

PAGE XML bleibt als Export-Format fuer Tools, die es erwarten (`export_pagexml.py`). Page-JSON ist das Arbeitsformat der Pipeline.

### 1.3 Vorgaenger

Dieses Format ersetzt das "HTR Interchange Format" (v0.1, April 2026), das Text und Layout getrennt hielt und nie als Code implementiert wurde. Page-JSON fuehrt die drei bisher getrennten Dateien (Pipeline-JSON, Layout-JSON, PAGE XML) konzeptionell zusammen.

---

## 2. Datenmodell

```
Page-JSON
├── source            Metadaten zum Quelldokument
├── provenance        Wie und wann erzeugt (Modell, Pipeline, Parameter)
├── pages[]           Seitenarray
│   ├── page          Seitennummer (1-basiert)
│   ├── image         Bildverweis (Dateiname oder URI)
│   ├── image_width   Bildbreite in Pixel (wenn regions vorhanden)
│   ├── image_height  Bildhoehe in Pixel (wenn regions vorhanden)
│   ├── type          content | blank | color_chart
│   ├── text          Volltext der Seite (immer vorhanden)
│   ├── notes         Beobachtungen des Modells
│   └── regions[]     Layout-Regionen (optional)
│       ├── id        Region-ID (r1, r2, ...)
│       ├── type      paragraph | heading | list | table | marginalia
│       ├── bbox      Bounding Box [x%, y%, w%, h%] (0-100)
│       ├── reading_order  Lesereihenfolge (1, 2, 3, ...)
│       ├── text      Text innerhalb dieser Region
│       ├── lines     Geschaetzte Zeilenanzahl
│       └── label     Kurzbeschreibung
├── confidence        high | medium | low (Modell-Selbsteinschaetzung)
├── confidence_notes  Begruendung
├── quality           Automatische Qualitaetssignale (optional)
└── evaluation        CER/WER gegen Ground Truth (optional)
```

### 2.1 Zwei Zustaende

**Zustand 1 — Nur Text** (nach `transcribe.py`):
Jede Seite hat `text`, `type`, `notes`. Keine `regions`. Ausreichend fuer Viewer und Export.

**Zustand 2 — Text + Layout** (nach `layout_analysis.py`):
Zusaetzlich `regions[]` mit Bounding Boxes, Regionstypen und regionsbezogenem Text. Ermoeglicht PAGE-XML-Export und DIA-XAI-Visualisierung.

---

## 3. JSON Schema

Das Schema ist als eigenstaendige, validierbare Datei verfuegbar: [`schemas/page-json-v0.1.json`](../schemas/page-json-v0.1.json)

```json
{
  "page_json": "0.1",

  "source": {
    "id": "o_szd.100",
    "title": "Agreement Longmans, Green & Co. Inc.",
    "language": "en",
    "date": "1938-09-12",
    "document_type": "typescript",
    "collection": "lebensdokumente",
    "repository": "Literaturarchiv Salzburg",
    "shelfmark": "SZ-AAP/L13.23",
    "images": [
      "https://gams.uni-graz.at/o:szd.100/IMG.1",
      "https://gams.uni-graz.at/o:szd.100/IMG.2",
      "https://gams.uni-graz.at/o:szd.100/IMG.3"
    ]
  },

  "provenance": {
    "model": "gemini-3.1-flash-lite-preview",
    "provider": "google",
    "created_at": "2026-04-01T14:30:00Z",
    "pipeline": "szd-htr 0.4",
    "prompt_layers": ["system", "group_b_typoskript", "object_context"],
    "layout_model": "gemini-3.1-flash-lite-preview"
  },

  "pages": [
    {
      "page": 1,
      "image": "IMG_1.jpg",
      "image_width": 4912,
      "image_height": 7360,
      "type": "content",
      "text": "THIS AGREEMENT\nis made this twelfth day of September, 1938 ...",
      "notes": "Unterschriften als Platzhalter in Klammern.",
      "regions": [
        {
          "id": "r1",
          "type": "heading",
          "bbox": [3.9, 2.9, 4.8, 0.3],
          "reading_order": 1,
          "text": "THIS AGREEMENT",
          "lines": 1,
          "label": "Titel des Dokuments"
        },
        {
          "id": "r2",
          "type": "paragraph",
          "bbox": [3.9, 3.2, 12.6, 1.0],
          "reading_order": 2,
          "text": "is made this twelfth day of September, 1938 ...",
          "lines": 4,
          "label": "Einleitungstext"
        }
      ]
    },
    {
      "page": 2,
      "image": "IMG_2.jpg",
      "type": "blank",
      "text": "",
      "notes": "Rueckseite, leer."
    },
    {
      "page": 3,
      "image": "IMG_3.jpg",
      "type": "color_chart",
      "text": "",
      "notes": "Farbskala fuer Archivierung."
    }
  ],

  "confidence": "high",
  "confidence_notes": "Gut lesbares Typoskript.",

  "quality": {
    "needs_review": false,
    "needs_review_reasons": [],
    "total_chars": 2057,
    "total_words": 356,
    "marker_density": 0.0,
    "language_detected": "en",
    "language_match": true
  }
}
```

---

## 4. Feldspezifikation

### 4.1 `page_json` (required)

Schema-Version. Aktuell `"0.1"`.

### 4.2 `source` (required)

| Feld | Pflicht | Typ | Beschreibung |
|---|---|---|---|
| `id` | Ja | string | Eindeutige Objekt-ID (`o_szd.100`, `BL_Add_MS_1234`) |
| `title` | Ja | string | Dokumenttitel |
| `language` | Ja | string | ISO 639-1/3 (`de`, `en`, `fr`, `la`, `und`) |
| `date` | Nein | string | Datierung, Freitext (`1918`, `ca. 1935-1940`) |
| `document_type` | Nein | enum | Physischer Dokumenttyp (kontrolliertes Vokabular, siehe §4.7) |
| `collection` | Nein | string | Sammlungskontext |
| `repository` | Nein | string | Aufbewahrende Institution |
| `shelfmark` | Nein | string | Signatur |
| `images` | Nein | string[] | URIs der Quellbilder in Seitenreihenfolge |
| `additional` | Nein | object | Projektspezifische Metadaten (freie Struktur) |

### 4.3 `provenance` (required)

| Feld | Pflicht | Typ | Beschreibung |
|---|---|---|---|
| `model` | Ja | string | Modell-ID fuer Transkription |
| `provider` | Nein | string | API-Anbieter (`google`, `anthropic`, `openai`) |
| `created_at` | Ja | date-time | ISO 8601 Zeitstempel |
| `pipeline` | Nein | string | Pipeline-Name/Version |
| `prompt_layers` | Nein | string[] | Prompt-Schichten (`["system", "group_handschrift"]`) |
| `parameters` | Nein | object | Modell-Parameter (temperature, top_p etc.) |
| `layout_model` | Nein | string | Modell-ID fuer Layout-Analyse (wenn abweichend) |

### 4.4 `pages[]` (required)

| Feld | Pflicht | Typ | Beschreibung |
|---|---|---|---|
| `page` | Ja | integer | Seitennummer (1-basiert, entspricht Bild-Index) |
| `image` | Nein | string | Bildverweis (Dateiname oder URI) |
| `image_width` | Nein | integer | Bildbreite in Pixel (required wenn `regions` vorhanden) |
| `image_height` | Nein | integer | Bildhoehe in Pixel (required wenn `regions` vorhanden) |
| `type` | Ja | enum | `content`, `blank`, `color_chart` |
| `text` | Ja | string | Transkribierter Text (leer bei blank/color_chart) |
| `notes` | Nein | string | Beobachtungen des Modells |
| `regions` | Nein | array | Layout-Regionen (siehe §4.5) |

### 4.5 `regions[]` (optional, pro Seite)

| Feld | Pflicht | Typ | Beschreibung |
|---|---|---|---|
| `id` | Ja | string | Region-ID (`r1`, `r2`, ..., Pattern: `^r\d+$`) |
| `type` | Ja | enum | `paragraph`, `heading`, `list`, `table`, `marginalia` |
| `bbox` | Ja | number[4] | Bounding Box `[x%, y%, w%, h%]` relativ zur Seite (0-100) |
| `reading_order` | Ja | integer | Lesereihenfolge (1, 2, 3, ...) |
| `text` | Nein | string | Text innerhalb dieser Region |
| `lines` | Nein | integer | Geschaetzte Zeilenanzahl |
| `label` | Nein | string | Kurzbeschreibung der Region |

**Koordinaten:** Prozentbasiert (0-100), relativ zur Seitengroesse. `[x, y, w, h]` = linke obere Ecke (x%, y%) + Breite (w%) + Hoehe (h%). Aufloesungsunabhaengig; Umrechnung in Pixel: `x_px = x% / 100 * image_width`.

### 4.6 `quality` und `evaluation` (optional)

Wie im bisherigen Format. `quality` enthaelt automatisch berechnete Signale (needs_review, marker_density, DWR, etc.). `evaluation` enthaelt CER/WER-Metriken gegen Ground Truth. Beide sind pipeline-abhaengig und nicht Teil des Kernformats.

### 4.7 `document_type` — Kontrolliertes Vokabular

```
manuscript, typescript, letter, postcard, notebook, diary, form, certificate,
newspaper_clipping, proof_sheet, register, calendar, ledger, mixed_materials
```

Abgeleitet aus den TEI-Objekttypen der 4 SZD-Sammlungen. Erweiterbar fuer andere Projekte.

---

## 5. Progressive Anreicherung

Der Kern-Workflow der Pipeline:

```
Schritt 1: transcribe.py
  → Page-JSON mit text + type + notes pro Seite
  → Kein regions-Array

Schritt 2: layout_analysis.py (optional)
  → Fuegt regions[] zu bestehenden Seiten hinzu
  → Setzt image_width, image_height
  → Ordnet Text den Regionen zu

Schritt 3: export_pagexml.py (optional)
  → Konvertiert Page-JSON → PAGE XML 2019
  → Nur wenn regions vorhanden
```

Beide Zustaende sind gueltige Page-JSON-Dokumente — ohne Regionen als Fliesstext, mit Regionen strukturiert.

---

## 6. Konvertierung

### 6.1 Page-JSON → PAGE XML

Deterministisch, verlustfrei. Pro Seite eine PAGE-XML-Datei:

| Page-JSON | PAGE XML |
|---|---|
| `pages[].image` | `<Page imageFilename="...">` |
| `pages[].image_width` | `<Page imageWidth="...">` |
| `pages[].regions[].id` | `<TextRegion id="...">` |
| `pages[].regions[].type` | `<TextRegion type="...">` |
| `pages[].regions[].bbox` | `<Coords points="x1,y1 x2,y1 x2,y2 x1,y2">` |
| `pages[].regions[].text` | `<TextEquiv><Unicode>...</Unicode></TextEquiv>` |
| `pages[].regions[].reading_order` | `<ReadingOrder><OrderedGroup>` |

**Bbox → Coords:** `[x%, y%, w%, h%]` → 4-Punkt-Polygon in Pixel:
```
x1 = round(x% / 100 * image_width)
y1 = round(y% / 100 * image_height)
x2 = round((x% + w%) / 100 * image_width)
y2 = round((y% + h%) / 100 * image_height)
points = "x1,y1 x2,y1 x2,y2 x1,y2"
```

Implementiert in `pipeline/export_pagexml.py`.

### 6.2 PAGE XML → Page-JSON

Umgekehrte Konvertierung (fuer Import aus Transkribus oder eScriptorium):

| PAGE XML | Page-JSON |
|---|---|
| `<Page imageWidth/imageHeight>` | `image_width`, `image_height` |
| `<TextRegion id="r1" type="paragraph">` | `regions[].id`, `regions[].type` |
| `<Coords points="...">` | `regions[].bbox` (Minimum Bounding Rect, in %) |
| `<TextEquiv><Unicode>` | `regions[].text` |
| `<ReadingOrder>` | `regions[].reading_order` |

### 6.3 Pipeline-Format → Page-JSON

Das aktuelle SZD-HTR-Output laesst sich verlustfrei abbilden:

| Pipeline-JSON | Page-JSON |
|---|---|
| `object_id` | `source.id` |
| `collection` | `source.collection` |
| `group` | `source.additional.group` |
| `model` | `provenance.model` |
| `metadata.title` | `source.title` |
| `metadata.language` | `source.language` (normalisiert: "Deutsch" → "de") |
| `metadata.images[]` | `source.images[]` |
| `context` | `source.additional.context` |
| `result.pages[].page` | `pages[].page` |
| `result.pages[].transcription` | `pages[].text` |
| `result.pages[].notes` | `pages[].notes` |
| `result.pages[].type` | `pages[].type` |
| `result.confidence` | `confidence` |
| `quality_signals.*` | `quality.*` |

Plus Merge mit `*_layout.json`:

| Layout-JSON | Page-JSON |
|---|---|
| `pages[].image_filename` | `pages[].image` |
| `pages[].image_width_px` | `pages[].image_width` |
| `pages[].image_height_px` | `pages[].image_height` |
| `pages[].regions[]` | `pages[].regions[]` (1:1) |

Die Konvertierung kann als Export-Schritt (`export_page_json.py`) oder als schrittweise Migration des Pipeline-Formats erfolgen.

---

## 7. Abgrenzung zu bestehenden Standards

| Frage | Antwort |
|---|---|
| Warum nicht direkt PAGE XML? | PAGE XML erfordert Koordinaten als Pflichtfeld. VLMs produzieren Fliesstext ohne Koordinaten. Page-JSON macht Koordinaten optional und ist das interne Arbeitsformat. PAGE XML ist Teil des Zielformats (METS/MODS + PAGE XML). |
| Warum nicht ALTO? | ALTO erfordert Wort-Koordinaten. Dasselbe Grundproblem wie PAGE XML. |
| Verhaeltnis zu METS/MODS? | Page-JSON = internes Arbeitsformat (Pipeline, Viewer). METS/MODS + PAGE XML = Archiv- und Austauschformat (GAMS, Transkribus, OCR-D). Page-JSON wird zuerst erzeugt, METS/MODS daraus abgeleitet. Siehe [[page-xml-mets-architecture]]. |
| Kann man PAGE XML exportieren? | Ja. `export_pagexml.py` konvertiert Page-JSON → PAGE XML 2019 (§6.1). |
| Kann man PAGE XML importieren? | Ja. Die Umkehrkonvertierung (§6.2) ermoeglicht Import von extern erzeugtem PAGE XML. |

---

## 8. Deskriptive Metadaten (v0.2)

v0.2 erweitert `source` um einen optionalen `descriptive_metadata`-Block, der das physische Objekt beschreibt. Dublin Core als Kern, materialtypologische Erweiterungen fuer Archivmaterial.

Schema: `schemas/page-json-v0.2.json`. Export: `pipeline/export_page_json.py`. TEI-Extraktion: `pipeline/tei_context.py` (`parse_tei_full_metadata()`).

### 8.1 Dublin-Core-Mapping

| `descriptive_metadata`-Feld | DC/DCT-Term | Datenquelle |
|---|---|---|
| `creator[]` (name, role, gnd) | dc:creator | TEI titleStmt/author, editor |
| `subject[]` | dc:subject | TEI keywords/term[@type="classification"] |
| `origin_place` | dct:spatial | TEI origPlace |
| `extent` | dct:extent | TEI measure[@type="leaf"] |
| `rights` | dc:rights | Backup metadata.json |
| `provenance[]` | dct:provenance | TEI history/provenance + acquisition |

### 8.2 Materialtypologische Erweiterungen

| Feld | Beschreibung | Datenquelle |
|---|---|---|
| `holding` (repository, gnd, country, settlement) | Archivkontext | TEI msIdentifier |
| `physical_description.writing_instrument` | Schreibinstrument | TEI material[@ana="WritingInstrument"] |
| `physical_description.writing_material` | Beschreibstoff | TEI material[@ana="WritingMaterial"] |
| `physical_description.hands[]` | Schreiberhaende | TEI handDesc/ab |
| `physical_description.dimensions` | Physische Masse | TEI measure[@type="format"] |
| `physical_description.binding` | Einband | TEI bindingDesc |
| `physical_description.inscriptions[]` | Aufschriften | TEI docEdition |
| `correspondence` (sender, recipient, direction) | Korrespondenz-Kontext | TEI correspDesc |
| `notes` | Katalogisierungsnotizen | TEI notesStmt/note |

### 8.3 Rueckwaertskompatibilitaet

- `page_json` akzeptiert `"0.1"` und `"0.2"` — v0.1-Dateien validieren gegen v0.2-Schema
- `descriptive_metadata` ist vollstaendig optional, alle Unterfelder optional
- `source.repository` (v0.1, String) koexistiert mit `descriptive_metadata.holding` (v0.2, Objekt mit GND)

---

## 9. Offene Punkte

1. **Schema-Hosting:** `$id`-URI auf GitHub Pages publizieren?
2. **Polygon-Koordinaten:** Aktuell nur Bounding Boxes (Rechtecke). Fuer unregelmässige Regionen waeren Polygon-Punkte (wie PAGE XML) noetig.
3. **Zeilen-Ebene:** PAGE XML kennt `<TextLine>` innerhalb von Regionen. Page-JSON hat aktuell nur `lines` (Anzahl) ohne Zeilen-Koordinaten.
4. **Korrespondenzen-TEI-Matching:** TEI hat nur Konvolut-Eintraege (nicht pro Brief). correspDesc-Daten muessen ueber Signatur-Prefix zugeordnet werden — noch nicht implementiert.
