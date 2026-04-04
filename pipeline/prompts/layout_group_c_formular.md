# Layout-Gruppen-Prompt C: Formular (Schicht 2)

Layout-spezifische Anweisungen fuer Formulare (Urkunden, Bankdokumente, Amtsformulare).

```
## Dokumenttyp-Layout

Vorgedrucktes Formular mit handschriftlich oder maschinell ausgefuellten Feldern. Typisch: Mischung aus gedruckter Struktur und handschriftlichem Inhalt.

## Erwartete Regionen

- **heading**: Vorgedruckte Formulartitel, Abschnittsbezeichnungen, Feldlabels die als eigene Zeile erscheinen (z.B. "Name:", "Datum:", "Betrag:").
- **paragraph**: Ausgefuellte Formularbereiche mit mehrzeiligem Text. Ein Formularfeld mit seinem ausgefuellten Inhalt bildet EINE Region (nicht Label und Inhalt getrennt).
- **table**: Formularteile mit tabellarischer Struktur (z.B. Kontoauszuege mit Spalten: Datum | Buchungstext | Betrag).
- **list**: Ankreuzfelder, Checkboxen, kurze Aufzaehlungen.
- **marginalia**: Handschriftliche Anmerkungen ausserhalb der Formularstruktur.

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild.

- Formulare sind oft dicht bedruckt. Das Papier beginnt typisch bei x=15–22, y=10–15.
- Formularfelder: x=18–25, breite=50–65, hoehe=2–6% pro Feld.
- Tabellarische Bereiche koennen 30–55% der Bildhoehe einnehmen.
- Kopfbereich (Institution, Logo): y=12–18.

## Besonderheiten

- Vorgedruckter Text und handschriftlicher Inhalt innerhalb desselben Feldes bilden EINE Region.
- Stempel (Amtsstempel, Datumsstempel): Im Label erwaehnen, keine eigene Region.
- Leere Formularfelder: Nicht als Region erfassen (nur Felder mit Inhalt).
- Bankdokumente: Betraege und Saldospalten als table-Region erfassen.
```
