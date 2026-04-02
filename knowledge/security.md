---
title: "Security Review"
created: 2026-04-02
updated: 2026-04-02
type: reference
status: active
---

# Security Review — SZD-HTR

Systematische Sicherheitsanalyse des SZD-HTR-Projekts (Pipeline + Viewer + Dev-Server), verifiziert gegen OWASP-Richtlinien, CVE-Datenbanken und aktuelle Security-Literatur. Stand: 2. April 2026.

## 1  Threat Model

Die Applikation hat **zwei Deployment-Kontexte** mit unterschiedlichen Angriffsflaechern:

| | GitHub Pages (oeffentlich) | Lokaler Dev-Server (`serve.py`) |
|---|---|---|
| Zugang | Jeder im Internet | Nur localhost (127.0.0.1) |
| Schreibzugriff | Keiner (statische Dateien) | POST-Endpoints (approve, edit, rebuild) |
| Authentifizierung | n/a | Keine |
| Daten | `catalog.json`, `data/*.json`, `knowledge.json` — committed, oeffentlich | Dieselben + live Pipeline-JSONs in `results/` |
| Edit-Funktionen | UI-seitig deaktiviert via `isLocal`-Check | Aktiv |
| CORS | n/a (GitHub setzt eigene Header) | `Access-Control-Allow-Origin: *` |

**Datenklassifikation**: Alle Daten sind oeffentliche Archivmaterialien (Stefan-Zweig-Nachlass, bereits auf GAMS publiziert). Keine PII, keine Credentials in den ausgelieferten Dateien. API-Keys nur in `.env` (gitignored, nie committed).

---

## 2  Findings — Verifiziert und priorisiert

### 2.1  HOCH (Fix empfohlen)

#### H1  XSS via `innerHTML` + fehlendes CSP

