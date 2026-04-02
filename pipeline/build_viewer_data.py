"""Build catalog.json + data/{collection}.json + data/knowledge.json from enriched result files."""

import json
import re
from datetime import datetime, timezone

import markdown
import yaml

from config import COLLECTIONS, DATA_DIR as TEI_DIR, GROUP_LABELS, MODEL, PROJECT_ROOT, RESULTS_BASE, RESULTS_DIR
from tei_context import parse_tei_for_object

DOCS_DIR = PROJECT_ROOT / "docs"
CATALOG_PATH = DOCS_DIR / "catalog.json"
DATA_DIR = DOCS_DIR / "data"
GAMS_BASE = "https://gams.uni-graz.at/"


def load_consensus(result_file) -> dict | None:
    """Load consensus data for an object if it exists."""
    consensus_file = result_file.parent / (
        result_file.stem.split("_gemini")[0].split("_claude")[0] + "_consensus.json"
    )
    if not consensus_file.exists():
        return None
    try:
        data = json.loads(consensus_file.read_text(encoding="utf-8"))
        cons = data.get("consensus", {})
        judge_pages = data.get("judge_data", {}).get("pages", [])
        # Merge transcription texts from judge_data into consensus pages
        pages = []
        for cp in cons.get("pages", []):
            page_entry = {
                "page": cp.get("page", 0),
                "cer": cp.get("cer"),
                "cer_orderless": cp.get("cer_orderless"),
                "agreement": cp.get("agreement", ""),
                "type": cp.get("type", "content"),
            }
            # Find matching judge page for transcription texts
            jp = next((j for j in judge_pages if j.get("page") == cp.get("page")), None)
            if jp:
                page_entry["transcription_a"] = jp.get("transcription_a", "")
                page_entry["transcription_b"] = jp.get("transcription_b", "")
            pages.append(page_entry)
        return {
            "category": cons.get("category", ""),
            "effective_cer": cons.get("effective_cer", 0),
            "overall_cer": cons.get("overall_cer", 0),
            "word_overlap": cons.get("word_overlap", 0),
            "content_pages": cons.get("content_pages", 0),
            "skipped_pages": cons.get("skipped_pages", 0),
            "model_a": data.get("model_a", ""),
            "model_b": data.get("model_b", ""),
            "pages": pages,
        }
    except (json.JSONDecodeError, KeyError):
        return None


def extract_signature(title: str) -> tuple[str, str]:
    """Extract signature from title. Returns (title_clean, signature)."""
    parts = title.rsplit(",", 1)
    if len(parts) == 2 and parts[1].strip().startswith("SZ-"):
        return parts[0].strip(), parts[1].strip()
    return title, ""


def compute_verification(pages: list[dict]) -> dict:
    """Compute verification metrics from transcription text."""
    uncertain = 0
    illegible = 0
    total_chars = 0
    empty_pages = 0

    for page in pages:
        text = page.get("transcription", "")
        if not text.strip():
            empty_pages += 1
            continue
        total_chars += len(text)
        uncertain += len(re.findall(r"\[\?\]", text))
        illegible += len(re.findall(r"\[\.\.\..*?\]", text))

    non_empty = len(pages) - empty_pages
    return {
        "uncertainCount": uncertain,
        "illegibleCount": illegible,
        "totalChars": total_chars,
        "emptyPages": empty_pages,
        "avgCharsPerPage": round(total_chars / non_empty) if non_empty else 0,
    }


