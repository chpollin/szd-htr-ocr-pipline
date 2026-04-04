# Layout-Gruppen-Prompt A: Handschrift (Schicht 2)

Layout-spezifische Anweisungen fuer handschriftliche Dokumente (Tagebuecher, Notizbuecher, Manuskripte).

```
## Dokumenttyp-Layout

Handschriftliches Dokument (Manuskript, Tagebuch, Notizbuch). Das Layout ist unregelmaessig — Raender, Zeilenabstaende und Textdichte variieren stark.

## Erwartete Regionen

- **paragraph**: Haupttext-Bloecke. Bei Tagebueachern kann eine Seite mehrere Absaetze mit unterschiedlichem Datum enthalten.
- **heading**: Datumzeilen (z.B. "15. Mai 1935"), Ueberschriften, Kapitelmarkierungen. Oft am oberen Seitenrand oder als Trenner zwischen Abschnitten.
- **marginalia**: Randnotizen in anderer Tinte oder Bleistift. Stefan Zweig nutzte oft violette Tinte fuer den Haupttext und Bleistift fuer spaetere Ergaenzungen.
- **list**: Selten — nur bei expliziten Aufzaehlungen oder Notizlisten.

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild, nicht nur zum Papier. Das Papier beginnt typischerweise bei x=15–25, y=10–20.

- Haupttext: x=20–30, breite=40–60. Handschrift nutzt oft nicht die volle Papierbreite.
- Raender sind unregelmaessig — der Text kann nach rechts driften oder am Seitenende enger werden.
- Randnotizen: x=15–22 (links neben dem Haupttext), breite=5–12.
- Zeilenhoehe variiert: 1.5–3.5% pro Zeile (groesser als bei Typoskript).

## Besonderheiten

- Interlinear-Ergaenzungen (Text zwischen den Zeilen eingefuegt) sind KEINE eigene Region — sie gehoeren zum darunterliegenden Absatz.
- Durchgestrichener Text gehoert zur Region des umgebenden Textes.
- Zeichnungen oder Skizzen: erwaehne sie im Label, aber erstelle keine eigene Region.
- Tinte-Wechsel (violett → Bleistift) kann auf verschiedene Schreibsitzungen hindeuten — im Label erwaehnen.
```
