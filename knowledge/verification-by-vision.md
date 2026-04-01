---
title: "Verification-by-Vision: LLM-gestuetzte Bildpruefung der Transkriptionen"
aliases: ["VbV", "Verification-by-Vision"]
created: 2026-04-01
updated: 2026-04-01
type: concept
tags: [szd-htr, methodology, verification]
status: draft
related:
  - "[[verification-concept]]"
  - "[[annotation-protocol]]"
  - "[[pilot-design]]"
---

# Verification-by-Vision: LLM-gestuetzte Bildpruefung der Transkriptionen

Abhaengigkeit: [[verification-concept]] (Gesamtrahmen), [[annotation-protocol]] (Fehlertypen)

---

## 1. Zweck und Abgrenzung

Verification-by-Vision (VbV) ist ein Verfahren zur automatischen Qualitaetspruefung von VLM-Transkriptionen. Zwei VLMs vergleichen unabhaengig voneinander das Faksimile-Bild mit dem Transkriptionstext und identifizieren Fehler.

**Staerke:** Direkter Bild↔Text-Vergleich — staerker als Transkriptionsvergleich (Cross-Model aus [[verification-concept]] §4), weil das Quellbild einbezogen wird, nicht nur zwei Textversionen.

**Abgrenzung:**
- VbV **ersetzt nicht** den manuellen Pilot (der misst CER gegen Ground Truth).
- VbV **ersetzt nicht** quality_signals (die automatische Anomalie-Erkennung ohne Bildvergleich).
- VbV **ergaenzt** beide Verfahren um eine direkte Bildpruefung mit konkreten Fehlermeldungen.
- VbV hat **inhaerent VLM-Grenzen**: Beide Kanaele teilen aehnliche Schwaechen (z.B. bei Kurrent-Schrift). Menschliche Expertise bleibt fuer editionskritische Nutzung unersetzlich.

---

## 2. Workflow

### 2.1 Zwei unabhaengige Kanaele

```
Faksimile (Bild) + Transkription (Text)
        |                         |
   Kanal A                   Kanal B
   Claude Code Agent         Gemini API
   (Read-Tool, Vision)       (verify_gemini.py)
        |                         |
   Fehlerliste A             Fehlerliste B
        |                         |
        +-------- Merge ----------+
                    |
            Verification-Ergebnis
```

**Kanal A — Claude Code Agent:**
- Ein Subagent liest das Faksimile-Bild via Read-Tool (Claude Codes eingebaute Vision).
- Liest die Transkription aus der Result-JSON.
- Vergleicht seitenweise, dokumentiert Fehler als strukturierte Liste.
- Kein API-Call, keine Kosten. Wird von der Forschungsleitstelle koordiniert.
- Dauer: ~2-5 Minuten pro Objekt (abhaengig von Seitenzahl und Komplexitaet).

**Kanal B — Gemini API:**
- `pipeline/verify_gemini.py` (Lane 3) sendet Bild + Text an Gemini Vision API.
- Erhaelt strukturierte Fehlerliste als JSON.
- Kostet API-Calls (~1 pro Seite).

### 2.2 Merge-Logik

| Kanal A | Kanal B | Ergebnis | Konfidenz |
|---|---|---|---|
| Fehler X gefunden | Fehler X gefunden | Error (Cross-Model-Agreement) | Hoch |
| Fehler X gefunden | Kein Fehler | Error (Einzelbefund) | Mittel |
| Kein Fehler | Fehler X gefunden | Error (Einzelbefund) | Mittel |
| Kein Fehler | Kein Fehler | Verified (Agreement) | Hoch |

"Fehler X gefunden" = beide identifizieren denselben Fehler an derselben Textstelle.

### 2.3 Nur ein Kanal verfuegbar

Wenn nur Kanal A vorliegt (Regelfall bei Stichproben): Ergebnis gilt als Einzelbefund (mittlere Konfidenz). Wenn nur Kanal B vorliegt (nach Batch-Verifikation): ebenso.

---

## 3. Status-Kategorien

| Status | Bedeutung | Farbe (Frontend) |
|---|---|---|
| `llm_verified` | Kein VLM findet Fehler | Gruen |
| `llm_error_suggestion` | Mindestens ein Fehler gefunden | Orange/Rot |
| `unverified` | Noch nicht geprueft | Grau |
| `human_verified` | Operator hat manuell bestaetigt | Blau |

Status wird pro Objekt gesetzt (nicht pro Seite). Pro Seite gibt es die Fehlerliste.

---

## 4. Error-Markup-Format

### 4.1 Inline-Markup

Fehler werden direkt im Transkriptionstext markiert:

```
«original→korrektur|konfidenz»
```

