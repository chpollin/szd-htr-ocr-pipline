# Lane-Koordination: SZD-HTR-Projekt

Letzte Aktualisierung: 2026-04-01 (Session 8, Forschungsleitstelle v0.4, knowledge/ refactored)

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

L2: verification-by-vision Spec ──→ L3: verify.py (Claude+Gemini Vision)
  ──→ L1: Error-Markup-Rendering + Status-Badges
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
- `quality_signals` fuer ALLE bestehenden Objekte in `results/` nachberechnen (inzwischen ~30+).
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

Du bist fuer das Frontend (`docs/`) zustaendig — Katalog, Viewer, Design-System. L3 erweitert gerade den Datenbestand auf ~74 Objekte und implementiert danach `quality_signals`. Sobald L3 `build_viewer_data.py` ausfuehrt, enthalten die JSONs neue Felder. Ausserdem wird es spaeter einen Interchange-Format-Export geben (L3 Schritt 5) — das betrifft dich erst bei der Diff-Ansicht.

### Deine Aufgaben (in dieser Reihenfolge)

**Schritt 1: Classification-Pruefung — ERLEDIGT** (Commit `e1b90e8`)

**Schritt 2: quality_signals-UI — CODE FERTIG, WARTET AUF L3-DATEN**
- Sobald L3 Schritt 3 (Backfill + Build) abschliesst → Reload + visueller Test mit ~30+ Objekten.

**Schritt 3: Statistik-Dashboard (JETZT MACHBAR)**
- L3 hat inzwischen ~30 Objekte transkribiert. Bitte den Operator, `python pipeline/build_viewer_data.py` auszufuehren, damit du mit aktuellen Daten arbeiten kannst.
- Baue eine Statistik-Uebersicht oberhalb der Katalog-Tabelle:
  - Gesamtzahl transkribierter Objekte
  - Verteilung nach Sammlung (Balken oder Zahlen)
  - Verteilung nach Gruppe (A-I)
  - Wenn quality_signals vorhanden: Anteil needs_review
- Die Daten kommen aus `catalog.json` — zaehle dort die Eintraege.
- Halte es kompakt (1-2 Zeilen, aufklappbar fuer Details).
- Design: SZD-Farbsystem, konsistent mit bestehendem Katalog.

**Schritt 4: Diff-Ansicht — UI-Konzept skizzieren (JETZT MACHBAR)**
- Fuer Cross-Model-Verification (spaeter): Zwei Transkriptionen desselben Objekts vergleichen.
- L2 hat die Anforderungen in `knowledge/verification-concept.md` §5 skizziert.
- Du brauchst noch keine echten Daten — entwirf das UI-Konzept:
  - Wo im Viewer? (Tab, Toggle, Split-View?)
  - Wie zeigt man Differenzen? (Inline-Diff mit Farbmarkierung? Side-by-Side?)
  - Wie waehlt man den Provider? (Dropdown, Toggle-Button?)
  - Wie zeigt man Agreement/Disagreement-Statistik pro Seite?
- Implementiere einen Prototyp mit Platzhalter-Daten (hardcoded, nicht von L3 abhaengig).
- Ergebnis: Funktionierender UI-Prototyp, den der Operator visuell pruefen kann.

**Schritt 5: Verification-Status + Error-Markup rendern (NACH L3 verify.py)**
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

**Schritt 2: HTR-Interchange-Format — ERLEDIGT** (`knowledge/htr-interchange-format.md`, JSON Schema v0.1)

**Schritt 3: Verification-by-Vision spezifizieren (NEU — PRIORITAET)**
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

**Schritt 4: teiCrafter-Integrationskonzept (NEU)**
- Lies das teiCrafter-Repo: `C:\Users\Chrisi\Documents\GitHub\ResearchTools\teiCrafter`
- Konkretisiere, wie der JSON-Import in teiCrafter Step 1 aussehen soll:
  - Welche Felder braucht Step 2 (Mapping) minimal? (sourceType, language, epoch, project)
  - Wie werden mehrseitige Dokumente behandelt? (Seitentrenner → `<pb/>`)
  - Welche teiCrafter-Mapping-Rules brauchen wir fuer SZD-Dokumente? (DTABf-Profil, Zweig-spezifische Entitaeten)
