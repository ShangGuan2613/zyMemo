#!/usr/bin/env python3
"""
zyMemo 微信导入工具 - 命令行入口

用法示例（未来）：
    python -m scripts.import_wechat.cli --help
    python scripts/import_wechat/cli.py export --help

当前状态：骨架 + 引导。完整功能正在快速开发中。
针对微信 4.1.7.2 + macOS + 全量媒体导出 已特别优化。
"""

import sys
from pathlib import Path

# 尝试引入漂亮的终端库（推荐先 pip install rich typer）
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None

def print_banner():
    banner = """
[bold magenta]zyMemo[/] 微信聊天记录导入工具
[cyan]独立 · 安全 · 全量媒体 · 专为回忆册设计[/]
"""
    if RICH_AVAILABLE:
        console.print(Panel(banner, border_style="magenta", expand=False))
    else:
        print("=== zyMemo 微信聊天记录导入工具 ===")
        print("独立 · 安全 · 全量媒体 · 专为回忆册设计")

def cmd_status():
    """显示当前状态和下一步建议"""
    print_banner()

    if RICH_AVAILABLE:
        table = Table(title="当前版本与支持情况", show_header=True)
        table.add_column("项目", style="cyan")
        table.add_column("状态", style="green")
        table.add_row("微信版本", "4.1.7.2（macOS 特别适配）")
        table.add_row("输出格式", "SQLite (zy_memo.db) + media/（架构手册推荐）")
        table.add_row("媒体导出", "全量（你要求）+ 内容哈希去重")
        table.add_row("智能切片", "开发中（时间+密度+交互确认）")
        table.add_row("Rich/Typer UI", "部分可用（建议先安装）")
        console.print(table)

        console.print(Panel.fit(
            "[bold yellow]立即行动（推荐）[/]\n\n"
            "1. 仔细阅读 [bold]scripts/import_wechat/README.md[/]\n"
            "2. 按 README 完成「重签微信 + 社区工具解密」阶段\n"
            "3. 拿到解密后的 DB 目录 + 微信媒体文件目录后回来\n"
            "4. 运行本工具完成「选人 → 切片 → 全量媒体拷贝 → 生成 zy_memo.db」",
            border_style="yellow"
        ))
    else:
        print("\n建议先安装依赖获得最佳体验：")
        print("  pip3 install rich typer pysqlcipher3")
        print("\n请阅读 scripts/import_wechat/README.md 获取微信 4.1.7.2 精确操作步骤。")

def cmd_install_deps():
    """一键提示安装依赖"""
    print("推荐依赖（后续会提供 requirements.txt）：")
    print("  pip3 install rich typer pysqlcipher3 protobuf pillow")
    print("\n安装后重新运行即可获得彩色界面和完整功能。")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="import_wechat",
        description="zyMemo 微信聊天记录独立导入工具（支持 4.1.7.2 全量媒体）"
    )
    subparsers = parser.add_subparsers(dest="command")

    # status
    p_status = subparsers.add_parser("status", help="查看工具状态和下一步建议")
    p_status.set_defaults(func=cmd_status)

    # deps
    p_deps = subparsers.add_parser("install-deps", help="显示推荐依赖安装命令")
    p_deps.set_defaults(func=cmd_install_deps)

    # 占位：未来真正的导出命令
    p_export = subparsers.add_parser("export", help="执行完整导出（开发中）")
    p_export.add_argument("--decrypted-db-dir", required=False, help="解密后的数据库目录")
    p_export.add_argument("--wechat-files-dir", required=False, help="微信原始媒体文件根目录")
    p_export.add_argument("--contact", required=False, help="联系人昵称或 wxid（支持模糊）")
    p_export.add_argument("--output", default="./data", help="输出 data/ 目录")
    p_export.add_argument("--full-media", action="store_true", help="导出全部媒体（默认开启）")
    p_export.set_defaults(func=lambda args: _placeholder_export(args))

    args = parser.parse_args()

    if not args.command:
        cmd_status()
        return

    args.func(args) if hasattr(args, 'func') else cmd_status()

def _placeholder_export(args):
    print_banner()
    msg = f"""
[bold red]导出功能正在开发中[/]

你提供的参数：
  解密DB目录: {args.decrypted_db_dir or '未指定'}
  媒体目录  : {args.wechat_files_dir or '未指定'}
  联系人    : {args.contact or '未指定'}
  输出位置  : {args.output}
  全量媒体  : {args.full_media}

请先按 README 完成解密阶段。
当你准备好解密后的目录时，运行：

  python scripts/import_wechat/cli.py export \\
      --decrypted-db-dir /path/to/decrypted \\
      --wechat-files-dir /path/to/xwechat_files \\
      --contact "对方昵称" \\
      --full-media

届时工具会：
• 列出匹配的会话让你确认
• 智能切成多个 Slice（事件片段）
• 交互式调整标题和事件类型
• **完整拷贝所有媒体**（哈希命名）
• 生成 zy_memo.db + media/ 目录

开发进度请看 scripts/import_wechat/README.md
"""
    if RICH_AVAILABLE:
        console.print(Panel(msg, border_style="red"))
    else:
        print(msg)

if __name__ == "__main__":
    main()
