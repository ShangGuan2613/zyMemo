# zyMemo 微信聊天记录导入工具（独立版）

> **推荐工作流（2026年最新建议）**：
> **在另一台 Windows 电脑上导出数据包**（用成熟的 Windows 工具）→ 把数据包复制到这台 Mac → 用本工具处理成 zyMemo 格式（`data/zy_memo.db + media/`）→ 复制到 U 盘即可使用。
>
> 这样可以避开 macOS 4.1.7.2 极其麻烦的密钥提取、重签、SIP 等问题。

**核心原则**（来自项目架构手册）：
- 这个工具**永远独立**，运行完后可以删除。
- zyMemo App **永远不会**碰任何微信原始数据或解密逻辑。
- 你只需要把生成好的 `data/` 文件夹复制到 U 盘根目录。

---

## 为什么推荐「Windows 导出 + Mac 处理」？

- Windows 上有非常成熟、支持全量媒体导出的工具（WeChatMsg 等）。
- macOS 4.1.7.2 版本的数据库加密 + 沙盒机制导致直接导出非常困难且不稳定（需要重签、关闭 SIP、内存扫描等）。
- 你已经明确说要在另一台 Windows 电脑上导出数据包，然后在这台电脑处理 —— 这正是最优路径。

本工具现在主要职责是：**把各种 Windows 导出包高质量地转换成 zyMemo 格式**（智能事件切片、全量媒体哈希去重、SQLite 单文件输出）。

---

## 推荐的 Windows 导出工具（参考）

最常用且支持较好的：
- **WeChatMsg**（最流行，支持全量导出 + 媒体）
- wechat-dump-rs / 其他开源 Windows 解密工具

**导出时建议勾选 / 注意**：
- 选定你要导出的联系人（或全部）
- 必须包含**媒体文件**（图片、视频、语音）
- 导出格式最好是「文件夹结构」或「解密后的数据库 + 媒体文件夹」
- 导出完成后，整个导出目录打包（zip 或直接复制文件夹）带到这台 Mac

---

## 使用流程（Windows 导出 → 本工具处理）

1. 在 Windows 电脑上用工具导出数据包（包含 DB + 所有媒体）。
2. 把整个导出文件夹复制到这台 Mac（例如放到 `~/wechat-export-张三`）。
3. 在这台 Mac 上运行本工具：

```bash
cd /Users/a111/zyMemo

# 安装依赖（首次）
pip3 install rich typer pysqlcipher3  # 后续会提供 requirements.txt

python3 scripts/import_wechat/cli.py process \
    --input ~/wechat-export-张三 \
    --output ./data \
    --contact "张三" \
    --full-media
```

工具会自动尝试识别常见的 Windows 导出结构，列出联系人/会话让你确认，然后：
- 智能切片（按时间 + 密度生成「事件片段」）
- 全量媒体拷贝 + 内容哈希命名（避免重复和中文路径）
- 生成 `data/zy_memo.db`（SQLite）+ `data/media/`

4. 把整个 `data/` 文件夹复制到 U 盘根目录 → 插上 U 盘就能用 zyMemo 了。

---

## 当前支持的输入结构（持续完善）

本工具正在针对以下常见 Windows 导出格式做适配：

- 典型 `WeChatMsg` 导出目录（包含 `Msg` 文件夹 + `File` / `Image` 等媒体目录 + 解密后的 DB）
- 纯解密后的多 DB 文件夹 + 独立媒体目录
- JSON/CSV + 媒体文件夹的混合结构

运行时会自动探测，如果识别失败会给出清晰提示 + 建议你提供目录结构截图，我可以快速增加支持。

---

## 输出结构（严格匹配架构手册）

```
data/
├── zy_memo.db                 # SQLite 单文件（推荐，ACID、易备份）
└── media/
    ├── <content-hash>.jpg
    ├── <content-hash>.mp4
    └── ...                    # 所有媒体扁平存放，哈希命名
    # 可选 by-event/ 硬链接副本（方便人工查看）
```

数据库包含表（详见 `schema.sql`）：
- `slices`（事件片段）
- `messages`
- `media_assets`
- `annotations`（初始为空）
- `settings`

---

## 开发状态（实时更新）

- [x] 项目结构 + 本 README（已转向 Windows 导出包处理）
- [x] schema.sql（SQLite，匹配最新架构手册）
- [x] 基础 CLI 骨架 + 状态展示
- [x] 机器探测模块（保留，可用于辅助）
- [ ] Windows 导出包自动识别 + 联系人/会话列表
- [ ] 全量媒体收集 + 哈希拷贝 + 进度条
- [ ] 智能切片 + 交互式编辑 Slice
- [ ] 完整 SQLite 导出器
- [ ] 详细支持多种流行 Windows 工具的格式
- [ ] 双击 .command 包装 + 依赖处理

---

## 下一步

请告诉我：
1. 你打算在 Windows 上用哪个具体工具导出？（WeChatMsg？其他？）
2. 导出完成后，目录大概长什么样？（可以截图或描述主要文件夹）
3. 是否需要我现在就开始实现「处理 Windows 导出包」的核心逻辑（parser + 媒体拷贝 + SQLite 生成）？

一旦你把数据包复制过来，我可以立刻帮你跑转换，或者继续完善工具让你自己一键处理。

这个方案比直接在 macOS 上硬刚 4.1.7.2 要稳得多，也更符合 zyMemo「导入工具必须独立、长期可维护」的原则。

随时更新进展，我在这里继续写代码。需要我现在写哪个模块就说一声。