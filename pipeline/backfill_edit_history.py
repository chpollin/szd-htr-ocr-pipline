"""Backfill edit_history for agent-verified result files.

Recovers original transcriptions from git (HEAD) and injects
edit_history entries into pages that were modified by agent verification.

Usage:
    python pipeline/backfill_edit_history.py [--dry-run]
"""

import json
import subprocess
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"


def get_git_version(rel_path: str, ref: str = "HEAD") -> dict | None:
    """Get a specific git-committed version of a JSON file."""
    try:
        out = subprocess.run(
            ["git", "show", f"{ref}:{rel_path}"],
            capture_output=True, cwd=RESULTS_DIR.parent,
        )
        if out.returncode != 0:
            return None
        return json.loads(out.stdout.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def find_pre_edit_ref(rel_path: str) -> str | None:
    """Find the last git commit where the file had no review block."""
    try:
        out = subprocess.run(
            ["git", "log", "--oneline", "--", rel_path],
            capture_output=True, cwd=RESULTS_DIR.parent,
        )
        if out.returncode != 0:
            return None
        commits = [line.split()[0] for line in out.stdout.decode().strip().split("\n") if line.strip()]
        # Walk commits newest→oldest, find first where file has no review
        for commit in commits:
            version = get_git_version(rel_path, commit)
            if version and not version.get("review"):
                return commit
        return None
    except OSError:
        return None


def backfill_file(path: Path, dry_run: bool = False) -> int:
    """Add edit_history to a single result file. Returns number of pages patched."""
    current = json.loads(path.read_text(encoding="utf-8"))
    review = current.get("review", {})

    if review.get("status") != "agent_verified":
        return 0
    edited_pages = review.get("edited_pages", [])
    if not edited_pages:
        return 0

    # Check if already backfilled
    pages = current.get("result", {}).get("pages", [])
    already_done = any(p.get("edit_history") for p in pages if p.get("page") in edited_pages)
    if already_done:
        return 0

    rel_path = path.relative_to(RESULTS_DIR.parent).as_posix()
    # Try HEAD first, then search git history for pre-edit version
    original = get_git_version(rel_path)
    if original and original.get("review"):
        # HEAD already has review — find the pre-edit commit
        ref = find_pre_edit_ref(rel_path)
        if ref:
            original = get_git_version(rel_path, ref)
        else:
            original = None
    if not original:
        print(f"  SKIP {path.name}: no pre-edit git version found")
        return 0

    orig_pages = {p.get("page"): p for p in original.get("result", {}).get("pages", [])}
    cur_pages = {p.get("page"): p for p in pages}

    patched = 0
    for page_num in edited_pages:
        orig_page = orig_pages.get(page_num)
        cur_page = cur_pages.get(page_num)
        if not orig_page or not cur_page:
            continue

        orig_text = orig_page.get("transcription", "")
        cur_text = cur_page.get("transcription", "")
        if orig_text == cur_text:
            continue

        cur_page["edit_history"] = [{
            "original_transcription": orig_text,
            "edited_by": review.get("reviewed_by", "Claude Code Agent"),
            "edited_at": review.get("reviewed_at", ""),
            "source": "agent",
        }]
        patched += 1

    if patched > 0 and not dry_run:
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    return patched


def main():
    dry_run = "--dry-run" in sys.argv
    total_patched = 0
    total_files = 0

    for collection in ["lebensdokumente", "werke", "aufsatzablage", "korrespondenzen"]:
        for path in sorted((RESULTS_DIR / collection).glob("*_gemini-*.json")):
            patched = backfill_file(path, dry_run)
            if patched > 0:
                mode = "WOULD PATCH" if dry_run else "PATCHED"
                print(f"  {mode} {path.name}: {patched} page(s)")
                total_patched += patched
                total_files += 1

    print(f"\n{'DRY RUN: ' if dry_run else ''}Backfilled {total_patched} pages in {total_files} files.")


if __name__ == "__main__":
    main()
