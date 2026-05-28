# zyMemo — 项目完整设计文档

---

## 一、产品概述

### 1.1 产品形态
- 一个**单文件 Windows 可执行程序（.exe，约 80–120MB）**，直接放在 U 盘根目录
- 绿色便携版，无需安装，双击即可运行
- 完全离线、本地运行，所有数据存储在 U 盘 `data/` 文件夹内

### 1.2 核心用途
两人专属的情感纪念礼物。用于长期保存和温习一整年的微信聊天记录，并添加私人批注。

### 1.3 核心价值
让聊天记录不再是冷冰冰的数据库，而是可以随时重温、可以写下私人批注的温暖回忆册。最重要的是**批注功能**——可以在任何一条消息、任何一张照片、任何一个事件片段上写下只属于两个人的心情和故事。

### 1.4 使用场景
- 闲暇时插上 U 盘，打开 exe，重温某一年的聊天
- 在某个事件/片段下写批注（日常、争吵、旅行、纪念日等）
- 想看某段时间的所有图片/视频时，切换到媒体库模式
- 作为长期保存的数字礼物，多年后依然可以打开回忆

---

## 二、技术栈

| 层 | 技术选型 | 说明 |
|----|---------|------|
| 桌面框架 | **Electron** | 主进程 + 渲染进程架构 |
| 构建工具 | **electron-vite + Vite** | 启动快、HMR 开发体验好 |
| 前端框架 | **React 18 + TypeScript** | 严格模式，全量类型覆盖 |
| UI 组件库 | **shadcn/ui + Tailwind CSS** | 高度可定制的治愈风组件 |
| 动画 | **Framer Motion** | 0.2s–0.3s 缓动弹跳动画 |
| 状态管理 | **Zustand** | 轻量响应式全局状态 |
| 虚拟滚动 | **react-virtuoso** | 十万级消息流丝滑滚动 |
| 图标 | **Lucide Icons** | 圆润风格图标集 |
| Markdown 渲染 | **react-markdown** | 批注内容支持 Markdown |
| 文件读写 | **Electron preload + contextBridge** | 安全隔离的原子文件操作 |
| 打包 | **electron-builder** | 输出单文件 Windows .exe |
| 预处理脚本 | **Node.js + TypeScript** | 位于 `scripts/preprocess.ts` |

---

## 三、项目源码目录结构

```
zyMemo/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── electron.vite.config.ts
├── electron-builder.yml
│
├── src/
│   ├── main/                         # Electron 主进程
│   │   ├── index.ts                  # 入口：创建窗口、注册 IPC
│   │   └── fileService.ts           # 文件读写服务（原子写入、读取、备份）
│   │
│   ├── preload/                      # Preload 脚本
│   │   └── index.ts                  # contextBridge 暴露 fileAPI
│   │
│   └── renderer/                     # React 渲染进程
│       ├── index.html
│       ├── main.tsx                  # React 入口
│       ├── App.tsx                   # 根组件（布局 + 路由）
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── LeftSidebar.tsx
│       │   │   ├── MainContent.tsx
│       │   │   ├── RightSidebar.tsx
│       │   │   └── Splitter.tsx          # 拖拽分隔条
│       │   │
│       │   ├── left-panel/
│       │   │   ├── ProfileHeader.tsx     # 头像 + 标题
│       │   │   ├── TabSwitcher.tsx       # 文字聊天 / 媒体库
│       │   │   ├── TextSidebarContent.tsx # 文字 Tab 目录树
│       │   │   ├── MediaSidebarContent.tsx # 媒体 Tab 文件夹列表
│       │   │   ├── SliceTree.tsx
│       │   │   └── EventFolderList.tsx
│       │   │
│       │   ├── main-content/
│       │   │   ├── ContentHeader.tsx      # 当前选中事件标题
│       │   │   ├── TextMessageFlow.tsx    # 消息流（文字模式）
│       │   │   ├── MediaFlow.tsx          # 媒体网格/时间线（媒体模式）
│       │   │   ├── MessageBubble.tsx      # 消息气泡组件
│       │   │   ├── MediaCard.tsx          # 媒体缩略图卡片
│       │   │   └── SearchBar.tsx          # 搜索条
│       │   │
│       │   ├── right-panel/
│       │   │   ├── AnnotationPanel.tsx    # 批注栏容器
│       │   │   ├── AnnotationCard.tsx     # 单条批注卡片
│       │   │   ├── AnnotationList.tsx     # 批注列表
│       │   │   ├── AddAnnotationForm.tsx # 添加批注表单
│       │   │   ├── TagSelector.tsx        # 8个固定标签选择器
│       │   │   └── EmptyState.tsx         # 空状态插图
│       │   │
│       │   ├── media-viewer/
│       │   │   ├── Lightbox.tsx           # 图片全屏查看
│       │   │   └── VideoPlayer.tsx        # 视频播放器
│       │   │
│       │   ├── context-menu/
│       │   │   └── ContextMenu.tsx        # 右键菜单（仅「添加批注」）
│       │   │
│       │   └── ui/                        # shadcn/ui 基础组件
│       │       ├── button.tsx
│       │       ├── card.tsx
│       │       ├── scroll-area.tsx
│       │       ├── tooltip.tsx
│       │       └── ...
│       │
│       ├── stores/                    # Zustand 状态管理
│       │   ├── useSidebarStore.ts
│       │   ├── useContentStore.ts
│       │   ├── useAnnotationStore.ts
│       │   ├── useDataStore.ts
│       │   ├── useUIStore.ts
│       │   └── useSettingsStore.ts
│       │
│       ├── hooks/                     # 自定义 Hooks
│       │   ├── useFileAPI.ts          # 封装 preload fileAPI 调用
│       │   ├── useCurrentAnnotations.ts
│       │   └── useMediaUrl.ts
│       │
│       ├── types/                     # TypeScript 类型定义
│       │   ├── data.ts               # Slice, Message, Annotation 等
│       │   ├── file-api.ts           # FileAPI 接口定义
│       │   └── store.ts              # Store 类型
│       │
│       └── utils/                     # 工具函数
│           ├── format.ts             # 日期格式化
│           ├── markdown.ts           # Markdown 渲染辅助
│           └── sync.ts               # 智能合并逻辑
│
├── scripts/
│   └── preprocess.ts                 # 数据预处理脚本
│
└── resources/                         # 静态资源
    ├── empty-state.svg               # 空状态插图
    └── icon.png                      # 应用图标
```

