# Imágenes (OCR), Diálogo de descarga de audio y Warning de "sin contenido" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir OCR local de imágenes, un diálogo que pide aceptar la descarga del modelo de audio (con estado "Omitido" si se rechaza), y un manejo de "sin contenido" que muestra una advertencia en vez de generar un `.md` vacío.

**Architecture:** El `ConvertWorker` enruta cada archivo por extensión: audio → `transcribe.py` (faster-whisper), imagen → `ocr.py` (RapidOCR), resto → `markitdown`. Si el texto extraído queda vacío, no se escribe archivo y se emite una señal `file_warning`. La ventana detecta audios al agregarlos y, si el modelo Whisper no está en caché, pregunta al usuario antes de permitir la conversión.

**Tech Stack:** Python 3.12, PyQt6, markitdown 0.1.6, faster-whisper 1.2.1, rapidocr-onnxruntime 1.4.4, pytest.

## Global Constraints

- Todas las dependencias nuevas deben funcionar **offline** y **sin binarios del sistema** (ni ffmpeg ni Tesseract).
- OCR: paquete exacto `rapidocr-onnxruntime==1.4.4` (modelos empaquetados; NO usar `rapidocr` 3.x que descarga de un CDN).
- Audio: `faster-whisper==1.2.1`, modelo tamaño `"base"`, `device="cpu"`, `compute_type="int8"`.
- Los módulos pesados (`faster_whisper`, `rapidocr_onnxruntime`, `markitdown`) se importan **de forma perezosa** dentro de funciones, nunca a nivel de módulo, para no frenar el arranque ni romper los tests (que stubean estas funciones).
- Extensiones de imagen soportadas: `.jpg .jpeg .png .bmp .tiff .tif .webp`.
- Extensiones de audio (ya existentes): `.mp3 .wav .m4a .ogg .flac .aac`.
- Textos de UI en español e inglés (`src/i18n.py`), ambos idiomas siempre sincronizados.
- Mensaje de warning (ES): `"El archivo no contenía nada para convertir."` (EN): `"The file had no content to convert."`
- Tests corren desde `tests/` con `sys.path` ya apuntando a `src/` (ver `tests/conftest.py`). Comando: `pytest` desde la raíz del repo dentro del `.venv`.

---

## File Structure

- **Create** `src/ocr.py` — OCR de imágenes con RapidOCR. Responsable de: detectar imágenes y extraer su texto.
- **Modify** `src/transcribe.py` — añadir `download_root` propio, `is_model_cached()`, y que `transcribe_audio` devuelva solo el cuerpo.
- **Modify** `src/converter.py` — enrutar imágenes a OCR; emitir `file_warning` y no escribir `.md` cuando el resultado esté vacío.
- **Modify** `src/queue_model.py` — estados `WARNING` y `SKIPPED`; íconos de imagen y texto.
- **Modify** `src/queue_widget.py` — pintar los estados `WARNING` y `SKIPPED`.
- **Modify** `src/drop_zone.py` — quitar `.doc`/`.ppt`, agregar `.txt`/`.md` e imágenes.
- **Modify** `src/i18n.py` — textos nuevos (estados y diálogo de audio).
- **Modify** `src/window.py` — conectar `file_warning`; diálogo de descarga de audio y marcado "Omitido".
- **Modify** `requirements.txt` — agregar `rapidocr-onnxruntime==1.4.4`.
- **Modify** `build.sh`, `build-windows.bat`, `.github/workflows/build.yml` — recolectar RapidOCR y libs nativas.
- **Modify** `README.md` — documentar imágenes y el comportamiento de "sin contenido".
- **Modify** `tests/conftest.py`, `tests/test_converter.py`, `tests/test_queue_model.py`, `tests/test_i18n.py` — fixtures y pruebas nuevas.

---

## Task 1: Estados WARNING/SKIPPED e íconos de imagen y texto

**Files:**
- Modify: `src/queue_model.py:6-11` (enum `FileStatus`), `src/queue_model.py:36-44` (`type_icon`)
- Test: `tests/test_queue_model.py`

**Interfaces:**
- Consumes: nada nuevo.
- Produces: `FileStatus.WARNING`, `FileStatus.SKIPPED`; `FileItem.type_icon` devuelve `🖼️` para imágenes y `📄` para `.txt`/`.md`.

- [ ] **Step 1: Write the failing tests**

