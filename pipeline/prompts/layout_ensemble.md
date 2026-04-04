# Layout-Ensemble: Docling + Surya -> VLM Merger + Verifikation (Stufe 2+3)

Merged zwei automatische Layout-Analysen zu einem finalen Ergebnis und bewertet die Qualitaet.
Wird von `layout_analysis.py` (Stufe 2+3, kombiniert) verwendet.

```
Du erhaeltst ein Dokumentbild und zwei automatische Layout-Analysen desselben Bildes.

## Analyse A: Block-Erkennung (Docling)

Erkennt groessere Textbloecke und klassifiziert ihren Typ (text, section_header, table, etc.). Die Bounding-Box-Koordinaten sind pixelgenau.

{docling_regions}

## Analyse B: Zeilen-Erkennung (Surya)

Erkennt einzelne Textzeilen mit praezisen Bounding Boxes. Keine Typklassifikation — nur Zeilenpositionen.

{surya_lines}

## Deine Aufgabe

Erzeuge die FINALE Layout-Beschreibung fuer dieses Dokumentbild UND bewerte deren Qualitaet. Nutze das Beste aus BEIDEN Analysen:

1. **ZEILEN GRUPPIEREN**: Fasse Surya-Zeilen zu logischen Regionen zusammen. Aufeinanderfolgende Zeilen mit aehnlicher x-Position gehoeren zum selben Absatz. Die Bbox der gruppierten Region umfasst alle enthaltenen Zeilen (kleinster x, kleinster y, groesste Breite, Summe der Hoehen).

2. **TYPEN ZUWEISEN**: Nutze die Docling-Typen als Orientierung. Klassifiziere jede Region als einen der 5 Typen:
   - **paragraph**: Fliesstext, Brieftext
   - **heading**: Ueberschrift, Datumzeile, Anrede, Grussformel, Unterschrift
   - **list**: Aufzaehlung
   - **table**: Tabelle, tabellarische Struktur
   - **marginalia**: Randnotiz, Annotation

3. **LUECKEN FUELLEN**: Wenn BEIDE Tools einen Textbereich uebersprungen haben, ergaenze eine neue Region. Typische Luecken: Unterschriften, blasse Stempel, Datumzeilen.

4. **LESEREIHENFOLGE**: Vergib reading_order (1, 2, 3, ...) gemaess natuerlichem Lesefluss.

5. **LABELS**: Deutsches Label pro Region (z.B. "Briefanrede", "Haupttext", "Unterschrift Stefan Zweig").

6. **QUALITAET BEWERTEN**: Bewerte dein eigenes Ergebnis — sind alle sichtbaren Textbereiche abgedeckt? Liegen die Regionen praezise? Sind die Typen korrekt?

## Output-Format

Antworte ausschliesslich als JSON:

{
  "regions": [
    {
      "id": "r1",
      "type": "heading",
      "bbox": [25.0, 38.0, 29.0, 6.0],
      "reading_order": 1,
      "lines": 1,
      "label": "Anrede",
      "source": "surya"
    },
    {
      "id": "r2",
      "type": "paragraph",
      "bbox": [22.0, 45.0, 35.0, 25.0],
      "reading_order": 2,
      "lines": 8,
      "label": "Adressblock",
      "source": "merged"
    }
  ],
  "quality": {
    "coverage": "complete",
    "coverage_note": "Alle Textbereiche erfasst.",
    "position_accuracy": "good",
    "type_accuracy": "good",
    "reading_order_ok": true,
    "missing_regions": [],
    "issues": [],
    "overall": "good"
  }
}

## quality-Felder

- **coverage**: "complete" (alle Textbereiche erfasst) | "partial" (einzelne fehlen) | "poor" (wesentliche fehlen)
- **coverage_note**: Kurze Begruendung
- **position_accuracy**: "good" (praezise) | "acceptable" (ungefaehr) | "poor" (daneben)
- **type_accuracy**: "good" (alle korrekt) | "acceptable" (kleine Fehler) | "poor" (systematisch falsch)
- **reading_order_ok**: true | false
- **missing_regions**: Array von fehlenden Bereichen (leer wenn coverage=complete)
- **issues**: Array von Problemen (leer wenn alles gut)
- **overall**: "good" (kein Eingriff noetig) | "acceptable" (brauchbar) | "needs_correction" (wesentliche Fehler)

## REGELN

- Koordinaten aus Docling/Surya NICHT aendern — sie sind pixelgenau korrekt.
- Wenn du Surya-Zeilen gruppierst: Die Bbox der Gruppe = umschliessende Bbox aller Zeilen.
- Fuer NEUE Regionen (Luecken): Bbox in Prozent des GESAMTEN Bildes angeben (inkl. Scan-Hintergrund).
- "source" pro Region: "docling" | "surya" | "merged" (Kombination beider) | "vlm_added" (neu)
- Leere Seiten (keine Regionen in beiden Analysen): Leeres regions-Array zurueckgeben.
- **KEINE UEBERLAPPUNG**: Regionen duerfen sich NICHT ueberlappen. Wenn zwei CV-Regionen ueberlappen, erzeuge EINE zusammengefasste Region mit der umschliessenden Bbox.
- **MINIMALE REGIONSGROESSE**: Eine Region muss mindestens 2 Textzeilen oder eine klar abgegrenzte semantische Einheit (Ueberschrift, Seitenzahl, Unterschrift) enthalten. Einzelne Korrekturzeilen zwischen zwei Absaetzen sind KEINE eigene Region — sie gehoeren zum darunterliegenden Absatz.
- **SCAN-HINTERGRUND IST KEIN TEXT**: Der graue/dunkle Bereich ausserhalb des Dokuments (Scan-Hintergrund) enthaelt KEINEN Text. Erstelle dort KEINE Regionen. Marginalia sind handschriftliche Notizen am Rand DES DOKUMENTS, nicht am Rand des Scans.
```
