---
title: "SZD-HTR Research Journal"
aliases: ["Journal", "Session-Log"]
created: 2026-03-30
updated: 2026-04-01
type: journal
tags: [szd-htr, session-log]
status: active
related:
  - "[[data-overview]]"
  - "[[verification-concept]]"
  - "[[annotation-protocol]]"
  - "[[pilot-design]]"
---

# SZD-HTR — Research Journal

Chronologisches Log aller Arbeitssessions, Erkenntnisse und Entscheidungen.

---

## 2026-03-30 — Session 1: Projektplanung

### Was wurde gemacht
- CLAUDE.md gelesen und Projektanforderungen verstanden
- Implementierungsplan erstellt (→ [Plan.md](../Plan.md))
- Knowledge-Ordner als Research-Vault angelegt

### Entscheidungen
- **Gemini 3.1 Flash-Lite** als Transkriptions-Provider
  - Guenstig ($0.25/1M input), schnell, 1M-Token-Kontext, multimodal
  - Ermoeglicht Kosten-/Qualitaetsvergleich zwischen Providern
- **Kategoriale Konfidenz** (sicher/pruefenswert/problematisch) statt numerischer Scores
  - Erfahrung aus coOCR HTR: LLMs koennen Qualitaet nicht zuverlaessig numerisch einschaetzen

### Offene Fragen
- [x] Wie gut erkennt Gemini Kurrentschrift? → high confidence bei Zweigs Handschrift (Session 2)
- [ ] Optimale Bildgroesse fuer API-Calls? Originale 4912x7360 (~1.4MB)
- [ ] Lizenz klaeren: MIT fuer Code, CC-BY fuer Daten?

---

## 2026-03-30 — Session 2: Pipeline aufgebaut, erste Tests, alle Sammlungen analysiert

### TEI-Metadaten heruntergeladen und analysiert

Vier TEI-XML-Dateien von stefanzweig.digital heruntergeladen. Detaillierte Analyse: [[data-overview]].

| Sammlung | TEI-Eintraege | mit PID | Groesse |
|---|---|---|---|
| Lebensdokumente | 143 | 120 | 666 KB |
| Werke | 352 | 162 | 1.6 MB |
| Aufsatzablage | 624 | 624 | 2.5 MB |
| Korrespondenzen | 723 | 0 (TEI) | 1.5 MB |

Backup-Daten (lokal): 1186 Korrespondenzen, 625 Aufsaetze, 169 Faksimiles. **Gesamtbestand: ~2107 digitalisierte Objekte.**

### Dreischichtiges Prompt-System entwickelt

System-Prompt (global) → Gruppen-Prompt (A-E) → Objekt-Kontext (aus TEI). Prompts unter `pipeline/prompts/`.

### Erste Transkriptionstests

| Objekt | Gruppe | Sprache | Confidence | Beobachtung |
|---|---|---|---|---|
| Theaterkarte Jeremias (o:szd.161) | D | DE | high | Gedruckter + handschriftl. Text korrekt |
| Certified Copy of Marriage (o:szd.160) | C | EN | high | Formularfelder korrekt |
| Verlagsvertrag Grasset (o:szd.78) | B | FR | high | Franz. Vertragstext, Durchstreichungen erkannt |
| Tagebuch 1918 (o:szd.72) | A | DE | high | Zweigs Handschrift fluessig gelesen |

**Kernbefund:** Gemini 3.1 Flash Lite liefert auf allen 4 Gruppen (A-D) high confidence. Zweigs Handschrift wird fluessig transkribiert.

### Neue Prompt-Gruppen aus Sammlungsanalyse

| Gruppe | Quelle | Objekte | Besonderheit |
|---|---|---|---|
| F: Korrekturfahne | Werke + Aufsatz | ~55 | Gedruckter Text + handschriftliche Korrekturen |
| G: Konvolut | Werke | 24 | Gemischte Materialien |
| H: Zeitungsausschnitt | Aufsatzablage | 312 | Gedruckt, oft Fraktur |
| I: Korrespondenz | Korrespondenzen | ~1186 | Handschriftliche Briefe |

### Erkenntnisse