Añadir al final de `tests/test_queue_model.py`:

```python
def test_file_status_has_warning_and_skipped():
    assert FileStatus.WARNING.value == "warning"
    assert FileStatus.SKIPPED.value == "skipped"


def test_file_item_image_and_text_icons():
    assert FileItem("/x.png").type_icon == "🖼️"
    assert FileItem("/x.jpg").type_icon == "🖼️"
    assert FileItem("/x.jpeg").type_icon == "🖼️"
    assert FileItem("/x.webp").type_icon == "🖼️"
    assert FileItem("/x.txt").type_icon == "📄"
    assert FileItem("/x.md").type_icon == "📄"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_queue_model.py -v`
Expected: FAIL — `AttributeError: WARNING` y/o iconos `🖼️` no coinciden.

- [ ] **Step 3: Add the enum members**

En `src/queue_model.py`, reemplazar el bloque del enum:

```python
class FileStatus(Enum):
    WAITING = "waiting"
    CONVERTING = "converting"
    DONE = "done"
    ERROR = "error"
    WARNING = "warning"
    SKIPPED = "skipped"
```

- [ ] **Step 4: Add the icons**

En `src/queue_model.py`, reemplazar el dict de `type_icon` por:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_queue_model.py -v`
Expected: PASS (todos).

- [ ] **Step 6: Commit**

```bash
git add src/queue_model.py tests/test_queue_model.py
git commit -m "feat: add WARNING/SKIPPED statuses and image/text icons"
```

---

## Task 2: Dependencia de OCR

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: nada.
- Produces: `rapidocr-onnxruntime` disponible para `src/ocr.py`.

- [ ] **Step 1: Add the dependency**

En `requirements.txt`, agregar al final (después de `faster-whisper==1.2.1`):

```
rapidocr-onnxruntime==1.4.4
```

- [ ] **Step 2: Install and verify import**

Run:
```bash
pip install -r requirements.txt
python -c "from rapidocr_onnxruntime import RapidOCR; print('rapidocr OK')"
```
Expected: imprime `rapidocr OK` sin error.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "build: add rapidocr-onnxruntime for offline image OCR"
```

---

## Task 3: Módulo de OCR (`src/ocr.py`)

**Files:**
- Create: `src/ocr.py`
- Test: `tests/test_ocr.py`

**Interfaces:**
- Consumes: `rapidocr_onnxruntime.RapidOCR` (importado perezosamente).
- Produces:
  - `IMAGE_EXTS: set[str]`
  - `is_image(path: str) -> bool`
  - `ocr_image(path: str) -> str` — texto extraído (líneas unidas por `\n`), o `""` si no hay texto.

- [ ] **Step 1: Write the failing tests**

Crear `tests/test_ocr.py`:

```python
import ocr


def test_is_image_detects_extensions():
    assert ocr.is_image("/foto.png")
    assert ocr.is_image("/FOTO.JPG")
    assert ocr.is_image("/x.webp")
    assert not ocr.is_image("/doc.pdf")
    assert not ocr.is_image("/audio.mp3")


def test_ocr_image_joins_lines(monkeypatch):
    class FakeEngine:
        def __call__(self, path):
            # RapidOCR devuelve (result, elapse); result = [[box, text, score], ...]
            return ([[None, "Hola", 0.99], [None, "mundo", 0.98]], None)

    monkeypatch.setattr(ocr, "_get_engine", lambda: FakeEngine())
    assert ocr.ocr_image("/x.png") == "Hola\nmundo"


def test_ocr_image_empty_when_no_text(monkeypatch):
    class FakeEngine:
        def __call__(self, path):
            return (None, None)

    monkeypatch.setattr(ocr, "_get_engine", lambda: FakeEngine())
    assert ocr.ocr_image("/x.png") == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ocr.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ocr'`.

- [ ] **Step 3: Create the module**

Crear `src/ocr.py`:

```python
"""OCR local de imágenes con RapidOCR (rapidocr-onnxruntime).

Se usa porque markitdown no extrae texto de imágenes por sí solo (solo
metadatos o, con un LLM, una descripción). RapidOCR corre offline, trae los
modelos ONNX empaquetados y no requiere binarios del sistema.
"""
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# El motor es costoso de crear; se instancia una sola vez y se reutiliza.
_engine = None


def is_image(path: str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def ocr_image(path: str) -> str:
    engine = _get_engine()
    result, _ = engine(path)
    if not result:
        return ""
    lines = [str(line[1]).strip() for line in result if len(line) > 1 and line[1]]
    return "\n".join(l for l in lines if l)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ocr.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/ocr.py tests/test_ocr.py
git commit -m "feat: add local image OCR module using RapidOCR"
```