---

## 四、U盘运行时目录结构

```
U盘根目录/
├── zyMemo.exe                        # 单文件可执行程序
│
├── data/                             # 所有用户数据（只读为主，仅 annotations.json 可写）
│   ├── slices.json                   # 切片/事件索引
│   ├── annotations.json              # 批注数据（唯一可写文件）
│   ├── settings.json                 # 用户偏好
│   │
│   ├── messages/                     # 消息分片（按 Slice，一个 Slice 一个文件）
│   │   ├── slice_20250315_daily.json
│   │   ├── slice_20250322_quarrel.json
│   │   ├── slice_20250401_travel.json
│   │   └── ...
│   │
│   └── media/                        # 媒体文件
│       ├── images/                   # 全部原始图片（扁平存放）
│       ├── videos/                   # 全部原始视频（扁平存放）
│       ├── voice/                    # 全部语音
│       ├── stickers/                 # 表情包
│       └── by-event/                 # 按事件分类的副本（与 slices 一一对应）
│           ├── 2025-03-日常聊天/
│           │   ├── images/
│           │   └── videos/
│           ├── 2025-03-争吵/
│           └── 2025-04-旅行回忆/
```

---

## 五、完整数据模型

### 5.1 slices.json

```jsonc
{
  "slices": [
    {
      "id": "slice_20250315_daily",
      "month": "2025-03",
      "eventType": "日常",
      "title": "3月15-18日 日常聊天",
      "startDate": "2025-03-15",
      "endDate": "2025-03-18",
      "messageCount": 1248,
      "coverImage": "media/by-event/2025-03-日常聊天/images/cover.jpg"
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 唯一标识，前缀 `slice_` |
| `month` | string | 是 | 所属月份，格式 `YYYY-MM` |
| `eventType` | string | 是 | 枚举值，见下方说明 |
| `title` | string | 是 | 人类可读的标题 |
| `startDate` | string | 是 | 起始日期 `YYYY-MM-DD` |
| `endDate` | string | 是 | 结束日期 `YYYY-MM-DD` |
| `messageCount` | number | 是 | 该 Slice 的消息总数 |
| `coverImage` | string | 否 | 封面图路径，相对于 `data/` |

**eventType 完整枚举：** `日常` | `争吵` | `旅行` | `纪念日` | `节日` | `表白` | `感动` | `特殊事件` | `其他`

### 5.2 messages/slice_{id}.json

```jsonc
{
  "sliceId": "slice_20250315_daily",
  "messages": [
    {
      "id": "msg_1748123456123",
      "sliceId": "slice_20250315_daily",
      "time": "2025-03-15T14:32:10.123Z",
      "type": "text",
      "content": "你今天过得怎么样呀～",
      "isSentByMe": false,
      "mediaPath": null
    },
    {
      "id": "msg_1748123456789",
      "sliceId": "slice_20250315_daily",
      "time": "2025-03-15T14:32:30.456Z",
      "type": "image",
      "content": "",
      "isSentByMe": true,
      "mediaPath": "media/by-event/2025-03-日常聊天/images/20250315_143230.jpg"
    }
  ]
}
```

**Message.type 完整枚举及渲染方式：**

| type | 渲染方式 | 说明 |
|------|---------|------|
| `text` | 标准气泡，`content` 为文本内容 | 最常规的消息类型 |
| `image` | 缩略图卡片（max-height 200px），点击打开 Lightbox | `mediaPath` 指向图片文件 |
| `video` | 缩略图 + 播放按钮叠加，点击打开 VideoPlayer | `mediaPath` 指向视频文件 |
| `voice` | 迷你音频条（播放/暂停 + 时长显示） | `mediaPath` 指向音频文件，`content` 存时长 |
| `sticker` | 直接渲染图片（静态/GIF），不做额外交互 | `mediaPath` 指向表情文件 |
| `file` | 图标 + 文件名 + 大小，提供「打开」按钮 | `mediaPath` 指向文件，`content` 存原始文件名 |
| `system` | **不渲染，直接过滤** | 红包、转账、加好友等系统消息一律跳过 |

### 5.3 annotations.json

```jsonc
{
  "annotations": [
    {
      "id": "ann_1748123456789",
      "targetType": "slice",
      "targetId": "slice_20250315_daily",
      "content": "这段日子她总是熬夜陪我加班，我却没有说一声谢谢…",
      "tags": ["感动", "想念", "纪念"],
      "createdAt": "2026-05-25T14:32:10.123Z",
      "updatedAt": "2026-05-25T14:35:22.456Z"
    },
    {
      "id": "ann_1748123456790",
      "targetType": "message",
      "targetId": "msg_1748123456789",
      "content": "这条消息让我想起第一次遇见她",
      "tags": ["甜蜜", "故事"],
      "createdAt": "2026-05-25T15:00:00.000Z",
      "updatedAt": "2026-05-25T15:00:00.000Z"
    },
    {
      "id": "ann_1748123456791",
      "targetType": "media",
      "targetId": "media/by-event/2025-03-日常聊天/images/20250315_143230.jpg",
      "content": "这张照片是她偷拍的，那天我穿了她最喜欢的白衬衫",
      "tags": ["甜蜜", "纪念"],
      "createdAt": "2026-05-25T16:00:00.000Z",
      "updatedAt": "2026-05-25T16:00:00.000Z"
    }
  ]
}
```

**三种 targetType 对应关系：**

| targetType | targetId 格式 | 被批注的对象 |
|------------|--------------|------------|
| `slice` | Slice.id | 整个事件片段 |
| `message` | Message.id | 单条消息 |
| `media` | 媒体文件相对于 data/ 的完整路径 | 单张图片/视频/语音 |

**八个固定批注标签：**

| 标签 | emoji | 含义 |
|------|-------|------|
| 感动 | ❤️ | 触动人心的瞬间 |
| 有趣 | 😂 | 搞笑的对话/事件 |
| 想念 | 😢 | 思念对方的时刻 |
| 纪念 | 🌟 | 值得记住的里程碑 |
| 争吵 | 🔥 | 吵架/冲突（也是一种重要回忆） |
| 日常 | 🐱 | 平淡温馨的日子 |
| 甜蜜 | 💕 | 甜蜜互动 |
| 故事 | 📖 | 值得讲给未来的故事 |

**不支持自定义标签**（避免同步冲突，保持极简）。

### 5.4 settings.json

```jsonc
{
  "leftWidth": 280,
  "rightWidth": 260,
  "rightCollapsed": false,
  "lastOpenedTab": "text",
  "lastSelectedSliceId": null,
  "lastSelectedEventFolder": null
}
```

---

## 六、数据流与 Electron 安全读写

### 6.1 整体数据流

```
                        预处理阶段（一次性）
