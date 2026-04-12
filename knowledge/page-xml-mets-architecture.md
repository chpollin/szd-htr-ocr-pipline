---
title: "PAGE XML, Metadaten und METS-Architektur"
aliases: ["METS-Architektur", "PAGE XML", "Ausgabeformate"]
created: 2026-04-03
updated: 2026-04-12
type: concept
status: stable
related:
  - "[[htr-interchange-format]]"
  - "[[layout-analysis]]"
  - "[[data-overview]]"
---

# PAGE XML, Metadaten und METS-Architektur

Wissensdokument zur Schichtenarchitektur der OCR/HTR-Datenmodellierung. Durchgaengiges Beispiel aus dem Projekt *Stefan Zweig Digital* (Literaturarchiv Salzburg, GAMS-Infrastruktur, Universitaet Graz).

## 1. PAGE XML als Layoutschicht

PAGE XML (Page Analysis and Ground-truth Elements) ist das Standardformat fuer Layout-Analyse und Texterkennungsergebnisse. Entwickelt im PRImA-Projekt (University of Salford), aktuelles Schema 2019-07-15.

Das Format modelliert eine hierarchische Struktur pro Seitenbild. Die oberste Ebene bildet das `Page`-Element mit Referenz auf das Rasterbild. Darunter ordnen sich Regionen ein (`TextRegion`, `ImageRegion`, `TableRegion`, `SeparatorRegion`), jeweils ueber Polygonkoordinaten (`Coords`) auf dem Bild verortet. Innerhalb von `TextRegion` folgt die Schachtelung `TextLine` → `Word` → `Glyph`, wobei jede Ebene eigene Koordinaten und ein `TextEquiv`-Element fuer den erkannten Text tragen kann. Konfidenzwerte lassen sich pro Ebene als Attribut mitfuehren.

PAGE XML ist das native Format in den meisten aktuellen HTR/OCR-Werkzeugen. Transkribus arbeitet damit, ebenso OCR-D (DFG-Koordinierungsprojekt zur Volltextdigitalisierung historischer Drucke), Kraken/eScriptorium und LAREX. In der SZD-HTR-OCR-Pipeline werden PAGE-XML-Dateien pro Seite aus den VLM-Transkriptionsergebnissen exportiert (`export_pagexml.py`).

### Metadaten in PAGE XML

Das `Metadata`-Element erfasst ausschliesslich Prozessmetadaten (Tool, Zeitstempel, Kommentare). Es beantwortet die Frage „Wie wurde diese Datei erzeugt?", nicht „Was ist dieses Dokument?".

Daneben existiert das `custom`-Attribut auf fast allen Elementen. Transkribus nutzt es fuer Strukturtagging (`structure {type:heading;}`) oder Schreiberhand-Markierung auf Regionenebene. Das sind Freitext-Schluessel-Wert-Paare ohne Schemavalidierung, ein pragmatischer Workaround, keine saubere Modellierung.

Deskriptive Metadaten (Schreiberhand, Schreibstoff, Datierung, Dokumententyp) gehoeren konzeptuell zu einer anderen Schicht und werden in PAGE XML bewusst nicht modelliert.

## 2. Warum XML und nicht JSON?

Die gleiche Information liesse sich in JSON abbilden. Die Wahl von XML ist keine technische Notwendigkeit, sondern eine Oekosystem-Entscheidung mit funktionalen Konsequenzen.

**Schema-Validierung als Qualitaetssicherung.** PAGE XML hat ein XSD-Schema, gegen das jede Datei validiert werden kann. In einem Kontext, in dem Ground-Truth-Daten zwischen Institutionen ausgetauscht werden, muss strukturelle Korrektheit maschinell pruefbar sein.

**Attribut-Element-Unterscheidung.** XML trennt strukturell zwischen Attributen (Metadaten ueber ein Element, etwa `confidence="0.92"`) und Kindknoten (inhaltliche Bestandteile, etwa `TextLine` in `TextRegion`). JSON kennt diese Unterscheidung nicht, alles wird zu Schluessel-Wert-Paaren auf derselben Ebene.

**Namespace-Mechanismus und Oekosystem-Integration.** PAGE XML operiert in einem Oekosystem mit METS, ALTO, TEI und anderen XML-Standards. Namespaces erlauben die Kombination dieser Vokabulare ohne Namenskollisionen. XSLT-Transformationen zwischen PAGE und ALTO oder PAGE und TEI sind direkt moeglich.

**Was JSON besser kann.** JSON ist kompakter, parsing-effizienter und fuer webbasierte Anwendungen die natuerlichere Wahl. In der SZD-Pipeline werden die Transkriptionsergebnisse intern als JSON gespeichert und erst fuer den Export nach PAGE XML transformiert.

## 3. Deskriptive Metadaten und die Grenze von PAGE XML