Beispiele:
- `«entbalten→enthalten|0.8»` — Zeichenfehler, hohe Konfidenz
- `«Ictreesten→[unleserlich]|0.8»` — Halluzination/Fehllesung
- `«gegebenfalls→gegebenenfalls|0.7»` — fehlendes "en"
- `«Kiow→Kiew|0.6»` — unsichere Lesung (moeglicherweise Autorvariante)
- `«selten→schon|0.4»` — niedrige Konfidenz, menschliche Pruefung noetig

### 4.2 Abgrenzung zu bestehenden Markern

| Marker | Quelle | Bedeutung |
|---|---|---|
| `[?]` | VLM (Transkription) | VLM markiert eigene Unsicherheit |
| `[...]` | VLM (Transkription) | VLM markiert unleserliche Stelle |
| `~~...~~` | VLM (Transkription) | Durchgestrichener Text |
| `{...}` | VLM (Transkription) | Einfuegung/Ergaenzung |
| `«...→...|...»` | **VbV (Verifikation)** | **Fehlervorschlag mit Korrektur und Konfidenz** |

Die `«»`-Guillemets wurden gewaehlt, weil sie in keinem bestehenden Markup vorkommen und visuell auffallen.

### 4.3 Frontend-Rendering

L1 parst `«...»`-Spans und rendert sie als:
- `<span class="error-suggestion" data-conf="0.8">` mit Tooltip (Korrektur + Konfidenz)
- Rot (conf >= 0.7), Orange (conf 0.4-0.7), Gelb (conf < 0.4)
- Click akzeptiert Korrektur (aendert Text, entfernt Markup)

---

## 5. Konfidenz-Modell

### 5.1 Ebenen

| Ebene | Signal | Staerke | Anmerkung |
|---|---|---|---|
| Cross-Model-Agreement (Fehler) | Beide VLMs finden denselben Fehler | Stark | Bester Indikator |
| Cross-Model-Agreement (kein Fehler) | Beide VLMs finden keinen Fehler | Stark | Aber nicht perfekt — beide koennen denselben Fehler uebersehen |
| Einzelbefund | Nur ein VLM findet den Fehler | Mittel | Kann false positive sein |
| Pro-Fehler-Konfidenz (0.0-1.0) | VLM-Selbsteinschaetzung | Schwach | LLMs ueberschaetzen systematisch (siehe [[verification-concept]] Ausgangslage) |

### 5.2 Warum Pro-Fehler-Konfidenz trotzdem nuetzlich

Obwohl LLM-Selbsteinschaetzung schwach ist, hilft sie bei der **Priorisierung**: Fehler mit Konfidenz 0.9 sind wahrscheinlicher als Fehler mit 0.3. Der absolute Wert ist unzuverlaessig, aber die **relative Rangfolge** ist brauchbar fuer die Triage durch den Operator.

---

## 6. Fehlertypen

Kompatibel mit [[annotation-protocol]] §7 (Fehlertaxonomie):

| Typ | Beschreibung | Beispiel (aus Tests) |
|---|---|---|
| Zeichenfehler | Einzelne Buchstaben falsch | "entbalten" statt "enthalten" |
| Wortfehler | Ganzes Wort falsch | "Kiow" statt "Kiew" |
| Auslassung | Text im Bild, fehlt in Transkription | "Datum:"-Label nicht transkribiert |
| Halluzination | Text in Transkription, nicht im Bild | "Ictreesten" (Nonsens-Wort) |
| Strukturfehler | Reihenfolge, Absaetze, Zuordnung falsch | Korrekturschichten falsch verschachtelt |
| Markup-Fehler | Falsches oder fehlendes Markup | Durchstreichung nicht markiert |

---

## 7. Empirische Befunde

Getestet in Session 11 (Forschungsleitstelle, Kanal A = Claude Code Agent).

### 7.1 Ergebnistabelle

| Objekt | Gruppe | Gemini Conf | VbV Status | Klare Fehler | Unsichere Stellen | Kernbefund |
|---|---|---|---|---|---|---|
| o_szd.161 | D Kurztext | high | llm_verified | 0 | 0 | Gedruckter Text + Bleistift-Kurztext fehlerfrei |
| o_szd.72 | A Handschrift | high | error_suggestion | 0 | 18 | Kurrent-Ambiguitaeten, keine Halluzinationen, bemerkenswert gut |
| o_szd.277 | G Konvolut | medium | error_suggestion | 2 | 10 | "entbalten", "Ictreesten" in Korrekturschicht |
| o_szd.139 | C Formular | high | error_suggestion | 0 | 2 | "Datum:"-Label auf Seite 1 fehlt (Seite 3 hat es) |
| o_szd.1887 | F Korrekturfahne | high | error_suggestion | 0 | 5 | Drucktext korrekt, handschriftl. Vermerke problematisch ("ueberhagn") |
| o_szd.147 | C Formular | ? | BROKEN | — | — | 64 Bilder, 0 Seiten transkribiert — Pipeline-Bug |

