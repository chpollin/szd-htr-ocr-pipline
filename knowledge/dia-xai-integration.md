---
title: "DIA-XAI-Integration"
aliases: ["DIA-XAI-Integration"]
created: 2026-04-01
updated: 2026-04-01
type: spec
status: draft
related:
  - "[[verification-concept]]"
  - "[[htr-interchange-format]]"
---

# DIA-XAI-Integration: SZD-HTR als Datenlieferant fuer EQUALIS

Abhaengigkeit: [[verification-concept]] (quality_signals, CER), [[htr-interchange-format]] (Page-JSON)

---

## 1. Zweck

Dieses Dokument definiert, wie die SZD-HTR-Pipeline Daten an das DIA-XAI-Evaluationsframework liefert. DIA-XAI (PLUS Early Career Grant, April 2026 – April 2027) evaluiert Expert-in-the-Loop-Workflows auf heterogenen Kulturdaten mit dem EQUALIS-Framework.

SZD-HTR bedient den DIA-XAI Use Case:
- **UC3 (HTR-Verifikation):** Wie effektiv ist Expert-Korrektur von VLM-Transkriptionen?

### 1.1 Zeitliche Abhaengigkeit

| Meilenstein | Datum | Abhaengigkeit |
|---|---|---|
| SZD-HTR Pilot (5 Seiten) | April 2026 | Muss vor DIA-XAI Phase 1 fertig sein |
| DIA-XAI Phase 1 (Interface-Design) | Mai–Jun 2026 | Nutzt Pilot-CER als Baseline |
| SZD-HTR GT-Sample (31 Objekte) | Jun–Aug 2026 | Liefert Ground Truth fuer EQUALIS QUA |
| DIA-XAI Phase 3 (EQUALIS-Durchlauf) | Okt 2026–Maerz 2027 | Voller Durchlauf auf SZD-HTR-Batch |

### 1.2 Was DIA-XAI ist (und was nicht)

DIA-XAI ist ein **Aggregator**, kein Verifikationstool. Es importiert Metriken-JSON (`dia-xai-metrics-v1`) aus externen Tools und berechnet die 5 EQUALIS-Dimensionen. Die eigentliche Verifikation findet in den Quelltools statt:

- **HTR-Verifikation:** Im SZD-HTR-Viewer (Frontend) oder via Verification-by-Vision
- **Metriken-Aggregation:** In DIA-XAI (Import → EQUALIS-Dashboard)

---

## 2. Datenfluss SZD-HTR → DIA-XAI

```
Faksimile (JPG)
  │
  ▼
SZD-HTR Pipeline (Gemini Flash Lite)
  │ → Transkriptions-JSON + quality_signals
  │
  ├──→ Verification-by-Vision (Claude + Gemini Vision)
  │     → Error-Markup, Corrections, Verification-Status
  │     → DIA-XAI Export (UC3: HTR-Verifikation)
  │
  ├──→ export_page_json.py
  │     → Page-JSON (Text + Layout + Metadaten)
  │
  ▼
DIA-XAI (EQUALIS-Dashboard)
  → 5-dimensionale Evaluation
```

### 2.1 Zwei Export-Punkte

**Export-Punkt A: Nach HTR + Verification (UC3)**

Quelle: SZD-HTR quality_signals + Verification-by-Vision-Ergebnisse.
Wann: Nach Verification-Durchlauf (manuell oder VbV).
Was wird exportiert: CER (wenn GT vorhanden), Fehlertypen, Korrekturzahlen, Expert-Effort.

---

## 3. EQUALIS-Mapping fuer SZD-HTR

Das EQUALIS-Framework misst 5 Dimensionen. Fuer jeden wird hier definiert, welche SZD-HTR-Daten die Metrik speisen.

### 3.1 E — Explainability (Provenienz)

**Frage:** Woher kommt jede Annotation? Maschinell, manuell, oder regelbasiert?

| SZD-HTR-Datenquelle | EQUALIS-Metrik | Berechnung |
|---|---|---|
| quality_signals (automatisch) | `provenance.regex` | Anzahl regelbasierter Flags (page_image_mismatch etc.) |
| VLM-Transkription | `provenance.llm` | Anzahl maschinell transkribierter Seiten |
| Expert-Review im Viewer | `provenance.expert` | Anzahl manuell korrigierter Seiten |