┌──────────────────┐         ┌─────────────────────┐
│  微信聊天记录导出  │ ──────▶│ scripts/preprocess.ts│
│  (原始数据源)     │        │ 生成 slices.json     │
└──────────────────┘        │ 拆分 messages/       │
                             │ 整理 media/          │
                             │ 生成 by-event/       │
                             └─────────┬───────────┘
                                       │ 输出到 data/
                                       ▼
                               ┌───────────────┐
                               │  U盘 data/    │
                               │  (静态数据)   │
                               └───────┬───────┘
                                       │
                        运行时阶段（每次启动）
                                       │ Electron Main Process
                                       ▼
┌──────────────────────────────────────────────────┐
│              Preload (contextBridge)             │
│  暴露 fileAPI 对象给渲染进程：                    │
│                                                  │
│  fileAPI.readSlices()         → slices.json      │
│  fileAPI.readMessages(id)     → messages/slice_*.json │
│  fileAPI.readAnnotations()    → annotations.json │
│  fileAPI.writeAnnotations()   → 原子写入          │
│  fileAPI.getMediaUrl(path)    → file:// URL      │
│  fileAPI.checkMediaExists()   → boolean          │
│  fileAPI.getMediaDirectory()  → by-event/ 结构    │
│  fileAPI.getDataPath()        → data/ 绝对路径    │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│               Renderer Process                   │
│   React App 通过 useFileAPI Hook 调用            │
│   Zustand Store 持有数据                          │
│   虚拟滚动渲染 → 用户交互 → 批注 CRUD             │
└──────────────────────────────────────────────────┘
```

### 6.2 annotations.json 原子写入机制（最终方案）

**核心原则：绝不直接覆盖原文件，始终走「写入临时文件 → 校验 → 原子替换 → 备份」流水线。**

```
保存批注
    │
    ▼
1. 读入当前 annotations.json 并解析
    │ 若 JSON 损坏 → 加载最新备份 → 若仍失败 → 降级为空数组
    ▼
2. 在内存中新增/修改批注条目
    │
    ▼
3. 序列化新数据为 JSON 字符串
    │
    ▼
4. 写入临时文件 annotations.json.tmp
    │ 若 U 盘被拔出 / 磁盘满 → 捕获错误
    ▼
5. fs.readFile(tmp) 校验临时文件内容完整性
    │ 比对字节数 + 尝试 JSON.parse
    │ 若校验失败 → 删除 tmp → 返回错误
    ▼
6. fs.rename(tmp, annotations.json)   ← 原子操作
    │ Node.js fs.rename 在同一文件系统内为原子操作
    │ 要么成功替换，要么原文件保持不变
    ▼
7. 自动生成备份 annotations-backup-{timestamp}.json
    │ 保留最近 5 个备份，自动清理旧备份
    ▼
8. 返回成功
```

**异常处理：**

| 异常场景 | 行为 |
|---------|------|
| U盘拔出（写入中） | `fs.writeFile` 抛出 `ENXIO`/`EPERM`，捕获后提示「U 盘写入异常，请检查连接」 |
| 磁盘空间不足 | `fs.writeFile` 抛出 `ENOSPC`，提示「磁盘空间不足」 |
| JSON 解析失败（文件损坏） | 自动回退到最新备份文件；若备份也损坏，降级为空批注数组，提示「批注文件已损坏，已重置为空白状态」 |
| 快速连续保存（并发写入） | 使用队列机制，确保写入操作严格串行执行 |

### 6.3 Preload API 完整定义

```typescript
// src/preload/index.ts 通过 contextBridge 暴露

interface FileAPI {
  // === 读取 ===
  readSlices(): Promise<Slice[]>
  readSliceMessages(sliceId: string): Promise<{ sliceId: string; messages: Message[] }>
  readAnnotations(): Promise<Annotation[]>

  // === 写入（原子操作） ===
  writeAnnotations(annotations: Annotation[]): Promise<{ success: boolean; error?: string }>

  // === 媒体 ===
  getMediaUrl(relativePath: string): string  // 返回 file:// 协议 URL
  checkMediaExists(relativePath: string): Promise<boolean>
  getMediaDirectory(): Promise<EventFolder[]>

  // === 设置 ===
  readSettings(): Promise<Settings>
  writeSettings(settings: Settings): Promise<void>

  // === 同步 ===
  importAnnotationsFromFile(filePath: string): Promise<Annotation[]>

  // === 元信息 ===
  getDataPath(): Promise<string>