---

## Task 4: Audio — download_root y detección de caché (`src/transcribe.py`)

**Files:**
- Modify: `src/transcribe.py`
- Test: `tests/test_transcribe.py`

**Interfaces:**
- Consumes: `faster_whisper.WhisperModel` (perezoso).
- Produces:
  - `MODEL_DIR: Path` (carpeta de descarga propia).
  - `is_model_cached() -> bool`.
  - `transcribe_audio(path: str) -> str` — devuelve **solo el cuerpo** transcrito (sin título), `""` si no hay habla.
  - (sin cambios) `AUDIO_EXTS`, `is_audio()`.

- [ ] **Step 1: Write the failing tests**

Crear `tests/test_transcribe.py`:

```python
import transcribe


def test_is_audio_detects_extensions():
    assert transcribe.is_audio("/a.mp3")
    assert transcribe.is_audio("/A.WAV")
    assert not transcribe.is_audio("/a.png")


def test_is_model_cached_false_when_dir_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(transcribe, "MODEL_DIR", tmp_path)
    assert transcribe.is_model_cached() is False


def test_is_model_cached_true_when_model_bin_present(tmp_path, monkeypatch):
    monkeypatch.setattr(transcribe, "MODEL_DIR", tmp_path)
    nested = tmp_path / "models--Systran--faster-whisper-base" / "snapshots" / "abc"
    nested.mkdir(parents=True)
    (nested / "model.bin").write_bytes(b"x")
    assert transcribe.is_model_cached() is True


def test_transcribe_audio_returns_body(monkeypatch):
    class Seg:
        def __init__(self, text):
            self.text = text

    class FakeModel:
        def transcribe(self, path):
            class Info:
                language = "es"
            return ([Seg(" Hola "), Seg(" mundo ")], Info())

    monkeypatch.setattr(transcribe, "_get_model", lambda: FakeModel())
    assert transcribe.transcribe_audio("/a.mp3") == "Hola\n\nmundo"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_transcribe.py -v`
Expected: FAIL — `AttributeError: module 'transcribe' has no attribute 'MODEL_DIR'` / `is_model_cached`.

- [ ] **Step 3: Rewrite the module**

Reemplazar `src/transcribe.py` completo por:

```python
"""Transcripción de audio local con faster-whisper.

Corre 100% offline tras descargar el modelo una vez; multilingüe; no requiere
ffmpeg del sistema (trae las libs de FFmpeg vía PyAV). El modelo se descarga a
MODEL_DIR en el primer uso y queda cacheado allí.
"""
from pathlib import Path

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}

_MODEL_SIZE = "base"
# Carpeta propia de descarga para poder detectar de forma fiable si el modelo
# ya está en caché (en Windows y macOS).
MODEL_DIR = Path.home() / ".markit" / "whisper-models"

_model = None


def is_audio(path: str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTS


def is_model_cached() -> bool:
    """True si el modelo Whisper ya fue descargado a MODEL_DIR."""
    return MODEL_DIR.exists() and any(MODEL_DIR.rglob("model.bin"))


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        _model = WhisperModel(
            _MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root=str(MODEL_DIR),
        )
    return _model


def transcribe_audio(path: str) -> str:
    """Devuelve el texto transcrito (cuerpo), o '' si no hay habla."""
    model = _get_model()
    segments, _info = model.transcribe(path)
    return "\n\n".join(seg.text.strip() for seg in segments if seg.text.strip())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_transcribe.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/transcribe.py tests/test_transcribe.py
git commit -m "feat: add whisper model cache detection and body-only transcript"
```

---

## Task 5: Enrutamiento a OCR y warning de "sin contenido" (`src/converter.py`)

**Files:**
- Modify: `src/converter.py`
- Test: `tests/test_converter.py`

**Interfaces:**
- Consumes: `transcribe.is_audio`, `transcribe.transcribe_audio`, `ocr.is_image`, `ocr.ocr_image`.
- Produces: señal `ConvertWorker.file_warning = pyqtSignal(str)` (emite el path cuando el resultado está vacío y NO escribe `.md`).

- [ ] **Step 1: Write the failing tests**

