from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from markitdown import MarkItDown


class ConvertWorker(QThread):
    file_started = pyqtSignal(str)
    file_finished = pyqtSignal(str, str)
    file_error = pyqtSignal(str, str)
    all_done = pyqtSignal()

    def __init__(self, files: list[str], output_dir: str, parent=None):
        super().__init__(parent)
        self._files = list(files)
        self._output_dir = output_dir
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        if self._cancelled:
            self.all_done.emit()
            return

        md = MarkItDown()
        out = Path(self._output_dir)
        out.mkdir(parents=True, exist_ok=True)

        for path in self._files:
            if self._cancelled:
                break
            self.file_started.emit(path)
            try:
                result = md.convert(path)
                stem = Path(path).stem
                out_path = out / f"{stem}.md"
                out_path.write_text(result.text_content, encoding="utf-8")
                self.file_finished.emit(path, str(out_path))
            except Exception as exc:
                self.file_error.emit(path, str(exc))

        self.all_done.emit()
