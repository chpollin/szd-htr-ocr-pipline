---
title: "Layout-Analyse"
created: 2026-04-02
updated: 2026-04-03
type: spec
status: draft
---

# Layout-Analyse: Ensemble-Pipeline

Dokumentiert den Ensemble-Ansatz (Docling + Surya + VLM) fuer die Layout-Erkennung im SZD-HTR-Projekt.

## 1. Motivation

Die HTR-Pipeline (`transcribe.py`) erzeugt seitenweisen Fliesstext ohne Strukturinformation. Fuer zwei nachgelagerte Ziele wird strukturiertes Layout benoetigt:

1. **Strukturierte Ausgabe:** Unterscheidung zwischen Ueberschriften, Absaetzen, Listen, Tabellen und Marginalien.
2. **DIA-XAI Expert-in-the-Loop:** Raeumliche Verortung von Textregionen auf dem Faksimile (Bild↔Text-Sync).

## 2. Ansatz: Ensemble-Pipeline (v4)

### 2.1 Entwicklung

| Version | Ansatz | Ergebnis |
|---|---|---|
| v1 | VLM-only (Gemini Flash Lite) | Gute Typisierung, aber systematisch falsche Koordinaten (y=5% statt y=38%) |
| v2 | Docling-only (CV) | Pixelgenaue Koordinaten bei Druck, versagt bei Handschrift und kontrastarmen Scans |
| v3 | Docling + Surya mit Routing | Surya `LayoutPredictor` erkennt nur grobe Bloecke, zu wenig Regionen |
| **v4** | **Ensemble: Docling + Surya + VLM** | **Pixelgenaue Koordinaten + intelligente Gruppierung + Typisierung** |

### 2.2 Architektur

```
Bild ──┬── Docling (Block-Level)     → Regionen mit Typen + Bbox
       │   IBM, DocLayNet-Modell       (paragraph, heading, table, ...)
       │
       ├── Surya Detection (Lines)   → Einzelne Textzeilen + Bbox
       │   DetectionPredictor          (pixelgenaue Zeilenerkennung)
       │
       └── Gemini 3 Flash (VLM)      → Finale Regionen
           Sieht: Bild + Docling + Surya
           → Merged, gruppiert, klassifiziert
           → Verifikation (Layout-Qualitaetssignal)
```

**Kern-Prinzip:** Beide CV-Tools laufen IMMER parallel auf jeder Seite. Das VLM sieht das Originalbild UND beide CV-Ergebnisse und erzeugt die finale Layout-Beschreibung. Kein Routing — das Ensemble nutzt immer alle drei Stufen.

### 2.3 Warum Ensemble?

| Tool | Staerke | Schwaeche |
|---|---|---|
| **Docling** | Pixelgenaue Bboxes, Typklassifikation (DocLayNet) | Verpasst Regionen bei Handschrift und kontrastarmen Scans |
| **Surya** | Praezise Zeilenerkennung, auch bei Handschrift | Keine Typklassifikation, erkennt nur Textzeilen |
| **Gemini 3 Flash** | Semantische Gruppierung, Typisierung, Lueckenerkennung | Kann keine pixelgenauen Koordinaten schaetzen |

Das Ensemble kombiniert: CV-Tools liefern die Koordinaten (Wo?), das VLM liefert die Semantik (Was?).

## 3. Stufen

### Stufe 1a: Docling (Block-Level)

- **Tool:** IBM Docling (`DocumentConverter`)
- **Input:** JPEG-Bild als Temp-Datei
- **Output:** Regionen mit Bbox + DocLayNet-Typ (text, section_header, table, etc.)
- **Koordinaten:** BOTTOMLEFT-Pixel → Konvertierung zu TOPLEFT-Prozent
- **Laufzeit:** ~15s/Seite auf GPU

### Stufe 1b: Surya (Line-Level)

