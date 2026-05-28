#!/usr/bin/env python3
"""
Safe backfill for media_assets.message_time

This script adds a 'message_time' column (if missing) and populates it
using the filesystem mtime of the copied media files in data/media/.

Because the importer used shutil.copy2, the mtime is preserved from the
original exported files in backup/images/ (and videos/).

This gives us a usable proxy for the original photo/message time,
which is the foundation for correctly linking photo_contexts later.

Run from project root:
    python3 scripts/import_wechat/backfill_media_message_times.py

It is idempotent and only touches the message_time column.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import os

DB_PATH = Path("data/zy_memo_real.db")
MEDIA_ROOT = Path("data/media")


def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Add the column safely if it doesn't exist
    try:
        cur.execute("ALTER TABLE media_assets ADD COLUMN message_time TEXT")
        conn.commit()
        print("Added column 'message_time' to media_assets.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'message_time' already exists. Continuing...")
        else:
            raise

    # 2. Find all image media that don't have message_time yet (or all)
    cur.execute("""
        SELECT id, relative_path, type
        FROM media_assets
        WHERE type IN ('image', 'video')
          AND (message_time IS NULL OR message_time = '')
        ORDER BY id
    """)
    rows = cur.fetchall()

    print(f"Found {len(rows)} media items to backfill...")

    updated = 0
    not_found = 0

    for media_id, rel_path, media_type in rows:
        file_path = MEDIA_ROOT / Path(rel_path).name   # relative_path is like "media/xxx.jpg"

        if not file_path.exists():
            # Try the full relative path from project root
            alt_path = Path(rel_path)
            if alt_path.exists():
                file_path = alt_path
            else:
                not_found += 1
                continue

        try:
            stat = file_path.stat()
            # Use mtime (last modification time of the original exported file)
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            iso_time = mtime.isoformat()

            cur.execute(
                "UPDATE media_assets SET message_time = ? WHERE id = ?",
                (iso_time, media_id)
            )
            updated += 1

            if updated % 500 == 0:
                print(f"  Updated {updated} items...")

        except Exception as e:
            print(f"  Warning: failed to process {media_id}: {e}")

    conn.commit()
    conn.close()

    print(f"\nDone.")
    print(f"  Updated with message_time: {updated}")
    print(f"  Files not found: {not_found}")
    print(f"\nYou can now use message_time in queries for time-based context matching.")


if __name__ == "__main__":
    main()
