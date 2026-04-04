# Layout-Gruppen-Prompt D: Kurztext (Schicht 2)

Layout-spezifische Anweisungen fuer Kurztexte (Visitenkarten, Einladungen, Widmungen, Tickets).

```
## Dokumenttyp-Layout

Dokument mit wenig Text — Visitenkarte, Einladung, Widmung, Ticket, Exlibris. Der Text nimmt oft nur einen kleinen Teil der Seitenflaeche ein.

## Erwartete Regionen

- **heading**: Titel, Name, Veranstaltungsname. Oft das prominenteste Textelement.
- **paragraph**: Detailtext (Adresse, Datum, Beschreibung). Wenige Zeilen.
- **list**: Selten. Nur bei expliziten Aufzaehlungen.
- **marginalia**: Handschriftliche Ergaenzungen auf gedruckten Karten.

## Koordinaten-Richtwerte

WICHTIG: Koordinaten relativ zum GESAMTEN Scan-Bild. Bei kleinen Dokumenten (Karten, Tickets) liegt das Objekt oft in der Mitte des Scans.

- Wenige Regionen pro Seite: typischerweise 1–3.
- Text kann zentriert sein: x=25–40, breite=20–50.
- Das Dokument belegt oft nur 40–60% des Scan-Bildes.
- Visitenkarten: Kompakter Text, x=25–35, breite=30–50.
- Die Regionen muessen NICHT das ganze Bild abdecken — nur den tatsaechlich beschriebenen Bereich erfassen.

## Besonderheiten

- Bei Recto/Verso-Dokumenten: Jede Seite einzeln analysieren. Die Rueckseite kann leer sein oder wenig Text haben.
- Gedruckter Kleintext (Druckereivermerk, Copyright): Als eigene paragraph-Region erfassen, wenn lesbar.
- Dekorative Elemente (Rahmen, Ornamente): Im Label erwaehnen, keine eigene Region.
- Die Regionen koennen klein sein (breite 30–50%) — das ist korrekt fuer diesen Dokumenttyp.
```