- **Tool:** Surya `DetectionPredictor` (nicht `LayoutPredictor`)
- **Input:** PIL Image aus Bytes
- **Output:** Textzeilen mit Bbox (keine Typklassifikation)
- **Koordinaten:** TOPLEFT-Pixel → Konvertierung zu Prozent
- **Laufzeit:** ~10s/Seite auf GPU
- **Wichtig:** `DetectionPredictor` erkennt einzelne Textzeilen, nicht Layoutbloecke

### Stufe 2: VLM Ensemble-Merger

- **Modell:** Gemini 3 Flash (`gemini-3-flash-preview`)
- **Prompt:** `prompts/layout_ensemble.md` + Gruppen-Prompt (`layout_group_*.md`)
- **Input:** Bild + Docling-Regionen (JSON) + Surya-Zeilen (JSON)
- **Aufgabe:**
  1. Surya-Zeilen zu logischen Regionen gruppieren
  2. Docling-Typen uebernehmen/korrigieren
  3. Fehlende Regionen ergaenzen
  4. Lesereihenfolge und Labels vergeben
- **Output:** Finale `regions[]` mit `source`-Feld (docling/surya/merged/vlm_added)

### Stufe 3: VLM Verifikation

- **Prompt:** `prompts/layout_verify.md`
- **Bewertet:** Abdeckung, Position, Typen, Lesereihenfolge
- **Output:** `layout_quality` mit `overall` (good/acceptable/needs_correction)

## 4. Strukturelemente

Fuenf Regionentypen:

| Typ | Beschreibung | Typische Dokumente |
|---|---|---|
| `paragraph` | Fliesstext-Absatz | Alle Gruppen |
| `heading` | Ueberschrift, Datumzeile, Anrede, Grussformel, Unterschrift | Briefe (I), Werke (A) |
| `list` | Aufzaehlung, nummerierte Liste | Vertraege, Register |
| `table` | Tabelle, tabellarische Struktur | Register (E), Kontorbuecher |
| `marginalia` | Randnotiz, Annotation | Manuskripte (A), Korrekturfahnen (F) |

## 5. Koordinatensystem

**Prozent des GESAMTEN Bildes (0-100):** Inklusive Scan-Hintergrund und Raender.

```
bbox: [x%, y%, breite%, hoehe%]

Beispiel: [25, 38, 35, 18]
→ Region beginnt bei 25% vom linken Bildrand, 38% vom oberen Bildrand
→ Ist 35% der Bildbreite breit und 18% der Bildhoehe hoch
```

Typische Werte bei Archiv-Scans: Das Papier beginnt bei ca. x=15-25%, y=10-20%. Text liegt daher typisch bei x=20-30%, y=15-75%.

## 6. Output-Format

### Layout JSON (`*_layout.json`)

```json
{
  "object_id": "o_szd.1079",
  "collection": "korrespondenzen",
  "group": "korrespondenz",
  "model": "docling+surya+gemini-3-flash-preview",
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
          "bbox": [17.5, 37.9, 34.9, 5.2],
          "reading_order": 1,
          "lines": 1,
          "label": "Anrede",
          "source": "surya"
        }
      ]
    }
  ],
  "layout_quality": {
    "overall": "good",
    "pages": [...]
  }
}
```

Das `source`-Feld dokumentiert die Herkunft jeder Region:
- `docling` — Bbox aus Docling, Typ unveraendert
- `surya` — Bbox aus Surya-Zeilenerkennung
- `merged` — Kombination aus beiden CV-Tools
- `vlm_added` — Vom VLM ergaenzt (Lueckenfuellung)

## 7. Dateien

| Datei | Beschreibung |
|---|---|
| `pipeline/layout_analysis.py` | Ensemble-Pipeline (Docling + Surya + VLM) |
| `pipeline/export_pagexml.py` | Deterministischer PAGE XML Export |
| `pipeline/prompts/layout_ensemble.md` | Prompt fuer VLM-Merger (Stufe 2) |
| `pipeline/prompts/layout_verify.md` | Prompt fuer VLM-Verifikation (Stufe 3) |
| `pipeline/prompts/layout_group_*.md` | 9 gruppenspezifische Layout-Prompts |

### CLI

