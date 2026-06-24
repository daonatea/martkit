import platform
import sys


def _check_arch() -> bool:
    """En macOS, muestra aviso si no es Apple Silicon y retorna False."""
    if platform.system() != "Darwin":
        return True

    machine = platform.machine()
    if machine == "arm64":
        return True

    from PyQt6.QtWidgets import QApplication, QMessageBox
    app = QApplication(sys.argv)
    dlg = QMessageBox()
    dlg.setWindowTitle("markIT — Equipo incompatible")
    dlg.setIcon(QMessageBox.Icon.Critical)
    dlg.setText(
        "<b>markIT no puede ejecutarse en este Mac.</b>"
    )
    dlg.setInformativeText(
        f"Esta versión fue compilada exclusivamente para Mac con Apple Silicon (M1/M2/M3/M4).\n\n"
        f"Tu equipo tiene arquitectura: <b>{machine}</b> (Intel).\n\n"
        "Solicita al desarrollador una versión compatible con Intel."
    )
    dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
    dlg.exec()
    return False


def main():
    if not _check_arch():
        sys.exit(1)

    if platform.system() == "Darwin":
        try:
            import AppKit
            AppKit.NSApplication.sharedApplication()
        except ImportError:
            pass

    from PyQt6.QtWidgets import QApplication
    from window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("markIT")
    app.setOrganizationName("markIT")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
