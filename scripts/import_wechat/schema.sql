-- zyMemo 微信导入工具输出数据库 schema
-- 严格遵循 docs/给AI和开发者看的架构手册.md（维护优先版）
-- 目标：单个 SQLite 文件 + 外部 media/ 目录 = 完整可移植数据

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;   -- 更好并发与崩溃恢复（U 盘场景友好）

-- ============================================================
-- 1. slices：事件片段（回忆的基本单位）
-- ============================================================
CREATE TABLE IF NOT EXISTS slices (
    id               TEXT PRIMARY KEY,           -- slice_20250315_daily 或自定义
    month            TEXT NOT NULL,              -- '2025-03'
    title            TEXT NOT NULL,              -- '3月15-18日 日常聊天'
    start_date       TEXT NOT NULL,              -- '2025-03-15'
    end_date         TEXT NOT NULL,              -- '2025-03-18'
    message_count    INTEGER NOT NULL DEFAULT 0,
    cover_media_id   TEXT,                       -- 指向 media_assets.id，作为封面
    event_type       TEXT,                       -- 日常/感动/旅行/争吵/纪念日/节日/表白/特殊事件/其他
    created_at       TEXT DEFAULT (datetime('now')),
    updated_at       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_slices_month ON slices(month);
CREATE INDEX IF NOT EXISTS idx_slices_dates ON slices(start_date, end_date);

-- ============================================================
-- 2. media_assets：媒体文件元数据（哈希命名，扁平存储）
-- ============================================================
CREATE TABLE IF NOT EXISTS media_assets (
    id               TEXT PRIMARY KEY,           -- 通常就是 hash
    hash             TEXT UNIQUE NOT NULL,       -- SHA-256 或 MD5（内容哈希）
    relative_path    TEXT NOT NULL,              -- media/xxxx.jpg （相对于 data/ 根）
    type             TEXT NOT NULL,              -- image / video / voice / file / sticker
    mime_type        TEXT,
    width            INTEGER,
    height           INTEGER,
    duration         REAL,                       -- 秒（视频/语音）
    size_bytes       INTEGER,
    original_name    TEXT,                       -- 微信里的原始文件名（如果有）
    created_at       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_media_hash ON media_assets(hash);
CREATE INDEX IF NOT EXISTS idx_media_type ON media_assets(type);

-- ============================================================
-- 3. messages：单条消息
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id               TEXT PRIMARY KEY,           -- msg_<timestamp>_<随机> 或微信内部 id
    slice_id         TEXT NOT NULL,
    time             TEXT NOT NULL,              -- ISO8601 '2025-03-15T14:32:10.123+08:00'
    type             TEXT NOT NULL,              -- text / image / video / voice / sticker / file / system / other
    content          TEXT,                       -- 文字内容，或富文本 JSON（复杂 appmsg 可放这里）
    is_sent_by_me    INTEGER NOT NULL DEFAULT 0, -- 1=我发的，0=对方发的
    media_id         TEXT,                       -- 关联 media_assets.id（可空）
    wxid             TEXT,                       -- 发送者 wxid（群聊时有用）
    extra            TEXT,                       -- JSON：原始类型、撤回标记、红包信息等
    created_at       TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (slice_id) REFERENCES slices(id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media_assets(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_slice_time ON messages(slice_id, time);
CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(time);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);

-- ============================================================
-- 4. annotations：用户小纸条（初始为空，App 运行时写入）
-- 目标类型：slice / message / media
-- ============================================================
CREATE TABLE IF NOT EXISTS annotations (
    id               TEXT PRIMARY KEY,
    target_type      TEXT NOT NULL,              -- 'slice' | 'message' | 'media'
    target_id        TEXT NOT NULL,              -- slices.id 或 messages.id 或 media_assets.id
    content          TEXT NOT NULL,              -- Markdown 支持
    tags             TEXT,                       -- JSON array: ["感动","甜蜜"]
    created_at       TEXT DEFAULT (datetime('now')),
    updated_at       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_annotations_target ON annotations(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_annotations_updated ON annotations(updated_at);

-- ============================================================
-- 5. settings：运行时偏好（可选，App 也可自己管理）
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    key              TEXT PRIMARY KEY,
    value            TEXT
);

-- 初始化默认设置
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('schema_version', '1.0'),
    ('imported_at', datetime('now')),
    ('wechat_version', '4.1.7.2'),
    ('import_tool', 'zyMemo import_wechat');

-- ============================================================
-- 视图：方便查询
-- ============================================================
CREATE VIEW IF NOT EXISTS v_slice_summary AS
SELECT
    s.id,
    s.title,
    s.month,
    s.event_type,
    s.start_date,
    s.end_date,
    s.message_count,
    (SELECT COUNT(*) FROM annotations a WHERE a.target_type='slice' AND a.target_id=s.id) AS annotation_count,
    m.relative_path AS cover_path
FROM slices s
LEFT JOIN media_assets m ON m.id = s.cover_media_id;

-- 全文搜索（可选，后续增强）
-- CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(content, content='messages', content_rowid='rowid');

-- ============================================================
-- 完成提示
-- ============================================================
-- 导入完成后，zyMemo App 启动时检测 data/zy_memo.db 即可直接使用。
-- 所有批注都写在这个库里，备份 = 复制整个 data/ 文件夹。
