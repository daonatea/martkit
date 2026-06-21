import sys
from pathlib import Path
import pytest
from PyQt6.QtCore import QCoreApplication

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture(scope="session")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
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
