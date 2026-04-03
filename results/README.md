# results/ — Ergebnis-Dateien der HTR-Pipeline

Jede Sammlung hat einen Unterordner. Pro Objekt koennen mehrere Dateien existieren:

## Dateitypen

| Muster | Beispiel | Beschreibung |
|---|---|---|
| `{id}_{model}.json` | `o_szd.100_gemini-3.1-flash-lite-preview.json` | **Primaere Transkription** — Hauptergebnis der Pipeline. Enthaelt `pages[]`, `quality_signals`, optional `review`. |
| `{id}_consensus.json` | `o_szd.100_consensus.json` | **Modellkonsensus** — Vergleich von 2-3 Modellen (Flash Lite + Flash/Pro + Claude Judge). Erzeugt von `verify.py`. |
| `{id}_gemini-3.1-pro.json` | `o_szd.100_gemini-3.1-pro.json` | **Zweittranskription** — Gemini Pro als Vergleichsmodell fuer Konsensus. |
| `{id}_layout.json` | `o_szd.100_layout.json` | **Layout-Analyse** — VLM-basierte Regionenerkennung (Bounding Boxes). Erzeugt von `layout_analysis.py`. |
| `{id}_page.json` | `o_szd.100_page.json` | **Merged Page-JSON** — Transkription + Layout zusammengefuehrt. Erzeugt von `export_page_json.py`. |
| `{id}_page/` | `o_szd.100_page/page_001.xml` | **PAGE XML Export** — PAGE XML 2019 pro Seite. Erzeugt von `export_pagexml.py`. |
| `{id}_gt_draft.json` | (nur in `groundtruth/`) | **GT-Draft** — 3-Modell-Konsensus als Grundlage fuer manuelles Ground-Truth-Review. |

## Ordnerstruktur

```
results/
├── lebensdokumente/     127 Objekte
├── werke/                54 Objekte
├── aufsatzablage/       115 Objekte
├── korrespondenzen/    1032 Objekte
└── groundtruth/          18 GT-Drafts
```

Objektzahlen mit `python pipeline/transcribe.py --all --dry-run` pruefen.

## Primaeres Ergebnis vs. Nebenprodukte

Die primaere Transkription (`{id}_{model}.json`) ist die einzige Datei, die von `transcribe.py` erzeugt wird und von `build_viewer_data.py` fuer den Viewer gelesen wird. Alle anderen Dateitypen sind Nebenprodukte der Verifikations- und Export-Pipeline.
