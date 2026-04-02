---
title: "Evaluationsergebnisse"
aliases: ["CER-Baseline"]
created: 2026-04-02
updated: 2026-04-02
type: analysis
status: stable
related:
  - "[[verification-concept]]"
  - "[[annotation-protocol]]"
  - "[[data-overview]]"
---

# Evaluationsergebnisse: CER-Baseline der SZD-HTR-Pipeline

Stand: Session 19 (2. April 2026)

---

## 1. Ueberblick

34 Objekte wurden verifiziert — Faksimile-Bild gegen VLM-Transkription geprueft, Fehler dokumentiert und korrigiert. Alle 9 Prompt-Gruppen sind abgedeckt.

| Review-Typ | Objekte | Content-Seiten | Zeichen |
|---|---:|---:|---:|
| Human Approved | 14 | 17 | 10.541 |
| Agent Verified (Batch 1+2) | 12 | 22 | 19.863 |
| Agent Verified (Batch 3) | 8 | 18 | ~8.000 |
| **Gesamt** | **34** | **57** | **~38.400** |

**Human Approved**: Experte prueft Transkription im Frontend-Viewer gegen das Faksimile, korrigiert bei Bedarf, markiert als `approved`.

**Agent Verified**: Claude Code Sub-Agents (Opus 4.6 mit Vision) vergleichen jede Seite Bild-fuer-Bild gegen den Transkriptionstext. Gefundene Fehler werden korrigiert und als `agent_verified` gestempelt (→ [[verification-concept]] §8).

---

## 2. Methodik: Agent-Verifikation

### Workflow

1. Fuer jedes Objekt wird ein Sub-Agent gestartet
2. Der Agent liest alle Seitenbilder aus dem lokalen Backup (`SZD_BACKUP_ROOT`)
3. Der Agent liest die Transkription aus dem Pipeline-JSON
4. Seite fuer Seite: Bild wird gegen Text verglichen, Zeichen fuer Zeichen
5. Ergebnis: Fehlerliste mit Zitat, Korrektur, Schweregrad
6. Fehler werden direkt im JSON korrigiert
7. Review-Metadaten werden geschrieben: `status`, `agent_model`, `errors_found`, `estimated_accuracy`, `edited_pages`

### Einschraenkungen

- Claude als Vision-Judge ist **kein Ersatz** fuer menschliches Expert-Review — es ist ein Cross-Model-Check (Gemini transkribiert, Claude verifiziert)
- Handschrift-Verifikation ist schwieriger als Drucktext — bei ambiguer Handschrift wird "unsicher" markiert
- Der Agent kann Fehler **uebersehen** (kein exhaustiver Beweis)
- Deshalb liegt `agent_verified` im 4-Tier-Modell **unter** `approved`

---

## 3. CER-Ergebnisse nach Prompt-Gruppe

| Gruppe | Objekte | Zeichen | Fehler | Geschaetzte Genauigkeit | Hauptfehlertypen |
|---|---:|---:|---:|---|---|
| Korrekturfahne | 2 | 11.515 | 4 | 99.6–99.9% | Fraktur-Grossschreibung, Wortgrenze |
| Typoskript | 2 | 3.093 | 1–2 | 99.8–99.9% | Fehlende Satzzeichen |
| Zeitungsausschnitt | 2 | 10.032 | 9–12 | 99.7–99.8% | **Fraktur f/s-Verwechslung**, Grossschreibung |
| Formular | 2 | 763 | 3 | 98.5–100% | Handschrift-Felder auf Formularen |
| Konvolut | 1 | 1.655 | 5 | 99.1% | Artikelform (der/den), Grossschreibung |
| Korrespondenz | 13 | ~3.600 | 37–39 | 90–100% | Kurrent-Verwechslungen, Nonsens-Halluzination, Grussformeln |
| Handschrift | 6 | 709 | 1–3 | 99.4% | Fachbegriffe (Recension), Leseunsicherheiten |
| Kurztext | 6 | 235 | 0 | ~100% | (zu kurz fuer Aussage) |
| Tabellarisch | 1 | 457 | 1 | ~99% | (zu wenig Daten) |

