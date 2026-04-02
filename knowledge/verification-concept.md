---
title: "Verifikationskonzept"
aliases: ["Verifikationskonzept"]
created: 2026-04-01
updated: 2026-04-02
type: concept
status: stable
related:
  - "[[annotation-protocol]]"
  - "[[evaluation-results]]"
  - "[[data-overview]]"
  - "[[layout-analysis]]"
---

# Verifikationskonzept: Qualitaetsmessung der SZD-HTR-Pipeline

Adressaten: Lane 1 (Frontend/Viewer), Lane 3 (Pipeline-Implementierung)

---

## Ausgangslage

Die Pipeline hat 601 Objekte transkribiert (Stand Session 14, 2026-04-02), davon alle ausser 1 mit Selbsteinschaetzung "high confidence" (o_szd.277, Konvolut mit ueberlappenden Korrekturen, erhielt "medium"). 1 Objekt (o_szd.147, 64 Bilder) hat ein leeres Ergebnis (Pipeline-Bug). Die Selbsteinschaetzung ist nahezu wertlos: Sie diskriminiert nicht zwischen einem sauber gedruckten Typoskript (o_szd.100) und einer fuenfseitigen Kurrent-Handschrift (o_szd.72, Tagebuch 1918). In ca. 57.000 transkribierten Zeichen ueber alle 16 Objekte finden sich genau ein `[...]`-Marker und ein `[?]`-Marker. Das Modell nutzt also weder das Konfidenz-Feld noch die Inline-Markup-Konventionen als zuverlaessiges Unsicherheitssignal.

**Empirischer Befund (Stand Session 8):** Die Gruppen-Prompts weisen das Modell explizit an, bei Kurrent-Ambiguitaeten (e/n, s/f) Unsicherheitsmarker zu setzen. Ergebnis: Null Marker bei 6.711 Zeichen Kurrent-Handschrift (o_szd.72). Die Vorsichts-Guidance in den Prompts wird faktisch ignoriert. Strukturelle Guidance (Briefformat bei Korrespondenz) wird hingegen befolgt. Die quality_signals flaggen aktuell 10/16 Objekte (63%) als `needs_review` — das ist zu viel fuer effektive Triage und zeigt, dass die Schwellenwerte vor Kalibrierung zu aggressiv sind.

**Empirischer Befund (Stand Session 14):** quality_signals v1.4 aktiv (8 Signale + page.type + DWR). 27-Objekt-Modellkonsensus-Validierung mit verbesserter Metrik (word_overlap + 4-Tier-Klassifikation) abgeschlossen. 18-Objekt-GT-Pipeline mit 3-Modell-Merge (Flash Lite + Flash + Pro) laeuft. Bleed-Through als neues Fehlermuster identifiziert und im System-Prompt adressiert (Regel 9).

Daraus ergeben sich drei Probleme, die dieses Dokument adressiert:
1. Es gibt keine Ground Truth, um die tatsaechliche Fehlerrate zu messen.
2. Es gibt keinen funktionierenden Mechanismus, um problematische Transkriptionen fuer menschliche Pruefung zu markieren.
3. Es ist unbekannt, ob die Gruppen-Prompts die Transkriptionsqualitaet tatsaechlich verbessern.

---

## 1. Ground Truth

### 1.1 Zweck

Ein manuell verifiziertes Referenz-Sample dient zwei Zwecken:
- **Fehlertypologie**: Welche Fehler macht die Pipeline? (Zeichenverwechslungen, Auslassungen, Halluzinationen, Strukturfehler)
- **Metrische Basislinie**: Wie hoch ist die Fehlerrate, aufgeschluesselt nach Gruppe, Sprache und Schwierigkeitsgrad?

Ohne diese Basislinie sind alle weiteren Optimierungen (Prompt-Tuning, Provider-Vergleich, Bildgroessenanpassung) nicht messbar.

### 1.2 Sample-Groesse

Die Minimalanforderung ergibt sich aus zwei Faktoren:

**Gruppenabdeckung.** Alle 9 aktiven Prompt-Gruppen (A-I) muessen im Sample vertreten sein. Pro Gruppe mindestens 2-3 Objekte, um Intra-Gruppen-Varianz abschaetzen zu koennen (ein einzelnes Objekt kann nicht repraesentativ sein — die Handschrift-Qualitaet schwankt innerhalb derselben Gruppe erheblich).

**Seitenvolumen.** CER und WER sind zeichenbasierte bzw. wortbasierte Metriken. Ihre Aussagekraft haengt nicht von der Anzahl der Objekte, sondern von der Zeichenmenge ab. Ein 1-seitiges Typoskript mit 500 Zeichen und ein 39-seitiges Tagebuch produzieren sehr unterschiedlich belastbare CER-Werte. Mindestens 80-100 transkribierte Seiten mit substantiellem Text (nicht Leerseiten oder Farbkarten) sind noetig, um auf Gruppen-Ebene belastbare Mediane zu bilden.

**Empfohlene Sample-Groesse: 30 Objekte / ca. 100-150 Textseiten.**

Das ist ein Kompromiss zwischen statistischer Belastbarkeit und manuellem Aufwand. Der Engpass ist nicht die API (30 Transkriptionen kosten <1 USD), sondern die manuelle Referenztranskription. Bei geschaetzten 15-45 Minuten pro Seite (je nach Schwierigkeitsgrad) sind 100 Seiten ein erheblicher Aufwand.

### 1.3 Sampling-Kriterien

Das Sample muss drei Dimensionen abdecken:

**Dimension 1: Gruppen (Pflicht — alle 9)**

| Gruppe | Population (ca.) | Sample | Begruendung |
|---|---|---|---|
| A Handschrift | ~100 | 5 | Kerngruppe, hoechste erwartete Fehlerrate |
| B Typoskript | ~300 | 4 | Groesste Gruppe bei Lebensdokumenten, erwartbar niedrige Fehlerrate |
| C Formular | ~25 | 3 | Kleine Population, Minimum |
| D Kurztext | ~30 | 2 | Kleine Population, wenig Text pro Objekt |
| E Tabellarisch | ~230 | 3 | Bisher ungetestet, Registerstrukturen |
| F Korrekturfahne | ~55 | 3 | Mischtyp (Druck + Handschrift), methodisch interessant |
| G Konvolut | ~24 | 2 | Einziges bisheriges "medium"-Objekt (o_szd.277), heterogene Materialien |
| H Zeitungsausschnitt | ~312 | 4 | Fraktur-Frage offen, grosse Population |
| I Korrespondenz | ~1186 | 5 | Groesste Sammlung, nur 1 bisheriger Test |
| **Gesamt** | | **31** | (Pilot kann auf 30 reduzieren, wenn Gruppe mit CER <5%) |

**Dimension 2: Schwierigkeitsspektrum (innerhalb jeder Gruppe)**

Jede Gruppe sollte mindestens enthalten:
- 1 "leichtes" Objekt (klare Schrift, guter Kontrast, wenig Text)
- 1 "mittleres" Objekt (typischer Vertreter)
- 1 "schwieriges" Objekt (blasse Tinte, enge Schrift, Ueberlagerungen, Fraktur)

Schwierigkeitsindikatoren, die aus den Metadaten ableitbar sind:
- Schreibinstrument: Bleistift und Durchschlag sind schwieriger als Tinte und Typoskript
- Hand: Zweig (schnell, Kurrentelemente) schwieriger als Maschinenschrift
- Umfang: Viele Seiten erhoehen die Wahrscheinlichkeit fuer schwierige Passagen
- Datum: Fruehere Dokumente (1901-1910) oft in staerkerer Kurrentschrift

**Dimension 3: Sprachen**

| Sprache | Anteil am Gesamtbestand | Sample-Minimum |
|---|---|---|
| Deutsch | ~85% | 20 Objekte |
| Franzoesisch | ~5% | 3 Objekte |
| Englisch | ~5% | 3 Objekte |
| Andere (IT, ES, Jiddisch) | <3% | 1-2 wenn verfuegbar, sonst dokumentieren |

### 1.4 Konkrete Objekt-Vorschlaege

Die 7 bestehenden Test-Objekte koennen als Startpunkt dienen. Folgende ergaenzen die Luecken:

**Vorhandene Tests (7) — zu uebernehmen:**

| Objekt | Gruppe | Sprache | Schwierigkeit |
|---|---|---|---|
| o_szd.72 Tagebuch 1918 | A Handschrift | DE | mittel-schwer (Kurrent, 5 Seiten) |
| o_szd.78 Vertrag Grasset | B Typoskript | FR | leicht (Maschinenschrift) |
| o_szd.160 Certificate of Marriage | C Formular | EN | leicht (Formular, klare Schrift) |
| o_szd.161 Theaterkarte | D Kurztext | DE | leicht (wenig Text) |
| o_szd.287 Der Bildner | F Korrekturfahne | DE | leicht (sauberer Druck, kaum Korrekturen) |
| o_szd.2215 Werkstatt der Dichter | H Zeitungsausschnitt | DE | leicht (Antiqua, kein Fraktur) |
| o_szd.1079 Brief an Fleischer | I Korrespondenz | DE | mittel (Jugendhandschrift 1901) |

**Gezielte Ergaenzungen (23) — Vorschlaege:**

Fuer Gruppe A (Handschrift), 4 weitere:
- 1 Manuskript in Zweigs spaeter Handschrift (1930er), z.B. aus Clarissa oder Schachnovelle
- 1 Notizbuch mit Bleistift (schwieriger Kontrast)
- 1 Dokument von Lotte Zweig (andere Hand)
- 1 Dokument von Erwin Rieger (Registerblatt, seine Handschrift ist bei 225 Objekten relevant)

Fuer Gruppe B (Typoskript), 3 weitere:
- 1 Durchschlag (blasser als Original)
- 1 englisches Typoskript (Sprachtest)
- 1 Typoskript mit handschriftlichen Annotationen (Mischform)

Fuer Gruppe C (Formular), 2 weitere:
- 1 deutsches Rechtsdokument
- 1 franzoesisches Formular

Fuer Gruppe D (Kurztext), 2 weitere:
- 1 Postkarte (kurz, aber handschriftlich)
- 1 Visitenkarte oder Telegramm

Fuer Gruppe E (Tabellarisch), 3 neu:
- 1 Registerblatt (Erwin Rieger, Aufsatzablage)
- 1 Kalender mit handschriftlichen Eintraegen
- 1 Verzeichnis/Adressbuch

Fuer Gruppe F (Korrekturfahne), 2 weitere:
- 1 Korrekturfahne mit tatsaechlichen handschriftlichen Korrekturen (der Bildner hatte kaum welche)
- 1 Druckfahne aus der Aufsatzablage

Fuer Gruppe H (Zeitungsausschnitt), 3 weitere:
- 1 Fraktur-Zeitungsausschnitt (bisher ungetestet — kritische Luecke)
- 1 mehrspaltig
- 1 mit handschriftlichen Annotationen

