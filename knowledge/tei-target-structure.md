---
title: "TEI-Zielstruktur"
aliases: ["TEI-Zielstruktur"]
created: 2026-04-01
updated: 2026-04-01
type: spec
status: draft
related:
  - "[[htr-interchange-format]]"
  - "[[teiCrafter-integration]]"
  - "[[annotation-protocol]]"
  - "[[verification-concept]]"
---

# TEI-Zielstruktur: Transkriptions-TEI fuer den SZD-Nachlass

Abhaengigkeit: [[htr-interchange-format]] (Page-JSON Input), [[teiCrafter-integration]] (Workflow), [[annotation-protocol]] (Markup-Konventionen)

---

## 1. Zweck

Dieses Dokument definiert das TEI-XML-Zielformat fuer transkribierte und annotierte Objekte des Stefan-Zweig-Nachlasses. Es beschreibt, wie die VLM-Transkriptionen (aus der szd-htr-Pipeline) nach der Annotation durch teiCrafter als TEI-XML aussehen sollen.

### 1.1 Zwei TEI-Schichten im SZD

Das SZD-Projekt hat aktuell **eine** TEI-Schicht: Metadaten-Kataloge (`data/szd_*_tei.xml`). Diese enthalten `<biblFull>`-Eintraege pro Objekt in einer `<listBibl>` — keine Transkriptionsinhalte.

Die HTR-Pipeline erzeugt eine **zweite** TEI-Schicht: Transkriptions-TEI mit dem tatsaechlichen Text der Dokumente, strukturiert und annotiert.

| Schicht | Inhalt | Format | Status |
|---|---|---|---|
| **Metadaten-TEI** | Katalog (physische Beschreibung, Signatur, Haende, Material) | `<listBibl>/<biblFull>` pro Sammlung | Bestehend |
| **Transkriptions-TEI** | Text + Struktur + NER pro Objekt | `<text>/<body>` pro Objekt | **Neu (dieses Dokument)** |

Die beiden Schichten werden ueber die PID (`o:szd.NNN`) verknuepft, bleiben aber separate Dateien.

---

## 2. TEI-Profil

### 2.1 Entscheidung: DTABf als Basis

**Empfehlung: DTABf (Deutsches Textarchiv Basisformat)** als Profil fuer die Transkriptions-TEI.

Begruendung:
1. **teiCrafter verwendet DTABf** — das Schema (`dtabf.json`, ~30 Elemente) ist bereits implementiert und validiert.
2. **zbz-ocr-tei setzt DTABf erfolgreich ein** — das Schwesterprojekt hat gezeigt, dass DTABf fuer LLM-annotierte historische Texte funktioniert.
3. **De-facto-Standard** fuer deutschsprachige historische Texte in den Digital Humanities.
4. **Interoperabilitaet** — DTABf-konformes TEI ist kompatibel mit DTA-Infrastruktur und CLARIN.

### 2.2 SZD-Erweiterungen

Das bestehende SZD-TEI verwendet den Custom-Namespace `szdg:` (definiert in `<listPrefixDef>`):

```xml
<prefixDef ident="szdg" matchPattern="([(a-z)|(A-Z)]+)" 
           replacementPattern="szdg:$1">
  <p>Namespace fuer den Glossar in Stefan Zweig Digital.</p>
</prefixDef>
```

Fuer die Transkriptions-TEI werden `szdg:`-Attribute nur verwendet, wenn projektspezifische Semantik noetig ist (z.B. Dokumentklassifikation). Alle Standard-TEI/DTABf-Elemente haben Vorrang.

### 2.3 Element-Inventar

Basierend auf dem teiCrafter-DTABf-Schema plus Erweiterungen fuer diplomatische Transkription:

**Strukturelemente:**
- `<div>` — Hauptstruktur (Brief, Tagebucheintrag, Vertrag)
- `<p>` — Absaetze
- `<head>` — Ueberschriften
- `<pb n="N" facs="URL"/>` — Seitenumbruch mit Faksimile-Link
- `<lb/>` — Zeilenumbruch (optional, nur wenn explizit gewuenscht)
- `<fw>` — Forme Work (Kolumnentitel, Seitenzahlen bei Drucken)
- `<cb/>` — Spaltenumbruch (Zeitungsausschnitte)
- `<table>`, `<row>`, `<cell>` — Tabellen (Gruppe E: Register, Kalender)