Reemplazar el test de audio existente y añadir dos nuevos en `tests/test_converter.py`. Reemplazar `test_routes_audio_to_whisper_not_markitdown` por estos tres:

```python
def test_routes_audio_to_whisper_not_markitdown(qapp, tmp_audio, tmp_path, monkeypatch):
    import converter
    monkeypatch.setattr(converter, "transcribe_audio", lambda p: "hola mundo")
    out_dir = tmp_path / "output"
    worker = converter.ConvertWorker([tmp_audio], str(out_dir))
    finished = []
    worker.file_finished.connect(lambda p, out: finished.append(out))
    worker.run()
    assert len(finished) == 1
    out_file = Path(finished[0])
    assert out_file.stem == "clip"
    assert out_file.read_text(encoding="utf-8") == "hola mundo"


def test_routes_image_to_ocr(qapp, tmp_png, tmp_path, monkeypatch):
    import converter
    monkeypatch.setattr(converter, "ocr_image", lambda p: "texto en imagen")
    out_dir = tmp_path / "output"
    worker = converter.ConvertWorker([tmp_png], str(out_dir))
    finished = []
    worker.file_finished.connect(lambda p, out: finished.append(out))
    worker.run()
    assert len(finished) == 1
    assert Path(finished[0]).read_text(encoding="utf-8") == "texto en imagen"


def test_empty_result_emits_warning_and_writes_no_file(qapp, tmp_png, tmp_path, monkeypatch):
    import converter
    monkeypatch.setattr(converter, "ocr_image", lambda p: "   ")  # solo espacios
    out_dir = tmp_path / "output"
    worker = converter.ConvertWorker([tmp_png], str(out_dir))
    warned, finished = [], []
    worker.file_warning.connect(lambda p: warned.append(p))
    worker.file_finished.connect(lambda p, out: finished.append(out))
    worker.run()
    assert warned == [tmp_png]
    assert finished == []
    assert not (out_dir / "clip.md").exists()
```

- [ ] **Step 2: Add the `tmp_png` fixture**

En `tests/conftest.py`, añadir después del fixture `tmp_audio`:

```python
@pytest.fixture
def tmp_png(tmp_path):
    # PNG 1x1 transparente válido (las pruebas stubean el OCR).
    import base64
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    f = tmp_path / "clip.png"
    f.write_bytes(data)
    return str(f)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_converter.py -v`
Expected: FAIL — `AttributeError: 'ConvertWorker' object has no attribute 'file_warning'` y/o `ocr_image` no importado.

- [ ] **Step 4: Update the converter**

En `src/converter.py`:

(a) Cambiar el import de transcribe y añadir ocr — reemplazar la línea `from transcribe import is_audio, transcribe_audio` por:

```python
from transcribe import is_audio, transcribe_audio
from ocr import is_image, ocr_image
```

(b) Añadir la señal nueva — dentro de `class ConvertWorker`, junto a las otras señales:

```python
    file_started = pyqtSignal(str)
    file_finished = pyqtSignal(str, str)
    file_error = pyqtSignal(str, str)
    file_warning = pyqtSignal(str)
    all_done = pyqtSignal()
```

(c) Reemplazar el bloque `try:` que hace la conversión (desde `if is_audio(path):` hasta el `self.file_finished.emit(...)`) por:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_converter.py -v`
Expected: PASS (incluye los 3 nuevos/actualizados y los existentes de texto/html/error).

- [ ] **Step 6: Commit**

```bash
git add src/converter.py tests/test_converter.py tests/conftest.py
git commit -m "feat: route images to OCR and emit warning instead of empty .md"
```

---

## Task 6: Textos nuevos (`src/i18n.py`)

**Files:**
- Modify: `src/i18n.py`
- Test: `tests/test_i18n.py`

**Interfaces:**
- Consumes: nada.
- Produces (claves en ambos idiomas): `status_warning`, `status_skipped`, `warn_no_content`, `audio_dl_title`, `audio_dl_body`, `audio_dl_accept`, `audio_dl_skip`.

- [ ] **Step 1: Write the failing test**

En `tests/test_i18n.py`, añadir las nuevas claves a `REQUIRED_KEYS`:

```python
REQUIRED_KEYS = [
    "drop_hint", "drop_sub", "btn_select", "btn_convert", "btn_cancel",
    "btn_open_folder", "status_waiting", "status_converting", "status_done",
    "status_error", "folder_label", "folder_change", "queue_clear",
    "queue_header", "counter", "window_title",
    "status_warning", "status_skipped", "warn_no_content",
    "audio_dl_title", "audio_dl_body", "audio_dl_accept", "audio_dl_skip",
]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_i18n.py::test_all_required_keys_present -v`
Expected: FAIL — `Missing key 'status_warning' in lang 'es'`.

- [ ] **Step 3: Add the strings**

En `src/i18n.py`, añadir estas claves dentro del dict `"es"` (antes de `"window_title"`):

```python
        "status_warning": "Sin contenido",
        "status_skipped": "Omitido",
        "warn_no_content": "El archivo no contenía nada para convertir.",
        "audio_dl_title": "Descargar modelo de voz",
        "audio_dl_body": "Para convertir audio se debe descargar una sola vez un modelo de voz (~140 MB). ¿Deseas descargarlo ahora?",
        "audio_dl_accept": "Descargar y continuar",
        "audio_dl_skip": "Omitir audio",
