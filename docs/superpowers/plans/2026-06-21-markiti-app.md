# Markiti App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Mac desktop app with PyQt6 that wraps Microsoft's markitdown library, letting non-technical users convert documents to Markdown via drag & drop.

**Architecture:** Single-window PyQt6 app (640×460 px). Left panel = animated drop zone. Right panel = scrollable file queue with per-file status. Bottom bar = "Convert all" + "Open folder". A `QThread` worker runs `markitdown` sequentially without blocking the UI. `QSettings` persists the output folder. Dict-based i18n loads Spanish or English at startup from `QLocale`.

**Tech Stack:** Python 3.10+, PyQt6, markitdown[all], PyInstaller, pytest

## Global Constraints

- Python ≥ 3.10 (uses `X | Y` union syntax)
- PyQt6 (not PyQt5, not PySide6)
- macOS only — `--windowed --onedir` PyInstaller flags
- Window fixed size: 640 × 460 px (`setFixedSize`)
- Output folder default: `~/Documents/Markiti`
- Locale detection: `QLocale.system().name()[:2]` → `"es"` or fallback `"en"`
- Output file: same stem as input + `.md`, written to configured output folder
- Existing `.md` files are silently overwritten
- Duplicate paths in the queue are silently ignored

---

## File Map

| File | Responsibility |
|---|---|
| `src/main.py` | Entry point: `QApplication` setup, launch `MainWindow` |
| `src/window.py` | `MainWindow`: assembles all widgets, wires all signals |
| `src/drop_zone.py` | `DropZone(QWidget)`: animated blob, drag & drop, file selector button |
| `src/queue_widget.py` | `QueueWidget` + `FileRow`: visual file list with per-file status rows |
| `src/queue_model.py` | `FileQueueModel`, `FileItem`, `FileStatus`: pure-Python data model (no Qt) |
| `src/converter.py` | `ConvertWorker(QThread)`: runs markitdown sequentially, emits signals |
| `src/settings.py` | `AppSettings`: thin `QSettings` wrapper for output folder |
| `src/i18n.py` | `load_strings() → dict`: Spanish/English string lookup with fallback |
| `tests/conftest.py` | `qapp` session fixture, `tmp_txt` / `tmp_html` file fixtures |
| `tests/test_settings.py` | Unit tests for `AppSettings` |
| `tests/test_i18n.py` | Unit tests for `load_strings()` |
| `tests/test_converter.py` | Unit tests for `ConvertWorker` (run synchronously via `.run()`) |
| `tests/test_queue_model.py` | Unit tests for `FileQueueModel` and `FileItem` |
| `requirements.txt` | Runtime deps |
| `requirements-dev.txt` | Dev/test deps |
| `build.sh` | PyInstaller invocation → `dist/Markiti.app` |

---

## Task 1: Project scaffolding + test infrastructure

**Files:**
- Create: `src/` (directory)
- Create: `tests/` (directory)
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: `qapp` pytest fixture, `tmp_txt` fixture, `tmp_html` fixture

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src tests
touch src/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
markitdown[all]
PyQt6
```

- [ ] **Step 3: Write `requirements-dev.txt`**

```
-r requirements.txt
pytest
pytest-qt
PyInstaller
```

- [ ] **Step 4: Install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Expected: no errors. Verify with:
```bash
python3 -c "import PyQt6; import markitdown; print('OK')"
```

- [ ] **Step 5: Write `tests/conftest.py`**

```python
import sys
from pathlib import Path
import pytest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app