  // === 事件 ===
  onDataPathChange(callback: (path: string) => void): void
}
```

### 6.4 数据完整性保障

| 场景 | 处理方式 |
|------|---------|
| Message.sliceId 指向不存在的 Slice | 跳过该消息，console.warn 记录 |
| annotations.json 中 targetId 指向不存在的 Slice/Message/Media | 批注卡片上显示「目标已丢失」标记，不删除批注数据 |
| media/ 文件被手动删除 | 渲染时检测 `checkMediaExists`，不存在则显示「文件已丢失」占位图 |
| by-event/ 文件夹存在但 slices.json 无对应条目 | 媒体 Tab 仍显示该文件夹（容错显示） |
| data/ 目录不存在 | 启动时弹窗提示「请将程序放入包含 data/ 文件夹的 U 盘根目录」 |

---

## 七、预处理脚本（`scripts/preprocess.ts`）

### 7.1 输入

从微信 PC 版导出的聊天记录目录（用户通过命令行参数指定路径）。

微信导出目录结构（假设使用 WeChatMsg 等工具导出）：

```
导出目录/
├── 消息.csv / 消息.json           # 所有聊天消息
├── images/                         # 导出的图片
├── videos/                         # 导出的视频
├── voice/                          # 语音文件
├── stickers/                       # 表情包
└── files/                          # 文件类型消息
```

### 7.2 处理流程

```
1. 解析原始消息文件
   ├── 读取所有消息 → 解析时间、类型、发送者、内容
   ├── 过滤系统消息（红包、转账、加好友等）
   └── 统一时间格式为 ISO 8601
        │
2. 事件切片（Slice）
   ├── 按日期连续性 + 消息密度自动切分
   ├── 跨天讨论（超过 3 小时的间隔视为新事件）
   └── 生成每个 Slice 的 id、标题、时间范围、消息计数
        │
3. 事件类型标注（交互式）
   ├── 逐个展示 Slice 摘要（起止日期、消息数、前几条消息预览）
   ├── 用户从枚举值中选择 eventType
   ├── 用户可修改自动生成的 title
   └── 支持批量设置（同一月份连续 Slice 可批量标记为「日常」）
        │
4. 输出数据文件
   ├── 生成 slices.json
   ├── 按 Slice 拆分并生成 messages/slice_{id}.json
   ├── 复制媒体文件到 media/images/, media/videos/ 等
   ├── 创建 by-event/ 下的分类副本（硬链接或符号链接优先，节省空间）
   └── 若有图片，自动选取第一张作为 coverImage
        │
5. 生成处理报告
   ├── 总消息数、Slice 数量
   ├── 各 eventType 统计
   ├── 媒体文件总数和总大小
   └── 异常数据（无法解析的消息数等）
```

### 7.3 运行方式

```bash
npm run preprocess -- --input="/path/to/wechat-export" --output="./data"
```

### 7.4 输出文件

- `data/slices.json`
- `data/messages/slice_{id}.json` × N
- `data/media/images/`
- `data/media/videos/`
- `data/media/voice/`
- `data/media/stickers/`
- `data/media/by-event/`
- `data/annotations.json`（初始化为 `{ "annotations": [] }`）
- `data/settings.json`（初始化为默认值）

---

## 八、UI 风格与设计系统

### 8.1 全局 UI 风格：可爱治愈动态风

**配色方案：**

| Token | 色值 | 用途 |
|-------|------|------|
| `bg-primary` | `#f8f1eb` | 全局背景（温暖奶油米白） |
| `bg-surface` | `#fffaf0` | 卡片/面板背景（极浅杏仁色） |
| `accent-pink` | `#ff9eb1` | 强调色 / 批注色（温柔樱花粉） |
| `accent-mint` | `#a8e6cf` | 辅助强调色（薄荷绿） |
| `text-primary` | `#5c4636` | 主文字色（暖棕巧克力色） |
| `text-secondary` | `#8c7563` | 次要文字色 |
| `bg-muted` | `#f0e6d9` | 弱色背景 |
| `accent-light` | `#ffe4e1` | 亮粉辅助色 |

**圆角：** 全局统一 `rounded-3xl`（18px–24px），卡片、气泡、按钮、侧边栏统一采用。

**质感：**
- 大量毛玻璃效果：`backdrop-blur-2xl bg-white/75`
- 轻微外发光阴影：`shadow-[0_0_20px_-4px] shadow-pink-200/30`
- 所有卡片/面板带有极浅的粉色/薄荷绿渐变叠加

**动效：**
- 所有交互使用 Framer Motion，0.2s–0.3s ease-out
- Hover：上浮 3px + 阴影增强
- 点击/选中：0.15s 按压缩放 + 心跳回弹
- 新批注出现：从底部淡入 + 小心跳动画
- 模式切换：0.2s 淡出 + 0.25s 淡入

**整体感觉：** 温暖、柔软、治愈、干净。避免任何锐利、直角、科技感元素。

### 8.2 Tailwind 扩展配置

```ts
// tailwind.config.ts 关键扩展
theme: {
  extend: {
    colors: {
      cream: '#f8f1eb',
      almond: '#fffaf0',
      sakura: '#ff9eb1',
      mint: '#a8e6cf',
      cocoa: '#5c4636',
      taupe: '#8c7563',
      beige: '#f0e6d9',
      blush: '#ffe4e1',
    },
    borderRadius: {
      '3xl': '1.375rem',
      '4xl': '1.75rem',
    },
    boxShadow: {
      'healing': '0 0 20px -4px rgba(255, 158, 177, 0.3)',
      'card': '0 2px 16px -4px rgba(92, 70, 54, 0.08)',
    },
  },
}
```

---

## 九、UI 布局架构

### 9.1 经典三段式固定布局

