---
title: "Statistik-Dashboard"
type: spec
status: implemented
created: 2026-04-02
updated: 2026-04-12
related:
  - "[[verification-concept]]"
  - "[[data-overview]]"
tags:
  - visualization
  - quality
---

# Statistik-Dashboard

Dedizierte Statistik-Seite im SZD-HTR Viewer (`#stats`), die aggregierte Qualitaetsmetriken als narrative Informationsvisualisierungen darstellt. Ziel: OCR-Qualitaet akademisch argumentierbar machen.

## 1 Motivation

Die bestehende Inline-Statistik im Katalog zeigt Zahlen als Text-Chips. Fuer eine wissenschaftliche Qualitaetsbewertung der Pipeline reicht das nicht: Verteilungen, Ausreisser und Zusammenhaenge zwischen Metriken sind erst durch Visualisierungen erkennbar. Mehrere aktuelle Arbeiten argumentieren, dass Standard-OCR-Metriken (CER/WER) fuer historische Dokumente unzureichend sind (Beyene & Dancy 2026; Levchenko 2025) — proxy-basierte Quality Signals und deren Verteilung liefern bessere Einsichten.

## 2 Expertenperspektive

Das Dashboard folgt der Perspektive **Computational Philology / Digital Scholarly Editing**, kombiniert mit Prinzipien der Informationsvisualisierung (Yuan et al. 2024). Primaere Nutzer sind DH-Forscher und Archivare, nicht ML-Engineers. Metriken muessen philologisch interpretierbar sein.

## 3 Datenquellen

Alle Visualisierungen werden client-seitig aus `catalog.json` aggregiert (`computeStatsData()`, Single-Pass ueber alle Objekte). Kein Backend-Umbau noetig. Jedes der ~2080 Objekte traegt quality_signals v1.5 (7 Signale + `page.type`, DWR entfernt), Review-Status, optional Modellkonsensus-Daten, und TEI-Metadaten. Archiv-Gesamtzahlen als `COLLECTION_TOTALS`-Konstante in `app.js`.

## 4 Narrative Struktur: 5 Sektionen

Das Dashboard erzaehlt eine Qualitaetsnarrative in 5 Schritten — jede Sektion hat einen Header mit Erklaerung und ein 2-Spalten-Grid fuer Charts.

### Sektion 1: Abdeckung

Zeigt Umfang und Fortschritt der Transkription.

- **Fortschritt pro Sammlung** (Stacked Horizontal Bar): 4 Sammlungen × (transkribiert / ausstehend). Archiv-Gesamtzahlen aus `COLLECTION_TOTALS` (2107 Objekte). Klick navigiert zu `#catalog?collection=X`.
- **Seitenkomposition** (Stacked Vertical Bar): Pro Sammlung aufgeschluesselt nach Inhalt / Leer / Farbskala.

### Sektion 2: Mehrstufige Verifikation

Zeigt die 3-stufige Verifikationsarchitektur (automatisch → Cross-Model → Expert).

- **Review-Status** (Donut): 5 Segmente — GT Verifiziert, Expert Geprueft, Agent Verifiziert, LLM OK, Needs Review. Nur Segmente mit Wert > 0 angezeigt. Klick auf "Needs Review" navigiert zu gefiltertem Katalog.
- **VLM-Konfidenz** (Donut): High / Medium / Low. Explizit als "schwaches Signal" deklariert — Modelle ueberschaetzen ihre Leistung.

### Sektion 3: Textcharakteristik

Zeichen pro Inhaltsseite nach Dokumenttyp (horizontaler Balken). Zeigt die strukturelle Vielfalt des Nachlasses: Registerblaetter (Gruppe A, 73% der Handschrift) haben ~50 Zeichen/Seite, Zeitungsausschnitte ~4800. Quelle: `quality_signals.py` (chars_per_page) → `catalog.json` (verification.avgCharsPerPage).

### Sektion 4: Signalanalyse

Heatmap: Welche Dokumenttypen loesen welche Quality Signals aus? Anteil Objekte pro Gruppe in Prozent. Quelle: `quality_signals.py` (needs_review_reasons) → `catalog.json` (needsReviewReasons).