Fuer Gruppe I (Korrespondenz), 4 weitere:
- 1 Brief mit mehreren Seiten (vollstaendiger Briefaufbau)
- 1 Postkarte (Doppelseite: Adressseite + Text)
- 1 fremdsprachiger Brief (FR oder EN)
- 1 Brief von fremder Hand an Zweig (andere Handschrift)

**Wichtig:** Die konkreten Object-IDs muessen aus dem Backup-Bestand ermittelt werden. Die obigen Kriterien sind Auswahlrichtlinien, keine IDs. Lane 3 kann die Auswahl mit `--dry-run` und den TEI-Metadaten unterstuetzen.

### 1.5 Fehlertypen

Diplomatische Transkription produziert andere Fehler als normalisierte Volltexterfassung. Folgende Taxonomie:

| Fehlertyp | Beschreibung | Beispiel | Schwere |
|---|---|---|---|
| **Zeichenfehler** | Falsches Zeichen an richtiger Position | "n" statt "u", "f" statt "s" (Kurrent) | niedrig (einzeln), hoch (systematisch) |
| **Wortfehler** | Ganzes Wort falsch gelesen | "Eltern" statt "Altern" | mittel |
| **Auslassung** | Text im Faksimile vorhanden, in Transkription fehlend | Ganze Zeile uebersprungen | hoch |
| **Halluzination** | Text in Transkription vorhanden, nicht im Faksimile | Erfundene Woerter oder Saetze | sehr hoch |
| **Strukturfehler** | Reihenfolge, Seitenumbruch, Spalten falsch | Spalte 2 vor Spalte 1 transkribiert | mittel |
| **Markup-Fehler** | Unsicherheitsmarker fehlen oder sind falsch gesetzt | Unleserliches Wort ohne [...], leserliches mit [?] | mittel |
| **Duplikat** | Derselbe Text doppelt transkribiert | Seite 1 und 3 im Bildner-Ergebnis | hoch |
| **Anachronismus** | Zeichen oder Schreibweisen aus falscher historischer Periode eingefuegt (Levchenko 2025) | Langes s (ſ) in Zweig-Text (20. Jh.), archaische Ligaturen | mittel-hoch |

Die Fehlertypen Halluzination, Duplikat und Anachronismus verdienen besondere Aufmerksamkeit: Sie sind bei VLMs bekannte Phaenomene und mit reinen Zeichenmetriken (CER) nicht gut erfassbar, weil sie den Text verlaengern statt ihn zu veraendern.

### 1.6 Evaluationsmetriken

**Primaermetrik: CER (Character Error Rate)**

CER = (S + D + I) / N

- S = Zeichensubstitutionen, D = Zeichenloeschungen, I = Zeicheneinfuegungen (jeweils bezogen auf die Referenz)
- N = Gesamtzahl der Zeichen in der Referenz
- Berechnung ueber Levenshtein-Distanz auf Zeichenebene

CER ist die Standardmetrik in der HTR-Forschung (u.a. in den ICDAR-Wettbewerben) und erlaubt Vergleich mit publizierten Benchmarks. CER-Werte unter 5% gelten als gut, unter 2% als sehr gut.

**Sekundaermetrik: WER (Word Error Rate)**

Selbe Formel wie CER, aber auf Wortebene (Tokenisierung an Whitespace). WER ist intuitiver fuer die Bewertung der Lesbarkeit ("wie viele Woerter sind falsch?"), aber empfindlicher gegenueber Tokenisierungsentscheidungen.

**Zusatzmetriken (spezifisch fuer diplomatische Transkription):**

| Metrik | Was sie misst | Berechnung |
|---|---|---|
| Auslassungsrate | Anteil der Referenzzeichen, die in der Transkription komplett fehlen | D / N (nur Loeschungen) |
| Halluzinationsrate | Anteil der Transkriptionszeichen, die in der Referenz nicht vorkommen | I / M (Einfuegungen / Zeichen in Transkription) |
| Markup-Praezision | Wie oft sind gesetzte Unsicherheitsmarker berechtigt? | korrekte Marker / gesetzte Marker |
| Markup-Recall | Wie oft werden tatsaechlich unsichere Stellen markiert? | gesetzte Marker / unsichere Stellen in Referenz |

**Empfehlung:** CER als Primaermetrik, WER als Sekundaermetrik. Auslassung und Halluzination getrennt reporten. Markup-Metriken nur auswertbar, wenn die Referenz-Transkription ebenfalls [?]- und [...]-Stellen markiert — das muss Teil der Annotationsrichtlinie sein.

### 1.7 Normalisierung vor der CER-Berechnung

Diplomatische Transkription bedeutet: keine Orthographienormalisierung. Aber fuer eine faire CER-Berechnung muessen Pipeline-Output und Referenz auf derselben Repraesentationsebene verglichen werden. Folgende Normalisierungsschritte vor der Berechnung:

1. Unicode-Normalisierung (NFC)
2. Whitespace-Normalisierung (mehrfache Leerzeichen → eins, Trailing-Whitespace entfernen)
3. Zeilenumbruch-Normalisierung: `\r\n` → `\n`
4. **Keine** Gross/Kleinschreibung-Normalisierung (ist bedeutungstragend)
5. **Keine** Interpunktions-Entfernung (gehoert zur diplomatischen Transkription)

Markup-Zeichen (`[?]`, `[...]`, `~~...~~`, `{...}`) werden fuer die Basis-CER-Berechnung **entfernt**, fuer die Markup-Metriken separat ausgewertet.

### 1.8 Empfehlung

Vor jedem weiteren Batch-Lauf ein 30-Objekt-Referenz-Sample erstellen. Prioritaet: Die 7 bestehenden Test-Objekte manuell verifizieren (das sind die einzigen Objekte, bei denen Bild und Transkription bereits vorliegen), dann gezielt die 23 Luecken-Objekte ergaenzen. Die Referenz-Transkription muss denselben Konventionen folgen wie der Pipeline-Output (diplomatisch, mit [?]/[...]/~~...~~/\{...\}-Markup). Ohne diesen Schritt ist die Pipeline eine Blackbox.

### 1.9 Adaptive Sampling-Anpassung

*Konsolidiert aus dem historischen Pilot-Design (nicht ausgefuehrt, ersetzt durch Modellkonsensus-Validierung + GT-Pipeline).*

**Eskalationsschwellen** (pro Gruppe, nicht aggregiert):

| CER-Bereich | Bewertung | Handlung |
|---|---|---|
| **< 5%** | Sehr gut. Pipeline funktioniert fuer diese Gruppe. | Weiter mit Batch, quality_signals als Triage. |
| **5–15%** | Brauchbar mit Review. Typisch fuer schwierige Handschrift. | Batch fortsetzen, Cross-Model-Verification fuer diese Gruppe einplanen. |
| **15–30%** | Problematisch. Zu viele Fehler fuer unbeaufsichtigten Batch. | Prompt-Ueberarbeitung, dann erneuter Test. Batch nur mit manuellem Review. |
| **> 30%** | Unbrauchbar. | Grundlegende Aenderung: anderes Modell, Preprocessing, oder Gruppe vom Batch ausschliessen. |

**Anpassungsregeln fuer das Sample:**

1. **Schwierigkeits-Gewichtung**: Wenn eine Gruppe CER >15% zeigt → Objektzahl verdoppeln; Gruppen mit CER <5% reduzieren.
2. **Fehlertyp-spezifische Ergaenzung**: Wenn ein Fehlertyp >30% aller Fehler ausmacht, gezielt Objekte aufnehmen, die diesen Fehlertyp provozieren (z.B. mehr Fraktur bei f/s-Verwechslungen, mehr Tabellen bei Strukturfehlern).
3. **Protokoll-Korrektur**: Luecken im Annotationsprotokoll ergaenzen, bevor das Sample beginnt.
4. **Metriken-Ergaenzung**: Wenn CER allein nicht ausreicht (z.B. Strukturfehler bei Tabellen), zusaetzliche Metrik definieren.

**Was sich NICHT aendert**: CER als Primaermetrik, manuelles Referenz-Sample als Grundentscheidung, die Normalisierungsregeln (§1.7), die quality_signals-Spezifikation.

**Empirische Validierung (Session 18):** Die Schwellen wurden an 26 verifizierten Objekten geprueft — alle 9 Gruppen liegen im Bereich <5% (gedruckter Text) bis ~10% (schwierige Handschrift/Tabellen). Details → [[evaluation-results]].

---

## Stand der Forschung (April 2026)

Die Literatur zu VLM-basierter HTR ist seit 2024 stark gewachsen. Dieser Abschnitt fasst zusammen, was sechs aktuelle Arbeiten fuer die drei Kernfragen des Projekts bedeuten. Nur verifizierte Befunde sind aufgenommen — wo der Volltext nicht zugaenglich war, ist das markiert.

### Quellen

| Kuerzel | Referenz | Zugang |
|---|---|---|
| LEV25 | Levchenko (2025): "Evaluating LLMs for Historical Document OCR: A Methodological Framework for Digital Humanities." arXiv:2510.06743 | Volltext gelesen |
| HUM24 | Humphries et al. (2024): "Unlocking the Archives: LLMs Achieve State-of-the-Art Performance on Transcription of Handwritten Historical Documents." arXiv:2411.03340 | Volltext gelesen |
| GUT25 | Gutteridge et al. (2025): "Judge a Book by Its Cover: Multi-Modal LLMs for Multi-Page Handwritten Document Transcription." arXiv:2502.20295 | Volltext gelesen |
| CRO25 | Crosilla, Klic, Colavizza (2025): "Benchmarking Large Language Models for Handwritten Text Recognition." Journal of Documentation 81(7). arXiv:2503.15195 | Volltext gelesen |
| DIE25 | Diez Garcia et al. (2025): "Evaluating Vision Language Models for Handwritten Text Recognition." DisTech 2025, Springer | Nur Abstract und Fazit (Springer-Paywall) |
| STR22 | Stroebel et al. (2022): "Evaluation of HTR models without Ground Truth Material." LREC 2022, S. 4395-4404 | Abstract und Metriken-Beschreibung (PDF-Zugang fehlgeschlagen) |
| ZHA25 | Zhang et al. (2025): "Consensus Entropy: Harnessing Multi-VLM Agreement for Self-Verifying and Self-Improving OCR." arXiv:2504.11101, akzeptiert bei ICLR 2026 | Abstract und Methodenbeschreibung gelesen |
| RCO26 | "From Plausibility to Verifiability: Risk-Controlled Generative OCR for Vision-Language Models." arXiv:2603.19790, Maerz 2026 | Abstract gelesen |
| BEY26 | Beyene & Dancy (2026): "A Survey of OCR Evaluation Methods and Metrics and the Invisibility of Historical Documents." arXiv:2603.25761 | Abstract und Methodik gelesen |
| OCR25 | "OCR-Quality: A Human-Annotated Dataset for OCR Quality Assessment." arXiv:2510.21774, Oktober 2025 | Abstract gelesen |