```
┌───────────────────────────────────────────────────────────────┐
│  App 标题栏 (可选，使用系统默认窗口装饰)                        │
├─────────────┬─────────────────────────────────┬───────────────┤
│  LEFT       │          MAIN                  │    RIGHT      │
│  280px      │          flex-1                │    260px      │
│ (240-360)   │                                │  (220-min)    │
│             │                                │  可折叠       │
│ ┌─────────┐ │  ┌──────────────────────────┐  │ ┌───────────┐ │
│ │🌸头像   │ │  │  当前选中事件标题        │  │  │ 📝 批注   │ │
│ │标题     │ │  └──────────────────────────┘  │  │           │ │
│ ├─────────┤ │                                │  │ 批注卡片  │ │
│ │[文字聊天]│ │  ┌──────────────────────────┐  │  │ 批注卡片  │ │
│ │[媒体库 ]│ │  │                          │  │  │ 批注卡片  │ │
│ ├─────────┤ │  │  TextMessageFlow          │  │  │           │ │
│ │         │ │  │  或                       │  │  │ 空状态    │ │
│ │ Slice树 │ │  │  MediaFlow                │  │  │ 插图+文字 │ │
│ │ 或      │ │  │                          │  │  ├───────────┤ │
│ │ 事件文件夹│ │  │  react-virtuoso 虚拟滚动 │  │  │ 输入框    │ │
│ │         │ │  │                          │  │  │ 标签选择  │ │
│ │         │ │  │                          │  │  │ [保存按钮]│ │
│ └─────────┘ │  └──────────────────────────┘  │  └───────────┘ │
└─────────────┴─────────────────────────────────┴───────────────┘
```

### 9.2 左侧面板详细设计

**上部固定区（高度 68px）：**
- 对方头像（圆形，48px）+ 项目标题「与 TA 的回忆」

**Tab 切换区（高度 52px）：**
- 两个等宽大 Tab 按钮（类似 QQ PC 底部切换风格）
- Tab 1：💬 文字聊天（默认选中）
- Tab 2：🖼️ 媒体库
- 选中状态：粉色渐变高亮 + 轻微弹跳
- 切换时使用 Framer Motion 动画

**下方内容区（剩余高度，虚拟滚动）：**

| 当前 Tab | 渲染内容 | 组件 |
|---------|---------|------|
| 文字聊天 | 按月分组 + 按 Slice 排序的目录树 | `TextSidebarContent → SliceTree` |
| 媒体库 | 按 `by-event/` 文件夹结构的事件列表 | `MediaSidebarContent → EventFolderList` |

**Slice 目录树排序规则：**
- 第一层：按月分组（月份降序：最新在上）
- 第二层：同月内按 `startDate` 升序
- 每个 Slice 项显示：事件类型 emoji + 标题 + 消息数
- 点击 Slice → 中间区域加载对应消息流

**严格隔离规则：**
- 文字 Tab 只加载 slices.json + messages/，绝不出现媒体缩略图
- 媒体 Tab 只加载 by-event/ 文件夹结构，绝不出现文字消息
- 两个 Tab 的内容组件完全独立，无交叉引用

### 9.3 中间区域详细设计

**顶部标题栏（固定高度 48px）：**
- 左侧：当前选中对象标题
  - 文字模式：「🌸 3月15-18日 日常聊天」
  - 媒体模式：「📸 2025-03-日常聊天」
- 右侧：搜索图标按钮（点击展开搜索条）

**内容区（剩余高度）：**

**文字模式 `TextMessageFlow`：**
- 使用 `react-virtuoso` 实现虚拟滚动
- 消息气泡样式：
  - 自己发的消息：右对齐，浅粉色气泡
  - 对方发的消息：左对齐，浅薄荷绿色气泡
  - 气泡圆角 `rounded-3xl`，超大圆角可爱风
- 每种消息类型独立渲染（见 5.2 节）
- 右键任意消息 → 弹出 ContextMenu →「添加批注」
- 支持搜索：在当前 Slice 内搜索文字内容，匹配项高亮

**媒体模式 `MediaFlow`：**
- 网格布局（响应式列数，默认 3–4 列）
- 每张图片/视频显示缩略图卡片（rounded-2xl）
- 图片：显示缩略图，点击打开 Lightbox
- 视频：缩略图 + 中央播放按钮叠加，点击打开 VideoPlayer
- 懒加载：滚动到可视区域才加载图片（IntersectionObserver）
- 右键任意媒体 → 弹出 ContextMenu →「添加批注」

**模式切换动画：**
- Framer Motion AnimatePresence
- 旧内容：0.2s 淡出 + 轻微向下平移 8px
- 新内容：0.25s 淡入 + 轻微向上平移 8px
- 组件不卸载，仅隐藏（保留滚动位置）
- 切换时记忆各 Tab 的选中状态

### 9.4 右侧批注栏详细设计

**整体规格：**
- 宽度 260px（用户可拖拽调整，最小 220px，可完全折叠）
- 毛玻璃背景 `backdrop-blur-2xl bg-white/80`
- 顶部樱花粉到薄荷绿渐变
- 圆角 `rounded-3xl` + 粉色外发光阴影

**从上到下布局：**

1. **标题区（固定高度 48px）**
   - 图标 + 当前选中对象标题摘要
   - Slice：「🌸 3月15-18日 日常聊天」
   - Message：「💬 消息前30字预览」
   - Media：「📸 2025-03-15 的照片」
   - 右侧粉色「批注」标签

2. **批注列表区（flex-1，可滚动）**
   - 每条批注为独立卡片 `rounded-2xl bg-white/90`
   - 卡片内容：标签行 → Markdown 内容 → 创建时间
   - 按 `createdAt` 倒序（最新在上）
   - 空状态：居中插图（小熊/猫咪写日记）+「还没有写下任何批注呢～」+「来记录你最想记住的瞬间吧 ❤️」

3. **添加批注区（固定高度，自适应增长）**
   - 多行 textarea（自动增高），占位文字：「写下你此刻的心情或想记住的细节…」
   - 8 个固定标签按钮行（可多选，选中高亮粉色）
   - 底部：「💾 保存批注」粉色渐变按钮

**交互细节：**
- 保存后新批注从底部淡入 + 心跳动画
- 保存成功后自动清空输入框和已选标签
- 不支持草稿保存（极简原则）

### 9.5 右键菜单

- 在消息气泡 / 媒体缩略图 / Slice 标题上右键触发
- 样式：毛玻璃 `backdrop-blur-xl bg-white/90`、`rounded-2xl`、粉色阴影
- 唯一菜单项：「✨ 添加批注」
- 点击后：设置 `currentTarget` → 右侧自动联动 → 输入框聚焦
- 纯 Portal 渲染，不干扰主布局

