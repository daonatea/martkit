from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QFrame, QSizePolicy,
    QMessageBox,
)
from settings import AppSettings
from i18n import load_strings
from drop_zone import DropZone
from queue_widget import QueueWidget
from queue_model import FileQueueModel, FileStatus
from converter import ConvertWorker
from transcribe import is_audio, is_model_cached

# Palette derivada del logo: navy #12165A + violeta #643CC8
_BG_APP      = "#F5F4FC"
_BG_SURFACE  = "#FFFFFF"
_BORDER      = "#E2DFFA"
_TEXT_PRI    = "#12165A"   # navy del logo
_TEXT_SEC    = "#6B5B9E"
_ACCENT      = "#643CC8"   # violeta del logo

_BTN_NEUTRAL_BG   = "#EEEDF8"
_BTN_NEUTRAL_HV   = "#E4E2F3"
_BTN_NEUTRAL_TEXT = "#3D3476"

_BTN_CONVERT_BG   = "#EDE8FB"
_BTN_CONVERT_HV   = "#E0D9F8"
_BTN_CONVERT_TEXT = "#3D1F9E"

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
        self._queue.queue_changed.connect(self._refresh_convert_btn)
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
        self._convert_btn.setEnabled(False)
        self._convert_btn.clicked.connect(self._on_convert_clicked)
        h.addWidget(self._convert_btn)
        self._apply_convert_style()

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
        audios = [p for p in paths if is_audio(p)]
        if audios and not is_model_cached():
            if not self._ask_audio_download():
                for p in audios:
                    self._queue.update_status(p, FileStatus.SKIPPED)
        self._refresh_counter()
        self._refresh_convert_btn()

    def _ask_audio_download(self) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle(self._strings["audio_dl_title"])
        box.setIcon(QMessageBox.Icon.Question)
        box.setText(self._strings["audio_dl_body"])
        accept = box.addButton(
            self._strings["audio_dl_accept"], QMessageBox.ButtonRole.AcceptRole
        )
        box.addButton(self._strings["audio_dl_skip"], QMessageBox.ButtonRole.RejectRole)
        box.exec()
        return box.clickedButton() is accept

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
        self._worker.file_error.connect(self._on_file_error)
        self._worker.file_warning.connect(self._on_file_warning)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _apply_convert_style(self):
        self._convert_btn.setStyleSheet(f"""
            QPushButton {{
                background:{_ACCENT};
                color:#FFFFFF;
                border:none;
                border-radius:10px;
                font-size:13px;
                font-weight:600;
                padding:0 22px;
            }}
            QPushButton:hover  {{ background:#7B52D4; }}
            QPushButton:pressed {{ background:#4E2A9E; }}
            QPushButton:disabled {{ background:#DDDBE6; color:#A8A8BE; }}
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

    def _on_file_error(self, path: str, error: str):
        self._queue.update_status(path, FileStatus.ERROR, error)
        self._refresh_counter()
        name = Path(path).name
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Error de conversión")
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setText(f"No se pudo convertir <b>{name}</b>")
        dlg.setInformativeText(error)
        dlg.exec()

    def _on_file_warning(self, path: str):
        self._queue.update_status(
            path, FileStatus.WARNING, self._strings["warn_no_content"]
        )
        self._refresh_counter()

    def _on_all_done(self):
        self._convert_btn.setText(self._strings["btn_convert"])
        self._apply_convert_style()
        self._refresh_counter()
        self._refresh_convert_btn()

    def _refresh_convert_btn(self):
        has_waiting = bool(self._queue.waiting_paths())
        is_running = bool(self._worker and self._worker.isRunning())
        self._convert_btn.setEnabled(has_waiting or is_running)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        event.accept()

    def _refresh_counter(self):
        done = self._model.done_count()
        total = self._model.total()
        if total:
            self._counter_lbl.setText(
                self._strings["counter"].format(done=done, total=total)
            )
        else:
            self._counter_lbl.setText("")