### Befund 1: CER-Erwartungswerte fuer unser Projekt

Die aktuelle Literatur liefert CER-Referenzwerte, die unsere Erwartungen kalibrieren:

| Quelle | Dokumenttyp | Sprache | Bestes Modell | CER |
|---|---|---|---|---|
| CRO25 | Modern handschriftlich (IAM) | EN | GPT-4o-mini | 1.7% |
| CRO25 | Modern handschriftlich (RIMES) | FR | Claude 3.5 Sonnet | 1.6% |
| LEV25 | 18. Jh. Druck, Zivilschrift | RU | Gemini-2.5-Pro | 3.4% |
| HUM24 | 18./19. Jh. handschriftlich | EN | Claude Sonnet-3.5 | 5.7% (modifiziert), 7.3% (strikt) |
| CRO25 | 18. Jh. handschriftlich (LAM) | IT | Claude 3.5 Sonnet | 20.6% |
| CRO25 | 15.-19. Jh. handschriftlich (READ2016) | DE | Claude 3.5 Sonnet | 71.2% |
| CRO25 | 19. Jh. mehrsprachig (ICDAR2017) | DE/FR/IT | Claude 3.5 Sonnet | 41.2% |

**Implikation fuer SZD-HTR:** Die Spanne ist enorm. Fuer Zweigs Typoskripte (Gruppe B) und gedruckte Texte (F, H) sind CER-Werte unter 5% realistisch. Fuer Zweigs Handschrift (Gruppe A, I) ist die Erwartung unklar: Zweig schrieb im fruehen 20. Jahrhundert in einer Mischung aus lateinischer Schrift und Kurrentelementen — das ist naeher an "modern handschriftlich" als an "15. Jh. historisch", aber entfernt von den sauberen IAM-Benchmarks. Der READ2016-Wert (71% CER auf historischem Deutsch) zeigt, dass deutschsprachige historische Handschriften die groesste Schwaeche aktueller VLMs sind. Unsere Ground-Truth-Evaluation (Abschnitt 1) muss klaeren, wo der Zweig-Nachlass auf dieser Skala liegt.

Die Benchmark-Daten stuetzen die Empfehlung, die CER getrennt nach Gruppe und Sprache zu reporten — ein aggregierter Wert ueber alle 2107 Objekte waere bedeutungslos.

### Befund 2: Selbstkorrektur funktioniert nicht — Kreuzkorrektur schon

Zwei Papers untersuchen, ob ein zweiter LLM-Durchlauf Transkriptionsfehler korrigieren kann. Ihre Ergebnisse widersprechen sich auf den ersten Blick, sind aber bei genauer Betrachtung komplementaer:

**Humphries et al. (HUM24):** Wenn Claude Sonnet die Transkription von Transkribus korrigiert (heterogene Korrektur: anderes System, Bild + Text), sinkt die CER von 8.0% auf 1.8% — eine Reduktion um 78%.

**Crosilla et al. (CRO25):** Wenn ein Modell seine eigene Transkription korrigiert (homogene Selbstkorrektur), verschlechtert sich die Qualitaet in der Mehrzahl der Faelle. Konkrete Beispiele:
- Claude 3.5 Sonnet auf IAM: 1.75% → 8.55% CER (4.9x schlechter)
- Claude 3.5 Sonnet auf Bentham: 10.97% → 40.87% CER (3.7x schlechter)
- GPT-4o auf IAM: 1.75% → 1.39% CER (seltene Verbesserung)
- Open-Source-Modelle: durchgehend Verschlechterung

**Levchenko (LEV25)** bestaetigt: Wenn dem korrigierenden Modell Bild und OCR-Text gemeinsam gegeben werden, "performance does not exceed the correcting model's direct OCR capabilities — models essentially re-perform OCR rather than correct the provided text." Reine Textkorrektur ohne Bild verschlechtert das Ergebnis konsistent.

**Aufloesung:** Kreuzkorrektur (Modell A korrigiert Modell B, mit Quellbild) kann funktionieren. Selbstkorrektur (Modell A korrigiert sich selbst) funktioniert nicht zuverlaessig. Der Mechanismus: LLMs "are built to output the most probable token in a sequence, and cannot properly judge the correctness of their reasoning" (CRO25). Sie generieren neu, statt minimal zu editieren.

**Implikation fuer SZD-HTR:** Ein Korrektur-Durchlauf in der Pipeline ist nur dann sinnvoll, wenn er (a) ein anderes Modell verwendet als den Ersttranskriptor und (b) das Quellbild mitliefert. Die Kosten verdoppeln sich damit. Ob der Qualitaetsgewinn die Kosten rechtfertigt, muss am Ground-Truth-Sample gemessen werden. Selbstkorrektur mit demselben Gemini-Modell ist ausdruecklich nicht empfohlen.

### Befund 3: Over-Historicization — ein unbekannter Fehlertyp

Levchenko (LEV25) identifiziert einen Halluzinationstyp, der in der bisherigen Fehlertaxonomie (Abschnitt 1.5) fehlt: **Over-Historicization**. VLMs fuegen archaische Zeichen ein, die aus der falschen historischen Periode stammen. Bei 18. Jh. russischen Texten inseriert GPT-4o in 59% der Dateien kirchenslawische Zeichen (ѡ, ѧ, ꙋ), die zum Zeitpunkt der Textproduktion bereits obsolet waren.

Levchenko fuehrt dafuer zwei Metriken ein:
- **HCPR (Historical Character Preservation Rate):** Misst, ob periodenspezifische Zeichen korrekt erhalten bleiben
- **AIR (Archaic Insertion Rate):** Misst, wie oft obsolete Zeichen faelschlich eingefuegt werden

(Anmerkung: Das Paper gibt keine formalen Definitionen dieser Metriken an; die Beschreibungen sind deskriptiv.)

**Implikation fuer SZD-HTR:** HCPR und AIR sind in ihrer konkreten Form nicht direkt uebertragbar — sie messen slawische Zeicheninsertion fuer russische Zivilschrift. Aber das Phaenomen ist relevant: Gemini koennte bei Zweigs Texten (fruehes 20. Jh.) archaisierende Schreibweisen einfuegen, etwa langes s (ſ), ſt-Ligaturen, oder ae/oe statt ae/oe-Umlaute, die Zweig nicht verwendet hat. Ob das in der Praxis auftritt, muss die Ground-Truth-Evaluation zeigen. Die Fehlertaxonomie in Abschnitt 1.5 wird um diesen Typ ergaenzt.

### Befund 4: Kontextuelle Information verbessert Multi-Page-Transkription

Gutteridge et al. (GUT25) zeigen, dass minimale Kontextinformation die Transkriptionsqualitaet auf Folgeseiten erheblich verbessert. Ihre "+first page"-Methode liefert dem Modell den OCR-Output des gesamten Dokuments plus nur das Bild der ersten Seite. Ergebnis:

- gpt-4o-mini: CER 0.037 (Baseline) → 0.017 (+first page) — 54% Verbesserung auf Seiten, die das Modell nie als Bild gesehen hat
- Der Effekt entsteht durch Extrapolation von Formatierung, Schriftstil und Fehlermustern, nicht durch Textinhalt

Zusaetzlich: gpt-4o-mini uebertrifft gpt-4o haeufig. Die Autoren vermuten, "the supposedly more capable model may have a tendency to do too much; for OCR post-processing, often what is left alone is more important than what is changed."

**Implikation fuer SZD-HTR:** Dieser Befund stuetzt das dreischichtige Prompt-System grundsaetzlich — Kontext hilft. Aber er differenziert auch: Der Nutzen liegt nicht in domainspezifischem Wissen (Kurrent-Verwechslungspaare), sondern in dokumentspezifischem Kontext (Schriftbild, Layout, Fehlerpatterns). Das Prompt-Experiment (Abschnitt 3) sollte diesen Unterschied testen: Verbessert der TEI-Objekt-Kontext (Schicht 3) die Qualitaet staerker als der Gruppen-Prompt (Schicht 2)?

Der Befund zu gpt-4o-mini vs. gpt-4o ist relevant fuer den Provider-Vergleich (Phase 4): "Leistungsfaehiger" bedeutet nicht automatisch "besser fuer HTR".

### Befund 5: GT-freie Qualitaetsschaetzung ist moeglich

Stroebel et al. (STR22) zeigen, dass Proxy-Metriken ohne Ground Truth die relative Qualitaet von HTR-Modellen einschaetzen koennen:

- **Dictionary Word Ratio:** Anteil der Woerter, die in einem Referenzlexikon vorkommen
- **Token Ratio:** Verhaeltnis bekannter zu unbekannter Tokens (Tokenizer-basiert)
- **Pseudo-Perplexity (PPPL):** Bewertung der Textplausibilitaet durch ein Masked Language Model (z.B. BERT)

Kernergebnis: MLM-basierte Metriken (PPPL) korrelieren mit CER vergleichbar gut wie lexikonbasierte Metriken, haben aber den Vorteil, dass sie fuer beliebige Sprachen verfuegbar sind (mehrsprachige Transformer existieren).

(Anmerkung: Die exakten Korrelationswerte konnte ich nicht verifizieren — PDF-Zugang fehlgeschlagen. Die qualitative Aussage ist aus Abstract und Metadaten belegbar.)

**Implikation fuer SZD-HTR:** Pseudo-Perplexity ist ein starker Kandidat fuer den Signalkatalog in Abschnitt 2. Ein mehrsprachiges MLM (z.B. multilingual BERT) koennte pro Transkription eine Plausibilitaetsbewertung liefern, die mit der tatsaechlichen Qualitaet korreliert. Das erfordert allerdings eine zusaetzliche Modell-Abhaengigkeit (Transformer lokal oder via API). Ob sich der Aufwand lohnt, haengt davon ab, wie gut die einfacheren Signale (Abschnitt 2.3) nach Kalibrierung funktionieren — PPPL waere eine Eskalationsstufe, falls die einfachen Signale nicht genuegend diskriminieren.

### Befund 6: Proprietaere VLMs naehern sich spezialisierten HTR-Systemen

Crosilla et al. (CRO25) und Diez Garcia et al. (DIE25, nur Abstract verifiziert) zeigen uebereinstimmend: Proprietaere VLMs (Claude, GPT-4o, Gemini) erreichen auf modernen Handschriften bessere CER-Werte als Transkribus (CRO25: 1.7% vs. 9.1% auf IAM). Bei historischen Dokumenten ist das Bild gemischt: Auf einigen historischen Datasets uebertreffen VLMs Transkribus, auf anderen (besonders historisches Deutsch) liegt Transkribus deutlich vorn.

