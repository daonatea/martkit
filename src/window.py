from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QFrame, QSizePolicy,
)
from settings import AppSettings
from i18n import load_strings
from drop_zone import DropZone
from queue_widget import QueueWidget
from queue_model import FileQueueModel, FileStatus
from converter import ConvertWorker

# Palette constants
_BG_APP      = "#F6F7FB"
_BG_SURFACE  = "#FFFFFF"
_BORDER      = "#E8EAF2"
_TEXT_PRI    = "#1C1C2E"
_TEXT_SEC    = "#7C7D95"
_ACCENT      = "#9BAEFF"

_BTN_NEUTRAL_BG   = "#EEEEF6"
_BTN_NEUTRAL_HV   = "#E4E4EF"
_BTN_NEUTRAL_TEXT = "#5A5B78"

_BTN_CONVERT_BG   = "#EDFBF3"
_BTN_CONVERT_HV   = "#D9F5E7"
_BTN_CONVERT_TEXT = "#2C7A4B"

_BTN_CANCEL_BG    = "#FFEEEE"
_BTN_CANCEL_HV    = "#FFE0E0"
_BTN_CANCEL_TEXT  = "#C03030"

_CLR_DONE = "#5BBF85"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._strings = load_strings()
        self._settings = AppSettings()
        self._model = FileQueueModel()
        self._worker: ConvertWorker | None = None

        self.setWindowTitle(self._strings["window_title"])
        self.setFixedSize(680, 480)
        self.setStyleSheet(f"QMainWindow {{ background: {_BG_APP}; }}")
        self._setup_ui()

    def _setup_ui(self):
        root = QWidget()
        root.setStyleSheet(f"background: {_BG_APP};")
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._build_folder_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._drop = DropZone(self._strings)
        self._drop.setFixedWidth(int(680 * 0.46))
        self._drop.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._drop.files_dropped.connect(self._on_files_added)
        body.addWidget(self._drop)

        vsep = QFrame()
        vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setStyleSheet(f"color: {_BORDER};")
        body.addWidget(vsep)

        self._queue = QueueWidget(self._model, self._strings)
        self._queue.setStyleSheet(f"background: {_BG_APP};")
        body.addWidget(self._queue, stretch=1)

        body_w = QWidget()
        body_w.setLayout(body)
        vbox.addWidget(body_w, stretch=1)
        vbox.addWidget(self._build_bottom_bar())

    def _build_folder_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(36)
        bar.setStyleSheet(
            f"background:{_BG_SURFACE};"
            f"border-bottom:1px solid {_BORDER};"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(6)

        dot = QLabel("◉")
        dot.setStyleSheet(f"font-size:10px;color:{_ACCENT};background:transparent;")
        h.addWidget(dot)

        h.addWidget(self._lbl(
            self._strings["folder_label"],
            f"font-size:11px;color:{_TEXT_SEC};background:transparent;"
        ))

        self._folder_lbl = self._lbl(
            self._settings.output_folder(),
            f"font-size:11px;color:{_ACCENT};font-weight:500;background:transparent;",
        )
        h.addWidget(self._folder_lbl, stretch=1)

        btn = QPushButton(self._strings["folder_change"])
        btn.setFixedHeight(24)
        btn.setStyleSheet(f"""
            QPushButton {{
                background:{_BTN_NEUTRAL_BG};
                color:{_BTN_NEUTRAL_TEXT};
                border:none;
                border-radius:6px;
                font-size:11px;
                font-weight:500;
                padding:0 10px;
            }}
            QPushButton:hover  {{ background:{_BTN_NEUTRAL_HV}; }}
            QPushButton:pressed {{ background:#D8D8E8; }}
        """)
        btn.clicked.connect(self._change_folder)
        h.addWidget(btn)
        return bar

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(
            f"background:{_BG_SURFACE};"
            f"border-top:1px solid {_BORDER};"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)

        self._counter_lbl = QLabel("")
        self._counter_lbl.setStyleSheet(
            f"font-size:12px;color:{_CLR_DONE};font-weight:600;"
        )
        h.addWidget(self._counter_lbl)
        h.addStretch()

        self._convert_btn = QPushButton(self._strings["btn_convert"])
        self._convert_btn.setFixedHeight(36)
        self._convert_btn.setStyleSheet(f"""
            QPushButton {{
                background:{_BTN_CONVERT_BG};
                color:{_BTN_CONVERT_TEXT};
                border:none;
                border-radius:10px;
                font-size:13px;
                font-weight:600;
                padding:0 22px;
            }}
            QPushButton:hover  {{ background:{_BTN_CONVERT_HV}; }}
            QPushButton:pressed {{ background:#C8EFD8; }}
            QPushButton:disabled {{ background:{_BTN_NEUTRAL_BG}; color:#B0B1C8; }}
        """)
        self._convert_btn.clicked.connect(self._on_convert_clicked)
        h.addWidget(self._convert_btn)

        open_btn = QPushButton(self._strings["btn_open_folder"])
        open_btn.setFixedHeight(36)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background:{_BTN_NEUTRAL_BG};
                color:{_BTN_NEUTRAL_TEXT};
                border:none;
                border-radius:10px;
                font-size:12px;
                font-weight:500;
                padding:0 16px;
            }}
            QPushButton:hover  {{ background:{_BTN_NEUTRAL_HV}; }}
            QPushButton:pressed {{ background:#D8D8E8; }}
        """)
        open_btn.clicked.connect(self._open_folder)
        h.addWidget(open_btn)
        return bar

    def _lbl(self, text: str, style: str = "") -> QLabel:
        lbl = QLabel(text)
        if style:
            lbl.setStyleSheet(style)
        return lbl

    def _on_files_added(self, paths: list[str]):
        self._queue.add_files(paths)
        self._refresh_counter()

    def _change_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, self._strings["folder_change"], self._settings.output_folder()
        )
        if path:
            self._settings.set_output_folder(path)
            self._folder_lbl.setText(path)

    def _open_folder(self):
        folder = self._settings.output_folder()
        Path(folder).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _on_convert_clicked(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._convert_btn.setText(self._strings["btn_convert"])
            self._convert_btn.setStyleSheet(self._convert_btn.styleSheet().replace(
                _BTN_CANCEL_BG, _BTN_CONVERT_BG
            ).replace(_BTN_CANCEL_TEXT, _BTN_CONVERT_TEXT))
            self._apply_convert_style()
            return

        waiting = self._queue.waiting_paths()
        if not waiting:
            return

        self._apply_cancel_style()
        self._convert_btn.setText(self._strings["btn_cancel"])
        self._worker = ConvertWorker(waiting, self._settings.output_folder())
        self._worker.file_started.connect(
            lambda p: self._queue.update_status(p, FileStatus.CONVERTING)
        )
        self._worker.file_finished.connect(
            lambda p, _: (
                self._queue.update_status(p, FileStatus.DONE),
                self._refresh_counter(),
            )
        )
        self._worker.file_error.connect(
            lambda p, e: (
                self._queue.update_status(p, FileStatus.ERROR, e),
                self._refresh_counter(),
            )
        )
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _apply_convert_style(self):
        self._convert_btn.setStyleSheet(f"""
            QPushButton {{
                background:{_BTN_CONVERT_BG};
                color:{_BTN_CONVERT_TEXT};
                border:none;
                border-radius:10px;
                font-size:13px;
                font-weight:600;
                padding:0 22px;
            }}
            QPushButton:hover  {{ background:{_BTN_CONVERT_HV}; }}
            QPushButton:pressed {{ background:#C8EFD8; }}
            QPushButton:disabled {{ background:{_BTN_NEUTRAL_BG}; color:#B0B1C8; }}
        """)

    def _apply_cancel_style(self):
        self._convert_btn.setStyleSheet(f"""
            QPushButton {{
                background:{_BTN_CANCEL_BG};
                color:{_BTN_CANCEL_TEXT};
                border:none;
                border-radius:10px;
                font-size:13px;
                font-weight:600;
                padding:0 22px;
            }}
            QPushButton:hover  {{ background:{_BTN_CANCEL_HV}; }}
            QPushButton:pressed {{ background:#FFD0D0; }}
        """)

    def _on_all_done(self):
        self._convert_btn.setText(self._strings["btn_convert"])
        self._apply_convert_style()
        self._refresh_counter()

    def _refresh_counter(self):
        done = self._model.done_count()
        total = self._model.total()
        if total:
            self._counter_lbl.setText(
                self._strings["counter"].format(done=done, total=total)
            )
        else:
            self._counter_lbl.setText("")
