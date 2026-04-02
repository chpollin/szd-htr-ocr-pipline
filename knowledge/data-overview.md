---
title: "Datengrundlage"
aliases: ["Datenanalyse"]
created: 2026-03-30
updated: 2026-04-01
type: analysis
status: stable
related:
  - "[[verification-concept]]"
  - "[[pilot-design]]"
  - "[[journal]]"
---

# Datengrundlage: TEI-Metadaten aller Sammlungen

## Ueberblick

4 Sammlungen, ~2107 Objekte im Backup, TEI-XML als primaere Metadatenquelle.

| Sammlung | TEI-Eintraege | mit PID | Backup-Objekte | TEI-Datei |
|---|---|---|---|---|
| Lebensdokumente | 143 | 120 | ~127 | `szd_lebensdokumente_tei.xml` |
| Werke | 352 | 162 | ~169 | `szd_werke_tei.xml` |
| Aufsatzablage | 624 | 624 | ~625 | `szd_aufsatzablage_tei.xml` |
| Korrespondenzen | 723 | 0 | ~1186 | `szd_korrespondenzen_tei.xml` |
| **Gesamt** | **1842** | **906** | **~2107** | |

TEI-Quellen heruntergeladen am 30.03.2026 von https://stefanzweig.digital/.

---

## 1. Lebensdokumente

**Quelle:** `data/szd_lebensdokumente_tei.xml` — 143 Eintraege, 120 mit PID.

### Klassifikationen

| Klassifikation | Anzahl | Anteil |
|---|---|---|
| Verlagsvertraege | 61 | 43% |
| Rechtsdokumente | 21 | 15% |
| Diverses | 14 | 10% |
| Bueromaterialien | 13 | 9% |
| Tagebuecher | 12 | 8% |
| Verzeichnisse | 9 | 6% |
| Kalender | 6 | 4% |
| Finanzen | 4 | 3% |
| Abschiedsbrief | 2 | 1% |
| Adressbuecher | 1 | 1% |

### Sprachen

Deutsch (86), Englisch (23), Franzoesisch (13), Deutsch? (10), unbekannt (7), Italienisch (2), Spanisch (2). Mehrsprachigkeit haeufig implizit: Verlagsvertraege in Sprache des Verlagslands, deutsche Ergaenzungen.

### Objekttypen

| Objekttyp | Anzahl | Transkriptions-Relevanz |
|---|---|---|
| Typoskript | 38 | Maschinenschrift, gut lesbar |
| Typoskriptdurchschlag | 36 | Oft blasser |
| Notizbuch | 12 | Handschrift Zweig, Hauptherausforderung |
| Karte | 8 | Kurztexte, gemischt |
| Manuskript | 7 | Handschrift, variabel |
| Kalender | 6 | Druck + handschriftliche Eintraege |
| Register | 3 | Tabellarisch, handschriftlich |
| Sonstige | ~33 | Druck, Scheckheft, Passkopie, Urkunde, Umschlaege etc. |

### Haende

Stefan Zweig (98), fremde Hand (50), Lotte Zweig (19), Ben Huebsch (5), Eugen Relgis (5), Halfdan Jespersen (3), Lotte Altmann (3), Anna Meingast (2), Friderike Zweig (2).

### Schreibinstrumente

Violette Tinte (Zweigs Standard), Bleistift (Annotationen), Buntstifte (blau, rot, gruen — Markierungen), schwarzes/violettes Farbband (Typoskripte), Durchschlagpapier.

### Physische Metadaten in TEI

Pro Objekt: `<material ana="szdg:WritingMaterial">` (Papierart), `<material ana="szdg:WritingInstrument">` (Schreibinstrument), `<extent>` (Blattanzahl), `<measure type="format">` (Masse), `<foliation>`, `<handDesc>`, `<bindingDesc>`, `<accMat>` (Beilagen).

---

## 2. Werke (Manuskripte)

**Quelle:** `data/szd_werke_tei.xml` — 352 Eintraege, 162 mit PID.

### Klassifikationen