**Implikation fuer SZD-HTR:** Der Provider-Vergleich (Phase 4) sollte nicht nur VLMs untereinander vergleichen, sondern auch Transkribus als Baseline einbeziehen — zumindest auf dem Ground-Truth-Sample. Es ist nicht ausgemacht, dass VLMs fuer alle Dokumentgruppen die beste Wahl sind.

### Befund 7: Multi-VLM-Modellkonsensus als GT-freier Qualitaetsproxy (2025-2026)

Drei juengere Arbeiten zeigen, dass Multi-Modell-Agreement ein starkes, GT-freies Qualitaetssignal liefert:

**Zhang et al. (ZHA25, ICLR 2026):** Consensus Entropy (CE) quantifiziert OCR-Unsicherheit durch Aggregation der Outputs mehrerer VLMs. Kerninsight: *Korrekte Transkriptionen konvergieren im Output-Space, Fehler divergieren.* CE erreicht 15.2% hoehere F1-Scores als VLM-as-Judge-Methoden und erfordert nur bei 7.3% der Inputs eine Eskalation an ein staerkeres Modell. Das Verfahren ist training-free und plug-and-play.

**Risk-Controlled VLM OCR (RCO26, Maerz 2026):** Deployment-zentriertes Accept/Abstain-Framework fuer generative OCR. Ein externer Control Layer prueft bei Inferenz die Cross-View-Stabilitaet (kontrollierte Input-Variationen + strukturelle Validitaetschecks) und akzeptiert eine Transkription nur bei hinreichend stabilem Agreement. Kernbeitrag: Die Accept/Abstain-Entscheidung ist als fester, auditierbarer Deployment-Vertrag spezifiziert — nicht als probabilistischer Score.

**Beyene & Dancy (BEY26, 2026):** Unsupervised Evaluation Framework fuer historische Digitalisate ohne GT. Drei Metriken: Semantic Coherence Score (SCS, Woerterbuch-Wortanteil pro Textregion), Region Entropy Divergence (RED, N-Gram-Diversitaet als Kohaerenzindikator), Textual Redundancy Score (TRS, Strafterm fuer wiederholten Text ueber Regionen).

**Implikation fuer SZD-HTR:** Der 3-Modell-Modellkonsensus-Ansatz ist wissenschaftlich fundiert und direkt umsetzbar:

1. **Gemini 3.1 Flash Lite** (bisheriger Ersttranskriptor, guenstig)
2. **Gemini 3.1 Flash** (staerkeres Modell, unabhaengige Zweittranskription)
3. **Claude** (via Claude Code Subagent mit Vision — LLM-as-Judge, sieht Bild + beide Transkriptionen)

Bei hohem Agreement aller drei Modelle kann die Transkription als **automatisch generiertes Ground Truth** akzeptiert werden (Ensemble Agreement Error Rate ~2-6%, vgl. LLM-Generated GT Literatur). Bei Divergenz wird das Objekt fuer manuellen Review geflaggt. Dieser Ansatz reduziert den manuellen GT-Aufwand drastisch: Statt 30 Objekte vollstaendig manuell zu transkribieren, werden nur die ~7-15% Divergenz-Faelle manuell geprueft.

**Abgrenzung zu Abschnitt 4 (Cross-Model-Verification):** Abschnitt 4 beschreibt Doppeltranskription als Qualitaetssignal. Der Modellkonsensus-Ansatz geht weiter: Er nutzt drei Modelle + eine Judge-Rolle und akzeptiert bei Konsens automatisch als GT. Das ist eine staerkere Behauptung, die durch ZHA25 und RCO26 gestuetzt wird, aber am eigenen Corpus validiert werden muss.

### 7.1 Empirische Umsetzung: GT-Pipeline (Session 14)

**Architektur (implementiert in `pipeline/generate_gt.py`):**
- Modell A: Gemini 3.1 Flash Lite (existierende Transkription)
- Modell B: Gemini 3 Flash (aus Modellkonsensus-Verifikation)
- Modell C: Gemini 3.1 Pro (staerkstes Modell, via API)
- Expert: Mensch im Frontend (Review + Approval)

**Merge-Logik pro Seite:**
- Alle 3 stimmen ueberein (paarweise CER < 2%): → `consensus_3of3` (automatisch akzeptiert)
- 2 von 3 stimmen ueberein (bestes Paar CER < 5%): → `majority_2of3` (staerkeres Modell gewaehlt)
- Alle divergieren: → `pro_only` (Pro-Version als Draft)

**Ergebnis (18 GT-Objekte, 46 Content-Seiten):**

| Merge-Typ | Seiten | Anteil |
|---|---|---|
| consensus_3of3 | 15 | 33% |
| majority_2of3 | 20 | 43% |
| pro_only | 11 | 24% |

76% der Content-Seiten haben mindestens 2/3-Uebereinstimmung. Der Expert-Review-Aufwand konzentriert sich auf die 11 pro_only-Seiten.

**Kosten:** 18 API-Calls mit Gemini Pro (ca. $3-5). Gesamt inkl. Flash-Modellkonsensus: ca. $8-12.

**Frontend-Integration:** GT Review-Modus im Viewer mit 3-Varianten-Ansicht, Source-Badges pro Seite, Approve-Workflow. Expert-Reviewed-GT wird als `{object_id}_gt.json` exportiert.

### Ergaenzung der Fehlertaxonomie

Basierend auf LEV25 wurde die Fehlertabelle in Abschnitt 1.5 um den Typ **Anachronismus** erweitert. Dieser ist eine Unterform der Halluzination, aber spezifisch genug, um getrennt erfasst zu werden: Er deutet auf ein systematisches Bias im Modell hin, nicht auf Leseprobleme. Bei den bisherigen 16 Objekten wurde kein Anachronismus beobachtet (kein langes s, keine archaischen Ligaturen) — aber Fraktur-Texte (o_szd.2232) und historische Handschrift sind die Risikogruppe, die der Pilot pruefen wird.

---

## 2. Konfidenz-Ersatz

### 2.1 Problem

Das `confidence`-Feld im Pipeline-Output ("high"/"medium"/"low") ist eine Selbsteinschaetzung des VLM. Empirisch: 12/12 Objekte "high", nahezu keine Inline-Unsicherheitsmarker. Das Feld hat keinen Informationsgehalt.

Ziel ist ein Satz automatisch berechenbarer Signale, die nach der Transkription (ohne Ground Truth) berechnet werden und problematische Ergebnisse fuer menschliche Pruefung markieren. Diese Signale ersetzen nicht die Qualitaetsmessung (dafuer braucht es Ground Truth), sondern priorisieren den menschlichen Review-Aufwand.

### 2.2 Bewertung der drei projektierten Ebenen

**Ebene 1: Unsicherheitsmarker ([?], [...]) — gering nuetzlich**

Theoretisch das direkteste Signal: Das Modell markiert selbst, wo es unsicher ist. Empirisch: Das Modell tut es fast nie. In 30+ Seiten findet sich 1x [...] und 1x [?]. Das kann drei Ursachen haben:
- Das Modell ist tatsaechlich ueberall sicher (unwahrscheinlich bei Kurrent)
- Der Prompt erzeugt keine ausreichende Tendenz zur Selbstmarkierung
- VLMs kalibrieren Unsicherheit grundsaetzlich schlecht

Marker-Dichte bleibt als Signal nuetzlich (wenn Marker auftreten, ist das informativ), aber ihr Fehlen ist kein Qualitaetssignal. Niedrige Marker-Dichte heisst nicht "gut", sondern "uninformativ".

**Ebene 2: VLM-Selbsteinschaetzung (confidence-Feld) — nicht nuetzlich**

Kategorialer Wert, der aus demselben API-Call stammt wie die Transkription. Leidet unter denselben Kalibrierungsproblemen wie die Marker. Kann nicht unabhaengig vom Transkriptionsprozess berechnet werden. Empfehlung: Feld beibehalten (es kostet nichts), aber nicht als Filtersignal verwenden.

**Ebene 3: Textstatistik — vielversprechend**

Signale, die aus dem fertigen Transkriptionstext berechnet werden, ohne das VLM erneut zu befragen. Koennen systematische Probleme erkennen (Auslassungen, Halluzinationen, Strukturfehler), auch wenn sie einzelne Zeichenfehler nicht finden.

### 2.3 Signalkatalog

Sechs automatisch berechenbare Signale, geordnet nach erwartetem Nutzen.

**Empirische Einordnung (Stand 16 Objekte):** Die Signale wurden anhand der ersten 16 Objekte getestet. Ergebnis: 10/16 Objekte (63%) werden als `needs_review` geflaggt. Das ist zu viel fuer effektive Triage. Hauptursache: `page_image_mismatch` feuert bei jedem Objekt, das Leerseiten hat (Rueckseiten, Farbkarten) — im SZD-Nachlass ist das der Normalfall, kein Fehler. `marker_density` ist bei 16/16 Objekten nahe 0.0 (das Modell setzt fast keine Marker). `group_text_density` braucht >10 Objekte/Gruppe, die bisher nur Typoskript hat. Nur `duplicate_pages` (4 Treffer) und `language_mismatch` (2 Treffer) produzieren potenziell nuetzliche Signale. Die Schwellenwerte muessen dringend nach dem Pilot kalibriert werden — insbesondere sollte `page_image_mismatch` bei Objekten mit bekannten Leerseiten-Mustern (Farbkarten, Rueckseiten) nicht ausloesen.

**Update v1.4 (2026-04-02):** Schwellenwerte weiter rekalibriert. Duplikaterkennung: Jaccard-Schwelle beibehalten (0.9), aber Mindestzeichenzahl von 200 auf 50 gesenkt — das erkennt jetzt Seiten-Halluzinationen (Modell dupliziert kurze Seiten wie Deckblaetter). DWR (Dictionary Word Ratio) seit v1.2 integriert: Anteil der Woerter in sprachspezifischer Frequenzliste (~500 Woerter DE/FR/EN), korreliert mit CER (Springmann 2016). needs_review-Rate bei 601 Objekten: ~41%.

**Signal 1: Seitenlaengen-Anomalie (page_length_anomaly)**

Logik: Seiten desselben Dokuments haben typischerweise aehnliche Textmengen (vor allem bei fortlaufendem Text). Eine Seite mit 50 Zeichen zwischen Seiten mit je 1500 Zeichen ist verdaechtig — entweder eine echte Kurzseite (letzte Seite, Titelblatt) oder eine Auslassung.

Berechnung:
- Fuer jede Seite: Zeichenzahl `c_i`
- Median der Zeichenzahlen aller Seiten mit Text: `c_med`
- Seiten mit `c_i < 0.2 * c_med` und `c_i > 0` als anomal markieren
- Leerseiten (`c_i == 0`) separat zaehlen

Einschraenkung: Bei Dokumenten mit nur 1-2 Seiten oder bei heterogenen Dokumenten (Briefumschlag + Brieftext) wenig aussagekraeftig.

