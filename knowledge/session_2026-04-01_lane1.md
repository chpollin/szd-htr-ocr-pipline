# Lane 1 Bericht — Frontend/Viewer (2026-04-01)

Adressaten: Lane 2 (Methodik), Lane 3 (Pipeline)

---

## Was gebaut wurde

Kompletter Frontend-Rewrite. Vorher: zwei separate HTML-Dateien (index.html Scroll-Dump + viewer.html Side-by-Side). Nachher: Single-Page-App mit Katalog → Viewer-Navigation.

### Dateien

```
docs/
├── index.html        ← HTML-Skelett, Help-Modal
├── app.css           ← SZD-Design-System (Burgundy/Gold, Source Serif/Sans)
├── app.js            ← Routing, Katalog, Viewer, Edit, Export
├── catalog.json      ← Leichtgewichtige Metadaten (~200 KB bei 2107 Obj.)
└── data/
    ├── lebensdokumente.json   ← Transkriptionen (on-demand geladen)
    ├── werke.json
    ├── aufsatzablage.json
    └── korrespondenzen.json
```

### Katalog-Ansicht

Sortierbare Tabelle mit Suche (Titel/Signatur/PID), Filter (Sammlung, Typ, Qualitaet), Pagination (50/Seite), GAMS-Thumbnails. Klick auf Zeile oeffnet Viewer.

Spalten: Thumbnail | Titel | Signatur | PID | Sammlung | Typ | Sprache | Review | Qualitaet | Seiten

**"Typ"-Spalte zeigt TEI `classification`** (Verlagsvertraege, Tagebuecher, Korrespondenz) statt Prompt-Gruppe (Typoskript, Handschrift). Tooltip zeigt `objecttyp` (Typoskriptdurchschlag, Notizbuch). Die Prompt-Gruppe bleibt intern in der Pipeline, ist aber nicht mehr im UI sichtbar.

### Viewer

Side-by-Side Faksimile (GAMS) + Transkription. Metadaten-Bar (collapsible), Seiten-/Objekt-Navigation, GAMS-Link. Keyboard (Pfeiltasten, Esc), Touch-Swipe.

### Edit-Modus (nur lokal)

Inline-Editing von Transkription + Notes, localStorage-Persistenz, JSON-Export. Auf GitHub Pages ausgegraut mit Tooltip "Lokal starten: python -m http.server 8000".

---

## Was Lane 3 wissen muss

### build_viewer_data.py produziert jetzt 5 Dateien

Statt einer `data.json` erzeugt das Script `catalog.json` + `data/{collection}.json`. Der Katalog laedt nur die leichtgewichtigen Metadaten, Transkriptionen werden pro Sammlung on-demand nachgeladen.

### Neue Felder in catalog.json

Jedes Objekt hat jetzt:

```json
{
  "titleClean": "Verlagsvertrag Grasset",
  "signature": "SZ-AAP/L13.1",
  "classification": "Verlagsverträge",
  "objecttyp": "Typoskript",
  "thumbnail": "https://gams.uni-graz.at/o:szd.78/THUMBNAIL",
  "pageCount": 3,
  "verification": {
    "uncertainCount": 0,
    "illegibleCount": 1,
    "totalChars": 4520,
    "emptyPages": 0,
    "avgCharsPerPage": 1506,
    "vlmConfidence": "high"
  }
}
```

`classification` und `objecttyp` werden aus TEI-XML via `parse_tei_for_object()` geholt. Fallback fuer Korrespondenzen (keine TEI-Classification): "Korrespondenz"/"Brief".

### quality_signals-Integration ist vorbereitet

Das Frontend ist bereit fuer das `quality_signals`-Objekt aus Lane 2 / Abschnitt 2.5:

**Im Katalog:**
- Spalte "Review" zeigt `needs_review` als farbigen Dot (Burgundy = Review, Gruen = OK)
- Sortierbar (Review-Objekte oben)
- Tooltip zeigt `needs_review_reasons` als Liste
- Checkbox-Filter "Nur Review" (erscheint automatisch wenn Daten vorhanden)

**Im Viewer:**
- Qualitaets-Bereich zeigt: `needs_review` + Gruende, `marker_density`, `empty_pages`, `language_match`, `total_chars`/`total_words`
- Seiten-Anomalie-Marker (Warning-Icon) bei `page_length_anomalies`

**Graceful Degradation:** Wenn `quality_signals` fehlt, wird nichts angezeigt, keine Fehler. Das Frontend faellt auf die bisherige `verification`-Anzeige zurueck.

### Was Lane 3 liefern muss

1. **`quality_signals`-Objekt im Ergebnis-JSON** (Spezifikation: verification-concept.md §2.5)
2. **`needs_review` und `needsReviewReasons` als Top-Level-Felder in catalog.json** (build_viewer_data.py propagiert sie)

Das Frontend liest:
- `obj.needsReview` (boolean) — fuer Katalog-Spalte und Filter
- `obj.needsReviewReasons` (string[]) — fuer Tooltip
- `obj.quality_signals` (ganzes Objekt) — fuer Viewer-Detailansicht
- `obj.quality_signals.page_length_anomalies` (int[]) — fuer Seiten-Marker

---

## Was Lane 2 wissen muss

### Aktuelle Verifikation im Frontend (Zwischenloesung)

Solange `quality_signals` nicht existiert, zeigt das Frontend die einfache `verification` aus build_viewer_data.py:
- Marker-Count: [?] und [...] aus Transkriptionstext gezaehlt
- VLM-Selbsteinschaetzung: als "schwaches Signal" gelabelt
- Textstatistik: Zeichenzahl, Leerseiten, Zeichen/Seite

### Befunde aus 16 Objekten

- 12/16 haben 0 Marker (uninformativ)
- 1x `[...]` (Tagebuch 1918), 1x `[?]` (Certificate of Marriage)
- Alle VLM-Einschaetzungen "high" (ausser 1x "medium" bei Konvolut)
- Bestaetigt Lane 2s Analyse: Marker-Dichte ist kein negatives Signal, nur ein positives

### TEI-Klassifikation verfuegbar

Die Felder `classification` und `objecttyp` sind jetzt im Frontend sichtbar. Sie koennen fuer die Sampling-Strategie (§1.3) genutzt werden: statt nach Prompt-Gruppe zu samplen, nach TEI-Klassifikation — das ist naeher an der inhaltlichen Varianz.

### Filter fuer QA-Workflow

Lane 2 kann im Viewer gezielt arbeiten:
- Sammlung → Typ filtern (z.B. nur "Verlagsvertraege" in Lebensdokumenten)
- Wenn `quality_signals` da sind: "Nur Review" filtert auf problematische Objekte
- Objekt-Navigation (Prev/Next) erlaubt sequentielles Durcharbeiten der gefilterten Liste