1. **GAMS-URLs funktionieren als direkte Bildquellen** — kein Download/Hosting noetig.
2. **Korrespondenzen-TEI** hat nur Verzeichnis-Charakter. Metadaten aus Backup-metadata.json.
3. **Erwin Rieger** zweithaeufigste Hand in Aufsatzablage (225x) — eigene Handschrift.
4. **Zeitungsausschnitte (312)** brauchen eigenen Fraktur-Prompt.
5. **Lotte Zweig** zweithaeufigste Hand in Werken (83x).

---

## 2026-03-30 — Session 3: Phase 2 abgeschlossen, alle Sammlungen integriert

### Neue Gruppen-Prompts

- `group_f_korrekturfahne.md` — Gedruckter Text + Korrekturen
- `group_h_zeitungsausschnitt.md` — Zeitungsdruck, Fraktur-Hinweise
- `group_i_korrespondenz.md` — Briefstruktur, Postkarten-Doppelseiten

Gruppe G (Konvolut) bewusst aufgeschoben — zu wenige Objekte, zu heterogen.

### Pipeline auf Multi-Collection erweitert

`test_single.py` refactored mit `COLLECTIONS`-Dict, Enriched JSON-Output, `--list`. Neue Module: `tei_context.py`, `build_viewer_data.py`.

### Drei neue Test-Objekte

| Objekt | Sammlung | Gruppe | Confidence | Beobachtung |
|---|---|---|---|---|
| Der Bildner (o:szd.287) | Werke | F | high | Rodin-Gedicht fehlerfrei, Stempel erkannt |
| Aus der Werkstatt (o:szd.2215) | Aufsatzablage | H | high | Antiqua (kein Fraktur-Test) |
| Brief an Fleischer (o:szd.1079) | Korrespondenzen | I | high | Jugendhandschrift (1901) |

**Gesamtstand: 7/7 high confidence, alle 4 Sammlungen abgedeckt.**

### Erkenntnisse

1. Gemini meistert alle Dokumenttypen — kein einziges Objekt unter high.
2. Fraktur noch nicht getestet (Antiqua-Zeitungsausschnitt).
3. Enriched JSON-Format vereinfacht den Viewer-Build.

---

## 2026-03-31 — Session 4: Cleanup und Refactoring vor Phase 3

### Kernarbeiten

- `pipeline/config.py` — Gemeinsame Konfiguration (Pfade, Collections, Groups, API-Keys via .env)
- `requirements.txt` — Formale Dependencies
- Auto-Kontext aus TEI: `resolve_context()` ersetzt ~100 Zeilen manuelle Context-Strings
- Bug-Fix `resolve_group()`: Formular-Checks vor generischen Typoskript-Check

### Erkenntnisse

1. **Auto-Kontext funktioniert zuverlaessig**: 6/7 direkt aus TEI, 1/7 ueber Backup-Fallback.
2. **resolve_group() braucht semantische Ordnung**: Klassifikation vor Objekttyp pruefen.
3. **Gemeinsame config.py eliminiert Drift** zwischen Scripts.

---

## 2026-03-31 — Session 5: Phase 3 abgeschlossen, Batch-CLI und erster Lauf

### pipeline/transcribe.py

CLI-Modi: Einzelobjekt, Sammlung, `--all`, `--group`, `--limit`, `--force`, `--delay`, `--max-images`, `--dry-run`.

### Object Discovery

Primaerquelle: Backup-Verzeichnisse (TEI lueckenhaft bei PIDs).

| Sammlung | Backup-Objekte | PIDs in TEI |
|---|---|---|
| Lebensdokumente | 127 | 121 (85%) |
| Werke | 169 | 163 (46%) |
| Aufsatzablage | 625 | 625 (100%) |
| Korrespondenzen | 1186 | 0 |
| **Gesamt** | **2107** | |

### Erster Batch-Lauf: 5 Lebensdokumente

o_szd.100-104, alle Typoskript, alle high confidence. Skip-Logik funktioniert. **Gesamtstand: 12 Objekte.**

### Erkenntnisse

1. **Backup-Dirs zuverlaessiger als TEI** fuer Object Discovery.
2. **2s Delay reicht** fuer Rate-Limiting.
3. **Windows-Encoding (cp1252)**: Unicode-Zeichen verursachen Fehler → ASCII-Alternativen.

