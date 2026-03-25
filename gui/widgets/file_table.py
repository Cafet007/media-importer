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
from gui.theme import (
    TABLE_STYLE, HEADER_STYLE, PANEL_TITLE_STYLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, SUCCESS, DANGER, CONFLICT, WARNING,
)


_KIND_ICON = {
    MediaType.RAW:     "🟠 RAW",
    MediaType.PHOTO:   "🟢 JPG",
    MediaType.VIDEO:   "🔵 Video",
    MediaType.UNKNOWN: "⚪ ?",
}

_STATUS_COLOR = {
    "new":      ACCENT,
    "imported": TEXT_MUTED,
    "failed":   DANGER,
}


class _SortableItem(QTableWidgetItem):
    def __init__(self, text: str, sort_key=None):
        super().__init__(text)
        self._sort_key = sort_key if sort_key is not None else text

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, _SortableItem):
            try:
                return self._sort_key < other._sort_key
            except TypeError:
                pass
        return super().__lt__(other)


class FileTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

        self._title = QLabel("FILES")
        self._title.setFont(QFont("Arial", 11, QFont.Bold))
        self._title.setStyleSheet(PANEL_TITLE_STYLE)
        h_layout.addWidget(self._title)
        h_layout.addStretch()

        self._summary = QLabel("")
        self._summary.setFont(QFont("Arial", 11))
        self._summary.setStyleSheet(f"color: {TEXT_SECONDARY};")
        h_layout.addWidget(self._summary)
        layout.addWidget(header)

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
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setSortIndicatorShown(True)
        self._table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self._table.setStyleSheet(TABLE_STYLE)
        layout.addWidget(self._table, stretch=1)

    def load(self, files: list[MediaFile], new_set: set[str] | None = None):
        self._table.setSortingEnabled(False)
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
            date_key = f.captured_at.timestamp() if f.captured_at else 0.0
            kind_str  = _KIND_ICON.get(f.media_type, "?")
            size_str  = f"{f.size_mb:.1f} MB"
            status_str = "New" if is_new else "Already imported"

            items = [
                QTableWidgetItem(f.name),
                QTableWidgetItem(kind_str),
                _SortableItem(date_str, sort_key=date_key),
                _SortableItem(size_str, sort_key=f.size_mb),
                QTableWidgetItem(status_str),
            ]

            status_color = QColor(_STATUS_COLOR.get(status, TEXT_PRIMARY))
            for col, item in enumerate(items):
                item.setForeground(status_color if col == 4 else QColor(TEXT_PRIMARY))
                self._table.setItem(row, col, item)

            self._table.setRowHeight(row, 28)

        self._table.setSortingEnabled(True)

        total_mb = sum(f.size_mb for f in files)
        self._summary.setText(
            f"{len(files)} files  ·  {total_mb:.0f} MB  |  "
            f"New: {new_count}   Already imported: {skipped_count}"
        )

    def _update_status(self, filename: str, text: str, color: str):
        for row in range(self._table.rowCount()):
            if self._table.item(row, 0) and self._table.item(row, 0).text() == filename:
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self._table.setItem(row, 4, item)
                break

    def mark_in_progress(self, filename: str):
        self._update_status(filename, "In Progress...", WARNING)
        for row in range(self._table.rowCount()):
            if self._table.item(row, 0) and self._table.item(row, 0).text() == filename:
                self._table.scrollToItem(self._table.item(row, 4))
                break

    def mark_copied(self, filename: str):
        self._update_status(filename, "Copied ✓", SUCCESS)

    def mark_conflict(self, filename: str):
        self._update_status(filename, "Conflict ⚠", CONFLICT)

    def mark_failed(self, filename: str):
        self._update_status(filename, "Failed ✗", DANGER)

    def clear(self):
        self._table.setRowCount(0)
        self._summary.setText("")