| Klassifikation | Anzahl | mit PID | Anteil |
|---|---|---|---|
| Essays/Reden/Feuilletons | 164 | 75 | 47% |
| Biographien | 86 | 26 | 24% |
| Romane/Erzaehlungen | 65 | 32 | 18% |
| Buehnenwerke/Filme | 12 | 0 | 3% |
| Werknotizen | 10 | 9 | 3% |
| Autobiographisches | 8 | 5 | 2% |
| Gedichte | 6 | 3 | 2% |
| Uebersetzungen | 1 | 0 | <1% |

### Sprachen

Deutsch (304), Englisch (27), Franzoesisch (17), Italienisch (2), Jiddisch (1), Spanisch (1). Primaer Deutsch (86%).

### Objekttypen

| Objekttyp | Anzahl | Transkriptions-Relevanz |
|---|---|---|
| Typoskriptdurchschlag | 113 | Maschinenschrift, oft blass |
| Typoskript | 67 | Maschinenschrift, gut lesbar |
| Manuskript | 65 | Handschrift — Hauptherausforderung |
| Korrekturfahne | 43 | Gedruckter Text + handschriftliche Korrekturen |
| Notizbuch | 26 | Handschrift, fliessender Text |
| Konvolut | 24 | Gemischte Materialien |
| Sonstige | ~14 | Umschlaege, Zeitungsausschnitte, Postkarten |

### Haende

Stefan Zweig (193), Lotte Zweig (83), fremde Hand (53), Richard Friedenthal (18), Friderike Zweig (3), Anna Meingast (3).

### Vergleich: Lebensdokumente vs. Werke

| Merkmal | Lebensdokumente (143) | Werke (352) |
|---|---|---|
| Hauptkategorie | Verlagsvertraege (43%) | Essays (47%) |
| Dominanter Objekttyp | Typoskript/Durchschlag | Typoskript/Durchschlag |
| Handschrift-Anteil | 12 Notizbuecher (8%) | 65 Manuskripte + 26 Notizbuecher (26%) |
| Besonderheit | Formulare, Urkunden | Korrekturfahnen (43), Konvolute (24) |
| Sprache | Mehrsprachiger | Primaer Deutsch (86%) |

---

## 3. Aufsatzablage

**Quelle:** `data/szd_aufsatzablage_tei.xml` — 624 Eintraege, alle mit PID. Zweigs persoenliche Sammlung von Presseausschnitten, Registern und Arbeitsmaterialien.

### Klassifikationen

| Klassifikation | Anzahl | Anteil |
|---|---|---|
| Zeitungsausschnitte | 317 | 51% |
| Registerblaetter | 207 | 33% |
| Typoskripte | 56 | 9% |
| Register | 25 | 4% |
| Manuskripte | 7 | 1% |
| Druckfahnen | 6 | 1% |
| Druckschriften | 3 | <1% |
| Korrekturfahnen | 2 | <1% |
| Separatdruck | 1 | <1% |

### Objekttypen

Zeitungsausschnitt (312), Manuskript (213), Typoskript (44), Typoskriptdurchschlag (34), Druckfahne (6), Korrekturfahne (4).

### Sprachen

Primaer Deutsch (599), Franzoesisch (9), Englisch (6), Italienisch (3).

### Haende

Unbekannt (391), **Erwin Rieger** (225 — Zweigs Sekretaer, hat die Registerblaetter angelegt), Lotte Zweig (46), Richard Friedenthal (24), Stefan Zweig (24).

### Besonderheit: Zeitungsausschnitte

312 Zeitungsausschnitte — voellig eigener Dokumenttyp: Gedruckter Text in verschiedenen Zeitungsschriften (oft Fraktur), verschiedene Layouts (Spalten, Ueberschriften), teils mit handschriftlichen Annotationen.

---

## 4. Korrespondenzen

**TEI-Quelle:** `data/szd_korrespondenzen_tei.xml` — 723 Eintraege, NUR Korrespondenz-Metadaten (`<correspDesc>`: wer schrieb an wen, wann). Keine physischen Beschreibungen, keine PIDs.

