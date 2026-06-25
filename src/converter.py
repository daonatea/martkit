import traceback
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from markitdown import MarkItDown

_LOG = Path("/tmp/markit.log")


def _log(msg: str) -> None:
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')} {msg}\n")
            f.flush()
    except Exception:
        pass


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
        _log(f"run() started files={self._files} out={self._output_dir}")
        try:
            if self._cancelled:
                return
            _log("Instanciando MarkItDown...")
            md = MarkItDown()
            _log("MarkItDown OK")
            out = Path(self._output_dir)
            out.mkdir(parents=True, exist_ok=True)
            for path in self._files:
                if self._cancelled:
                    break
                _log(f"Convirtiendo: {path}")
                self.file_started.emit(path)
                try:
                    result = md.convert(path)
                    stem = Path(path).stem
                    out_path = out / f"{stem}.md"
                    if out_path.exists():
                        for n in range(1, 100):
                            candidate = out / f"{stem}_{n}.md"
                            if not candidate.exists():
                                out_path = candidate
                                break
                    out_path.write_text(result.text_content, encoding="utf-8")
                    _log(f"OK -> {out_path}")
                    self.file_finished.emit(path, str(out_path))
                except Exception as exc:
                    tb = traceback.format_exc()
                    _log(f"ERROR en {path}:\n{tb}")
                    self.file_error.emit(path, str(exc))
        except Exception as exc:
            tb = traceback.format_exc()
            _log(f"CRITICO (fuera del loop):\n{tb}")
            # Notificar error en todos los archivos para que el UI lo muestre
            for path in self._files:
                self.file_error.emit(path, str(exc))
        finally:
            _log("run() terminado")
            self.all_done.emit()
