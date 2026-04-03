# Pipeline

## prompts/

Dreischichtiges Prompt-System für die VLM-Transkription:

| Schicht | Datei | Funktion |
|---|---|---|
| 1 — System | `system.md` | Rolle, Regeln, Output-Format (für alle Objekte gleich) |
| 2 — Gruppe | `group_*.md` | Typspezifische Anweisungen pro Dokumentgruppe |
| 3 — Kontext | `context_template.md` | Objektspezifische Metadaten aus TEI (zur Laufzeit generiert) |

### Gruppen (9 Stueck)

| Gruppe | Prompt | Sammlungen | Hauptmerkmal |
|---|---|---|---|
| A | `group_a_handschrift.md` | Lebensdok., Werke | Zweigs Handschrift, Kurrent |
| B | `group_b_typoskript.md` | Lebensdok., Werke, Aufsatz | Maschinenschrift, Durchschläge |
| C | `group_c_formular.md` | Lebensdokumente | Formulare, Urkunden |
| D | `group_d_kurztext.md` | Lebensdokumente | Kurztexte, Karten |
| E | `group_e_tabellarisch.md` | Lebensdok., Aufsatz | Register, Kalender, Listen |
| F | `group_f_korrekturfahne.md` | Werke, Aufsatz | Druck + handschriftl. Korrekturen |
| G | `group_g_konvolut.md` | Werke | Gemischte Materialien |
| H | `group_h_zeitungsausschnitt.md` | Aufsatzablage | Zeitungsdruck, ggf. Fraktur |
| I | `group_i_korrespondenz.md` | Korrespondenzen | Briefe, Postkarten |

## Kern-Pipeline

Scripts die den regulaeren Datenfluss bilden (Transkription → Enrichment → Export → Viewer):

| Script | Funktion |
|---|---|
| `config.py` | Pfade, API-Key, Sammlungs-Mapping, Konstanten |
| `tei_context.py` | TEI-Parser: extrahiert Metadaten, generiert Kontext, ordnet Gruppen zu |
| `transcribe.py` | Batch-CLI: Einzel-/Sammlungs-/Gesamtmodus mit Rate-Limit-Retry |
| `quality_signals.py` | 7 Qualitaetssignale + page.type (v1.5, DWR entfernt) |
| `verify.py` | Modellkonsensus: Gemini Flash Lite + Flash 3 + Claude Judge |
| `evaluate.py` | CER/WER-Berechnung mit Normalisierung (annotation-protocol.md §5) |
| `build_viewer_data.py` | Baut `catalog.json` + `data/{collection}.json` aus enriched Ergebnis-JSONs |
| `serve.py` | Lokaler Dev-Server mit Review-API (Approve/Edit) |
| `import_reviews.py` | Expert-Review Write-Back (Frontend-Export → Pipeline-JSON) |

## Export

Zwei komplementaere Ausgabeformate: Page-JSON v0.2 (internes Arbeitsformat) und METS/MODS + PAGE XML (Archiv- und Austauschformat).

| Script | Funktion |
|---|---|
| `layout_analysis.py` | VLM-basierte Layout-Analyse (Regionen + Bounding Boxes) |
| `export_page_json.py` | OCR + Layout + TEI-Metadaten → Page-JSON v0.2 (Arbeitsformat) |
| `export_pagexml.py` | Page-JSON → PAGE XML 2019 (Teil des Zielformats) |
| `export_mets.py` | METS-Container mit MODS + PAGE XML Referenzen (geplant) |

## Diagnose & Werkzeuge

Einmal- oder Gelegenheits-Scripts fuer Analyse, Reparatur und Batch-Steuerung:

| Script | Funktion | Status |
|---|---|---|
| `diagnose_truncation.py` | Vergleicht Seitenzahlen in JSONs mit Backup-Bildern, findet Truncation | Aktiv — Output auf stdout oder `--json` |
| `fraktur_postprocess.py` | Woerterbuch-basierte Fraktur-Korrektur (f↔s etc.), nur Vorschlaege | Prototyp — 38% Precision, brauchbar als Flagging-Tool |
| `quality_report.py` | Aggregierte Statistiken pro Gruppe/Sammlung (CLI + JSON) | Aktiv |
| `run_sample_batch.py` | Gezielter Batch: fuellt jede Gruppe auf 10 auf | Erledigt (Sample komplett) |
| `generate_gt.py` | 3-Modell-GT-Pipeline (Flash Lite + Flash + Pro) | Aktiv — 18 GT-Drafts erzeugt |
| `backfill_page_types.py` | Stempelt page.type auf bestehende JSONs | Einmal-Migration, erledigt |
| `backfill_quality_signals.py` | Recompute quality_signals nach Schwellenwert-Aenderungen | Bei Bedarf |
| `backfill_edit_history.py` | Retroaktives edit_history-Patching aus Git-History | Einmal-Migration, erledigt |

## Beispiel

`example_theaterkarte.md` — vollständig zusammengesetzter Prompt (alle 3 Schichten) für o:szd.161.
