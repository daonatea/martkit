import platform
import sys


def main():
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
