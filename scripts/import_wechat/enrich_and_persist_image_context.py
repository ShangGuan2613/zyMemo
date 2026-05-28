#!/usr/bin/env python3
"""
Phase 2 - Persist image context and emotion into the database.

This script:
1. Analyzes the CSV for image messages + nearby text context.
2. Computes simple emotion tags.
3. Persists the data into a new clean table `photo_contexts`.

This is safe: it creates a new table and does not break existing data.

Run after the daily importer:
    python3 scripts/import_wechat/enrich_and_persist_image_context.py
"""

import csv
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

CSV_PATH = "backup/texts/私聊_羊.csv"
DB_PATH = "data/zy_memo_real.db"

# Simple emotion keywords (expand as needed)
EMOTION_KEYWORDS = {
    "开心": ["哈哈", "笑", "开心", "高兴", "太好了", "棒", "爱你", "哈哈哈"],
    "甜蜜": ["爱你", "亲亲", "抱抱", "想你", "甜", "么么", "喜欢"],
    "想念": ["想你", "好久不见", "想念", "想念你"],
    "日常": ["吃饭", "上班", "睡觉", "天气", "今天", "在干嘛"],
    "感动": ["感动", "哭了", "眼泪", "谢谢", "谢谢你"],
    "争执": ["生气", "吵", "为什么", "算了", "滚", "红温"],
}

def parse_time(ts_str):
    if not ts_str:
        return None
    ts_str = ts_str.strip().replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(ts_str)
    except:
        return None

def detect_emotion(texts):
    combined = " ".join(texts).lower()
    scores = defaultdict(int)
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                scores[emotion] += 1
    if not scores:
        return "日常"
    return max(scores, key=scores.get)

def get_context_snippet(nearby_messages, max_chars=120):
    """Create a short, readable context string."""
    if not nearby_messages:
        return ""
    parts = []
    for m in nearby_messages[:3]:
        speaker = m['talker'][:4] if m['talker'] else "对方"
        text = m['content'][:40]
        parts.append(f"{speaker}: {text}")
    snippet = "；".join(parts)
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars] + "…"
    return snippet

def main():
    print("Loading CSV...")
    messages = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = parse_time(row.get('CreateTime'))
            if not t:
                continue
            messages.append({
                'id': row['id'],
                'type': row['type_name'],
                'talker': row['talker'].strip(),
                'content': row['msg'],
                'src': row['src'].strip(),
                'time': t,
            })

    # Group by day for performance
    by_day = defaultdict(list)
    for m in messages:
        by_day[m['time'].date()].append(m)

    image_msgs = [m for m in messages if m['type'] == 'image']
    print(f"Found {len(image_msgs)} image messages. Processing context...")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create clean table for enriched photo data (safe, additive)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS photo_contexts (
            media_id TEXT PRIMARY KEY,
            message_time TEXT,
            context_text TEXT,
            emotion_tag TEXT,
            FOREIGN KEY (media_id) REFERENCES media_assets(id)
        )
    """)
    conn.commit()

    enriched_count = 0
    for img in image_msgs:
        day = img['time'].date()
        day_msgs = by_day.get(day, [])

        # Find nearby text messages (±5 minutes)
        window = timedelta(minutes=5)
        nearby = [
            m for m in day_msgs
            if abs((m['time'] - img['time']).total_seconds()) <= window.total_seconds()
            and m['type'] == 'text'
        ]
        nearby.sort(key=lambda x: abs((x['time'] - img['time']).total_seconds()))

        context_text = get_context_snippet(nearby)
        emotion = detect_emotion([m['content'] for m in nearby])

        # Try to find matching media (best effort - can be improved later)
        # For now we use time proximity + rough matching. In real run we can improve.
        # Placeholder: we will link later. For demo we insert with time + context only.
        # In next iteration we will do better matching.

        # For demonstration, we insert using a synthetic key or skip for now.
        # Better: we will create the link in a follow-up pass.
        # For this safe step, we store the raw image message info + context.

        # To make it immediately usable, we can create entries keyed by the CSV src for now.
        # But to keep schema clean, let's just demonstrate and print.

        # For actual persistence in this version, we will skip perfect linking
        # and just show the power of the data. Real linking comes in next micro-step.

        enriched_count += 1
        if enriched_count <= 5:
            print(f"\n[Example {enriched_count}]")
            print(f"  Time: {img['time']}")
            print(f"  Context: {context_text}")
            print(f"  Emotion: {emotion}")

    print(f"\nPersisting context for {len(image_msgs)} images...")

    inserted = 0
    for img in image_msgs:
        day = img['time'].date()
        day_msgs = by_day.get(day, [])

        window = timedelta(minutes=5)
        nearby = [
            m for m in day_msgs
            if abs((m['time'] - img['time']).total_seconds()) <= window.total_seconds()
            and m['type'] == 'text'
        ]
        nearby.sort(key=lambda x: abs((x['time'] - img['time']).total_seconds()))

        context_text = get_context_snippet(nearby)
        emotion = detect_emotion([m['content'] for m in nearby])

        # Use CSV image message id as temporary key for now.
        # We will improve matching to real media_id in the next micro-step.
        temp_key = f"csv_img_{img['id']}"

        cur.execute("""
            INSERT OR REPLACE INTO photo_contexts 
            (media_id, message_time, context_text, emotion_tag)
            VALUES (?, ?, ?, ?)
        """, (temp_key, img['time'].isoformat(), context_text, emotion))
        inserted += 1

    conn.commit()
    print(f"Successfully persisted {inserted} photo contexts into 'photo_contexts' table.")

    print("\n✅ Data is now in the database.")
    print("Next safe micro-step: Improve matching from CSV images to actual media_assets files, then surface this context in the UI cards.")

    conn.close()

if __name__ == "__main__":
    main()
