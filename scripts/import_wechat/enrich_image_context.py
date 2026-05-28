#!/usr/bin/env python3
"""
Phase 2 for image information optimization:
Enrich images with nearby chat context and basic emotion tags.

This script does NOT modify the database yet — it is for analysis and planning.
It shows what kind of rich information we can attach to each photo.

Run from project root:
    python3 scripts/import_wechat/enrich_image_context.py
"""

import csv
from datetime import datetime, timedelta
from collections import defaultdict
import re

CSV_PATH = "backup/texts/私聊_羊.csv"

# Simple emotion keywords (extend as needed)
EMOTION_KEYWORDS = {
    "开心": ["哈哈", "笑", "开心", "高兴", "太好了", "棒", "爱你"],
    "甜蜜": ["爱你", "亲亲", "抱抱", "想你", "甜", "么么"],
    "想念": ["想你", "好久不见", "想念"],
    "日常": ["吃饭", "上班", "睡觉", "天气", "今天"],
    "感动": ["感动", "哭了", "眼泪", "谢谢"],
    "争执": ["生气", "吵", "为什么", "算了", "滚"],
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
    """Simple rule-based emotion from a list of nearby texts."""
    combined = " ".join(texts).lower()
    scores = defaultdict(int)
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                scores[emotion] += 1
    if not scores:
        return "日常"
    return max(scores, key=scores.get)

def main():
    print("Loading CSV and building time index...")
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

    # Group by rough day for faster search
    by_day = defaultdict(list)
    for m in messages:
        key = m['time'].date()
        by_day[key].append(m)

    image_msgs = [m for m in messages if m['type'] == 'image']
    print(f"Found {len(image_msgs)} image messages in CSV.\n")

    print("=== Example: Image + nearby context + emotion ===\n")

    for img in image_msgs[:5]:  # Show first 5 as examples
        day = img['time'].date()
        day_msgs = by_day.get(day, [])

        # Find messages within ±5 minutes
        window = timedelta(minutes=5)
        nearby = [
            m for m in day_msgs
            if abs((m['time'] - img['time']).total_seconds()) <= window.total_seconds()
            and m['type'] == 'text'
        ]
        nearby.sort(key=lambda x: abs((x['time'] - img['time']).total_seconds()))

        context_texts = [m['content'] for m in nearby[:3]]
        emotion = detect_emotion(context_texts)

        print(f"📷 Image at {img['time'].strftime('%Y-%m-%d %H:%M')} (src: {img['src'][:12]}...)")
        print(f"   Nearby context ({len(nearby)} texts):")
        for m in nearby[:3]:
            delta = (m['time'] - img['time']).total_seconds()
            print(f"     [{delta:+.0f}s] {m['talker']}: {m['content'][:45]}")
        print(f"   → Suggested emotion: {emotion}")
        print(f"   → Suggested title: 照片 · {img['time'].strftime('%m月%d日')} · {emotion}\n")

    print("=" * 60)
    print("This is the kind of rich information we can attach to every photo.")
    print("Next step: persist this context into the database and show it in the UI cards.")
    print("=" * 60)

if __name__ == "__main__":
    main()
