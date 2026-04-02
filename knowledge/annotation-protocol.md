---
title: "Annotationsprotokoll"
aliases: ["Annotationsprotokoll"]
created: 2026-04-01
updated: 2026-04-01
type: protocol
status: stable
related:
  - "[[verification-concept]]"
---

# Annotationsprotokoll: Referenztranskription fuer das SZD-HTR Ground-Truth-Sample

Abhaengigkeit: [[verification-concept]] (Abschnitt 1 definiert das Sample)

---

## Zweck

Dieses Protokoll definiert die Transkriptionskonventionen fuer die manuelle Referenztranskription von 30 Objekten aus dem Stefan-Zweig-Nachlass. Es muss so praezise sein, dass zwei Annotierende dasselbe Dokument unabhaengig transkribieren und vergleichbare CER-Werte erzielen (Inter-Annotator-Agreement).

Die Referenztranskription dient als Ground Truth fuer:
- CER/WER-Berechnung der Pipeline-Ergebnisse
- Kalibrierung der quality_signals-Schwellenwerte
- Prompt-Wirksamkeitsvergleich (3 Varianten)

---

## 1. Textfluss

### 1.1 Zeilenumbrueche: Beibehalten

**Entscheidung:** Die Referenztranskription behaelt die Zeilenumbrueche des Originals bei.

**Begruendung:** Die Pipeline behaelt Zeilenumbrueche bei (sichtbar als `\n` in den JSON-Ergebnissen). Wenn die Referenz Fliesstext waere, die Pipeline aber zeilengetreu transkribiert, wuerden alle Zeilenumbrueche als Insertions (Pipeline) oder Deletions (Referenz) in die CER eingehen — das verfaelscht die Messung zugunsten von Nicht-Textfehlern.

Die CER-Normalisierung (Abschnitt 5) neutralisiert Zeilenumbruch-Differenzen vor der Berechnung, aber nur in eine Richtung: Sie kann Umbrueche entfernen, nicht einfuegen. Deshalb ist es sicherer, in der Referenz Umbrueche zu erfassen (koennen spaeter normalisiert werden) als sie auszulassen (koennen nicht rekonstruiert werden).

**Praxis:** Ein Zeilenumbruch wird dort gesetzt, wo die Schrift im Faksimile physisch auf die naechste Zeile wechselt. Nicht bei jedem visuellen Abstand — nur bei klarem Zeilenwechsel.

### 1.2 Silbentrennung am Zeilenende

**Entscheidung:** Trennstriche beibehalten, genau wie im Faksimile.

Wenn das Faksimile am Zeilenende "Mar-" zeigt und auf der naechsten Zeile "neschlacht" fortfaehrt, wird transkribiert:

```
Mar-
neschlacht
```

Die CER-Normalisierung (Abschnitt 5) fuegt getrennte Woerter vor der Berechnung zusammen. So misst die CER Lesegenauigkeit, nicht Trennungsgenauigkeit.

### 1.3 Absaetze

**Entscheidung:** Absaetze werden durch eine Leerzeile markiert (doppelter Zeilenumbruch `\n\n`).

Ein Absatzwechsel liegt vor, wenn:
- Sichtbarer vertikaler Abstand zwischen Textbloecken
- Einrueckung am Beginn einer neuen Zeile (bei Fliesstext-Dokumenten)
- Thematischer Wechsel mit visueller Markierung (neues Datum im Tagebuch, Grusskformel im Brief)

Kein Absatzwechsel bei:
- Blosser Zeilenwechsel ohne zusaetzlichen Abstand
- Einrueckung der ersten Zeile nach einem Seitenumbruch

### 1.4 Spalten bei mehrspaltigem Layout

**Entscheidung:** Spaltenweise, links nach rechts, dann oben nach unten.

Bei Zeitungsausschnitten (Gruppe H) mit Mehrspaltensatz:
1. Linke Spalte vollstaendig transkribieren
2. Leerzeile als Spaltentrenner
3. Rechte Spalte vollstaendig transkribieren

Wenn Text ueber die Spaltengrenze fliesst (Satz beginnt in Spalte 1 und endet in Spalte 2): den Textfluss des Originals beibehalten, d.h. Spalte 1 bis zum Spaltenende, dann Spalte 2 ab Spaltenanfang.

### 1.5 Seitenumbrueche und Worttrennung ueber Seitengrenzen

