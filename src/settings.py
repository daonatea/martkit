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
