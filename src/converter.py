import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from transcribe import is_audio, transcribe_audio
from ocr import is_image, ocr_image

_LOG = Path(tempfile.gettempdir()) / "markit.log"


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
    file_warning = pyqtSignal(str)
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
            # markitdown se instancia de forma perezosa: si solo hay audio, no
            # hace falta cargarlo. Whisper se carga aparte dentro de transcribe.
            md = None
            out = Path(self._output_dir)
            out.mkdir(parents=True, exist_ok=True)
            for path in self._files:
                if self._cancelled:
                    break
                _log(f"Convirtiendo: {path}")
                self.file_started.emit(path)
                try:
                    if is_audio(path):
                        _log(f"Audio -> transcribiendo con Whisper: {path}")
                        text = transcribe_audio(path)
                    elif is_image(path):
                        _log(f"Imagen -> OCR con RapidOCR: {path}")
                        text = ocr_image(path)
                    else:
                        if md is None:
                            _log("Instanciando MarkItDown...")
                            from markitdown import MarkItDown
                            md = MarkItDown()
                            _log("MarkItDown OK")
                        text = md.convert(path).text_content
                    if not (text or "").strip():
                        _log(f"Sin contenido para convertir: {path}")
                        self.file_warning.emit(path)
                        continue
                    stem = Path(path).stem
                    out_path = out / f"{stem}.md"
                    if out_path.exists():
                        for n in range(1, 100):
                            candidate = out / f"{stem}_{n}.md"
                            if not candidate.exists():
                                out_path = candidate
                                break
                    out_path.write_text(text, encoding="utf-8")
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
