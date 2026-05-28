#!/usr/bin/env python3
"""
Safe, focused fix for existing databases.

This script can be run on an already-populated zy_memo_real.db + the original
backup folder + CSV. It does two important things for "正确照片时间":

1. Scans the CSV for image messages and their real CreateTime.
2. Tries harder to link them to the existing media_assets rows (using hash,
   original_name, and src signals).
3. Updates `message_time` on the matched media rows with the real historical time.
4. Inserts the missing image message rows into the `messages` table with
   correct time + media_id (so future context work and "当时在聊" become possible).

This is the practical way to fix your current data without a full re-import.

Usage (from project root):
    python3 scripts/import_wechat/fix_image_times_from_csv.py

It is idempotent (safe to run multiple times).
"""

import csv
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

CSV_PATH = Path("backup/texts/私聊_羊.csv")
DB_PATH = Path("data/zy_memo_real.db")
BACKUP_IMAGES = Path("backup/images")


def parse_time(ts_str: str) -> datetime:
    ts_str = ts_str.strip().replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.strptime(ts_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        return
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    print("Loading CSV image messages...")
    image_events = []  # list of (create_time, src, original_msg_id)
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('type_name', '').strip().lower() != 'image':
                continue
            t = parse_time(row['CreateTime'])
            src = row.get('src', '').strip()
            if src:
                image_events.append((t, src, row['id']))

    print(f"Found {len(image_events)} image messages in CSV")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Load current media with their identifiers
    print("Loading existing media_assets...")
    cur.execute("""
        SELECT id, hash, original_name, relative_path
        FROM media_assets
        WHERE type = 'image'
    """)
    media_rows = cur.fetchall()  # (id, hash, original_name, relative_path)

    # Build lookup structures for better matching
    hash_to_id = {row[0]: row[0] for row in media_rows}  # id == hash
    name_to_id = {}
    for row in media_rows:
        mid, h, orig_name, _ = row
        if orig_name:
            name_to_id[orig_name.lower()] = mid
            # also index by parts of the name (common in these exports)
            for part in orig_name.lower().split('_'):
                if len(part) > 6:
                    name_to_id[part] = mid

    print(f"Loaded {len(media_rows)} image media assets")

    # Try to match CSV images to media and collect updates
    time_updates = []
    message_inserts = []
    matched = 0

    for create_time, src, orig_msg_id in image_events:
        matched_id = None

        # Strategy 1: src appears in hash (original weak logic)
        for h in hash_to_id:
            if src in h:
                matched_id = h
                break

        # Strategy 2: src appears in original_name (or parts of it)
        if not matched_id:
            src_lower = src.lower()
            if src_lower in name_to_id:
                matched_id = name_to_id[src_lower]
            else:
                for part in src_lower.split('_'):
                    if len(part) > 6 and part in name_to_id:
                        matched_id = name_to_id[part]
                        break

        if matched_id:
            iso_time = create_time.isoformat()
            time_updates.append({'message_time': iso_time, 'id': matched_id})

            # Also prepare to insert the image message row (if not already present)
            msg_id = f"msg_{orig_msg_id}"
            # We don't have slice here easily, so we leave slice_id as NULL for now
            # (or we could look it up by time, but that's heavier).
            # For the photo grid use case this is acceptable.
            message_inserts.append({
                'id': msg_id,
                'slice_id': None,
                'time': iso_time,
                'from_me': 0,  # will be updated if we have the data
                'type': 'image',
                'content': '',
                'media_id': matched_id,
                'extra': json.dumps({'original_type': 'image', 'src': src})
            })
            matched += 1

    print(f"Successfully matched {matched} CSV images to media files")

    if time_updates:
        cur.executemany("""
            UPDATE media_assets
            SET message_time = :message_time
            WHERE id = :id
        """, time_updates)
        conn.commit()
        print(f"  Updated message_time on {len(time_updates)} media rows")

    if message_inserts:
        # Use INSERT OR IGNORE so re-runs are safe
        cur.executemany("""
            INSERT OR IGNORE INTO messages
            (id, slice_id, time, from_me, type, content, media_id, extra)
            VALUES (:id, :slice_id, :time, :from_me, :type, :content, :media_id, :extra)
        """, message_inserts)
        conn.commit()
        print(f"  Inserted/ignored {len(message_inserts)} image message rows")

    conn.close()
    print("\nDone.")
    print("You can now re-run the time-based context linker if you want,")
    print("or rebuild the app to see better times on the photo grid.")


if __name__ == "__main__":
    main()