### 9.6 媒体查看器

**Lightbox（图片全屏查看）：**
- 全屏遮罩 `bg-black/80 backdrop-blur-sm`
- 图片居中显示，支持双指缩放 + 滚轮缩放
- 左右箭头翻页（切换到同一事件内的上一张/下一张图片）
- 右上角关闭按钮 + 图片计数「3 / 12」
- 底部可选：显示当前图片的批注数（若有）

**VideoPlayer（视频播放）：**
- 全屏遮罩同上
- 视频居中，带标准播放/暂停、进度条、音量控制
- 关闭按钮 + Esc 退出

### 9.7 搜索功能

- 搜索范围：当前选中 Slice 内的所有文字消息
- 触发方式：点击中间区域顶部的搜索图标，或快捷键 `Ctrl+F` / `Cmd+F`
- 搜索条从标题栏下方滑出（Framer Motion），包含输入框 + 匹配计数
- 匹配结果在消息流中高亮（淡黄色背景 `#fff3cd`）
- 支持上下箭头在匹配项间跳转（自动滚动对应消息到可视区）
- 关闭搜索：Esc 或再次点击搜索图标

---

## 十、状态管理完整设计（Zustand）

### 10.1 Store 划分

```
┌──────────────────────────────────────────────────────┐
│                  Zustand Stores                      │
│                                                      │
│  useSidebarStore        useContentStore              │
│  ├─ tab: 'text'|'media'├─ mode: 'text'|'media'       │
│  ├─ width: 280         ├─ currentSliceId: string|null│
│  ├─ setTab()           ├─ currentEventFolder: string  │
│  ├─ lastTextSliceId    ├─ scrollPositions: Map       │
│  └─ lastEventFolder    ├─ setMode()                  │
│                        ├─ setSlice()                 │
│                        └─ setScrollPosition()        │
│                                                      │
│  useAnnotationStore     useDataStore                 │
│  ├─ currentTarget:     ├─ slices: Slice[]            │
│  │  {type,id,title}    ├─ messagesCache: Map         │
│  ├─ annotations:       ├─ mediaStructure: EventFolder│
│  │  Annotation[]       ├─ isLoading: boolean         │
│  ├─ isSaving: boolean  ├─ error: string|null         │
│  ├─ setTarget()        ├─ loadSlices()               │
│  ├─ addAnnotation()    ├─ loadMessages(sliceId)      │
│  ├─ loadAnnotations()  └─ loadMediaStructure()       │
│  └─ clearTarget()                                    │
│                                                      │
│  useUIStore             useSettingsStore              │
│  ├─ isCompact: boolean  ├─ leftWidth: 280             │
│  ├─ rightCollapsed:     ├─ rightWidth: 260            │
│  │  boolean             ├─ rightCollapsed: false      │
│  ├─ contextMenu:        ├─ lastTab: 'text'            │
│  │  {x,y,target}|null   ├─ lastSliceId: null          │
│  ├─ searchQuery: string └─ lastEventFolder: null      │
│  ├─ isSearchOpen: bool                                │
│  ├─ showContextMenu()                                 │
│  ├─ hideContextMenu()                                 │
│  ├─ toggleCompact()                                   │
│  └─ setCompact()                                      │
└──────────────────────────────────────────────────────┘
```

### 10.2 Store 联动流程

**启动加载：**
```
App 挂载
  → useDataStore.loadSlices()
  → useDataStore.loadMediaStructure()
  → useAnnotationStore.loadAnnotations()
  → 默认选中 'text' Tab + 最新月份第一个 Slice
```

**Tab 切换：**
```
左侧点击 Tab
  → useSidebarStore.setTab('media')
  → useContentStore.setMode('media')
  → 中间区域 Framer Motion 切换 MediaFlow
  → useContentStore 恢复上次在该 Tab 的选中状态
```

**选中 Slice / 事件：**
```
左侧点击 Slice
  → useContentStore.setSlice(sliceId)
  → useDataStore.loadMessages(sliceId)  // 按需加载
  → 中间区域渲染 TextMessageFlow
```

**右键添加批注：**
```
右键消息/媒体/Slice
  → useUIStore.showContextMenu({x, y, target})
  → 点击「添加批注」
  → useAnnotationStore.setTarget(target)
  → useUIStore.hideContextMenu()
  → 右侧批注栏联动刷新 + 输入框聚焦
```

**保存批注：**
```
输入内容 + 选择标签 → 点击保存
  → useAnnotationStore.addAnnotation()
    → 更新内存中的 annotations[]
    → fileAPI.writeAnnotations() (原子写入)
  → 成功后：清空输入框 + 弹跳动画
```

**窗口尺寸变化：**
```
window resize 事件
  → useUIStore.setCompact(window.innerWidth < 1280)
  → 紧凑模式：右侧栏自动折叠
  → 极窄模式 (width < 1024)：左侧栏收缩为图标模式 (64px)
```

---

## 十一、Electron 窗口与打包

### 11.1 窗口配置

```typescript
// src/main/index.ts
const mainWindow = new BrowserWindow({
  width: 1400,
  height: 900,
  minWidth: 1024,
  minHeight: 640,
  title: 'zyMemo — 与 TA 的回忆',
  icon: path.join(__dirname, '../resources/icon.png'),
  webPreferences: {
    preload: path.join(__dirname, '../preload/index.js'),
    contextIsolation: true,       // 必须开启
    nodeIntegration: false,       // 必须关闭
    sandbox: false,               // preload 需要访问 Node API
  },
  show: false,                    // ready-to-show 后再显示，避免白屏
  backgroundColor: '#f8f1eb',    // 与主题背景色一致
})
```

**窗口行为：**
- 使用系统默认窗口装饰（标题栏 + 最小化/最大化/关闭按钮），与治愈风配色统一
- 背景色 `#f8f1eb`，避免加载时的白色闪烁
- `ready-to-show` 事件触发后才显示窗口

### 11.2 打包配置

