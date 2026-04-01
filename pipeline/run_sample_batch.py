"""Run targeted sample batch: fill each group to 10 objects (E to max 5).

Usage: python pipeline/run_sample_batch.py [--dry-run] [--max-images N]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from config import COLLECTIONS, RESULTS_BASE
from transcribe import discover_objects, resolve_context, run_batch

# Target count per group (E has only 5 objects in backup)
TARGET = {
    "handschrift": 10,
    "typoskript": 10,
    "formular": 10,
    "kurztext": 10,
    "tabellarisch": 5,  # Only 5 exist
    "korrekturfahne": 10,
    "konvolut": 10,
    "zeitungsausschnitt": 10,
    "korrespondenz": 10,
}


def get_done_ids() -> set:
    """Get set of already-transcribed object IDs."""
    done = set()
    for f in RESULTS_BASE.rglob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if "object_id" in data:
                done.add(data["object_id"])
        except (json.JSONDecodeError, KeyError):
            pass
    return done


def main():
    parser = argparse.ArgumentParser(description="Sample batch: 10 per group")
    parser.add_argument("--dry-run", action="store_true", help="List objects without transcribing")
    parser.add_argument("--max-images", type=int, default=5, help="Max images per object (default: 5)")
    args = parser.parse_args()

    done_ids = get_done_ids()

    # Count current objects per group
    current = Counter()
    for f in RESULTS_BASE.rglob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if "group" in data:
                current[data["group"]] += 1
        except (json.JSONDecodeError, KeyError):
            pass

    # Discover all objects and resolve groups
    all_objects = []
    for col in COLLECTIONS:
        for obj in discover_objects(col):
            if obj["object_id"] in done_ids:
                continue
            all_objects.append(obj)

    # Assign groups and select needed objects
    batch = []
    needed = {g: TARGET[g] - current.get(g, 0) for g in TARGET}

    print(f"{'Gruppe':20s} {'Haben':>6s} {'Ziel':>6s} {'Fehlen':>6s}")
    print("-" * 42)
    for g in sorted(TARGET):
        n = needed.get(g, 0)
        print(f"{g:20s} {current.get(g, 0):6d} {TARGET[g]:6d} {max(0, n):6d}")

    print(f"\nResolve groups for {len(all_objects)} undone objects...")

    group_counts = Counter()
    for obj in all_objects:
        group, _, _ = resolve_context(obj["object_id"], obj["collection"])
        if needed.get(group, 0) > 0 and group_counts[group] < needed[group]:
            obj["group"] = group
            batch.append(obj)
            group_counts[group] += 1

    print(f"\nAusgewählt: {len(batch)} Objekte")
    print(f"{'Gruppe':20s} {'Anzahl':>6s}")
    print("-" * 28)
    for g in sorted(group_counts):
        print(f"{g:20s} {group_counts[g]:6d}")

    if args.dry_run:
        print(f"\n{'Object-ID':20s} {'Sammlung':20s} {'Gruppe':20s}")
        print("-" * 62)
        for obj in batch:
            print(f"{obj['object_id']:20s} {obj['collection']:20s} {obj['group']}")
        print(f"\n{len(batch)} Objekte (dry-run)")
        return

    # Run batch
    print(f"\nStarte Batch: {len(batch)} Objekte, max-images={args.max_images}")
    print("=" * 60)
    done, skipped, failed = run_batch(batch, max_images=args.max_images)
    print("=" * 60)
    print(f"Fertig: {done} transkribiert, {skipped} übersprungen, {failed} fehlgeschlagen")


if __name__ == "__main__":
    main()
