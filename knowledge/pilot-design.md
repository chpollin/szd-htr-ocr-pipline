---
title: "Pilot-Design (historisch)"
aliases: ["Pilot"]
created: 2026-04-01
updated: 2026-04-02
type: concept
status: historical
related:
  - "[[annotation-protocol]]"
  - "[[verification-concept]]"
---

> **Historisches Dokument.** Dieses Design wurde nicht ausgefuehrt. Stattdessen wurden zwei empirische Evaluationen durchgefuehrt, die dieselben Fragen beantworten:
> - **27-Objekt-Konsensus-Validierung** ([[verification-concept]] §4.7): CER + word_overlap, 4-Tier-Klassifikation.
> - **18-Objekt-GT-Pipeline** ([[verification-concept]] §7.1): 3-Modell-Merge, 46 Content-Seiten, Expert-Review.
>
> Das Design bleibt als Referenz fuer die Sampling-Kriterien und Eskalationsschwellen erhalten.

# Pilot-Design: 5 Seiten zur Erstbewertung der Pipeline-Qualitaet

Voraussetzung: [[annotation-protocol]] (Konventionen), [[verification-concept]] (Metriken)

---

## Zweck

Bevor das 30-Objekt-Referenz-Sample erstellt wird, pruefen wir 5 einzelne Seiten manuell gegen die Faksimiles. Der Pilot beantwortet:

1. In welcher Groessenordnung liegt die CER? (2%, 10%, 20%?)
2. Welche Fehlertypen dominieren? (Zeichenfehler, Auslassungen, Halluzinationen, Strukturfehler?)
3. Unterscheidet sich die Fehlerrate zwischen den Gruppen so stark, wie vermutet?
4. Funktioniert das Annotationsprotokoll in der Praxis?

Ohne diesen Pilot ist das 30-Objekt-Sample blind designed — wir wuessten nicht, ob wir die richtigen Objekte und die richtige Granularitaet gewaehlt haben.

**Zeitaufwand:** 2-3 Stunden (5 Seiten, je 20-40 Minuten je nach Schwierigkeit).

---

## 1. Pilot-Sample: 5 Seiten

### Auswahlkriterien

- 5 verschiedene Gruppen (maximale Varianz in Dokumenttyp)
- Mindestens 1 Seite, die als schwierig gilt (Kurrent, Fraktur)
- Mindestens 1 Seite, die als leicht gilt (Typoskript/Formular)
- Mindestens 2 Sprachen
- Nur Seiten mit substantiellem Text (>500 Zeichen im Pipeline-Output)
- Nur aus den 16 bereits transkribierten Objekten (keine neuen API-Calls)

### Die 5 Seiten

**Seite 1: Kurrent-Handschrift (Gruppe A)**

| | |
|---|---|
| Objekt | o_szd.72 — Tagebuch 1918 |
| Seite | 2 |
| Gruppe | A: Handschrift |
| Sprache | Deutsch |
| Zeichen (Pipeline) | ~1800 |
| Erwartete Schwierigkeit | Schwer |
| Faksimile | https://gams.uni-graz.at/o:szd.72/IMG.2 |

**Begruendung:** Zweigs Kurrent-Handschrift ist die Kernherausforderung des Projekts (~100 Handschrift-Objekte, ~1186 Korrespondenzen). Seite 2 statt Seite 1 gewaehlt, weil sie diagnostisch ergiebiger ist: Abkuerzungen ("R.", "frz. Cons.", "J."), ein franzoesisches Zitat ("a fond"), der potenzielle Schreibfehler "gegebenfalls", und zahlreiche Eigennamen (Chapiro, Rolland, Kiow). Jeder dieser Punkte testet eine andere Konvention des Annotationsprotokolls.

---

**Seite 2: Fraktur-Zeitungsausschnitt (Gruppe H)**

| | |
|---|---|
| Objekt | o_szd.2232 — "Zwei Einsame" (Stimmen der Gegenwart, 1901) |
| Seite | 1 |
| Gruppe | H: Zeitungsausschnitt |
| Sprache | Deutsch |
| Zeichen (Pipeline) | ~4200 |
| Erwartete Schwierigkeit | Schwer |
| Faksimile | https://gams.uni-graz.at/o:szd.2232/IMG.1 |

