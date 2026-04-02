---
title: "Ground-Truth-Pipeline: 3-Modell-Konsensus + Expert-Review"
aliases: ["GT-Pipeline"]
created: 2026-04-02
updated: 2026-04-02
type: concept
tags: [szd-htr, methodology, ground-truth]
status: active
related:
  - "[[verification-concept]]"
  - "[[annotation-protocol]]"
  - "[[pilot-design]]"
---

# Ground-Truth-Pipeline: 3-Modell-Konsensus + Expert-Review

## 1. Zweck

Manuelle Ground-Truth-Erstellung fuer 100+ Seiten ist bei einem Einzelforscher nicht realistisch (geschaetzte 15-45 Min/Seite). Die GT-Pipeline nutzt stattdessen 3 VLMs als Ersttranskriptoren und reduziert den menschlichen Aufwand auf Review + Korrektur. Das ist methodisch analog zur OCR-Nachkorrektur in DH-Projekten — nur mit einem besseren Startentwurf.

**Wissenschaftliche Grundlage:** Zhang et al. 2025 (Consensus Entropy, ICLR 2026) zeigen, dass korrekte VLM-Transkriptionen im Output-Space konvergieren. Humphries et al. 2024 belegen, dass heterogene Kreuzkorrektur CER um 78% senkt (8.0% → 1.8%).

## 2. Architektur

```
Faksimile-Scans (JPG)
       │
       ├──→ Modell A: Gemini 3.1 Flash Lite  (existierende Transkription)
       ├──→ Modell B: Gemini 3 Flash          (aus Konsensus-Verifikation)
       └──→ Modell C: Gemini 3.1 Pro          (staerkstes Modell, via API)
                │
                ▼
       ┌─────────────────────┐
       │  Merge-Logik         │
       │  (generate_gt.py)    │
       │  consensus / majority│
       │  / pro_only          │
       └──────────┬──────────┘
                  ▼
       GT-Draft JSON (results/groundtruth/)
                  │
                  ▼
       ┌─────────────────────┐
       │  Frontend Review     │
       │  (app.js, localhost) │
       │  3-Varianten-Panel   │
       │  Approve pro Seite   │
       └──────────┬──────────┘
                  ▼
       Expert-GT JSON ({object_id}_gt.json)
```

## 3. Merge-Logik

Pro Seite werden die 3 Transkriptionen paarweise verglichen (CER nach `normalize_for_consensus`):

| Bedingung | Ergebnis | Label | Aktion |
|---|---|---|---|
| Alle 3 Paare CER < 2% | Alle stimmen ueberein | `consensus_3of3` | Pro-Version uebernommen (bestes Modell) |
| Bestes Paar CER < 5% | 2 von 3 stimmen ueberein | `majority_2of3` | Staerkeres Modell aus dem Paar (Pro > Flash > Flash Lite) |
| Kein Paar unter 5% | Alle divergieren | `pro_only` | Pro-Version als Draft, Expert muss entscheiden |
| Seite ist blank/color_chart | Nicht-Content | `skipped` | Uebersprungen |

## 4. Die 18 GT-Objekte

Stratifiziert ueber alle 9 Prompt-Gruppen, ausgewaehlt aus den 27 Konsensus-Objekten:

| Gruppe | Objekte | Begruendung |
|---|---|---|
| A Handschrift | o_szd.139 (verified), o_szd.141 (divergent) | 1 leicht + 1 schwer |
| B Typoskript | o_szd.102 (verified), o_szd.100 (moderate) | Vergleich verified vs moderate |
| C Formular | o_szd.145 (verified), o_szd.146 (review) | Verschiedene Schwierigkeitsgrade |
| D Kurztext | o_szd.142 (moderate, 100% word_overlap), o_szd.148 (divergent) | Reading-Order-Fall + schwierig |
| E Tabellarisch | o_szd.149 (moderate), o_szd.195 (moderate) | Registerstrukturen |
| F Korrekturfahne | o_szd.1887 (verified), o_szd.1888 (verified) | Baseline — geloester Dokumenttyp |
| G Konvolut | o_szd.127 (moderate) | Heterogene Materialien |
| H Zeitungsausschnitt | o_szd.2213 (moderate), o_szd.2217 (moderate) | Gedruckter Text, potentiell Fraktur |
| I Korrespondenz | o_szd.1079, o_szd.1081, o_szd.1088 (alle divergent) | Schwierigste Gruppe, 3 Objekte fuer Varianz |