PAGE XML modelliert die physische Layoutstruktur einer einzelnen Seite. Deskriptive Metadaten (Schreibstoff, Datierung, Schreiberhand, Dokumententyp) beschreiben das Dokument als Ganzes. Die Trennung dieser Schichten folgt dem Prinzip *separation of concerns*. Die Vermischung beider Ebenen in einer Datei funktioniert bei einzelnen Dokumenten pragmatisch, skaliert aber schlecht und widerspricht der Interoperabilitaet des gesamten Stacks.

## 4. METS als Container-Architektur

METS (Metadata Encoding and Transmission Standard) loest das Metadatenproblem architektonisch, indem es drei Funktionen uebernimmt:

- **Deskriptive Metadaten tragen** (`dmdSec` mit MODS, Dublin Core oder anderen Vokabularen)
- **Dateien referenzieren** (`fileSec` mit Verweisen auf Bilder und PAGE-XML-Dateien)
- **Struktur definieren** (`structMap` als physische und/oder logische Gliederung)

### Schichtenarchitektur

| Schicht | Format | Frage |
|---|---|---|
| Deskriptive Metadaten | MODS (in METS `dmdSec`) | Was ist dieses Dokument? |
| Seitenlayout und OCR | PAGE XML | Was steht wo auf dieser Seite? |
| Container und Struktur | METS | Wie haengt alles zusammen? |

Diese Trennung ist nicht willkuerlich, sondern folgt *separation of concerns*. Sie ermoeglicht, dass Layout-Ergebnisse ausgetauscht werden koennen, ohne Metadaten mitzuschleppen, und umgekehrt.

### MODS fuer deskriptive Metadaten

MODS bietet dedizierte Elemente fuer die meisten Archiv-Metadaten: `titleInfo`, `name` (mit `role` und Normdaten), `typeOfResource`, `genre`, `originInfo` (Datierung, Ort), `language`, `physicalDescription` (Form, Umfang), `location` (Repository, Signatur, URL), `identifier` (PID). Fuer Schreibstoff und Schreibinstrument nutzt man `physicalDescription/note[@type]` — funktional, aber semantisch schwaecher als ein explizites Element.

### Mapping: TEI-Metadaten → MODS

Die `parse_tei_full_metadata()`-Funktion in `tei_context.py` liefert alle Felder, die fuer MODS benoetigt werden:

| TEI-Feld | MODS-Element |
|---|---|
| title | `titleInfo/title` |
| creators (name, role, gnd) | `name/namePart` + `role/roleTerm` + `nameIdentifier` |
| date | `originInfo/dateCreated` |
| language | `language/languageTerm` |
| objecttyp | `genre` |
| extent | `physicalDescription/extent` |
| writing_instrument | `physicalDescription/note[@type="writing_instrument"]` |
| writing_material | `physicalDescription/note[@type="writing_material"]` |
| hands | `physicalDescription/note[@type="script"]` |
| dimensions | `physicalDescription/extent` (zweites) |
| holding (repository, country, settlement) | `location/physicalLocation` + `location/shelfLocator` |
| signature | `location/shelfLocator` |
| provenance | `note[@type="provenance"]` |
| rights | `accessCondition` |

### Erweiterungsmoeglichkeiten

**Logische Struktur.** Eine zweite `structMap TYPE="LOGICAL"` kann inhaltliche Gliederung (Abschnitte, Eintraege, thematische Bloecke) unabhaengig von der Seitenstruktur abbilden.

**OCR-D-Konventionen.** Im OCR-D-Kontext werden `fileGrp`-Bezeichnungen standardisiert (`OCR-D-IMG`, `OCR-D-GT-PAGE`, `OCR-D-OCR-PAGE`), um die Ergebnisse verschiedener Verarbeitungsschritte zu unterscheiden.

**TEI msDesc als Alternative zu MODS.** Fuer hochstrukturierte physische Beschreibungen waere TEI `msDesc` die ausdrucksstaerkere Alternative, die sich ebenfalls als `mdWrap` in METS einbetten laesst.

## 5. Bezug zur SZD-HTR-OCR-Pipeline

Die Pipeline nutzt zwei komplementaere Ausgabeformate:

- **Page-JSON v0.2** (`*_page.json`): Internes Arbeitsformat. OCR + Layout + deskriptive Metadaten (Dublin Core + Materialtypologie) in einer JSON-Datei. Koordinaten optional. Schema: `schemas/page-json-v0.2.json`. Export: `pipeline/export_page_json.py`.
- **METS/MODS + PAGE XML**: Archiv- und Austauschformat (Zielformat). METS-Container mit MODS-Metadaten und PAGE XML 2019 pro Seite. Kompatibel mit GAMS, Transkribus, eScriptorium, OCR-D, teiCrafter. PAGE XML Export: `pipeline/export_pagexml.py`. METS/MODS-Export: `pipeline/export_mets.py` (implementiert, 2074 Dateien exportiert in Session 25).

Die Architektur demonstriert den Pragmatismus: Intern arbeiten webbasierte und ML-orientierte Workflows besser mit JSON. Fuer die Interoperabilitaet mit dem breiteren DH-Oekosystem wird nach METS/PAGE XML exportiert. GAMS nutzt METS nativ als Containerformat, der Rueckweg ist damit direkt.