**Begruendung:** Fraktur-Erkennung ist die groesste offene Frage (312 Zeitungsausschnitte in der Aufsatzablage). Bisher kein einziger Fraktur-Test verifiziert. Die Pipeline-notes sagen "Der Text ist in Fraktur gesetzt" und melden "high confidence" — ob das stimmt, wissen wir nicht. Die Seite ist lang (Zweigs Fruehwerk "Zwei Einsame", S. 330-331 der Zeitschrift), was eine belastbare CER-Berechnung erlaubt.

Besonderheit: Dieser Text existiert vermutlich in gedruckter Form (Erstpublikation 1901). Wenn eine publizierte Fassung auffindbar ist, kann sie als Referenz dienen — dann entfaellt die manuelle Transkription fuer diese Seite und wir erhalten eine besonders zuverlaessige Ground Truth.

---

**Seite 3: Korrespondenz-Handschrift (Gruppe I)**

| | |
|---|---|
| Objekt | o_szd.1079 — Brief an Max Fleischer, 22. Mai 1901 |
| Seite | 3 |
| Gruppe | I: Korrespondenz |
| Sprache | Deutsch |
| Zeichen (Pipeline) | ~2000 |
| Erwartete Schwierigkeit | Mittel |
| Faksimile | https://gams.uni-graz.at/o:szd.1079/IMG.3 |

**Begruendung:** Korrespondenzen sind die groesste Sammlung (1186 Objekte). Seite 3 ist der eigentliche Brieftext (Seiten 1-2 sind Umschlag). Zweigs Jugendhandschrift (1901, Alter 19) — moeglicherweise anders als seine spaetere Handschrift. Der Text ist inhaltlich reich (Literaturbezuege, Eigennamen, Ortsnamen), was Halluzinations-Detection ermoeglicht: Wenn die Pipeline einen Namen falsch liest, koennen wir das inhaltlich pruefen.

---

**Seite 4: Tabellarische Struktur (Gruppe E)**

| | |
|---|---|
| Objekt | o_szd.143 — Hauptbuch |
| Seite | 5 |
| Gruppe | E: Tabellarisch |
| Sprache | Deutsch |
| Zeichen (Pipeline) | 1757 |
| Erwartete Schwierigkeit | Mittel (Struktur), leicht (Lesbarkeit) |
| Faksimile | https://gams.uni-graz.at/o:szd.143/IMG.5 |

**Begruendung:** Tabellarische Dokumente (Gruppe E, ~230 Objekte) sind strukturell voellig anders als Fliesstext. Das Hauptbuch-Inhaltsverzeichnis hat Spalten (Titel | Seitenzahl), die die Pipeline linearisieren muss. Hier testen wir nicht primaer Zeichengenauigkeit, sondern Strukturtreue: Stimmt die Zuordnung von Titeln zu Seitenzahlen? Werden Spalten korrekt getrennt?

---

**Seite 5: Englisches Formular (Gruppe C)**

| | |
|---|---|
| Objekt | o_szd.160 — Certified Copy of an Entry of Marriage |
| Seite | 1 |
| Gruppe | C: Formular |
| Sprache | Englisch |
| Zeichen (Pipeline) | ~1300 |
| Erwartete Schwierigkeit | Leicht |
| Faksimile | https://gams.uni-graz.at/o:szd.160/IMG.1 |

**Begruendung:** Die leichteste Seite im Sample — dient als Kontrollfall. Wenn selbst hier Fehler auftreten, ist das Pipeline-Problem grundsaetzlicher als angenommen. Testet ausserdem: englische Sprache, Formular-Linearisierung (Spaltenstruktur: When married | Name | Age | ...), und Unterscheidung zwischen gedrucktem Formulartext und handschriftlichen Eintraegen.

### Ueberblick