Jede Seite (= jedes Faksimile-Bild) wird separat transkribiert. Wenn ein Wort am Seitenende getrennt ist ("Ge-" auf Seite 4, "schenisse" auf Seite 5), bleibt die Trennung erhalten:

- Seite 4 endet mit: `Ge-`
- Seite 5 beginnt mit: `schenisse ins Unrecht setzen.`

Die CER wird pro Seite berechnet. Seitenuebergreifende Worttrennung beeinflust die CER minimal (ein Wortfragment pro Seitengrenze).

---

## 2. Diplomatische Konventionen

### 2.1 Grundprinzip

Transkribiere genau, was du siehst. Keine Normalisierung, keine Korrektur, keine Interpretation. Wenn Zweig "Cadaver" schreibt, steht in der Referenz "Cadaver", nicht "Kadaver".

### 2.2 Abkuerzungen

**Entscheidung:** Nicht aufloesen. Genau so transkribieren, wie sie im Faksimile erscheinen.

| Im Faksimile | In der Referenz | NICHT |
|---|---|---|
| R. | R. | Rolland |
| frz. Cons. | frz. Cons. | franzoesischer Konsul |
| u. | u. | und |
| Sept. | Sept. | September |
| Jerem. | Jerem. | Jeremias |

**Begruendung:** Abkuerzungsaufloesung ist eine editorische Entscheidung, keine Transkription. Die Pipeline loest manchmal auf und manchmal nicht — genau diese Inkonsistenz soll die CER erfassen.

### 2.3 Gross- und Kleinschreibung

**Entscheidung:** Exakt beibehalten.

Gross/Kleinschreibung ist bedeutungstragend (Substantivierung, Satzanfang, Eigenname). Keine Normalisierung.

Wenn nicht unterscheidbar (besonders bei Kurrent: D/d, P/p, S/s): die wahrscheinlichere Lesung waehlen. Wenn echt unsicher: [?] nach dem Wort.

### 2.4 Historische Orthographie

**Entscheidung:** Beibehalten. Keine Modernisierung.

| Beibehalten | NICHT normalisieren zu |
|---|---|
| daß | dass |
| grösser | groesser |
| Cadaver | Kadaver |
| Conflicte | Konflikte |
| Tramway | Strassenbahn |
| direct | direkt |

Das schliesst Zweigs individuelle Schreibgewohnheiten ein (Schweizer Schreibweisen mit ss statt ß, franzoesische Lehnwoerter ohne Anpassung).

### 2.5 Interpunktion

**Entscheidung:** Exakt beibehalten, einschliesslich fehlender oder unueblicher Interpunktion.

