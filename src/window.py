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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._strings = load_strings()
        self._settings = AppSettings()
        self._model = FileQueueModel()
        self._worker: ConvertWorker | None = None

        self.setWindowTitle(self._strings["window_title"])
        self.setFixedSize(640, 460)
        self._setup_ui()

    def _setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._build_folder_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._drop = DropZone(self._strings)
        self._drop.setFixedWidth(int(640 * 0.48))
        self._drop.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._drop.files_dropped.connect(self._on_files_added)
        body.addWidget(self._drop)

        vsep = QFrame()
        vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setStyleSheet("color: #e5e5ea;")
        body.addWidget(vsep)

        self._queue = QueueWidget(self._model, self._strings)
        body.addWidget(self._queue, stretch=1)

        body_w = QWidget()
        body_w.setLayout(body)
        vbox.addWidget(body_w, stretch=1)
        vbox.addWidget(self._build_bottom_bar())

    def _build_folder_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(34)
        bar.setStyleSheet("background:#f5f5f7;border-bottom:1px solid #e5e5ea;")
        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(6)
        h.addWidget(self._lbl("📁", "font-size:13px;"))
        h.addWidget(self._lbl(self._strings["folder_label"], "font-size:12px;color:#8e8e93;"))
        self._folder_lbl = self._lbl(
            self._settings.output_folder(),
            "font-size:12px;color:#007aff;font-weight:500;",
        )
        h.addWidget(self._folder_lbl, stretch=1)
        btn = QPushButton(self._strings["folder_change"])
        btn.setFixedHeight(22)
        btn.setStyleSheet("""
            QPushButton{background:#e5e5ea;color:#3c3c43;border:none;
                border-radius:5px;font-size:11px;padding:0 10px;font-weight:500;}
            QPushButton:hover{background:#d8d8de;}
        """)
        btn.clicked.connect(self._change_folder)
        h.addWidget(btn)
        return bar

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet(
            "background:qlineargradient(y1:0,y2:1,stop:0 #f5f5f7,stop:1 #efefef);"
            "border-top:1px solid #e0e0e0;"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(8)

        self._counter_lbl = QLabel("")
        self._counter_lbl.setStyleSheet("font-size:12px;color:#34c759;font-weight:600;")
        h.addWidget(self._counter_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedHeight(24)
        sep.setStyleSheet("color:#e0e0e0;")
        h.addWidget(sep)

        self._convert_btn = QPushButton(self._strings["btn_convert"])
        self._convert_btn.setFixedHeight(34)
        self._convert_btn.setStyleSheet("""
            QPushButton{background:qlineargradient(y1:0,y2:1,stop:0 #34c759,stop:1 #2db14e);
                color:white;border:none;border-radius:9px;
                font-size:13px;font-weight:700;padding:0 20px;}
            QPushButton:hover{background:#2db14e;}
            QPushButton:pressed{background:#259b43;}
            QPushButton:disabled{background:#c7c7cc;}
        """)
        self._convert_btn.clicked.connect(self._on_convert_clicked)
        h.addWidget(self._convert_btn, stretch=1)

        open_btn = QPushButton(f"🗂️ {self._strings['btn_open_folder']}")
        open_btn.setFixedHeight(34)
        open_btn.setStyleSheet("""
            QPushButton{background:#e5e5ea;color:#3c3c43;border:none;
                border-radius:9px;font-size:12px;font-weight:500;padding:0 14px;}
            QPushButton:hover{background:#d8d8de;}
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
            return

        waiting = self._queue.waiting_paths()
        if not waiting:
            return

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

    def _on_all_done(self):
        self._convert_btn.setText(self._strings["btn_convert"])
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
