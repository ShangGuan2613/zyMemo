"""
WeChat 数据发现模块（macOS 专用，针对 4.1.7.2 优化）

基于对用户真实机器的探测结果自动定位：
- 容器路径
- wxid
- 媒体/文件根目录（xwechat_files）
- 可能的 Message / DB 位置

这个模块是“即插即用”的核心，能大幅降低用户手动找路径的痛苦。
"""

import os
from pathlib import Path
from typing import Optional, Dict, List
import subprocess


class WeChatFinder:
    def __init__(self):
        self.container = Path.home() / "Library/Containers/com.tencent.xinWeChat"
        self.documents = self.container / "Data/Documents"
        self.xwechat_files = self.documents / "xwechat_files"

    def is_wechat_installed(self) -> bool:
        return (Path("/Applications/WeChat.app")).exists()

    def is_wechat_running(self) -> bool:
        try:
            result = subprocess.run(
                ["pgrep", "-x", "WeChat"],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def discover_wxids(self) -> List[str]:
        """发现所有可能的 wxid（通常用户只有一个）"""
        if not self.xwechat_files.exists():
            return []
        wxids = []
        for p in self.xwechat_files.iterdir():
            if p.is_dir() and p.name.startswith("wxid_"):
                wxids.append(p.name)
        return wxids

    def get_primary_wxid(self) -> Optional[str]:
        wxids = self.discover_wxids()
        if not wxids:
            return None
        # 简单策略：取第一个（大多数人只有一个账号）
        return wxids[0]

    def get_media_root(self, wxid: Optional[str] = None) -> Optional[Path]:
        if wxid is None:
            wxid = self.get_primary_wxid()
        if not wxid:
            return None
        candidate = self.xwechat_files / wxid
        if candidate.exists():
            return candidate
        return None

    def get_cache_message_dirs(self, wxid: Optional[str] = None) -> List[Path]:
        """找到 cache/YYYY-MM/Message 这种按月缓存的目录（媒体重要来源）"""
        media_root = self.get_media_root(wxid)
        if not media_root:
            return []
        cache = media_root / "cache"
        if not cache.exists():
            return []
        months = []
        for p in sorted(cache.iterdir()):
            if p.is_dir() and p.name.startswith(("202", "201")):
                msg_dir = p / "Message"
                if msg_dir.exists():
                    months.append(msg_dir)
        return months

    def get_full_status(self) -> Dict:
        """返回当前机器上微信的完整发现状态（用于 CLI 展示）"""
        wxid = self.get_primary_wxid()
        media_root = self.get_media_root(wxid)
        cache_dirs = self.get_cache_message_dirs(wxid)

        return {
            "wechat_installed": self.is_wechat_installed(),
            "wechat_running": self.is_wechat_running(),
            "container": str(self.container),
            "xwechat_files_root": str(self.xwechat_files),
            "primary_wxid": wxid,
            "media_root": str(media_root) if media_root else None,
            "monthly_cache_message_dirs": [str(d) for d in cache_dirs],
            "monthly_cache_count": len(cache_dirs),
        }

    def print_status(self):
        """漂亮打印当前发现结果（供 CLI 调用）"""
        status = self.get_full_status()
        print("\n=== WeChat 4.1.7.2 自动发现结果（本机）===\n")
        for k, v in status.items():
            if isinstance(v, list):
                print(f"{k}:")
                for item in v:
                    print(f"  - {item}")
            else:
                print(f"{k}: {v}")
        print()


if __name__ == "__main__":
    finder = WeChatFinder()
    finder.print_status()
