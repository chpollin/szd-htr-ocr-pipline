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

## 9. Offene Punkte

1. **Stratifizierter Test:** Bisher nur Korrespondenz (I) getestet. 8 weitere Gruppen ausstehend.
2. **Unterschriften:** Werden teilweise nicht erkannt (weder von Docling noch Surya).
3. **Nicht-Determinismus:** VLM-Merger liefert bei gleicher Eingabe unterschiedliche Gruppierungen.
4. **Batch-Performance:** ~40s/Seite (Docling 15s + Surya 10s + 2x VLM 5s + Delays). Fuer 18.700 Seiten: ~8.5 Tage.
5. **TextLine-Ebene:** Aktuell nur TextRegion-Level. Surya-Zeilen koennten als `<TextLine>` in PAGE XML exportiert werden.

## 10. Referenzen

- Docling: https://github.com/docling-project/docling (IBM, MIT License)
- Surya: https://github.com/datalab-to/surya (Datalab)
- [[htr-interchange-format]] — Page-JSON Spezifikation
- [[verification-concept]] — Qualitaetssignale und Verifikation