**Briefstruktur (Gruppe I):**
- `<opener>` — Briefoeffnung (Dateline + Anrede)
- `<closer>` — Briefschluss (Grussformel + Unterschrift)
- `<dateline>` — Datumszeile
- `<salute>` — Anrede/Gruss
- `<signed>` — Unterschrift
- `<postscript>` — Nachschrift

**Diplomatisches Markup:**
- `<unclear>` — Unsichere Lesung (Pipeline: `[?]` nach Wort)
- `<gap reason="illegible"/>` — Unleserlich (Pipeline: `[...]`)
- `<gap reason="illegible" quantity="N" unit="chars"/>` — Unleserlich mit Schaetzung (Pipeline: `[...N...]`)
- `<del>` — Streichung (Pipeline: `~~text~~`)
- `<add place="above">` — Einfuegung (Pipeline: `{text}`)
- `<stamp>` — Stempel (Pipeline: `[Stempel: text]`)
- `<note place="margin">` — Marginalie (Pipeline: `[Marginalie: text]`)

**Named Entities:**
- `<persName ref="GND:...">` — Personen
- `<placeName ref="GND:...">` — Orte
- `<orgName>` — Organisationen
- `<date when="YYYY-MM-DD">` — Daten
- `<bibl>` — Werkverweise

**Maschinen-Attribute (von teiCrafter gesetzt):**
- `@confidence="high|medium|low"` — LLM-Konfidenz pro Annotation
- `@resp="#machine"` — Kennzeichnung maschineller Annotation

---

## 3. Zielstruktur — XML-Beispiel

Vollstaendiges TEI-XML fuer o_szd.1079 (Brief an Max Fleischer, 22. Mai 1901):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Brief an Max Fleischer vom 22. Mai 1901</title>
        <author ref="http://d-nb.info/gnd/118637479">
          <persName>
            <surname>Zweig</surname>
            <forename>Stefan</forename>
          </persName>
        </author>
      </titleStmt>
      <publicationStmt>
        <publisher>
          <orgName>Literaturarchiv Salzburg</orgName>
        </publisher>
        <distributor>
          <orgName ref="https://gams.uni-graz.at">GAMS</orgName>
        </distributor>
        <availability>
          <licence target="https://creativecommons.org/licenses/by-nc/4.0">
            Creative Commons BY-NC 4.0
          </licence>
        </availability>
        <idno type="PID">o:szd.1079</idno>
      </publicationStmt>
      <sourceDesc>
        <msDesc>
          <msIdentifier>
            <repository>Literaturarchiv Salzburg</repository>
            <idno type="signature">SZ-LAS/B3.1</idno>
            <altIdentifier>
              <idno type="PID">o:szd.1079</idno>
            </altIdentifier>
          </msIdentifier>
        </msDesc>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <correspDesc>
        <correspAction type="sent">
          <persName ref="http://d-nb.info/gnd/118637479">Stefan Zweig</persName>
          <placeName>Wien</placeName>
          <date when="1901-05-22">22. Mai 1901</date>
        </correspAction>
        <correspAction type="received">
          <persName>Max Fleischer</persName>
          <placeName>Komotau</placeName>
        </correspAction>
      </correspDesc>
    </profileDesc>
  </teiHeader>
  <text xml:lang="de">
    <body>
      <!-- Seite 1: Umschlag Vorderseite -->
      <div type="envelope">
        <pb n="1" facs="https://gams.uni-graz.at/o:szd.1079/IMG.1"/>
        <p>Wohlgeboren</p>
        <p><persName confidence="high" resp="#machine">Max Fleischer</persName><lb/>
        Schriftsteller</p>
        <p><placeName confidence="high" resp="#machine">Komotau</placeName><lb/>
        <placeName confidence="high" resp="#machine">Boehmen</placeName></p>
      </div>

      <!-- Seite 2: Umschlag Rueckseite -->
      <div type="envelope-verso">
        <pb n="2" facs="https://gams.uni-graz.at/o:szd.1079/IMG.2"/>
        <p><persName confidence="high" resp="#machine">STEFAN ZWEIG</persName></p>
        <p><stamp>KOMOTAU <date when="1901-05-23" confidence="medium" 
          resp="#machine">23.5.01</date></stamp></p>
      </div>

      <!-- Seite 3: Brieftext -->
      <div type="letter">
        <pb n="3" facs="https://gams.uni-graz.at/o:szd.1079/IMG.3"/>
        <opener>
          <salute>Lieber Herr <persName confidence="high" resp="#machine">Fleischer</persName>!</salute>
        </opener>
        <p>Ich hoffe Sie werden sich als Dichter zu einer
        genuegend hohen Weltauffassung erhoben haben, um sich nicht
        ueber mein graessliches Briefpapier (der letzte Bogen!) zu mokieren!</p>
        <p>Ich danke Ihnen recht herzlich fuer Ihre liebe Kartennotiz. Ihr Buch
        kam mir noch nicht zu, doch las ich es mit aufrichtiger Freude
        bei <persName confidence="medium" resp="#machine">Donath</persName> durch 
        und schrieb eine Kritik ins Residenzblatt,
        die bald erscheint.</p>
        <!-- ... weiterer Text ... -->
        <p>Ihre Absicht mit <persName confidence="medium" resp="#machine">Donath</persName> 
        ist wunderschoen, nur glaube ich nicht dass er nach 
        <placeName confidence="high" resp="#machine">Karlsbad</placeName> wird 
        abkommen koennen, da es so viel wahrscheinlicher, dass Sie mich sehen, der
        ich nun geschlagene 16 Jahre nach 
        <placeName confidence="high" resp="#machine">Marienbad</placeName> gehen muss</p>
        <!-- ... -->
        <p>Nicht einmal Gerichte mehr, die mir zu einem Aufsatz ueber 
        <persName confidence="high" resp="#machine">Franz Evers</persName> 
        (fuer die <bibl confidence="medium" resp="#machine">Stimmen der 
        Gegenwart</bibl>) habe ich mich aufgerafft.</p>
        <closer>
          <!-- Grussformel und Unterschrift auf Seite 4/5 -->
        </closer>
      </div>
    </body>
  </text>
