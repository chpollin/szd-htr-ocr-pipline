# Lane-Koordination: SZD-HTR-Projekt

Letzte Aktualisierung: 2026-04-01 (Session 8–10, Forschungsleitstelle v0.5)

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

L2: htr-interchange-format.md        ──→ L3: export_interchange.py (Seitentrenner |{n}|)
L2: teiCrafter-integration.md        ──→ teiCrafter-Repo: JSON-Import, Schema, Templates
L2: tei-target-structure.md          ──→ TEI-Zielformat fuer Phase 5b

L2: verification-by-vision Spec ──→ L3: verify.py (Claude+Gemini Vision)
  ──→ L1: Error-Markup-Rendering + Status-Badges
```

### Naechste Schritte (Prioritaet)

```
SOFORT (parallel, unabhaengig voneinander):
  ├── Operator: PILOT durchfuehren (5 Seiten, 2-3h) ← KRITISCHER PFAD
  ├── L3: quality_signals.py implementieren + Backfill + Build
  ├── L3: Gezieltes Sample fertigstellen (~74 Objekte)
  └── L3: export_interchange.py (Spec steht)

NACH PILOT:
  ├── L2: pilot-results.md (CER pro Gruppe, Fehlertyp-Verteilung)
  ├── L2: Sample-Design finalisieren (31 Objekte, Regeln aus pilot-design.md §4)
  └── L2: Prompt-Experiment-Design

NACH QUALITY_SIGNALS + BUILD:
  ├── L1: quality_signals-UI mit echten Daten testen
  └── Operator: Visueller Review der needs_review-Objekte