**Signal 2: Seiten-Bild-Abgleich (page_image_mismatch)**

Logik: Die Anzahl transkribierter Seiten sollte der Anzahl der Input-Bilder entsprechen. Abweichungen deuten auf uebersprungene oder verdoppelte Seiten hin.

Berechnung:
- `n_images`: Anzahl der Bilder im Input
- `n_pages`: Anzahl der Eintraege in `pages[]`
- `n_empty`: Seiten mit leerer Transkription
- Flag wenn `n_pages != n_images` oder `n_empty > n_images * 0.5`

**Signal 3: Duplikaterkennung (duplicate_pages)**

Logik: Textduplikate zwischen Seiten (wie bei o_szd.287, Seiten 1 und 3) koennen reale Duplikate im Faksimile sein oder Modell-Wiederholungen. In beiden Faellen ist menschliche Pruefung sinnvoll.

Berechnung:
- Fuer jedes Seitenpaar (i, j): Jaccard-Aehnlichkeit auf Wortebene
- Flag wenn Aehnlichkeit > 0.8 und beide Seiten > 100 Zeichen

**Signal 4: Sprachkonsistenz (language_mismatch)**

Logik: Die Metadaten geben eine Sprache an. Wenn die Transkription ueberwiegend in einer anderen Sprache erscheint, stimmt etwas nicht — entweder die Metadaten oder die Transkription.

Berechnung:
- Einfache Heuristik: Top-20-Stoppwoerter pro Sprache (DE, FR, EN) zaehlen
- Dominante Sprache im Text bestimmen
- Flag wenn dominante Sprache != Metadaten-Sprache

(Anmerkung: Eine vollwertige Spracherkennung waere praeziser, erhoecht aber die Abhaengigkeiten. Die Stoppwort-Heuristik reicht fuer die drei Hauptsprachen.)

**Signal 5: Marker-Dichte (marker_density)**

Logik: Obwohl niedrige Marker-Dichte uninformativ ist, ist hohe Marker-Dichte ein valides Signal — wenn das Modell viele [?] setzt, gibt es wahrscheinlich Leseprobleme.

Berechnung:
- `n_uncertain`: Anzahl `[?]`-Marker
- `n_illegible`: Anzahl `[...]`-Marker
- `n_words`: Wortanzahl der gesamten Transkription
- `marker_density = (n_uncertain + n_illegible) / n_words`

Einschraenkung: Asymmetrisches Signal. Hoher Wert = informativ. Niedriger Wert = uninformativ.

**Signal 6: Textdichte relativ zur Gruppe (group_text_density)**

Logik: Innerhalb einer Prompt-Gruppe (z.B. "Handschrift") haben Dokumente mit aehnlicher Seitenanzahl aehnliche Textmengen. Starke Ausreisser (viel weniger oder viel mehr Text als erwartet) verdienen Pruefung.

Berechnung:
- Erst sinnvoll, wenn >10 Objekte pro Gruppe transkribiert sind
- Normalisierte Textdichte: Gesamtzeichen / Seitenanzahl
- Z-Score innerhalb der Gruppe
- Flag wenn |z| > 2

### 2.4 Zusammengesetztes Flag: `needs_review`

Die Einzelsignale werden zu einem einzigen boolschen Flag aggregiert: `needs_review`. Ein Objekt wird zur Pruefung markiert, wenn mindestens eines der folgenden Kriterien zutrifft:

| Kriterium | Schwelle |
|---|---|
| Seitenlaengen-Anomalie | Mindestens 1 anomale Seite |
| Seiten-Bild-Abweichung | `n_pages != n_images` oder `n_empty > n_images * 0.5` |
| Duplikat | Mindestens 1 Seitenpaar mit Jaccard > 0.8 |
| Sprachinkonsistenz | Dominante Sprache != Metadaten-Sprache |
| Marker-Dichte | `marker_density > 0.05` (mehr als 1 Marker pro 20 Woerter) |
| Gruppen-Ausreisser | `|z_text_density| > 2` (erst ab 10 Objekten pro Gruppe) |

**Wichtig:** Die Schwellenwerte sind Ausgangswerte und muessen anhand des Ground-Truth-Samples kalibriert werden. Ziel ist eine brauchbare Recall-Rate (>80% der tatsaechlich problematischen Transkriptionen werden geflaggt) bei akzeptabler Praezision (nicht mehr als 30% False Positives).

### 2.5 Spezifikation fuer Lane 3

Folgende Felder werden dem Ergebnis-JSON hinzugefuegt (neuer Top-Level-Key `quality_signals`, neben dem bestehenden `result`):

```
"quality_signals": {
  "version":                 string,   // Schema-Version, z.B. "1.0"
  "total_chars":             int,      // Gesamtzeichen (ohne Leerseiten)
  "total_words":             int,      // Gesamtwoerter
  "total_pages":             int,      // Seiten mit Text (> 0 Zeichen)
  "empty_pages":             int,      // Seiten mit 0 Zeichen
  "input_images":            int,      // Anzahl Input-Bilder
  "chars_per_page":          float[],  // Zeichenzahl pro Seite (Array, Index = Seite)
  "chars_per_page_median":   float,    // Median von chars_per_page (nur Seiten > 0)
  "marker_uncertain_count":  int,      // Anzahl [?]-Marker
  "marker_illegible_count":  int,      // Anzahl [...]-Marker (inkl. [...N...])
  "marker_density":          float,    // (uncertain + illegible) / total_words
  "duplicate_page_pairs":    int[][],  // Seitenpaare mit Jaccard > 0.8, z.B. [[1,3]]
  "language_expected":       string,   // Aus Metadaten
  "language_detected":       string,   // Dominante Sprache im Text (Stoppwort-Heuristik)
  "language_match":          boolean,  // expected == detected
  "page_length_anomalies":   int[],    // Indizes anomaler Seiten
  "needs_review":            boolean,  // Zusammengesetztes Flag
  "needs_review_reasons":    string[]  // Welche Kriterien ausgeloest haben
}
```

Alle Felder sind aus dem Transkriptionsergebnis und den Metadaten berechenbar, ohne zusaetzlichen API-Call. Die Berechnung soll nach jedem Transkriptionsaufruf automatisch erfolgen und im selben JSON gespeichert werden.

### 2.6 GT-freie Qualitaetsschaetzung: Moeglichkeiten und Grenzen

Neben den oben definierten heuristischen Signalen gibt es drei Ansaetze aus der Literatur, die Transkriptionsqualitaet ohne manuelle Referenz statistisch zu schaetzen:

**Pseudo-Perplexity (Stroebel et al. 2022):** Ein Masked Language Model (z.B. multilingual BERT) bewertet die sprachliche Plausibilitaet des Transkriptionstexts. Gibberish oder systematisch falsch gelesene Woerter erzeugen hohe Perplexitaet. Der Ansatz korreliert mit CER und ist sprachunabhaengig (mehrsprachige Transformer verfuegbar). Nachteil: erfordert eine zusaetzliche Modell-Abhaengigkeit (Transformer lokal oder via API).

**Dictionary Word Ratio (Stroebel et al. 2022):** Anteil der Woerter in einem Referenzlexikon. Einfach zu berechnen, aber sprachabhaengig. Fuer den Zweig-Nachlass mit historischer Orthographie, franzoesischen Einsprengseln und Abkuerzungen muesste das Lexikon sorgfaeltig zusammengestellt werden.

**Cross-Model-Agreement (Abschnitt 4):** Zwei Modelle transkribieren unabhaengig; hohe Uebereinstimmung korreliert mit Korrektheit. Am staerksten von den drei Ansaetzen, aber auch am teuersten (2x API-Kosten).

**Grenzen aller GT-freien Ansaetze:** Sie messen *Plausibilitaet* oder *Konsistenz*, nicht *Korrektheit*. Ein fluessig lesbarer, grammatisch korrekter Text kann trotzdem ein Wort falsch gelesen haben. Halluzinationen (plausibel klingender, aber im Faksimile nicht vorhandener Text) werden von keinem dieser Ansaetze zuverlaessig erkannt. Deshalb ersetzen sie die Ground-Truth-Evaluation nicht, sondern ergaenzen sie.

**Priorisierung:** Die heuristischen Signale (Abschnitt 2.3) und Cross-Model-Agreement (Abschnitt 4) sofort implementieren — sie erfordern keine Ground Truth und keine zusaetzlichen Abhaengigkeiten. Pseudo-Perplexity als Eskalationsstufe in Betracht ziehen, falls die einfachen Signale nach Kalibrierung nicht ausreichend diskriminieren.

### 2.7 Empfehlung

Die `quality_signals` sofort implementieren (sie sind guenstig und erfordern keine Ground Truth). Sie loesen das Konfidenz-Problem nicht vollstaendig — dafuer braucht es Ground Truth — aber sie bieten ein funktionierendes Triage-System fuer den Batch-Lauf ueber 2107 Objekte. Lane 1 kann `needs_review` im Viewer als Filter und visuelle Markierung einbauen.

Die Schwellenwerte nach Erstellung des Ground-Truth-Samples kalibrieren: quality_signals fuer die 30 Referenz-Objekte berechnen, gegen die CER-Werte abgleichen, Schwellen anpassen.

---

## 3. Prompt-Wirksamkeit

### 3.1 Fragestellung

Das dreischichtige Prompt-System (System → Gruppe → Objekt-Kontext) ist die zentrale Designentscheidung der Pipeline. Die Gruppen-Prompts enthalten spezifische Hinweise — z.B. Kurrent-Verwechslungspaare (e/n, s/f, u/n) fuer Handschriften, Fraktur-Hinweise fuer Zeitungsausschnitte, Korrekturmarking-Anweisungen fuer Druckfahnen.

Die Frage ist: Verbessern diese Hinweise die Transkriptionsqualitaet messbar, oder liefert ein generischer Prompt (nur Schicht 1) dasselbe Ergebnis?

### 3.2 Warum das wichtig ist

Wenn die Gruppen-Prompts keinen messbaren Effekt haben, sind sie totes Gewicht — sie erhoehen die Komplexitaet der Pipeline (Gruppenzuordnungs-Logik, 8 Prompt-Dateien), ohne Nutzen. Wenn sie einen Effekt haben, ist es wichtig zu wissen, bei welchen Gruppen und welchen Fehlertypen.

Es gibt plausible Gruende fuer beide Hypothesen:
- **Pro Effekt:** Kurrent-Verwechslungshinweise koennten gezielte Fehler reduzieren; Strukturhinweise (Briefformat, Spalten) koennten Reihenfolge-Fehler vermeiden.
- **Contra Effekt:** Moderne VLMs haben Kurrent und Fraktur in ihren Trainingsdaten gesehen; zusaetzliche Hinweise koennten redundant sein oder sogar stoeren (Overpriming).

Beide Hypothesen sind empirisch pruefbar.

### 3.3 Versuchsaufbau

