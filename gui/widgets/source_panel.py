"""
Source Panel — shows connected drives in two sections:
  • Camera Cards  — SD cards / camera storage (scan source)
  • Storage Drives — external HDDs/SSDs (import destination)
"""

from __future__ import annotations
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont

from backend.utils.detector import list_drives, DriveInfo
from gui.theme import (
    BG_PANEL, BG_CARD, BG_CARD_SEL, BORDER_CARD, BORDER_CARD_SEL,
    DIVIDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    HEADER_STYLE, PANEL_TITLE_STYLE, btn_secondary,
)

logger = logging.getLogger(__name__)


class DriveCard(QFrame):
    clicked = Signal(object)

    def __init__(self, drive: DriveInfo, parent=None):
        super().__init__(parent)
        self.drive = drive
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(72)
        self._build()
        self._apply_style(False)

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
        name.setStyleSheet(f"color: {TEXT_PRIMARY};")

        kind = "SD Card" if self.drive.is_camera_card else "External Drive"
        detail = QLabel(f"{kind}  ·  {self.drive.total_gb} GB  ·  {self.drive.filesystem}")
        detail.setFont(QFont("Arial", 11))
        detail.setStyleSheet(f"color: {TEXT_SECONDARY};")

        text.addWidget(name)
        text.addWidget(detail)
        layout.addLayout(text)
        layout.addStretch()

        free = QLabel(f"{self.drive.free_gb} GB\nfree")
        free.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        free.setFont(QFont("Arial", 11))
        free.setStyleSheet(f"color: {TEXT_MUTED};")
        layout.addWidget(free)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)

    def _apply_style(self, selected: bool):
        if selected:
            self.setStyleSheet(f"""
                DriveCard {{
                    background: {BG_CARD_SEL};
                    border: 2px solid {BORDER_CARD_SEL};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                DriveCard {{
                    background: {BG_CARD};
                    border: 1px solid {BORDER_CARD};
                    border-radius: 10px;
                }}
                DriveCard:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #fafafa, stop:1 #eeeeee);
                    border: 1px solid #aaaaaa;
                }}
            """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.drive)


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Arial", 10, QFont.Bold))
    lbl.setStyleSheet(f"color: {TEXT_MUTED}; letter-spacing: 1px; padding: 8px 0 4px 0;")
    return lbl


def _empty_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 8px 0;")
    lbl.setWordWrap(True)
    return lbl


class SourcePanel(QWidget):
    drive_selected = Signal(object)

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

        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(HEADER_STYLE)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 12, 0)

        title = QLabel("DRIVES")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet(PANEL_TITLE_STYLE)
        h_layout.addWidget(title)
        h_layout.addStretch()

        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #f0f0f0, stop:1 #d8d8d8);
                border: 1px solid #b0b0b0; border-radius: 14px;
                color: #555; font-size: 16px;
            }}
            QPushButton:hover {{ background: #e8e8e8; color: #222; }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        h_layout.addWidget(refresh_btn)
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {BG_PANEL}; border: none; }}")

        body = QWidget()
        body.setStyleSheet(f"background: {BG_PANEL};")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(12, 8, 12, 12)
        self._body_layout.setSpacing(0)
        self._body_layout.addStretch()

        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        self.refresh()

    def refresh(self):
        drives = list_drives()
        cards   = [d for d in drives if d.is_camera_card]
        storage = [d for d in drives if d.is_external_drive]

        while self._body_layout.count() > 1:
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._all_cards.clear()
        idx = 0

        self._body_layout.insertWidget(idx, _section_label("CAMERA CARDS")); idx += 1
        if cards:
            for d in cards:
                self._body_layout.insertWidget(idx, self._make_card(d)); idx += 1
        else:
            self._body_layout.insertWidget(idx, _empty_label("No camera card detected")); idx += 1

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"color: {DIVIDER}; margin: 8px 0;")
        self._body_layout.insertWidget(idx, div); idx += 1

        self._body_layout.insertWidget(idx, _section_label("STORAGE DRIVES")); idx += 1
        if storage:
            for d in storage:
                self._body_layout.insertWidget(idx, self._make_card(d)); idx += 1
        else:
            self._body_layout.insertWidget(idx, _empty_label("No external drive detected")); idx += 1

    def _make_card(self, drive: DriveInfo) -> DriveCard:
        card = DriveCard(drive)
        card.clicked.connect(self._on_card_clicked)
        self._all_cards.append(card)
        if self._selected_drive and drive.unique_id == self._selected_drive.unique_id:
            card.set_selected(True)
        return card

    def _on_card_clicked(self, drive: DriveInfo):
        self._selected_drive = drive
        for card in self._all_cards:
            card.set_selected(card.drive.unique_id == drive.unique_id)
        self.drive_selected.emit(drive)

    def selected_drive(self) -> DriveInfo | None:
        return self._selected_drive