**Backup-Quelle:** `szd-backup/data/korrespondenzen/` — **1186 Objekte** mit metadata.json und Bildern.

### Charakteristika

- Primaer handschriftliche **Briefe** (Zweigs Hand, violette Tinte)
- Mit Abstand groesste Sammlung (1186 Objekte)
- Keine TEI-Klassifikation — Dokumenttypen aus Titeln ableitbar: Brief, Postkarte, Telegramm, Visitenkarte
- Kontextinformation kommt aus Backup-metadata.json (Titel, Sprache, Bildliste, GAMS-URLs)

### Beispiel-Objekt

```json
{
  "object_id": "o:szd.1079",
  "title": "Brief an Max Fleischer vom 22. Mai 1901, SZ-LAS/B3.1",
  "language": "Deutsch",
  "images": ["5 Bilder, je 4912x7360px"]
}
```

---

## 5. Prompt-Gruppen (A–I)

Konsolidierte Master-Tabelle aller 9 Gruppen, abgeleitet aus der TEI-Analyse.

| Gruppe | Name | Population (ca.) | Quell-Sammlungen | Hauptherausforderung |
|---|---|---|---|---|
| **A** | Handschrift | ~100 | LD, W | Kurrent, violette Tinte, Abkuerzungen |
| **B** | Maschinenschrift | ~300 | LD, W, AA | Typoskripte, Durchschlaege (oft blass), mehrsprachig |
| **C** | Formular/Urkunde | ~25 | LD | Druck + Handschrift gemischt, tabellarisch |
| **D** | Kurztext | ~30 | LD | Heterogen, wenig Text |
| **E** | Tabellarisch | ~230 | LD, AA | Register, Kalender, Verzeichnisse, Datumseintraege |
| **F** | Korrekturfahne | ~55 | W, AA | Gedruckter Text + handschriftliche Korrekturen |
| **G** | Konvolut | ~24 | W | Gemischte Materialien, Materialwechsel zwischen Seiten |
| **H** | Zeitungsausschnitt | ~312 | AA | Gedruckt, Fraktur und Antiqua, verschiedene Layouts |
| **I** | Korrespondenz | ~1186 | K | Handschriftliche Briefe, Briefkonventionen |

LD = Lebensdokumente, W = Werke, AA = Aufsatzablage, K = Korrespondenzen.

Gruppenzuordnung automatisch via `resolve_group()` in `pipeline/tei_context.py`. Prompt-Dateien: `pipeline/prompts/group_{a-i}_*.md`.

## 6. Haende im Nachlass

| Hand | Sammlungen | Charakter |
|---|---|---|
| **Stefan Zweig** | Alle | Dominant, violette Tinte, lateinisch mit Kurrenteinfluessen |
| **Lotte Zweig** | LD, W, AA | Zweithaeufigst bei Werken |
| **Erwin Rieger** | AA | 225 Registerblaetter |
| **Richard Friedenthal** | W, AA | |
| **Friderike Zweig** | LD, W | |
| fremde Haende | Alle | Verleger, Behoerden, Sekretaere |

## 7. Nutzen fuer die Pipeline

Die TEI-Metadaten liefern pro Objekt automatischen Kontext fuer den VLM-Prompt (via `pipeline/tei_context.py`):

- **Sprache** → Sprachspezifische Transkriptionshinweise (Kurrent, Akzente, juristische Formeln)
- **Objekttyp** → Prompt-Gruppenzuordnung (Handschrift, Typoskript, Formular etc.)
- **Haende** → Hinweis auf Schriftbild, Multi-Hand-Warnung
- **Schreibinstrument** → Tintenfarbe und Strichstaerke
- **Papierart** → Signalisiert Raster bei kariertem Papier oder Tabellenvordrucken
- **Format/Masse** → Grosse Dokumente (54x38 cm) vs. Karten (12x8 cm)
- **Beilagen** → Eingelegte Manuskripte koennen auf Scans auftauchen
