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
from gui.theme import (
    BG_PANEL, HEADER_STYLE, PANEL_TITLE_STYLE, INPUT_STYLE,
    DIVIDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
)

logger = logging.getLogger(__name__)


class PathRow(QWidget):
    changed = Signal(str)

    def __init__(self, label: str, icon: str, default: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(f"{icon}  {label}")
        lbl.setFixedWidth(80)
        lbl.setFont(QFont("Arial", 12))
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(lbl)

        self._edit = QLineEdit(default)
        self._edit.setStyleSheet(INPUT_STYLE)
        self._edit.textChanged.connect(self.changed)
        layout.addWidget(self._edit, stretch=1)

        browse = QPushButton("…")
        browse.setFixedSize(32, 32)
        browse.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #f0f0f0, stop:1 #d8d8d8);
                border: 1px solid #b0b0b0; border-radius: 6px;
                color: #555; font-size: 16px;
            }}
            QPushButton:hover {{ background: #e0e0e0; color: #111; }}
        """)
        browse.clicked.connect(self._browse)
        layout.addWidget(browse)

    def _browse(self):
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

        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(HEADER_STYLE)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)
        title = QLabel("DESTINATION")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet(PANEL_TITLE_STYLE)
        h_layout.addWidget(title)
        layout.addWidget(header)

        body = QWidget()
        body.setStyleSheet(f"background: {BG_PANEL};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(16)

        drive_label = QLabel("External Drive")
        drive_label.setFont(QFont("Arial", 11, QFont.Bold))
        drive_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        body_layout.addWidget(drive_label)

        self._photo_row = PathRow("Photos", "📷")
        self._photo_row.changed.connect(self._emit_config)
        body_layout.addWidget(self._photo_row)

        self._video_row = PathRow("Videos", "🎬")
        self._video_row.changed.connect(self._emit_config)
        body_layout.addWidget(self._video_row)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"color: {DIVIDER};")
        body_layout.addWidget(div)

        preview_label = QLabel("Folder structure:")
        preview_label.setFont(QFont("Arial", 11, QFont.Bold))
        preview_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        body_layout.addWidget(preview_label)

        self._preview = QLabel(self._structure_text())
        self._preview.setFont(QFont("Menlo, Courier", 11))
        self._preview.setStyleSheet(f"color: {TEXT_MUTED}; line-height: 1.6;")
        self._preview.setWordWrap(True)
        body_layout.addWidget(self._preview)

        body_layout.addStretch()
        layout.addWidget(body, stretch=1)

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