**Visualisierung in DIA-XAI:** Provenienz-Balken pro Objekt (gruen=expert, gelb=llm, grau=missing).

### 3.2 QUA — Quality (Korrektheit)

**Frage:** Wie korrekt sind die Transkriptionen und Annotationen?

| SZD-HTR-Datenquelle | EQUALIS-Metrik | Berechnung |
|---|---|---|
| CER aus GT-Sample ([[verification-concept]] §1) | `quality.cer` | Character Error Rate pro Objekt |
| CER pro Gruppe | `quality.fields.{group}.cer` | Median-CER pro Prompt-Gruppe (A–I) |
| quality_signals needs_review | `outcomes.accuracy_ai_only` | Anteil korrekt geflaggter Objekte (nach GT-Kalibrierung) |
| Verification-by-Vision Ergebnisse | `outcomes.error_recovery` | Anzahl durch VbV gefundener Fehler |

**Empirischer Stand (Session 9):** CER unbekannt (Pilot steht aus). quality_signals flaggen 63% — Precision/Recall erst nach GT kalibrierbar.

### 3.3 L — Learning (Verbesserung ueber Iterationen)

**Frage:** Verbessert sich die Pipeline durch Feedback?

| SZD-HTR-Datenquelle | EQUALIS-Metrik | Berechnung |
|---|---|---|
| Cross-Model-Verification ([[verification-concept]] §4) | Agreement-Trend | Steigt Agreement ueber Batches? |
| Prompt-Ueberarbeitung nach Pilot | Vorher/Nachher-CER | CER vor vs. nach Prompt-Fix |

**Erwartung:** Prompt-Experiment liefert erste L-Daten. Echtes iteratives Learning erst in DIA-XAI Phase 3.

### 3.4 I — Interaction (Expert-Aufwand)

**Frage:** Wie viel menschlichen Aufwand spart die Pipeline?

| SZD-HTR-Datenquelle | EQUALIS-Metrik | Berechnung |
|---|---|---|
| SZD-HTR Viewer Review | `reliance.accept` | Anzahl akzeptierter Transkriptionen (approved) |
| SZD-HTR Viewer Review | `reliance.correct` | Anzahl korrigierter Transkriptionen (edited) |
| Verification-by-Vision Timing | `session.duration_minutes` | Zeit pro Objekt |
| Accept-on-Wrong | `reliance.accept_on_wrong` | Expert akzeptiert falschen LLM-Vorschlag (Anchoring Bias) |

**Messung:** SZD-HTR Viewer loggt approve/edit pro Objekt. DIA-XAI aggregiert zu Ratios und Override-Frequenz.

### 3.5 S — Scalability (Uebertragbarkeit)

**Frage:** Funktioniert der Workflow fuer verschiedene Dokumenttypen gleich gut?

| SZD-HTR-Datenquelle | EQUALIS-Metrik | Berechnung |
|---|---|---|
| CER pro Gruppe (A–I) | CER-Varianz | Standardabweichung der Median-CER ueber 9 Gruppen |
| CER pro Sprache (DE/EN/FR) | Sprach-Vergleich | CER-Differenz zwischen Sprachen |
| Vergleich SZD vs. MHDBDB | Cross-Domain | Gleiche EQUALIS-Dimensionen, verschiedene Korpora |
| Vergleich Zweig vs. Rieger vs. Lotte | Schreiber-Vergleich | CER pro Hand |

**SZD-HTR liefert hier besonders wertvolle Daten:** 9 Dokumentgruppen, 4 Sprachen, 6+ Schreiberhaende — natuerliche Varianz fuer Scalability-Messung.

---

## 4. Metriken-Export: SZD-HTR → DIA-XAI

### 4.1 Zielformat: `dia-xai-metrics-v1`

DIA-XAI importiert JSON im folgenden Schema (Drag-and-Drop in die Web-App):

