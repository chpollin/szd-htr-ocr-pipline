# Layout-Gruppen-Prompt B: Typoskript (Schicht 2)

Layout-spezifische Anweisungen fuer maschingeschriebene Dokumente (Vertraege, Typoskripte, Durchschlaege).

```
## Dokumenttyp-Layout

Maschingeschriebenes Dokument (Typoskript, Vertrag, Durchschlag). Das Layout ist regelmaessig mit einheitlichen Raendern und Zeilenabstaenden.

## Erwartete Regionen

- **paragraph**: Textabsaetze. Bei Vertraegen: nummerierte Absaetze sind jeweils eigene paragraph-Regionen (nicht list, da mehrzeiliger Prosatext).
- **heading**: Dokumenttitel, Vertragstitel, Abschnittsueberschriften, Datumzeile.
- **list**: Nur bei echten Aufzaehlungen (kurze einzeilige Punkte). Nummerierte Vertragsabsaetze mit mehrzeiligem Text sind paragraph.
- **marginalia**: Handschriftliche Annotationen, Korrekturen oder Anmerkungen am Rand. Oft in anderer Tinte als der Maschinenschrift.

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild, nicht nur zum Papier.

- Haupttext: x=22–30, breite=45–60. Das Papier beginnt typisch bei x=18–25, y=12–18.
- Zeilenhoehe: ca. 1.5–2% pro Zeile (gleichmaessiger Zeilenabstand).
- Unterschriftenblock unten: typisch y=65–80.
- Kopfzeile/Briefkopf oben: y=12–18.

## Besonderheiten

- Durchschlaege (Kopierpapier): Identisches Layout wie das Original, aber blasserer Text. Layout trotzdem vollstaendig erfassen.
- Handschriftliche Ergaenzungen auf Typoskripten: Als marginalia erfassen, wenn am Rand. Wenn direkt im Text (Einfuegungen, Korrekturen), zum umgebenden paragraph zaehlen.
- Stempel und Siegel: Im Label erwaehnen ("Stempel unten links"), keine eigene Region.
```
