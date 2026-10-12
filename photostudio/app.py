"""QApplication bootstrap."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import __app_name__, __version__
from .ui.main_window import MainWindow

ICON_PATH = Path(__file__).resolve().parent / "resources" / "icon.ico"


def main() -> int:
    if "--smoke-test" in sys.argv:
        from .smoke import main as smoke_main
        return smoke_main()
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("PhotoStudio")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
