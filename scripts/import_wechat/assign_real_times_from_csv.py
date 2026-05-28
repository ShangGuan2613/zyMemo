#!/usr/bin/env python3
"""
Improved time assignment for media using the original CSV CreateTime.

Because filesystem mtime in both backup/ and data/media/ only reflects
the day the export was prepared (all ~2026-05-27), we go back to the
source of truth: the CSV.

This script:
- Re-processes the CSV for image rows (with their real CreateTime).
- Uses the same best-effort src matching that the main importer used
  to associate a CSV image message with a media hash.
- Updates the corresponding media_assets row with the real message_time
  from the CSV.

After this, time-based context matching (the previous script) will be
able to find correct nearby chat for those images that get a real time.

Run:
    python3 scripts/import_wechat/assign_real_times_from_csv.py
"""

import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict

CSV_PATH = Path("backup/texts/私聊_羊.csv")
DB_PATH = Path("data/zy_memo_real.db")


def parse_time(ts_str: str) -> datetime:
    ts_str = ts_str.strip().replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        # fallback
        return datetime.strptime(ts_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")


def main():
    if not CSV_PATH.exists():
        print(f"CSV not found: {CSV_PATH}")
        return
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Load existing media hashes (id = hash)
    cur.execute("SELECT id FROM media_assets WHERE type = 'image'")
    existing_hashes = {row[0] for row in cur.fetchall()}
    print(f"Loaded {len(existing_hashes)} existing image hashes from DB")

    # We will also need a map from possible src to hash for matching
    # For now we use the weak src-in-hash logic from the original importer
    media_id_to_hash: Dict[str, str] = {h: h for h in existing_hashes}

    updates = []

    print("Scanning CSV for image messages...")
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('type_name', '').strip().lower() != 'image':
                continue

            create_time = parse_time(row['CreateTime'])
            src = row.get('src', '').strip()

            if not src:
                continue

            # Same weak matching logic as the main importer
            matched_id = None
            for mid in existing_hashes:
                if src in mid:
                    matched_id = mid
                    break

            if matched_id:
                iso = create_time.isoformat()
                updates.append((iso, matched_id))

    print(f"Found {len(updates)} image messages in CSV that could be matched to media hashes via src")

    if updates:
        cur.executemany(
            "UPDATE media_assets SET message_time = ? WHERE id = ?",
            updates
        )
        conn.commit()
        print(f"Updated {len(updates)} media rows with real CSV CreateTime as message_time")

    conn.close()
    print("\nDone. You can now re-run the time-based context linker for better results.")


if __name__ == "__main__":
    main()
