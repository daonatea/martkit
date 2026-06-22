from pathlib import Path
from PyQt6.QtCore import QSettings

def test_default_output_folder(qapp, tmp_path):
    from settings import AppSettings
    qs = QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    s = AppSettings(qsettings=qs)
    assert s.output_folder() == str(Path.home() / "Documents" / "markIT")

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
