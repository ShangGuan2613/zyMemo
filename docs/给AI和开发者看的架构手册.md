# zyMemo 技术架构与实现手册（给 AI 和未来开发者）

> **目标**：做一个 5–10 年后依然容易维护、不会变成屎山的温馨可爱 U 盘回忆册程序。
> 配套文档：`给你们看的设计说明.md`（给使用者的非技术描述）

---

## 1. 核心设计目标（永远不要偏离）

1. **极致降低长期维护成本** > 任何炫技功能
2. **一个“完整的数据库”**：用户插 U 盘就能看到全部内容，备份 = 复制文件夹
3. **严格的关注点分离**：UI 永远不知道数据怎么存、文件在哪里
4. **可爱温馨的体验必须真实存在**，不能因为“技术简单”就牺牲感觉
5. **导入微信数据** 永远是独立的一次性工具，和运行时 App 彻底隔离

---

## 2. 推荐技术栈（2026 年版本）

| 层级         | 推荐技术              | 理由（维护角度）                              |
|--------------|-----------------------|-----------------------------------------------|
| 桌面框架     | **Tauri 2**           | 体积 8-15MB、启动快、系统 WebView、安全面小、易打包 portable |
| 后端语言     | Rust                  | 数据安全（SQLite）、强类型、编译时防错         |
| 前端         | Svelte 5（首选）或轻量 React + Tailwind | 体积小、响应式简单、长期维护成本低             |
| 数据库       | **SQLite**（单文件 `zy_memo.db`） | ACID、FTS5 搜索、备份简单、一个文件 = 完整数据库 |
| 媒体存储     | 扁平 `media/` + 内容哈希命名 | 去重、校验完整性、避免中文路径和符号问题       |
| 状态管理     | 极简（Context + hooks / Svelte runes） | 禁止 6 个全局 store 互相联动                  |
| 构建打包     | Tauri + cargo         | 输出真正的 portable 文件夹或 exe               |

**坚决不选**：
- Electron（太大、太重、维护成本高）
- 纯文件 JSON + 手写原子写入（太脆弱）
- 媒体物理重复（by-event/ 文件夹）

---

## 3. 整体架构（三层干净分离）

```
UI Layer（只负责显示和交互）
    ↓ 通过 typed commands / hooks
Command / Application Layer（Rust）
    ↓ 通过 Repository
Data Layer（SQLite + 文件系统）
```

**严格规则**：
- UI 层**永远**不直接读写文件、不写 SQL、不知道路径
- 所有数据操作必须走 Repository
- 只有 Rust 那一层知道 `data/` 文件夹在哪

---

## 4. 推荐文件夹结构

```
zyMemo/
├── src-tauri/                  # Rust 后端（数据和命令的唯一主人）
│   ├── src/
│   │   ├── main.rs
│   │   ├── db/                 # SQLite 相关
│   │   │   ├── schema.sql
│   │   │   ├── migrations/
│   │   │   └── repositories/   # SliceRepo, MessageRepo, AnnotationRepo, MediaRepo
│   │   ├── commands/           # Tauri 暴露给前端的函数（薄薄一层）
│   │   └── error.rs            # 统一错误类型
│   └── tauri.conf.json
│
├── src/                        # 前端（轻量）
│   ├── components/
│   │   ├── layout/             # LeftSidebar, MainContent, RightAnnotationPanel, Splitter
│   │   ├── chat/               # MessageBubble, TextMessageFlow
│   │   ├── media/              # MediaCard, MediaMasonry, Lightbox
│   │   ├── annotation/         # AnnotationCard, AnnotationForm, TagSelector
│   │   └── ui/                 # 通用可爱组件
│   ├── stores/                 # 最多一个极小的 prefs store
│   ├── hooks/                  # useRepository, useCurrentAnnotations 等
│   └── types/                  # 从 Rust 生成或手写的类型
│
├── scripts/
│   └── import_wechat.py        # **独立工具**，把微信导出转成 zy_memo.db + media/
│
├── docs/
│   ├── 给你们看的设计说明.md
│   └── 给AI和开发者看的架构手册.md   ← 本文件
│
├── resources/                  # 可爱插画（小熊、小猫）
└── data/                       # 运行时数据（开发时用，真实 U 盘上也这样）
    ├── zy_memo.db
    └── media/
```

---

## 5. 核心组件拆解（位置 + 职责）