```

Y dentro del dict `"en"` (antes de `"window_title"`):

```python
        "status_warning": "No content",
        "status_skipped": "Skipped",
        "warn_no_content": "The file had no content to convert.",
        "audio_dl_title": "Download speech model",
        "audio_dl_body": "Converting audio requires a one-time download of a speech model (~140 MB). Do you want to download it now?",
        "audio_dl_accept": "Download and continue",
        "audio_dl_skip": "Skip audio",
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_i18n.py -v`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add src/i18n.py tests/test_i18n.py
git commit -m "feat: add i18n strings for warning, skipped and audio download dialog"
```

---

## Task 7: Pintado de WARNING y SKIPPED en la cola (`src/queue_widget.py`)

**Files:**
- Modify: `src/queue_widget.py:34-42` (colores), `src/queue_widget.py:84-107` (`refresh`)
- Test: `tests/test_queue_widget.py`

**Interfaces:**
- Consumes: `FileStatus.WARNING`, `FileStatus.SKIPPED`; `strings["status_warning"]`, `strings["status_skipped"]`.
- Produces: filas que muestran el texto correcto y, en WARNING, un tooltip con el mensaje de error/aviso.

- [ ] **Step 1: Write the failing test**

Añadir al final de `tests/test_queue_widget.py`:

```python
def test_warning_and_skipped_render(qapp):
    from queue_widget import QueueWidget
    from queue_model import FileQueueModel, FileStatus
    from i18n import load_strings

    strings = load_strings()
    model = FileQueueModel()
    w = QueueWidget(model, strings)
    w.add_files(["/a.png", "/b.mp3"])

    w.update_status("/a.png", FileStatus.WARNING, strings["warn_no_content"])
    w.update_status("/b.mp3", FileStatus.SKIPPED)

    row_a = w._rows["/a.png"]
    row_b = w._rows["/b.mp3"]
    assert strings["status_warning"] in row_a._status_lbl.text()
    assert row_a._status_lbl.toolTip() == strings["warn_no_content"]
    assert strings["status_skipped"] in row_b._status_lbl.text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_queue_widget.py::test_warning_and_skipped_render -v`
Expected: FAIL — el label queda vacío para WARNING/SKIPPED (la rama no existe).

- [ ] **Step 3: Add colors**

En `src/queue_widget.py`, en el bloque de colores (después de `_BORDER_ROW`), añadir:

```python
_CLR_WARN    = "#C9920B"   # ámbar
_CLR_SKIP    = "#9A9BB8"   # gris
_BG_WARN     = "#FFF8EC"
```

- [ ] **Step 4: Add the refresh branches**

En `src/queue_widget.py`, dentro de `refresh`, antes del cierre del método (después de la rama `FileStatus.ERROR`), añadir:

```python
        elif s == FileStatus.WARNING:
            self._status_lbl.setText(f"⚠ {self._strings['status_warning']}")
            self._status_lbl.setStyleSheet(f"font-size:11px;color:{_CLR_WARN};font-weight:600;")
            self.setStyleSheet(f"QFrame{{background:{_BG_WARN};border-bottom:1px solid {_BORDER_ROW};}}")
            if self._item.error:
                self._status_lbl.setToolTip(self._item.error)
            self._timer.stop()
        elif s == FileStatus.SKIPPED:
            self._status_lbl.setText(self._strings["status_skipped"])
            self._status_lbl.setStyleSheet(f"font-size:11px;color:{_CLR_SKIP};font-style:italic;")
            self.setStyleSheet(f"QFrame{{background:{_BG_ROW};border-bottom:1px solid {_BORDER_ROW};}}")
            self._timer.stop()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_queue_widget.py -v`
