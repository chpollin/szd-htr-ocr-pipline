"""SZD-HTR METS/MODS Export: OCR + Layout + TEI-Metadaten → METS-Container.

Generates METS XML containers with embedded MODS descriptive metadata,
fileSec (image + optional PAGE XML references), and physical structMap.
Follows the GAMS METS structure used at University of Graz.

Specification: knowledge/page-xml-mets-architecture.md
GAMS template:  {backup}/o_szd.*/mets.xml

Usage:
    python pipeline/export_mets.py o_szd.100 -c lebensdokumente
    python pipeline/export_mets.py -c werke
    python pipeline/export_mets.py --all
    python pipeline/export_mets.py --all --dry-run
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from config import BACKUP_ROOT, COLLECTIONS, DATA_DIR, MODEL, RESULTS_BASE, results_dir_for
from export_page_json import LANG_MAP
from export_pagexml import load_ocr_and_layout
from tei_context import parse_tei_full_metadata
from transcribe import discover_objects, find_ocr_file

# --- Namespaces ---

METS_NS = "http://www.loc.gov/METS/"
MODS_NS = "http://www.loc.gov/mods/v3"
XLINK_NS = "http://www.w3.org/1999/xlink"
DV_NS = "http://dfg-viewer.de/"
EXIF_NS = "http://ns.adobe.com/exif/1.0/"
XMPMETA_NS = "adobe:ns:meta/"

ET.register_namespace("mets", METS_NS)
ET.register_namespace("mods", MODS_NS)
ET.register_namespace("xlink", XLINK_NS)
ET.register_namespace("dv", DV_NS)
ET.register_namespace("exif", EXIF_NS)
ET.register_namespace("x", XMPMETA_NS)


def _normalize_lang(lang_str: str) -> tuple[str, str]:
    """Return (text_form, iso_code) for a language string."""
    if not lang_str:
        return ("", "und")
    text = lang_str.strip()
    key = text.lower()
    code = LANG_MAP.get(key, key[:2].lower())
    return (text, code)


# --- MODS Builder ---

def _build_mods(full_meta: dict, backup_meta: dict, pid: str) -> ET.Element:
    """Build a MODS element from TEI + backup metadata."""
    mods = ET.Element(f"{{{MODS_NS}}}mods")

    # titleInfo
    title_info = ET.SubElement(mods, f"{{{MODS_NS}}}titleInfo")
    title_el = ET.SubElement(title_info, f"{{{MODS_NS}}}title")
    title_el.text = (full_meta.get("title", "")
                     or backup_meta.get("title", "")
                     or backup_meta.get("label", ""))
    sig = full_meta.get("signature", "") or backup_meta.get("signature", "")
    if sig:
        note_el = ET.SubElement(title_info, f"{{{MODS_NS}}}note", type="signature")
        note_el.text = sig

    # name (creators with roles and GND, fallback to backup)
    creators = full_meta.get("creators", [])
    if not creators and backup_meta.get("author"):
        creators = [{"name": backup_meta["author"], "role": "author"}]
    for creator in creators:
        name_el = ET.SubElement(mods, f"{{{MODS_NS}}}name", type="personal")
        display = ET.SubElement(name_el, f"{{{MODS_NS}}}displayForm")
        display.text = creator.get("name", "")
        if creator.get("role"):
            role_el = ET.SubElement(name_el, f"{{{MODS_NS}}}role")
            role_term = ET.SubElement(role_el, f"{{{MODS_NS}}}roleTerm", type="text")
            role_term.text = creator["role"]
        if creator.get("gnd"):
            name_id = ET.SubElement(name_el, f"{{{MODS_NS}}}nameIdentifier", type="gnd")
            name_id.text = creator["gnd"]

    # language
    lang_text, lang_code = _normalize_lang(
        full_meta.get("language", "") or backup_meta.get("language", "")
    )
    if lang_text or lang_code != "und":
        lang_el = ET.SubElement(mods, f"{{{MODS_NS}}}language")
        if lang_text:
            lt = ET.SubElement(lang_el, f"{{{MODS_NS}}}languageTerm", type="text")
            lt.text = lang_text
        lt_code = ET.SubElement(lang_el, f"{{{MODS_NS}}}languageTerm",
                                authority="iso639-1", type="code")
        lt_code.text = lang_code

    # originInfo
    date_str = full_meta.get("date", "")
    origin_place = full_meta.get("origin_place", "")
    if date_str or origin_place:
        origin = ET.SubElement(mods, f"{{{MODS_NS}}}originInfo")
        if date_str:
            date_el = ET.SubElement(origin, f"{{{MODS_NS}}}dateCreated")
            date_el.text = date_str
        if origin_place:
            place_el = ET.SubElement(origin, f"{{{MODS_NS}}}place")
            place_term = ET.SubElement(place_el, f"{{{MODS_NS}}}placeTerm", type="text")
            place_term.text = origin_place

    # genre / subject
    objecttyp = full_meta.get("objecttyp", "")
    subjects = full_meta.get("subject", [])
    if objecttyp:
        genre_el = ET.SubElement(mods, f"{{{MODS_NS}}}genre")
        genre_el.text = objecttyp
    if subjects:
        subj_el = ET.SubElement(mods, f"{{{MODS_NS}}}subject")
        for s in subjects:
            topic = ET.SubElement(subj_el, f"{{{MODS_NS}}}topic")
            topic.text = s

    # physicalDescription
    phys_parts = []
    extent = full_meta.get("extent", "")
    dimensions = full_meta.get("dimensions", "")
    writing_instrument = full_meta.get("writing_instrument", "")
    writing_material = full_meta.get("writing_material", "")
    hands = full_meta.get("hands", [])

    if extent or dimensions or writing_instrument or writing_material or hands:
        phys = ET.SubElement(mods, f"{{{MODS_NS}}}physicalDescription")
        if extent:
            ext_el = ET.SubElement(phys, f"{{{MODS_NS}}}extent")
            ext_el.text = extent
        if dimensions:
            dim_el = ET.SubElement(phys, f"{{{MODS_NS}}}extent")
            dim_el.text = dimensions
        if writing_instrument:
            note_el = ET.SubElement(phys, f"{{{MODS_NS}}}note", type="writing_instrument")
            note_el.text = writing_instrument
        if writing_material:
            note_el = ET.SubElement(phys, f"{{{MODS_NS}}}note", type="writing_material")
            note_el.text = writing_material
        for hand in hands:
            note_el = ET.SubElement(phys, f"{{{MODS_NS}}}note", type="script")
            note_el.text = hand

    # location (holding + signature)
    holding = full_meta.get("holding", {})
    if holding.get("repository") or sig:
        loc = ET.SubElement(mods, f"{{{MODS_NS}}}location")
        if holding.get("repository"):
            phys_loc = ET.SubElement(loc, f"{{{MODS_NS}}}physicalLocation")
            phys_loc.text = holding["repository"]
            if holding.get("repository_gnd"):
                phys_loc.set("authority", "gnd")
                phys_loc.set("valueURI", holding["repository_gnd"])
        if sig:
            shelf = ET.SubElement(loc, f"{{{MODS_NS}}}shelfLocator")
            shelf.text = sig

    # identifier
    if pid:
        ident = ET.SubElement(mods, f"{{{MODS_NS}}}identifier", type="urn")
        ident.text = f"info:fedora/{pid}"

    # provenance
    for prov in full_meta.get("provenance", []):
        if prov:
            note_el = ET.SubElement(mods, f"{{{MODS_NS}}}note", type="provenance")
            note_el.text = prov

    # accessCondition (rights)
    rights = backup_meta.get("rights", "")
    if rights:
        ac = ET.SubElement(mods, f"{{{MODS_NS}}}accessCondition")
        ac.text = rights

    # notes (from TEI)
    notes = full_meta.get("notes", "")
    if notes:
        note_el = ET.SubElement(mods, f"{{{MODS_NS}}}note")
        note_el.text = notes

    return mods


# --- METS Structure ---

def _build_mets(
    object_id: str,
    collection: str,
    mods_el: ET.Element,
    image_urls: list[str],
    pagexml_dir: Path | None,
    rights_owner: str,
) -> ET.Element:
    """Build a complete METS document."""
    mets = ET.Element(f"{{{METS_NS}}}mets")

    # --- dmdSec ---
    dmd = ET.SubElement(mets, f"{{{METS_NS}}}dmdSec", ID="DMD.1")
    md_wrap = ET.SubElement(dmd, f"{{{METS_NS}}}mdWrap", MDTYPE="MODS", MIMETYPE="text/xml")
    xml_data = ET.SubElement(md_wrap, f"{{{METS_NS}}}xmlData")
    xml_data.append(mods_el)

    # --- amdSec (rights + provenance) ---
    amd = ET.SubElement(mets, f"{{{METS_NS}}}amdSec", ID="AMD.1")

    rights_md = ET.SubElement(amd, f"{{{METS_NS}}}rightsMD", ID="RMD.1")
    rmd_wrap = ET.SubElement(rights_md, f"{{{METS_NS}}}mdWrap",
                              MDTYPE="OTHER", MIMETYPE="text/xml", OTHERMDTYPE="DVRIGHTS")
    rmd_data = ET.SubElement(rmd_wrap, f"{{{METS_NS}}}xmlData")
    dv_rights = ET.SubElement(rmd_data, f"{{{DV_NS}}}rights")
    owner_el = ET.SubElement(dv_rights, f"{{{DV_NS}}}owner")
    owner_el.text = rights_owner or "Literaturarchiv Salzburg, https://stefanzweig.digital, CC-BY"

    digiprov = ET.SubElement(amd, f"{{{METS_NS}}}digiprovMD", ID="PMD.1")
    dp_wrap = ET.SubElement(digiprov, f"{{{METS_NS}}}mdWrap",
                             MDTYPE="OTHER", MIMETYPE="text/xml", OTHERMDTYPE="DVLINKS")
    dp_data = ET.SubElement(dp_wrap, f"{{{METS_NS}}}xmlData")
    dv_links = ET.SubElement(dp_data, f"{{{DV_NS}}}links")
    ET.SubElement(dv_links, f"{{{DV_NS}}}reference")
    ET.SubElement(dv_links, f"{{{DV_NS}}}presentation")

    # --- fileSec ---
    file_sec = ET.SubElement(mets, f"{{{METS_NS}}}fileSec")

    # Image fileGrp
    img_grp = ET.SubElement(file_sec, f"{{{METS_NS}}}fileGrp", USE="DEFAULT")
    for i, url in enumerate(image_urls, 1):
        file_el = ET.SubElement(img_grp, f"{{{METS_NS}}}file",
                                 ID=f"IMG.{i}", MIMETYPE="image/jpeg")
        flocat = ET.SubElement(file_el, f"{{{METS_NS}}}FLocat", LOCTYPE="URL")
        flocat.set(f"{{{XLINK_NS}}}href", url)

    # PAGE XML fileGrp (if layout data exists)
    if pagexml_dir and pagexml_dir.exists():
        page_files = sorted(pagexml_dir.glob("page_*.xml"))
        if page_files:
            page_grp = ET.SubElement(file_sec, f"{{{METS_NS}}}fileGrp", USE="PAGE")
            for pf in page_files:
                page_num = pf.stem.replace("page_", "").lstrip("0") or "1"
                file_el = ET.SubElement(page_grp, f"{{{METS_NS}}}file",
                                         ID=f"PAGE.{page_num}", MIMETYPE="application/xml")
                flocat = ET.SubElement(file_el, f"{{{METS_NS}}}FLocat", LOCTYPE="URL")
                flocat.set(f"{{{XLINK_NS}}}href", f"{object_id}_page/{pf.name}")

    # --- structMap PHYSICAL ---
    struct_phys = ET.SubElement(mets, f"{{{METS_NS}}}structMap", TYPE="PHYSICAL")
    phys_seq = ET.SubElement(struct_phys, f"{{{METS_NS}}}div",
                              ID="PHY.1", TYPE="physSequence")

    pid = object_id.replace("o_szd.", "o:szd.")
    for i in range(1, len(image_urls) + 1):
        page_div = ET.SubElement(phys_seq, f"{{{METS_NS}}}div",
                                  ID=f"DIV.{i}", ORDER=str(i), TYPE="page")
        page_div.set("CONTENTIDS", f"http://gams.uni-graz.at/{pid}/IMG.{i}")
        ET.SubElement(page_div, f"{{{METS_NS}}}fptr", FILEID=f"IMG.{i}")

        # Link PAGE XML if available
        if pagexml_dir and pagexml_dir.exists():
            page_path = pagexml_dir / f"page_{i:03d}.xml"
            if page_path.exists():
                ET.SubElement(page_div, f"{{{METS_NS}}}fptr", FILEID=f"PAGE.{i}")

    # --- structMap LOGICAL ---
    struct_log = ET.SubElement(mets, f"{{{METS_NS}}}structMap", TYPE="LOGICAL")
    log_div = ET.SubElement(struct_log, f"{{{METS_NS}}}div",
                             ADMID="AMD.1", DMDID="DMD.1", ID="LOG.1", TYPE="monograph")
    ET.SubElement(log_div, f"{{{METS_NS}}}div", ID="U.1", TYPE="Textseiten")
    ET.SubElement(log_div, f"{{{METS_NS}}}div", ID="U.2", TYPE="Farbreferenz/Schluss")

    # --- structLink ---
    struct_link = ET.SubElement(mets, f"{{{METS_NS}}}structLink")

    # Load OCR to determine page types for structLink
    ocr_data, _ = load_ocr_and_layout(object_id, collection)
    page_types = {}
    if ocr_data:
        for p in ocr_data.get("result", {}).get("pages", []):
            page_types[p.get("page", 0)] = p.get("type", "content")

    for i in range(1, len(image_urls) + 1):
        ptype = page_types.get(i, "content")
        target = "U.1" if ptype == "content" else "U.2"
        sm_link = ET.SubElement(struct_link, f"{{{METS_NS}}}smLink")
        sm_link.set(f"{{{XLINK_NS}}}from", target)
        sm_link.set(f"{{{XLINK_NS}}}to", f"DIV.{i}")

    return mets


# --- Object Export ---

def export_object_mets(
    object_id: str,
    collection: str,
    force: bool = False,
) -> Path | None:
    """Export METS/MODS for a single object."""
    results_dir = results_dir_for(collection)
    out_path = results_dir / f"{object_id}_mets.xml"

    if out_path.exists() and not force:
        return None

    # Load OCR data (required for image URLs)
    ocr_file = find_ocr_file(results_dir, object_id)
    if not ocr_file or not ocr_file.exists():
        print(f"  {object_id}: kein OCR-Ergebnis", file=sys.stderr)
        return None

    ocr_data = json.loads(ocr_file.read_text(encoding="utf-8"))
    image_urls = ocr_data.get("metadata", {}).get("images", [])
    if not image_urls:
        print(f"  {object_id}: keine Bild-URLs", file=sys.stderr)
        return None

    # Load TEI metadata
    pid = object_id.replace("o_szd.", "o:szd.")
    tei_file = DATA_DIR / COLLECTIONS[collection]["tei"]
    full_meta = parse_tei_full_metadata(tei_file, pid) or {}

    # Load backup metadata
    subdir = COLLECTIONS[collection]["subdir"]
    backup_meta_path = BACKUP_ROOT / subdir / object_id / "metadata.json"
    backup_meta = {}
    if backup_meta_path.exists():
        backup_meta = json.loads(backup_meta_path.read_text(encoding="utf-8"))

    # Check for PAGE XML
    pagexml_dir = results_dir / f"{object_id}_page"

    # Build MODS
    mods_el = _build_mods(full_meta, backup_meta, pid)

    # Build METS
    rights_owner = backup_meta.get("rights", "")
    mets_el = _build_mets(object_id, collection, mods_el, image_urls, pagexml_dir, rights_owner)

    # Write
    tree = ET.ElementTree(mets_el)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="unicode", xml_declaration=True)

    return out_path


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="METS/MODS Export: OCR + TEI-Metadaten → METS-Container"
    )
    parser.add_argument("object_id", nargs="?", help="Einzelnes Objekt (z.B. o_szd.100)")
    parser.add_argument("-c", "--collection", help="Sammlung", choices=COLLECTIONS.keys())
    parser.add_argument("--all", action="store_true", help="Alle Sammlungen")
    parser.add_argument("--force", action="store_true", help="Bestehende ueberschreiben")
    parser.add_argument("--dry-run", action="store_true", help="Nur zaehlen, nicht exportieren")
    args = parser.parse_args()

    objects = []
    if args.object_id:
        if not args.collection:
            print("FEHLER: --collection erforderlich bei Einzelobjekt")
            sys.exit(1)
        objects = [{"object_id": args.object_id, "collection": args.collection}]
    elif args.all:
        for col in COLLECTIONS:
            objects.extend(discover_objects(col))
    elif args.collection:
        objects = discover_objects(args.collection)
    else:
        parser.print_help()
        sys.exit(1)

    # Filter to objects that have OCR results
    filtered = []
    for obj in objects:
        ocr_file = find_ocr_file(results_dir_for(obj["collection"]), obj["object_id"])
        if ocr_file and ocr_file.exists():
            filtered.append(obj)

    if args.dry_run:
        print(f"METS Export (dry-run): {len(filtered)} Objekte mit OCR-Ergebnis "
              f"(von {len(objects)} gesamt)")
        for col in COLLECTIONS:
            col_count = sum(1 for o in filtered if o["collection"] == col)
            total_col = sum(1 for o in objects if o["collection"] == col)
            print(f"  {col}: {col_count}/{total_col}")
        return

    print(f"METS Export: {len(filtered)} Objekte")
    print("=" * 60)

    done, skipped, failed = 0, 0, 0
    for i, obj in enumerate(filtered):
        oid = obj["object_id"]
        col = obj["collection"]

        out_path = results_dir_for(col) / f"{oid}_mets.xml"
        if out_path.exists() and not args.force:
            skipped += 1
            continue

        path = export_object_mets(oid, col, args.force)
        if path:
            done += 1
            if done <= 5 or done % 100 == 0:
                print(f"  [{i + 1}/{len(filtered)}] {path.name}")
        else:
            failed += 1

    print("=" * 60)
    print(f"Fertig: {done} exportiert, {skipped} uebersprungen, {failed} fehlgeschlagen")


if __name__ == "__main__":
    main()