**Design: Gepaarter Vergleich mit drei Prompt-Varianten**

Jedes Objekt im Sample wird dreimal transkribiert:

| Variante | Prompt-Schichten | Kosten |
|---|---|---|
| V1: Basis | Nur System-Prompt (Schicht 1) | 1 API-Call |
| V2: Gruppe | System + Gruppen-Prompt (Schicht 1+2) | 1 API-Call |
| V3: Voll | System + Gruppe + Objekt-Kontext (Schicht 1+2+3) | 1 API-Call |

**Sample:** Die 30 Ground-Truth-Objekte. Damit sind 30 x 3 = 90 API-Calls noetig.

**Vergleichsmetrik:** CER-Differenz zwischen Varianten, pro Objekt. Der gepaarte Vergleich (dasselbe Objekt unter verschiedenen Bedingungen) eliminiert die Objektvarianz und isoliert den Prompt-Effekt.

**Auswertung:**
- Median-CER pro Variante und Gruppe
- Gepaarter Vergleich: Fuer wie viele Objekte ist V2 < V1? Fuer wie viele V3 < V2?
- Fehlertyp-Analyse: Welche Fehlertypen reduzieren die Gruppen-Prompts?

### 3.4 Erwartete Befunde und Konsequenzen

| Befund | Konsequenz |
|---|---|
| V2 signifikant besser als V1 bei Handschrift/Fraktur, nicht bei Typoskript | Gruppen-Prompts beibehalten fuer schwierige Gruppen, vereinfachen fuer leichte |
| V2 und V1 gleichwertig | Gruppen-Prompts koennen entfallen — Pipeline wird einfacher |
| V3 signifikant besser als V2 | TEI-Kontext-Integration lohnt sich |
| V3 schlechter als V2 bei einigen Objekten | Objekt-Kontext erzeugt Halluzinationen (bekanntes Risiko bei zu viel Kontext) |

### 3.5 Zeitliche Einordnung

**Das Prompt-Experiment setzt die Ground Truth voraus.** Ohne Referenztranskription kann der CER-Vergleich nicht durchgefuehrt werden.

Reihenfolge:
1. Ground-Truth-Sample erstellen (Abschnitt 1)
2. Prompt-Experiment durchfuehren (90 API-Calls, kostet <3 USD)
3. CER pro Variante berechnen, Ergebnisse auswerten
4. Auf Basis der Ergebnisse entscheiden, ob das Prompt-System angepasst wird

**Parallelisierbar mit der Ground-Truth-Erstellung:** Die drei Transkriptionsvarianten koennen gleichzeitig mit der manuellen Referenz-Transkription produziert werden. Die Auswertung erfolgt erst, wenn beides vorliegt.

### 3.6 Empfehlung

Das Prompt-Experiment auf das Ground-Truth-Sample ausfuehren — es ist billig (90 API-Calls) und liefert eine empirische Grundlage fuer eine Designentscheidung, die die gesamte Pipeline betrifft. Nicht vorher vereinfachen oder verkomplizieren, sondern zuerst messen. Die 90 Transkriptions-Varianten gleichzeitig mit der Ground-Truth-Erstellung produzieren lassen (Lane 3 kann das als Batch konfigurieren), damit die Auswertung unmittelbar nach Fertigstellung der Referenz erfolgen kann.

---

## 4. Cross-Model-Verification

### 4.1 Fragestellung

Kann ein zweites VLM die Transkriptionsqualitaet verbessern oder zumindest problematische Stellen identifizieren — ohne manuelles Ground Truth?

Die Literatur (Abschnitt "Stand der Forschung") liefert dazu klare Befunde:
- Kreuzkorrektur (Modell B korrigiert Modell A, mit Bild) kann CER drastisch senken: 8.0% → 1.8% (Humphries et al.)
- Selbstkorrektur (Modell A korrigiert sich selbst) versagt in der Mehrzahl der Faelle (Crosilla et al.)
- Korrektur ohne Bild verschlechtert das Ergebnis konsistent (Levchenko)

### 4.2 Zwei Ansaetze

**Ansatz A: Unabhaengige Doppeltranskription (Agreement-basiert)**

Beide Modelle transkribieren dasselbe Bild unabhaengig. Uebereinstimmung = hohes Vertrauen. Abweichung = Pruefbedarf.

| Eigenschaft | Bewertung |
|---|---|
| Kosten | 2x API-Calls (doppelte Basiskosten) |
| Abhaengigkeit | Keine — Modelle arbeiten unabhaengig |
| Informationsgehalt | Hoch: Abweichungen lokalisieren exakt die problematischen Stellen |
| Risiko | Wenn beide Modelle denselben Fehler machen, bleibt er unentdeckt (systematischer Bias) |

**Ansatz B: Heterogene Korrektur (Humphries-Ansatz)**

Modell B erhaelt das Bild UND die Transkription von Modell A. Es soll korrigieren.

| Eigenschaft | Bewertung |
|---|---|
| Kosten | 2x API-Calls (doppelte Basiskosten) |
| Abhaengigkeit | Sequentiell — Modell B braucht Output von Modell A |
| Informationsgehalt | Direkte Verbesserung der Transkription, nicht nur Flagging |
| Risiko | "Re-generation statt Korrektur" (Levchenko): Modell B ignoriert Modell A und transkribiert neu |

### 4.3 Empfohlene Strategie: Agreement-First

**Primaer: Ansatz A (Agreement) auf dem gesamten Batch.**

Begruendung:
1. Unabhaengige Transkriptionen sind methodisch sauberer — kein Modell beeinflusst das andere.
2. Der Agreement-Score ist ein robusteres Qualitaetssignal als die Selbsteinschaetzung: Wenn Gemini und Claude denselben Text produzieren, ist die Wahrscheinlichkeit hoch, dass er korrekt ist.
3. Der Agreement-basierte Ansatz produziert automatisch einen Diff, der im Frontend (Abschnitt 5) angezeigt werden kann.
4. Ansatz A ist parallelisierbar (beide Calls gleichzeitig), Ansatz B ist sequentiell.

**Sekundaer: Ansatz B (Korrektur) nur fuer `needs_review`-Objekte.**

Fuer Objekte, bei denen Agreement niedrig ist und die quality_signals auffaellig sind, kann ein dritter Durchlauf mit Ansatz B versucht werden. Aber: Nur wenn das Ground-Truth-Sample zeigt, dass Ansatz B die CER tatsaechlich verbessert.

### 4.4 Agreement-Metrik

Fuer jedes Objekt, das von zwei Modellen transkribiert wird:

```
"cross_model": {
  "model_b":              string,   // z.B. "claude-sonnet-4-20250514"
  "agreement_cer":        float,    // CER zwischen Modell A und Modell B (nicht gegen GT)
  "agreement_wer":        float,    // WER zwischen Modell A und Modell B
  "disagreement_pages":   int[],    // Seiten mit CER > 0.05 zwischen den Modellen
  "high_agreement":       boolean   // true wenn agreement_cer < 0.03
}
```

**Interpretation:**
- `agreement_cer < 0.03` (unter 3%): Hohe Uebereinstimmung. Die Transkription ist mit hoher Wahrscheinlichkeit korrekt — beide Modelle lesen dasselbe.
- `agreement_cer 0.03-0.10`: Moderate Abweichung. Einzelne Woerter oder Passagen divergieren. Review empfohlen.
- `agreement_cer > 0.10`: Starke Abweichung. Mindestens eines der Modelle hat erhebliche Probleme. Manuelle Pruefung noetig.

**Wichtig:** Agreement ist notwendig, aber nicht hinreichend fuer Korrektheit. Zwei Modelle koennen sich auf einen falschen Text einigen, besonders bei systematischen Biases (z.B. beide lesen "n" statt "u" in Kurrent). Der Agreement-Score ersetzt nicht die Ground-Truth-Evaluation, sondern ergaenzt sie als Triage-Signal.

### 4.5 Kosten-Abschaetzung

| Szenario | Objekte | API-Calls | Geschaetzte Kosten |
|---|---|---|---|
| GT-Sample (30 Objekte, 2 Modelle) | 30 | 60 | ~3-5 USD |
| Vollstaendiger Batch (2107 Objekte, 2 Modelle) | 2107 | 4214 | ~200-400 USD |
| Vollstaendiger Batch, nur 1 Modell + selektiv 2. Modell fuer Auffaellige | 2107 + ~400 | ~2500 | ~120-200 USD |

Empfehlung: Zunaechst nur das GT-Sample mit zwei Modellen transkribieren. Anhand der Ergebnisse entscheiden, ob der vollstaendige Batch eine Doppeltranskription rechtfertigt oder ob die quality_signals als Triage ausreichen.

### 4.6 Modellwahl fuer das zweite Modell

Basierend auf den Benchmark-Daten (Stand der Forschung):

| Kandidat | Staerken | Schwaechen | Kosten |
|---|---|---|---|
| Claude Sonnet | Beste CER auf Franzoesisch (1.6%), stark auf Englisch | Schwach auf historischem Deutsch (71% CER auf READ2016) | Mittel |
| GPT-4o | Solide ueber alle Sprachen, gute Korrektur-Ergebnisse | Neigt zu Over-Historicization (Levchenko) | Hoch |
| GPT-4o-mini | Ueberraschend stark (Gutteridge), 30x guenstiger als GPT-4o | Weniger getestet auf nicht-englischen Dokumenten | Niedrig |

Empfehlung: **Claude Sonnet** als zweites Modell neben Gemini Flash Lite. Begruendung: Maximale Diversitaet (anderer Anbieter, anderes Training), starke Baseline auf modernen und historischen Dokumenten, moderate Kosten. GPT-4o-mini als guenstige Alternative, falls Budget relevant.

### 4.7 Empirische Ergebnisse: Modellkonsensus-Validierung (Session 14)

**Durchfuehrung:** 27 Objekte, stratifiziert (3 pro Gruppe), mit `verify.py --sample 3 --force`. Modell A: Gemini Flash Lite, Modell B: Gemini 3 Flash. Neue Metriken: `effective_cer` (Minimum aus ordered/orderless CER) + `word_overlap` (Jaccard auf Wortmengen, order-invariant).

**4-Tier-Klassifikation:**

| Kategorie | Kriterium | Anzahl | Anteil |
|---|---|---|---|
| consensus_verified | effective_cer < 3% ODER (word_overlap >= 95% UND cer < 10%) | 7 | 26% |
| consensus_moderate | effective_cer < 10% ODER word_overlap >= 90% | 9 | 33% |
| consensus_review | word_overlap >= 75% | 4 | 15% |
| consensus_divergent | Rest | 7 | 26% |

**Ergebnisse nach Gruppe:**