Expected: PASS (incluye el nuevo y los existentes).

- [ ] **Step 6: Commit**

```bash
git add src/queue_widget.py tests/test_queue_widget.py
git commit -m "feat: render WARNING and SKIPPED rows in the queue"
```

---

## Task 8: Extensiones soportadas (`src/drop_zone.py`)

**Files:**
- Modify: `src/drop_zone.py:12-18` (tupla `_SUPPORTED_EXTS`)
- Test: `tests/test_drop_zone.py`

**Interfaces:**
- Consumes: nada.
- Produces: `_SUPPORTED_EXTS` sin `.doc`/`.ppt`, con `.txt`, `.md` y las 7 de imagen.

- [ ] **Step 1: Write the failing test**

Añadir al final de `tests/test_drop_zone.py`:

```python
def test_supported_exts_cover_images_text_and_drop_legacy():
    from drop_zone import _SUPPORTED_EXTS
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".txt", ".md"):
        assert ext in _SUPPORTED_EXTS
    assert ".doc" not in _SUPPORTED_EXTS
    assert ".ppt" not in _SUPPORTED_EXTS
    # Modernos sí permanecen
    assert ".docx" in _SUPPORTED_EXTS
    assert ".pptx" in _SUPPORTED_EXTS
    assert ".xlsx" in _SUPPORTED_EXTS
    assert ".xls" in _SUPPORTED_EXTS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_drop_zone.py -v`
Expected: FAIL — `.doc` aún presente y/o `.png` ausente.

- [ ] **Step 3: Update the tuple**

En `src/drop_zone.py`, reemplazar la definición de `_SUPPORTED_EXTS` por:

```python
_SUPPORTED_EXTS = (
    ".pdf", ".docx", ".xlsx", ".xls", ".pptx",
    ".html", ".htm", ".csv", ".json", ".xml", ".epub", ".msg", ".zip",
    ".txt", ".md",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac",
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp",
)
_SUPPORTED = " ".join(f"*{ext}" for ext in _SUPPORTED_EXTS)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_drop_zone.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/drop_zone.py tests/test_drop_zone.py
git commit -m "feat: support images/txt/md, drop unsupported legacy .doc/.ppt"
```

---

## Task 9: Diálogo de descarga de audio y wiring de warning (`src/window.py`)

**Files:**
- Modify: `src/window.py` (método `_on_files_added`, conexión de señales del worker)
- Test: `tests/test_window.py`

**Interfaces:**
- Consumes: `transcribe.is_audio`, `transcribe.is_model_cached`; `FileStatus.SKIPPED`, `FileStatus.WARNING`; `strings["audio_dl_*"]`, `strings["warn_no_content"]`; `ConvertWorker.file_warning`.
- Produces: comportamiento de UI (no expone API nueva consumida por otras tareas).

**Diseño:** `_on_files_added` agrega los archivos a la cola y, si hay audios y el modelo no está en caché, abre un `QMessageBox`. Si el usuario elige "Omitir audio", cada audio pasa a `SKIPPED`. La detección del diálogo se aísla en un método `_ask_audio_download()` para poder stubearlo en tests.

- [ ] **Step 1: Write the failing tests**

Añadir al final de `tests/test_window.py`:

