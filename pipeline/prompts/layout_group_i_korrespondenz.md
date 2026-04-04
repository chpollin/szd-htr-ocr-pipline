# Layout-Gruppen-Prompt I: Korrespondenz (Schicht 2)

Layout-spezifische Anweisungen fuer Korrespondenz (Briefe, Postkarten, Telegramme).

```
## Dokumenttyp-Layout

Brief, Postkarte oder Telegramm. Briefe haben eine charakteristische Struktur mit festgelegten Layoutzonen.

## Erwartete Regionen (Brief)

Typische Reihenfolge (reading_order):
1. **heading**: Briefkopf/Letterhead (wenn vorhanden, oft gedruckt, oben zentriert oder links)
2. **heading**: Datumzeile (oben rechts, z.B. "Salzburg, 15. Mai 1935")
3. **heading**: Anrede (z.B. "Lieber Max!", "Sehr geehrter Herr Doktor")
4. **paragraph**: Brieftext — 1 bis 3 Absaetze, Hauptteil des Dokuments
5. **heading**: Grussformel (z.B. "Herzlichst Ihr", "Mit besten Gruessen")
6. **heading**: Unterschrift
7. **paragraph**: Postskriptum (PS), falls vorhanden

## Erwartete Regionen (Postkarte)

- Nachrichtenseite: heading (Anrede) + paragraph (Nachricht) + heading (Unterschrift)
- Adressseite: heading (Adressfeld) — oft vorgedruckte Linien

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild. Briefe und Umschlaege liegen typisch in der Mitte des Scans mit grauem Hintergrund drumherum.

Brief (Papier beginnt ca. bei x=18–25, y=10–18):
- Briefkopf: x=22–35, y=12–18, breite=35–55.
- Datumzeile: x=45–65, y=15–22, breite=18–30. Rechtsbuendig.
- Anrede: x=22–30, y=22–28, breite=25–40.
- Brieftext: x=22–30, y=28–70, breite=45–55. Groesste Region.
- Grussformel: x=22–30, y=65–75, breite=25–40.
- Unterschrift: x=25–35, y=72–82, breite=20–35.

Postkarte/Umschlag:
- Adressfeld: x=30–45, y=30–55, breite=30–40.
- Stempel-Bereich im Label erwaehnen, keine eigene Region.

## Besonderheiten

- Briefstruktur beibehalten: Jedes Strukturelement (Datum, Anrede, Gruss, Unterschrift) als eigene heading-Region, auch wenn es nur eine Zeile ist.
- Postscriptum: Als paragraph-Region nach der Unterschrift.
- Briefkopf (gedruckt): Eigene heading-Region, im Label "Briefkopf, gedruckt" vermerken.
- Adressfeld auf Umschlaegen/Postkarten: Als heading-Region.
- Poststempel: Im Label erwaehnen, keine eigene Region.
```