</TEI>
```

**Anmerkungen zum Beispiel:**
- `<teiHeader>` kombiniert Elemente aus dem bestehenden Metadaten-TEI mit neuen Transkriptions-spezifischen Feldern
- `<correspDesc>` entspricht dem bestehenden SZD-Schema fuer Korrespondenzen
- `<pb facs="..."/>` verlinkt direkt auf GAMS-Faksimiles
- NER-Annotationen tragen `@confidence` und `@resp="#machine"` — der Expert-in-the-Loop kann diese im teiCrafter-Preview pruefen und anpassen
- Diplomatische Konventionen: Originaltreue Schreibweise, keine Normalisierung

---

## 4. Diplomatische Transkription → TEI-Mapping

Die Pipeline verwendet ein einfaches Markup-System (definiert in [[annotation-protocol]]). teiCrafter uebersetzt dieses in TEI-Elemente:

| Pipeline-Markup | TEI-Element | Beispiel (Pipeline) | Beispiel (TEI) |
|---|---|---|---|
| `Wort[?]` | `<unclear>Wort</unclear>` | `Gieser[?]` | `<unclear>Gieser</unclear>` |
| `[...]` | `<gap reason="illegible"/>` | `[...]` | `<gap reason="illegible"/>` |
| `[...N...]` | `<gap reason="illegible" quantity="N" unit="chars"/>` | `[...3...]` | `<gap reason="illegible" quantity="3" unit="chars"/>` |
| `~~text~~` | `<del>text</del>` | `~~Eltern~~` | `<del>Eltern</del>` |
| `{text}` | `<add place="above">text</add>` | `{sehr}` | `<add place="above">sehr</add>` |
| `[Stempel: text]` | `<stamp>text</stamp>` | `[Stempel: WIEN 22.5.01]` | `<stamp>WIEN 22.5.01</stamp>` |
| `[Marginalie: text]` | `<note place="margin">text</note>` | `[Marginalie: NB]` | `<note place="margin">NB</note>` |
| Seitenumbruch | `<pb n="N" facs="URL"/>` | (implizit, pro Bild) | `<pb n="1" facs="https://gams.uni-graz.at/o:szd.1079/IMG.1"/>` |

### 4.1 Konvertierungslogik

Die Uebersetzung erfolgt in zwei Stufen:

**Stufe 1: Export (L3, `export_page_json.py`)** — Pipeline-JSON + Layout-JSON → Page-JSON. Seiten werden mit `|{n}|`-Markern konkateniert. Markup bleibt als Plaintext.

**Stufe 2: Annotation (teiCrafter)** — Interchange-Plaintext → TEI-XML. teiCrafter's LLM erkennt die Markup-Muster und uebersetzt sie in TEI-Elemente. Die Mapping-Rules (siehe [[teiCrafter-integration]]) instruieren den LLM, welche Muster welchen TEI-Elementen entsprechen.

### 4.2 DTABf-Schema-Erweiterungen

Das bestehende teiCrafter-DTABf-Schema (`dtabf.json`) muss um folgende Elemente erweitert werden:

| Element | Fehlt in dtabf.json | Benoetigt fuer |
|---|---|---|
| `<unclear>` | Nein (vorhanden) | [?]-Marker |
| `<gap>` | **Ja** | [...]-Marker |
| `<del>` | **Ja** | ~~Streichungen~~ |
| `<add>` | **Ja** | {Einfuegungen} |
| `<stamp>` | **Ja** | [Stempel:]-Praefixe |
| `<table>`, `<row>`, `<cell>` | **Ja** | Gruppe E (Tabellarisch) |
| `<cb/>` | **Ja** | Spaltenumbrueche (Zeitungen) |
| `<postscript>` | Nur in Mapping, nicht im Schema | Nachschriften in Briefen |

Diese Elemente sind alle TEI-P5-konform und DTABf-kompatibel — sie muessen nur in `dtabf.json` ergaenzt werden (allowedChildren, allowedParents, Attribute).

---

## 5. Named Entities im Zweig-Kontext

### 5.1 Relevante Entitaetstypen

| Typ | TEI-Element | Haeufigkeit im Nachlass | Autoritaetsdatei |
|---|---|---|---|
| **Personen** | `<persName ref="GND:...">` | Sehr hoch (Korrespondenzpartner, Verleger, Literaten) | GND |
| **Orte** | `<placeName ref="GND:...">` | Hoch (Wohnorte, Reiseziele, Verlagsstaedte) | GND / GeoNames |
| **Werke** | `<bibl>` / `<title>` | Mittel (Zweigs Werke, referenzierte Literatur) | GND |
| **Organisationen** | `<orgName>` | Mittel (Verlage, Archive, Behoerden) | GND |
| **Daten** | `<date when="...">` | Hoch (Briefe, Vertraege, Tagebuecher) | ISO 8601 |

### 5.2 Prioritaet

**Phase 1 (sofort):** Personen + Orte + Daten — haeufigste Entitaeten, hoechster Informationsgewinn, GND-Verlinkung etabliert.

**Phase 2 (spaeter):** Werke + Organisationen — erfordert Zweig-spezifisches Wissen (Werkverzeichnis, Verlagslandschaft).

### 5.3 Bekannte Personen im Nachlass

Das bestehende Metadaten-TEI enthaelt bereits GND-verlinkte Personen:

- **Stefan Zweig** — GND 118637479
- **Lotte Zweig** — im Metadaten-TEI referenziert
- **Erwin Rieger** — 225 Registerblaetter in der Aufsatzablage
- **Richard Friedenthal** — in Werken und Aufsatzablage

Korrespondenzpartner sind in `szd_korrespondenzen_tei.xml` via `<correspDesc>/<correspAction>/<persName ref="GND:...">` erfasst. Diese GND-Links koennen automatisch in die Transkriptions-TEI uebernommen werden.

### 5.4 Biographisch relevante Orte

Salzburg, Wien, London, Bath, Petropolis (Brasilien), New York, Paris, Montreux, Ruedesheim. Diese Orte erscheinen in Briefen, Tagebucheintraegen und Vertraegen und sollten prioritaer annotiert werden.

---

## 6. Verhaeltnis zum bestehenden SZD-Datenmodell

### 6.1 Bestehendes Modell (Metadaten-TEI)

```
szd_lebensdokumente_tei.xml → <listBibl> mit 143 <biblFull>
szd_werke_tei.xml           → <listBibl> mit 352 <biblFull>
szd_aufsatzablage_tei.xml   → <listBibl> mit 624 <biblFull>
szd_korrespondenzen_tei.xml → <listBibl> mit 723 <biblFull>
```

Jedes `<biblFull>` enthaelt `<msDesc>` mit physischer Beschreibung, Signatur, Haenden, Material — aber **keinen Transkriptionstext**.

### 6.2 Empfehlung: Separate Dateien pro Objekt

**Option A (empfohlen): Eine TEI-Datei pro transkribiertem Objekt.**

```
tei/
  o_szd.72.xml     ← Tagebuch 1918 (transkribiert + annotiert)
  o_szd.100.xml    ← Agreement Longmans
  o_szd.1079.xml   ← Brief an Fleischer
  ...
