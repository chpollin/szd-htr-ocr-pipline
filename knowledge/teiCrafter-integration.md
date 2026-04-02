---
title: "teiCrafter-Integration"
aliases: ["teiCrafter-Integration"]
created: 2026-04-01
updated: 2026-04-01
type: spec
status: draft
related:
  - "[[htr-interchange-format]]"
  - "[[tei-target-structure]]"
  - "[[annotation-protocol]]"
---

# teiCrafter-Integrationskonzept: SZD-HTR → TEI-Annotation

Abhaengigkeit: [[htr-interchange-format]] (JSON-Schema), [[tei-target-structure]] (TEI-Ziel), [[annotation-protocol]] (Markup-Konventionen)

---

## 1. Zweck und Scope

Dieses Dokument konkretisiert, wie die HTR-Transkriptionen aus der SZD-Pipeline via [teiCrafter](https://digitalhumanitiescraft.github.io/teiCrafter/) in annotiertes TEI-XML ueberfuehrt werden. Es loest die 5 offenen Erweiterungsbedarfe aus [[htr-interchange-format]] §4.2 und liefert die Mapping-Templates, die teiCrafter fuer die SZD-Annotation benoetigt.

### 1.1 Datenfluss

```
Pipeline-JSON → export_interchange.py → Interchange-JSON → teiCrafter Import (Step 1)
  → Mapping (Step 2) → LLM-Annotation (Step 3) → Validierung (Step 4) → Export (Step 5)
  → TEI-XML pro Objekt
```

### 1.2 teiCrafter-Architektur (Zusammenfassung)

teiCrafter ist eine Browser-SPA (Vanilla JS, kein Backend) mit 5 Schritten:

| Schritt | Funktion | SZD-relevant |
|---|---|---|
| **Step 1: Import** | Datei laden (.txt, .md, .xml, .docx) | JSON-Import ergaenzen |
| **Step 2: Mapping** | sourceType, language, epoch, project, mappingRules konfigurieren | Auto-Vorbelegung aus JSON |
| **Step 3: Transform** | LLM annotiert Text → TEI-XML | Diplomatisches Markup erkennen |
| **Step 4: Validate** | Well-formedness, Plaintext-Preservation, Schema, Review | DTABf-Schema erweitern |
| **Step 5: Export** | TEI-XML herunterladen, Attribute optional strippen | Standard |

Repo: `C:\Users\Chrisi\Documents\GitHub\ResearchTools\teiCrafter`

---

## 2. JSON-Import fuer teiCrafter Step 1

### 2.1 Neuer Dateityp: `.json`

teiCrafter akzeptiert aktuell .txt, .md, .xml, .docx. Fuer SZD-HTR wird `.json` als fuenfter Typ ergaenzt.

**Import-Logik:**
1. Datei laden und als JSON parsen
2. Pruefen ob `htr_interchange`-Feld vorhanden (Schema-Erkennung)
3. Version pruefen (`htr_interchange == "0.1"`)
4. `transcription.pages[]` extrahieren
5. Seiten mit `|{n}|`-Marker konkatenieren (siehe §5)
6. Ergebnis in `AppState.inputContent` speichern
7. Metadaten fuer Step 2 vorbelegen (siehe §2.2)

**Code-Stelle:** `docs/js/app.js`, Funktion `handleFileUpload()` (ca. Zeile 69-232)

### 2.2 Auto-Vorbelegung von Step 2

Wenn eine Interchange-JSON importiert wird, sollen die Step-2-Felder automatisch befuellt werden (User kann ueberschreiben):

| teiCrafter-Feld | Interchange-Quelle | Transformation |
|---|---|---|
| `sourceType` | `source.document_type` | Mapping-Tabelle (§2.3) |
| `language` | `source.language` | ISO 639-1 direkt (`de`, `en`, `fr`, `it`, `es`) |
| `epoch` | `source.date` | Ableitung: `19xx`/`20xx` → `20c`, `18xx` → `18c`, `1xxx` → `medieval`. Fallback: `20c` |
| `project` | `source.repository` oder `source.collection` | Freitext, z.B. "Stefan Zweig Digital" |
| `mappingRules` | (nicht im JSON) | Default-Mapping basierend auf sourceType laden (§4) |

### 2.3 sourceType-Mapping (aktualisiert)

| Interchange `source.document_type` | teiCrafter `sourceType` | SZD-Mapping-Template |
|---|---|---|
| `manuscript`, `notebook`, `diary` | `generic` → **`manuscript`** (neu) | szd-manuscript |
| `letter`, `postcard`, `correspondence` | `correspondence` | szd-correspondence |
| `typescript`, `form`, `certificate` | `generic` | szd-print |
| `newspaper_clipping`, `proof_sheet` | `print` | szd-print |
| `register`, `calendar`, `ledger` | `generic` → **`tabular`** (neu) | szd-manuscript |
| `mixed_materials` (Konvolut) | `generic` | szd-manuscript |

**Neue sourceTypes fuer teiCrafter:** `manuscript` und `tabular` als Ergaenzung zu den bestehenden 5 Typen. Das erfordert Anpassung in `docs/js/utils/constants.js` (SOURCE_LABELS).

---

## 3. Sprach- und Epochen-Erweiterung

### 3.1 Neue Sprachen

Aktuell: `de` (German), `la` (Latin), `mhd` (Middle High German).

Erweiterung fuer SZD:

| Code | Label | Begruendung |
|---|---|---|
| `en` | English | 23 Lebensdokumente, 27 Werke, 6 Aufsaetze |
| `fr` | French | 13 Lebensdokumente, 17 Werke, 9 Aufsaetze |
| `it` | Italian | 2+2+3 Objekte |
| `es` | Spanish | 2+1 Objekte |

**Code-Stelle:** `docs/js/app.js` (Zeilen 280-285, language `<select>` Options) und `docs/js/utils/constants.js`.

### 3.2 Neue Epoche

Aktuell: `19c`, `18c`, `medieval`.

Erweiterung:

| Code | Label | Begruendung |
|---|---|---|
| `20c` | 20th century | Zweigs Schaffensperiode 1901-1942, >95% aller SZD-Objekte |

**Code-Stelle:** `docs/js/app.js` (Zeilen 288-293, epoch `<select>` Options).

**Auswirkung auf Prompt:** Die Epoche wird im Context-Layer an den LLM uebergeben (`Period: 20c`). Das beeinflusst, wie der LLM mit Orthographie, Abkuerzungen und Zeitbezuegen umgeht.

---

## 4. SZD-spezifische Mapping-Rules

Drei Templates fuer die Hauptgruppen des Nachlasses, im Format der teiCrafter-Demo-Mappings (Markdown-Bullet-Listen).

**Die Templates sind als eigenstaendige Dateien extrahiert und im teiCrafter-Repo abgelegt:**

| Template | Datei | Gruppen |
|---|---|---|
| Korrespondenz | `teiCrafter/data/demo/mappings/correspondence-szd.md` | I, D |
| Manuskript | `teiCrafter/data/demo/mappings/manuscript-szd.md` | A, E, G |
| Druck/Typoskript | `teiCrafter/data/demo/mappings/print-szd.md` | B, C, F, H |

### 4.1 Template: szd-correspondence.md

Fuer Gruppe I (Korrespondenzen, ~1186 Objekte) und Gruppe D (Kurztexte — Postkarten, Visitenkarten).

```markdown
You will act as a skilled expert automaton that is proficient in transforming 
diplomatically transcribed letters from the Stefan Zweig estate (early 20th century) 
into well-formed TEI XML according to DTABf. The text may contain inline markup 
from the HTR pipeline that must be converted to TEI elements. Analyze the provided 
text based on the mapping rules and execute the transformation.

Mapping rules:
* <div type="envelope"> Envelope content (address, stamps)
* <div type="letter"> Letter body
* <pb> Marks page breaks e.g. "|{n}|", with @facs for facsimile URL if available
* <opener> Opening of the letter (dateline + salutation)
* <closer> Closing of the letter (greeting + signature)
* <dateline> Date/place reference
* <date> Dates; when={YYYY-MM-DD}
* <salute> Salutation or greeting formula
* <signed> Signature
* <postscript> Postscript (P.S.)
* <p> Paragraphs
* <lb> Line breaks where significant
* <persName> Person names
* <placeName> Place names
* <orgName> Organisations (publishers, archives)
* <date> Dates in running text; when={YYYY-MM-DD}
* <bibl> References to literary works
* <foreign> Foreign language passages; xml:lang={ISO 639-1}
* <unclear> HTR pipeline marker: word followed by [?] → wrap word in <unclear>
* <gap reason="illegible"/> HTR pipeline marker: [...] → self-closing <gap>
* <gap reason="illegible" quantity="N" unit="chars"/> HTR marker: [...N...] → <gap> with count
* <del> HTR pipeline marker: ~~text~~ → wrap text in <del>
* <add place="above"> HTR pipeline marker: {text} → wrap text in <add>
* <stamp> HTR pipeline marker: [Stempel: text] → wrap text in <stamp>
* <note place="margin"> HTR pipeline marker: [Marginalie: text] → wrap in <note>

Guidelines:
* Strictly follow mapping rules
* Preserve the original text including historical spelling (diplomatische Transkription)
* Do NOT correct spelling, expand abbreviations, or normalize orthography
* Convert HTR pipeline markup ([?], [...], ~~...~~, {...}) to the corresponding TEI elements
* Produce well-formed TEI XML according to DTABf
* Return the content starting from <div>
* Annotate named entities only when confident
* Add @confidence="high|medium|low" and @resp="#machine" to all annotations
* Compact XML without unnecessary whitespace
```

### 4.2 Template: szd-manuscript.md

Fuer Gruppen A (Handschrift), E (Tabellarisch), G (Konvolut) — Tagebuecher, Notizbuecher, Register, Kalender, gemischte Materialien.

```markdown
You will act as a skilled expert automaton that is proficient in transforming 
diplomatically transcribed manuscripts from the Stefan Zweig estate (early 20th century)
into well-formed TEI XML according to DTABf. The text may contain inline markup 
from the HTR pipeline. Documents include diaries, notebooks, registers, and mixed 
materials (Konvolute). Analyze the provided text and execute the transformation.

Mapping rules:
* <div> Main structural division (diary entry, register section, document within Konvolut)
* <head> Section heading or date header (e.g., diary date)
* <p> Paragraphs of running text
* <pb> Marks page breaks e.g. "|{n}|", with @facs for facsimile URL
* <lb> Line breaks where significant
* <table> Tabular structures (registers, calendars, ledgers)
* <row> Table row
* <cell> Table cell
* <persName> Person names
* <placeName> Place names
* <orgName> Organisations
* <date> Dates; when={YYYY-MM-DD} or when={YYYY}
* <bibl> References to literary works
* <foreign> Foreign language passages; xml:lang={ISO 639-1}
* <unclear> HTR pipeline marker: word followed by [?] → wrap word in <unclear>
* <gap reason="illegible"/> HTR pipeline marker: [...] → self-closing <gap>
* <gap reason="illegible" quantity="N" unit="chars"/> HTR marker: [...N...] → <gap> with count
* <del> HTR pipeline marker: ~~text~~ → wrap text in <del>
* <add place="above"> HTR pipeline marker: {text} → wrap text in <add>
* <note place="margin"> HTR pipeline marker: [Marginalie: text] → wrap in <note>

Guidelines:
* Strictly follow mapping rules
* Preserve the original text including historical spelling
* Do NOT correct spelling, expand abbreviations, or normalize orthography
* Convert HTR pipeline markup to corresponding TEI elements
* For tabular content: use <table>/<row>/<cell> instead of pipe-separated text
* Pipe characters (|) in the source text indicate column separators → convert to <cell> boundaries
* Produce well-formed TEI XML according to DTABf
* Return the content starting from <div>
* Annotate named entities only when confident
* Add @confidence and @resp="#machine" to all annotations
* Compact XML without unnecessary whitespace
```

### 4.3 Template: szd-print.md

Fuer Gruppen B (Typoskript), C (Formular), F (Korrekturfahne), H (Zeitungsausschnitt) — gedruckte oder maschinenschriftliche Texte.

```markdown
You will act as a skilled expert automaton that is proficient in transforming 
diplomatically transcribed printed/typed documents from the Stefan Zweig estate 
(early 20th century) into well-formed TEI XML according to DTABf. Documents include 
typescripts, forms, proof sheets with corrections, and newspaper clippings (some in 
Fraktur). The text may contain HTR pipeline markup. Execute the transformation.

Mapping rules:
* <div> Main structural division (document, article, contract section)
* <head> Headings and titles
* <p> Paragraphs of running text
* <pb> Marks page breaks e.g. "|{n}|", with @facs for facsimile URL
* <lb> Line breaks where significant
* <cb/> Column breaks (newspaper clippings with multi-column layout)
* <fw> Forme work (running headers, page numbers, printed letterhead)
* <hi rendition="#b"> Bold text
* <hi rendition="#i"> Italic text
* <hi rendition="#u"> Underlined text
* <persName> Person names
* <placeName> Place names
* <orgName> Organisations (publishers, legal entities)
* <date> Dates; when={YYYY-MM-DD}
* <bibl> Bibliographic references
* <foreign> Foreign language passages; xml:lang={ISO 639-1}
* <note> Editorial or authorial notes
* <unclear> HTR pipeline marker: word followed by [?] → wrap word in <unclear>
* <gap reason="illegible"/> HTR pipeline marker: [...] → self-closing <gap>
* <gap reason="illegible" quantity="N" unit="chars"/> HTR marker: [...N...] → <gap> with count
* <del> HTR pipeline marker: ~~text~~ → wrap text in <del> (corrections on proof sheets)
* <add place="above"> HTR pipeline marker: {text} → wrap text in <add>
* <stamp> HTR pipeline marker: [Stempel: text] → wrap text in <stamp>

Guidelines:
* Strictly follow mapping rules
* Preserve the original text including historical spelling
* Do NOT correct spelling, expand abbreviations, or normalize orthography
* Convert HTR pipeline markup to corresponding TEI elements
* For newspaper clippings: use <cb/> to mark column transitions
* For proof sheets: <del> and <add> represent author/editor corrections
* For forms: preserve field structure, use <p> for each field entry
* Produce well-formed TEI XML according to DTABf
* Return the content starting from <div>
* Annotate named entities only when confident
* Add @confidence and @resp="#machine" to all annotations
* Compact XML without unnecessary whitespace
```

---

## 5. Mehrseitige Dokumente

### 5.1 Seitentrenner-Konvention

**Entscheidung:** `|{n}|` als Seitentrenner (teiCrafter-Konvention).

Das korrigiert den Vorschlag in [[htr-interchange-format]] §8.2, der `\n\n---\n\n` vorschlug. teiCrafter verwendet `|{n}|` bereits in allen Demo-Mappings und die LLM-Annotation erwartet dieses Format.

### 5.2 Export-Logik (fuer L3)

`export_interchange.py` muss beim Konkatenieren der Seiten `|{n}|`-Marker einsetzen:

```
Seite 1 Text|{1}|Seite 2 Text|{2}|Seite 3 Text
```

Leerseiten (leere Transkription) erhalten nur den Marker ohne Text:

```
Seite 1 Text|{1}||{2}|Seite 3 Text
```

### 5.3 Faksimile-Verknuepfung

Die `source.images[]`-URLs aus dem Interchange-JSON koennen in die `|{n}|`-Marker nicht eingebettet werden (die sind reine Seitennummern). Stattdessen werden die Faksimile-URLs im Mapping-Kontext an den LLM uebergeben:

```
Page images:
Page 1: https://gams.uni-graz.at/o:szd.1079/IMG.1
Page 2: https://gams.uni-graz.at/o:szd.1079/IMG.2
Page 3: https://gams.uni-graz.at/o:szd.1079/IMG.3
```

Der LLM setzt dann `<pb n="1" facs="https://gams.uni-graz.at/o:szd.1079/IMG.1"/>`.

---

## 6. Offene Punkte aus htr-interchange-format.md §8

### 6.1 Schema-Hosting

**Entscheidung:** JSON-Schema auf GitHub Pages im szd-htr-Repo publizieren.

URL-Muster: `https://chpollin.github.io/szd-htr/schemas/htr-interchange-v0.1.json`

Das `$id`-Feld im Schema wird entsprechend aktualisiert.

### 6.2 Mehrseitige Konkatenation

**Entscheidung:** `|{n}|` als Seitentrenner (siehe §5.1). Die Korrektur von `\n\n---\n\n` zu `|{n}|` wird in htr-interchange-format.md nachgetragen.

### 6.3 Sprach-Normalisierung

**Entscheidung:** `source.language` erfordert ISO 639-1 Codes (`de`, `en`, `fr`, `it`, `es`, `la`). Freitext wie "Deutsch" oder "Englisch" wird im Export normalisiert (L3, `export_interchange.py`).

Normalisierungstabelle:

| SZD-HTR `metadata.language` | Interchange `source.language` |
|---|---|
| Deutsch, Deutsch? | `de` |
| Englisch | `en` |
| Franzoesisch | `fr` |
| Italienisch | `it` |
| Spanisch | `es` |
| Jiddisch | `yi` |
| unbekannt | `und` (undetermined) |

### 6.4 document_type-Vokabular

**Entscheidung:** Kontrolliertes Vokabular (Enumeration):

```
manuscript, typescript, letter, postcard, notebook, diary, form, certificate,
newspaper_clipping, proof_sheet, register, calendar, ledger, mixed_materials
```

Abgeleitet aus den TEI-Objekttypen der 4 Sammlungen. Neue Werte koennen ergaenzt werden, aber das Schema validiert gegen diese Liste.

### 6.5 Versionierung

**Entscheidung:** SemVer.

- `0.1` → aktueller Entwurf
- `0.2` → nach Pilot-Ergebnissen (ggf. Felderweiterung)
- `1.0` → nach erfolgreichem Durchlauf mit teiCrafter (Stabilisierung)

---

## 7. DTABf-Schema-Erweiterungen fuer teiCrafter

Das bestehende `dtabf.json` muss um diplomatische Transkriptionselemente erweitert werden (vgl. [[tei-target-structure]] §4.2):

```json
"gap": {
  "allowedChildren": [],
  "allowedParents": ["p", "div", "head", "unclear"],
  "attributes": {
    "reason": { "type": "enum", "values": ["illegible", "damage", "censored"] },
    "quantity": { "type": "number" },
    "unit": { "type": "enum", "values": ["chars", "words", "lines"] }
  },
  "selfClosing": true
},
"del": {
  "allowedChildren": ["#text", "gap", "unclear", "persName", "placeName", "date"],
  "allowedParents": ["p", "div"],
  "attributes": {
    "rendition": { "type": "string" }
  }
},
"add": {
  "allowedChildren": ["#text", "persName", "placeName", "date"],
  "allowedParents": ["p", "div"],
  "attributes": {
    "place": { "type": "enum", "values": ["above", "below", "margin", "inline"] }
  }
},
"stamp": {
  "allowedChildren": ["#text", "date", "placeName", "orgName"],
  "allowedParents": ["p", "div"],
  "attributes": {
    "type": { "type": "string" }
  }
},
"table": {
  "allowedChildren": ["row", "head"],
  "allowedParents": ["div", "body"],
  "attributes": {
    "rows": { "type": "number" },
    "cols": { "type": "number" }
  }
},
"row": {
  "allowedChildren": ["cell"],
  "allowedParents": ["table"],
  "attributes": {
    "role": { "type": "enum", "values": ["label", "data"] }
  }
},
"cell": {
  "allowedChildren": ["#text", "persName", "placeName", "date", "measure", "lb"],
  "allowedParents": ["row"],
  "attributes": {}
},
"cb": {
  "allowedChildren": [],
  "allowedParents": ["div", "p", "body"],
  "attributes": {
    "n": { "type": "string" }
  },
  "selfClosing": true
}
```

---

## 8. Zusammenfassung der teiCrafter-Aenderungen

| Aenderung | Wo | Prioritaet | Abhaengigkeit |
|---|---|---|---|
| JSON-Import (.json) | `app.js` handleFileUpload | Hoch | Interchange-Export (L3) |
| Auto-Vorbelegung Step 2 | `app.js` Step 2 init | Hoch | JSON-Import |
| Sprachen: en, fr, it, es | `constants.js`, `app.js` | Hoch | Keine |
| Epoche: 20c | `constants.js`, `app.js` | Hoch | Keine |
| sourceTypes: manuscript, tabular | `constants.js` | Mittel | Keine |
| DTABf-Schema: gap, del, add, stamp, table, cb | `dtabf.json` | Hoch | Mapping-Templates |
| SZD-Mapping-Templates (3) | `data/demo/mappings/` | Hoch | Schema-Erweiterung |
| Faksimile-URLs in Kontext | `transform.js` | Mittel | JSON-Import |

**Geschaetzter Implementierungsaufwand:** Die meisten Aenderungen sind Konfiguration (constants, Schema-JSON, Mapping-Templates). Der JSON-Import und die Auto-Vorbelegung erfordern ~100-200 Zeilen JavaScript. Die Schema-Erweiterung ist eine JSON-Ergaenzung. Der Gesamtaufwand liegt unter einem Arbeitstag.
