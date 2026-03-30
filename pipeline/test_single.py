"""Test: Einzelobjekt-Transkription mit Gemini Vision."""

import json
import os
import re
import sys
from pathlib import Path

from google import genai

# --- Config ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
MODEL = os.environ.get("HTR_MODEL", "gemini-3.1-flash-lite-preview")
BACKUP_ROOT = Path(os.environ.get(
    "SZD_BACKUP_ROOT",
    "C:/Users/Chrisi/Documents/PROJECTS/szd-backup/data/lebensdokumente"
))
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"
RESULTS_DIR = PROJECT_ROOT / "results" / "test"


def load_prompt(filename: str) -> str:
    """Load prompt text from a markdown file, extracting content from code blocks."""
    path = PROMPTS_DIR / filename
    text = path.read_text(encoding="utf-8")
    # Extract content between ``` markers
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    return blocks[0].strip() if blocks else text.strip()


# --- Prompts (loaded from files) ---
SYSTEM_PROMPT = load_prompt("system.md")

GROUP_PROMPTS = {
    "kurztext": load_prompt("group_d_kurztext.md"),
    "handschrift": load_prompt("group_a_handschrift.md"),
    "typoskript": load_prompt("group_b_typoskript.md"),
    "formular": load_prompt("group_c_formular.md"),
    "tabellarisch": load_prompt("group_e_tabellarisch.md"),
}

# --- Test Cases ---
TEST_CASES = {
    "theaterkarte": {
        "object_id": "o_szd.161",
        "group": "kurztext",
        "context": """## Dieses Dokument

- Titel: Theaterkarte zur Uraufführung von „Jeremias" 1918
- Signatur: SZ-SDP/L2
- Datum: 27. Febr. 1918
- Sprache: Deutsch
- Objekttyp: Eintrittskarte
- Umfang: 1 Blatt (3 Scans: Vorderseite, Rückseite, Gesamtansicht)
- Schreibinstrument: Bleistift
- Hand: Friderike Zweig
- Anmerkungen: „Jerem. Uraufführung" von Friderike Zweigs Hand auf der Rückseite""",
    },
    "certificate": {
        "object_id": "o_szd.160",
        "group": "formular",
        "context": """## Dieses Dokument

- Titel: Certified Copy of an Entry of Marriage
- Signatur: SZ-SDP/L1
- Datum: Sixth September 1939
- Sprache: Englisch
- Objekttyp: Typoskript (beglaubigte Kopie einer Heiratsurkunde)
- Umfang: 1 Blatt
- Schreibinstrument: Schwarze Tinte
- Hand: Fremde Hand
- Anmerkungen: Beglaubigte Kopie vom 3. September 1980""",
    },
    "vertrag_grasset": {
        "object_id": "o_szd.78",
        "group": "typoskript",
        "context": """## Dieses Dokument

- Titel: Verlagsvertrag Grasset
- Signatur: SZ-AAP/L13.1
- Datum: le Premier Février, mil neuf cent trente deux (1. Februar 1932)
- Sprache: Französisch
- Objekttyp: Typoskript (Verlagsvertrag in Formularform)
- Umfang: 1 Blatt
- Schreibinstrument: Violettes Farbband, violette und schwarze Tinte
- Hand: Stefan Zweig, fremde Hand
- Anmerkungen: Maschinschriftliche Eintragungen in Formular, recto mit aufgeklebter Stempelmarke und mehrfach gestempelt, verso mit eigenhändiger Aufschrift „lu et approuvé" und Unterschrift von Stefan Zweig und unbekannt""",
    },
    "tagebuch_1918": {
        "object_id": "o_szd.72",
        "group": "handschrift",
        "max_images": 5,
        "context": """## Dieses Dokument

- Titel: Tagebuch 1918
- Signatur: SZ-AAP/L6
- Datum: [1918]
- Sprache: Deutsch
- Objekttyp: Notizbuch
- Umfang: 19 Blatt beschrieben (39 Scans)
- Schreibinstrument: Violette Tinte
- Hand: Stefan Zweig
- Anmerkungen: Tagebuch aus dem letzten Kriegsjahr. Hier werden nur die ersten Seiten transkribiert (Testlauf).""",
    },
}


def load_images(object_id: str, max_images: int = 0) -> list[tuple[str, bytes]]:
    """Load images for an object from the backup directory."""
    img_dir = BACKUP_ROOT / object_id / "images"
    if not img_dir.exists():
        print(f"FEHLER: Bildverzeichnis nicht gefunden: {img_dir}")
        sys.exit(1)
    img_paths = sorted(img_dir.glob("IMG_*.jpg"), key=lambda p: int(p.stem.split("_")[1]))
    if not img_paths:
        print(f"FEHLER: Keine Bilder gefunden in {img_dir}")
        sys.exit(1)
    images = []
    for img_path in img_paths:
        images.append((img_path.name, img_path.read_bytes()))
        if max_images and len(images) >= max_images:
            break
    return images


def run_test(test_name: str):
    if test_name not in TEST_CASES:
        print(f"FEHLER: Unbekannter Test '{test_name}'")
        print(f"Verfügbar: {', '.join(TEST_CASES.keys())}")
        sys.exit(1)

    if not GOOGLE_API_KEY:
        print("FEHLER: GOOGLE_API_KEY nicht gesetzt.")
        print("  export GOOGLE_API_KEY=AIza...")
        sys.exit(1)

    tc = TEST_CASES[test_name]
    max_img = tc.get("max_images", 0)
    images = load_images(tc["object_id"], max_img)
    print(f"Objekt: {tc['object_id']} — {len(images)} Bilder geladen")

    # Build prompt
    group_prompt = GROUP_PROMPTS[tc["group"]]
    context = tc["context"]
    user_prompt = f"{group_prompt}\n\n{context}\n\nTranskribiere die folgenden {len(images)} Faksimile-Scans."

    # Build content parts for Gemini
    parts = []
    for name, img_bytes in images:
        parts.append(genai.types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        parts.append(f"[{name}]")
    parts.append(user_prompt)

    # Call Gemini
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print(f"Sende an {MODEL}...")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
            ),
        )
    except Exception as e:
        print(f"FEHLER bei API-Aufruf: {e}")
        sys.exit(1)

    result_text = response.text
    print("\n" + "=" * 60)
    print("ERGEBNIS")
    print("=" * 60)
    print(result_text)

    # Save result
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{test_name}_{MODEL}.json"
    out_path.write_text(result_text, encoding="utf-8")
    print(f"\nGespeichert: {out_path}")


if __name__ == "__main__":
    test = sys.argv[1] if len(sys.argv) > 1 else "theaterkarte"
    run_test(test)