```python
def test_declined_audio_is_skipped(qapp, monkeypatch):
    import transcribe
    from window import MainWindow
    from queue_model import FileStatus

    monkeypatch.setattr(transcribe, "is_model_cached", lambda: False)
    w = MainWindow()
    # Simula que el usuario rechaza la descarga.
    monkeypatch.setattr(w, "_ask_audio_download", lambda: False)
    w._on_files_added(["/song.mp3", "/doc.pdf"])

    statuses = {i.path: i.status for i in w._model.items()}
    assert statuses["/song.mp3"] == FileStatus.SKIPPED
    assert statuses["/doc.pdf"] == FileStatus.WAITING
    w.close()


def test_accepted_audio_stays_waiting(qapp, monkeypatch):
    import transcribe
    from window import MainWindow
    from queue_model import FileStatus

    monkeypatch.setattr(transcribe, "is_model_cached", lambda: False)
    w = MainWindow()
    monkeypatch.setattr(w, "_ask_audio_download", lambda: True)
    w._on_files_added(["/song.mp3"])

    assert w._model.items()[0].status == FileStatus.WAITING
    w.close()


def test_no_dialog_when_model_cached(qapp, monkeypatch):
    import transcribe
    from window import MainWindow
    from queue_model import FileStatus

    monkeypatch.setattr(transcribe, "is_model_cached", lambda: True)
    called = []
    w = MainWindow()
    monkeypatch.setattr(w, "_ask_audio_download", lambda: called.append(True) or True)
    w._on_files_added(["/song.mp3"])

    assert called == []  # no se preguntó porque ya está en caché
    assert w._model.items()[0].status == FileStatus.WAITING
    w.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_window.py -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute '_ask_audio_download'`.

- [ ] **Step 3: Add imports**

En `src/window.py`, junto a los imports de `from converter import ConvertWorker` y demás, añadir:

```python
from transcribe import is_audio, is_model_cached
```

(`FileStatus` ya está importado en la línea `from queue_model import FileQueueModel, FileStatus`.)

- [ ] **Step 4: Replace `_on_files_added` and add the dialog helper**

En `src/window.py`, reemplazar el método `_on_files_added` por:

```python
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
```

- [ ] **Step 5: Wire the `file_warning` signal**

En `src/window.py`, en `_on_convert_clicked`, después de la línea `self._worker.file_error.connect(self._on_file_error)`, añadir:

```python
        self._worker.file_warning.connect(self._on_file_warning)
```

Y añadir el método manejador (junto a `_on_file_error`):

```python
    def _on_file_warning(self, path: str):
        self._queue.update_status(
            path, FileStatus.WARNING, self._strings["warn_no_content"]
        )
        self._refresh_counter()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_window.py -v`
Expected: PASS (3 nuevos + el existente `test_main_window_opens`).

- [ ] **Step 7: Commit**

```bash
git add src/window.py tests/test_window.py
git commit -m "feat: audio download prompt with skip, and warning wiring in UI"
```

---

## Task 10: Empaquetado — RapidOCR y libs nativas

**Files:**
- Modify: `build.sh`, `build-windows.bat`, `.github/workflows/build.yml`

**Interfaces:**
- Consumes: nada.
- Produces: builds que incluyen `ocr.py`, `rapidocr_onnxruntime` (con sus modelos), `cv2` y `shapely`.

- [ ] **Step 1: Update `build.sh`**

En `build.sh`, en la sección de flags de PyInstaller, después de `--hidden-import transcribe \`, añadir `--hidden-import ocr \`; y después de `--collect-all av \`, añadir:

```bash
    --collect-all rapidocr_onnxruntime \
    --collect-all cv2 \
    --collect-all shapely \
```

- [ ] **Step 2: Update `build-windows.bat`**

En `build-windows.bat`, después de `--hidden-import transcribe ^`, añadir `--hidden-import ocr ^`; y después de `--collect-all av ^`, añadir:

```bat
    --collect-all rapidocr_onnxruntime ^
    --collect-all cv2 ^
    --collect-all shapely ^
```

- [ ] **Step 3: Update CI (`.github/workflows/build.yml`)**

En los **tres** bloques de PyInstaller (macOS ARM, macOS Intel con `\`, y Windows con `` ` ``):
- añadir `--hidden-import ocr` tras `--hidden-import transcribe`
- añadir `--collect-all rapidocr_onnxruntime`, `--collect-all cv2`, `--collect-all shapely` tras `--collect-all av`
(respetando el carácter de continuación de cada bloque: `\` en los dos de macOS, `` ` `` en el de Windows).

- [ ] **Step 4: Verify no stale references**

Run: `grep -rn "collect-all rapidocr_onnxruntime" build.sh build-windows.bat .github/workflows/build.yml`
Expected: 5 coincidencias (1 + 1 + 3).

- [ ] **Step 5: Commit**

```bash
git add build.sh build-windows.bat .github/workflows/build.yml
git commit -m "build: bundle RapidOCR, cv2 and shapely for image OCR"
```

> ⚠️ **Nota de riesgo:** el empaquetado de RapidOCR/cv2/shapely (binarios nativos) solo se confirma con un build real en CI. Si faltan modelos en runtime, añadir `--collect-data rapidocr_onnxruntime`. Si faltan libs de shapely (GEOS), añadir `--collect-binaries shapely`.

