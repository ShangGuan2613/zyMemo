#!/usr/bin/env python3
"""
A4: Time-based linking of photo contexts to actual images.

This script matches entries from photo_contexts (which have high-quality
nearby-chat snippets + emotion from the original CSV analysis) to real
media_assets rows using the now-populated message_time on both sides.

It works by:
- Taking each image's message_time (backfilled from file mtime)
- Finding the photo_context whose message_time is closest in time
- If within a reasonable window (default 10 minutes), attaching the
  context_text and emotion_tag directly onto the media_assets row.

This is safe, additive, and gives us correct per-photo "当时在聊" + emotion
without needing perfect filename/src matching from the original export.

After running this, rebuild the app and the photo grid will show accurate
context for most images.

Usage (from project root):
    python3 scripts/import_wechat/link_photo_contexts_by_time.py

You can re-run it anytime (it will overwrite with latest best match).
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import sys

DB_PATH = Path("data/zy_memo_real.db")
MATCH_WINDOW_MINUTES = 10
# Only consider matches where |delta| <= this many seconds
MAX_DELTA_SECONDS = MATCH_WINDOW_MINUTES * 60


def parse_time(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    ts = ts.strip()
    try:
        # Handle both with and without Z / offset
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def find_closest_context(
    image_time: datetime,
    contexts: list[Tuple[datetime, str, str]]
) -> Optional[Tuple[str, str, float]]:
    """
    contexts: list of (time, context_text, emotion_tag)
    Returns (context_text, emotion_tag, delta_seconds) or None
    """
    if not contexts:
        return None

    best = None
    best_delta = float('inf')

    for ctx_time, ctx_text, emotion in contexts:
        delta = abs((image_time - ctx_time).total_seconds())
        if delta < best_delta:
            best_delta = delta
            best = (ctx_text, emotion, delta)

    if best and best[2] <= MAX_DELTA_SECONDS:
        return best
    return None


def main():
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Ensure media_assets has the context columns (safe, additive)
    for col in ("context_text", "emotion_tag"):
        try:
            cur.execute(f"ALTER TABLE media_assets ADD COLUMN {col} TEXT")
            print(f"Added column {col} to media_assets")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                pass
            else:
                raise

    conn.commit()

    # 2. Load images that have a usable message_time
    print("Loading images with message_time...")
    cur.execute("""
        SELECT id, message_time
        FROM media_assets
        WHERE type = 'image'
          AND message_time IS NOT NULL
          AND message_time != ''
        ORDER BY message_time
    """)
    images = cur.fetchall()
    print(f"  Found {len(images)} images with message_time")

    # 3. Load all photo contexts (they have good message_time + context + emotion)
    print("Loading photo_contexts...")
    cur.execute("""
        SELECT message_time, context_text, emotion_tag
        FROM photo_contexts
        WHERE message_time IS NOT NULL
          AND message_time != ''
          AND context_text IS NOT NULL
          AND context_text != ''
        ORDER BY message_time
    """)
    raw_contexts = cur.fetchall()

    contexts: list[Tuple[datetime, str, str]] = []
    for mt, ctx, emo in raw_contexts:
        dt = parse_time(mt)
        if dt and ctx:
            contexts.append((dt, ctx, emo or "日常"))

    print(f"  Loaded {len(contexts)} usable photo contexts")

    if not contexts:
        print("No usable contexts found. Nothing to do.")
        conn.close()
        return

    # 4. For each image, find best matching context by time
    print(f"Matching with ±{MATCH_WINDOW_MINUTES} minute window...")
    matches = 0
    total_delta = 0.0
    updates = []

    for media_id, mt_str in images:
        img_time = parse_time(mt_str)
        if not img_time:
            continue

        best = find_closest_context(img_time, contexts)
        if best:
            ctx_text, emotion, delta = best
            updates.append((ctx_text, emotion, media_id))
            matches += 1
            total_delta += abs(delta)

            if matches % 500 == 0:
                print(f"  Matched {matches} images...")

    # 5. Bulk update
    if updates:
        print(f"Writing {len(updates)} matches to database...")
        cur.executemany("""
            UPDATE media_assets
            SET context_text = ?, emotion_tag = ?
            WHERE id = ?
        """, updates)
        conn.commit()

    conn.close()

    print("\n=== Matching complete ===")
    print(f"Images with message_time: {len(images)}")
    print(f"Successfully matched:     {matches}")
    if matches > 0:
        avg_delta = total_delta / matches
        print(f"Average time delta:     {avg_delta:.1f} seconds ({avg_delta/60:.1f} min)")
        print(f"Match rate:             {matches / len(images) * 100:.1f}%")
    print("\nRebuild the app (cargo tauri build or pnpm tauri dev) to see correct")
    print("contexts and emotions on the photo cards.")


if __name__ == "__main__":
    main()