```yaml
# electron-builder.yml
appId: com.zymemo.app
productName: zyMemo
directories:
  output: release
win:
  target:
    - target: portable
      arch: [x64]
  icon: resources/icon.png
portable:
  artifactName: zyMemo.exe
asar: true
compression: maximum
files:
  - out/**/*
  - resources/**/*
```

**打包策略：**
- 使用 `portable` 目标，输出单个 .exe 文件
- 不包含 `data/` 目录，数据文件由预处理脚本生成后手动放入 U 盘
- .exe 运行时自动从自身所在目录寻找 `data/` 文件夹

### 11.3 首次启动检测

```
程序启动
  → 检测 exe 所在目录下是否存在 data/ 文件夹
  → 若不存在 → 弹窗提示：
    「未找到 data/ 文件夹。请确保：
    1. 程序已放入 U 盘根目录
    2. U 盘根目录包含 data/ 文件夹
    3. data/ 文件夹由预处理脚本生成（npm run preprocess）」
  → 用户点击「确定」后退出
  → 若存在 → 正常启动
```

---

## 十二、紧凑模式与响应式适配

### 12.1 断点定义

| 窗口宽度 | 模式 | 表现 |
|---------|------|------|
| ≥ 1280px | 标准模式 | 完整三段式布局 |
| 1024px – 1279px | 紧凑模式 | 右侧批注栏自动折叠 |
| 640px – 1023px | 极窄模式 | 左侧收缩为图标模式（64px），右侧折叠，中间全宽 |
| < 640px | 不支持 | 最小窗口限制 1024×640 |

### 12.2 紧凑模式表现

- **右侧批注栏完全折叠**：点击中间区域的「批注」图标按钮（浮动在右下角）可临时展开
- **左侧保持正常宽度**：用户仍可浏览 Slice 树或事件文件夹
- **中间区域占据剩余空间**：消息流和媒体网格自适应变宽
- **所有文字和媒体正常渲染**：仅布局结构调整

### 12.3 极窄模式表现

- **左侧收缩为图标模式**（64px）：仅显示头像 + 两个 Tab 图标（💬 / 🖼️），Hover 时展开
- **右侧折叠**：同上
- **中间全宽**：消息气泡自动限制最大宽度 600px，居中显示

### 12.4 用户手动控制

- 用户可拖拽左侧和右侧的分隔条调整宽度
- 右侧栏的折叠/展开按钮始终可见
- 这些偏好存入 `settings.json`，下次启动时恢复

---

## 十三、同步方案（P0 优先级）

### 13.1 当前方案：手动覆盖

两个 U 盘之间通过手动复制 `annotations.json` 实现同步。

**操作方式：**
1. 甲方写完批注后，将 `data/annotations.json` 复制出来
2. 乙方将该文件粘贴覆盖到自己的 U 盘 `data/` 目录下
3. 反之亦然

**纯覆盖模式的缺点：**
- 先写批注的人可能丢失未同步的数据

### 13.2 智能合并同步（P0，立即实现）

在应用设置页增加「同步批注」按钮，实现智能合并。

**同步流程：**

```
1. 点击「同步批注」
    ├── 提示用户在弹出的文件选择框中选择对方的 annotations.json
    └── 读取对方文件内容
         │
2. 智能合并算法
    ├── 按 id 去重
    │     ├── id 仅在己方存在 → 保留
    │     ├── id 仅在对方存在 → 新增到己方
    │     └── id 在双方都存在
    │           ├── updatedAt 相同 → 保留己方（无变化）
    │           └── updatedAt 不同 → 取 updatedAt 最新的那条
    │
    └── 如果有 id 相同但 content/tags 不同且 updatedAt 相同的情况
          → 保留己方版本（极罕见，几乎不会发生）
         │
3. 合并结果预览
    ├── 展示：新增 X 条 | 更新 Y 条 | 无变化 Z 条
    └── 用户点击「确认合并」
         │
4. 写入 annotations.json（原子写入）
    └── 显示成功提示
```

**冲突处理策略：** 「最后写入者胜出」（Last Writer Wins），以 `updatedAt` 为准。

### 13.3 备份策略

- 每次合并前自动生成 `annotations-backup-{timestamp}.json`
- 保留最近 5 个备份
- 旧备份自动清理

---

## 十四、各状态设计

### 14.1 加载状态

| 组件 | 加载态 |
|------|--------|
| 左侧目录树 | 骨架屏：3 个月份组，每组 2-3 个圆角矩形条目 |
| 消息流 | 骨架屏：8 条参差不齐的圆角矩形气泡交替排列 |
| 媒体网格 | 骨架屏：12 个圆角矩形占位格，带浅色脉冲动画 |
| 批注列表 | 骨架屏：3 个圆角卡片占位 |
| 图片缩略图（流中） | 浅灰色占位 + 脉冲动画，加载完成后淡入 |
| 应用首次启动 | 居中加载页：Logo + 「正在加载你的回忆…」+ 进度条 |

### 14.2 空状态

| 场景 | 空状态 |
|------|--------|
| 批注列表为空 | 居中插图（小熊写日记）+「还没有写下任何批注呢～」+「来记录你最想记住的瞬间吧 ❤️」 |
| Slice 无消息 | 「这个事件片段中没有消息记录」 |
| 媒体文件夹为空 | 「这个事件中没有图片或视频」 |
| 搜索结果为空 | 「在当前片段中没有找到匹配的内容」+ 搜索图标 |
| 某个月没有数据 | 左侧目录树中该月份显示灰色「无数据」占位 |

### 14.3 错误状态

| 场景 | 错误态 |
|------|--------|
| data/ 目录不存在 | 弹窗：「请将程序放入包含 data/ 文件夹的 U 盘根目录」→ 退出 |
| slices.json 无法解析 | 弹窗：「slices.json 文件损坏，请检查格式或重新运行预处理脚本」→ 退出 |
| messages 文件无法加载 | 对应 Slice 显示「消息数据加载失败」+ 重试按钮 |
| 媒体文件已删除 | 卡片显示「文件已丢失 😢」占位图（破碎的照片图标） |
| annotations.json 损坏 | 自动回退到最新备份，若也损坏则降级为空，提示用户 |
| U盘写入失败 | Toast 提示「写入失败，请检查 U 盘连接后重试」+ 自动回滚 |
| 磁盘空间不足 | Toast 提示「U 盘空间不足，请清理后重试」 |