## 5. Empirische Ergebnisse (2026-04-02)

**46 Content-Seiten + 23 Skipped (Blank/Farbskala):**

| Merge-Typ | Seiten | Anteil | Review-Aufwand |
|---|---|---|---|
| consensus_3of3 | 15 | 33% | Minimal — nur bestaetigen |
| majority_2of3 | 20 | 43% | Mittel — Mehrheit pruefen |
| pro_only | 11 | 24% | Hoch — Expert muss entscheiden |

**Muster nach Gruppe:**
- **Korrekturfahne** (o_szd.1888): 3/3 Konsensus auf allen Content-Seiten — gedruckter Text ist geloest
- **Typoskript** (o_szd.102): 1 Konsensus + 2 Mehrheit — sehr gut
- **Korrespondenz** (o_szd.1079): 1 Konsensus + 2 Mehrheit + 2 Pro-only — gemischt, erwartbar bei Handschrift
- **Kurztext** (o_szd.148): 0 Konsensus, 0 Mehrheit, 1 Pro-only — wenig Text = instabil

## 6. JSON-Schema: GT-Draft

```json
{
  "object_id": "o_szd.102",
  "collection": "lebensdokumente",
  "group": "typoskript",
  "title": "Agreement THE VIKING PRESS, INC.",
  "models": {
    "a": "gemini-3.1-flash-lite-preview",
    "b": "gemini-3-flash-preview",
    "c": "gemini-3.1-pro-preview"
  },
  "pages": [
    {
      "page": 1,
      "transcription": "...",
      "type": "content",
      "source": "majority_2of3",
      "notes": "",
      "variants": {
        "flash_lite": "...",
        "flash": "...",
        "pro": "..."
      }
    }
  ],
  "merge_stats": {
    "consensus_3of3": 1,
    "majority_2of3": 2,
    "pro_only": 0,
    "skipped": 0
  },
  "expert_verified": false,
  "reviewed_by": null,
  "reviewed_at": null,
  "created_at": "2026-04-02T..."
}
```

Nach Expert-Review wird `{object_id}_gt.json` exportiert mit:
- `expert_verified: true`
- `reviewed_by: "Christopher Pollin"`
- `reviewed_at: "2026-04-02T..."`
- `pages[].approved: true/false`
- `pages[].expert_edited: true/false`

## 7. Abgrenzung

| Aspekt | GT-Pipeline | Manueller Pilot (pilot-design.md) |
|---|---|---|
| Startentwurf | 3 VLM-Transkriptionen | Mensch transkribiert from scratch |
| Aufwand/Seite | ~5-10 Min (Review) | ~20-40 Min (Transkription) |
| Skalierbarkeit | Hoch (API-Kosten ~$0.50/Objekt) | Niedrig (menschliche Zeit) |
| Qualitaet | Abhaengig von VLM-Qualitaet + Expert-Review | Gold-Standard |
| Bias-Risiko | 3 Modelle koennen systematisch irren | Mensch kann lesen, was Modelle nicht koennen |

Die GT-Pipeline ersetzt den manuellen Pilot nicht konzeptionell, sondern praktisch: Sie liefert dieselben Antworten (CER-Groessenordnung, Fehlertypen, Gruppenunterschiede) mit weniger Aufwand. Der Expert-Review stellt sicher, dass das Ergebnis menschlich validiert ist.

## 8. Dateien

| Datei | Funktion |
|---|---|
| `pipeline/generate_gt.py` | GT-Erzeugung: Pro-Transkription + 3-Modell-Merge |
| `results/groundtruth/{object_id}_gt_draft.json` | GT-Drafts (18 Objekte) |
| `results/{collection}/{object_id}_gemini-3.1-pro.json` | Pro-Transkriptionen (18 Objekte) |
| `docs/data/groundtruth.json` | GT-Daten fuer Frontend |
| `docs/app.js` | GT Review-Modus (toggleGtReview, renderGtReview) |
