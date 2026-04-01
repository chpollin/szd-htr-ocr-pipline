---
title: "HTR Interchange Format: JSON-Schema fuer szd-htr → teiCrafter"
aliases: ["Interchange-Format", "HTR-JSON"]
created: 2026-04-01
updated: 2026-04-01
type: format-spec
tags: [szd-htr, tei, methodology]
status: draft
related:
  - "[[verification-concept]]"
  - "[[data-overview]]"
---

# HTR Interchange Format — Spezifikation

Version: 0.1 (Entwurf)

---

## 1. Zweck

Ein projektunabhaengiges JSON-Format fuer die Ergebnisse VLM-basierter Handschriften- und Texterkennung (HTR/OCR). Das Format dient als Bruecke zwischen HTR-Pipelines (wie SZD-HTR) und nachgelagerten Annotationswerkzeugen (wie teiCrafter).

### 1.1 Warum ein neues Format?

Die drei etablierten HTR/OCR-Standards — ALTO XML (Library of Congress), PAGE XML (PRImA Lab), hOCR — sind alle auf wort- und zeilenbasierte Bounding-Box-Ausgaben traditioneller OCR/HTR-Engines ausgelegt. VLMs (Gemini, Claude, GPT-4o) produzieren seitenweisen Fliesstext ohne raeumliche Koordinaten. Die bestehenden Standards passen strukturell nicht:

| Standard | Koordinaten erforderlich | Granularitaet | VLM-tauglich |
|---|---|---|---|
| ALTO XML 4.4 | Ja (HPOS/VPOS/W/H) | Wort/Zeile/Block | Nein |
| PAGE XML 2019 | Ja (Polygon-Punkte) | Glyphe/Wort/Zeile/Region | Nein |
| hOCR 1.2 | Ja (bbox) | Wort/Zeile/Bereich | Nein |
| **HTR Interchange** | **Nein** | **Seite** | **Ja** |

Es gibt keinen bestehenden JSON-Standard fuer VLM-basierte HTR. Jedes aktuelle Projekt (Humphries et al. 2024, Crosilla et al. 2025, Sherren et al. 2025) verwendet Ad-hoc-Formate. Dieses Format formalisiert das gemeinsame Muster.

### 1.2 Designprinzipien

1. **Seitenbasiert:** Eine Transkription pro Eingabebild. Keine Wort- oder Zeilenkoordinaten.
2. **Provenienz-transparent:** Welches Modell, welcher Prompt, wann? Reproduzierbarkeit.
3. **Qualitaetssignale integriert:** Kategoriale Konfidenz + automatisch berechnete Metriken.
4. **teiCrafter-kompatibel:** Alle Felder, die teiCrafter fuer Step 2 (Mapping) braucht, sind direkt abbildbar.
5. **Projektunabhaengig:** Keine SZD-spezifischen Felder auf Top-Level. Projekt-Metadaten gehoeren in `source`.

---

## 2. Abgrenzung

Das Interchange-Format kodiert **Transkriptionsergebnisse**, nicht:
- Layout-Analyse (Regionen, Bounding Boxes) → ALTO/PAGE
- TEI-Annotation (Named Entities, Strukturelemente) → teiCrafter-Output
- Editorische Entscheidungen (Normalisierung, Aufloesung) → nachgelagerte Pipeline-Stufen

Es ist ein **Transportformat zwischen HTR und Annotation**, kein Langzeitarchivierungsformat.

---

