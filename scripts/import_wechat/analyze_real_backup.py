#!/usr/bin/env python3
"""
Real Data Analysis Script for zyMemo
Analyzes the WeClone-style backup export in backup/ folder.

Run from project root:
    python3 scripts/import_wechat/analyze_real_backup.py
"""

import csv
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# === Configuration ===
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKUP_ROOT = PROJECT_ROOT / "backup"
CSV_PATH = BACKUP_ROOT / "texts" / "私聊_羊.csv"

# Media folders
IMAGES_DIR = BACKUP_ROOT / "images"
VIDEOS_DIR = BACKUP_ROOT / "videos"
EMOJIS_DIR = BACKUP_ROOT / "emojis"
FILES_DIR = BACKUP_ROOT / "file"
VOICES_DIR = BACKUP_ROOT / "voices"

# Time gap threshold for suggesting slice breaks (in hours)
SLICE_GAP_HOURS = 48


def parse_time(ts_str: str) -> datetime:
    """Parse ISO time from CSV (handles trailing .000Z)."""
    if not ts_str:
        return None
    ts_str = ts_str.strip()
    if ts_str.endswith('Z'):
        ts_str = ts_str[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        # Fallback for some variants
        return datetime.strptime(ts_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")


def extract_hash_from_src(src: str) -> Optional[str]:
    """Extract the hash part from src column."""
    if not src:
        return None
    src = src.strip()
    # For images: just the hash (e.g. f47daf2eaa98fc2e0476b8a8cfe38d54)
    # For stickers/emojis: ../emojis/xxx.gif -> take filename stem
    if src.startswith('../emojis/'):
        name = Path(src).stem
        return name
    # For plain hash in images (most common case)
    if re.match(r'^[0-9a-f]{8,}$', src):
        return src
    # Try to extract hash from full filename if present
    match = re.search(r'([0-9a-f]{8,})\.[a-z]+$', src)
    if match:
        return match.group(1)
    return None


def get_media_file_for_hash(hash_val: str, media_dir: Path) -> Optional[Path]:
    """Find a media file in the folder that contains the hash in its name."""
    if not hash_val:
        return None
    for f in media_dir.glob(f"*{hash_val}*"):
        return f
    return None


def main():
    print("=" * 60)
    print("zyMemo Real Data Analysis - backup/ folder")
    print("=" * 60)
    print(f"CSV: {CSV_PATH}")
    print()

    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        return

    # === Load and basic parsing ===
    messages = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            msg_time = parse_time(row.get('CreateTime', ''))
            if not msg_time:
                continue
            messages.append({
                'id': row.get('id'),
                'MsgSvrID': row.get('MsgSvrID'),
                'type_name': row.get('type_name', '').strip(),
                'is_sender': row.get('is_sender', ''),
                'talker': row.get('talker', '').strip(),
                'msg': row.get('msg', ''),
                'src': row.get('src', '').strip(),
                'time': msg_time,
            })

    total = len(messages)
    print(f"Total messages parsed: {total:,}")

    if total == 0:
        print("No messages found.")
        return

    # === Time range ===
    min_time = min(m['time'] for m in messages)
    max_time = max(m['time'] for m in messages)
    duration_days = (max_time - min_time).days
    print(f"Time range: {min_time.date()}  →  {max_time.date()}  ({duration_days} days)")

    # === Type distribution ===
    type_counts = Counter(m['type_name'] for m in messages)
    print("\n--- Message Type Distribution ---")
    for t, count in type_counts.most_common(15):
        pct = count / total * 100
        print(f"  {t or '(empty)':<20} {count:>7,}  ({pct:5.1f}%)")

    # === Sender distribution ===
    sender_counts = Counter(m['talker'] for m in messages)
    print("\n--- Talker Distribution ---")
    for name, count in sender_counts.most_common(10):
        print(f"  {name:<15} {count:>7,}")

    # === Monthly distribution ===
    monthly = defaultdict(int)
    for m in messages:
        key = m['time'].strftime("%Y-%m")
        monthly[key] += 1

    print("\n--- Messages per Month (top 12) ---")
    for month, count in sorted(monthly.items(), key=lambda x: -x[1])[:12]:
        print(f"  {month}: {count:,}")

    # === Conversation gaps (for slicing) ===
    messages_sorted = sorted(messages, key=lambda x: x['time'])
    gaps = []
    for i in range(1, len(messages_sorted)):
        delta = messages_sorted[i]['time'] - messages_sorted[i-1]['time']
        gaps.append(delta)

    large_gaps = [g for g in gaps if g > timedelta(hours=SLICE_GAP_HOURS)]
    print(f"\n--- Conversation Gaps (threshold = {SLICE_GAP_HOURS}h) ---")
    print(f"  Total gaps analyzed: {len(gaps):,}")
    print(f"  Gaps > {SLICE_GAP_HOURS}h: {len(large_gaps):,}")

    if large_gaps:
        print(f"  Largest gap: {max(large_gaps)}")
        print(f"  Average large gap: {sum(large_gaps, timedelta()) / len(large_gaps)}")

    # === Media coverage analysis (improved) ===
    print("\n--- Media File Coverage (improved matching) ---")

    # Sample raw src values for images
    image_src_samples = [m['src'] for m in messages if m['type_name'] == 'image' and m['src']][:5]
    print(f"  Sample image 'src' values from CSV: {image_src_samples}")

    # Images - collect all src values and try to match files by containing the src string
    image_srcs = [m['src'] for m in messages if m['type_name'] == 'image' and m['src']]
    unique_image_srcs = set(image_srcs)
    print(f"  Unique non-empty image src values in CSV: {len(unique_image_srcs):,}")

    if IMAGES_DIR.exists():
        actual_images = list(IMAGES_DIR.glob("*.*"))
        print(f"  Actual image files on disk: {len(actual_images):,}")

        # Improved matching: check if the src string appears inside any filename
        matched_count = 0
        for src in list(unique_image_srcs)[:200]:  # sample 200
            for f in actual_images:
                if src in f.name:
                    matched_count += 1
                    break
        print(f"  Improved sample match rate (first 200 unique src): {matched_count}/{min(200, len(unique_image_srcs))} ({matched_count/min(200, len(unique_image_srcs))*100:.1f}%)")

    # Videos
    video_srcs = [m['src'] for m in messages if m['type_name'] == 'video' and m['src']]
    print(f"  Video src entries in CSV: {len(video_srcs):,}")
    if VIDEOS_DIR.exists():
        print(f"  Actual video files on disk: {len(list(VIDEOS_DIR.glob('*.mp4'))):,}")

    # Stickers
    sticker_srcs = [m['src'] for m in messages if m['type_name'] == 'sticker' and m['src']]
    print(f"  Sticker src entries in CSV: {len(sticker_srcs):,}")
    if EMOJIS_DIR.exists():
        print(f"  Actual emoji files on disk: {len(list(EMOJIS_DIR.glob('*.*'))):,}")

    # === Proposed initial slices ===
    print(f"\n--- Suggested Initial Slices (gap > {SLICE_GAP_HOURS}h) ---")
    current_slice_start = messages_sorted[0]['time']
    slice_count = 1
    for i, g in enumerate(gaps):
        if g > timedelta(hours=SLICE_GAP_HOURS):
            end_time = messages_sorted[i]['time']
            print(f"  Slice {slice_count:02d}: {current_slice_start.date()} → {end_time.date()}  ({(end_time - current_slice_start).days} days, ~{i - (slice_count-1)*1000 if slice_count > 1 else i} msgs est.)")
            current_slice_start = messages_sorted[i+1]['time']
            slice_count += 1
    # Last slice
    print(f"  Slice {slice_count:02d}: {current_slice_start.date()} → {messages_sorted[-1]['time'].date()}  ({(messages_sorted[-1]['time'] - current_slice_start).days} days)")

    # === Better practical slicing proposals ===
    print("\n--- Practical Slicing Proposals (recommended for this data) ---")
    print("  Because there is almost no natural long gap, pure time-gap slicing is not useful.")
    print("  Recommended approaches:")
    print("  1. Monthly slices (simple, predictable)")
    print("  2. Quarterly (every 3 months) + manual merge in app")
    print("  3. High-activity periods (top months) as separate slices")

    # Monthly slice count
    months = sorted(set(m['time'].strftime("%Y-%m") for m in messages))
    print(f"\n  Monthly approach would create ~{len(months)} slices (one per month with data).")

    # Quarterly suggestion
    print("  Quarterly example:")
    quarters = {}
    for m in messages:
        q = f"{m['time'].year}-Q{(m['time'].month-1)//3 + 1}"
        quarters[q] = quarters.get(q, 0) + 1
    for q in sorted(quarters):
        print(f"    {q}: ~{quarters[q]:,} messages")

    print("\n" + "=" * 60)
    print("Analysis complete. Use these numbers to decide slicing strategy.")
    print("=" * 60)


if __name__ == "__main__":
    main()