---

## 2026-04-01 — Session 6: Frontend-Refactoring, Verifikationskonzept

### CLAUDE.md ueberarbeitet

Veraltete Objektzahlen, Modell-Widerspruch (Claude als primaer, nur Gemini implementiert), Phasen inkonsistent. Komplett neu geschrieben, Plan.md als einzige Wahrheitsquelle.

### Frontend: Zwei Dateien → Single-Page-App

Vorher: `index.html` (Scroll-Dump) + `viewer.html` (Side-by-Side). Nachher:

| Datei | Funktion |
|---|---|
| `docs/index.html` | HTML-Skelett, Help-Modal |
| `docs/app.css` | SZD-Design-System (Burgundy/Gold, Source Serif/Sans) |
| `docs/app.js` | Routing, Katalog, Viewer, Edit, Export |

**Daten-Split:** `catalog.json` (~6 KB Metadaten) + `data/{collection}.json` (on-demand). Features: Sortierbare Tabelle, Hash-Routing (`#view/{id}/{page}`), Side-by-Side Viewer, GAMS-Thumbnails, Inline-Edit, JSON-Export.

**Design-System:** Burgundy `#631a34`, Gold `#C2A360`, Cream `#FAF8F3`, Source Serif 4, Source Sans 3, JetBrains Mono.

### Verifikationskonzept: 3 Ebenen

| Ebene | Signal | Staerke |
|---|---|---|
| 1 | Unsicherheits-Marker (`[?]`, `[...]`) | Stark |
| 2 | VLM-Selbsteinschaetzung | Schwach |
| 3 | Textstatistik (Zeichenzahl, Leerseiten) | Mittel |

Befund: 12/12 "high confidence", fast keine Marker. VLMs ueberschaetzen systematisch ihre Leistung → staerkere Metriken noetig.

### Lane 1 Bericht

**Katalog:** Typ-Spalte zeigt TEI `classification` (Verlagsvertraege, Tagebuecher) statt Prompt-Gruppe. Tooltip zeigt `objecttyp`.

**quality_signals-UI vorbereitet:** Review-Spalte (Burgundy/Gruen-Badge, sortierbar, Toggle-Filter), Qualitaets-Panel im Viewer, Seiten-Anomalie-Marker. Graceful Degradation wenn Felder fehlen.

**Neue Felder in catalog.json:** `titleClean`, `signature`, `classification`, `objecttyp`, `thumbnail`, `pageCount`, `verification`.

**Interface-Vertrag fuer L3:** `obj.needsReview` (boolean), `obj.needsReviewReasons` (string[]), `obj.quality_signals` (ganzes Objekt), `obj.quality_signals.page_length_anomalies` (int[]).

**Befunde fuer L2:** 12/16 Objekte haben 0 Marker. Marker-Dichte ist kein negatives, nur positives Signal. TEI-Klassifikation nutzbar fuer Sampling-Strategie.

Geloeschte Dateien: `docs/viewer.html`, `docs/data.json`.

---

## 2026-04-01 — Session 7: Forschungsleitstelle, 3 Lanes, Gruppenabdeckung 9/9

### Lane-System initialisiert

Drei parallele Claude-Code-Agents: L1 (Frontend), L2 (Methodik), L3 (Backend). Koordination ueber [Lane.md](../Lane.md).

### L3: Gruppenabdeckung vervollstaendigt

| Objekt | Sammlung | Gruppe | Confidence | Beobachtung |
|---|---|---|---|---|
| o_szd.143 (Kontorbuch) | Lebensdokumente | E | high | Pipe-getrennte Spalten |
| o_szd.174 (Adressbuch) | Lebensdokumente | E | high | Tabellarisch |
| o_szd.2232 (Fraktur 1901) | Aufsatzablage | H | high | **Fraktur funktioniert** |
| o_szd.277 (Der Fall von Byzanz) | Werke | G | medium | Erstes non-high — heterogene Korrekturen |

**Alle 9 Gruppen A-I haben mindestens ein Testobjekt. Gesamtstand: 16 Objekte (15x high, 1x medium).**

### L2: Methodische Deliverables