## 3. JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/htr-interchange/v0.1",
  "title": "HTR Interchange Format",
  "description": "Seitenbasiertes JSON-Format fuer VLM-basierte HTR/OCR-Ergebnisse",
  "type": "object",
  "required": ["htr_interchange", "source", "provenance", "transcription"],
  "properties": {

    "htr_interchange": {
      "type": "string",
      "const": "0.1",
      "description": "Schema-Version"
    },

    "source": {
      "type": "object",
      "description": "Metadaten zum Quelldokument",
      "required": ["id", "title", "language"],
      "properties": {
        "id":           { "type": "string", "description": "Eindeutige Objekt-ID (z.B. 'o_szd.100', 'BL_Add_MS_1234')" },
        "title":        { "type": "string" },
        "language":     { "type": "string", "description": "ISO 639-1 oder Freitext (z.B. 'de', 'fr', 'en', 'la')" },
        "date":         { "type": "string", "description": "Datierung des Dokuments (Freitext, z.B. '1918', 'ca. 1935-1940')" },
        "document_type": { "type": "string", "description": "Physischer Typ (z.B. 'manuscript', 'typescript', 'letter', 'newspaper_clipping', 'form')" },
        "collection":   { "type": "string", "description": "Sammlungskontext (z.B. 'lebensdokumente', 'korrespondenzen')" },
        "repository":   { "type": "string", "description": "Aufbewahrende Institution" },
        "shelfmark":    { "type": "string", "description": "Signatur" },
        "images":       {
          "type": "array",
          "items": { "type": "string", "format": "uri" },
          "description": "URIs der Quellbilder in Seitenreihenfolge"
        },
        "additional":   {
          "type": "object",
          "description": "Projektspezifische Metadaten (z.B. SZD-Gruppe, TEI-Kontext)",
          "additionalProperties": true
        }
      }
    },

    "provenance": {
      "type": "object",
      "description": "Wie und wann die Transkription erzeugt wurde",
      "required": ["model", "created_at"],
      "properties": {
        "model":        { "type": "string", "description": "Modell-ID (z.B. 'gemini-3.1-flash-lite-preview', 'claude-sonnet-4-5')" },
        "provider":     { "type": "string", "description": "API-Anbieter (z.B. 'google', 'anthropic', 'openai')" },
        "created_at":   { "type": "string", "format": "date-time", "description": "Zeitstempel der Transkription (ISO 8601)" },
        "pipeline":     { "type": "string", "description": "Name/Version der HTR-Pipeline (z.B. 'szd-htr 0.3')" },
        "prompt_layers": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Verwendete Prompt-Schichten (z.B. ['system', 'group_handschrift', 'object_context'])"
        },
        "parameters":   {
          "type": "object",
          "description": "Modell-Parameter (temperature, top_p, max_tokens etc.)",
          "additionalProperties": true
        }
      }
    },

    "transcription": {
      "type": "object",
      "description": "Die eigentliche Transkription",
      "required": ["pages"],
      "properties": {
        "pages": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["page", "text"],
            "properties": {
              "page":  { "type": "integer", "minimum": 1, "description": "Seitennummer (1-basiert, entspricht Bild-Index)" },
              "text":  { "type": "string", "description": "Transkribierter Text der Seite" },
              "notes": { "type": "string", "description": "Beobachtungen des Modells zu dieser Seite" }
            }
          }
        },
        "confidence": {
          "type": "string",
          "enum": ["high", "medium", "low"],
          "description": "Kategoriale Selbsteinschaetzung des Modells (Gesamt)"
        },
        "confidence_notes": {
          "type": "string",
          "description": "Begruendung der Konfidenz-Einschaetzung"
        }
      }
    },

    "quality": {
      "type": "object",
      "description": "Automatisch berechnete Qualitaetssignale (optional, pipeline-abhaengig)",
      "properties": {
        "needs_review":         { "type": "boolean" },
        "needs_review_reasons": { "type": "array", "items": { "type": "string" } },
        "total_chars":          { "type": "integer" },
        "total_words":          { "type": "integer" },
        "marker_density":       { "type": "number", "description": "([?] + [...]) / Wortanzahl" },
        "duplicate_page_pairs": { "type": "array", "items": { "type": "array", "items": { "type": "integer" } } },
        "language_detected":    { "type": "string" },
        "language_match":       { "type": "boolean" }
      },
      "additionalProperties": true
    },

    "evaluation": {
      "type": "object",
      "description": "Evaluationsmetriken gegen Ground Truth (optional, erst nach GT-Erstellung)",
      "properties": {
        "cer":            { "type": "number", "description": "Character Error Rate (0.0 = perfekt)" },
        "wer":            { "type": "number", "description": "Word Error Rate" },
        "cer_per_page":   { "type": "array", "items": { "type": "number" } },
        "reference":      { "type": "string", "description": "Verweis auf Referenz-Datei oder -ID" },
        "evaluated_at":   { "type": "string", "format": "date-time" }
      }
    }
  }
}
```

---

## 4. Mapping auf teiCrafter

teiCrafter (Step 1: Import, Step 2: Mapping) erwartet folgende Daten:

| teiCrafter-Feld | Interchange-Quelle | Transformation |
|---|---|---|
| `inputContent` | `transcription.pages[].text` | Seiten mit `|{n}|` konkatenieren (teiCrafter-Seitentrenner) |
| `inputFormat` | (konstant) | `"plaintext"` |
| `sourceType` | `source.document_type` | Mapping: manuscript/letter → correspondence, newspaper_clipping/print → print, sonst → generic |
| `language` | `source.language` | ISO 639-1 direkt, ggf. erweitern (teiCrafter kennt bisher nur de/la/mhd) |
| `epoch` | `source.date` | Ableiten: "19xx" → 19c, "18xx" → 18c, "1xxx" → medieval. Fallback: 19c |
| `project` | `source.collection` oder `source.repository` | Freitext |
| `mappingRules` | (nicht im Interchange) | Vom Benutzer in teiCrafter konfiguriert oder aus Vorlagen geladen |
| `fileName` | `source.id` + `.json` | Generiert |

### 4.1 sourceType-Mapping

| Interchange `document_type` | teiCrafter `sourceType` |
|---|---|
| `manuscript`, `notebook`, `diary` | `generic` (kein passendes teiCrafter-Mapping) |
| `letter`, `postcard`, `correspondence` | `correspondence` |
| `typescript`, `form`, `certificate` | `generic` |
| `newspaper_clipping`, `proof_sheet` | `print` |
| `register`, `calendar`, `ledger` | `bookkeeping` |
| `recipe` | `recipe` |

### 4.2 Erweiterungsbedarf in teiCrafter

Fuer die SZD-HTR-Integration muss teiCrafter erweitert werden:

1. **JSON-Import in Step 1:** Neuer Dateityp `.json`, Validierung gegen das Schema, automatische Extraktion von `inputContent` aus `transcription.pages[]`.
2. **Sprachen erweitern:** `en`, `fr`, `it`, `es` neben `de`, `la`, `mhd`.
3. **Epochen erweitern:** `20c` (fruehes 20. Jahrhundert) neben `medieval`, `18c`, `19c`.
4. **Step-2-Vorbelegung:** Wenn JSON `source.language`, `source.date`, `source.document_type` enthaelt, Step-2-Felder automatisch vorbelegen (Benutzer kann ueberschreiben).
5. **Mehrseitige Dokumente:** Seitentrenner im Import erkennen und ggf. als `<pb/>`-Elemente in die TEI-Annotation uebernehmen.

---

## 5. Mapping auf SZD-HTR (aktuelles Format)

Das aktuelle SZD-HTR-Output laesst sich verlustfrei auf das Interchange-Format abbilden:

| SZD-HTR-Feld | Interchange-Feld |
|---|---|
| `object_id` | `source.id` |
| `collection` | `source.collection` |
| `group` | `source.additional.group` |
| `model` | `provenance.model` |
| `metadata.title` | `source.title` |
| `metadata.language` | `source.language` (normalisiert: "Deutsch" → "de", "Englisch" → "en") |
| `metadata.images[]` | `source.images[]` |
| `context` | `source.additional.context` |
| `result.pages[].page` | `transcription.pages[].page` |
| `result.pages[].transcription` | `transcription.pages[].text` |
| `result.pages[].notes` | `transcription.pages[].notes` |
| `result.confidence` | `transcription.confidence` |
| `result.confidence_notes` | `transcription.confidence_notes` |
| `quality_signals.*` | `quality.*` |

Die Konvertierung ist ein 1:1-Mapping mit minimaler Normalisierung (Sprachcodes, Feldnamen). Lane 3 kann das als Export-Funktion oder als Konformitaetsanpassung des bestehenden Formats implementieren.

### 5.1 Empfehlung: Konformitaet vs. Export

**Option A: Konformitaet.** Das SZD-HTR-Output-Format direkt an das Interchange-Format anpassen. Vorteil: Keine separate Konvertierung noetig. Nachteil: Aendert das bestehende Format, bestehende 16 Objekte muessen migriert werden.

**Option B: Export.** Das bestehende Format beibehalten und einen separaten Export-Schritt ergaenzen (`pipeline/export_interchange.py`). Vorteil: Keine Migration, bestehender Code bleibt stabil. Nachteil: Zwei Formate pflegen.

**Empfehlung: Option B (Export).** Das bestehende Format funktioniert fuer die Pipeline-interne Verarbeitung. Das Interchange-Format ist ein Austauschformat fuer externe Tools. Die Konvertierung ist trivial und kann als Build-Schritt nach `build_viewer_data.py` laufen.

---

## 6. Beispiel

Ein vollstaendiges Beispiel basierend auf o_szd.100 (Agreement Longmans):

```json
{
  "htr_interchange": "0.1",

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
    ],
    "additional": {
      "group": "typoskript",
      "context": "## Dieses Dokument\n\n- Titel: Agreement Longmans, Green & Co. Inc.\n- Signatur: SZ-AAP/L13.23\n- Datum: twelfth day of September, 1938\n- Sprache: Englisch\n- Objekttyp: Typoskriptdurchschlag"
    }
  },

  "provenance": {
    "model": "gemini-3.1-flash-lite-preview",
    "provider": "google",
    "created_at": "2026-03-31T14:30:00Z",
    "pipeline": "szd-htr 0.3",
    "prompt_layers": ["system", "group_b_typoskript", "object_context"]
  },

  "transcription": {
    "pages": [
      {
        "page": 1,
        "text": "THIS AGREEMENT\n\nis made this twelfth day of September, 1938 between Stefan Zweig ...",
        "notes": "Die Unterschriften wurden als Platzhalter in Klammern gesetzt."
      },
      {
        "page": 2,
        "text": "",
        "notes": "Rueckseite des Dokuments, kein Text."
      },
      {
        "page": 3,
        "text": "",
        "notes": "Rueckseite mit Farb- und Graukarte."
      }
    ],
    "confidence": "high",
    "confidence_notes": "Gut lesbares Typoskript."
  },

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

