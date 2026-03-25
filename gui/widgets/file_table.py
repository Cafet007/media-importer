"""
File Table — shows scanned media files with kind, date, size, status.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from backend.core.models import MediaFile, MediaType


_KIND_ICON = {
    MediaType.RAW:     "🟠 RAW",
    MediaType.PHOTO:   "🟢 JPG",
    MediaType.VIDEO:   "🔵 Video",
    MediaType.UNKNOWN: "⚪ ?",
}

_STATUS_COLOR = {
    "new":      "#4a9eff",
    "imported": "#555",
    "failed":   "#e74c3c",
}


class FileTable(QWidget):
    """Displays scanned files with new/already-imported status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #333;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        self._title = QLabel("FILES")
        self._title.setFont(QFont("Arial", 11, QFont.Bold))
        self._title.setStyleSheet("color: #888; letter-spacing: 1px;")
        h_layout.addWidget(self._title)
        h_layout.addStretch()

        self._summary = QLabel("")
        self._summary.setFont(QFont("Arial", 11))
        self._summary.setStyleSheet("color: #666;")
        h_layout.addWidget(self._summary)
        layout.addWidget(header)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["File", "Kind", "Date", "Size", "Status"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setStyleSheet("""
            QTableWidget {
                background: #1e1e1e;
                alternate-background-color: #222;
                color: #ddd;
                font-size: 12px;
                border: none;
            }
            QHeaderView::section {
                background: #252525;
                color: #888;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid #333;
                text-transform: uppercase;
            }
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected { background: #1e3a5f; }
        """)
        layout.addWidget(self._table, stretch=1)

    def load(self, files: list[MediaFile], new_set: set[str] | None = None):
        """
        Populate table with files.
        new_set: set of filenames that are new (not yet imported).
        """
        self._table.setRowCount(len(files))

        new_count = skipped_count = 0

        for row, f in enumerate(files):
            is_new = new_set is None or f.name in new_set
            status = "new" if is_new else "imported"
            if is_new:
                new_count += 1
            else:
                skipped_count += 1

            date_str = f.captured_at.strftime("%Y-%m-%d  %H:%M") if f.captured_at else "—"
            kind_str = _KIND_ICON.get(f.media_type, "?")
            size_str = f"{f.size_mb:.1f} MB"
            status_str = "New" if is_new else "Already imported"

            items = [
                QTableWidgetItem(f.name),
                QTableWidgetItem(kind_str),
                QTableWidgetItem(date_str),
                QTableWidgetItem(size_str),
                QTableWidgetItem(status_str),
            ]

            color = QColor(_STATUS_COLOR.get(status, "#ddd"))
            for col, item in enumerate(items):
                item.setForeground(color if col == 4 else QColor("#ddd"))
                self._table.setItem(row, col, item)

            self._table.setRowHeight(row, 28)

        total_mb = sum(f.size_mb for f in files)
        self._summary.setText(
            f"{len(files)} files  ·  {total_mb:.0f} MB  |  "
            f"New: {new_count}   Already imported: {skipped_count}"
        )

    def mark_in_progress(self, filename: str):
        """Update a row's status to 'In Progress...' while copying."""
        for row in range(self._table.rowCount()):
            if self._table.item(row, 0).text() == filename:
                item = QTableWidgetItem("In Progress...")
                item.setForeground(QColor("#f39c12"))
                self._table.setItem(row, 4, item)
                self._table.scrollToItem(item)
                break

    def mark_copied(self, filename: str):
        """Update a row's status to 'Copied ✓' after import."""
        for row in range(self._table.rowCount()):
            if self._table.item(row, 0).text() == filename:
                item = QTableWidgetItem("Copied ✓")
                item.setForeground(QColor("#2ecc71"))
                self._table.setItem(row, 4, item)
                break

    def mark_failed(self, filename: str):
        for row in range(self._table.rowCount()):
            if self._table.item(row, 0).text() == filename:
                item = QTableWidgetItem("Failed ✗")
                item.setForeground(QColor("#e74c3c"))
                self._table.setItem(row, 4, item)
                break

    def clear(self):
        self._table.setRowCount(0)
        self._summary.setText("")
