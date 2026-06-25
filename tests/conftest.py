import sys
import platform
from pathlib import Path
import pytest

# macOS 26 Tahoe requires explicit NSApplication registration before Qt
# initializes its cocoa platform plugin; without this, QApplication aborts.
if platform.system() == "Darwin":
    try:
        import AppKit
        AppKit.NSApplication.sharedApplication()
    except ImportError:
        pass

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