- [[verification-concept]] v2 (5 Abschnitte, Literatur-Review mit 6 Papers)
- [[annotation-protocol]] (8 Abschnitte, Normalisierung, Beispiele)
- [[pilot-design]] (5 Seiten, Pruefprotokoll, Eskalationsschwellen)

### L1: quality_signals-UI vorbereitet

Review-Spalte, Qualitaets-Panel, Seiten-Anomalie-Marker im Code, wartet auf L3-Daten.

### Entscheidungen

- Pilot vor vollem GT-Sample (CER unbekannt)
- quality_signals sofort implementieren (kostenlos, kein GT noetig)
- Cross-Model: Agreement-First-Strategie
- Claude Sonnet als zweites Modell

---

## 2026-04-01 — Session 8: Interchange-Format, Selbstkritik, Korrekturen

### L2: Deliverables abgeschlossen

- **htr-interchange-format.md** geschrieben — JSON Schema v0.1, teiCrafter-Mapping, SZD-HTR-Mapping, Abgrenzung ALTO/PAGE/hOCR, Beispiel basierend auf o_szd.100.
- **pilot-design.md** geprueft und bestaetigt — keine Aenderungen noetig.
- Schritt 1 + 2 der L2-Auftraege erledigt. Schritt 3+4 blockiert (warten auf Pilot-Durchfuehrung durch Operator).

### Selbstkritische Review aller knowledge-Dokumente

Systematische Pruefung aller 6 knowledge-Dateien + Lane.md auf Konsistenz, Korrektheit und empirische Fundierung.

**Korrekturen durchgefuehrt:**
- **verification-concept.md**: Objektzahlen 12→16, Konfidenz "alle high" → "15 high + 1 medium", Gruppe G ins Sample-Design aufgenommen (31 statt 30), Anachronismus direkt in Fehlertaxonomie-Tabelle §1.5, empirische Einordnung der quality_signals ergaenzt (10/16 flagged = zu aggressiv)
- **journal.md**: Session 8 nachgetragen

**Kritische Befunde:**
1. **Marker-Problem bestaetigt:** 57.000 Zeichen, 2 Marker. marker_density ist kein funktionierendes Signal.
2. **quality_signals zu aggressiv:** 10/16 (63%) als needs_review geflaggt — hauptsaechlich page_image_mismatch bei normalen Leerseiten.
3. **Gruppen-Prompts:** Strukturelle Guidance (Briefformat) wirkt. Vorsichts-Guidance (Marker setzen bei Kurrent-Ambiguitaeten) wird ignoriert.
4. **Interchange-Format moeglicherweise verfrueeht:** Sinnvoll als Analyse, aber Schema vor CER-Kenntnis wenig dringend.
5. **30-Objekt-Sample:** Konkretes Design ist Platzhalter — haengt komplett vom Pilot ab.

### Entscheidungen

- Pilot bleibt der kritische naechste Schritt — alles andere ist Theorie
- quality_signals-Schwellenwerte muessen nach Pilot kalibriert werden (page_image_mismatch braucht Leerseiten-Toleranz)
- Prompt-Experiment ist wichtiger als gedacht (Evidenz fuer Wirkungslosigkeit der Vorsichts-Prompts)

---

## Offene Fragen (Stand 2026-04-01)

- [ ] Optimale Bildgroesse: Resizing vor API-Call?
- [ ] Lizenz klaeren: MIT fuer Code, CC-BY fuer Daten?
- [ ] Korrektur-Markup: Erweitertes Markup noetig?
- [x] Fraktur-Erkennung: o_szd.2232 high confidence (Session 7)
- [x] Batch-Modus: transcribe.py (Session 5)
- [x] Konvolut: Gruppe G erstellt, o_szd.277 medium (Session 7)
- [ ] Provider-Vergleich: Claude Vision, GPT-4o (Phase 4)
- [ ] Alle 2107 Objekte transkribieren (nach JSON-Parsing-Fix)
- [ ] quality_signals kalibrieren: page_image_mismatch zu aggressiv (Session 8)
- [ ] Prompt-Wirksamkeit: Vorsichts-Guidance ignoriert — Experiment noetig (Session 8)
- [ ] o_szd.143 nur 20 Zeichen auf 3 Seiten — Pipeline-Problem oder korrektes Ergebnis? (Session 8)