| Nr. | Objekt | Gruppe | Sprache | ~Zeichen | Schwierigkeit | Testet primaer |
|---|---|---|---|---|---|---|
| 1 | o_szd.72 S.2 | A Handschrift | DE | 1800 | schwer | Kurrent, Abkuerzungen |
| 2 | o_szd.2232 S.1 | H Zeitungsausschnitt | DE | 4200 | schwer | Fraktur-Erkennung |
| 3 | o_szd.1079 S.3 | I Korrespondenz | DE | 2000 | mittel | Brief-Handschrift, Eigennamen |
| 4 | o_szd.143 S.5 | E Tabellarisch | DE | 1757 | mittel | Struktur, Tabellen |
| 5 | o_szd.160 S.1 | C Formular | EN | 1300 | leicht | Kontrollfall, Englisch |
| | | | **Gesamt** | **~11000** | | |

---

## 2. Pruefprotokoll

### 2.1 Setup

1. Faksimile in hoher Aufloesung oeffnen (GAMS-URL oder lokales Backup-Bild)
2. Pipeline-Output der betreffenden Seite oeffnen (aus dem Ergebnis-JSON, Feld `result.pages[N].transcription`)
3. `annotation-protocol.md` griffbereit haben
4. Fehlerprotokoll-Tabelle anlegen (Vorlage unten)

### 2.2 Vergleichsprozedur

**Schritt 1: Grob-Scan (5 Minuten pro Seite)**

Faksimile und Pipeline-Output nebeneinander. Text absatzweise ueberfliegen. Grobe Abweichungen notieren:
- Fehlende Passagen (Auslassungen)
- Offensichtlich falscher Text (Halluzinationen)
- Strukturprobleme (falsche Reihenfolge, fehlende Seitenteile)

**Schritt 2: Wort-fuer-Wort-Vergleich (15-30 Minuten pro Seite)**

Zeile fuer Zeile durch das Faksimile gehen. Jedes Wort im Pipeline-Output mit dem Faksimile abgleichen. Bei Abweichung:
- Referenz-Lesung notieren (was steht tatsaechlich im Faksimile?)
- Pipeline-Lesung notieren (was hat die Pipeline produziert?)
- Fehlertyp klassifizieren (aus der Taxonomie in verification-concept.md 1.5)

**Schritt 3: Referenz-Transkription erstellen (parallel zu Schritt 2)**

Waehrend des Wort-fuer-Wort-Vergleichs die Referenz-Transkription der Seite erstellen. Diese folgt den Konventionen aus `annotation-protocol.md`. Am Ende liegt fuer jede der 5 Seiten eine vollstaendige Referenz vor, gegen die CER berechnet werden kann.

### 2.3 Fehlerprotokoll-Format

Pro Seite eine Tabelle in folgendem Format:

```markdown
## Fehlerprotokoll: [Objekt-ID], Seite [N]

| Nr | Zeile | Position | Referenz | Pipeline | Fehlertyp | Anmerkung |
|----|-------|----------|----------|----------|-----------|-----------|
| 1  | 3     | Wort 5   | Gieser   | Gieser   | (korrekt) | —         |
| 2  | 17    | Wort 3   | à        | a        | Zeichenfehler | Akzent fehlt |
| 3  | 21    | Wort 8-9 | —        | [Text]   | Halluzination | Wort nicht im Faksimile |
| 4  | 5     | Wort 12  | Cons.    | Consul   | Zeichenfehler | Abkuerzung aufgeloest |
```

**Spalten:**
- **Nr**: Laufende Nummer
- **Zeile**: Zeilennummer im Pipeline-Output (ungefaehr)
- **Position**: Wort-Position in der Zeile (ungefaehr, muss nicht exakt sein)
- **Referenz**: Was tatsaechlich im Faksimile steht (leer bei Halluzination)
- **Pipeline**: Was die Pipeline produziert hat (leer bei Auslassung)
- **Fehlertyp**: Einer von: `Zeichenfehler`, `Wortfehler`, `Auslassung`, `Halluzination`, `Strukturfehler`, `Markup-Fehler`, `Duplikat`, `Anachronismus`
- **Anmerkung**: Optionaler Kommentar (z.B. "typische Kurrent-Verwechslung e/n")

