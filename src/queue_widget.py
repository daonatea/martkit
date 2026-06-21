import time
import math
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton,
)
from queue_model import FileQueueModel, FileStatus, FileItem

# Status colours
_CLR_WAIT    = "#B8B9D0"
_CLR_CONV    = "#6E8EFF"
_CLR_DONE    = "#5BBF85"
_CLR_ERR     = "#FF7A7A"
_BG_CONV     = "#F2F4FF"
_BG_ERR      = "#FFF4F4"
_BG_ROW      = "#FFFFFF"
_BORDER_ROW  = "#F0F1F7"


class FileRow(QFrame):
    def __init__(self, item: FileItem, strings: dict, parent=None):
        super().__init__(parent)
        self._item = item
        self._strings = strings
        self._progress_x = 0.0
        self.setFixedHeight(54)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        self._icon_lbl = QLabel(item.type_icon)
        self._icon_lbl.setFixedWidth(26)
        self._icon_lbl.setStyleSheet("font-size: 20px;")
        layout.addWidget(self._icon_lbl)

        info = QVBoxLayout()
        info.setSpacing(2)
        name = QLabel(item.name)
        name.setStyleSheet("font-size: 12px; font-weight: 500; color: #1C1C2E;")
        size = QLabel(item.size_label)
        size.setStyleSheet("font-size: 10px; color: #9A9BB8;")
        info.addWidget(name)
        info.addWidget(size)
        layout.addLayout(info, stretch=1)

        self._status_lbl = QLabel()
        self._status_lbl.setFixedWidth(110)
        self._status_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._status_lbl)

        self.refresh()

    def refresh(self):
        s = self._item.status
        if s == FileStatus.WAITING:
            self._status_lbl.setText(self._strings["status_waiting"])
            self._status_lbl.setStyleSheet(f"font-size: 11px; color: {_CLR_WAIT};")
            self.setStyleSheet(f"QFrame{{background:{_BG_ROW};border-bottom:1px solid {_BORDER_ROW};}}")
            self._timer.stop()
        elif s == FileStatus.CONVERTING:
            self._status_lbl.setText(f"⏳ {self._strings['status_converting']}")
            self._status_lbl.setStyleSheet(f"font-size:11px;color:{_CLR_CONV};font-weight:600;")
            self.setStyleSheet(f"QFrame{{background:{_BG_CONV};border-bottom:1px solid {_BORDER_ROW};}}")
            self._timer.start(16)
        elif s == FileStatus.DONE:
            self._status_lbl.setText(f"✓ {self._strings['status_done']}")
            self._status_lbl.setStyleSheet(f"font-size:11px;color:{_CLR_DONE};font-weight:600;")
            self.setStyleSheet(f"QFrame{{background:{_BG_ROW};border-bottom:1px solid {_BORDER_ROW};}}")
            self._timer.stop()
        elif s == FileStatus.ERROR:
            self._status_lbl.setText(f"✗ {self._strings['status_error']}")
            self._status_lbl.setStyleSheet(f"font-size:11px;color:{_CLR_ERR};font-weight:600;")
            self.setStyleSheet(f"QFrame{{background:{_BG_ERR};border-bottom:1px solid {_BORDER_ROW};}}")
            if self._item.error:
                self._status_lbl.setToolTip(self._item.error)
            self._timer.stop()

    def _tick(self):
        self._progress_x = (self._progress_x + 3) % (self.width() + 120)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._item.status != FileStatus.CONVERTING:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() - 2
        w = 120
        x = int(self._progress_x) - w
        grad = QLinearGradient(x, y, x + w, y)
        grad.setColorAt(0,   QColor(110, 142, 255, 0))
        grad.setColorAt(0.5, QColor(110, 142, 255, 180))
        grad.setColorAt(1,   QColor(110, 142, 255, 0))
        painter.fillRect(x, y, w, 2, grad)


class QueueWidget(QWidget):
    def __init__(self, model: FileQueueModel, strings: dict, parent=None):
        super().__init__(parent)
        self._model = model
        self._strings = strings
        self._rows: dict[str, FileRow] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(14, 10, 14, 8)
        self._header_lbl = QLabel(self._strings["queue_header"].upper())
        self._header_lbl.setStyleSheet(
            "font-size:10px;font-weight:700;color:#8A8BA8;letter-spacing:1.5px;"
        )
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("font-size:11px;color:#B0B1C8;")
        clear = QPushButton(self._strings["queue_clear"])
        clear.setFlat(True)
        clear.setStyleSheet(
            "font-size:11px;color:#9BAEFF;border:none;background:transparent;padding:0;"
        )
        clear.clicked.connect(self._on_clear)
        header.addWidget(self._header_lbl)
        header.addWidget(self._count_lbl)
        header.addStretch()
        header.addWidget(clear)
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#EEEEF6;")
        layout.addWidget(sep)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("background: #FAFBFE;")
        self._container = QWidget()
        self._container.setStyleSheet("background: #FAFBFE;")
        self._rows_layout = QVBoxLayout(self._container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)
        self._rows_layout.addStretch()
        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll, stretch=1)

    def add_files(self, paths: list[str]) -> None:
        newly = self._model.add_files(paths)
        for path in newly:
            item = next(i for i in self._model.items() if i.path == path)
            row = FileRow(item, self._strings)
            self._rows[path] = row
            idx = self._rows_layout.count() - 1
            self._rows_layout.insertWidget(idx, row)
        self._refresh_count()

    def update_status(self, path: str, status: FileStatus, error: str = "") -> None:
        self._model.set_status(path, status, error)
        if path in self._rows:
            self._rows[path].refresh()
        self._refresh_count()

    def waiting_paths(self) -> list[str]:
        return self._model.waiting_paths()

    def _on_clear(self):
        self._model.clear()
        for row in self._rows.values():
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self._refresh_count()

    def _refresh_count(self):
        n = self._model.total()
        self._count_lbl.setText(f"  {n}" if n else "")