| 组件                      | 文件位置（示例）                        | 职责                                      | UI 风格要求                     |
|---------------------------|-----------------------------------------|-------------------------------------------|---------------------------------|
| LeftSidebar               | src/components/layout/LeftSidebar.tsx  | 展示两个 Tab + 目录树/事件列表            | 奶油背景 + 粉色高亮 Tab         |
| TextSidebarContent        | 同上                                    | 按月分组的 Slice 列表                     | 柔和圆角卡片                    |
| MediaSidebarContent       | 同上                                    | 按事件的分组文件夹（纯查询驱动）          | 同上                            |
| MainContent               | src/components/layout/MainContent.tsx  | 根据 Tab 渲染聊天流或媒体瀑布流           | 大量留白、温柔过渡              |
| TextMessageFlow           | src/components/chat/TextMessageFlow.tsx| 虚拟滚动 + 气泡渲染                       | 自己右对齐浅粉、对方左对齐薄荷绿，超大圆角 |
| MessageBubble             | 同上                                    | 单条消息（文字/图片/视频/语音/表情）      | 可爱、带时间戳                  |
| MediaMasonry              | src/components/media/MediaMasonry.tsx  | 瀑布流照片墙（IntersectionObserver 懒加载）| 圆角 2xl，hover 轻微放大        |
| MediaCard                 | 同上                                    | 单张媒体缩略图 + 类型角标                 | 柔和阴影                        |
| RightAnnotationPanel      | src/components/annotation/             | 当前选中对象的批注列表 + 新建表单         | 毛玻璃 + 樱花粉到薄荷渐变顶部   |
| AnnotationCard            | 同上                                    | 单条批注（标签 + Markdown 内容 + 时间）   | 白色卡片 + 粉色小标签           |
| TagSelector               | 同上                                    | 8 个固定标签多选                          | 选中时粉色高亮，圆形标签        |
| Lightbox                  | src/components/media/Lightbox.tsx      | 全屏看大图，支持翻页                      | 黑色半透明背景，图片居中        |
| Splitter                  | src/components/layout/Splitter.tsx     | 可拖拽的分隔条                            | 极细、hover 时变色              |

**原则**：每个组件只做一件事。复杂逻辑下沉到 hooks 或 commands。

---

## 6. 数据模型（简化版）

核心表（SQLite）：

- `slices`（事件片段）：id, month, title, start_date, end_date, message_count, cover_media_id...
- `messages`：id, slice_id, time, type, content, is_sent_by_me, media_id (nullable)
- `media_assets`：id, hash, relative_path, type, width, height, duration...
- `annotations`：id, target_type ('slice'|'message'|'media'), target_id, content, tags (JSON array), created_at, updated_at
- `settings`：单行，存窗口宽度、最后打开的 Tab 等

**批注的三种目标**用 `target_type + target_id` 统一处理，简单干净。

---

## 7. 铁一般的实现原则（防止屎山）

1. **DB 是唯一真相来源**。前端缓存只做性能优化，刷新必能拿到最新。
2. **UI 层禁止任何 fs、SQL、路径拼接**。只能调用 `invoke('get_xxx')` 或自定义 hooks。
3. **一个功能只改一个地方**。新增批注目标类型？只在 Repository 里加方法 + 前端一个 hook。
4. **禁止 6 个全局 store 互相联动**。最多一个极小的 prefs store。
5. **错误必须对用户友好**。U 盘被拔 → 友好提示 + 自动回滚，而不是崩溃。
6. **导入工具永远独立**。`scripts/import_wechat.py` 死了，App 依然能正常打开已有数据。
7. **每次写数据都要经过事务 + 备份**。SQLite 的事务比手写 JSON 安全 100 倍。
8. **组件 props 尽量只传数据，不传函数**（除非必要）。
9. **可爱风格是第一优先级**。即使为了性能，也不能牺牲圆角、动画、留白。
10. **加新功能前先问**：“这个功能 5 年后还会有人维护吗？它会不会让代码复杂度上升？”

---

## 8. 微信导入流程（必须独立，当前默认 WeFlow CSV）

**核心原则**：App 运行时**永远不直接接触微信原始数据库**。所有数据清洗、事件切片、媒体归一化都在独立的导入工具中完成。导入工具死了，App 依然能正常打开已有数据。

### 当前默认输入格式（基于 WeFlow 等 CSV 导出工具）

你提到目前预计使用 **WeFlow（微流）** 或类似工具导出 CSV（或 Excel/JSON）。我们据此定义了**当前默认输入格式**，方便立刻往下推进实现。

**典型导出文件夹结构**（WeFlow 导出后）：
```
weflow_export_与TA的聊天_2025-03/
├── messages.csv
├── images/
│   └── 20250315_143230.jpg
├── videos/
├── voice/
└── stickers/
```

**messages.csv 默认表头（我们会做兼容映射）**：