---

## Task 11: Documentación (`README.md`)

**Files:**
- Modify: `README.md` (tabla "Supported formats")

**Interfaces:**
- Consumes: nada. Produces: nada (docs).

- [ ] **Step 1: Update the formats table**

En `README.md`, reemplazar la tabla de formatos por:

```markdown
| Category | Formats |
|---|---|
| Documents | PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx / .xls) |
| Text | TXT, Markdown (.md) |
| Data | CSV, JSON, XML |
| Web | HTML |
| Books | EPUB |
| Images | JPG, JPEG, PNG, BMP, TIFF, WEBP (text extracted via local OCR) |
| Audio | MP3, WAV, M4A, OGG, FLAC, AAC (transcribed locally with faster-whisper) |
| Email | Outlook (.msg) |
| Archives | ZIP |

> **Images** are read with [RapidOCR](https://github.com/RapidAI/RapidOCR) (offline, no system dependencies). **Audio** is transcribed with [faster-whisper](https://github.com/SYSTRAN/faster-whisper); the speech model (~140 MB) is downloaded once on first use (the app asks for confirmation). If a file has no extractable text (e.g. a photo with no text, or silent audio), no Markdown file is produced and the item is flagged with a warning.
```

- [ ] **Step 2: Verify legacy formats are not advertised**

Run: `grep -n "\.doc\b\|\.ppt\b\|YouTube\|SpeechRecognition" README.md`
Expected: sin coincidencias (no se promete `.doc`, `.ppt`, YouTube ni SpeechRecognition).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document image OCR, audio download prompt and no-content behavior"
```

---

## Task 12: Verificación final

**Files:** ninguno (solo verificación).

- [ ] **Step 1: Syntax check de todo `src/`**

Run: `python -m py_compile src/*.py`
Expected: sin salida (éxito).

- [ ] **Step 2: Suite completa**

Run: `pytest -v`
Expected: PASS en todos. Si `rapidocr-onnxruntime`/`faster-whisper` no están instalados, los tests siguen pasando porque stubean `ocr_image`/`transcribe_audio`/`_get_engine`/`_get_model`.

- [ ] **Step 3: Smoke test manual de la app**

Run: `python src/main.py`
Verificar: arrastrar una imagen con texto → genera `.md` con el texto; una imagen sin texto → fila en ⚠ "Sin contenido", sin `.md`; un audio con el modelo no descargado → aparece el diálogo; "Omitir audio" → fila "Omitido".

- [ ] **Step 4: Verificación de cierre**

REQUIRED SUB-SKILL: usar superpowers:verification-before-completion antes de declarar el trabajo terminado (correr los comandos y confirmar la salida real, no asumir).

---

## Self-Review

**1. Spec coverage** (contra `docs/PLAN-audio-imagenes-ocr.md` y las 9 decisiones):
- Decisión 1 (Whisper local): ya implementado antes; Task 4 ajusta caché y cuerpo. ✅
- Decisión 2 (diálogo descarga si no cacheado): Task 9. ✅
- Decisión 3 (rechazo → "Omitido"): Task 1 (estado) + Task 7 (pintado) + Task 9 (lógica). ✅
- Decisión 4 (sin YouTube): ya hecho; Task 11 verifica que no se anuncie. ✅
- Decisión 5 (imágenes RapidOCR, formatos): Task 2/3/5/8. ✅
- Decisión 6 (quitar `.doc`/`.ppt`): Task 8. ✅
- Decisión 7 (Excel xlsx/xls): Task 8 (se conservan) + Task 11 (documentado). ✅
- Decisión 8 (`.txt`/`.md`): Task 1 (íconos) + Task 8 (selector). ✅
- Decisión 9 (sin contenido → warning, no `.md`): Task 5 + Task 7 + Task 9. ✅

**2. Placeholder scan:** sin "TBD"/"TODO"/"manejar edge cases"; todo paso de código incluye el código. ✅

**3. Type consistency:** `file_warning = pyqtSignal(str)` se emite con `(path)` en converter (Task 5) y se conecta a `_on_file_warning(self, path)` en window (Task 9). `transcribe_audio`/`ocr_image` devuelven `str`. `is_model_cached() -> bool`. `_ask_audio_download() -> bool`. Nombres consistentes entre tareas. ✅
