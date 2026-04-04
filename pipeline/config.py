"""Gemeinsame Konfiguration für die SZD-HTR-Pipeline."""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env automatisch laden
load_dotenv()

# --- Pfade ---
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_BASE = PROJECT_ROOT / "results"
RESULTS_DIR = RESULTS_BASE / "test"  # Legacy Test-Ergebnisse
PROMPTS_DIR = SCRIPT_DIR / "prompts"
BACKUP_ROOT = Path(os.environ.get(
    "SZD_BACKUP_ROOT",
    "C:/Users/Chrisi/Documents/PROJECTS/szd-backup/data"
))

# --- API ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
MODEL = os.environ.get("HTR_MODEL", "gemini-3.1-flash-lite-preview")
LAYOUT_MODEL = os.environ.get("HTR_LAYOUT_MODEL", "gemini-3-flash-preview")

# --- Sammlungen ---
COLLECTIONS = {
    "lebensdokumente": {"subdir": "lebensdokumente", "tei": "szd_lebensdokumente_tei.xml"},
    "werke":           {"subdir": "facsimiles",       "tei": "szd_werke_tei.xml"},
    "aufsatzablage":   {"subdir": "aufsatz",          "tei": "szd_aufsatzablage_tei.xml"},
    "korrespondenzen": {"subdir": "korrespondenzen",  "tei": "szd_korrespondenzen_tei.xml"},
}

# --- Batch ---
BATCH_DELAY = float(os.environ.get("HTR_BATCH_DELAY", "2.0"))
CHUNK_SIZE = int(os.environ.get("HTR_CHUNK_SIZE", "20"))

# --- Layout-Analyse Schwellenwerte ---
LAYOUT_MIN_REGION_WIDTH_PCT = 0.5   # Regionen schmaler als 0.5% = Rauschen
LAYOUT_MIN_REGION_HEIGHT_PCT = 0.3  # Regionen flacher als 0.3% = Rauschen
LAYOUT_MAX_REGION_PCT = 95.0        # Regionen groesser als 95% = VLM-Halluzination


def results_dir_for(collection: str) -> Path:
    """Return results directory for a collection, creating it if needed."""
    d = RESULTS_BASE / collection
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- Prompt-Gruppen ---
GROUP_LABELS = {
    "kurztext":          ("D", "Kurztext"),
    "handschrift":       ("A", "Handschrift"),
    "typoskript":        ("B", "Typoskript"),
    "formular":          ("C", "Formular"),
    "tabellarisch":      ("E", "Tabellarisch"),
    "korrekturfahne":    ("F", "Korrekturfahne"),
    "konvolut":          ("G", "Konvolut"),
    "zeitungsausschnitt": ("H", "Zeitungsausschnitt"),
    "korrespondenz":     ("I", "Korrespondenz"),
}