### 2.4 CER-Berechnung

Nach Erstellung der 5 Referenz-Transkriptionen:

**Option A: Script von Lane 3 (empfohlen)**

Lane 3 schreibt ein kleines Python-Script, das:
1. Referenz-Text und Pipeline-Text einliest
2. Normalisierung gemaess annotation-protocol.md Abschnitt 5 anwendet
3. Levenshtein-Distanz berechnet
4. CER = (S + D + I) / N ausgibt

Abhaengigkeit: Nur `python-Levenshtein` oder Eigenimplementierung (edit distance ist ~20 Zeilen Code).

**Option B: Manuelle Schaetzung (Fallback)**

Falls kein Script verfuegbar: Fehler im Protokoll zaehlen und durch Gesamtzeichenzahl teilen.

Formel: CER ≈ (Anzahl fehlerhafter Zeichen) / (Zeichenzahl der Referenz)

Das ist ungenauer als Levenshtein (ueberschaetzt Insertions, unterschaetzt Deletions), aber als Pilot-Schaetzung ausreichend.

### 2.5 Ergebnis-Ablage

Pro gepruefter Seite werden zwei Dateien erzeugt:

1. **Referenz-Transkription**: `results/groundtruth/[object_id]_page[N]_reference.txt`
   Reiner Text, Konventionen gemaess annotation-protocol.md.

2. **Fehlerprotokoll**: `results/groundtruth/[object_id]_page[N]_errors.md`
   Markdown-Tabelle im Format aus 2.3.

Verzeichnis `results/groundtruth/` muss angelegt werden. (Lane 3 kann das in die Projektstruktur aufnehmen.)

---

## 3. Erwartete Erkenntnisse

### 3.1 Was wir vorher nicht wissen

| Frage | Aktueller Wissensstand | Was der Pilot klaert |
|---|---|---|
| CER bei Kurrent-Handschrift | Unbekannt. Pipeline sagt "high confidence". Literatur: 1.7% (modern EN) bis 71% (historisch DE). | Konkreter Wert fuer Zweigs Handschrift. |
| CER bei Fraktur | Voellig unbekannt. Kein einziger Fraktur-Test verifiziert. | Ob Fraktur ein Blocker ist (CER >30%) oder beherrschbar (<10%). |
| Dominante Fehlertypen | Hypothese: Zeichenfehler bei Kurrent (e/n, s/f), Strukturfehler bei Tabellen. Unbestaetigt. | Empirische Verteilung der Fehlertypen. |
| Halluzinationsrate | Unbekannt. Pipeline setzt fast keine [?]-Marker — das koennte heissen "alles korrekt" oder "alles unkritisch uebernommen". | Ob die Pipeline Text erfindet, der nicht im Faksimile steht. |
| Strukturtreue bei Tabellen | Unbekannt. Pipeline linearisiert Spalten — ob die Zuordnung stimmt, ist ungeprueft. | Ob Tabellen-Linearisierung funktioniert oder systematisch fehlschlaegt. |
| Protokoll-Tauglichkeit | Ungetestet. Das Annotationsprotokoll ist theoretisch, nicht erprobt. | Wo das Protokoll Luecken hat, wo Entscheidungen fehlen. |
| Prompt-Wirksamkeit | Evidenz aus Session 8: Vorsichts-Guidance in Gruppen-Prompts (Kurrent e/n, Fraktur s/f) wird ignoriert — 0 Marker bei 6711 Zeichen Kurrent. Strukturelle Guidance (Briefformat) wird befolgt. | Ob die Pipeline trotzdem korrekt liest (dann ist die fehlende Unsicherheitsmarkierung nur ein Darstellungsproblem) oder ob sie still falsch liest (dann ist die fehlende Markierung ein ernstes Qualitaetsproblem). |

### 3.2 Entscheidungen, die vom Pilot abhaengen

**A. Sample-Zusammensetzung (30-Objekt-Plan)**