| Gruppe | Ergebnis |
|---|---|
| Korrekturfahne | 3/3 verified (<1% CER) — gedruckter Text ist geloest |
| Typoskript | 1 verified + 2 moderate — sehr gut |
| Zeitungsausschnitt | 3 moderate — solide |
| Tabellarisch | 2 moderate, 1 divergent (near-blank) |
| Handschrift | 2 verified, 1 divergent — variabel |
| Konvolut | 1 moderate, 2 review — komplex |
| Formular | 1 verified, 1 review, 1 divergent |
| Kurztext | 1 moderate, 1 review, 1 divergent — wenig Text = instabil |
| Korrespondenz | 3/3 divergent — echte Herausforderung |

**Kernerkenntnisse:**
1. **Reading-Order-Divergenz** ist die Hauptursache fuer hohe CER bei Dokumenten mit komplexen Layouts. Beispiel: o_szd.142 hat CER 55% aber word_overlap 100% — identische Woerter in anderer Reihenfolge (Marginalia, Spalten). Die `word_overlap`-Metrik loest dieses Problem.
2. **Seiten-Halluzination**: Flash Lite dupliziert gelegentlich kurze Seiten (z.B. o_szd.101, Seiten 3/4 identisch). quality_signals v1.4 erkennt das jetzt.
3. **Bleed-Through**: VLM transkribiert durchscheinenden Text der Rueckseite. System-Prompt Regel 9 adressiert das.
4. **VLM-Nondeterminismus**: Derselbe Objekt liefert bei verschiedenen Laeufen unterschiedliche CER-Werte (o_szd.101: 10% vs 55%). Temperature 0.1 ist nicht deterministisch genug.

---

## 5. Verification-by-Vision (VbV)

Zwei VLMs vergleichen unabhaengig Faksimile-Bild mit Transkriptionstext und identifizieren Fehler. Staerker als Cross-Model (§4), weil das Quellbild einbezogen wird.

### 5.1 Zwei-Kanal-Workflow

| Kanal | Methode | Kosten | Dauer |
|---|---|---|---|
| A: Claude Code Agent | Read-Tool (Vision), Faksimile + Transkription | $0 | ~2-5 Min/Objekt |
| B: Gemini API | Bild + Text an Gemini Vision | ~$0.001/Seite | ~10 Sek/Objekt |

Merge: Beide finden Fehler X = hoch konfident. Nur einer = mittel konfident. Keiner = verified.

### 5.2 Error-Markup

```
«original→korrektur|konfidenz»
```

Beispiele: `«entbalten→enthalten|0.8»`, `«Kiow→Kiew|0.6»`. Guillemets gewaehlt, weil in keinem bestehenden Markup verwendet.

### 5.3 Empirische Befunde (Session 11, 8 Objekte)

| Muster | Befund |
|---|---|
| Gedruckter Text | Durchgehend korrekt bei Antiqua, 0 Fehler in 8 Objekten |
| Fraktur | >99% korrekt, aber typische Verwechslungen (fl-Ligatur, langes s, u/n) |
| Handschrift | Einzelwort-Ambiguitaeten, keine Halluzinationen. d/r-Verwechslung bei Korrespondenz |
| Handschriftliche Korrekturen | Schwaechste Schicht (~60-70% korrekt), Nonsens-Woerter bei Ueberlagerungen |
| Pipeline-Bug | Objekte mit >60 Bildern erzeugen leere Ergebnisse (o_szd.147) |

Methodische Grenze: Claude und Gemini teilen VLM-typische Schwaechen bei Kurrent. Cross-Model-Agreement ist dort weniger informativ.

---

## 6. Frontend-Anforderungen

### 6.1 Kontext

Lane 1 (Frontend) baut den Viewer unter `docs/`. Die Abschnitte 2 (quality_signals), 4 (Cross-Model) und 5 (VbV) produzieren Daten, die im Frontend sichtbar werden muessen.

### 6.2 Anforderung 1: needs_review-Indikator

Jedes Objekt mit `needs_review: true` muss im Katalog visuell markiert sein. Der Viewer muss `needs_review_reasons` anzeigen koennen (welche Signale ausgeloest haben).

**Filterung:** Der Katalog muss nach `needs_review` filterbar sein (alle / nur auffaellige / nur unauffaellige).

**Datenquelle:** `quality_signals.needs_review` und `quality_signals.needs_review_reasons` im Ergebnis-JSON.

### 6.3 Anforderung 2: Quality-Signal-Dashboard

Pro Objekt eine kompakte Uebersicht der quality_signals:

| Signal | Anzeige |
|---|---|
| Marker-Dichte | Zahl + Farbindikator (gruen/gelb/rot) |
| Seitenlaengen-Anomalien | Liste der anomalen Seiten |
| Duplikate | Betroffene Seitenpaare |
| Sprachkonsistenz | Match/Mismatch + erkannte Sprache |
| Leerseiten | Anzahl |

Kein eigener View noetig — die Signale koennen im bestehenden Objekt-Detail-View eingeblendet werden.

### 6.4 Anforderung 3: Diff-Ansicht fuer Cross-Model-Verification

Wenn fuer ein Objekt zwei Transkriptionen vorliegen (Gemini + Claude), muss der Viewer einen Vergleichsmodus anbieten:

**Layout:** Zwei Transkriptionstexte nebeneinander, Differenzen farblich hervorgehoben.

**Diff-Granularitaet:** Wortebene (nicht zeichenebene — zu unuebersichtlich bei laengerem Text). Woerter, die nur in Transkription A vorkommen: rot. Woerter, die nur in B vorkommen: blau. Uebereinstimmende Woerter: schwarz.

**Interaktion:** Der Benutzer kann fuer jedes divergierende Wort waehlen, welche Lesung uebernommen wird (A, B, oder manuell). Das ist der Expert-in-the-Loop-Kern fuer das DIA-XAI-Projekt.

**Datenquelle:** Zwei separate JSON-Ergebnisse fuer dasselbe Objekt (unterschiedliche `model`-Werte). Die Zuordnung erfolgt ueber `object_id`.

### 6.5 Anforderung 4: CER-Anzeige (nach Ground-Truth-Erstellung)

Wenn Ground-Truth-Referenzen vorliegen, soll der Viewer die CER pro Objekt und pro Seite anzeigen koennen.

**Anzeige:** CER-Wert als Zahl + Farbkodierung (gruen < 5%, gelb 5-15%, rot > 15%).

**Datenquelle:** Wird als separates Feld im JSON ergaenzt, nachdem die Referenztranskription erstellt und ausgewertet ist. Format:

```
"evaluation": {
  "reference_available":  boolean,
  "cer":                  float,     // Gesamt-CER (Basis, nach Normalisierung)
  "wer":                  float,
  "cer_per_page":         float[],
  "evaluated_at":         string     // ISO-Datum
}
```

### 6.6 Prioritaet

| Anforderung | Abhaengigkeit | Prioritaet |
|---|---|---|
| needs_review-Indikator | quality_signals (Lane 3) | Sofort — blockiert nicht, quality_signals koennen sofort implementiert werden |
| Quality-Signal-Dashboard | quality_signals (Lane 3) | Sofort |
| Diff-Ansicht | Cross-Model-Verification (Phase 4) | Nach GT-Sample |
| CER-Anzeige | Ground Truth (manuelle Arbeit) | Nach GT-Erstellung |

---

## 6. Verification-by-Vision

Vollstaendige Spezifikation: [[verification-by-vision]]

**Kernidee:** Zwei VLMs vergleichen unabhaengig das Faksimile-Bild mit der Transkription und identifizieren konkrete Fehler. Kanal A (Claude Code Agent, kostenlos — liest Bilder via eingebauter Vision) + Kanal B (Gemini API, `verify_gemini.py`). Cross-Model-Agreement aus zwei unabhaengigen Pruefungen.

**Getestet an 6 Objekten (Session 11):** 1x `llm_verified`, 4x `llm_error_suggestion`, 1x Pipeline-Bug. Staerkstes Verifikationsverfahren im Projekt — direkter Bild↔Text-Vergleich statt nur Textvergleich.

**Empirische Muster:**
- Gedruckter Text: durchgehend korrekt (0 Fehler in 6 Objekten)
- Handschrift: gut, Einzelwort-Ambiguitaeten bei Kurrent (keine Halluzinationen)
- Handschriftliche Korrekturen/Vermerke: schwaechste Schicht (~60-70% korrekt)

**Error-Markup:** Fehler werden inline im Transkriptionstext markiert als `«original→korrektur|konfidenz»`. Im Frontend farbig hervorgehoben, per Click akzeptierbar.

**Status-Kategorien:** `llm_verified` | `llm_error_suggestion` | `unverified` | `human_verified`

**Abgrenzung:** VbV ersetzt nicht den manuellen Pilot (CER) und nicht quality_signals (Anomalie-Erkennung). Es ergaenzt beide um eine direkte Bildpruefung mit konkreten, actionable Fehlermeldungen.

---

## 7. Modellkonsensus (LLM-as-Judge)

> **Definition:** *Modellkonsensus* (Cross-Model Agreement) bezeichnet den automatischen Vergleich zweier unabhaengiger VLM-Transkriptionen desselben Faksimiles. Zwei verschiedene Modelle (Gemini Flash Lite + Gemini Flash) transkribieren dasselbe Bild getrennt; die Uebereinstimmung wird zeichenweise (CER = Character Error Rate) und wortweise (Jaccard Word Overlap) gemessen. Wo die Modelle uebereinstimmen, ist die Transkription mit hoher Wahrscheinlichkeit korrekt. Wo sie divergieren, markiert das automatisch Stellen fuer menschliche Pruefung. Das Ergebnis wird in 4 Stufen klassifiziert: `consensus_verified` (CER < 3%), `consensus_moderate` (CER < 10%), `consensus_review` (Overlap >= 75%), `consensus_divergent` (Overlap < 75%).

### 7.1 Motivation

Die bisherigen Verifikationsansaetze (quality_signals, Cross-Model, VbV) haben jeweils Grenzen:
- **quality_signals** erkennen Formatanomalien, nicht Inhaltsfehler
- **Cross-Model** (Abschnitt 4) vergleicht zwei Transkriptionen, aber ohne Judge-Rolle
- **VbV** (Abschnitt 6) prueft Bild↔Text, aber nur stichprobenartig

Der Modellkonsensus kombiniert alle drei Dimensionen und fuegt eine **Judge-Rolle** hinzu, die methodisch dem LLM-as-a-Judge-Paradigma (Gu et al. 2025, arXiv:2411.15594) folgt.

### 7.2 Architektur

```
Faksimile-Bild
    │
    ├──→ Modell A: Gemini 3.1 Flash Lite (billig, Ersttranskription)
    │        → Transkription A (existiert bereits fuer alle Objekte)
    │
    ├──→ Modell B: Gemini 3.1 Flash (staerker, unabhaengige Zweittranskription)
    │        → Transkription B
    │
    └──→ Judge: Claude (via Claude Code Subagent mit Vision)
             Eingabe: Bild + Transkription A + Transkription B
             Ausgabe: Bewertung, korrigierte Version, Modellkonsensus-Score
```

