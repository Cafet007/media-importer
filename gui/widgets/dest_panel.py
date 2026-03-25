"""
Destination Panel — lets user set photo_base and video_base paths.
"""

from __future__ import annotations
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QFrame
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from pathlib import Path

from backend.core.rules import DestinationConfig
from gui.theme import T

logger = logging.getLogger(__name__)


class PathRow(QWidget):
    changed = Signal(str)

    def __init__(self, label: str, icon: str, default: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._lbl = QLabel(f"{icon}  {label}")
        self._lbl.setFixedWidth(80)
        self._lbl.setFont(QFont("Arial", 12))
        layout.addWidget(self._lbl)

        self._edit = QLineEdit(default)
        self._edit.textChanged.connect(self.changed)
        layout.addWidget(self._edit, stretch=1)

        self._browse = QPushButton("…")
        self._browse.setFixedSize(32, 32)
        self._browse.clicked.connect(self._browse_dir)
        layout.addWidget(self._browse)

        self.apply_theme()

    def apply_theme(self):
        self._lbl.setStyleSheet(f"color: {T.TEXT_SECONDARY};")
        self._edit.setStyleSheet(T.INPUT_STYLE)
        if T.dark:
            self._browse.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #3a3a3c, stop:1 #2c2c2e);
                    border: 1px solid #48484a; border-radius: 6px;
                    color: #f0f0f0; font-size: 16px;
                }
                QPushButton:hover { background: #48484a; }
            """)
        else:
            self._browse.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #f0f0f0, stop:1 #d8d8d8);
                    border: 1px solid #b0b0b0; border-radius: 6px;
                    color: #555; font-size: 16px;
                }
                QPushButton:hover { background: #e0e0e0; color: #111; }
            """)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder", self._edit.text())
        if path:
            self._edit.setText(path)

    def path(self) -> Path:
        return Path(self._edit.text())

    def set_path(self, path: str):
        self._edit.setText(path)


class DestPanel(QWidget):
    config_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header_widget = QWidget()
        self._header_widget.setFixedHeight(52)
        h_layout = QHBoxLayout(self._header_widget)
        h_layout.setContentsMargins(16, 0, 16, 0)
        self._title_lbl = QLabel("DESTINATION")
        self._title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        h_layout.addWidget(self._title_lbl)
        layout.addWidget(self._header_widget)

        self._body = QWidget()
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(16)

        self._drive_label = QLabel("External Drive")
        self._drive_label.setFont(QFont("Arial", 11, QFont.Bold))
        body_layout.addWidget(self._drive_label)

        self._photo_row = PathRow("Photos", "📷")
        self._photo_row.changed.connect(self._emit_config)
        body_layout.addWidget(self._photo_row)

        self._video_row = PathRow("Videos", "🎬")
        self._video_row.changed.connect(self._emit_config)
        body_layout.addWidget(self._video_row)

        self._div = QFrame()
        self._div.setFrameShape(QFrame.HLine)
        body_layout.addWidget(self._div)

        self._preview_label = QLabel("Folder structure:")
        self._preview_label.setFont(QFont("Arial", 11, QFont.Bold))
        body_layout.addWidget(self._preview_label)

        self._preview = QLabel(self._structure_text())
        self._preview.setFont(QFont("Menlo, Courier", 11))
        self._preview.setWordWrap(True)
        body_layout.addWidget(self._preview)

        body_layout.addStretch()
        layout.addWidget(self._body, stretch=1)

        self.apply_theme()

    def apply_theme(self):
        self._header_widget.setStyleSheet(T.HEADER_STYLE)
        self._title_lbl.setStyleSheet(T.PANEL_TITLE_STYLE)
        self._body.setStyleSheet(f"background: {T.BG_PANEL};")
        self._drive_label.setStyleSheet(f"color: {T.TEXT_PRIMARY};")
        self._div.setStyleSheet(f"color: {T.DIVIDER};")
        self._preview_label.setStyleSheet(f"color: {T.TEXT_PRIMARY};")
        self._preview.setStyleSheet(f"color: {T.TEXT_MUTED}; line-height: 1.6;")
        self._photo_row.apply_theme()
        self._video_row.apply_theme()

    def _structure_text(self) -> str:
        return (
            "Photos/\n"
            "  RAW/\n"
            "    2026-03-24/\n"
            "  JPG/\n"
            "    2026-03-24/\n\n"
            "Footage/\n"
            "  2026-03-24/"
        )

    def set_paths(self, photo: str, video: str):
        self._photo_row.set_path(photo)
        self._video_row.set_path(video)
        self._emit_config()

    def set_drive_root(self, root: Path):
        logger.info("Destination auto-filled from drive root: %s", root)
        self._photo_row.set_path(str(root / "Photography"))
        self._video_row.set_path(str(root / "Footage"))
        self._emit_config()

    def _emit_config(self, *_):
        self._preview.setText(self._structure_text())
        self.config_changed.emit(self.config())

    def config(self) -> DestinationConfig:
        return DestinationConfig(
            photo_base=self._photo_row.path(),
            video_base=self._video_row.path(),
        )
