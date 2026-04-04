# Layout-Verifikation (Stufe 3)

Bewertet die Qualitaet der Layout-Erkennung als Ganzes.
Wird von `layout_analysis.py` (Stufe 3) verwendet.

```
Du erhaeltst ein Dokumentbild und eine Liste von Textregionen mit Bounding Boxes. Bewerte die Qualitaet der Layout-Erkennung.

## Bewertungskriterien

1. **ABDECKUNG**: Sind alle sichtbaren Textbereiche im Bild durch Regionen abgedeckt?
   - "complete": Alle Textbereiche sind erfasst.
   - "partial": Die meisten Textbereiche sind erfasst, aber einzelne fehlen.
   - "poor": Wesentliche Textbereiche fehlen.

2. **POSITION**: Liegen die Regionen tatsaechlich ueber dem Text im Bild?
   - "good": Alle Regionen liegen praezise ueber dem Text.
   - "acceptable": Regionen liegen ungefaehr richtig, aber nicht pixelgenau.
   - "poor": Regionen liegen deutlich neben dem Text.

3. **TYPEN**: Sind die Regionentypen (paragraph, heading, list, table, marginalia) plausibel?
   - "good": Alle Typen korrekt.
   - "acceptable": Kleinere Fehlklassifikationen.
   - "poor": Systematische Fehlklassifikation.

4. **LESEREIHENFOLGE**: Entspricht die reading_order dem natuerlichen Lesefluss?

## Regionen

{regions_json}

## Output-Format

Antworte ausschliesslich als JSON:

{
  "coverage": "complete",
  "coverage_note": "Alle Textbereiche erfasst.",
  "position_accuracy": "good",
  "type_accuracy": "good",
  "reading_order_ok": true,
  "missing_regions": [],
  "issues": [],
  "overall": "good"
}

## Werte fuer "overall"

- "good": Layout-Erkennung ist korrekt und vollstaendig. Kein manueller Eingriff noetig.
- "acceptable": Kleinere Maengel, aber fuer die weitere Verarbeitung brauchbar.
- "needs_correction": Wesentliche Fehler — manuelle Korrektur oder erneute Analyse empfohlen.
```
