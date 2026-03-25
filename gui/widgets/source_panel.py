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
from gui.theme import T

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

        self._name_lbl = QLabel(self.drive.label)
        self._name_lbl.setFont(QFont("Arial", 13, QFont.Bold))

        kind = "SD Card" if self.drive.is_camera_card else "External Drive"
        self._detail_lbl = QLabel(f"{kind}  ·  {self.drive.total_gb} GB  ·  {self.drive.filesystem}")
        self._detail_lbl.setFont(QFont("Arial", 11))

        text.addWidget(self._name_lbl)
        text.addWidget(self._detail_lbl)
        layout.addLayout(text)
        layout.addStretch()

        self._free_lbl = QLabel(f"{self.drive.free_gb} GB\nfree")
        self._free_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._free_lbl.setFont(QFont("Arial", 11))
        layout.addWidget(self._free_lbl)

        self._refresh_labels()

    def _refresh_labels(self):
        self._name_lbl.setStyleSheet(f"color: {T.TEXT_PRIMARY};")
        self._detail_lbl.setStyleSheet(f"color: {T.TEXT_SECONDARY};")
        self._free_lbl.setStyleSheet(f"color: {T.TEXT_MUTED};")

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)

    def _apply_style(self, selected: bool):
        self._refresh_labels()
        if selected:
            self.setStyleSheet(f"""
                DriveCard {{
                    background: {T.BG_CARD_SEL};
                    border: 2px solid {T.BORDER_CARD_SEL};
                    border-radius: 10px;
                }}
            """)
        else:
            hover_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #48484a, stop:1 #3a3a3c)" \
                if T.dark else \
                "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fafafa, stop:1 #eeeeee)"
            hover_border = "#606062" if T.dark else "#aaaaaa"
            self.setStyleSheet(f"""
                DriveCard {{
                    background: {T.BG_CARD};
                    border: 1px solid {T.BORDER_CARD};
                    border-radius: 10px;
                }}
                DriveCard:hover {{
                    background: {hover_bg};
                    border: 1px solid {hover_border};
                }}
            """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.drive)


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Arial", 10, QFont.Bold))
    lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; letter-spacing: 1px; padding: 8px 0 4px 0;")
    return lbl


def _empty_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; font-size: 12px; padding: 8px 0;")
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

        self._header_widget = QWidget()
        self._header_widget.setFixedHeight(52)
        h_layout = QHBoxLayout(self._header_widget)
        h_layout.setContentsMargins(16, 0, 12, 0)

        self._title_lbl = QLabel("DRIVES")
        self._title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        h_layout.addWidget(self._title_lbl)
        h_layout.addStretch()

        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.clicked.connect(self.refresh)
        h_layout.addWidget(self._refresh_btn)
        root.addWidget(self._header_widget)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(12, 8, 12, 12)
        self._body_layout.setSpacing(0)
        self._body_layout.addStretch()

        self._scroll.setWidget(self._body)
        root.addWidget(self._scroll, stretch=1)

        self.apply_theme()
        self.refresh()

    def apply_theme(self):
        self._header_widget.setStyleSheet(T.HEADER_STYLE)
        self._title_lbl.setStyleSheet(T.PANEL_TITLE_STYLE)
        if T.dark:
            self._refresh_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #3a3a3c, stop:1 #2c2c2e);
                    border: 1px solid #48484a; border-radius: 14px;
                    color: #f0f0f0; font-size: 16px;
                }
                QPushButton:hover { background: #48484a; }
            """)
        else:
            self._refresh_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #f0f0f0, stop:1 #d8d8d8);
                    border: 1px solid #b0b0b0; border-radius: 14px;
                    color: #555; font-size: 16px;
                }
                QPushButton:hover { background: #e8e8e8; color: #222; }
            """)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {T.BG_PANEL}; border: none; }}"
        )
        self._body.setStyleSheet(f"background: {T.BG_PANEL};")
        # Recreate cards with new theme
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
        div.setStyleSheet(f"color: {T.DIVIDER}; margin: 8px 0;")
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