**Judge-Prompt-Struktur:**
- Claude sieht das Originalbild UND beide Transkriptionen
- Aufgabe: Identifiziere Abweichungen, entscheide welche Version korrekt ist, oder markiere Stellen wo beide falsch liegen
- Output: Modellkonsensus-Transkription + per-Seite-Konfidenz + Fehlerlog

### 7.3 Modellkonsensus-Kategorien

| Kategorie | Bedingung | Aktion |
|---|---|---|
| **consensus_verified** | A ≈ B ≈ Judge (CER < 3%) | Akzeptiere als automatisches GT |
| **consensus_corrected** | A ≠ B, Judge korrigiert | Verwende Judge-Version, flagge fuer Stichprobe |
| **consensus_divergent** | Alle drei divergieren (CER > 10%) | Manueller Review erforderlich |

### 7.4 Wissenschaftliche Fundierung

| Behauptung | Stuetzende Evidenz |
|---|---|
| Korrekte Outputs konvergieren | Zhang et al. 2025 (ICLR 2026): CE framework |
| Accept/Abstain ist formalisierbar | Risk-Controlled VLM OCR 2026 |
| Kreuzkorrektur mit Bild funktioniert | Humphries et al. 2024: 8.0% → 1.8% CER |
| Selbstkorrektur funktioniert NICHT | Crosilla et al. 2025: 3.7-4.9x Verschlechterung |
| LLM-generated GT mit Ensemble: ~2-6% Error Rate | Emergent consensus in LLM-Generated GT literature |

### 7.5 Implementierungsstrategie

**Phase 1: Validierung (30 Objekte)**
- 30 stratifizierte Objekte (3-4 pro Gruppe) durch alle 3 Modelle
- Claude Code Subagent mit eingebautem Vision liest GAMS-Bilder direkt
- Gemini 3.1 Flash als Zweittranskriptor (nicht Flash Lite)
- CER zwischen A↔B, A↔Judge, B↔Judge berechnen
- Modellkonsensus-Kategorien zuweisen
- Ergebnis: Wie viel % der Objekte erreichen `consensus_verified`?

**Phase 2: Skalierung (nur bei Erfolg)**
- Wenn >70% der Validierungs-Objekte `consensus_verified` erreichen:
  → Selektive Modellkonsensus-Pruefung fuer alle `needs_review`-Objekte (~44% von 2107)
- Wenn <70%: Rueckfall auf manuelles GT-Sample (Pilot-Design)

**Phase 3: Kalibrierung**
- Modellkonsensus-verifizierte Objekte als automatisches GT verwenden
- quality_signals-Schwellenwerte gegen dieses GT kalibrieren
- DWR (Dictionary Word Ratio) und group_text_density validieren

### 7.6 Kosten-Abschaetzung

| Schritt | Objekte | API-Calls | Geschaetzte Kosten |
|---|---|---|---|
| Validierung (30 Objekte, 3 Modelle) | 30 | ~90 | ~$5-10 |
| Selektiv (44% von 2107, 2 Extra-Modelle) | ~930 | ~1860 | ~$100-200 |
| Vollstaendig (alle 2107, 3 Modelle) | 2107 | ~6321 | ~$300-500 |

**Empfehlung:** Validierung zuerst (30 Objekte). Entscheidung ueber Skalierung basiert auf Modellkonsensus-Rate und manueller Stichprobe der Ergebnisse.

### 7.7 Abgrenzungen

- **Modellkonsensus ≠ Wahrheit:** Drei Modelle koennen sich auf denselben Fehler einigen (systematischer Bias). Deshalb ist eine manuelle Stichprobe der `consensus_verified`-Objekte noetig (~5-10 Objekte pruefen).
- **Judge ist nicht neutral:** Claude hat eigene Biases. Der Judge-Prompt muss instruieren, Abweichungen zu begruenden, nicht einfach "das bessere" auszuwaehlen.
- **Kosten sind real:** 3 Modelle = ~3x Basiskosten. Nur sinnvoll wenn manuelle GT-Erstellung teurer waere (was bei ~2107 Objekten der Fall ist).

---

## 8. Agent-Verifikation (agent_verified)

*Implementiert in Session 18 (2. April 2026). Empirische Ergebnisse → [[evaluation-results]].*

### 8.1 Motivation

Menschliches Expert-Review skaliert nicht — bei 2107 Objekten ist Seite-fuer-Seite-Verifikation durch den Projektleiter ein Flaschenhals. Gleichzeitig ist die rein automatische Qualitaetsmessung (quality_signals, Modellkonsensus) blind fuer bestimmte Fehlertypen, die nur im Bild-Text-Vergleich sichtbar werden (z.B. Fraktur f/s-Verwechslungen, die echte Woerter ergeben).

Agent-Verifikation schliesst diese Luecke: Ein zweites VLM (Claude) vergleicht systematisch Faksimile-Bilder gegen die Gemini-Transkription und meldet Abweichungen. Das ist methodisch ein **Cross-Provider-Check mit Vision** — konzeptionell eine Operationalisierung von Verification-by-Vision (§5).

### 8.2 4-Tier Review-Modell

| Tier | Status im JSON | Label (Frontend) | Vertrauensniveau | Quelle |
|---|---|---|---|---|
| 0 | `gt_verified` (GT-Draft) | GT ✓ | Hoechstes | Mensch auf 3-Modell-GT-Draft |
| 1 | `approved` | Geprueft | Hoch | Mensch im Frontend-Viewer |
| 2 | `agent_verified` | Agent ✓ | Mittel-hoch | Claude Code Sub-Agent (Vision) |
| 3 | — (kein Review) | LLM OK / Review | Niedrig | Nur Pipeline-Selbsteinschaetzung |

**Wichtig:** `agent_verified` ist kein Ersatz fuer menschliches Review, sondern ein **Zwischen-Tier**, das:
- Objekte identifiziert, die wahrscheinlich korrekt sind (zur Priorisierung menschlicher Zeit)
- Konkrete Fehler findet und korrigiert (der korrigierte Text ist besser als das VLM-Original)
- CER-Schaetzungen pro Objekt liefert (fuer Aggregatstatistiken)

### 8.3 Technische Umsetzung

**Workflow:**

1. Sub-Agent wird mit Object-ID, Collection und Bildpfaden gestartet
2. Agent liest alle Seitenbilder aus dem lokalen Backup (`SZD_BACKUP_ROOT`)
3. Agent liest die Transkription aus dem Pipeline-JSON
4. Pro Content-Seite: Bild-Text-Vergleich, Zeichen fuer Zeichen
5. Ergebnis: Fehlerliste mit Zitat, Korrektur, Schweregrad, Qualitaetsnote
6. Korrekturen werden direkt im JSON angewendet
7. Review-Metadaten werden geschrieben

**JSON-Struktur:**

```json
{
  "review": {
    "status": "agent_verified",
    "agent_model": "claude-opus-4-6",
    "errors_found": 2,
    "estimated_accuracy": 0.996,
    "edited_pages": [1, 3],
    "reviewed_by": "Claude Code Agent",
    "reviewed_at": "2026-04-02T..."
  }
}
```

**API:** `POST /api/approve` mit `status: "agent_verified"` (`serve.py`).

**Parallelisierung:** Bis zu 4 Sub-Agents gleichzeitig (je 2 Objekte pro Agent). Ein Batch von 8 Objekten dauert ~3 Minuten.

### 8.4 Verhaeltnis zu bestehenden Verfahren

| Verfahren | Vergleichsgrundlage | Persistenz | Abschnitt |
|---|---|---|---|
| Cross-Model (Modellkonsensus) | Text ↔ Text (2 VLMs) | `_consensus.json` | §4 + §7 |
| Verification-by-Vision (VbV) | Bild ↔ Text (manuell) | Nicht persistiert | §5 |
| **Agent-Verifikation** | **Bild ↔ Text (automatisch)** | **`review` im Ergebnis-JSON** | **§8** |

Agent-Verifikation kombiniert die Staerke von VbV (Bild-Text-Vergleich) mit der Skalierbarkeit von Modellkonsensus (automatisiert). Die Schwaeche: Claude als Judge kann selbst Fehler machen — daher der niedrigere Tier-Rang als menschliches Review.

### 8.5 Empirische Ergebnisse

In Session 18 wurden 12 Objekte agent-verifiziert (→ [[evaluation-results]] fuer Details):

- **4 Objekte fehlerfrei** (100% Genauigkeit)
- **6 Objekte mit 1–5 Fehlern** (99.1–99.9%)
- **2 Objekte mit Strukturproblemen** (90–98.5%)
- **Hauptfehlertypen**: Fraktur f/s-Verwechslung (hoch), Grossschreibung (niedrig), Tabellenstruktur (hoch)

---

## Zusammenfassung der Abhaengigkeiten

```
ERLEDIGT:
  ├── quality_signals v1.1 implementiert (Abschnitt 2) — rekalibriert, 68% → 44%
  ├── needs_review-Indikator im Viewer (Abschnitt 5.2)
  ├── Annotationsprotokoll finalisiert (annotation-protocol.md)
  ├── evaluate.py: CER/WER-Berechnung mit Normalisierung
  ├── quality_report.py: Aggregierte Statistiken
  └── Batch-Transkription laeuft (~360+/2107 Objekte)

NAECHSTER SCHRITT — Modellkonsensus-Validierung (Abschnitt 7):
  └── 30 Objekte durch 3 Modelle (Flash Lite + Flash + Claude Judge)
        |
        ├── Modellkonsensus-Rate bestimmen (Ziel: >70% consensus_verified)
        ├── CER zwischen Modellpaaren berechnen
        ├── Manuelle Stichprobe der Modellkonsensus-Ergebnisse (~5-10 Objekte)
        └── Entscheidung: Automatisches GT akzeptieren?
              |
              JA (>70% Modellkonsensus):
              │  ├── quality_signals kalibrieren gegen Modellkonsensus-GT
              │  ├── Selektive Modellkonsensus-Pruefung fuer needs_review-Objekte
              │  ├── DWR + group_text_density validieren
              │  └── Statistik-Dashboard mit Modellkonsensus-Metriken
              │
              NEIN (<70% Modellkonsensus):
                 ├── Manueller Pilot (→ Adaptive Sampling-Anpassung §1.9)
                 ├── Manuelles GT-Sample (30 Objekte)
                 └── Klassischer CER-Workflow (Abschnitt 1)

SPAETER (nach GT-Kalibrierung):
  ├── Prompt-Experiment (CER-Vergleich V1/V2/V3)
  ├── Provider-Vergleich (Gemini vs. Claude vs. GPT-4o)
  ├── Diff-Ansicht im Viewer mit echten Cross-Model-Daten
  └── Entscheidung: Doppeltranskription fuer vollen Batch?
```
