"""
Source Panel — shows connected drives in two sections:
  • Camera Cards  — SD cards / camera storage (scan source)
  • Storage Drives — external HDDs/SSDs (import destination)
"""

from __future__ import annotations
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont

from backend.utils.detector import list_drives, DriveInfo

logger = logging.getLogger(__name__)


class DriveCard(QFrame):
    """A single drive card showing label, size, type."""

    clicked = Signal(object)  # emits DriveInfo

    def __init__(self, drive: DriveInfo, parent=None):
        super().__init__(parent)
        self.drive = drive
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(72)
        self._build()
        self._apply_style(selected=False)

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        icon = QLabel("💾" if self.drive.is_camera_card else "💽")
        icon.setFont(QFont("Arial", 20))
        icon.setFixedWidth(36)
        layout.addWidget(icon)

        text = QVBoxLayout()
        text.setSpacing(2)

        name = QLabel(self.drive.label)
        name.setFont(QFont("Arial", 13, QFont.Bold))

        kind = "SD Card" if self.drive.is_camera_card else "External Drive"
        detail = QLabel(f"{kind}  ·  {self.drive.total_gb} GB  ·  {self.drive.filesystem}")
        detail.setFont(QFont("Arial", 11))
        detail.setStyleSheet("color: #888;")

        text.addWidget(name)
        text.addWidget(detail)
        layout.addLayout(text)
        layout.addStretch()

        free = QLabel(f"{self.drive.free_gb} GB\nfree")
        free.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        free.setFont(QFont("Arial", 11))
        free.setStyleSheet("color: #aaa;")
        layout.addWidget(free)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)

    def _apply_style(self, selected: bool):
        if selected:
            self.setStyleSheet("""
                DriveCard {
                    background: #1e3a5f;
                    border: 2px solid #4a9eff;
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                DriveCard {
                    background: #2a2a2a;
                    border: 1px solid #3a3a3a;
                    border-radius: 10px;
                }
                DriveCard:hover {
                    border: 1px solid #555;
                    background: #303030;
                }
            """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.drive)


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Arial", 10, QFont.Bold))
    lbl.setStyleSheet("color: #555; letter-spacing: 1px; padding: 8px 0 4px 0;")
    return lbl


def _empty_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("color: #444; font-size: 12px; padding: 8px 0;")
    lbl.setWordWrap(True)
    return lbl


class SourcePanel(QWidget):
    """
    Left panel — lists connected drives in two sections.
    Emits drive_selected for any click; callers check drive.is_camera_card.
    """

    drive_selected = Signal(object)  # DriveInfo

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)
        self._all_cards: list[DriveCard] = []
        self._selected_drive: DriveInfo | None = None
        self._build()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(3000)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #333;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 12, 0)

        title = QLabel("DRIVES")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet("color: #888; letter-spacing: 1px;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setStyleSheet("""
            QPushButton { background: #333; border: none; border-radius: 14px;
                          color: #aaa; font-size: 16px; }
            QPushButton:hover { background: #444; color: white; }
        """)
        refresh_btn.clicked.connect(self.refresh)
        h_layout.addWidget(refresh_btn)
        root.addWidget(header)

        # ── Scrollable body ───────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #1a1a1a; border: none; }")

        body = QWidget()
        body.setStyleSheet("background: #1a1a1a;")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(12, 8, 12, 12)
        self._body_layout.setSpacing(0)
        self._body_layout.addStretch()

        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        self.refresh()

    def refresh(self):
        """Re-scan drives and rebuild both sections."""
        drives = list_drives()
        logger.debug("Drive refresh: %d drives found", len(drives))

        cards = [d for d in drives if d.is_camera_card]
        storage = [d for d in drives if d.is_external_drive]

        # Clear existing widgets (everything except the trailing stretch)
        while self._body_layout.count() > 1:
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._all_cards.clear()
        insert_at = 0

        # ── Camera Cards section ──────────────────────────────────────────
        self._body_layout.insertWidget(insert_at, _section_label("CAMERA CARDS"))
        insert_at += 1

        if cards:
            for drive in cards:
                card = self._make_card(drive)
                self._body_layout.insertWidget(insert_at, card)
                insert_at += 1
        else:
            self._body_layout.insertWidget(insert_at, _empty_label("No camera card detected"))
            insert_at += 1

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color: #2a2a2a; margin: 8px 0;")
        self._body_layout.insertWidget(insert_at, div)
        insert_at += 1

        # ── Storage Drives section ────────────────────────────────────────
        self._body_layout.insertWidget(insert_at, _section_label("STORAGE DRIVES"))
        insert_at += 1

        if storage:
            for drive in storage:
                card = self._make_card(drive)
                self._body_layout.insertWidget(insert_at, card)
                insert_at += 1
        else:
            self._body_layout.insertWidget(insert_at, _empty_label("No external drive detected"))
            insert_at += 1

    def _make_card(self, drive: DriveInfo) -> DriveCard:
        card = DriveCard(drive)
        card.clicked.connect(self._on_card_clicked)
        self._all_cards.append(card)
        if self._selected_drive and drive.unique_id == self._selected_drive.unique_id:
            card.set_selected(True)
        return card

    def _on_card_clicked(self, drive: DriveInfo):
        logger.info("User selected drive: %s (%s)", drive.label, drive.mount_point)
        self._selected_drive = drive
        for card in self._all_cards:
            card.set_selected(card.drive.unique_id == drive.unique_id)
        self.drive_selected.emit(drive)

    def selected_drive(self) -> DriveInfo | None:
        return self._selected_drive
