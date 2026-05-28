use serde::{Deserialize, Serialize};

// Core domain models for zyMemo
// These are the contracts between frontend and Rust layer.
// UI code should never know about how these are stored.

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Slice {
    pub id: String,
    pub title: String,
    pub start_date: String,
    pub end_date: String,
    pub message_count: i32,
    pub event_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Message {
    pub id: String,
    pub slice_id: String,
    pub time: String,           // HH:mm or ISO
    pub from_me: bool,
    pub r#type: String,         // text, image, video, voice, sticker
    pub content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaItem {
    pub id: String,
    pub title: String,
    pub url: String,
    pub date: String,
    pub r#type: String,         // image / video
    // 更丰富的图片信息
    pub size_bytes: Option<i64>,
    pub width: Option<i32>,
    pub height: Option<i32>,
    // 原始消息时间（由 backfill 脚本从文件 mtime 回填，作为照片真实时间的代理）
    pub message_time: Option<String>,
    // Phase 2: 图片的聊天上下文 + 情绪（从 photo_contexts 表来，真实可展示）
    pub context_text: Option<String>,
    pub emotion_tag: Option<String>,
}

// 新增：图片的聊天上下文信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhotoContext {
    pub media_id: String,
    pub message_time: String,
    pub context_text: Option<String>,
    pub emotion_tag: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Annotation {
    pub id: String,
    pub target_type: String,    // "slice" | "message" | "media"
    pub target_id: String,
    pub content: String,
    pub tags: Vec<String>,
    pub created_at: String,     // ISO8601 string for simplicity
    pub updated_at: String,
}