```

---

## Auftraege: Lane 3 (Backend/Daten)

### Was du wissen musst

Du bist fuer die Pipeline (`pipeline/`), die Ergebnisse (`results/`) und die Datenverarbeitung zustaendig. Du erweiterst gerade den Datenbestand auf ein gezieltes Sample (~10 pro Gruppe, ~74 Objekte). L1 (Frontend) wartet auf deine `quality_signals`-Daten. L2 (Methodik) hat die Spezifikation in `knowledge/verification-concept.md` §2.5 definiert. L2 hat ausserdem das HTR-Interchange-Format spezifiziert (`knowledge/htr-interchange-format.md`) — das wird nach quality_signals relevant. Der Operator prueft jede Datenaenderung visuell im Frontend, deshalb endet jeder deiner Schritte mit `build_viewer_data.py`.

### Deine Aufgaben (in dieser Reihenfolge)

**Schritt 1: JSON-Parsing haerten — pruefen ob erledigt**
- Falls schon implementiert: Bestaetigen (was wurde geaendert, welche Muster abgefangen).
- Falls nicht: Codeblock-Stripping, Escape-Sanitization, Retry (max 2), Logging.
- **Erfolgskriterium:** Kein unkontrollierter Abbruch bei JSON-Fehlern.

**Schritt 2: quality_signals.py implementieren**
- Spec: `knowledge/verification-concept.md` §2.5.
- 6 Signale: `page_length_anomaly`, `page_image_mismatch`, `duplicate_pages`, `language_mismatch`, `marker_density`, `group_text_density`.
- Output: `quality_signals`-Objekt in jeder Result-JSON + `needs_review` (boolean) + `needs_review_reasons` (string[]).
- L2-Befund beachten: `marker_density` ist fast immer 0 (2/57k Zeichen bei 16 Objekten) — trotzdem implementieren, aber bei needs_review-Schwellenwert beruecksichtigen.
- L2-Befund beachten: Bei 63% flagged war quality_signals zu aggressiv — Schwellenwerte konservativ waehlen.
- `group_text_density` erst ab 10 Objekte/Gruppe aktivieren.

**Schritt 3: Backfill + Build**
- `quality_signals` fuer ALLE bestehenden Objekte in `results/` nachberechnen (aktuell ~61).
- `build_viewer_data.py`: `quality_signals` + `needs_review` in `catalog.json` und `data/{collection}.json` durchreichen.
- Build ausfuehren + pruefen.

**Schritt 4: Gezieltes Sample erweitern (~74 Objekte)**
- Ziel: ~10 Objekte pro Gruppe (A-I), Verteilung ueber alle Sammlungen.
- `run_sample_batch.py` nutzen oder `transcribe.py --group` pro Gruppe.
- Nach Abschluss: Build + Report mit Verteilung.
- Noch NICHT den vollen Batch (2107) starten — erst nach Operator-Freigabe.

**Schritt 5: verify_gemini.py — Gemini-Seite der Verification-by-Vision (NACH L2-Spec)**
- Lies die Spec: `knowledge/verification-by-vision.md` (kommt von L2 Schritt 3).
- Implementiere `pipeline/verify_gemini.py`: Fuer jedes transkribierte Objekt:
  1. Lade Faksimile-Bilder (lokal aus Backup)
  2. Lade Transkriptionstext aus Result-JSON
  3. Sende Bild + Text an Gemini Vision → strukturierte Fehlerliste (JSON)
  4. Schreibe Gemini-Verifikationsergebnis in Result-JSON (`verification.gemini`)
- CLI: `verify_gemini.py o_szd.100 -c lebensdokumente` (Einzelobjekt), `verify_gemini.py --all`
- Die **Claude-Seite** wird NICHT ueber API gemacht, sondern durch einen Claude-Code-Agent/Subagent, der Bilder mit dem Read-Tool liest und direkt vergleicht. Die Forschungsleitstelle koordiniert das.
- `build_viewer_data.py` anpassen: `verification_status` (llm_verified/llm_error_suggestion/unverified) in catalog.json durchreichen
- Merge-Logik: Wenn sowohl Claude-Agent-Ergebnis als auch Gemini-Ergebnis vorliegen → Cross-Model-Agreement berechnen, Gesamt-Status setzen

**Schritt 6: Interchange-Format-Export (nach Schritt 3)**
- Lies die Spec: `knowledge/htr-interchange-format.md` (JSON Schema v0.1, Feld-Mapping §5).
- L2 empfiehlt Option B (separater Export, nicht Format-Migration).
- Implementiere `pipeline/export_interchange.py`: Liest Result-JSONs, erzeugt Interchange-JSONs.
- Testen: Mindestens 3 Objekte exportieren, Schema validieren.

### Reporting

Nach jedem abgeschlossenen Schritt: **Kurzmeldung an die Forschungsleitstelle** im Chat + Lane.md Status aktualisieren:

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
- Keinen vollen Batch-Run (2107 Objekte) ohne Operator-Freigabe.
- Keine Aenderungen am Prompt-System (`prompts/`) ohne Ruecksprache.

---

## Auftraege: Lane 1 (Frontend)

### Was du wissen musst

Du bist fuer das Frontend (`docs/`) zustaendig — Katalog, Viewer, Design-System. Du hast Schritt 1-4 abgeschlossen. L3 hat ~61 Objekte transkribiert und arbeitet am gezielten Sample (~74). Die Forschungsleitstelle fuehrt parallel Verification-by-Vision durch (Claude Code Agent liest Faksimiles). Dein naechster Fokus: quality_signals-UI testen (sobald L3 liefert) und Error-Markup rendern (sobald Verification-Ergebnisse vorliegen).

### Deine Aufgaben (in dieser Reihenfolge)

**Schritt 1: Classification-Pruefung — ERLEDIGT**

**Schritt 2: quality_signals-UI — CODE FERTIG, WARTET AUF L3-DATEN**
- Sobald L3 Schritt 3 (Backfill + Build) abschliesst → Reload + visueller Test mit ~61 Objekten.

**Schritt 3: Statistik-Dashboard — ERLEDIGT**

**Schritt 4: Diff-Ansicht UI-Prototyp — ERLEDIGT**

**Schritt 5: Verification-Status + Error-Markup rendern (NACH Forschungsleitstelle + L3)**
- Wenn L3 Verification-by-Vision implementiert hat, enthalten die Daten neue Felder:
  - `verification_status`: `llm_verified` | `llm_error_suggestion` | `unverified` | `human_verified`
  - Inline-Markup im Transkriptionstext: `«original→korrektur|konfidenz»`
- **Im Katalog:** Status-Badge neben Review-Badge (Gruen = verified, Orange = error_suggestion, Grau = unverified, Blau = human_verified). Sortierbar, filterbar.
- **Im Viewer:** Error-Markup farbig hervorheben:
  - `«...»`-Spans parsen und als `<span class="error-suggestion">` rendern
  - Tooltip zeigt Korrekturvorschlag + Konfidenz
  - Rot = high confidence error, Orange = medium
  - Click auf Error → akzeptiert Korrektur (aendert Text, entfernt Markup)
- **Verification-Panel:** Neben dem Qualitaets-Panel: Anzahl Fehler, Cross-Model-Agreement-Rate, Gesamtstatus.

**Schritt 6: Interchange-Format-Vorschau (NACH L3 Schritt 6)**
- Wenn L3 den Interchange-Export implementiert hat: "Export"-Button im Viewer fuer Interchange-JSON-Download.

### Reporting

Nach jedem abgeschlossenen Schritt: **Kurzmeldung an die Forschungsleitstelle** im Chat + Lane.md Status aktualisieren:

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

---

## Auftraege: Lane 2 (Methodik/Forschung)

### Was du wissen musst

Du bist fuer die methodische Fundierung zustaendig — Evaluationsdesign, Spezifikationen, Literaturarbeit. Deine Deliverables landen in `knowledge/`. Du schreibst keinen Code. L3 implementiert deine Spezifikationen. L1 setzt deine Frontend-Anforderungen um. Das knowledge/-Verzeichnis ist jetzt ein Obsidian Vault mit Frontmatter und Wikilinks — halte diese Konvention bei neuen Dateien ein (siehe `knowledge/index.md` fuer das Schema).

### Deine Aufgaben (in dieser Reihenfolge)

**Schritt 1: Pilot-Design — ERLEDIGT**

**Schritt 2: HTR-Interchange-Format — ERLEDIGT**

**Schritt 3: teiCrafter-Integrationskonzept — ERLEDIGT** (`knowledge/teiCrafter-integration.md`)

**Schritt 4: TEI-Zielstruktur — ERLEDIGT** (`knowledge/tei-target-structure.md`)

**Schritt 5: Verification-by-Vision spezifizieren (PRIORITAET)**
- Neues Verifikationsverfahren: Zwei VLMs (Claude Vision + Gemini Vision) vergleichen unabhaengig das Faksimile-Bild mit der Transkription und identifizieren Fehler.
- Spezifiziere in `knowledge/verification-by-vision.md`:
  - **Workflow — zwei Kanaele:**
    - **Kanal A (Claude Code Agent):** Ein Subagent liest das Faksimile-Bild via Read-Tool (Claude Codes eingebaute Vision), liest die Transkription, vergleicht Zeichen fuer Zeichen, schreibt Fehlerliste als JSON in die Result-Datei. Kein API-Call, keine Kosten. Wird von der Forschungsleitstelle koordiniert.
    - **Kanal B (Gemini API):** `verify_gemini.py` (L3) sendet Bild + Text an Gemini Vision API → strukturierte Fehlerliste. Kostet API-Calls.
    - **Merge:** Wenn beide Kanaele vorliegen → Cross-Model-Agreement. Beide finden denselben Fehler = hohe Konfidenz. Nur einer findet ihn = mittlere Konfidenz.
  - **Status-Kategorien:** `llm_verified` (keine Fehler), `llm_error_suggestion` (Fehler gefunden), `unverified` (noch nicht geprueft), `human_verified` (Operator bestaetigt).
  - **Error-Markup im Plaintext:** Format `«original→korrektur|konfidenz»` — maschinenlesbar, menschenlesbar, im Frontend farbig hervorhebbar. Abgrenzung zu bestehenden Markern ([?], [...], ~~...~~).
  - **Konfidenz-Modell:** Cross-Model-Agreement (beide finden denselben Fehler = stark), Einzelbefund (mittel), Agreement "kein Fehler" (stark). Pro-Fehler-Konfidenz als Zahl 0.0-1.0 (schwach, dokumentieren warum).
  - **Fehlertypen:** Zeichenfehler, Wortfehler, Auslassung, Hinzufuegung/Halluzination, Strukturfehler, Markup-Fehler — kompatibel mit annotation-protocol.md §7.
  - **Prompt/Instruktions-Design:** Was genau bekommt der Claude-Code-Agent? Was bekommt Gemini? Soll seitenweise oder abschnittsweise geprueft werden? Wie detailliert ist die Fehlerbeschreibung?
  - **JSON-Schema:** Wie sehen die Verifikations-Ergebnisse in der Result-JSON aus? Getrennte Abschnitte fuer `verification.claude` und `verification.gemini` + `verification.merged`.
  - **Kosten-/Aufwandsschaetzung:** Pro Seite 1 Gemini-API-Call (Claude-Seite ist kostenlos). Bei ~74 Objekten × ~3 Seiten = ~220 Calls. Claude-Code-Agent-Zeit: ~2-5 Min pro Objekt.
  - **Abgrenzung:** Verification-by-Vision ersetzt NICHT den manuellen Pilot (der misst CER). Es ergaenzt quality_signals um eine direkte Bild↔Text-Pruefung.

**Schritt 6: Pilot-Ergebnisse auswerten (WARTET AUF Operator)**
- Voraussetzung: Operator hat Pilot durchgefuehrt, Ergebnisse liegen vor.
- CER pro Seite und pro Gruppe berechnen (manuell oder mit L3-Script).
- Annotationsprotokoll ggf. anpassen.
- 30-Objekt-GT-Sample-Design finalisieren (informiert durch Pilot-CER).
- Ergebnis: `knowledge/pilot-results.md`

**Schritt 7: Prompt-Experiment-Design**
- Gepaarter 3-Varianten-Vergleich: V1 nur System, V2 System+Gruppe, V3 System+Gruppe+Kontext.
- 30 GT-Objekte × 3 Varianten = 90 API-Calls.
- Design als Abschnitt in `knowledge/verification-concept.md` §3 verfeinern.
- Konkrete Hypothesen formulieren, Auswertungsplan (gepaarter t-Test oder Wilcoxon auf CER).

### Reporting

Nach jedem abgeschlossenen Schritt: **Kurzmeldung an die Forschungsleitstelle** im Chat + Lane.md Status aktualisieren:

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
- Neue knowledge/-Dateien immer mit Obsidian-Frontmatter (siehe index.md fuer Schema).

---

## Auftraege: Forschungsleitstelle (Koordination + Verification-by-Vision)

### Eigene Aufgaben

**Schritt 1: Build ausloesen**
- `python pipeline/build_viewer_data.py` — Frontend auf ~61 Objekte aktualisieren.
- Operator fuehrt aus, Forschungsleitstelle prueft Ergebnis im Frontend.

**Schritt 2: Verification-by-Vision durchfuehren (PRIORITAET)**
- Systematisch Objekte verifizieren: Faksimile-Bild lesen (Read-Tool), Transkription lesen, Zeichen fuer Zeichen vergleichen.
- Prioritaet: Objekte mit hoher Fehlerwahrscheinlichkeit zuerst:
  1. Konvolute (Gruppe G) — o_szd.277 bereits geprueft: `llm_error_suggestion`
  2. Handschrift (Gruppe A) — o_szd.72 bereits geprueft: `llm_error_suggestion`
  3. Neue Batch-Ergebnisse (ungepruefte Lebensdokumente, Werke)
  4. Einfache Objekte (Typoskripte, Formulare) als Gegenprobe
- Pro Objekt: Subagent starten, Ergebnis als JSON dokumentieren.
- Ergebnisse in Result-JSONs schreiben (`verification.claude` Abschnitt).
- Bereits verifiziert: o_szd.161 (verified), o_szd.277 (error_suggestion), o_szd.72 (error_suggestion).

**Schritt 3: Verification-by-Vision Spec schreiben**
- Basierend auf den praktischen Erfahrungen: `knowledge/verification-by-vision.md`
- Formalisiert den Workflow, Error-Markup-Format, JSON-Schema, Konfidenz-Modell.
- Gibt L3 die Grundlage fuer `verify_gemini.py` und L1 fuer Error-Markup-Rendering.

**Schritt 4: Pilot vorbereiten**
- Die 5 Pilot-Seiten aus `knowledge/pilot-design.md` selbst via Vision pruefen.
- Ergebnis dem Operator vorlegen als Vorab-Einschaetzung (ersetzt nicht den manuellen Pilot).

### Koordinationsaufgaben (laufend)

- Lane.md aktuell halten (Status, Auftraege, Entscheidungen)
- L3-Report liegt vor (Session 10, Lane.md Status-Sektion aktualisiert)
- Plan.md synchron halten
- knowledge/index.md bei neuen Dateien aktualisieren

---

## Status der Lanes

### Lane 1 — Frontend
**Stand:** 2026-04-01, Schritt 1–4 abgeschlossen.

**Schritt 1 (Classification-Pruefung): ERLEDIGT** (Commit `e1b90e8`)
- Typ-Spalte zeigt TEI `classification` statt Prompt-Gruppe
- Gruppen-Filter: dynamische Dropdown, passt sich an Sammlung an

**Schritt 2 (quality_signals-UI): CODE FERTIG, WARTET AUF L3-DATEN**
- Review-Spalte, Qualitaets-Panel, Graceful Degradation
- Sobald L3 Schritt 3 (Backfill + Build) abschliesst → visueller Test

**Schritt 3 (Statistik-Dashboard): ERLEDIGT**
- Kompakte Leiste oberhalb der Katalog-Tabelle: Gesamtzahl + Chips pro Sammlung + Review-Count
- Aufklappbar: Verteilung nach Typ (Classification)
- Daten aus `state.catalog` berechnet, kein Extra-Request
- Reagiert auf Datenwachstum (funktioniert bei 17 wie bei 2107 Objekten)

**Schritt 4 (Diff-Ansicht UI-Prototyp): ERLEDIGT**
- Toggle-Button "Diff" in der Viewer-Nav-Bar
- Wort-basierter LCS-Diff-Algorithmus (rein clientseitig, O(mn))
- Side-by-Side-Layout: Spalte A (Gemini, rot) vs. Spalte B (Claude, blau)
- Agreement-Statistik pro Seite (% Uebereinstimmung, Anzahl gleich/abweichend)
- Farbkodierung: rot = nur A, blau = nur B, schwarz = Match
- Legende + "Prototyp"-Badge zur Kennzeichnung der Platzhalterdaten
- Hardcoded Placeholder: 3 Seiten eines fiktiven Briefvergleichs
- Diff-Modus und Edit-Modus sind gegenseitig exklusiv
- Diff wird bei Seitenwechsel automatisch aktualisiert
- Reset bei Objekt-Wechsel und bei Rueckkehr zum Katalog
- Help-Modal dokumentiert die Diff-Ansicht
- Responsive: Side-by-Side → Stacked bei < 900px
- **Naechster Schritt:** Anbindung an echte Cross-Model-Daten (wenn L3 zweiten Provider liefert)

**Edit-Modus UX-Verbesserung: ERLEDIGT**
- Expliziter "Speichern"-Button (+ Ctrl+S) mit Toast-Feedback "Gespeichert (localStorage)"
- Per-Page Undo: "Seite"-Button setzt einzelne Seite auf Original zurueck
- "Alles verwerfen" fuer alle Aenderungen am Objekt
- Status-Leiste: zeigt Anzahl bearbeiteter Seiten + Speicherort (localStorage)
- Toast-Benachrichtigungen fuer alle Aktionen (Speichern, Reset, JSON-Export)
- JSON-Export-Button weiterhin verfuegbar
- Help-Modal aktualisiert mit neuen Edit-Features

**Refactoring: ERLEDIGT**
- `resetDiffMode()` extrahiert (3x duplizierter Code → 1 Funktion)
- Textarea-XSS gefixt (`.value = text` statt Template-Interpolation)
- 3 Inline-Styles durch CSS-Klassen ersetzt
- 6 Diff-Farb-Variablen in `:root` extrahiert
- 5 unbenutzte CSS-Klassen entfernt
- Stats-Dashboard `display`-Bug gefixt

**Fruehere Arbeiten (Session 7–8):**
- Viewer: Zoom/Pan/Rotate, Metadaten-Bar, CSS-Cleanup, Korrespondenzen-Typ
- Details siehe Session-Berichte in Lane.md History

### Lane 2 — Methodik
**Stand:** 2026-04-01 (Session 8–12). Schritt 1–4 erledigt + 3 Bonus-Deliverables.
- [x] Schritt 1: pilot-design.md
- [x] Schritt 2: htr-interchange-format.md (JSON Schema v0.1)
- [x] Schritt 3: teiCrafter-integration.md (JSON-Import, 3 Mapping-Templates, Seitentrenner `|{n}|`)
- [x] Schritt 4: tei-target-structure.md (DTABf-Profil, NER-Strategie, XML-Beispiel)
- [x] Selbstkritische Review (Session 9): verification-concept.md aktualisiert
- [x] Bonus (Session 12): 3 teiCrafter-Mapping-Templates als Dateien extrahiert (correspondence-szd.md, manuscript-szd.md, print-szd.md → teiCrafter-Repo)
- [x] Bonus (Session 12): JSON-Schema als validierbare Datei (`schemas/htr-interchange-v0.1.json`)
- [x] Bonus (Session 12): DIA-XAI-Integrationskonzept (`knowledge/dia-xai-integration.md`) — EQUALIS-Mapping, Metriken-Export, UC3/UC4-Anbindung
- [ ] Schritt 5: Verification-by-Vision Spec — **naechster Schritt**
- [ ] Schritt 6: Pilot-Ergebnisse auswerten — WARTET AUF Operator
- [ ] Schritt 7: Prompt-Experiment-Design — WARTET AUF Pilot

### Forschungsleitstelle
**Stand:** 2026-04-01 (Session 8–10).
- [x] Lane-Modell aufgesetzt, Lane.md geschrieben
- [x] knowledge/ zu Obsidian Vault refactored (11→7 Dateien)
- [x] Verification-by-Vision getestet: o_szd.161 (verified), o_szd.277 (error_suggestion), o_szd.72 (error_suggestion)
- [ ] Build ausloesen (Frontend auf ~61 Objekte)
- [ ] Verification-by-Vision: weitere Objekte systematisch pruefen
- [ ] Verification-by-Vision Spec schreiben (`knowledge/verification-by-vision.md`)
- [ ] Pilot-Seiten vorab via Vision pruefen

### Lane 3 — Backend
**Stand:** 2026-04-01 (Session 8–10, L3-Report).

**Schritt 1 (JSON-Parsing haerten): ERLEDIGT** (Commit `ceb39dd`)
- `parse_api_response()`: 3-stufig (direkt → Codeblock-Strip → Escape-Fix) + Retry
- Absicherung gegen leere API-Antworten (`response.text is None`)
- Beobachtete Muster: `\j`-Escape (2×), Markdown-Codeblocks (2×), leere Antwort (1×, o_szd.219)

**Schritt 2 (quality_signals.py): ERLEDIGT** (Commit `ceb39dd`)
- Neues Modul `pipeline/quality_signals.py` (140 Zeilen), 6 Signale implementiert
- `needs_review` + `needs_review_reasons` als Top-Level-Aggregation
- Integriert in `transcribe.py` (auto-compute) + `build_viewer_data.py` (catalog.json propagiert `needsReview`)
- **L1 kann quality_signals-UI jetzt mit echten Daten aktivieren**

**Schritt 3 (Backfill + Build): ERLEDIGT** (Commit `ceb39dd`)
- Alle Ergebnis-JSONs mit quality_signals angereichert
- `catalog.json` enthaelt `needsReview` + `needsReviewReasons`

**Schritt 4 (Gezieltes Sample): IN ARBEIT**
- `run_sample_batch.py`: fuellt jede Gruppe auf 10 auf (E auf max 5)
- Aktueller Stand: 63/85 Objekte (Formular 10, Handschrift 10, Kurztext 10, Typoskript 10, Korrekturfahne 9, Konvolut 6, Tabellarisch 5). Korrespondenz + Zeitungsausschnitt noch ausstehend (Batch laeuft).
- Verteilung: 46 Lebensdokumente, 14 Werke, 2 Aufsatzablage, 1 Korrespondenzen
- Crash-Fix: `response.text is None` bei o_szd.219 (leere Gemini-Antwort) — gefixt, Batch fortgesetzt
- JSON-Fixes im Batch: 2× Codeblock-Strip, 1× \j-Escape — alle automatisch repariert

**Schritt 5 (Interchange-Export): AUSSTEHEND**

**Offene Fragen beantwortet:**
- Objekte mit Bildern: 2107/2107 (100%), kein fehlendes Material
- Gruppen ≥10 Objekte: 8/9 (alle ausser E:Tabellarisch mit 5)
- Weitere JSON-Muster: Codeblocks + `\j` + leere Antworten. Alle abgefangen.
- Kostenabschaetzung voller Batch: ~$29 API, ~10h Laufzeit (2s Delay)

**Neuer Vorschlag (von Forschungsleitstelle):**
- Postkarten-Bildbeschreibung: Bei Ansichtspostkarten Bildseite identifizieren, mit Gemini beschreiben (nicht transkribieren), in eigener Struktur ablegen. Betrifft ~56 Ansichtspostkarten + 94 Postkarten. Braucht Prompt-Design (L2) + Pipeline-Erweiterung (L3) + UI (L1).

---

## Entscheidungslog

| Datum | Entscheidung | Begruendung | Betrifft |
|---|---|---|---|
| 2026-04-01 | Pilot vor vollem GT-Sample | CER unbekannt — Sample-Design ohne Pilot ist blind | Alle |
| 2026-04-01 | quality_signals sofort | Kostet nichts, braucht kein GT, bietet Triage fuer Batch | L3, L1 |
| 2026-04-01 | Cross-Model: Agreement-First | Unabhaengige Doppeltranskription methodisch sauberer | L3 |
| 2026-04-01 | Claude Sonnet als zweites Modell | Max. Diversitaet zu Gemini, starke Baseline, moderate Kosten | L3 |
| 2026-04-01 | teiCrafter-Integration via Interchange-Format | Kein eigener TEI-Konverter — teiCrafter hat LLM-Annotation + Validierung | L2, L3 |
| 2026-04-01 | Verification-by-Vision (Claude Code Agent + Gemini API) | Claude Code liest Bilder direkt (kostenlos, eingebaute Vision), Gemini via API. Cross-Model-Agreement aus zwei unabhaengigen Pruefungen. | L2, L3, L1 |
| 2026-04-01 | Error-Markup inline im Plaintext | Reviewer muss Fehler sofort sehen. Format `«orig→korr|conf»` maschinenlesbar + menschenlesbar | L2, L1 |