```

Vorteile:
- Unabhaengig vom bestehenden Metadaten-TEI (keine Migration noetig)
- Versionierbar pro Objekt (Git-freundlich)
- teiCrafter produziert natuerlich eine Datei pro Transformation
- GAMS kann einzelne TEI-Objekte ingestieren

Verknuepfung: `<idno type="PID">o:szd.NNN</idno>` in `<teiHeader>` der Transkriptions-TEI verweist auf das Metadaten-TEI.

**Option B (alternativ): Einbettung in `<biblFull>`.**

Theoretisch koennte `<text>` innerhalb von `<biblFull>` ergaenzt werden. Das waere TEI-konform, aber:
- Aendert die bestehenden Sammlungsdateien (Risiko)
- Macht die Dateien sehr gross (2107 Objekte × durchschnittlich 3 Seiten Text)
- teiCrafter-Workflow passt nicht (erzeugt einzelne Dateien)

### 6.3 GAMS-Integration

Die Transkriptions-TEI nutzt dieselben PIDs wie das Metadaten-TEI (`o:szd.NNN`). GAMS-seitig kann die Transkription als zusaetzlicher Datastream zum bestehenden Objekt hinzugefuegt werden — das muss mit dem GAMS-Team geklaert werden.

Faksimile-Links in `<pb facs="..."/>` zeigen auf die bestehenden GAMS-Bild-URLs (`https://gams.uni-graz.at/o:szd.NNN/IMG.M`).

