"""SZD-HTR Page-JSON Export: Pipeline-JSON + Layout-JSON → Page-JSON v0.1.

Merges the two pipeline outputs (transcription + optional layout) into a single
Page-JSON file per object, conforming to schemas/page-json-v0.1.json.

Specification: knowledge/htr-interchange-format.md (Page-JSON v0.1)
Schema:        schemas/page-json-v0.1.json

Input:
    results/{collection}/{object_id}_{model}.json    — transcription + quality_signals
    results/{collection}/{object_id}_layout.json     — layout regions (optional)

Output:
    results/{collection}/{object_id}_page.json       — merged Page-JSON

Mapping (Pipeline-JSON → Page-JSON):
    object_id                    → source.id
    collection                   → source.collection
    group                        → source.additional.group
    model                        → provenance.model
    metadata.title               → source.title
    metadata.language             → source.language  (normalize: "Deutsch" → "de")
    metadata.images[]            → source.images[]
    context                      → source.additional.context
    result.pages[].page          → pages[].page
    result.pages[].transcription → pages[].text
    result.pages[].notes         → pages[].notes
    result.pages[].type          → pages[].type
    result.confidence            → confidence
    quality_signals.*            → quality.*

Mapping (Layout-JSON → Page-JSON, merged into pages[]):
    pages[].image_filename       → pages[].image
    pages[].image_width_px       → pages[].image_width
    pages[].image_height_px      → pages[].image_height
    pages[].regions[]            → pages[].regions[]  (1:1)

Language normalization:
    Deutsch / Deutsch?  → de
    Englisch            → en
    Franzoesisch        → fr
    Italienisch         → it
    Spanisch            → es
    Jiddisch            → yi
    unbekannt           → und

Usage (planned):
    python pipeline/export_page_json.py o_szd.100 -c lebensdokumente
    python pipeline/export_page_json.py -c werke
    python pipeline/export_page_json.py --all

TODO: Implement. Estimated ~100-150 lines. Key steps:
    1. Load pipeline JSON + optional layout JSON (reuse load_ocr_and_layout from export_pagexml.py)
    2. Build source{} from metadata + TEI context
    3. Build provenance{} from model + timestamps
    4. Build pages[] — merge transcription pages with layout regions
    5. Normalize language codes
    6. Write Page-JSON with page_json: "0.1" version marker
    7. Optional: validate against schema (requires jsonschema dependency)
"""

# Implementation pending — see docstring for full specification.
