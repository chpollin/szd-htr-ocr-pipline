# Layout-Gruppen-Prompt F: Korrekturfahne (Schicht 2)

Layout-spezifische Anweisungen fuer Korrekturfahnen (Druckfahnen mit handschriftlichen Korrekturen).

```
## Dokumenttyp-Layout

Korrekturfahne (Druckfahne): Schmales, hohes Druckformat mit gedrucktem Basistext und handschriftlichen Korrekturen. Das Fahnenformat ist typischerweise schmaler als eine normale Buchseite.

## Erwartete Regionen

- **paragraph**: Gedruckter Basistext. Jeder Absatz des gedruckten Textes ist eine eigene Region. Bei langen Fahnen kann ein einzelner Absatz 30–50% der Seitenhoehe einnehmen.
- **heading**: Artikelueberschriften, Kapitelueberschriften, Zwischentitel im Drucktext.
- **marginalia**: Handschriftliche Korrekturen am Rand — Einfuegungen, Streichungen, Ersetzungen. Korrekturzeichen und ihre Aufloesung am Rand sind marginalia.
- **list**: Selten. Nur bei expliziten Aufzaehlungen im Drucktext.

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild.

- Drucktext: x=25–35, breite=35–50. Korrekturfahnen sind schmaler als Normaldokumente.
- Marginalien links: x=15–22, breite=8–15.
- Marginalien rechts: x=65–80, breite=8–15.
- Der Drucktext kann fast die gesamte Papierhoehe einnehmen: hoehe=50–70%.

## Besonderheiten

- Interlineare Korrekturen (zwischen den Druckzeilen): Gehoeren zur paragraph-Region des umgebenden Textes, nicht eigene Region.
- Marginale Korrekturen mit Einfuegungszeichen: Als marginalia-Region erfassen. Im Label die Art der Korrektur erwaehnen (z.B. "Einfuegung", "Streichung", "Ersetzung").
- Fahnen koennen sehr lang sein — eine einzelne paragraph-Region kann 50%+ der Seitenhoehe ausmachen. Das ist korrekt.
- Satzspiegelmarkierungen und Druckereianweisungen: Im Label erwaehnen.
```