### 14.4 通用 Toast 通知

- 使用 shadcn/ui Toast（`sonner` 库）
- 成功：绿色 + 勾号图标
- 警告：黄色 + 感叹号
- 错误：红色 + 叉号
- 位置：右下角
- 自动消失：3 秒

---

## 十五、MVP 优先级总览

### P0 — 必须实现（MVP 核心）

| 功能 | 说明 |
|------|------|
| Electron 窗口 + 打包 | 单文件 .exe，electron-builder portable |
| 三段式布局 | Left 280px + Main flex-1 + Right 260px |
| 左侧文字 Tab + Slice 目录树 | 按月分组、按 startDate 排序 |
| 左侧媒体 Tab + 事件文件夹列表 | 基于 by-event/ 目录结构 |
| TextMessageFlow | react-virtuoso 虚拟滚动，消息气泡渲染 |
| 批注 CRUD | 添加、查看、删除批注 |
| annotations.json 原子读写 | 临时文件 → rename → 备份 |
| 数据加载 | slices.json + messages 按需加载 |
| 预处理脚本 | scripts/preprocess.ts |
| 智能合并同步 | 设置页「同步批注」按钮 |
| 右键「添加批注」 | ContextMenu 触发 |
| 空状态 / 错误状态 | 基础覆盖 |

### P1 — 应该实现（MVP 增强）

| 功能 | 说明 |
|------|------|
| MediaFlow | 图片网格 + 懒加载 |
| Lightbox | 图片全屏查看 + 缩放 + 翻页 |
| VideoPlayer | 视频全屏播放 |
| Framer Motion 动效 | Tab 切换、批注保存、Hover、模式切换 |
| 消息搜索（当前 Slice 内） | 搜索条 + 高亮 + 跳转 |
| 紧凑模式 | 窗口 <1280px 时自动适配 |
| 骨架屏加载态 | 统一各组件加载态 |

### P2 — 应该实现（体验完善）

| 功能 | 说明 |
|------|------|
| 拖拽调整侧边栏宽度 | Splitter 组件 + 持久化到 settings.json |
| 语音消息播放 | 迷你音频播放器 |
| 文件类型消息 | 显示文件名 + 「打开」按钮 |
| Sticker 动画 | GIF/APNG 表情动图渲染 |
| 搜索增强 | 全局搜索（跨 Slice） |
| 批注导出 | 导出为 Markdown / PDF |

### P3 — 后期考虑

| 功能 | 说明 |
|------|------|
| 自定义窗口标题栏 | 无边框窗口 + 自绘标题栏 |
| 暗色模式 | 可切换的暗色主题 |
| 数据统计面板 | 消息数、批注数、活跃时段等统计图表 |
| 媒体 EXIF 信息展示 | 照片拍摄时间、地点等 |
| 本地服务器模式 | 同一局域网内另一设备可访问 |

---

## 十六、附录：关键交互时序图

### 16.1 添加批注完整流程

```
用户在中间区域浏览消息
         │
         ▼
右键点击某条消息气泡 / 图片
         │
         ▼
useUIStore.showContextMenu({ x, y, target: { type:'message', id:'msg_xxx', title:'预览30字' } })
         │
         ▼
ContextMenu 在 Portal 中渲染 → 用户看到「✨ 添加批注」
         │
         ▼
用户点击「添加批注」
         │
         ├── useUIStore.hideContextMenu()
         ├── useAnnotationStore.setTarget({ type:'message', id:'msg_xxx', title:'预览30字' })
         │     └── 触发右侧 AnnotationPanel 重新渲染
         │           ├── 标题区更新为「💬 消息前30字预览」
         │           ├── 加载该 target 的已有批注列表
         │           └── 输入框自动 focus()
         │
         ▼
用户在右侧输入批注内容 + 选择标签
         │
         ▼
点击「💾 保存批注」
         │
         ├── useAnnotationStore.addAnnotation(content, tags)
         │     ├── 构造 Annotation 对象 (id = 'ann_' + timestamp)
         │     ├── 更新内存中 annotations[]
         │     ├── fileAPI.writeAnnotations(annotations)
         │     │     ├── 写临时文件
         │     │     ├── 校验
         │     │     ├── rename 原子替换
         │     │     └── 生成备份
         │     └── 更新 Store
         │
         ├── 新批注卡片从底部淡入 + 心跳动画
         ├── 清空输入框和已选标签
         └── Toast: 「批注已保存 ✨」
```

### 16.2 Tab 切换时序

```
用户在左侧点击「媒体库」Tab
         │
         ▼
useSidebarStore.setTab('media')
         │
         ├── 左侧下方内容区切换
         │     └── TextSidebarContent → MediaSidebarContent
         │           └── 渲染 EventFolderList（by-event/ 目录结构）
         │
         ├── useContentStore.setMode('media')
         │     │
         │     ├── 保存当前文字模式的 scrollPosition → scrollPositions Map
         │     │
         │     └── 中间区域切换
         │           └── Framer Motion AnimatePresence
         │                 ├── TextMessageFlow 退出: 0.2s fadeOut + translateY(8px)
         │                 └── MediaFlow 进入: 0.25s fadeIn + translateY(-8px)
         │                       └── 恢复上次在媒体模式下的选中状态
         │
         └── 右侧批注栏
               └── 检查 currentTarget.targetType
                     ├── 若 target 在新模式下有效 → 保持
                     └── 若无效（如 target 是消息而切换到媒体模式）
                           → 清空 currentTarget → 显示空状态
```

---

> **文档版本：** v2.0
> **最后更新：** 2026-05-25
> **状态：** 完整设计定稿，可进入开发阶段