| Pilot-Befund | Konsequenz fuer das Sample |
|---|---|
| CER bei Kurrent >15% | Mehr Handschrift-Objekte ins Sample (von 5 auf 8), um Fehlervarianz zu verstehen |
| CER bei Fraktur >20% | Fraktur als eigene Evaluationskategorie, nicht unter "Zeitungsausschnitt" subsumiert |
| Strukturfehler dominieren bei Tabellen | Eigene Metrik fuer Strukturtreue definieren (CER reicht nicht), mehr Tabellen-Objekte |
| Halluzinationen haeufig | Halluzinationsrate als eigene Metrik im Sample tracken, Objekte mit viel Kontext priorisieren |
| CER ueber alle Gruppen <5% | Sample kann kleiner ausfallen (20 statt 30 Objekte reichen fuer Feinjustierung) |

**B. Prompt-System**

| Pilot-Befund | Konsequenz |
|---|---|
| Typische Kurrent-Verwechslungen (e/n, s/f) trotz Gruppen-Prompt A | Prompt A versagt bei seinem Kernziel → Prompt-Ueberarbeitung vor weiterem Batch |
| Fraktur-spezifische Fehler (s/f, ch/ck) trotz Gruppen-Prompt H | Prompt H braucht konkretere Beispiele oder anderes Format |
| Abkuerzungen werden inkonsistent aufgeloest | System-Prompt braucht explizitere Regel: "Abkuerzungen NICHT aufloesen" |

**C. Pipeline-Architektur**

| Pilot-Befund | Konsequenz |
|---|---|
| CER bei irgendeiner Gruppe >30% | Cross-Model-Verification (Abschnitt 4 in verification-concept.md) wird Pflicht, nicht optional |
| Halluzinationen bei >5% der Seiten | Zweiter LLM-Durchlauf als Verification, nicht nur als Korrektur |
| CER durchgehend <5% | quality_signals und einfaches needs_review reichen, Cross-Model-Verification ist nice-to-have |

### 3.3 Eskalationsschwellen

| CER-Bereich | Bewertung | Handlung |
|---|---|---|
| **< 5%** | Sehr gut. Pipeline funktioniert fuer diese Gruppe. | Weiter mit Batch, quality_signals als Triage. |
| **5-15%** | Brauchbar mit Review. Typisch fuer schwierige Handschrift. | Batch fortsetzen, Cross-Model-Verification fuer diese Gruppe einplanen. |
| **15-30%** | Problematisch. Zu viele Fehler fuer unbeaufsichtigten Batch. | Prompt-Ueberarbeitung fuer diese Gruppe, dann erneuter Pilot. Batch nur mit manuellem Review. |
| **> 30%** | Unbrauchbar. Die Pipeline ist fuer diese Gruppe nicht geeignet. | Grundlegende Aenderung: anderes Modell, Preprocessing, oder Gruppe vom Batch ausschliessen. |

Diese Schwellen gelten pro Gruppe, nicht aggregiert. Eine CER von 3% bei Typoskripten und 25% bei Kurrent ergibt eine aggregierte CER von ~14%, die die Schwere des Kurrent-Problems verdeckt.

---

## 4. Anpassung des 30-Objekt-Plans

### 4.1 Vorab-Regeln

Folgende Anpassungen am Sample (verification-concept.md Abschnitt 1) werden vor dem Pilot festgelegt und automatisch angewendet:

**Regel 1: Schwierigkeits-Gewichtung**

Wenn eine Gruppe im Pilot CER >15% zeigt: Die Objektzahl fuer diese Gruppe im 30-Objekt-Sample verdoppeln (von 3 auf 6 bzw. von 5 auf 8). Dafuer Objekte aus Gruppen mit CER <5% reduzieren (von 4 auf 2).

Begruendung: Fuer gut funktionierende Gruppen reicht eine kleinere Stichprobe zur Bestaetigung. Fuer problematische Gruppen brauchen wir mehr Datenpunkte, um die Fehlervarianz zu verstehen.

**Regel 2: Fehlertyp-spezifische Ergaenzung**

Wenn ein Fehlertyp >30% aller Fehler ausmacht, gezielt Objekte ins Sample aufnehmen, die diesen Fehlertyp provozieren:

| Dominanter Fehlertyp | Ergaenzung im Sample |
|---|---|
| Zeichenfehler (Kurrent e/n, s/f) | Mehr Handschrift-Objekte verschiedener Haende (Zweig, Lotte, Rieger) |
| Auslassungen | Mehr lange Dokumente (>10 Seiten), um Dropout-Muster zu finden |
| Halluzinationen | Mehr Objekte mit wenig Text (Kurztexte, Karten) — dort ist Halluzination leichter erkennbar |
| Strukturfehler | Mehr Tabellen und Mehrspalten-Dokumente |
| Anachronismen | Mehr Fraktur-Objekte, um systematischen Bias zu quantifizieren |

**Regel 3: Protokoll-Korrektur**

Wenn der Pilot Luecken im Annotationsprotokoll aufdeckt (Entscheidungen, die nicht getroffen sind, Grenzfaelle, die zu verschiedenen Annotierungen fuehren): Protokoll ergaenzen, bevor das 30-Objekt-Sample beginnt. Das Protokoll blockiert das Sample.

**Regel 4: Metriken-Ergaenzung**

Wenn CER allein die Qualitaetsprobleme nicht erfasst (z.B. Strukturfehler bei Tabellen, wo die Zeichen stimmen aber die Zuordnung falsch ist): Zusaetzliche Metrik definieren. Kandidat: Strukturtreue-Score (Anteil der korrekten Spalten-Zuordnungen).

### 4.2 Was der Pilot NICHT aendert

- Die Grundentscheidung fuer ein manuelles Referenz-Sample (es gibt keine Alternative, die absolute Korrektheit misst)
- CER als Primaermetrik
- Die Normalisierungsregeln (die sind logisch begruendet, nicht empirisch)
- Die quality_signals-Spezifikation (wird sofort implementiert, unabhaengig vom Pilot)

---

## 5. Durchfuehrung

### 5.1 Reihenfolge

Die 5 Seiten in dieser Reihenfolge pruefen:

1. **o_szd.160 S.1 (Formular, EN)** — Aufwaermpruefung. Erwartbar wenig Fehler. Der Operator gewoehnt sich an die Prozedur und das Protokoll.
2. **o_szd.143 S.5 (Hauptbuch, Tabelle)** — Strukturtest. Neue Herausforderung (Tabelle), aber gut lesbar.
3. **o_szd.1079 S.3 (Brief, Handschrift)** — Mittlere Schwierigkeit. Briefhandschrift 1901.
4. **o_szd.72 S.2 (Tagebuch, Kurrent)** — Schwer. Kurrent mit Abkuerzungen.
5. **o_szd.2232 S.1 (Fraktur, Zeitungsausschnitt)** — Schwer. Die kritische Frage.

Begruendung: Leicht → schwer. Der Operator baut Routine auf, bevor die schwierigen Seiten kommen. Die schwierigsten Seiten am Ende, wenn die Fehlerklassifikation schon sitzt.

### 5.2 Abschluss-Dokument

Nach Abschluss des Pilots ein kurzes Ergebnis-Dokument schreiben (`knowledge/pilot-results.md`):

```markdown
# Pilot-Ergebnisse

## CER pro Seite

| Seite | Gruppe | CER | WER | Fehler gesamt | Dominanter Fehlertyp |
|---|---|---|---|---|---|

## Fehlertyp-Verteilung (aggregiert)

| Fehlertyp | Anzahl | Anteil |
|---|---|---|

## Konsequenzen fuer das 30-Objekt-Sample

(Welche Regeln aus Abschnitt 4 greifen?)

## Protokoll-Luecken

(Was fehlt im Annotationsprotokoll?)
```

### 5.3 Checkliste vor Start

- [ ] Zugang zu GAMS-Bildern pruefen (oder lokale Backup-Bilder verwenden)
- [ ] annotation-protocol.md gelesen und verstanden
- [ ] Verzeichnis `results/groundtruth/` angelegt
- [ ] Fehlerprotokoll-Vorlage vorbereitet (5 Dateien)
- [ ] Optional: CER-Script von Lane 3 bereit (oder manuelle Berechnung planen)