Wenn Zweig keinen Punkt am Satzende setzt, steht keiner in der Referenz. Wenn er Anfuehrungszeichen in der deutschen Form („...") oder in der franzoesischen Form (»...« oder "...") verwendet, exakt uebernehmen.

### 2.6 Sonderzeichen und Ligaturen

**Entscheidung:** In modernem Unicode transkribieren. Keine historischen Codepoints.

| Im Faksimile | In der Referenz | NICHT |
|---|---|---|
| Langes s (wenn Fraktur) | s | ſ |
| ß (Eszett) | ß | ss (ausser Zweig schreibt tatsaechlich ss) |
| ae-Ligatur (wenn vorhanden) | ae | æ |

**Begruendung (Levchenko 2025):** VLMs neigen zu "Over-Historicization" — dem Einfuegen archaischer Zeichen aus der falschen Periode. Die Referenz verwendet nur Zeichen aus dem modernen Unicode-Block (Latin), die dem tatsaechlichen Zeicheninventar des fruehen 20. Jahrhunderts entsprechen. Wenn die Pipeline ein langes s (ſ) einfuegt, wo Zweig ein normales s schrieb, ist das ein CER-Fehler.

Ausnahme: Wenn das Faksimile tatsaechlich Frakturschrift enthaelt (Zeitungsausschnitte vor ~1940), wird trotzdem in Latin-Unicode transkribiert — der gedruckte Frakturbuchstabe wird als sein modernes Aequivalent gelesen.

---

## 3. Editorische Markierungen

### 3.1 Markup-System

Die Referenztranskription verwendet dasselbe Markup wie die Pipeline:

| Markup | Bedeutung | Beispiel |
|---|---|---|
| `[?]` | Unsichere Lesung | `Klard[?]` |
| `[...]` | Unleserliche Passage | `[...]` |
| `[...N...]` | Unleserlich, geschaetzte Zeichenzahl | `[...3...]` |
| `~~text~~` | Durchgestrichen | `~~Eltern~~` |
| `{text}` | Einfuegung (ueber der Zeile, am Rand) | `{eingefuegt}` |

### 3.2 Schwelle: Unsicher [?] vs. Unleserlich [...]

**Unsicher [?]:** Der Annotierende kann eine Lesung vorschlagen, ist aber nicht sicher. Typische Situation: Ein Buchstabe koennte "n" oder "u" sein, ein Eigenname ist plausibel aber nicht eindeutig. Schwelle: Der Annotierende ist sich zu 50-90% sicher.

**Unleserlich [...]:** Der Annotierende kann keine Lesung vorschlagen. Typische Situation: Tinte ist verblasst, Papier ist beschaedigt, Schrift ist ueberlagert. Schwelle: Der Annotierende ist sich zu <50% sicher ueber die Identitaet der Zeichen.

Praxis:
- `Klard[?]` — ich lese "Klard", bin aber unsicher (koennte "Klarb" sein)
- `[...1...] Mutter` — ein Wort vor "Mutter" ist nicht lesbar, geschaetzt 1 Zeichen
- `[...]` — eine Passage ist nicht lesbar, Laenge unbestimmt

**Wichtig:** [?] steht direkt nach dem unsicheren Wort, ohne Leerzeichen. Es markiert das vorangehende Wort, nicht eine Position im Text.

### 3.3 Streichungen

**Entscheidung:** Durchgestrichenen Text in `~~...~~` einschliessen und vollstaendig transkribieren, soweit lesbar.

```
~~Eltern~~ Schwester
```

Wenn der durchgestrichene Text nicht lesbar ist:
```
~~[...]~~ Schwester
```

Streichungen durch einfaches Ueberstreichen (ein Strich) und durch mehrfaches Ueberstreichen werden gleich markiert — die Intensitaet der Streichung wird nicht kodiert.

### 3.4 Einfuegungen

**Entscheidung:** In `{...}` einschliessen. Die Position im Textfluss richtet sich nach der intendierten Einfuegestelle, nicht nach der physischen Position auf dem Blatt.

```
Er ist {sehr} verzweifelt
```

Wenn die Einfuegestelle nicht eindeutig ist, den eingefuegten Text an der wahrscheinlichsten Stelle einfuegen und [?] anhaengen:

```
Er ist {sehr}[?] verzweifelt
```

### 3.5 Marginale Annotationen

**Entscheidung:** Transkribieren, wenn sie zum Dokumentinhalt gehoeren. Am Ende der jeweiligen Seite anfuegen, nach einer Leerzeile, mit dem Praefix `[Marginalie:]`.

```
...Haupttext letzte Zeile.

[Marginalie:] Anmerkung am Rand
```

Nicht transkribieren:
- Moderne Bibliotheksstempel oder Archivvermerke (sie gehoeren nicht zum historischen Dokument)
- Paginierungen von Archivhand

### 3.6 Unsichere Markup-Entscheidungen

Wenn unklar ist, ob eine Textstelle durchgestrichen, eingefuegt oder beides ist: Die beste Interpretation waehlen und in einer separaten Anmerkung dokumentieren (nicht in der Transkription selbst — die Referenz bleibt maschinenlesbar).

---

## 4. Dokumenttyp-spezifische Regeln

### 4.1 Briefumschlag + Brieftext (Gruppe I: Korrespondenz)

**Reihenfolge:** Bild-Reihenfolge beibehalten. Wenn Bild 1 den Umschlag zeigt und Bild 2 den Brief, wird Seite 1 = Umschlag, Seite 2 = Brief.

Die Pipeline transkribiert in Bildreihenfolge (vgl. o_szd.1079: Seite 1 = Umschlagvorderseite, Seite 2 = Umschlagrueckseite, Seite 3 = Brief). Die Referenz folgt derselben Reihenfolge.

### 4.2 Stempel

**Entscheidung:** Stempeltext transkribieren, wenn er zum Dokumentinhalt gehoert (Datumsstempel, Eingangsstempel, Behoerdenstempel).

```
[Stempel: RUDOLF M. ROHRER 7. VII. 1937]
```

Nicht transkribieren: Moderne Bibliotheksstempel (Inventarnummern, Barcodes).

### 4.3 Gedruckte Formularfelder (Gruppe C: Formular)

**Entscheidung:** Vorgedruckten Text und handschriftliche Eintragungen gleichermassen transkribieren. Keine Unterscheidung zwischen gedruckt und handschriftlich in der Referenz.

Bei tabellarischen Formularen: Die Tabellenstruktur als linearen Text wiedergeben, Spaltentrennungen durch ` | ` (Pipe mit Leerzeichen).

### 4.4 Farbkarten und Digitalisierungsartefakte

**Entscheidung:** Nicht transkribieren. Farbkarten, Grauskalen und Massstabsleisten sind Artefakte des Digitalisierungsprozesses, kein Dokumentinhalt.

Wenn ein Bild nur eine Farbkarte/Rueckseite ohne Text zeigt: Leere Transkription fuer diese Seite.

Die Pipeline transkribiert Farbkarten teilweise (vgl. o_szd.160, Seite 3: "Grauskala #13 C Y M B.I.G. ..."). Das ist ein Pipeline-Fehler, der in der CER sichtbar wird — die Referenz hat hier eine leere Seite, die Pipeline hat Text.

### 4.5 Mehrere Haende

**Entscheidung:** In der Basisreferenz nicht markieren. Der Text wird unabhaengig vom Schreiber transkribiert.

Begruendung: Haende-Zuweisung erfordert palaographische Expertise und ist subjektiv. Sie ist fuer die CER-Berechnung irrelevant (CER misst Zeichengenauigkeit, nicht Schreiber-Erkennung). Haende-Annotation koennte als separates Layer ergaenzt werden, blockiert aber nicht die Ground-Truth-Erstellung.

### 4.6 Farbige Annotationen (Buntstifte, verschiedene Tinten)

**Entscheidung:** Den Text transkribieren, unabhaengig von Farbe oder Instrument. Keine Farbkodierung in der Referenz.

Wenn Annotationen in verschiedenen Farben verschiedene Bearbeitungsschichten darstellen (z.B. Korrekturfahnen mit mehreren Korrektur-Runden): Alle Annotationen transkribieren, die Zuordnung zu Runden gehoert nicht in die Basisreferenz.

---

## 5. Normalisierung fuer die CER-Berechnung

Die folgenden Normalisierungsschritte werden auf **beide** Texte (Referenz und Pipeline-Output) angewendet, **bevor** die CER berechnet wird. Sie stellen sicher, dass die CER Lesegenauigkeit misst, nicht Formatierungsdifferenzen.

### 5.1 Basis-Normalisierung (aus verification-concept.md 1.7)

1. Unicode-Normalisierung (NFC)
2. Whitespace: Mehrfache Leerzeichen → ein Leerzeichen
3. Zeilenumbrueche: `\r\n` → `\n`
4. Trailing-Whitespace pro Zeile entfernen
5. **Keine** Gross/Kleinschreibung-Normalisierung
6. **Keine** Interpunktions-Entfernung

### 5.2 Silbentrennung zusammenfuegen

Trennstrich + Zeilenumbruch entfernen, Wortteile zusammenfuegen:

```
Eingabe:  Mar-\nschlacht → Marschlacht
Eingabe:  Ber-\nge       → Berge
Eingabe:  Ge-\ndanken    → Gedanken
```

Regex (auf normalisierten Text nach Schritt 5.1):

```
s/-\n//g
```

Achtung: Nur einfacher Trennstrich + Zeilenumbruch. Gedankenstriche ("Ge-\ndankenstriche" — mit Bindestrich als Teil des Wortes) werden ebenfalls zusammengefuegt, was korrekt ist ("Gedankenstriche").

Nicht zusammenfuegen: Bindestrich + Leerzeichen + Zeilenumbruch ("quasi- \nhistorisch") — hier ist der Bindestrich Teil der Schreibweise, nicht Silbentrennung.

### 5.3 Zeilenumbrueche zu Leerzeichen

Nach dem Zusammenfuegen der Silbentrennungen:

```
s/\n\n/\x00/g     # Absatzmarker temporaer sichern
s/\n/ /g           # Zeilenumbrueche → Leerzeichen
s/\x00/\n/g        # Absatzmarker wiederherstellen
```

Ergebnis: Fliesstext mit Absaetzen als einzige Zeilenumbrueche.

### 5.4 Markup-Entfernung fuer Basis-CER

Fuer die Berechnung der **Basis-CER** (reiner Text ohne editorische Markierungen) werden die Markup-Zeichen entfernt. Die Entfernungsregeln:

| Markup | Regex | Ersetzung | Beispiel |
|---|---|---|---|
| Unsicher-Marker | `\[\?\]` | (leer) | `Klard[?]` → `Klard` |
| Unleserlich-Marker | `\[\.\.\.(\d+\.\.\.)?\]` | (leer) | `[...3...]` → (leer) |
| Streichung-Klammern | `~~(.*?)~~` | `\1` (Inhalt behalten) | `~~Eltern~~` → `Eltern` |
| Einfuegung-Klammern | `\{(.*?)\}` | `\1` (Inhalt behalten) | `{sehr}` → `sehr` |
| Marginalie-Praefix | `\[Marginalie:\]` | (leer) | |
| Stempel-Praefix | `\[Stempel:(.+?)\]` | `\1` (Inhalt behalten) | `[Stempel: TEXT]` → ` TEXT` |

Reihenfolge der Anwendung:
1. Streichung-Klammern entfernen (Inhalt behalten)
2. Einfuegung-Klammern entfernen (Inhalt behalten)
3. Stempel-Praefix entfernen (Inhalt behalten)
4. Marginalie-Praefix entfernen
5. Unleserlich-Marker entfernen
6. Unsicher-Marker entfernen
7. Whitespace erneut normalisieren (Schritt 5.1.2)

### 5.5 Markup-CER (separat)

Fuer die Bewertung der Markup-Qualitaet (vgl. verification-concept.md 1.6, Markup-Praezision/Recall) wird der Text **mit** Markup verglichen. Hierbei gelten nur die Schritte 5.1-5.3, nicht 5.4.

---

## 6. Beispiele

### 6.1 Tagebuch 1918 (o_szd.72), Seite 1 — Handschrift

**Beschreibung des Faksimiles:** Notizbuchseite, violette Tinte, Zweigs Handschrift. Obere Haelfte: Datum ("Montreux 20. September, Freitag."), dann Fliesstext ohne Absatzeinrueckung. Zeilenumbrueche durch den Seitenrand bedingt. Mehrere Silbentrennungen am Zeilenende. Keine Streichungen, keine Einfuegungen auf dieser Seite.

**Pipeline-Output (Gemini Flash Lite):**
```
Montreux 20. September, Freitag.
Das Tagebuch nach mehr als einem halben Jahre
wieder aufgenommen. Die Zeit war tot, nun wird sie
weiterdings grauenhaft lebendig. Ich war müde des
Sinnlosen, nun findet sich allmählich wieder ein Sinn
der Zeit, oder besser: der immer in dieser Krise verborgene
Sinn beginnt sich zu zeigen. In den letzten Wochen schon,
seit der denkwürdigen Kriegswende in der zweiten Mar-
neschlacht war viel wichtig für mich nebst eigener Arbeit,
jene Polemik vorerst, die mein Aufsatz in der Neuen Zür-
cher Zeitung erregte, dann die Besprechung mit Gieser,
der nur seine allerhöchste Unzufriedenheit einschüchternd
mitteilen wollte und dabei auf eiserne Entschlossenheit stieß
(denn von dem Cadaver Österreichs lasse ich mich nicht
mehr einschüchtern und noch weniger von seinen Diplomaten,
die ins stille und beschämliche Land in den Abgrund eines
falschen Heroismus gestoßen haben.) Dann eine kurze Stelle
Hoffnung: das Friedensangebot, bald zerschellt an der stei-
nern fest aufgetürmten Mauer des andern Imperialismus.
Ein wenig Freiheit der Sinne gab dann die Fahrt in die Ber-
ge: ich habe gelernt, gegen den unnützen Flagellantismus
anzukämpfen, der sich selbst den Tag zerschlägt mit den Ge-
dankenstrichen. Man muss die Kunst lernen, dumpf zu leben
```

**Referenz-Transkription (Protokollkonform):**

(Anmerkung: Da das Faksimile nicht direkt einsehbar ist, kann hier keine tatsaechliche Referenz erstellt werden. Das folgende Beispiel zeigt das Format und illustriert typische Differenzen.)

```
Montreux 20. September, Freitag.
Das Tagebuch nach mehr als einem halben Jahre
wieder aufgenommen. Die Zeit war tot, nun wird sie
weiterdings grauenhaft lebendig. Ich war müde des
Sinnlosen, nun findet sich allmählich wieder ein Sinn
der Zeit, oder besser: der immer in dieser Krise verborgene
Sinn beginnt sich zu zeigen. In den letzten Wochen schon,
seit der denkwürdigen Kriegswende in der zweiten Mar-
neschlacht war viel wichtig für mich nebst eigener Arbeit,
jene Polemik vorerst, die mein Aufsatz in der Neuen Zür-
cher Zeitung erregte, dann die Besprechung mit Gieser[?],
der nur seine allerhöchste Unzufriedenheit einschüchternd
mitteilen wollte und dabei auf eiserne Entschlossenheit stieß
(denn von dem Cadaver Österreichs lasse ich mich nicht
mehr einschüchtern und noch weniger von seinen Diplomaten,
die ins stille und beschämliche[?] Land in den Abgrund eines
falschen Heroismus gestoßen haben.) Dann eine kurze Stelle
Hoffnung: das Friedensangebot, bald zerschellt an der stei-
nern fest aufgetürmten Mauer des andern Imperialismus.
Ein wenig Freiheit der Sinne gab dann die Fahrt in die Ber-
ge: ich habe gelernt, gegen den unnützen Flagellantismus
anzukämpfen, der sich selbst den Tag zerschlägt mit den Ge-
dankenstrichen. Man muss die Kunst lernen, dumpf zu leben
```

**Illustrierte Differenzen:**
- Zeile 11: `Gieser` → `Gieser[?]` — Eigenname in Kurrent ist schwer zu lesen; die Referenz markiert die Unsicherheit, die Pipeline nicht.
- Zeile 16: `beschämliche` → `beschämliche[?]` — ungewoehnliche Wortform, koennte auch "beschämende" sein; die Referenz markiert, die Pipeline nicht.
- Diese Differenzen zeigen das Kernproblem: Die Pipeline setzt fast nie [?]-Marker, auch wo ein menschlicher Leser unsicher waere.

### 6.2 Tagebuch 1918 (o_szd.72), Seite 2 — Abkuerzungen

**Pipeline-Output (Auszug, Zeile 17-22):**
```
für ihn, half ihm in jeder Weise: R. ist jetzt mitten im Kriege
und auf der Höhe seines Ruhmes noch nicht frei von Geld-
sorgen, weil er seine ganze Familie ernährt und eine Reihe von
Freunden unterstützt. Von seinen Taten eine verschwiegene: er
ist in Bern direct zum frz. Cons. gegangen und hat alle Aus-
künfte über J. erwirkt, um ihn gegebenfalls „a fond" verteidi-
```

**Referenz-Transkription (Protokollkonform):**
```
für ihn, half ihm in jeder Weise: R. ist jetzt mitten im Kriege
und auf der Höhe seines Ruhmes noch nicht frei von Geld-
sorgen, weil er seine ganze Familie ernährt und eine Reihe von
Freunden unterstützt. Von seinen Taten eine verschwiegene: er
ist in Bern direct zum frz. Cons. gegangen und hat alle Aus-
künfte über J. erwirkt, um ihn gegebenfalls „à fond" verteidi-
```

**Illustrierte Differenzen:**
- `R.` bleibt `R.` — Abkuerzung wird nicht aufgeloest (Protokoll 2.2)
- `frz. Cons.` bleibt `frz. Cons.` — ebenso
- `"a fond"` → `„à fond"` — hypothetische Differenz: Pipeline koennte das Akzentzeichen verlieren oder die Anfuehrungszeichen normalisieren. Die Referenz transkribiert exakt, was im Faksimile steht.
- `gegebenfalls` — wenn Zweig tatsaechlich "gegebenfalls" schrieb (ohne zweites "n"), steht das so in der Referenz. Kein stilles Korrigieren zu "gegebenenfalls".

### 6.3 Theaterkarte (o_szd.161), Seite 3 — Farbkarte

**Pipeline-Output (Seite 3):**
```
I. Rang Seiten-Loge
Links
27. Febr. 1918
Loge 5 Platz 5
Stadttheater Zürich
```

**Referenz-Transkription (Protokollkonform):**
```
I. Rang Seiten-Loge
Links
27. Febr. 1918
Loge 5 Platz 5
Stadttheater Zürich
```

In diesem Fall ist die Referenz identisch mit dem Pipeline-Output — das Bild zeigt die Karte zusammen mit einer Farbkarte. Die Farbkarte wird nicht transkribiert (Protokoll 4.4). Die Pipeline hat hier korrekt nur den Kartentext transkribiert.

(Zum Vergleich: Bei o_szd.160, Seite 3, transkribiert die Pipeline die Farbkarte mit — dort waere die Referenz leer, was als Halluzination in die CER eingeht.)

### 6.4 Korrespondenz (o_szd.1079), Seite 1 — Briefumschlag

**Pipeline-Output:**
```
Wohlgeboren

Herrn Max Fleischer
Schriftsteller

Komotau
Böhmen
```

**Referenz-Transkription (Protokollkonform):**
```
Wohlgeboren

Herrn Max Fleischer
Schriftsteller

Komotau
Böhmen

[Stempel: WIEN 22.5.01]
```

**Illustrierte Differenzen:**
- Die Pipeline beschreibt den Poststempel in den `notes`, aber nicht in der Transkription. Die Referenz transkribiert den Stempeltext mit dem `[Stempel:]`-Praefix (Protokoll 4.2).
- Ob das ein Pipeline-Fehler ist, haengt von der Perspektive ab: Der Stempel ist Dokumentinhalt (er gehoert zur Postkommunikation). Das Protokoll entscheidet: Stempel transkribieren.

---

## 7. Checkliste fuer Annotierende

Vor Beginn der Annotation eines Objekts:

- [ ] Alle Faksimile-Bilder des Objekts in hoher Aufloesung oeffnen
- [ ] Metadaten pruefen (Sprache, Objekttyp, Haende — aus TEI oder metadata.json)
- [ ] Gruppe des Objekts kennen (bestimmt, welche Schwierigkeiten zu erwarten sind)
- [ ] Dieses Protokoll griffbereit haben

Pro Seite:

- [ ] Zeilenumbrueche beibehalten (Abschnitt 1.1)
- [ ] Silbentrennungen beibehalten (Abschnitt 1.2)
- [ ] Abkuerzungen nicht aufloesen (Abschnitt 2.2)
- [ ] Orthographie nicht modernisieren (Abschnitt 2.4)
- [ ] Unsichere Lesungen mit [?] markieren (Abschnitt 3.2)
- [ ] Unleserliche Stellen mit [...] markieren (Abschnitt 3.2)
- [ ] Streichungen mit ~~...~~ markieren (Abschnitt 3.3)
- [ ] Einfuegungen mit {...} markieren (Abschnitt 3.4)
- [ ] Stempel mit [Stempel: ...] markieren (Abschnitt 4.2)
- [ ] Farbkarten/Digitalisierungsartefakte ignorieren (Abschnitt 4.4)

Nach Abschluss:

- [ ] Seitenzahl pruefen: Stimmt die Anzahl der transkribierten Seiten mit den Bildern ueberein?
- [ ] Leerseiten explizit als leer dokumentieren (leere Transkription)

---

## 8. Offene Entscheidungen

Folgende Punkte konnten in diesem Protokoll nicht abschliessend geklaert werden und muessen im Laufe der Pilotierung (erste 3-5 Referenztranskriptionen) entschieden werden:

1. **Inter-Annotator-Agreement-Test**: Mindestens 2 Objekte sollten von 2 Personen unabhaengig transkribiert werden, um die Reproduzierbarkeit des Protokolls zu pruefen. Welche Objekte?

2. **Kurrent-Ambiguitaeten**: Bei systematischen Kurrent-Verwechslungen (e/n, u/n, s/f) — soll der Annotierende Kontextwissen nutzen ("er muss 'und' gemeint haben, also ist das 'u' kein 'n'") oder rein zeichenbasiert transkribieren? Empfehlung: Kontextwissen nutzen (diplomatische Transkription ist nicht dasselbe wie mechanische Zeichenextraktion), aber bei echtem Zweifel [?] setzen.

3. **Grenzfaelle bei Einfuegungen**: Wenn Text am Rand steht, aber keine klare Einfuegemarke hat — Marginalie oder Einfuegung? Pilotierung wird zeigen, wie haeufig das vorkommt.

4. **Formular-Linearisierung**: Bei komplexen Tabellen (mehrzeilige Zellen, verschachtelte Felder) — ist die Pipe-Konvention ausreichend? Pilotierung mit einem Formular-Objekt noetig.
