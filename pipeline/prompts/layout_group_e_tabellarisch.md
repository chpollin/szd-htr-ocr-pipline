# Layout-Gruppen-Prompt E: Tabellarisch (Schicht 2)

Layout-spezifische Anweisungen fuer tabellarische Dokumente (Register, Verzeichnisse, Kalender, Kontorbuecher).

```
## Dokumenttyp-Layout

Tabellarisches Dokument mit Spalten- und Zeilenstruktur. Typisch: Vorgedruckte Raster mit handschriftlichen Eintraegen.

## Erwartete Regionen

- **table**: Hauptelement. Jede zusammenhaengende Tabelle ist EINE Region. Vorgedrucktes Raster + handschriftliche Eintraege bilden eine gemeinsame Region.
- **heading**: Spaltenueberschriften (wenn als eigene Zeile ueber der Tabelle), Seitentitel, Registername, Jahreszahl.
- **paragraph**: Freitextbereiche ausserhalb der Tabelle (selten).
- **list**: Registereintraege ohne Tabellenstruktur (z.B. alphabetische Namenslisten mit Einrueckung).
- **marginalia**: Anmerkungen am Rand ausserhalb der Tabellenstruktur.

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild.

- Tabellen nutzen oft fast das gesamte Papier. Papier beginnt typisch bei x=10–20, y=5–15.
- Tabellen: x=15–22, breite=55–70, hoehe=50–75%.
- Spaltenueberschriften oben: y=10–18, gleiche Breite wie die Tabelle.
- Kontorbuecher: Vorgedruckte Linien bilden ein Raster — die gesamte Tabelle ist EINE Region.

## Besonderheiten

- Mehrere Tabellen auf einer Seite: Jede als eigene table-Region mit eigenem reading_order.
- Spaltenkoepfe die fest zur Tabelle gehoeren (gleiche Breite, direkt darueber): Als Teil der table-Region erfassen, nicht als separates heading.
- Spaltenkoepfe die als eigenstaendiger Titel ueber der Tabelle stehen: Als heading-Region erfassen.
- Handschriftliche Eintraege in vorgedrucktem Raster: Zusammen als EINE table-Region.
- Leere Tabellenzeilen: Gehoeren zur table-Region (nicht abschneiden).
```
