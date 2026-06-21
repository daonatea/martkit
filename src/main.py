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
