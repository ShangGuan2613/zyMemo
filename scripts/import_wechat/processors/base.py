"""
Base processor interface.

All processors (Windows export, future macOS decrypted, etc.) should implement this.
Goal: Given an input directory, produce structured data that the zyMemo exporter can consume.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any


class BaseProcessor(ABC):
    def __init__(self, input_dir: Path):
        self.input_dir = input_dir

    @abstractmethod
    def detect(self) -> bool:
        """Return True if this processor can handle the given input_dir."""
        pass

    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        Return list of chat sessions/contacts.
        Each item should at least contain:
            - id / username (wxid or room id)
            - name / nickname / remark
            - message_count (approx)
            - last_time
        """
        pass

    @abstractmethod
    def extract_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Extract all messages for a given session.
        Return normalized message dicts (to be defined).
        """
        pass

    @abstractmethod
    def collect_media(self, session_id: str, output_media_dir: Path) -> Dict[str, str]:
        """
        Copy/collect all media for the session into output_media_dir (hashed names).
        Return mapping: original_ref -> hashed_filename
        """
        pass
