"""
History Panel — shows past import records from the database.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from gui.theme import T


class HistoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header_widget = QWidget()
        self._header_widget.setFixedHeight(52)
        h_layout = QHBoxLayout(self._header_widget)
        h_layout.setContentsMargins(16, 0, 16, 0)

        self._title_lbl = QLabel("IMPORT HISTORY")
        self._title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        h_layout.addWidget(self._title_lbl)
        h_layout.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedHeight(28)
        self._refresh_btn.clicked.connect(self.load)
        h_layout.addWidget(self._refresh_btn)
        layout.addWidget(self._header_widget)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["File", "Type", "Camera", "Captured", "Imported", "Destination"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table, stretch=1)

        self.apply_theme()

    def apply_theme(self):
        self._header_widget.setStyleSheet(T.HEADER_STYLE)
        self._title_lbl.setStyleSheet(T.PANEL_TITLE_STYLE)
        self._table.setStyleSheet(T.TABLE_STYLE)
        if T.dark:
            self._refresh_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #3a3a3c, stop:1 #2c2c2e);
                    border: 1px solid #48484a; border-radius: 5px;
                    color: #f0f0f0; font-size: 11px; padding: 0 10px;
                }
                QPushButton:hover { background: #48484a; }
            """)
        else:
            self._refresh_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #f0f0f0, stop:1 #d8d8d8);
                    border: 1px solid #b0b0b0; border-radius: 5px;
                    color: #444; font-size: 11px; padding: 0 10px;
                }
                QPushButton:hover { background: #e0e0e0; color: #111; }
            """)

    def load(self):
        try:
            from backend.db.repository import get_history
            records = get_history(limit=1000)
        except Exception:
            records = []

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(records))

        for row, rec in enumerate(records):
            from pathlib import Path
            filename   = Path(rec.source_path).name if rec.source_path else "—"
            media_type = rec.media_type or "—"
            camera     = " ".join(filter(None, [rec.camera_make, rec.camera_model])) or "—"
            captured   = rec.captured_at.strftime("%Y-%m-%d  %H:%M") if rec.captured_at else "—"
            imported   = rec.imported_at.strftime("%Y-%m-%d  %H:%M") if rec.imported_at else "—"
            dest       = rec.dest_path or "—"

            for col, text in enumerate([filename, media_type, camera, captured, imported, dest]):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(T.TEXT_PRIMARY))
                self._table.setItem(row, col, item)

            self._table.setRowHeight(row, 28)

        self._table.setSortingEnabled(True)
