from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileStatus(Enum):
    WAITING = "waiting"
    CONVERTING = "converting"
    DONE = "done"
    ERROR = "error"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class FileItem:
    path: str
    status: FileStatus = FileStatus.WAITING
    error: str = ""

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def size_label(self) -> str:
        try:
            size = Path(self.path).stat().st_size
        except OSError:
            return "—"
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.0f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"

    @property
    def type_icon(self) -> str:
        ext = Path(self.path).suffix.lower()
        return {
            ".pdf": "📄", ".docx": "📝", ".doc": "📝",
            ".xlsx": "📊", ".xls": "📊", ".pptx": "📋",
            ".ppt": "📋", ".html": "🌐", ".htm": "🌐",
            ".csv": "📋", ".json": "📋", ".xml": "📋",
            ".epub": "📚", ".msg": "✉️", ".zip": "🗜️",
            ".mp3": "🎙️", ".wav": "🎙️", ".m4a": "🎙️",
            ".ogg": "🎙️", ".flac": "🎙️", ".aac": "🎙️",
            ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
            ".bmp": "🖼️", ".tiff": "🖼️", ".tif": "🖼️", ".webp": "🖼️",
            ".txt": "📄", ".md": "📄",
        }.get(ext, "📄")


class FileQueueModel:
    def __init__(self):
        self._items: list[FileItem] = []

    def add_files(self, paths: list[str]) -> list[str]:
        existing = {item.path for item in self._items}
        added = []
        for p in paths:
            if p not in existing:
                self._items.append(FileItem(path=p))
                added.append(p)
        return added

    def clear(self) -> None:
        self._items.clear()

    def set_status(self, path: str, status: FileStatus, error: str = "") -> None:
        for item in self._items:
            if item.path == path:
                item.status = status
                item.error = error
                return

    def waiting_paths(self) -> list[str]:
        return [i.path for i in self._items if i.status == FileStatus.WAITING]

    def done_count(self) -> int:
        return sum(1 for i in self._items if i.status == FileStatus.DONE)

    def total(self) -> int:
        return len(self._items)

    def items(self) -> list[FileItem]:
        return list(self._items)