### Interpretation

**Gedruckter Text** (Korrekturfahne, Typoskript): **99.6–99.9% Genauigkeit**. Das VLM liest sauberen Druck nahezu fehlerfrei. Die wenigen Fehler betreffen fehlende Satzzeichen und Wortgrenzen an Seitenumbruechen.

**Fraktur** (Zeitungsausschnitt): **99.7–99.8%**, aber mit **systematischen Fraktur-Fehlern**. Das lange s (ſ) wird als "f" gelesen: "selbst**f**eligen" statt "selbst**s**eligen", "gerei**st**e" statt "gerei**ft**e". Dies ist der haeufigste und schwerwiegendste Fehlertyp — er erzeugt falsche, aber existierende Woerter.

**Handschrift** (inkl. Korrespondenz): **90–99.4%**. Breites Spektrum je nach Handschriftqualitaet. Saubere Handschrift (z.B. o_szd.1256, Brief an Fleischer): 100%. Schwierige Handschrift mit tabellarischem Layout (o_szd.1475, Tantiemen-Liste): ~90% — hier versagt die VLM-Linearisierung bei Zuordnung von Betraegen zu Zeilen.

**Formulare**: **98.5–100%**. Gedruckte Formularfelder werden korrekt gelesen, handschriftliche Eintragungen sind schwieriger (Matrik-Nummern, Unterschriften).

---

## 4. Fehlertypen-Analyse

### 4.1 Fraktur-spezifische Fehler (Schweregrad: hoch)

| Fehler | Transkription | Korrekt | Objekt |
|---|---|---|---|
| Langes s → f | selbst**f**eligen | selbst**s**eligen | o_szd.2213 |
| ft ↔ st | gerei**st**e | gerei**ft**e | o_szd.2213 |
| Fraktur a → Punkt | s**.g**en | s**ag**en | o_szd.2296 |

**Ursache**: Gemini Flash Lite verwechselt visuell aehnliche Fraktur-Glyphen. Das lange ſ (Unicode U+017F) sieht dem f aehnlich; die Ligaturen ft und st sind in Fraktur nahezu identisch.

**Haeufigkeit**: 3 Faelle in ~10.000 Fraktur-Zeichen (~0.03%). Selten, aber sinnentstellend.

### 4.2 Kurrent-Buchstabenverwechslungen (Schweregrad: hoch)

*Neu in Session 19 — 8 Korrespondenzen an Max Fleischer (~1901-1902), alle Kurrent-Handschrift.*

| Fehler | Transkription | Korrekt | Objekt |
|---|---|---|---|
| h ↔ I | muß ich jetzt **Ihre** schließen | muß ich jetzt **hier** schließen | o_szd.1079 |
| St ↔ H | **Hud. inr.** | **Stud. iur.** | o_szd.1081 |
| r ↔ v | gracioesa **devin** | gracioesa **darin** | o_szd.1081 |
| L ↔ B | **Besten** Gruss | **Liebsten** Gruss | o_szd.1100 |
| Nonsens | **Langentour Kantgewalt** | **Laufenden** | o_szd.1090 |

**Ursache**: Kurrent-Minuskeln weichen systematisch von Antiqua-Formen ab. Gemini (trainiert primaer auf Antiqua/Drucktext) erkennt die Unterschiede nicht zuverlaessig. Besonders betroffen: hastige Schrift auf kleinen Postkarten, rote Tinte auf Bildhintergrund.

**Haeufigkeit**: 33 Fehler in 8 Objekten (~4 pro Objekt). Genauigkeits-Spread: 90% (hastiger Kurrent) bis 99.7% (sauberer Kurrent). Groesster Einflussfaktor ist nicht der Prompt, sondern die Schriftqualitaet des Originals.

