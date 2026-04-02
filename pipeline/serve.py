"""Lokaler Entwicklungsserver fuer SZD-HTR: Frontend + API fuer Reviews/Edits.

Ersetzt den VS Code Live Server. Schreibt Approve/Edit direkt in die Pipeline-JSONs.

Usage:
  python pipeline/serve.py              # Port 8000
  python pipeline/serve.py --port 5501  # Anderer Port

API-Endpunkte (nur lokal):
  POST /api/approve  — Objekt als geprueft markieren
  POST /api/edit     — Editierte Seiten speichern + approve
  GET  /api/status   — Server-Status (Frontend erkennt lokalen Server)
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Pipeline imports
sys.path.insert(0, str(Path(__file__).parent))
from config import COLLECTIONS, RESULTS_BASE

DOCS_DIR = Path(__file__).parent.parent / "docs"
DEFAULT_REVIEWER = "Christopher Pollin"
_VALID_OBJECT_ID = re.compile(r"^o_szd\.[0-9a-zA-Z]+$")
_VALID_COLLECTION = frozenset(COLLECTIONS.keys())


def _validate_ids(object_id: str, collection: str) -> str | None:
    """Return error message if IDs are invalid, None if OK."""
    if not _VALID_OBJECT_ID.match(object_id):
        return f"Ungueltige object_id: {object_id}"
    if collection not in _VALID_COLLECTION:
        return f"Ungueltige collection: {collection}"
    return None


def find_result_file(object_id: str, collection: str, model: str = "") -> Path | None:
    """Find the result JSON file for an object."""
    col_dir = RESULTS_BASE / collection
    if not col_dir.exists():
        return None

    # Try exact match with model
    if model:
        path = col_dir / f"{object_id}_{model}.json"
        if path.exists():
            return path

    # Fallback: glob
    candidates = list(col_dir.glob(f"{object_id}_*.json"))
    candidates = [c for c in candidates if not c.stem.endswith(
        ("_consensus", "_layout", "_gt_draft", "_judge_data")
    )]
    if len(candidates) == 1:
        return candidates[0]
    return None


def handle_approve(data: dict) -> dict:
    """Write review.status to the result JSON (approved or agent_verified)."""
    object_id = data.get("object_id", "")
    collection = data.get("collection", "")
    model = data.get("model", "")
    reviewer = data.get("reviewed_by", DEFAULT_REVIEWER)
    status = data.get("status", "approved")

    if status not in ("approved", "agent_verified"):
        return {"error": f"Ungültiger Status: {status}"}
    if not object_id or not collection:
        return {"error": "object_id und collection sind Pflichtfelder."}
    if err := _validate_ids(object_id, collection):
        return {"error": err}

    result_path = find_result_file(object_id, collection, model)
    if not result_path:
        return {"error": f"Ergebnis-Datei nicht gefunden: {object_id} in {collection}"}

    result = json.loads(result_path.read_text(encoding="utf-8"))

    review = {
        "status": status,
        "edited_pages": result.get("review", {}).get("edited_pages", []),
        "reviewed_by": reviewer,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    if status == "agent_verified":
        review["agent_model"] = data.get("agent_model", "claude-opus-4-6")
        if "errors_found" in data:
            review["errors_found"] = data["errors_found"]
        if "estimated_accuracy" in data:
            review["estimated_accuracy"] = data["estimated_accuracy"]

    result["review"] = review

    try:
        backup_path = result_path.with_suffix(".json.bak")
        shutil.copy2(result_path, backup_path)
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        return {"error": f"Schreibfehler: {e}"}

    print(f"  {status.upper()}: {result_path.name} (by {reviewer})")
    return {"ok": True, "file": result_path.name, "status": status}


def handle_edit(data: dict) -> dict:
    """Write edited pages + review status to the result JSON."""
    object_id = data.get("object_id", "")
    collection = data.get("collection", "")
    model = data.get("model", "")
    reviewer = data.get("reviewed_by", DEFAULT_REVIEWER)
    pages = data.get("pages", [])

    if not object_id or not collection:
        return {"error": "object_id und collection sind Pflichtfelder."}
    if err := _validate_ids(object_id, collection):
        return {"error": err}

    result_path = find_result_file(object_id, collection, model)
    if not result_path:
        return {"error": f"Ergebnis-Datei nicht gefunden: {object_id} in {collection}"}

    result = json.loads(result_path.read_text(encoding="utf-8"))
    result_pages = result.get("result", {}).get("pages", [])
    result_page_map = {rp.get("page"): rp for rp in result_pages}

    edited_page_nums = []
    for export_page in pages:
        page_num = export_page.get("page")
        rp = result_page_map.get(page_num)
        if not rp:
            continue
        if export_page.get("transcription") is not None:
            rp["transcription"] = export_page["transcription"]
        if export_page.get("notes") is not None:
            rp["notes"] = export_page["notes"]
        edited_page_nums.append(page_num)

    result["review"] = {
        "status": "approved",
        "edited_pages": edited_page_nums,
        "reviewed_by": reviewer,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        backup_path = result_path.with_suffix(".json.bak")
        shutil.copy2(result_path, backup_path)
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        return {"error": f"Schreibfehler: {e}"}

    print(f"  EDITED: {result_path.name} -- {len(edited_page_nums)} Seite(n) (by {reviewer})")
    return {
        "ok": True,
        "file": result_path.name,
        "status": "approved",
        "edited_pages": edited_page_nums,
    }


def rebuild_viewer_data() -> dict:
    """Run build_viewer_data.py to refresh docs/data/."""
    try:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "build_viewer_data.py")],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode == 0:
            print("  REBUILD: Viewer-Daten aktualisiert")
            return {"ok": True, "output": proc.stdout[-500:] if proc.stdout else ""}
        else:
            print(f"  REBUILD FEHLER: {proc.stderr[-300:]}")
            return {"error": proc.stderr[-300:]}
    except Exception as e:
        return {"error": str(e)}


_ALLOWED_HOSTS = {"localhost", "127.0.0.1"}


class SZDHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves docs/ and handles API requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def _check_host(self) -> bool:
        """Reject requests with unexpected Host header (DNS rebinding protection)."""
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in _ALLOWED_HOSTS:
            self.send_error(403, "Forbidden: invalid Host header")
            return False
        return True

    def do_GET(self):
        if not self._check_host():
            return
        if self.path == "/api/status":
            self._json_response({"local": True, "server": "szd-htr-serve"})
        else:
            super().do_GET()

    def do_POST(self):
        if not self._check_host():
            return
        if not self.path.startswith("/api/"):
            self.send_error(404)
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._json_response({"error": "Ungültiges JSON"}, status=400)
            return

        # Route
        if self.path == "/api/approve":
            result = handle_approve(data)
        elif self.path == "/api/edit":
            result = handle_edit(data)
        elif self.path == "/api/rebuild":
            result = rebuild_viewer_data()
        else:
            self._json_response({"error": f"Unbekannter Endpunkt: {self.path}"}, status=404)
            return

        status = 400 if "error" in result else 200
        self._json_response(result, status=status)

    def _json_response(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default access logs for static files, show API calls."""
        if "/api/" in (args[0] if args else ""):
            super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(
        description="SZD-HTR Lokaler Entwicklungsserver mit Review-API"
    )
    parser.add_argument("--port", "-p", type=int, default=8000,
                        help="Port (Default: 8000)")
    parser.add_argument("--rebuild", action="store_true",
                        help="Viewer-Daten beim Start neu bauen")
    args = parser.parse_args()

    if args.rebuild:
        print("Baue Viewer-Daten...")
        rebuild_viewer_data()

    server = HTTPServer(("127.0.0.1", args.port), SZDHandler)
    print(f"\nSZD-HTR Dev-Server laeuft auf http://127.0.0.1:{args.port}")
    print(f"  Frontend:   http://127.0.0.1:{args.port}/index.html")
    print(f"  API Status: http://127.0.0.1:{args.port}/api/status")
    print(f"  Docs-Dir:   {DOCS_DIR}")
    print(f"\nAPI-Endpunkte:")
    print(f"  POST /api/approve  -- Objekt als geprueft markieren")
    print(f"  POST /api/edit     -- Editierte Seiten speichern")
    print(f"  POST /api/rebuild  -- Viewer-Daten neu bauen")
    print(f"\nStrg+C zum Beenden.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.")
        server.server_close()


if __name__ == "__main__":
    main()
