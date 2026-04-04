# Layout-Gruppen-Prompt H: Zeitungsausschnitt (Schicht 2)

Layout-spezifische Anweisungen fuer Zeitungsausschnitte und gedruckte Artikel.

```
## Dokumenttyp-Layout

Zeitungsausschnitt oder gedruckter Artikel. Typisch: Mehrspaltiges Layout, gedruckter Text, moeglicherweise handschriftliche Annotationen.

## Erwartete Regionen

- **paragraph**: Jede Textspalte ist eine eigene paragraph-Region. Bei zweispaltigem Layout: 2 paragraph-Regionen nebeneinander. Lesereihenfolge: linke Spalte zuerst, dann rechte.
- **heading**: Artikelueberschrift (oft ueber die volle Breite), Zwischenueberschriften, Autorenzeile/Byline.
- **marginalia**: Handschriftliche Anmerkungen von Stefan Zweig am Rand des Ausschnitts.
- **list**: Selten. Nur bei expliziten Aufzaehlungen im Artikel.

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild. Zeitungsausschnitte liegen typisch in der Mitte des Scans.

Einspaltiger Artikel:
- Ueberschrift: x=20–28, breite=45–60, y=12–18.
- Textblock: x=20–28, breite=45–60.

Zweispaltiger Artikel:
- Ueberschrift: x=18–25, breite=50–65.
- Linke Spalte: x=18–25, breite=22–30.
- Rechte Spalte: x=45–55, breite=22–30.

- Handschriftliche Randnotizen: x=12–18 oder x=75–85, breite=5–8.

## Besonderheiten

- Ausschnittgrenzen: Der Zeitungsausschnitt ist oft nicht seitendeckend — der Text kann in der Mitte des Bildes beginnen. Regionen nur dort setzen, wo tatsaechlich Text ist.
- Frakturschrift: Layout trotzdem erfassen — der Schrifttyp aendert nichts am Layout.
- Spaltentrenner (vertikale Linien): Implizit — die Regionen nebeneinander reichen aus.
- Artikeltrenner (horizontale Linien): Koennen auf zwei getrennte Artikel hindeuten — dann separate heading + paragraph Gruppen.
- Bildunterschriften: Als heading-Region erfassen, wenn unter einem Foto/Illustration.
```