**Besonders problematisch: Nonsens-Halluzination.** Bei unleserlichem Kurrent erfindet Gemini echte Woerter statt `[?]` zu setzen. Dies macht `marker_density` als Quality-Signal wertlos — das Modell signalisiert Unsicherheit nicht.

### 4.3 Halluziniertes "An" auf Adressseiten (Schweregrad: niedrig)

In 3 von 8 Korrespondenz-Objekten halluziniert Gemini ein "An" vor dem Adressaten auf Postkarten-Adressseiten. Auf den Originalen steht kein "An" — die Adresse beginnt direkt mit dem Namen.

**Fix**: Hinweis im Gruppen-Prompt I (Korrespondenz) oder Post-Processing-Regel.

### 4.4 Grossschreibung (Schweregrad: niedrig)

| Fehler | Transkription | Korrekt | Objekt |
|---|---|---|---|
| Eigenname | zweig | Zweig | o_szd.127 (3x) |
| Buchtitel | silberne Saiten | Silberne Saiten | o_szd.2296 |
| Substantiv | hingabe | Hingabe | o_szd.2213 |

**Ursache**: VLM normalisiert gelegentlich Grossschreibung weg, besonders bei Handschrift und Fraktur, wo Gross-/Kleinbuchstaben visuell weniger distinkt sind.

### 4.5 Fehlende Woerter/Zeichen (Schweregrad: mittel)

| Fehler | Transkription | Korrekt | Objekt |
|---|---|---|---|
| Fehlendes Wort | bloß angefuehlt | **nicht** bloß angefuehlt | o_szd.1888 |
| Wortgrenze | erhoben — Hand — | erhoben**e Hand** — | o_szd.1888 |
| Fehlende Anfuehrung | ADEPTS IN SELF | **"**ADEPTS IN SELF | o_szd.102 |

### 4.6 Strukturfehler bei tabellarischen Layouts (Schweregrad: hoch)

| Fehler | Beschreibung | Objekt |
|---|---|---|
| Betraege falscher Zeile zugeordnet | ffr 10.340 auf Aug-Zeile statt Okt-Zeile | o_szd.1475 |

**Ursache**: VLMs linearisieren Tabellen von oben nach unten. Wenn Betraege rechtsbuendig und Beschreibungen linksbuendig stehen, kann die Zuordnung verrutschen. Dies ist der schwerwiegendste systematische Fehler im Korpus.

---

## 5. Implikationen fuer die Pipeline

### Was gut funktioniert

- **Gedruckter Text** (Antiqua): Nahezu perfekt, keine systematischen Fehler
- **Saubere Handschrift**: Hohe Genauigkeit bei lesbarer Kurrentschrift
- **Seitentyp-Klassifikation**: content/blank/color_chart korrekt (nach Fix der Farbkarten-Erkennung)

### Wo Verbesserungsbedarf besteht

1. **Fraktur-Texte**: Post-Processing-Schritt fuer bekannte f/s-Verwechslungen erwaegen (Woerterbuch-Abgleich)
2. **Tabellarische Layouts**: Gruppe E (tabellarisch) und Tantiemen-Listen brauchen moeglicherweise einen speziellen Prompt oder Layout-Analyse-Vorschritt
3. **Grossschreibung**: Eigennamen-Erkennung als Nachverarbeitung (NER-basiert) koennte systematische Fehler beheben

### Naechste Schritte

- Weitere Objekte agent-verifizieren — 20 von 2107 verifiziert, Korrespondenzen-Sample jetzt 13 Objekte
- Prompt-Ablation mit den 18 GT-Objekten (jetzt moeglich, da CER-Baseline steht)
- Fraktur-spezifischen Post-Processing-Schritt evaluieren
- `duplicate_pages` False-Positive fixen (Color-Chart-Seiten ausschliessen)
- DWR-Score gegen Agent-Verifikation validieren (korreliert DWR mit tatsaechlicher Fehlerrate?)
