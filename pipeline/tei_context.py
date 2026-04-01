"""TEI-Parser: Automatische Kontext-Generierung aus TEI-XML-Metadaten."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def _extract_bibl_metadata(bibl) -> dict:
    """Extract metadata from a single TEI biblFull element."""
    def text(xpath: str) -> str:
        el = bibl.find(xpath, NS)
        return el.text.strip() if el is not None and el.text else ""

    date_el = bibl.find(".//tei:origDate", NS)
    date = ""
    if date_el is not None:
        date = date_el.text.strip() if date_el.text else date_el.get("when", "")

    objecttyp = ""
    for t in bibl.findall('.//tei:term[@type="objecttyp"]', NS):
        objecttyp = t.text or ""
        break

    extent = ""
    for m in bibl.findall('.//tei:measure[@type="leaf"]', NS):
        if m.text:
            extent = m.text.strip()
            break

    instrument = ""
    for mat in bibl.findall(".//tei:material", NS):
        if "WritingInstrument" in mat.get("ana", ""):
            instrument = mat.text.strip() if mat.text else ""
            break

    return {
        "title": text(".//tei:titleStmt/tei:title"),
        "signature": text('.//tei:msIdentifier/tei:idno[@type="signature"]'),
        "date": date,
        "language": text(".//tei:textLang/tei:lang"),
        "objecttyp": objecttyp,
        "extent": extent,
        "writing_instrument": instrument,
        "hand": text(".//tei:handDesc/tei:ab"),
        "notes": text(".//tei:notesStmt/tei:note"),
        "classification": text('.//tei:keywords/tei:term[@type="classification"]'),
    }


def parse_tei_for_object(tei_file: Path, pid: str) -> dict | None:
    """Extract metadata for a single object from a TEI file by its PID."""
    tree = ET.parse(tei_file)
    root = tree.getroot()
    for bibl in root.findall(".//tei:biblFull", NS):
        pid_el = bibl.find('.//tei:altIdentifier/tei:idno[@type="PID"]', NS)
        if pid_el is not None and pid_el.text == pid:
            return _extract_bibl_metadata(bibl)
    return None


def list_tei_objects(tei_file: Path) -> dict[str, dict]:
    """List all objects with PIDs from a TEI file. Returns {pid: metadata}."""
    tree = ET.parse(tei_file)
    root = tree.getroot()
    result = {}
    for bibl in root.findall(".//tei:biblFull", NS):
        pid_el = bibl.find('.//tei:altIdentifier/tei:idno[@type="PID"]', NS)
        if pid_el is None or not pid_el.text:
            continue
        pid = pid_el.text.strip()
        if not pid.startswith("o:szd.") or not pid.split(".")[-1].isdigit():
            continue
        result[pid] = _extract_bibl_metadata(bibl)
    return result


def context_from_backup_metadata(metadata_path: Path) -> dict:
    """Fallback: Extract context from backup metadata.json (for Korrespondenzen)."""
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    return {
        "title": data.get("title", ""),
        "signature": data.get("signature", "") or "",
        "date": "",
        "language": data.get("language", ""),
        "objecttyp": "Brief",
        "extent": f"{len(data.get('images', []))} Scans",
        "writing_instrument": "",
        "hand": "",
        "notes": "",
        "classification": "Korrespondenz",
    }


def format_context(metadata: dict, page_info: str = "") -> str:
    """Format metadata dict into a context string for the prompt."""
    lines = ["## Dieses Dokument", ""]
    field_map = [
        ("Titel", "title"),
        ("Signatur", "signature"),
        ("Datum", "date"),
        ("Sprache", "language"),
        ("Objekttyp", "objecttyp"),
        ("Umfang", "extent"),
        ("Schreibinstrument", "writing_instrument"),
        ("Hand", "hand"),
        ("Anmerkungen", "notes"),
    ]
    for label, key in field_map:
        val = metadata.get(key, "")
        if val:
            lines.append(f"- {label}: {val}")
    if page_info:
        lines.append("")
        lines.append(page_info)
    return "\n".join(lines)


def resolve_group(metadata: dict, collection: str) -> str:
    """Auto-assign prompt group based on TEI metadata and collection."""
    if collection == "korrespondenzen":
        return "korrespondenz"

    otyp = (metadata.get("objecttyp") or "").lower()
    classif = (metadata.get("classification") or "").lower()

    if "korrekturfahne" in otyp or "druckfahne" in otyp:
        return "korrekturfahne"
    if "zeitungsausschnitt" in otyp:
        return "zeitungsausschnitt"
    if "konvolut" in otyp:
        return "konvolut"
    if "notizbuch" in otyp or ("manuskript" in otyp and "tagebü" in classif):
        return "handschrift"
    if "manuskript" in otyp:
        return "handschrift"
    # Formular-Checks vor generischem Typoskript — ein Typoskript mit
    # Klassifikation "Rechtsdokumente" ist semantisch ein Formular.
    if any(x in otyp for x in ("urkunde", "passkopie", "bescheid", "nachweis", "geburtsschein")):
        return "formular"
    if any(x in classif for x in ("rechtsdokumente", "finanzen")):
        return "formular"
    if "typoskript" in otyp or "durchschlag" in otyp:
        return "typoskript"
    if any(x in otyp for x in ("register", "kalender", "adressbuch", "kontorbuch")):
        return "tabellarisch"
    if any(x in classif for x in ("verzeichnisse", "kalender")):
        return "tabellarisch"
    if any(x in otyp for x in ("karte", "eintrittskarte", "briefumschlag")):
        return "kurztext"
    if any(x in classif for x in ("diverses", "büromaterialien")):
        return "kurztext"

    return "handschrift"