## 7. Abgrenzung zu bestehenden Standards

| Frage | Antwort |
|---|---|
| Warum nicht ALTO? | ALTO erfordert Wort-Koordinaten (HPOS/VPOS/WIDTH/HEIGHT). VLMs produzieren keine. Leere Koordinaten wuerden das Schema verletzen und Downstream-Tools verwirren. |
| Warum nicht PAGE XML? | Selbes Problem: Polygon-Koordinaten auf jeder Ebene erforderlich. Zusaetzlich: kaum Metadaten-Felder (keine Sprache, kein Dokumenttyp). |
| Warum nicht hOCR? | HTML-basiert, erfordert Bounding Boxes. Fuer VLM-Output ueberkompliziert. |
| Kann man trotzdem ALTO/PAGE exportieren? | Ja, als Downstream-Schritt: Eine Seite = ein TextBlock mit Dummy-Koordinaten (0,0 bis Bildbreite,Bildhoehe). Das ist technisch moeglich, aber semantisch arm — es nutzt die Standards nicht fuer ihren eigentlichen Zweck. |
| Gibt es Interoperabilitaet? | Das Interchange-Format kann ALTO/PAGE/hOCR als zusaetzlichen Export produzieren, wenn Bibliotheksinfrastruktur das erfordert. Das ist ein separater Konvertierungsschritt, kein Teil dieses Formats. |

---

## 8. Offene Punkte

1. **Schema-Hosting:** Der `$id`-URI ist ein Platzhalter. Soll das Schema auf GitHub Pages publiziert werden?
2. **Mehrseitige Konkatenation:** ~~Vorschlag `\n\n---\n\n`~~ → **Entschieden: `|{n}|`** als Seitentrenner (teiCrafter-Konvention, alle Demo-Mappings verwenden dieses Format). Siehe [[teiCrafter-integration]] §5 fuer Details.
3. **Sprach-Normalisierung:** `source.language` erlaubt ISO 639-1 und Freitext. Soll das Schema strengere Validierung erzwingen?
4. **document_type-Vokabular:** Offene Enumeration vs. kontrolliertes Vokabular? Aktuell: offen (Freitext). Fuer Interoperabilitaet waere ein kontrolliertes Vokabular besser.
5. **Versionierung:** Wie wird das Schema versioniert? Vorschlag: SemVer (0.1 → 0.2 bei Felderweiterung, 1.0 bei Stabilisierung).
