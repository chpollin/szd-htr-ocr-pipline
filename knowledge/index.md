---
title: "SZD-HTR Research Vault"
created: 2026-04-01
updated: 2026-04-01
type: moc
tags: [szd-htr]
status: active
---

# SZD-HTR Research Vault

Methodische Grundlagen, Datenanalysen und Entscheidungen des SZD-HTR-Projekts.

## Leseordnung

1. [[data-overview]] — Datengrundlage verstehen (4 Sammlungen, 9 Gruppen, ~2107 Objekte)
2. [[annotation-protocol]] — Transkriptionskonventionen fuer das Referenz-Sample
3. [[verification-concept]] — Qualitaetsmessung: GT, quality_signals, Cross-Model, Multi-Model-Konsensus (§7 NEU)
4. [[pilot-design]] — 5-Seiten-Pilot (superseded durch Konsensus-Validierung + GT-Pipeline)
5. [[ground-truth-pipeline]] — 3-Modell-GT mit Expert-Review (18 Objekte, 46 Seiten)

## Spezifikationen

- [[htr-interchange-format]] — JSON-Schema fuer szd-htr → teiCrafter (Entwurf)
- [[tei-target-structure]] — TEI-Zielformat fuer annotierte SZD-Transkriptionen (DTABf-basiert)
- [[teiCrafter-integration]] — Integrationskonzept: JSON-Import, Mapping-Templates, Schema-Erweiterungen
- [[verification-by-vision]] — LLM-gestuetzte Bildpruefung: Claude Code Agent + Gemini API
- [[layout-analysis]] — VLM-basierte Layout-Analyse + PAGE XML Export (Regionen, Bounding Boxes, Koordinatensystem)
- [[dia-xai-integration]] — EQUALIS-Mapping: SZD-HTR → DIA-XAI (UC3 + UC4)

## Projektlog

- [[journal]] — Chronologisches Log aller Sessions (1–14)

## Verwandte Dokumente (ausserhalb des Vaults)

- [Plan.md](../Plan.md) — Phasen-Roadmap (einzige Wahrheitsquelle fuer Status)
- [CLAUDE.md](../CLAUDE.md) — Entwickler/AI-Guide