| 标准化列名（import 脚本内部使用） | WeFlow 常见对应列（中文/英文）                  | 必填 | 说明 |
|----------------------------------|------------------------------------------------|------|------|
| message_id                       | localId / serverId / id                        | 是   | 消息唯一标识 |
| timestamp                        | createTime / 发送时间                          | 是   | 优先支持 ISO 8601 或 Unix 时间戳 |
| sender_name                      | displayName / senderUsername / 发送者 / 备注名 | 是   | 用于显示和判断 is_self |
| is_self                          | isSend / 是否自己                              | 是   | 0=对方，1=自己 |
| type                             | localType / mediaType / 类型                   | 是   | text / image / video / voice / sticker / file / system |
| content                          | content / parsedContent / 消息内容             | 否   | 纯文本内容；媒体消息通常为空 |
| media_filename                   | mediaFileName / 媒体文件名                     | 否   | 媒体消息填写文件名（如 "xxx.jpg"） |
| media_subdir                     | （从实际路径推断或额外列）                     | 否   | images / videos / voice / stickers |

**媒体文件处理**：
- 导出时务必同时导出媒体文件，放在与 CSV 同级的对应子文件夹。
- 导入脚本会：
  1. 计算文件内容哈希（blake3 或 sha256）
  2. 去重后复制到最终 `data/media/{type}/<hash>.<ext>`
  3. 在数据库中记录相对路径

**事件切片（Slice）逻辑**（导入时自动 + 人工辅助）：
- 按连续时间 + 消息密度自动分组（超过 4-6 小时无消息视为新事件）
- 生成每个 Slice 的标题、起止日期、消息数
- 交互式让用户选择 eventType（日常/旅行/争吵/纪念日等 8 个选项）和自定义标题
- 支持批量设置同一月份的多个 Slice

### 导入脚本职责（scripts/import_wechat.py）

- 读取 CSV（pandas 或标准库，自动处理中文表头和编码）
- 规范化数据 → 内部 Message / MediaAsset 对象
- 自动 + 交互式切片
- 媒体哈希去重 + 复制
- 写入 SQLite（事务保证）
- 生成处理报告（总消息数、媒体数、切片列表、耗时）
- 可选：生成 `data/annotations.json` 初始空文件

**灵活性设计**：
- 所有解析逻辑集中在 `scripts/importers/weflow.py`（或其他工具对应模块）
- 以后换工具只需新增一个 parser，核心切片和入库逻辑完全复用
- 一旦你导出一个真实的小样本 CSV（哪怕只 200 条），我可以立刻精确调整字段映射

**App 启动时行为**：
- 检测 `data/zy_memo.db` 是否存在
- 不存在 → 友好提示：“请先运行导入工具生成数据文件夹”
- 存在 → 直接加载使用

这样既满足你当前用 WeFlow CSV 的计划，又为未来工具变化留了极低成本的扩展空间。

---

## 9. U 盘便携与安全要点

- 用 `std::env::current_exe()` 的父目录找 `data/`
- 启动时做 `PRAGMA quick_check`
- 写批注前自动做轻量备份（复制 db 文件）
- 提供“安全弹出”引导界面
- 所有媒体路径用相对路径存，哈希防重复和改名

---

## 10. 开发节奏建议（PR 顺序）

参考文档底部 PR Plan（8 个可独立合并的 PR）。

**永远先做**：PR 1 —— 可爱的三段式骨架 + mock 数据 + 主题系统跑起来。**先验证感觉，再写数据层**。

**当前状态（2026-05-27）**：前端骨架已跑通（Svelte 5 + Tauri 2）。运行 `npm run tauri:dev` 即可看到三栏布局 + 聊天气泡 + 瀑布流 + 右侧批注面板（全部用 Mock 数据）。颜色、圆角、交互均已按「温馨可爱」标准实现。后续 PR 会逐步接入真实 SQLite 数据。

---

## 11. 验收标准（做完一个功能就自问）

- 一个对技术不熟的人能不能 5 分钟内理解这个文件改了什么？
- 如果把这个功能删掉，代码会不会突然干净很多？
- 两年后我自己看这段代码会不会想骂人？

---

**最后提醒**：

这个项目最珍贵的不是代码，而是**用户写下的那些批注**。  
所有技术决策，都要为“让这些小纸条安全、温暖地保存十年”服务。

如果你在实现过程中发现某个设计会让未来维护变难，请立刻停下来，回来修改这份文档。

---

文档版本：v3.1（已适配 WeFlow CSV 默认输入格式）
配套使用文档：`docs/给你们看的设计说明.md`

**变更记录**：
- v3.1：明确当前默认使用 WeFlow 等工具导出的 CSV 作为导入输入，增加了详细字段映射表和媒体处理说明。