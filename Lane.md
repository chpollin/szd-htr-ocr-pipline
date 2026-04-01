# Lane-Koordination: SZD-HTR-Projekt

Letzte Aktualisierung: 2026-04-01 (Session 8, Forschungsleitstelle v0.4)

---

## Projektziel (fuer alle Lanes)

2107 Objekte des Stefan-Zweig-Nachlasses transkribieren (VLM-gestuetzte HTR), Qualitaet empirisch absichern und Ergebnisse in TEI-XML ueberfuehren. Zwei gleichwertige Ziele: **Produktion** (alle Objekte transkribiert, im Frontend pruefbar) und **Methodik** (dokumentierte Evaluation fuer den Aufsatz "Amplified, Not Automated"). Die Pipeline endet nicht bei JSON — die Transkriptionen fliessen via standardisiertem Interchange-Format in [teiCrafter](https://digitalhumanitiescraft.github.io/teiCrafter/) fuer die TEI-Annotation.

---

## Lane-Struktur

| Lane | Rolle | Arbeitsbereich | Darf NICHT anfassen |
|---|---|---|---|
| **Forschungsleitstelle** | Koordination, Entscheidungen | Dieses Dokument, Plan.md | — |
| **L1** | Frontend | `docs/` | `pipeline/`, `knowledge/` |
| **L2** | Methodik/Forschung | `knowledge/` | `pipeline/`, `docs/` — kein Code |
| **L3** | Backend/Daten | `pipeline/`, `results/` | `docs/`, `knowledge/` |

Alle Lanes committen nur eigene Dateien. Fremde Aenderungen nicht mitstagen.

---

## Abhaengigkeiten

```
L2: pilot-design.md (fertig) ──→ Operator: Pilot durchfuehren (5 Seiten)
  ──→ L2: Auswertung ──→ 30-Objekt-Sample-Design

L3: JSON-Parsing haerten ──→ L3: quality_signals.py ──→ L3: Backfill + Build
  ──→ L1: quality_signals-UI mit echten Daten ──→ Operator: visueller Review

L2: verification-concept.md §2.5 ──→ L3: quality_signals JSON-Spec
L2: verification-concept.md §5   ──→ L1: Frontend-Anforderungen
L3: CER-Script                   ──→ L2: Pilot-Auswertung

L2: htr-interchange-format.md   ──→ L3: Export + teiCrafter-Integration
```

---

## Auftraege: Lane 3 (Backend/Daten)

### Was du wissen musst

Du bist fuer die Pipeline (`pipeline/`), die Ergebnisse (`results/`) und die Datenverarbeitung zustaendig. L1 (Frontend) wartet auf deine `quality_signals`-Daten, um die Review-UI mit echten Werten zu fuellen. L2 (Methodik) hat die Spezifikation der 6 Signale in `knowledge/verification-concept.md` §2.5 definiert — das ist deine Quelle. Der Operator prueft jede Datenaenderung visuell im Frontend, deshalb endet jeder deiner Schritte mit `build_viewer_data.py`.

### Deine Aufgaben (in dieser Reihenfolge)

**Schritt 1: JSON-Parsing haerten**
- Gemini liefert gelegentlich Markdown-Codeblocks (` ```json ... ``` `) und invalide Escape-Sequenzen (`\j`).
- `transcribe.py`: Codeblock-Stripping vor `json.loads()`, Escape-Sanitization, strukturiertes Retry (max 2), Logging bei Parse-Fehler (Objekt-ID + Rohtext in Log).
- Testen: Mindestens 3 Objekte neu transkribieren (`--force`), darunter o_szd.277 (Konvolut, das "medium" war).
- **Erfolgskriterium:** Kein unkontrollierter Abbruch bei JSON-Fehlern.

**Schritt 2: quality_signals.py implementieren**
- Lies die Spec: `knowledge/verification-concept.md` §2.5 (JSON-Schema, 6 Signale, `needs_review`-Logik).
- 6 Signale: `page_length_anomaly`, `page_image_mismatch`, `duplicate_pages`, `language_mismatch`, `marker_density`, `group_text_density`.
- Output: `quality_signals`-Objekt wird in jede Result-JSON eingebettet (neben `result`).
- `needs_review: boolean` + `needs_review_reasons: string[]` als Top-Level-Zusammenfassung.
- `group_text_density` erst ab 10 Objekte/Gruppe aktivieren (bei 16 Objekten noch zu wenig Daten fuer die meisten Gruppen — dokumentiere, welche Gruppen genuegend Daten haben).

**Schritt 3: Backfill + Build**
- `quality_signals` fuer alle 16 bestehenden Objekte in `results/` nachberechnen.
- `build_viewer_data.py` anpassen: `quality_signals` + `needs_review` in `catalog.json` und `data/{collection}.json` durchreichen.
- Build ausfuehren. Pruefen, dass `catalog.json` die neuen Felder enthaelt.

**Schritt 4: Batch-Vorbereitung**
- Dry-Run (`--all --dry-run`): Wie viele Objekte wuerden transkribiert? Wie verteilen sie sich auf Gruppen?
- Kostenabschaetzung dokumentieren (Tokens × Preis fuer Gemini Flash Lite).
- Noch NICHT den vollen Batch starten — erst nach Operator-Freigabe.

### Reporting

Nach jedem abgeschlossenen Schritt: **Kurzmeldung an die Forschungsleitstelle** im folgenden Format direkt im Chat (nicht in eine Datei schreiben):

```
LANE 3 — SCHRITT [N] ABGESCHLOSSEN
Was: [1 Satz]
Ergebnis: [Dateien geaendert/erzeugt, Metriken]
Probleme: [Falls ja — was, warum, Workaround]
Learnings: [Was hast du ueber die Daten/Pipeline gelernt, das fuer L2 oder L1 relevant ist?]
Naechster Schritt: [Was kommt als naechstes]
```

### Was du NICHT tun sollst

- Keine Aenderungen an `docs/` oder `knowledge/`.
- Keinen vollen Batch-Run ohne Operator-Freigabe.
- Keine Aenderungen am Prompt-System (`prompts/`) ohne Ruecksprache.

### Offene Fragen (klaere, wenn du kannst)

- Wie viele der 2107 Objekte haben tatsaechlich Bilder im Backup? (`--dry-run` zeigt das.)
- Welche Gruppen haben genuegend Objekte fuer `group_text_density` (≥10)?
- Gibt es weitere JSON-Parsing-Muster ausser Codeblocks und `\j`?

---

## Auftraege: Lane 1 (Frontend)

### Was du wissen musst

Du bist fuer das Frontend (`docs/`) zustaendig — Katalog, Viewer, Design-System. L3 (Backend) arbeitet gerade daran, `quality_signals`-Daten in die JSONs einzubauen. Sobald L3 fertig ist und `build_viewer_data.py` laeuft, enthalten `catalog.json` und `data/{collection}.json` neue Felder: `quality_signals`, `needs_review`, `needs_review_reasons`. L2 (Methodik) hat die Frontend-Anforderungen in `knowledge/verification-concept.md` §5 spezifiziert.

### Deine Aufgaben (in dieser Reihenfolge)

**Schritt 1: Classification-Pruefung abschliessen**
- Du hast TEI-Classification-Integration begonnen. Pruefe alle 16 Objekte im Katalog:
  - Wird die Typ-Spalte korrekt befuellt? Tooltip mit Objecttyp?
  - Gruppen-Filter funktioniert?
  - Fallback bei fehlender Classification?
- Dokumentiere gefundene Probleme als Kommentar im Chat (nicht in Dateien).

**Schritt 2: quality_signals-UI aktivieren (WARTET AUF L3)**
- Voraussetzung: L3 hat Schritt 3 (Backfill + Build) abgeschlossen.
- Review-Spalte im Katalog: `needs_review` als Burgundy/Gruen-Badge, sortierbar, Toggle-Filter.
- Qualitaets-Panel im Viewer: `needs_review_reasons` als Liste, `marker_density` als Balken/Zahl, Leerseiten-Warnung, Sprachkonsistenz-Anzeige.
- Seiten-Anomalien: ⚠-Marker bei Seiten mit `page_length_anomaly`.
- Testen mit den 16 Objekten nach L3-Build.

**Schritt 3: Statistik-Uebersicht (optional, wenn Zeit)**
- Zusammenfassung ueber Sammlungen: Wie viele Objekte, wie viele needs_review, Verteilung nach Gruppe.
- Kann ein einfacher Abschnitt im Katalog sein (z.B. oberhalb der Tabelle).

### Reporting

Nach jedem abgeschlossenen Schritt: **Kurzmeldung an die Forschungsleitstelle** im Chat:

```
LANE 1 — SCHRITT [N] ABGESCHLOSSEN
Was: [1 Satz]
Ergebnis: [Was sieht man jetzt im Frontend?]
Probleme: [Falls ja — was, Screenshot-Beschreibung, Workaround]
Learnings: [Was hast du ueber die Daten/Darstellung gelernt?]
Naechster Schritt: [Was kommt als naechstes]
```

### Was du NICHT tun sollst

- Keine Aenderungen an `pipeline/` oder `knowledge/`.
- Keine Dummy-Daten fuer quality_signals erfinden — warte auf L3.
- Keine neuen Bibliotheken/Frameworks einbauen (Vanilla JS bleibt).

### Offene Fragen (klaere, wenn du kannst)

- Gibt es Objekte, bei denen GAMS-Thumbnails fehlen oder 404 liefern?
- Wie verhaelt sich der Katalog bei >500 Objekten (Performance)?
- Reicht die aktuelle Pagination fuer 2107 Eintraege?

---

## Auftraege: Lane 2 (Methodik/Forschung)

### Was du wissen musst

Du bist fuer die methodische Fundierung zustaendig — Evaluationsdesign, Spezifikationen, Literaturarbeit. Deine Deliverables landen in `knowledge/`. Du schreibst keinen Code. L3 implementiert deine Spezifikationen (`verification-concept.md` §2.5 → quality_signals, §4 → Cross-Model). L1 setzt deine Frontend-Anforderungen um (§5). Die kritische Luecke: Noch keine Transkription wurde manuell geprueft. Der Pilot schliesst das.

### Deine Aufgaben (in dieser Reihenfolge)

**Schritt 1: Pilot-Design finalisieren**
- `knowledge/pilot-design.md` liegt vor. Pruefe nochmal:
  - Sind die 5 Seiten aus genuegend verschiedenen Gruppen?
  - Ist das Pruefprotokoll klar genug, dass der Operator es in 2-3h abarbeiten kann?
  - Sind die Eskalationsschwellen definiert (ab welchem CER wird das Sample-Design geaendert)?
- Falls Anpassungen noetig: Datei aktualisieren. Falls fertig: Bestaetigen.

**Schritt 2: HTR-Interchange-Format spezifizieren**
- Neues Deliverable: `knowledge/htr-interchange-format.md`
- Zweck: Standardisiertes JSON-Format fuer HTR/OCR-Ergebnisse, das von teiCrafter (und potenziell anderen Tools) als Import verwendet werden kann.
- Das Format muss projektunabhaengig sein. Orientiere dich am aktuellen szd-htr-Output (`results/`), aber abstrahiere die SZD-spezifischen Felder.
- Kernstruktur: Seiten mit Transkriptionen, Quell-Metadaten, Provenienz (Modell, Zeitstempel), Qualitaetssignale.
- Lies den teiCrafter-Import (Step 1 akzeptiert: .txt, .md, .xml, .docx — kein JSON bisher) und ueberlege, welche Felder teiCrafter braucht, um den Mapping-Kontext (Sprache, Epoche, Dokumenttyp) automatisch vorzubelegen.
- JSON Schema beifuegen (als Codeblock in der Spec).
- teiCrafter-Repo: `C:\Users\Chrisi\Documents\GitHub\DHCraft\teiCrafter`

**Schritt 3: Pilot-Ergebnisse auswerten (WARTET AUF Operator)**
- Voraussetzung: Operator hat Pilot durchgefuehrt, Ergebnisse liegen vor.
- CER pro Seite und pro Gruppe berechnen (manuell oder mit L3-Script).
- Annotationsprotokoll ggf. anpassen.
- 30-Objekt-GT-Sample-Design finalisieren (informiert durch Pilot-CER).
- Ergebnis: `knowledge/pilot-results.md`

**Schritt 4: Prompt-Experiment-Design**
- Gepaarter 3-Varianten-Vergleich: V1 nur System, V2 System+Gruppe, V3 System+Gruppe+Kontext.
- 30 GT-Objekte × 3 Varianten = 90 API-Calls.
- Design als Abschnitt in `knowledge/verification-concept.md` §3 verfeinern (ist schon skizziert).
- Konkrete Hypothesen formulieren, Auswertungsplan (gepaarter t-Test oder Wilcoxon auf CER).

### Reporting

Nach jedem abgeschlossenen Schritt: **Kurzmeldung an die Forschungsleitstelle** im Chat:

```
LANE 2 — SCHRITT [N] ABGESCHLOSSEN
Was: [1 Satz]
Ergebnis: [Dateiname in knowledge/, was steht drin]
Probleme: [Methodische Unsicherheiten, fehlende Informationen]
Learnings: [Was hast du ueber die Methodik gelernt, das fuer L1 oder L3 relevant ist?]
Naechster Schritt: [Was kommt als naechstes]
```

### Was du NICHT tun sollst

- Kein Code schreiben oder aendern.
- Keine Aenderungen an `pipeline/` oder `docs/`.
- Keine Entscheidungen treffen, die Batch-Kosten verursachen (das entscheidet der Operator).

### Offene Fragen (klaere durch Recherche oder flagge sie)

- teiCrafter: Welche Metadaten braucht Step 2 (Mapping) minimal? → teiCrafter-Repo lesen.
- Gibt es bestehende Standards fuer HTR-Output-Formate (ALTO, PAGE XML, hOCR)? Wie verhaelt sich unser Format dazu?
- Prompt-Experiment: Ist der 3-Varianten-Vergleich statistisch valide bei n=30?

---

## Status der Lanes

### Lane 1 — Frontend
**Stand:** 2026-04-01, Schritt 1+2 abgeschlossen. Commit `e1b90e8`.

**Schritt 1 (Classification-Pruefung): ERLEDIGT**
- Typ-Spalte zeigt TEI `classification` statt Prompt-Gruppe (Verlagsvertraege, Tagebuecher, Korrespondenz etc.)
- Tooltip zeigt `objecttyp` (Typoskriptdurchschlag, Notizbuch, Eintrittskarte)
- Gruppen-Filter: dynamische Dropdown, Optionen passen sich an gewaehlte Sammlung an
- Korrespondenz-Fallback OK ("Korrespondenz"/"Brief" wenn kein TEI)
- 16/16 Objekte geprueft, keine Probleme

**Offene Fragen beantwortet:**
- GAMS-Thumbnails: 16/16 OK (HTTP 200, 1.2-2.6 KB). Kein 404.
- Performance: catalog.json bei 2107 Objekten ~1.5 MB. 50 Zeilen/Seite = 43 Seiten. Kein Performance-Risiko.
- Pagination: Architektur skaliert (nur sichtbare Seite wird gerendert).

**Schritt 2 (quality_signals-UI): CODE FERTIG, WARTET AUF L3-DATEN**
- Review-Spalte (Katalog): `needs_review` Badge, sortierbar, Toggle-Filter
- Qualitaets-Panel (Viewer): needs_review_reasons, marker_density, empty_pages, language_match
- Seiten-Anomalie: Warning-Icon bei page_length_anomalies
- Graceful Degradation: alles unsichtbar wenn Felder fehlen
- Sobald L3 Schritt 3 (Backfill + Build) abschliesst → Reload + visueller Test

**Viewer-Verbesserungen (Commit `05febe9`):**
- Image-Viewer: Scroll-Wheel-Zoom (zentriert auf Cursor), Drag-to-Pan, Touch-Pinch-Zoom, 90°-Rotation
- Zoom/Rotate-Controls als Floating-Overlay im Bild-Panel (nicht mehr in Nav-Bar)
- Keyboard: +/- Zoom, 0 Reset, R Rotate
- Metadaten-Bar umstrukturiert: Metadaten + Verifikation in einer kompakten Zeile, immer sichtbar (kein "i"-Toggle mehr)
- Nav-Bar entschlackt: nur noch Objekt-Nav + Seiten-Nav + Edit/JSON

**CSS/HTML-Cleanup (Commit `52a967a`):**
- 7 Farb-Variablen extrahiert (--sz-success, --sz-warning, --sz-danger, --sz-img-bg)
- 6 redundante font-family-Deklarationen entfernt
- Toten CSS/JS-Code entfernt (.badge-group, .viewer__verification, renderVerificationBar)
- Responsive fuer Image-Controls ergaenzt
- Help-Modal aktualisiert (Zoom/Pan/Rotate-Doku, Shortcuts +/-/0/R, Gruppe G)
- HTML-Semantik: viewer div → main

**Korrespondenzen-Typ-Erkennung:**
- Fallback erkennt jetzt Brief/Postkarte/Ansichtspostkarte/Telegramm aus dem Titel
- Verteilung im Bestand: 618 Briefe, 413 Andere, 94 Postkarten, 56 Ansichtspostkarten, 5 Telegramme
- Hinweis: Aenderung an `pipeline/build_viewer_data.py` (Cross-Lane, von Forschungsleitstelle autorisiert)

**Schritt 3 (Statistik-Uebersicht): ZURÜCKGESTELLT** — erst sinnvoll nach Batch-Lauf

### Lane 2 — Methodik
**Stand:** 2026-04-01 (Session 8).
- [x] Schritt 1: pilot-design.md finalisiert — 5 Seiten, 5 Gruppen, Eskalationsschwellen, Pruefprotokoll. Keine Anpassung noetig.
- [x] Schritt 2: htr-interchange-format.md geschrieben — JSON Schema v0.1, teiCrafter-Mapping, SZD-HTR-Mapping, Abgrenzung ALTO/PAGE/hOCR, Beispiel.
- [ ] Schritt 3: Pilot-Ergebnisse auswerten — WARTET AUF Operator-Durchfuehrung.
- [ ] Schritt 4: Prompt-Experiment-Design — WARTET AUF Pilot-Ergebnisse.

### Lane 3 — Backend
**Stand:** 2026-04-01. 16/2107 Objekte transkribiert, 9/9 Gruppen abgedeckt. JSON-Parsing-Problem bekannt. quality_signals noch nicht implementiert.

---

## Entscheidungslog

| Datum | Entscheidung | Begruendung | Betrifft |
|---|---|---|---|
| 2026-04-01 | Pilot vor vollem GT-Sample | CER unbekannt — Sample-Design ohne Pilot ist blind | Alle |
| 2026-04-01 | quality_signals sofort | Kostet nichts, braucht kein GT, bietet Triage fuer Batch | L3, L1 |
| 2026-04-01 | Cross-Model: Agreement-First | Unabhaengige Doppeltranskription methodisch sauberer | L3 |
| 2026-04-01 | Claude Sonnet als zweites Modell | Max. Diversitaet zu Gemini, starke Baseline, moderate Kosten | L3 |
| 2026-04-01 | teiCrafter-Integration via Interchange-Format | Kein eigener TEI-Konverter — teiCrafter hat LLM-Annotation + Validierung | L2, L3 |