- Entwurf fuer SZD-spezifische Mapping-Rules als Template (analog zu den bestehenden Demo-Mappings in teiCrafter `docs/data/demo/mappings/`)
- Ergebnis: Erweitere `knowledge/htr-interchange-format.md` §4 oder erstelle `knowledge/teicroafter-integration.md`

**Schritt 4: TEI-Zielstruktur definieren (NEU)**
- Wie soll das fertige TEI-XML fuer ein SZD-Objekt aussehen?
- Welches TEI-Profil? (DTABf? Eigenes SZD-Profil? Kompatibilitaet mit bestehendem SZD-Datenmodell auf GAMS?)
- Welche Named Entities sind relevant? (Personen, Orte, Werktitel, Institutionen — im Zweig-Kontext)
- Wie wird die diplomatische Transkription in TEI abgebildet? (`<del>`, `<add>`, `<unclear>`, `<gap>`)
- Beziehe dich auf das bestehende SZD-Datenmodell: https://stefanzweig.digital/
- Ergebnis: `knowledge/tei-target-structure.md`

**Schritt 5: Pilot-Ergebnisse auswerten (WARTET AUF Operator)**
- Voraussetzung: Operator hat Pilot durchgefuehrt, Ergebnisse liegen vor.
- CER pro Seite und pro Gruppe berechnen (manuell oder mit L3-Script).
- Annotationsprotokoll ggf. anpassen.
- 30-Objekt-GT-Sample-Design finalisieren (informiert durch Pilot-CER).
- Ergebnis: `knowledge/pilot-results.md`

**Schritt 6: Prompt-Experiment-Design**
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

**Fruehere Arbeiten (Session 7–8):**
- Viewer: Zoom/Pan/Rotate, Metadaten-Bar, CSS-Cleanup, Korrespondenzen-Typ
- Details siehe Session-Berichte in Lane.md History

### Lane 2 — Methodik
**Stand:** 2026-04-01 (Session 8–10).
- [x] Schritt 1: pilot-design.md finalisiert — 5 Seiten, 5 Gruppen, Eskalationsschwellen, Pruefprotokoll.
- [x] Schritt 2: htr-interchange-format.md geschrieben — JSON Schema v0.1, teiCrafter-Mapping, Abgrenzung ALTO/PAGE/hOCR.
- [x] Selbstkritische Review (Session 9): verification-concept.md aktualisiert (16 Objekte, Gruppe G, quality_signals-Einordnung).
- [x] Schritt 3 (Session 10): `knowledge/teiCrafter-integration.md` — JSON-Import-Spec, 3 SZD-Mapping-Templates, Sprach/Epochen-Erweiterung, DTABf-Schema-Erweiterungen (gap/del/add/stamp/table/cb), Seitentrenner `|{n}|`.
- [x] Schritt 4 (Session 10): `knowledge/tei-target-structure.md` — DTABf-Profil, Markup→TEI-Mapping-Tabelle, NER-Strategie (Phase 1: Personen/Orte/Daten), XML-Beispiel (o_szd.1079), separate Dateien pro Objekt empfohlen.
- [ ] Schritt 5: Pilot-Ergebnisse auswerten — WARTET AUF Operator-Durchfuehrung.
- [ ] Schritt 6: Prompt-Experiment-Design — WARTET AUF Pilot-Ergebnisse.

### Lane 3 — Backend
**Stand:** 2026-04-01 (aktualisiert durch Forschungsleitstelle). ~61 Objekte transkribiert (42 Lebensdokumente, 11 Werke, 1 Aufsatzablage + 7 Test). `run_sample_batch.py` erstellt. `transcribe.py` modifiziert. Gezieltes Sample in Arbeit. quality_signals + Interchange-Export noch nicht implementiert. **Immer noch kein strukturierter Report — bei naechster Session einfordern.**

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
