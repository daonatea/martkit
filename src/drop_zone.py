import math
import time
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QRadialGradient, QColor, QBrush, QPen,
    QDragEnterEvent, QDropEvent,
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog

_SUPPORTED = (
    "*.pdf *.docx *.doc *.xlsx *.xls *.pptx *.ppt "
    "*.html *.htm *.csv *.json *.xml *.epub *.msg *.zip"
)

# Palette
_BLOB      = QColor(110, 142, 255)   # periwinkle
_BORDER    = QColor(200, 204, 226)   # muted lavender-grey
_BORDER_HI = QColor(110, 142, 255)  # active drag


class DropZone(QWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, strings: dict, parent=None):
        super().__init__(parent)
        self._strings = strings
        self._pulse = 0.0
        self._drag_active = False
        self.setAcceptDrops(True)
        self.setStyleSheet("background: #F6F7FB;")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        layout.addStretch()

        icon = QLabel("✦")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            "font-size: 32px; color: #9BAEFF; background: transparent; letter-spacing: 2px;"
        )
        layout.addWidget(icon)

        layout.addSpacing(4)

        hint = QLabel(self._strings["drop_hint"])
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #1C1C2E; background: transparent;"
        )
        layout.addWidget(hint)

        sub = QLabel(self._strings["drop_sub"])
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 12px; color: #7C7D95; background: transparent;")
        layout.addWidget(sub)

        formats = QLabel("PDF · Word · Excel · PowerPoint · HTML · más")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formats.setWordWrap(True)
        formats.setStyleSheet(
            "font-size: 10px; color: #B0B1C8; background: transparent; margin-top: 2px;"
        )
        layout.addWidget(formats)

        layout.addStretch()

        btn = QPushButton(self._strings["btn_select"])
        btn.setFixedHeight(38)
        btn.setStyleSheet("""
            QPushButton {
                background: #EEF0FF;
                color: #5A6BE8;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover  { background: #E2E5FF; }
            QPushButton:pressed { background: #D4D9FF; }
        """)
        btn.clicked.connect(self._open_dialog)
        layout.addWidget(btn)

    def _emit_files(self, paths: list[str]) -> None:
        self.files_dropped.emit(paths)

    def _tick(self):
        self._pulse = (math.sin(time.monotonic() * 1.6) + 1.0) / 2.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, (self.height() - 62) / 2
        radius = 90 + self._pulse * 28
        alpha = int(10 + self._pulse * 16)
        grad = QRadialGradient(QPointF(cx, cy), radius)
        c = _BLOB
        grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), alpha))
        grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        rect = self.rect().adjusted(20, 20, -20, -72)
        border_color = _BORDER_HI if self._drag_active else _BORDER
        pen = QPen(border_color, 1.5, Qt.PenStyle.DashLine)
        pen.setDashPattern([6, 5])
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 18, 18)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drag_active = True
            self.update()

    def dragLeaveEvent(self, event):
        self._drag_active = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._drag_active = False
        self.update()
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)

    def _open_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, self._strings["btn_select"], "",
            f"Documents ({_SUPPORTED});;All files (*)",
        )
        if paths:
            self.files_dropped.emit(paths)
