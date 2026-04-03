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
            lang = mat.get("{http://www.w3.org/XML/1998/namespace}lang", "")
            if lang == "en":
                continue
            if mat.text:
                instrument = " ".join(mat.text.split())  # normalize whitespace
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


def _extract_full_metadata(bibl) -> dict:
    """Extract complete metadata for Page-JSON v0.2 descriptive_metadata block.

    Extends _extract_bibl_metadata() with: creators+GND, holding+GND,
    provenance, origPlace, writing_material, dimensions, binding,
    inscriptions, correspondence context.
    """
    base = _extract_bibl_metadata(bibl)

    def text_de(xpath: str) -> str:
        """Extract German-language text (first match without xml:lang='en')."""
        for el in bibl.findall(xpath, NS):
            lang = el.get("{http://www.w3.org/XML/1998/namespace}lang", "")
            if lang == "en":
                continue
            if el.text and el.text.strip():
                return el.text.strip()
        return ""

    def all_text_de(xpath: str) -> list[str]:
        """Extract all German-language text entries."""
        results = []
        for el in bibl.findall(xpath, NS):
            lang = el.get("{http://www.w3.org/XML/1998/namespace}lang", "")
            if lang == "en":
                continue
            if el.text and el.text.strip():
                results.append(el.text.strip())
        return results

    def _parse_persname(el) -> str:
        """Extract person name from persName element (forename + surname or itertext)."""
        forename = el.find("tei:forename", NS)
        surname = el.find("tei:surname", NS)
        if surname is not None:
            parts = []
            if forename is not None and forename.text:
                parts.append(forename.text.strip())
            if surname.text:
                parts.append(surname.text.strip())
            return " ".join(parts)
        return " ".join(el.itertext()).strip()

    # Creators (author + editor with GND)
    creators = []
    for author in bibl.findall(".//tei:titleStmt/tei:author", NS):
        pn = author.find("tei:persName", NS)
        if pn is not None:
            name = _parse_persname(pn)
            if name:
                entry = {"name": name, "role": "author"}
                ref = pn.get("ref", "")
                if ref:
                    entry["gnd"] = ref
                creators.append(entry)
    for editor in bibl.findall(".//tei:titleStmt/tei:editor", NS):
        pn = editor.find("tei:persName", NS)
        if pn is not None:
            name = _parse_persname(pn)
            if name:
                role = editor.get("role", "editor")
                entry = {"name": name, "role": role}
                ref = pn.get("ref", "")
                if ref:
                    entry["gnd"] = ref
                creators.append(entry)

    # Holding (repository + country + settlement + GND)
    holding = {}
    ms = bibl.find(".//tei:msIdentifier", NS)
    if ms is not None:
        repo_el = ms.find("tei:repository", NS)
        if repo_el is not None:
            repo_text = " ".join(repo_el.itertext()).strip()
            repo_text = " ".join(repo_text.split())  # normalize whitespace
            if repo_text:
                holding["repository"] = repo_text
            ref = repo_el.get("ref", "")
            if ref:
                holding["repository_gnd"] = ref
        country_el = ms.find("tei:country", NS)
        if country_el is not None and country_el.text:
            holding["country"] = country_el.text.strip()
        settlement_el = ms.find("tei:settlement", NS)
        if settlement_el is not None and settlement_el.text:
            holding["settlement"] = settlement_el.text.strip()

    # Provenance + Acquisition
    provenance = all_text_de(".//tei:history/tei:provenance/tei:ab")
    for acq_text in all_text_de(".//tei:history/tei:acquisition/tei:ab"):
        provenance.append(f"Erwerb: {acq_text}")

    # Origin place
    origin_place = text_de(".//tei:origPlace")

    # Writing material (separate from writing instrument)
    writing_material = ""
    for mat in bibl.findall(".//tei:material", NS):
        ana = mat.get("ana", "")
        lang = mat.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        if "WritingMaterial" in ana and lang != "en" and mat.text:
            writing_material = mat.text.strip()
            break

    # Dimensions
    dimensions = ""
    for m in bibl.findall('.//tei:measure[@type="format"]', NS):
        if m.text and m.text.strip():
            dimensions = m.text.strip()
            break

    # Binding
    binding = text_de(".//tei:bindingDesc/tei:binding/tei:ab")

    # Inscriptions (docEdition)
    inscriptions = []
    for de in bibl.findall(".//tei:docEdition", NS):
        lang = de.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        if lang != "en" and de.text and de.text.strip():
            inscriptions.append(de.text.strip())

    # Hands as array (split existing hand string on comma)
    hands = []
    hand_str = base.get("hand", "")
    if hand_str:
        hands = [h.strip() for h in hand_str.split(",") if h.strip()]

    # Rights (from backup, not TEI — added in export_page_json.py)

    # Subject = classification as array
    subject = []
    classif = base.get("classification", "")
    if classif:
        subject.append(classif)

    return {
        **base,
        "creators": creators,
        "holding": holding,
        "provenance": provenance,
        "origin_place": origin_place,
        "writing_material": writing_material,
        "dimensions": dimensions,
        "binding": binding,
        "inscriptions": inscriptions,
        "hands": hands,
        "subject": subject,
    }


def parse_tei_full_metadata(tei_file: Path, pid: str) -> dict | None:
    """Extract full metadata for Page-JSON v0.2 descriptive_metadata."""
    tree = ET.parse(tei_file)
    root = tree.getroot()
    for bibl in root.findall(".//tei:biblFull", NS):
        pid_el = bibl.find('.//tei:altIdentifier/tei:idno[@type="PID"]', NS)
        if pid_el is not None and pid_el.text == pid:
            return _extract_full_metadata(bibl)
    return None


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