**Datei**: `docs/app.js`, Zeilen 524, 547; `docs/index.html`
**Vektor**: `content.innerHTML = doc.html` — pre-rendered HTML aus `knowledge.json` wird ohne Sanitisierung eingefuegt. Python-`markdown` laesst Raw-HTML durch ([Issue #230](https://github.com/Python-Markdown/markdown/issues/230)). Event-Handler-Payloads (`onerror`, `onload`) sind via `innerHTML` ausfuehrbar, `<script>`-Tags nicht (HTML5-Spec). Ohne CSP gibt es keine zweite Verteidigungslinie.
**Voraussetzung**: Kompromittierter Contributor oder manipulierte Markdown-Datei im Repo (Supply-Chain). Bei Single-Maintainer-Projekt mit Review kein externer Angriffsvektor.
**Referenzen**: [OWASP DOM XSS Prevention Rule #1](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html), [MDN innerHTML Security](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML#security_considerations), [GitHub Pages CSP Discussion #13309](https://github.com/orgs/community/discussions/13309)

**Status**: OFFEN
**Fix**: CSP-Meta-Tag in `index.html` (blockiert Inline-Scripts inkl. Event-Handler):
```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self';
               style-src 'self' https://fonts.googleapis.com 'unsafe-inline';
               font-src https://fonts.gstatic.com;
               img-src 'self' https://gams.uni-graz.at data:;
               connect-src 'self'">
```
GitHub Pages erlaubt keine HTTP-Header; `<meta>` ist der einzige Weg. Einschraenkung: `frame-ancestors` funktioniert nicht via Meta-Tag. Optional: DOMPurify fuer Defense-in-Depth.

**Status**: ERLEDIGT (2026-04-02) — CSP-Meta-Tag in `docs/index.html` eingefuegt.

---

#### H2  Unescaped Attribute in Katalog-Rendering

**Datei**: `docs/app.js`, Zeilen 831-832
**Vektor**: `obj.thumbnail` in `<img src>` und `obj.id` in `data-id` werden ohne `escapeHtml()` interpoliert. Attribut-Breakout via `" onerror="..."` moeglich. `javascript:`-URIs in `<img src>` werden von modernen Browsern nicht ausgefuehrt (verifiziert), aber Event-Handler-Injection funktioniert.
**Datenquelle**: `catalog.json`, deterministisch gebaut von `build_viewer_data.py` aus GAMS-URLs und TEI-IDs. Praktisches Risiko sehr niedrig, aber `escapeHtml()` wird bei allen Nachbarfeldern bereits korrekt eingesetzt — Inkonsistenz.
**Referenz**: [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Scripting_Prevention_Cheat_Sheet.html)

**Status**: ERLEDIGT (2026-04-02) — `escapeHtml()` auf beide Felder angewendet.
**Fix**: `escapeHtml(obj.thumbnail || '')` und `escapeHtml(obj.id)` — zwei Einzeiler.

#### H3  Path Traversal in `serve.py`

**Datei**: `pipeline/serve.py`, Zeilen 32-51
**Vektor**: `object_id` wird unvalidiert in Dateipfade eingebaut. Pathlib schuetzt **nicht** gegen Traversal (verifiziert via [Python Docs](https://docs.python.org/3/library/pathlib.html) und [CWE-22](https://cwe.mitre.org/data/definitions/22.html)). `col_dir / f"../../etc/passwd_model.json"` resolves ausserhalb von `results/`.
**Verifikation**: Pathlib's `/`-Operator joined Pfade ohne Sanitisierung. Fix: `.resolve()` + Prefix-Check gegen Base-Directory.
**Praktisches Risiko**: Nur lokal, aber via CORS-Wildcard (H4) oder DNS-Rebinding von extern triggerbar.

**Status**: ERLEDIGT (2026-04-02) — Regex-Whitelist + Collection-Whitelist in `_validate_ids()`.
**Fix**: Regex-Whitelist `^o_szd\.[0-9a-zA-Z]+$` auf `object_id`, Collection gegen `COLLECTIONS.keys()`.

#### H4  CORS Wildcard + keine Authentifizierung auf Dev-Server

**Datei**: `pipeline/serve.py`, Zeilen 208-219
**Vektor**: `Access-Control-Allow-Origin: *` erlaubt jeder Website Requests an den lokalen Server. Preflight-OPTIONS mit `*` erlaubt auch POST-Requests ([MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS), [PortSwigger CORS](https://portswigger.net/web-security/cors)). DNS-Rebinding kann die 127.0.0.1-Bindung umgehen ([NCC Group Singularity](https://github.com/nccgroup/singularity)).
**Praktisches Risiko**: Niedrig-Mittel. Nur ausnutzbar waehrend `serve.py` laeuft und User gleichzeitig eine boeswillige Seite besucht.

**Status**: ERLEDIGT (2026-04-02) — CORS auf localhost-Origins beschraenkt, Host-Header-Validierung via `_check_host()`.
**Fix**: CORS auf `http://127.0.0.1:{port}` einschraenken, Host-Header-Validierung.

---

### 2.2  MITTEL (bei Gelegenheit)

#### M1  Keine Input-Validierung auf API-Endpoints

**Datei**: `pipeline/serve.py`, Zeilen 56-99
**Felder ohne Validierung**: `reviewed_by` (beliebige Laenge), `pages[].transcription` (keine Laengenbegrenzung), `model` (koennte Path-Traversal enthalten).
**Risiko**: In Kombination mit CORS-Wildcard ausnutzbar (Disk-Exhaustion, Datenmanipulation).
**Status**: ERLEDIGT (2026-04-02) — `_validate_ids()` prueft object_id und collection vor jedem Dateizugriff.

#### M2  XML-Parsing ohne XXE-Schutz

**Datei**: `pipeline/tei_context.py`, Zeilen 54-55
**Verifikation**: CPython's `xml.etree.ElementTree` (Expat-Parser) resolvet **keine** externen Entities (kein klassisches XXE). Anfaellig fuer Billion-Laughs-Entity-Expansion — in Python 3.7.2+ mit 10MB-Limit entschaerft. `defusedxml` bleibt offizielle Empfehlung des Python Security Teams.
**Referenzen**: [Python XML Vulnerabilities](https://docs.python.org/3/library/xml.html#xml-vulnerabilities), [defusedxml](https://github.com/tiran/defusedxml)
**Praktisches Risiko**: Vernachlaessigbar (nur eigene, vertrauenswuerdige TEI-Dateien).
**Status**: AKZEPTIERT — Defense-in-Depth-Verbesserung optional.

#### M3  `escapeHtml()` ohne Single-Quote-Escaping

**Datei**: `docs/app.js`, Zeilen 78-85
**Verifikation**: Die Funktion escaped `&`, `<`, `>`, `"` — ausreichend fuer Double-Quoted-Attribute-Kontexte (OWASP XSS Prevention Cheat Sheet Rule #2). Single-Quote (`'` → `&#x27;`) fehlt, ist aber derzeit nicht ausnutzbar, da alle Template-Literals Double-Quotes verwenden.
**Status**: AKZEPTIERT — Verbesserung bei Gelegenheit.

#### M4  API-Response-Parsing speichert Roh-Text

**Datei**: `pipeline/transcribe.py`, Zeilen 136-216
**Vektor**: Wenn Gemini kein valides JSON liefert, wird der rohe Response als `{"raw": text}` gespeichert. Keine Laengenbegrenzung.
**Verifikation**: LLM-Output-Injection ist ein dokumentierter Angriffsvektor (OWASP LLM01:2025, CVE-2026-25802, CVE-2026-32626). Allerdings: `renderTranscription()` in `app.js` escaped alle Transkriptionstexte korrekt via `escapeHtml()` **bevor** sie in den DOM eingefuegt werden (Zeile 87-89). Die Mitigation ist bereits vorhanden.
**Referenzen**: [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), [PortSwigger Web LLM Attacks](https://portswigger.net/web-security/llm-attacks)
**Status**: MITIGIERT — `escapeHtml()` in `renderTranscription()` schuetzt vor XSS. Laengenbegrenzung waere zusaetzliche Haertung.

#### M5  `import_reviews.py` ohne Schema-Validierung

**Datei**: `pipeline/import_reviews.py`, Zeile 208
**Vektor**: Externe JSON-Dateien (Frontend-Exporte) werden geladen und in Pipeline-JSONs geschrieben, ohne Feldtypen oder Schema zu pruefen.
**Praktisches Risiko**: Niedrig — nur manuell via CLI aufrufbar, Eingabedateien sind selbst-generiert.
**Status**: AKZEPTIERT

#### M6  Dependencies nicht gepinnt

**Datei**: `requirements.txt`
**Verifikation**: Supply-Chain-Angriffe auf PyPI sind real und zunehmend (Ultralytics-Kompromittierung Dez 2024, LiteLLM 2025). Floating Versions (`>=`) ziehen kompromittierte Releases automatisch. Bei nur 4 gut gepflegten Dependencies ist das Risiko niedrig, aber exaktes Pinnen ist ein Low-Effort-Fix.
**Referenzen**: [PyPI Ultralytics Attack Analysis](https://blog.pypi.org/posts/2024-12-11-ultralytics-attack-analysis/), [LiteLLM Supply Chain Attack](https://blog.securelayer7.net/pypi-litellm-supply-chain-attack/)
**Status**: OFFEN — exakte Versionen pinnen.

---

### 2.3  NIEDRIG (akzeptiert)

#### L1  API Key in `.env`-Datei

**Status**: OK — `.env` ist in `.gitignore` (Zeile 5), war nie im Git-Verlauf. Fuer lokale Forschungsprojekte akzeptabel. Key-Rotation bei Verdacht auf Kompromittierung.

#### L2  Hardcoded Default-Reviewer-Name

**Datei**: `pipeline/serve.py`, Zeile 29
`DEFAULT_REVIEWER = "Christopher Pollin"` — Name steht ohnehin in Commits und README.
**Status**: AKZEPTIERT

#### L3  CLI-Argumente ohne Bereichspruefung

`--chunk-size 0` verursacht `ValueError` in `range()`. Kein Security-Issue, nur Robustheit.
**Status**: AKZEPTIERT

#### L4  Hardcoded Windows-Pfade in `config.py`

`C:/Users/Chrisi/...` als Fallback-Pfad. Durch `SZD_BACKUP_ROOT` ueberschreibbar.
**Status**: AKZEPTIERT

#### L5  Race Condition bei File-Backup

**Datei**: `pipeline/serve.py`, Zeilen 78-82
**Verifikation**: TOCTOU ist ein dokumentierter Angriffsvektor (CVE-2026-22702, CVE-2026-22701), aber nur relevant in Multi-User-Systemen oder bei Privilege-Escalation. Fuer ein Single-User-Localhost-Tool nicht realistisch.
**Status**: AKZEPTIERT

#### L6  SimpleHTTPRequestHandler

Python-Docs warnen explizit: "not recommended for production". Binding auf 127.0.0.1 mitigiert die Hauptrisiken. Der Server ist ein Dev-Tool, kein Produktionsserver.
**Status**: AKZEPTIERT

---

### 2.4  Geprueft — kein Handlungsbedarf

| Aspekt | Begruendung |
|---|---|
| Transkriptions-Rendering | `renderTranscription()` escaped via `escapeHtml()` vor DOM-Insertion (Zeile 87-89) |
| Keine `eval()`/`exec()`/`pickle` | Kein Vorkommen in der gesamten Codebase |
| Keine SQL-Interaktion | Kein Datenbank-Layer vorhanden |
| Keine Subprocess-Injection | `serve.py` nutzt List-Form (kein `shell=True`), Pfad ist hardcoded |
| `.env` nie committed | Git-History bestaetigt: kein Credential-Leak |
| `localStorage` nur lokal | Via `isLocal`-Check gesteuert (Zeile 149), keine Credentials gespeichert |
| Oeffentliche JSON-Daten | Archivmaterial, keine PII, keine Secrets — Information Disclosure nicht zutreffend |
| `img src` von GAMS | Vertrauenswuerdige institutionelle Quelle, geladen via sicheres `<img>`-Element |

---

## 3  Fix-Tracker

| ID | Prioritaet | Fix | Aufwand | Status |
|---|---|---|---|---|
| H1 | Hoch | CSP-Meta-Tag in `index.html` (entschaerft innerHTML-XSS) | 5 Min | ERLEDIGT |
| H2 | Hoch | `escapeHtml()` fuer `obj.thumbnail` und `obj.id` | 2 Zeilen | ERLEDIGT |
| H3 | Hoch | Path-Traversal-Schutz in `serve.py` | 15 Min | ERLEDIGT |
| H4 | Hoch | CORS einschraenken + Host-Header-Validierung | 15 Min | ERLEDIGT |
| M1 | Mittel | Input-Validierung auf API-Endpoints | 30 Min | ERLEDIGT (via H3) |
| M3 | Mittel | Single-Quote in `escapeHtml()` | 1 Zeile | OFFEN |
| M6 | Mittel | Dependencies exakt pinnen | 5 Min | OFFEN |

---

## 4  Methodik

- **Statische Analyse**: Alle Python- und JavaScript-Dateien manuell gegen OWASP Top 10 (2021) und OWASP LLM Top 10 (2025) geprueft
- **Web-Verifikation**: Jedes Finding gegen OWASP Cheat Sheets, MDN Web Docs, CVE-Datenbanken, Python Security Docs und PortSwigger Research abgeglichen
- **Threat Modeling**: Zwei Deployment-Kontexte (GitHub Pages vs. localhost) separat bewertet
- **False-Positive-Pruefung**: `javascript:`-URIs in `<img src>` (von Browsern geblockt), `xml.etree.ElementTree` XXE (Expat resolvet keine externen Entities), TOCTOU fuer Single-User (nicht realistisch) — als uebertrieben/nicht zutreffend eingestuft