---

## 7. Offene Entscheidungen

Folgende Punkte muessen im Laufe der Implementierung (Phase 5) geklaert werden:

### 7.1 Zeilenumbrueche

**Frage:** Sollen `<lb/>`-Elemente fuer physische Zeilenumbrueche gesetzt werden?

**Pro:** Maximale Originaltreue, ermoeglicht zeilensynoptische Ansicht mit Faksimile.
**Contra:** Die Pipeline transkribiert zeilenweise, aber ohne explizite Zeilen-Marker — `<lb/>` muesste aus den `\n` im Transkriptionstext abgeleitet werden, was bei normalisierten Texten (CER-Berechnung mit Zeilenumbruch-zu-Leerzeichen) zu Inkonsistenzen fuehrt.

**Vorlaeufige Empfehlung:** `<lb/>` optional. Fuer den Piloten: nur `<pb/>` (Seitenumbrueche) setzen, `<lb/>` spaeter ergaenzen, wenn die zeilensynoptische Ansicht benoetigt wird.

### 7.2 NER-Tiefe

**Frage:** Wie viele Entitaetstypen soll teiCrafter annotieren?

**Empfehlung:** Phase 1 nur Personen, Orte, Daten (3 Typen). Phase 2 Werke und Organisationen. Zu viele Entitaetstypen ueberfordern das LLM und erhoehen False Positives.

### 7.3 Confidence-Attribute im finalen TEI

**Frage:** Sollen `@confidence` und `@resp="#machine"` im publizierten TEI bleiben?

**Empfehlung:** Ja — sie dokumentieren die Provenienz der Annotation. Der Expert-in-the-Loop kann sie im teiCrafter-Review entfernen oder bestaetigen. Fuer die Publikation koennen sie optional gestrippt werden (teiCrafter Step 5 bietet das an).

### 7.4 Mehrsprachige Dokumente

**Frage:** Wie werden Dokumente kodiert, die mehrere Sprachen enthalten (z.B. deutscher Brief mit franzoesischem Zitat)?

**Empfehlung:** `xml:lang` auf `<text>`-Ebene fuer die Hauptsprache. Fremdsprachige Passagen mit `<foreign xml:lang="fr">` markieren. Das entspricht der DTABf-Konvention und ist im teiCrafter-Schema bereits vorgesehen.

### 7.5 Umschlaege und Beilagen

**Frage:** Wie werden Briefumschlaege (Seiten 1-2 bei Korrespondenzen) strukturiert?

**Empfehlung:** `<div type="envelope">` fuer Umschlag, `<div type="letter">` fuer Brieftext. Das ist TEI-konform und spiegelt die physische Struktur wider, die die Pipeline bereits korrekt erkennt (vgl. o_szd.1079).
