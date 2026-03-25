"""
Media Mporter — entry point.
Run: python3 main.py
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from backend.utils.log_setup import setup as setup_logging, get_log_path


def main():
    setup_logging(level="DEBUG")

    import logging
    logging.getLogger(__name__).info("Media Mporter starting up")

    app = QApplication(sys.argv)
    app.setApplicationName("Media Mporter")
    app.setStyle("Fusion")

    # Dark palette
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import Qt
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor("#1a1a1a"))
    palette.setColor(QPalette.WindowText,      QColor("#eeeeee"))
    palette.setColor(QPalette.Base,            QColor("#1e1e1e"))
    palette.setColor(QPalette.AlternateBase,   QColor("#222222"))
    palette.setColor(QPalette.Text,            QColor("#dddddd"))
    palette.setColor(QPalette.Button,          QColor("#2a2a2a"))
    palette.setColor(QPalette.ButtonText,      QColor("#dddddd"))
    palette.setColor(QPalette.Highlight,       QColor("#4a9eff"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipBase,     QColor("#2a2a2a"))
    palette.setColor(QPalette.ToolTipText,     QColor("#dddddd"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