```bash
# Ensemble-Analyse (alle 3 Stufen)
python pipeline/layout_analysis.py o_szd.1079 -c korrespondenzen --force

# Nur CV-Stufen (Docling + Surya, ohne VLM)
python pipeline/layout_analysis.py o_szd.1079 -c korrespondenzen --cv-only --force

# Batch
python pipeline/layout_analysis.py -c korrespondenzen --limit 10
```

## 8. Modellvergleich (VLM-Merger)

Getestet auf Briefumschlag o_szd.1079:

| Modell | Regionen | Gruppierung | Typisierung | Halluzinationen |
|---|---|---|---|---|
| Flash Lite | 2 (inkonsistent) | Grob | Teilweise falsch | Ja |
| Flash 2.0 | 5 (granular) | Jede Zeile einzeln | Gut | Nein |
| **Flash 3** | **2 (semantisch)** | **Anrede + Adressblock** | **Gut** | **Nein** |

Flash 3 ist der Default (`HTR_LAYOUT_MODEL=gemini-3-flash-preview`).

## 9. Stratifizierter Test (Session 24, 2026-04-03)

### 9.1 Robustness-Refactoring (Phase 1, erledigt)

8 Fixes in `layout_analysis.py`, `config.py`, `transcribe.py`, `export_pagexml.py`, `layout-regions-v0.1.json`:

1. Per-Page Error Handling (try-except um Seitenverarbeitung)
2. PIL-Fallback bei fehlenden JPEG-Dimensionen
3. VLM-Fallback-Logging (Warnung statt stille Degradation)
4. Halluzinations-Filter (Full-Page-Bbox >95% ablehnen, Tiny-Regions loggen)
5. Schwellenwerte nach `config.py` (`LAYOUT_MIN_REGION_WIDTH_PCT`, `LAYOUT_MIN_REGION_HEIGHT_PCT`, `LAYOUT_MAX_REGION_PCT`)
6. Region-ID-Normalisierung (`_normalize_region_ids()` → r1, r2, ..., Schema-konform)
7. Shared `find_ocr_file()` in `transcribe.py` (ersetzt fragile Glob-Logik)
8. Schema: `source`-Feld + `group`-Feld hinzugefuegt

### 9.2 Welle 1: Einfache Objekte (8 Objekte, 21 Content-Seiten)

| Objekt | Gruppe | Content-Seiten | Regionen | Quality | Bemerkungen |
|---|---|---|---|---|---|
| o_szd.148 | D Kurztext | 1 | 6 | good | Sachfoto, kein Dokument — Layout konzeptionell fragwuerdig |
| o_szd.1081 | I Korrespondenz | 2 | 7 | good | 1 False-Positive im Scan-Hintergrund (Region 1) |
| o_szd.2215 | H Zeitungsausschnitt | 2 | 17 | good | Bestes Ergebnis — komplexes Mixed-Layout hervorragend erkannt |
| o_szd.102 | B Typoskript | 2 | 22 | good | |
| o_szd.145 | C Formular | 1 | 4 | good | Perfekt — 4 praezise Regionen |
| o_szd.139 | A Handschrift | 2 | 14 | good | |
| o_szd.1887 | F Korrekturfahne | 2 | 8 | good | S1 Verify-Parse-Fehler (Regions selbst korrekt) |
| o_szd.206 | G Konvolut | 9 | 51 | acceptable | S17 fehlende Marginalien, einzelne Ueberlappungen |

**Quality-Verteilung (18 Objekte gesamt):** 13 good (72%), 2 acceptable (11%), 2 needs_correction (11%), 1 n/a (6%)

### 9.3 Identifizierte systematische Probleme

Aus visueller Inspektion von 12 Content-Seiten:

| Problem | Haeufigkeit | Betroffene Objekte | Schwere |
|---|---|---|---|
| **Scan-Hintergrund-False-Positives** | 2/12 Seiten | o_szd.1081, o_szd.206 | Mittel |
| **Ueberlappende Regionen** | 1/12 Seiten | o_szd.206 | Mittel |
| **Spurious Zwischen-Regionen** | 1/12 Seiten | o_szd.206 (Region 3: duenne Korrekturzeile als eigene Region) | Niedrig |
| **Sachfotos statt Dokumente** | 1/8 Objekte | o_szd.148 | Konzeptionell |
| **VLM-Verify-Parse-Fehler** | 1/21 Seiten | o_szd.1887 | Niedrig |