```json
{
  "schema": "dia-xai-metrics-v1",
  "source": "szd-htr",
  "useCase": "uc3",
  "exported": "2026-08-15T10:00:00Z",
  "session": {
    "duration_minutes": null,
    "expert_role": "Forschungsleitstelle"
  },
  "outcomes": {
    "total_items": 31,
    "accuracy_ai_only": null,
    "accuracy_expert_only": null,
    "accuracy_team": null,
    "error_recovery": null,
    "error_amplification": null
  },
  "reliance": {
    "accept": null,
    "correct": null,
    "add": null,
    "reject": null,
    "accept_on_wrong": null,
    "override_frequency": null
  },
  "quality": {
    "fields": {
      "handschrift":        { "precision": null, "recall": null, "f1": null },
      "typoskript":         { "precision": null, "recall": null, "f1": null },
      "korrespondenz":      { "precision": null, "recall": null, "f1": null },
      "zeitungsausschnitt": { "precision": null, "recall": null, "f1": null }
    },
    "cer": null
  },
  "provenance": {
    "regex": null,
    "llm": null,
    "missing": null,
    "expert": null
  },
  "interaction_log": []
}
```

Die `null`-Werte werden befuellt, sobald die entsprechenden Daten vorliegen (GT-Sample → CER/Quality, Viewer-Review → Reliance).

### 4.2 Wann wird was befuellt?

| EQUALIS-Feld | Befuellt nach | Datenquelle |
|---|---|---|
| `quality.cer` | Pilot + GT-Sample | CER-Script (L3) |
| `quality.fields.{group}` | GT-Sample (31 Objekte) | CER pro Gruppe |
| `outcomes.total_items` | Sofort | Anzahl transkribierter Objekte |
| `outcomes.accuracy_ai_only` | GT-Kalibrierung | quality_signals Precision |
| `reliance.*` | Viewer-Review | Approve/Edit-Zahlen |
| `provenance.*` | Pipeline + Viewer | LLM vs. Expert-Zaehlung |
| `interaction_log[]` | Viewer-Review | Pro-Objekt-Entscheidungen |
| `outcomes.error_recovery` | Verification-by-Vision | Durch VbV gefundene Fehler |

### 4.3 Export-Implementierung

**Fuer UC3 (HTR-Verifikation):**
L3 schreibt ein Script (`pipeline/export_dia_xai.py`), das:
1. Alle Result-JSONs liest
2. quality_signals aggregiert
3. CER-Werte (wenn vorhanden) einfuegt
4. VbV-Ergebnisse (wenn vorhanden) integriert
5. `dia-xai-metrics-v1` JSON erzeugt

---

## 5. Zeitplan und Abhaengigkeiten

```
April 2026 (JETZT):
  ├── SZD-HTR: ~1328 Objekte transkribiert (63%)
  └── DIA-XAI: Repo angelegt, EQUALIS spezifiziert, Use Cases definiert

Mai–Jun 2026 (DIA-XAI Phase 1):
  ├── SZD-HTR: GT-Kalibrierung, quality_signals-Schwellenwerte
  └── DIA-XAI: EIL-Interface-Prototyp mit SZD-HTR-Daten

Jul–Sep 2026:
  ├── SZD-HTR: Verbleibende Sammlungen transkribieren, GT-Sample erweitern
  └── DIA-XAI: UC3-Metriken (CER) importieren

Okt 2026–Maerz 2027 (DIA-XAI Phase 3):
  ├── Voller EQUALIS-Durchlauf auf SZD-HTR-Batch (~2107 Objekte)
  ├── Cross-Domain-Vergleich SZD vs. MHDBDB
  └── Aufsatz "Amplified, Not Automated"
```

### 5.1 Was SZD-HTR fuer DIA-XAI Phase 1 liefern muss

Minimum fuer Mai 2026:
1. **CER-Werte aus GT-Sample** — quantitative Baseline
2. **quality_signals fuer ~1328 Objekte** — zeigt Triage-Faehigkeit
3. **Verification-by-Vision Ergebnisse** — zeigt VbV-Ansatz

Das ist realistisch — Pilot und quality_signals sind die einzigen blockierenden Aufgaben.