### Entfernte Sektionen (Session 22)

Folgende Sektionen wurden entfernt, weil sie nicht gegroundet oder transient waren:

- **Abdeckung/Fortschritt** — Produktions-Tracking, wird bei 100% sinnlos
- **Seitenkomposition** — Inhalt/Leer/Farbskala als Chart, Information steht im Katalog
- **DWR-Histogram** — DWR in v1.5 entfernt (rho=0.05, F1=0.20, mass Prosadichte, nicht Qualitaet)
- **VLM-Konfidenz-Donut** — High/Medium/Low diskriminiert nicht zwischen fehlerfreien und fehlerhaften Transkriptionen
- **Modellkonsensus** — CER zwischen Modellen misst Agreement, nicht Korrektheit; nur 29/2080 Objekte hatten Daten

## 5 Metrik-Definitionen

| Metrik | Definition | Schwelle |
|---|---|---|
| Seitenduplikate | Jaccard-Aehnlichkeit > 0.9 bei > 50 Zeichen | = duplicate_pages (informativ) |
| Sprachkonsistenz | TEI-Sprache vs. erkannte Sprache | Mismatch = language_mismatch |
| Seitenlaengen-Anomalie | Inhaltsseite < 10% des Medians | = page_length_anomaly |
| Bild-Text-Mismatch | Seitenzahl ≠ Bildzahl oder > 75% leer | = page_image_mismatch |
| CER (Character Error Rate) | edit_distance(A, B) / max(len(A), len(B)) | < 3% = verifiziert |

## 6 Design-Entscheidungen

- **Chart.js 4.x** (vendored in `docs/lib/`, ~200KB): Lightweight, ausreichend fuer Bar/Donut. D3.js waere Overkill.
- **Client-seitige Aggregation**: Kein Pipeline-Umbau, `catalog.json` traegt alle noetigsten Felder. `computeStatsData()` als Single-Pass.
- **Donut-Charts mit eigener `donutOptions()`**: Getrennt von `chartOptions()`, da Doughnuts keine Achsen haben.
- **Drill-Down via Hash-Navigation**: Chart-Klick → `#catalog?collection=X` oder `?review_status=Y`.
- **Heatmap als HTML-Tabelle**: Praeziser als Canvas fuer tabellarische Daten, besser zugaenglich. In scrollbarem Container fuer schmale Viewports.
- **Kein CER-Dashboard**: Nur 4.5% der Objekte haben CER-Daten — ein CER-zentriertes Dashboard waere eine Fassade. CER-Verteilung konditional im Konsensus-Block.
- **Narrative Sektionen statt flaches Grid**: Jede Sektion hat Header + Beschreibung, die den Argumentationsschritt erklaert. Sektionen stacken vertikal, Cards 2-spaltig innerhalb.

## 7 Literatur

- Beyene, F.S. & Dancy, C.L. (2026). A Survey of OCR Evaluation Methods and Metrics and the Invisibility of Historical Documents. *FAccT 2026*. — CER reicht nicht, strukturelle Metriken noetig fuer historische Dokumente.
- Yuan, J. et al. (2024). Visual Analytics for Machine Learning: A Data Perspective Survey. *IEEE TVCG* 30(12). — Taxonomie fuer Dashboard-Features: Verteilungen statt Aggregate.
- Romein, C.A. et al. (2025). Assessing Advanced Handwritten Text Recognition Engines. *Int. J. Digital Humanities* 7(1), 115-134. — CER-Benchmarking-Methodik mit standardisierter Normalisierung.
- Levchenko, M. (2025). Evaluating LLMs for Historical Document OCR. *LM4DH 2025, RANLP*. — Domaenenspezifische Fehlertypen jenseits CER (Over-Historicization).
- Priestley, M. et al. (2023). A Survey of Data Quality Requirements That Matter in ML Development Pipelines. *JDIQ* 15(2). — Embedded Quality Monitoring entlang der Pipeline.