### 7.2 Muster

1. **Gedruckter Text** (Typoskript, Formular-Grundtext, Korrekturfahnen-Drucktext): Durchgehend korrekt. Keine Fehler in 6 Objekten.
2. **Handschrift** (Kurrent, Briefschrift, Bleistift): Gut, aber mit Einzelwort-Ambiguitaeten. Kein Fall von Halluzination. Geminis "high confidence" ist optimistisch aber vertretbar.
3. **Handschriftliche Korrekturen und Vermerke**: Schwaechste Schicht (~60-70% korrekt). Ueberlappende Tintenfarben, Durchstreichungen mit Einfuegungen, marginale Notizen — hier produziert Gemini Nonsens-Woerter und falsche Zuordnungen.
4. **Pipeline-Bug**: Objekte mit sehr vielen Bildern (o_szd.147: 64 Bilder) erzeugen leere Ergebnisse. Vermutlich `--max-images`-Limit oder Token-Ueberlauf.

### 7.3 Methodische Grenzen

- **Aehnliche Schwaechen**: Claude und Gemini teilen VLM-typische Schwaechen bei Kurrent-Schrift (n/u, e/r Verwechslungen). Cross-Model-Agreement ist hier weniger informativ.
- **Bildaufloesung**: Bei Korrekturfahnen mit kleinem Drucktext ist die Aufloesung der Backup-JPGs manchmal grenzwertig fuer Zeichen-fuer-Zeichen-Pruefung.
- **Kontextwissen**: Eigennamen (Gieser? Rieser?), historische Schreibweisen (Kiow/Kiew), Autorvarianten — ohne biographische Referenz nicht sicher verifizierbar.

---

## 8. JSON-Schema (Verifikationsergebnis)

```json
{
  "verification": {
    "claude": {
      "status": "llm_verified | llm_error_suggestion",
      "verified_at": "2026-04-01",
      "errors": [
        {
          "page": 3,
          "position": "Zeile 5, Wort 3",
          "original": "entbalten",
          "correction": "enthalten",
          "confidence": 0.8,
          "type": "zeichenfehler",
          "context": "~~erst entbalten~~ den"
        }
      ],
      "pages_checked": 3,
      "notes": "Freitext-Zusammenfassung"
    },
    "gemini": {
      "status": "...",
      "verified_at": "...",
      "errors": [],
      "pages_checked": 3,
      "notes": "..."
    },
    "merged": {
      "status": "llm_verified | llm_error_suggestion",
      "agreement_rate": 0.85,
      "errors_agreed": [],
      "errors_claude_only": [],
      "errors_gemini_only": []
    }
  }
}
```

---

## 9. Kosten und Aufwand

| Kanal | Kosten pro Seite | Kosten 74 Objekte (~220 Seiten) | Dauer pro Objekt |
|---|---|---|---|
| A (Claude Code) | Kostenlos | $0 | ~2-5 Min |
| B (Gemini API) | ~$0.001 | ~$0.22 | ~10 Sek |
| **Gesamt** | | **~$0.22 + Agent-Zeit** | |

**Empfehlung:**
- Kanal A (Claude Code) fuer Stichproben und schwierige Objekte (Handschrift, Konvolute)
- Kanal B (Gemini API) fuer systematischen Batch aller Objekte
- Merge wenn beide vorliegen

---

## 10. Offene Punkte

1. **Prompt-Design optimieren**: Der aktuelle Verifikations-Prompt ist ad-hoc. Systematische Evaluation verschiedener Prompt-Strategien (Zeile-fuer-Zeile vs. abschnittsweise vs. Gesamtseite) steht aus.
2. **CER-Berechnung aus Error-Markup**: `«orig→korr|conf»`-Markup koennte automatisch in CER umgerechnet werden (Levenshtein auf die Korrekturen). Vorsicht: Nur erkannte Fehler — die tatsaechliche CER ist hoeher.
3. **Schwellenwert fuer llm_verified**: Ab wann gilt ein Objekt als verified? Aktuell: 0 Fehler = verified. Aber was bei Fehlern mit Konfidenz < 0.3?
4. **Batch-Automatisierung Kanal A**: Kann ein Claude-Code-Subagent automatisiert durch alle 62+ Objekte iterieren? Token-Limits und Session-Laenge beachten.
5. **Integration mit quality_signals**: VbV-Status und quality_signals-`needs_review` sollten gemeinsam ausgewertet werden. Vorschlag: `needs_review = quality_signals.needs_review OR verification.status == "llm_error_suggestion"`.