def build():
    objects = []

    # Scan collection result directories (skip test/, groundtruth/)
    SKIP_DIRS = {"test", "groundtruth"}
    # Whitelist: only include primary model results (not Pro, consensus, layout, etc.)
    expected_suffix = f"_{MODEL}.json"
    result_files = []
    for subdir in sorted(RESULTS_BASE.iterdir()):
        if subdir.is_dir() and subdir.name not in SKIP_DIRS:
            result_files.extend(sorted(subdir.glob(f"*{expected_suffix}")))

    for result_file in result_files:

        data = json.loads(result_file.read_text(encoding="utf-8"))

        # Skip non-enriched legacy results (no "collection" key)
        if "collection" not in data:
            continue

        group_key = data.get("group", "")
        group_letter, group_label = GROUP_LABELS.get(group_key, ("?", group_key))

        meta = data.get("metadata", {})
        result = data.get("result", {})
        pid = data["object_id"].replace("o_szd.", "o:szd.")

        # Determine which GAMS images to use per page
        all_images = meta.get("images", [])
        raw_pages = result.get("pages", [])
        # Filter out color_chart pages (archival reference only, no transcription)
        filtered = [(i, p) for i, p in enumerate(raw_pages) if p.get("type") != "color_chart"]
        pages = [p for _, p in filtered]
        page_images = [all_images[i] for i, _ in filtered if i < len(all_images)] if all_images else []

        full_title = meta.get("title", "")
        title_clean, signature = extract_signature(full_title)

        # Get classification + objecttyp from TEI
        collection = data["collection"]
        tei_file = TEI_DIR / COLLECTIONS[collection]["tei"]
        tei_meta = parse_tei_for_object(tei_file, pid) or {}
        classification = tei_meta.get("classification", "")
        objecttyp = tei_meta.get("objecttyp", "")
        # Fallback for Korrespondenzen (no TEI classification) — parse title
        if not objecttyp and collection == "korrespondenzen":
            tl = full_title.lower()
            if "ansichtspostkarte" in tl:
                objecttyp = "Ansichtspostkarte"
            elif "postkarte" in tl:
                objecttyp = "Postkarte"
            elif "telegramm" in tl:
                objecttyp = "Telegramm"
            else:
                objecttyp = "Brief"
        if not classification and collection == "korrespondenzen":
            classification = "Korrespondenz"

        verification = compute_verification(pages)
        verification["vlmConfidence"] = result.get("confidence", "")

        # quality_signals from enriched JSON (added by transcribe.py or backfill)
        qs = data.get("quality_signals", {})

        # Expert review status (added by import_reviews.py)
        review = data.get("review")

        # Consensus data (from verify.py)
        consensus = load_consensus(result_file)

        obj = {
            "id": result_file.stem,
            "collection": data["collection"],
            "label": title_clean[:40],
            "group": group_letter,
            "groupLabel": group_label,
            "pid": pid,
            "title": full_title,
            "titleClean": title_clean,
            "signature": signature,
            "classification": classification,
            "objecttyp": objecttyp,
            "lang": meta.get("language", ""),
            "model": data.get("model", ""),
            "thumbnail": GAMS_BASE + pid + "/THUMBNAIL",
            "images": page_images,
            "pages": pages,
            "confidence": result.get("confidence", ""),
            "confidenceNotes": result.get("confidence_notes", ""),
            "pageCount": len(pages),
            "verification": verification,
            "needsReview": qs.get("needs_review", False),
            "needsReviewReasons": qs.get("needs_review_reasons", []),
            "blankPages": qs.get("blank_pages", 0),
            "contentPages": qs.get("content_pages", 0),
            "quality_signals": {
                "total_chars": qs.get("total_chars", 0),
                "total_words": qs.get("total_words", 0),
                "total_pages": qs.get("total_pages", 0),
                "empty_pages": qs.get("empty_pages", 0),
                "blank_pages": qs.get("blank_pages", 0),
                "content_pages": qs.get("content_pages", 0),
                "color_chart_pages": qs.get("color_chart_pages", 0),
                "chars_per_page": qs.get("chars_per_page", []),
                "chars_per_page_median": qs.get("chars_per_page_median", 0),
                "marker_uncertain_count": qs.get("marker_uncertain_count", 0),
                "marker_illegible_count": qs.get("marker_illegible_count", 0),
                "marker_density": qs.get("marker_density", 0),
                "dwr_score": qs.get("dwr_score", 0),
                "duplicate_page_pairs": qs.get("duplicate_page_pairs", []),
                "language_expected": qs.get("language_expected", ""),
                "language_detected": qs.get("language_detected", ""),
                "language_match": qs.get("language_match", True),
                "page_length_anomalies": qs.get("page_length_anomalies", []),
                "needs_review": qs.get("needs_review", False),
                "needs_review_reasons": qs.get("needs_review_reasons", []),
            },
            "consensus": consensus,  # None if no consensus file exists
            "review": review,  # None if not yet reviewed
        }
        objects.append(obj)

    # Sort: by collection, then by group
    objects.sort(key=lambda o: (o["collection"], o["group"]))

    collections = sorted(set(o["collection"] for o in objects))

    # --- catalog.json: lightweight metadata only ---
    catalog_objects = []
    for obj in objects:
        catalog_objects.append({
            "id": obj["id"],
            "collection": obj["collection"],
            "label": obj["label"],
            "group": obj["group"],
            "groupLabel": obj["groupLabel"],
            "pid": obj["pid"],
            "title": obj["title"],
            "titleClean": obj["titleClean"],
            "signature": obj["signature"],
            "classification": obj["classification"],
            "objecttyp": obj["objecttyp"],
            "lang": obj["lang"],
            "model": obj["model"],
            "confidence": obj["confidence"],
            "pageCount": obj["pageCount"],
            "thumbnail": obj["thumbnail"],
            "verification": obj["verification"],
            "needsReview": obj["needsReview"],
            "needsReviewReasons": obj["needsReviewReasons"],
            "blankPages": obj.get("blankPages", 0),
            "contentPages": obj.get("contentPages", 0),
            "dwrScore": obj.get("quality_signals", {}).get("dwr_score", 0),
            "consensusCategory": obj["consensus"]["category"] if obj.get("consensus") else None,
            "consensusCer": obj["consensus"]["effective_cer"] if obj.get("consensus") else None,
            "reviewStatus": obj["review"].get("status") if obj.get("review") else None,
        })

    catalog = {"objects": catalog_objects, "collections": collections}
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Katalog: {CATALOG_PATH} ({len(catalog_objects)} Objekte)")

    # --- data/{collection}.json: full objects with transcription text ---
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for col in collections:
        col_objects = []
        for obj in objects:
            if obj["collection"] != col:
                continue
            col_objects.append({
                "id": obj["id"],
                "images": obj["images"],
                "pages": obj["pages"],
                "confidence": obj["confidence"],
                "confidenceNotes": obj["confidenceNotes"],
                "verification": obj["verification"],
                "quality_signals": obj.get("quality_signals", {}),
                "consensus": obj.get("consensus"),
                "review": obj.get("review"),
            })
        col_path = DATA_DIR / f"{col}.json"
        col_path.write_text(
            json.dumps({"objects": col_objects}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  {col}: {col_path} ({len(col_objects)} Objekte)")

    # --- groundtruth.json: GT drafts for expert review ---
    gt_dir = RESULTS_BASE / "groundtruth"
    gt_objects = []
    if gt_dir.exists():
        for gt_file in sorted(gt_dir.glob("*_gt_draft.json")):
            gt_data = json.loads(gt_file.read_text(encoding="utf-8"))
            oid = gt_data.get("object_id", "")
            # Find the matching result ID
            result_id = None
            for obj in objects:
                if obj["id"].startswith(oid + "_"):
                    result_id = obj["id"]
                    break
            gt_objects.append({
                "id": result_id or oid,
                "object_id": oid,
                "collection": gt_data.get("collection", ""),
                "group": gt_data.get("group", ""),
                "title": gt_data.get("title", ""),
                "models": gt_data.get("models", {}),
                "pages": gt_data.get("pages", []),
                "merge_stats": gt_data.get("merge_stats", {}),
                "expert_verified": gt_data.get("expert_verified", False),
                "reviewed_by": gt_data.get("reviewed_by"),
                "reviewed_at": gt_data.get("reviewed_at"),
            })

    if gt_objects:
        gt_path = DATA_DIR / "groundtruth.json"
        gt_path.write_text(
            json.dumps({"objects": gt_objects}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  Ground Truth: {gt_path} ({len(gt_objects)} Objekte)")

        # Add GT status to catalog
        gt_ids = {g["id"] for g in gt_objects}
        gt_verified = {g["id"]: g.get("expert_verified", False) for g in gt_objects}
        for cat_obj in catalog_objects:
            cat_obj["hasGT"] = cat_obj["id"] in gt_ids
            if cat_obj["id"] in gt_ids:
                cat_obj["gtVerified"] = gt_verified.get(cat_obj["id"], False)

        # Re-write catalog with GT flags
        CATALOG_PATH.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  Katalog mit GT-Flags aktualisiert")

    print(f"Gesamt: {len(objects)} Objekte, {len(collections)} Sammlungen, {len(gt_objects)} GT-Drafts")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from markdown body."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 3:].strip()
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, body


def parse_index_sections(body: str) -> list[dict]:
    """Parse index.md body to extract section groupings with slugs."""
    sections = []
    current_label = None
    current_slugs = []

    for line in body.split("\n"):
        line = line.strip()
        # Section headers: ## Leseordnung, ## Spezifikationen, ## Projektlog
        if line.startswith("## "):
            if current_label and current_slugs:
                sections.append({"label": current_label, "slugs": current_slugs})
            heading = line[3:].strip()
            # Skip non-content sections
            if heading.lower().startswith("verwandte"):
                current_label = None
                current_slugs = []
                continue
            current_label = heading
            current_slugs = []
            continue
        # Extract [[slug]] from list items
        m = re.search(r"\[\[(.+?)\]\]", line)
        if m and current_label:
            current_slugs.append(m.group(1))

    if current_label and current_slugs:
        sections.append({"label": current_label, "slugs": current_slugs})

    return sections


def build_knowledge():
    """Build docs/data/knowledge.json from knowledge/*.md + README.md."""
    knowledge_dir = PROJECT_ROOT / "knowledge"
    if not knowledge_dir.exists():
        print("  Knowledge-Verzeichnis nicht gefunden, ueberspringe.")
        return

    md_extensions = ["tables", "fenced_code", "toc"]
    md_converter = markdown.Markdown(extensions=md_extensions)

    # First pass: collect all slugs + titles for wiki-link resolution
    title_map = {}
    for md_file in sorted(knowledge_dir.glob("*.md")):
        slug = md_file.stem
        fm, _ = parse_frontmatter(md_file.read_text(encoding="utf-8"))
        title_map[slug] = fm.get("title", slug)

    # Parse index.md for section structure
    index_file = knowledge_dir / "index.md"
    sections = []
    if index_file.exists():
        _, index_body = parse_frontmatter(index_file.read_text(encoding="utf-8"))
        sections = parse_index_sections(index_body)

    # Flat reading order from sections
    reading_order = []
    for sec in sections:
        reading_order.extend(sec["slugs"])

    # Second pass: convert each document
    docs = {}
    for md_file in sorted(knowledge_dir.glob("*.md")):
        slug = md_file.stem
        if slug == "index":
            continue  # index is used for structure, not rendered as doc

        raw = md_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(raw)

        # Resolve wiki-links: [[slug]] -> <a href="#knowledge/slug">title</a>
        def resolve_wikilink(m):
            target = m.group(1)
            title = title_map.get(target, target)
            return f'<a href="#knowledge/{target}" class="knowledge__wikilink">{title}</a>'

        body = re.sub(r"\[\[(.+?)\]\]", resolve_wikilink, body)

        # Convert markdown to HTML
        md_converter.reset()
        html = md_converter.convert(body)

        # Extract headings from TOC extension
        headings = []
        if hasattr(md_converter, "toc_tokens"):
            def extract_headings(tokens, result):
                for tok in tokens:
                    result.append({
                        "level": tok.get("level", 2),
                        "id": tok.get("id", ""),
                        "text": tok.get("name", ""),
                    })
                    if tok.get("children"):
                        extract_headings(tok["children"], result)
            extract_headings(md_converter.toc_tokens, headings)

        # Parse related links from frontmatter
        related = []
        for r in fm.get("related", []):
            m_rel = re.search(r"\[\[(.+?)\]\]", str(r))
            if m_rel:
                related.append(m_rel.group(1))

        # Word count
        words = len(re.findall(r"\w+", body))

        docs[slug] = {
            "slug": slug,
            "title": fm.get("title", slug),
            "type": fm.get("type", ""),
            "status": fm.get("status", ""),
            "tags": fm.get("tags", []),
            "created": str(fm.get("created", "")),
            "updated": str(fm.get("updated", "")),
            "related": related,
            "html": html,
            "headings": headings,
            "wordCount": words,
        }

    # README.md -> About page
    readme_file = PROJECT_ROOT / "README.md"
    about = {"html": "", "title": "SZD-HTR-OCR-Pipeline"}
    if readme_file.exists():
        readme_raw = readme_file.read_text(encoding="utf-8")
        md_converter.reset()
        about_html = md_converter.convert(readme_raw)
        about["html"] = about_html

    knowledge_json = {
        "meta": {
            "built_at": datetime.now(timezone.utc).isoformat(),
            "count": len(docs),
        },
        "sections": sections,
        "docs": docs,
        "about": about,
    }

    out_path = DATA_DIR / "knowledge.json"
    out_path.write_text(
        json.dumps(knowledge_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  Knowledge Vault: {out_path} ({len(docs)} Dokumente)")


if __name__ == "__main__":
    build()
    build_knowledge()