@pytest.fixture
def tmp_txt(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("# Hello\nThis is a test document.", encoding="utf-8")
    return str(f)

@pytest.fixture
def tmp_html(tmp_path):
    f = tmp_path / "sample.html"
    f.write_text("<html><body><h1>Hello</h1><p>World</p></body></html>", encoding="utf-8")
    return str(f)
```

- [ ] **Step 6: Verify pytest collects correctly**

```bash
pytest tests/ --collect-only
```

Expected: `0 items` (no tests yet), no import errors.

- [ ] **Step 7: Commit**

```bash
git add src/ tests/ requirements.txt requirements-dev.txt
git commit -m "feat: project scaffolding and test infrastructure"
```

---

## Task 2: Settings module

**Files:**
- Create: `src/settings.py`
- Create: `tests/test_settings.py`

**Interfaces:**
- Produces: `AppSettings(qsettings=None)`, `.output_folder() → str`, `.set_output_folder(path: str) → None`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_settings.py
from pathlib import Path
from PyQt6.QtCore import QSettings

def test_default_output_folder(qapp, tmp_path):
    from settings import AppSettings
    qs = QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    s = AppSettings(qsettings=qs)
    assert s.output_folder() == str(Path.home() / "Documents" / "Markiti")

def test_set_and_get_output_folder(qapp, tmp_path):
    from settings import AppSettings
    qs = QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    s = AppSettings(qsettings=qs)
    s.set_output_folder("/custom/path")
    assert s.output_folder() == "/custom/path"

def test_persists_across_instances(qapp, tmp_path):
    from settings import AppSettings
    ini = str(tmp_path / "test.ini")
    qs1 = QSettings(ini, QSettings.Format.IniFormat)
    AppSettings(qsettings=qs1).set_output_folder("/saved/path")

    qs2 = QSettings(ini, QSettings.Format.IniFormat)
    assert AppSettings(qsettings=qs2).output_folder() == "/saved/path"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_settings.py -v
```

Expected: `ImportError: No module named 'settings'`

- [ ] **Step 3: Write `src/settings.py`**

```python
from pathlib import Path
from PyQt6.QtCore import QSettings

_DEFAULT_OUTPUT = str(Path.home() / "Documents" / "Markiti")


class AppSettings:
    def __init__(self, qsettings: QSettings | None = None):
        self._qs = qsettings or QSettings("Markiti", "Markiti")

    def output_folder(self) -> str:
        return self._qs.value("output_folder", _DEFAULT_OUTPUT)

    def set_output_folder(self, path: str) -> None:
        self._qs.setValue("output_folder", path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_settings.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add src/settings.py tests/test_settings.py
git commit -m "feat: AppSettings with QSettings-backed output folder"
```

---

## Task 3: i18n module

**Files:**
- Create: `src/i18n.py`
- Create: `tests/test_i18n.py`

**Interfaces:**
- Produces: `load_strings() → dict[str, str]`, module-level `_STRINGS: dict[str, dict]`
- Keys guaranteed: `drop_hint`, `drop_sub`, `btn_select`, `btn_convert`, `btn_cancel`, `btn_open_folder`, `status_waiting`, `status_converting`, `status_done`, `status_error`, `folder_label`, `folder_change`, `queue_clear`, `queue_header`, `counter`, `window_title`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_i18n.py
from unittest.mock import patch

REQUIRED_KEYS = [
    "drop_hint", "drop_sub", "btn_select", "btn_convert", "btn_cancel",
    "btn_open_folder", "status_waiting", "status_converting", "status_done",
    "status_error", "folder_label", "folder_change", "queue_clear",
    "queue_header", "counter", "window_title",
]

def test_spanish_locale(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "es_ES"
        import i18n
        strings = i18n.load_strings()
        assert strings["btn_convert"] == "Convertir todo →"
        assert strings["status_done"] == "Listo"

def test_english_locale(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "en_US"
        import i18n
        strings = i18n.load_strings()
        assert strings["btn_convert"] == "Convert all →"
        assert strings["status_done"] == "Done"

def test_unknown_locale_falls_back_to_english(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "fr_FR"
        import i18n
        strings = i18n.load_strings()
        assert strings["btn_convert"] == "Convert all →"

def test_all_required_keys_present():
    import i18n
    for lang, lang_strings in i18n._STRINGS.items():
        for key in REQUIRED_KEYS:
            assert key in lang_strings, f"Missing key '{key}' in lang '{lang}'"

def test_counter_template_interpolates(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "es_ES"
        import i18n
        strings = i18n.load_strings()
        result = strings["counter"].format(done=2, total=5)
        assert result == "2 / 5 listos"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_i18n.py -v
```

Expected: `ImportError: No module named 'i18n'`

- [ ] **Step 3: Write `src/i18n.py`**

```python
from PyQt6.QtCore import QLocale

_STRINGS: dict[str, dict[str, str]] = {
    "es": {
        "drop_hint": "Arrastra tus archivos aquí",
        "drop_sub": "O selecciónalos con el botón",
        "btn_select": "Seleccionar archivos…",
        "btn_convert": "Convertir todo →",
        "btn_cancel": "Cancelar",
        "btn_open_folder": "Abrir carpeta",
        "status_waiting": "En espera",
        "status_converting": "Convirtiendo",
        "status_done": "Listo",
        "status_error": "Error",
        "folder_label": "Salida:",
        "folder_change": "Cambiar…",
        "queue_clear": "Limpiar",
        "queue_header": "Archivos",
        "counter": "{done} / {total} listos",
        "window_title": "Markiti",
    },
    "en": {
        "drop_hint": "Drop your files here",
        "drop_sub": "Or select them with the button",
        "btn_select": "Select files…",
        "btn_convert": "Convert all →",
        "btn_cancel": "Cancel",
        "btn_open_folder": "Open folder",
        "status_waiting": "Waiting",
        "status_converting": "Converting",
        "status_done": "Done",
        "status_error": "Error",
        "folder_label": "Output:",
        "folder_change": "Change…",
        "queue_clear": "Clear",
        "queue_header": "Files",
        "counter": "{done} / {total} done",
        "window_title": "Markiti",
    },
}


def load_strings() -> dict[str, str]:
    lang = QLocale.system().name()[:2].lower()
    return _STRINGS.get(lang, _STRINGS["en"])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_i18n.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/i18n.py tests/test_i18n.py
git commit -m "feat: dict-based i18n with Spanish/English and locale fallback"
```

---

## Task 4: Queue model (pure Python, no Qt)

**Files:**
- Create: `src/queue_model.py`
- Create: `tests/test_queue_model.py`

**Interfaces:**
- Produces:
  - `FileStatus(Enum)`: `WAITING`, `CONVERTING`, `DONE`, `ERROR`
  - `FileItem(path: str)`: `.name → str`, `.size_label → str`, `.type_icon → str`, `.status: FileStatus`, `.error: str`
  - `FileQueueModel()`: `.add_files(paths: list[str]) → list[str]`, `.clear()`, `.set_status(path, status, error="")`, `.waiting_paths() → list[str]`, `.done_count() → int`, `.total() → int`, `.items() → list[FileItem]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_queue_model.py
from queue_model import FileQueueModel, FileStatus, FileItem

def test_add_files_returns_newly_added():
    m = FileQueueModel()
    added = m.add_files(["/a.pdf", "/b.docx"])
    assert added == ["/a.pdf", "/b.docx"]
    assert m.total() == 2

def test_add_files_skips_duplicates():
    m = FileQueueModel()
    m.add_files(["/a.pdf"])
    added = m.add_files(["/a.pdf", "/b.docx"])
    assert added == ["/b.docx"]
    assert m.total() == 2

def test_clear_empties_queue():
    m = FileQueueModel()
    m.add_files(["/a.pdf", "/b.pdf"])
    m.clear()
    assert m.total() == 0

def test_set_status_updates_item():
    m = FileQueueModel()
    m.add_files(["/a.pdf"])
    m.set_status("/a.pdf", FileStatus.DONE)
    assert m.items()[0].status == FileStatus.DONE

def test_set_status_stores_error():
    m = FileQueueModel()
    m.add_files(["/a.pdf"])
    m.set_status("/a.pdf", FileStatus.ERROR, error="Conversion failed")
    assert m.items()[0].error == "Conversion failed"

def test_waiting_paths_excludes_done():
    m = FileQueueModel()
    m.add_files(["/a.pdf", "/b.pdf"])
    m.set_status("/a.pdf", FileStatus.DONE)
    assert m.waiting_paths() == ["/b.pdf"]

def test_done_count():
    m = FileQueueModel()
    m.add_files(["/a.pdf", "/b.pdf", "/c.pdf"])
    m.set_status("/a.pdf", FileStatus.DONE)
    m.set_status("/b.pdf", FileStatus.DONE)
    assert m.done_count() == 2

def test_file_item_name():
    assert FileItem("/folder/document.pdf").name == "document.pdf"

def test_file_item_type_icons():
    assert FileItem("/x.pdf").type_icon == "📄"
    assert FileItem("/x.xlsx").type_icon == "📊"
    assert FileItem("/x.docx").type_icon == "📝"
    assert FileItem("/x.pptx").type_icon == "📋"
    assert FileItem("/x.html").type_icon == "🌐"
    assert FileItem("/x.unknown").type_icon == "📄"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_queue_model.py -v
```

Expected: `ImportError: No module named 'queue_model'`

- [ ] **Step 3: Write `src/queue_model.py`**

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileStatus(Enum):
    WAITING = "waiting"
    CONVERTING = "converting"
    DONE = "done"
    ERROR = "error"


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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_queue_model.py -v
```

Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add src/queue_model.py tests/test_queue_model.py
git commit -m "feat: FileQueueModel with status tracking, FileItem with type icons"
```

---

## Task 5: Converter QThread worker

**Files:**
- Create: `src/converter.py`
- Create: `tests/test_converter.py`

**Interfaces:**
- Consumes: `queue_model.FileStatus`
- Produces:
  - `ConvertWorker(files: list[str], output_dir: str, parent=None)`
  - Signals: `file_started(path: str)`, `file_finished(path: str, output_path: str)`, `file_error(path: str, error: str)`, `all_done()`
  - Methods: `.cancel() → None`, `.run() → None` (called by QThread, also usable synchronously in tests)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_converter.py
from pathlib import Path

def test_converts_text_file(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "output"
    worker = ConvertWorker([tmp_txt], str(out_dir))

    finished = []
    worker.file_finished.connect(lambda p, out: finished.append(out))
    worker.run()

    assert len(finished) == 1
    out_file = Path(finished[0])
    assert out_file.exists()
    assert out_file.suffix == ".md"
    assert out_file.stem == "sample"

def test_converts_html_file(qapp, tmp_html, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "output"
    worker = ConvertWorker([tmp_html], str(out_dir))

    finished = []
    worker.file_finished.connect(lambda p, out: finished.append(out))
    worker.run()

    assert len(finished) == 1
    content = Path(finished[0]).read_text(encoding="utf-8")
    assert "Hello" in content

def test_emits_error_on_missing_file(qapp, tmp_path):
    from converter import ConvertWorker
    worker = ConvertWorker(["/nonexistent/file.xyz"], str(tmp_path / "out"))

    errors = []
    worker.file_error.connect(lambda p, e: errors.append((p, e)))
    worker.run()

    assert len(errors) == 1
    assert "nonexistent" in errors[0][0]

def test_cancel_before_run_skips_all(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    worker = ConvertWorker([tmp_txt], str(tmp_path / "out"))
    worker.cancel()

    started = []
    worker.file_started.connect(lambda p: started.append(p))
    worker.run()

    assert len(started) == 0

def test_creates_output_dir_if_missing(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "deep" / "nested" / "output"
    assert not out_dir.exists()
    worker = ConvertWorker([tmp_txt], str(out_dir))
    worker.run()
    assert out_dir.exists()

def test_overwrites_existing_md(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    existing = out_dir / "sample.md"
    existing.write_text("OLD CONTENT", encoding="utf-8")

    worker = ConvertWorker([tmp_txt], str(out_dir))
    worker.run()

    assert existing.read_text(encoding="utf-8") != "OLD CONTENT"

def test_all_done_emitted(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    done_called = []
    worker = ConvertWorker([tmp_txt], str(tmp_path / "out"))
    worker.all_done.connect(lambda: done_called.append(True))
    worker.run()
    assert done_called == [True]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_converter.py -v
```

Expected: `ImportError: No module named 'converter'`

- [ ] **Step 3: Write `src/converter.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_converter.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add src/converter.py tests/test_converter.py
git commit -m "feat: ConvertWorker QThread with cancel, error handling, and output dir creation"
```

---

## Task 6: Drop zone widget

**Files:**
- Create: `src/drop_zone.py`

**Interfaces:**
- Consumes: `strings: dict` (keys: `drop_hint`, `drop_sub`, `btn_select`)
- Produces: `DropZone(strings, parent=None)`, signal `files_dropped(list[str])`

- [ ] **Step 1: Write smoke test**

```python
# tests/test_drop_zone.py
def test_drop_zone_smoke(qapp):
    from drop_zone import DropZone
    strings = {
        "drop_hint": "Drop here", "drop_sub": "or select",
        "btn_select": "Select files…",
    }
    w = DropZone(strings)
    w.show()
    assert w.isVisible()
    w.close()

def test_files_dropped_signal(qapp, tmp_txt):
    from drop_zone import DropZone
    strings = {
        "drop_hint": "Drop here", "drop_sub": "or select",
        "btn_select": "Select files…",
    }
    w = DropZone(strings)
    received = []
    w.files_dropped.connect(lambda paths: received.extend(paths))
    w._emit_files([tmp_txt])
    assert received == [tmp_txt]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_drop_zone.py -v
```

Expected: `ImportError: No module named 'drop_zone'`

- [ ] **Step 3: Write `src/drop_zone.py`**

```python
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


class DropZone(QWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, strings: dict, parent=None):
        super().__init__(parent)
        self._strings = strings
        self._pulse = 0.0
        self._drag_active = False
        self.setAcceptDrops(True)
        self.setStyleSheet("background: #fafafa;")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.addStretch()

        icon = QLabel("🗂️")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 38px; background: transparent;")
        layout.addWidget(icon)

        hint = QLabel(self._strings["drop_hint"])
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #1d1d1f; background: transparent;"
        )
        layout.addWidget(hint)

        sub = QLabel(self._strings["drop_sub"])
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 12px; color: #8e8e93; background: transparent;")
        layout.addWidget(sub)

        formats = QLabel("PDF · Word · Excel · PowerPoint · HTML · +más")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formats.setWordWrap(True)
        formats.setStyleSheet(
            "font-size: 11px; color: #aeaeb2; background: transparent; margin-top: 4px;"
        )
        layout.addWidget(formats)

        layout.addStretch()

        btn = QPushButton(self._strings["btn_select"])
        btn.setFixedHeight(38)
        btn.setStyleSheet("""
            QPushButton {
                background: #007aff; color: white; border: none;
                border-radius: 10px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: #0066d6; }
            QPushButton:pressed { background: #0055b3; }
        """)
        btn.clicked.connect(self._open_dialog)
        layout.addWidget(btn)

    def _emit_files(self, paths: list[str]) -> None:
        self.files_dropped.emit(paths)

    def _tick(self):
        self._pulse = (math.sin(time.monotonic() * 2.0) + 1.0) / 2.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, (self.height() - 58) / 2
        radius = 80 + self._pulse * 30
        alpha = int(12 + self._pulse * 18)
        grad = QRadialGradient(QPointF(cx, cy), radius)
        grad.setColorAt(0, QColor(0, 122, 255, alpha))
        grad.setColorAt(1, QColor(0, 122, 255, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        rect = self.rect().adjusted(20, 20, -20, -68)
        color = "#007aff" if self._drag_active else "#c7c7cc"
        pen = QPen(QColor(color), 1.5, Qt.PenStyle.DashLine)
        pen.setDashPattern([6, 4])
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 16, 16)

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_drop_zone.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Visual smoke test** — run this and confirm the drop zone renders with animated blob and dashed border:

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from PyQt6.QtWidgets import QApplication
from drop_zone import DropZone
app = QApplication(sys.argv)
w = DropZone({'drop_hint': 'Drop here', 'drop_sub': 'or select', 'btn_select': 'Select…'})
w.resize(300, 400)
w.show()
app.exec()
"
```

Expected: window with pulsing blue blob, dashed border, emoji icon, and blue button.

- [ ] **Step 6: Commit**

```bash
git add src/drop_zone.py tests/test_drop_zone.py
git commit -m "feat: DropZone widget with animated blob, drag & drop, and file dialog"
```

---

## Task 7: Queue widget (right panel)

**Files:**
- Create: `src/queue_widget.py`

**Interfaces:**
- Consumes: `FileQueueModel`, `strings: dict` (keys: `queue_header`, `queue_clear`, `status_*`)
- Produces:
  - `QueueWidget(model, strings, parent=None)`
  - `.add_files(paths: list[str]) → None`
  - `.update_status(path: str, status: FileStatus, error: str = "") → None`
  - `.waiting_paths() → list[str]`

- [ ] **Step 1: Write smoke tests**

```python
# tests/test_queue_widget.py
import pytest

STRINGS = {
    "queue_header": "Files", "queue_clear": "Clear",
    "status_waiting": "Waiting", "status_converting": "Converting",
    "status_done": "Done", "status_error": "Error",
}

def test_add_files_shows_rows(qapp, tmp_txt):
    from queue_model import FileQueueModel
    from queue_widget import QueueWidget
    m = FileQueueModel()
    w = QueueWidget(m, STRINGS)
    w.add_files([tmp_txt])
    assert m.total() == 1

def test_update_status_done(qapp, tmp_txt):
    from queue_model import FileQueueModel, FileStatus
    from queue_widget import QueueWidget
    m = FileQueueModel()
    w = QueueWidget(m, STRINGS)
    w.add_files([tmp_txt])
    w.update_status(tmp_txt, FileStatus.DONE)
    assert m.items()[0].status == FileStatus.DONE

def test_waiting_paths_after_done(qapp, tmp_txt):
    from queue_model import FileQueueModel, FileStatus
    from queue_widget import QueueWidget
    m = FileQueueModel()
    w = QueueWidget(m, STRINGS)
    w.add_files([tmp_txt])
    w.update_status(tmp_txt, FileStatus.DONE)
    assert w.waiting_paths() == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_queue_widget.py -v
```

Expected: `ImportError: No module named 'queue_widget'`

- [ ] **Step 3: Write `src/queue_widget.py`**

```python
import time
import math
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton,
)
from queue_model import FileQueueModel, FileStatus, FileItem


class FileRow(QFrame):
    def __init__(self, item: FileItem, strings: dict, parent=None):
        super().__init__(parent)
        self._item = item
        self._strings = strings
        self._progress_x = 0.0
        self.setFixedHeight(52)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self._icon_lbl = QLabel(item.type_icon)
        self._icon_lbl.setFixedWidth(26)
        self._icon_lbl.setStyleSheet("font-size: 20px;")
        layout.addWidget(self._icon_lbl)

        info = QVBoxLayout()
        info.setSpacing(1)
        name = QLabel(item.name)
        name.setStyleSheet("font-size: 12px; font-weight: 500; color: #1d1d1f;")
        size = QLabel(item.size_label)
        size.setStyleSheet("font-size: 10px; color: #8e8e93;")
        info.addWidget(name)
        info.addWidget(size)
        layout.addLayout(info, stretch=1)

        self._status_lbl = QLabel()
        self._status_lbl.setFixedWidth(100)
        self._status_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._status_lbl)

        self.refresh()

    def refresh(self):
        s = self._item.status
        if s == FileStatus.WAITING:
            self._status_lbl.setText(f"— {self._strings['status_waiting']}")
            self._status_lbl.setStyleSheet("font-size: 11px; color: #c7c7cc;")
            self.setStyleSheet("QFrame{background:white;border-bottom:1px solid #f5f5f5;}")
            self._timer.stop()
        elif s == FileStatus.CONVERTING:
            self._status_lbl.setText(f"⏳ {self._strings['status_converting']}")
            self._status_lbl.setStyleSheet("font-size:11px;color:#007aff;font-weight:600;")
            self.setStyleSheet("QFrame{background:#f0f7ff;border-bottom:1px solid #f5f5f5;}")
            self._timer.start(16)
        elif s == FileStatus.DONE:
            self._status_lbl.setText(f"✓ {self._strings['status_done']}")
            self._status_lbl.setStyleSheet("font-size:11px;color:#34c759;font-weight:600;")
            self.setStyleSheet("QFrame{background:white;border-bottom:1px solid #f5f5f5;}")
            self._timer.stop()
        elif s == FileStatus.ERROR:
            self._status_lbl.setText(f"✗ {self._strings['status_error']}")
            self._status_lbl.setStyleSheet("font-size:11px;color:#ff3b30;font-weight:600;")
            self.setStyleSheet("QFrame{background:#fff5f5;border-bottom:1px solid #f5f5f5;}")
            if self._item.error:
                self._status_lbl.setToolTip(self._item.error)
            self._timer.stop()

    def _tick(self):
        self._progress_x = (self._progress_x + 4) % (self.width() + 100)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._item.status != FileStatus.CONVERTING:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() - 2
        w = 100
        x = int(self._progress_x) - w
        grad = QLinearGradient(x, y, x + w, y)
        grad.setColorAt(0, QColor(0, 122, 255, 0))
        grad.setColorAt(0.5, QColor(0, 122, 255, 200))
        grad.setColorAt(1, QColor(0, 122, 255, 0))
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
        header.setContentsMargins(12, 10, 12, 8)
        self._header_lbl = QLabel(self._strings["queue_header"].upper())
        self._header_lbl.setStyleSheet(
            "font-size:11px;font-weight:700;color:#1d1d1f;letter-spacing:1px;"
        )
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("font-size:11px;color:#8e8e93;")
        clear = QPushButton(self._strings["queue_clear"])
        clear.setFlat(True)
        clear.setStyleSheet(
            "font-size:11px;color:#007aff;border:none;background:transparent;padding:0;"
        )
        clear.clicked.connect(self._on_clear)
        header.addWidget(self._header_lbl)
        header.addWidget(self._count_lbl)
        header.addStretch()
        header.addWidget(clear)
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#f0f0f0;")
        layout.addWidget(sep)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
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
        self._count_lbl.setText(f"  {n} en cola" if n else "")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_queue_widget.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add src/queue_widget.py tests/test_queue_widget.py
git commit -m "feat: QueueWidget with FileRow status display and animated progress bar"
```

---

## Task 8: Main window assembly

**Files:**
- Create: `src/window.py`
- Create: `src/main.py`

**Interfaces:**
- Consumes: `AppSettings`, `load_strings`, `DropZone`, `QueueWidget`, `FileQueueModel`, `ConvertWorker`, `FileStatus`
- Produces: `MainWindow(QMainWindow)`, `main() → None`

- [ ] **Step 1: Write smoke test**

```python
# tests/test_window.py
def test_main_window_opens(qapp):
    from window import MainWindow
    w = MainWindow()
    w.show()
    assert w.isVisible()
    assert w.width() == 640
    assert w.height() == 460
    w.close()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_window.py -v
```

Expected: `ImportError: No module named 'window'`

- [ ] **Step 3: Write `src/window.py`**

```python
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
```

- [ ] **Step 4: Write `src/main.py`**

```python
import sys
from PyQt6.QtWidgets import QApplication
from window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Markiti")
    app.setOrganizationName("Markiti")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests pass. No new failures.

- [ ] **Step 6: Manual end-to-end smoke test**

```bash
cd /path/to/Markiti
source .venv/bin/activate
PYTHONPATH=src python3 src/main.py
```

Verify:
1. Window opens at 640×460
2. Animated blob pulses in left panel
3. Drag a PDF onto the window → file appears in queue as "En espera"
4. Click "Convertir todo →" → status changes to "⏳ Convirtiendo", then "✓ Listo"
5. Counter shows "1 / 1 listos"
6. Click "Abrir carpeta" → Finder opens showing the `.md` file
7. Click "Cambiar…" → folder picker dialog opens

- [ ] **Step 7: Commit**

```bash
git add src/window.py src/main.py tests/test_window.py
git commit -m "feat: MainWindow assembly with full signal wiring and end-to-end flow"
```

---

## Task 9: Build script (.app)

**Files:**
- Create: `build.sh`

- [ ] **Step 1: Write `build.sh`**

```bash
#!/usr/bin/env bash
set -e

echo "==> Activating venv"
source .venv/bin/activate

echo "==> Installing PyInstaller"
pip install -q pyinstaller

echo "==> Building Markiti.app"
pyinstaller \
    --windowed \
    --onedir \
    --name "Markiti" \
    --paths src \
    --hidden-import markitdown \
    --hidden-import markitdown._base_converter \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.QtGui \
    --collect-all markitdown \
    --noconfirm \
    src/main.py

echo ""
echo "==> Done! App built at: dist/Markiti.app"
echo "==> To install: cp -r dist/Markiti.app /Applications/"
echo "==> First run: right-click → Open (Gatekeeper bypass, one time only)"
```

- [ ] **Step 2: Make executable and run**

```bash
chmod +x build.sh
./build.sh
```

Expected output ends with:
```
==> Done! App built at: dist/Markiti.app
```

- [ ] **Step 3: Verify the .app opens**

```bash
open dist/Markiti.app
```

Expected: app window opens with full UI, no terminal window.

- [ ] **Step 4: Test Gatekeeper bypass flow (simulate fresh install)**

```bash
cp -r dist/Markiti.app ~/Desktop/Markiti.app
# Double-click on Desktop → blocked by Gatekeeper
# Right-click → Open → Open → app launches normally
```

- [ ] **Step 5: Commit**

```bash
git add build.sh
git commit -m "feat: PyInstaller build script generating Markiti.app"
```

---

## Self-Review

**Spec coverage:**
- ✅ Drop zone with animated blob, dashed border, emoji icon, format tags
- ✅ Drag & drop files onto window
- ✅ File selector button with multi-select and format filter
- ✅ File queue with per-file status (waiting/converting/done/error)
- ✅ Animated progress bar per converting file
- ✅ Output folder configurable + persisted via QSettings
- ✅ "Convertir todo" → changes to "Cancelar" during conversion
- ✅ "Abrir carpeta" opens Finder
- ✅ Locale detection (Spanish/English, fallback to English)
- ✅ QThread for non-blocking conversion
- ✅ App stays open after conversion
- ✅ Duplicates silently ignored
- ✅ Existing .md overwritten silently
- ✅ PyInstaller `.app` build script

**No placeholders found.**

**Type consistency verified:** `FileStatus` used consistently across `queue_model`, `queue_widget`, `window`, and `converter`.