### 9.4 Phase 2: Post-Processing + Prompt-Verfeinerung (erledigt)

**Phase 2a — 3 deterministische Post-Processing-Filter** (`_postprocess_regions()` in `layout_analysis.py`):

| Filter | Logik | Wirkung (Welle 2) |
|---|---|---|
| Scan-Hintergrund | y<8% oder y+h>92% bei h<2%, oder x<8% bei w<3% und h>20% | o_szd.101 S4: 2 Rand-Regionen entfernt |
| Ueberlappung | IoU >50% bei gleichem Typ → kleinere mergen | Kein Trigger in Welle 2 (Prompt-Verfeinerung verhindert Ueberlappung upstream) |
| Spurious Zwischen-Region | h<1.5% und vollstaendig innerhalb groesserer Region | o_szd.1888: 5 Seitenzahl-Regionen entfernt, o_szd.101 S1: 1 Zwischenzeile entfernt, o_szd.146 S3: 1 Abschnittsueberschrift entfernt |

**Phase 2b — Prompt-Verfeinerung** (`prompts/layout_ensemble.md`):
3 neue Regeln: Keine Ueberlappung, minimale Regionsgroesse, Scan-Hintergrund != Marginalie.

### 9.5 Welle 2: Mittelschwere Objekte (7 Objekte + 2 Re-Analysen)

| Objekt | Gruppe | Content-Seiten | Regionen | Quality | Filter-Aktionen |
|---|---|---|---|---|---|
| o_szd.168 | A Handschrift | 2 | 4 | good | — |
| o_szd.101 | B Typoskript | 4 | 40 | good | 3 Regionen entfernt (2x Scan-Rand, 1x spurious) |
| o_szd.146 | C Formular | 8 | 47 | acceptable | 1 spurious entfernt |
| o_szd.142 | D Kurztext | 1 | 2 | good | — |
| o_szd.1888 | F Korrekturfahne | 6 | 30 | good | 5 Seitenzahlen entfernt (spurious) |
| o_szd.2217 | H Zeitungsausschnitt | 1 | 11 | good | — |
| o_szd.1088 | I Korrespondenz | 2 | 5 | acceptable | — |

Re-Analysen mit neuen Filtern + Prompt:

| Objekt | Vorher | Nachher | Verbesserung |
|---|---|---|---|
| o_szd.1081 | good (3 False-Positive R1) | good (4 Regionen, kein FP) | Prompt-Verfeinerung verhindert Scan-Rand-Region |
| o_szd.206 | acceptable (S17) | needs_correction (S13) | S17 jetzt good; S13 neu problematisch (VLM-Nichtdeterminismus) |

### 9.6 Gesamtstatistik (25 Objekte, Stand 2026-04-03)

| Quality | Anzahl | Anteil |
|---|---|---|
| good | 18 | 72% |
| acceptable | 3 | 12% |
| needs_correction | 3 | 12% |
| n/a | 1 | 4% |

Filter-Bilanz: 12 Regionen in Welle 2 deterministisch entfernt (7 spurious, 3 Scan-Rand, 2 VLM-Verify-Parse-Auswirkung).

## 10. Offene Verbesserungen

### Phase 2c: Sachfoto-Erkennung (offen)

- Neuer `page.type`-Wert `photograph` in `quality_signals.py` — erkennt Seiten die Objekte statt Dokumente zeigen
- Layout-Analyse ueberspringt `photograph`-Seiten (analog zu `blank` und `color_chart`)
- Alternativ: Gruppe D (Kurztext) pruefen wie viele Sachfotos enthalten sind

### Phase 3: Quantitative Evaluation (offen)

Bisher nur qualitative Bewertung (visuell). Fuer methodische Absicherung:

1. **Layout-GT fuer 5 Seiten** manuell erstellen (1 pro Schwierigkeitsgrad):
   - Einfach: o_szd.145 S1 (Formular, 4 Regionen)
   - Mittel: o_szd.1081 S1 (Korrespondenz, Postkarte)
   - Komplex: o_szd.2215 S1 (Zeitungsausschnitt, 10 Regionen)
   - Schwer: o_szd.206 S1 (Konvolut, Korrekturen)
   - Sonderfall: o_szd.1887 S1 (Korrekturfahne, 72 Surya-Zeilen)

2. **Metriken:** Region-Count-Accuracy, Type-Accuracy, Coverage, False-Positive-Rate

### Phase 4: Merge+Verify Zusammenlegen (erledigt, Session 24)

- Vorher: 2 VLM-Calls pro Seite (Merge + Verify) = ~14s VLM-Zeit/Seite
- Nachher: 1 kombinierter VLM-Call (Merge+Verify) = ~7s VLM-Zeit/Seite
- **Einsparung: ~7s/Seite = ~36h bei 18.700 Seiten**
- Kombinierter Prompt in `prompts/layout_ensemble.md`: Output-Format enthaelt `regions[]` + `quality{}`
- `_merge_and_classify()` gibt jetzt `tuple[list[dict], dict | None]` zurueck (Regionen + Quality)
- `_verify_layout()` bleibt als Legacy-Funktion, wird nicht mehr aufgerufen
- `prompts/layout_verify.md` bleibt als Referenz, wird nicht mehr geladen
- Getestet auf o_szd.148: 5 Regionen + `good` Quality in einem Call

### Pipeline-Stufen nach Session 24

```
Bild --+-- Stufe 1a: Docling (Block-Level, ~15s)
       |
       +-- Stufe 1b: Surya  (Line-Level, ~10s)
       |
       +-- Stufe 2+3: Gemini 3 Flash (kombiniert)
       |   - Merge: Zeilen gruppieren, Typen zuweisen, Luecken fuellen
       |   - Verify: Coverage, Position, Typen bewerten
       |   - 1 VLM-Call statt 2 (~5-7s)
       |
       +-- Stufe 2.5: Deterministische Post-Processing-Filter
           - Scan-Hintergrund entfernen
           - Ueberlappungen aufloesen
           - Spurious Zwischen-Regionen entfernen
```

Geschaetzte Laufzeit pro Seite: ~33s (Docling 15s + Surya 10s + VLM 6s + Delay 2s).
Geschaetzte Gesamtlaufzeit fuer 18.700 Seiten: ~7 Tage (vorher ~8.5 Tage).

## 11. Offene Punkte (aktualisiert, Session 24)

1. ~~Stratifizierter Test: Bisher nur Korrespondenz (I) getestet~~ -> Erledigt (§9.2, alle 9 Gruppen)
2. ~~Merge+Verify zusammenlegen~~ -> Erledigt (§10 Phase 4)
3. **Unterschriften:** Werden teilweise nicht erkannt (weder von Docling noch Surya)
4. **Nicht-Determinismus:** VLM-Merger liefert bei gleicher Eingabe unterschiedliche Gruppierungen (o_szd.206 S13 vs. S17 Wechsel)
5. **TextLine-Ebene:** Surya-Zeilen als `<TextLine>` in PAGE XML exportieren (aktuell nur TextRegion)
6. **Sachfotos:** Gruppe D enthaelt Objektfotografien — Layout-Analyse dort konzeptionell fragwuerdig (§10 Phase 2c)
7. **Welle 2 visuelle Verifikation:** 9 Objekte stehen bereit, noch nicht vom Projektleiter inspiziert
8. **Batch-Lauf:** Nach visueller Verifikation und ggf. Prompt-Tuning: Layout-Analyse fuer alle ~1300 transkribierten Objekte

## 12. Referenzen

- Docling: https://github.com/docling-project/docling (IBM, MIT License)
- Surya: https://github.com/datalab-to/surya (Datalab)
- [[htr-interchange-format]] — Page-JSON Spezifikation
- [[verification-concept]] — Qualitaetssignale und Verifikation
