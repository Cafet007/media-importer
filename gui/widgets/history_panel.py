"""
History Panel — searchable, filterable import history backed by SQLite.

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  [Search files…]                     N records  Refresh │  ← row 1
  │  Camera ▾  [All][Photo][RAW][Video]  From  To  [Clear]  │  ← row 2
  ├─────────────────────────────────────────────────────────┤
  │  File  │ Type │ Camera │ Captured │ Imported │ Dest     │  ← table
  │  ...                                                    │
  ├─────────────────────────────────────────────────────────┤
  │  Source: /path   [Copy]   Dest: /path  [Copy]  Hash…   │  ← detail strip
  └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QLineEdit,
    QComboBox, QDateEdit, QSizePolicy, QFrame,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDate, QObject, Signal
from PySide6.QtGui import QFont, QColor

from gui.theme import T


_HISTORY_LIMIT = 300
_SESSION_LIMIT = 75
_LOAD_CACHE_SEC = 30


class _HistorySignals(QObject):
    search_done = Signal(int, object, object, bool)
    cameras_done = Signal(int, object, str)


class HistoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sig = _HistorySignals()
        self._sig.search_done.connect(self._on_search_done)
        self._sig.cameras_done.connect(self._on_cameras_done)
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._run_search)
        self._selected_row: int = -1
        self._records: list = []
        self._search_token = 0
        self._camera_token = 0
        self._loaded_once = False
        self._last_load_at = 0.0
        self._cameras_loaded = False
        # Grouped mode state
        self._row_data: dict[int, object] = {}   # row_index → ImportRecord | None (None = header)
        self._group_ranges: dict[int, tuple[int, int]] = {}  # header_row → (first_data, last_data)
        self._collapsed: set[int] = set()        # header rows that are collapsed
        self._build()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_row1())
        layout.addWidget(self._build_row2())

        div = QWidget()
        div.setFixedHeight(1)
        self._bar_div = div
        layout.addWidget(div)

        layout.addWidget(self._build_table(), stretch=1)
        layout.addWidget(self._build_detail_strip())

        self.apply_theme()

    def _build_row1(self) -> QWidget:
        """Search box + record count + refresh button."""
        self._row1 = QWidget()
        self._row1.setFixedHeight(56)
        layout = QHBoxLayout(self._row1)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search files…")
        self._search.setFixedHeight(38)
        self._search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search, stretch=1)

        self._count_lbl = QLabel("")
        f = QFont()
        f.setPixelSize(12)
        self._count_lbl.setFont(f)
        self._count_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout.addWidget(self._count_lbl)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedHeight(32)
        self._refresh_btn.clicked.connect(self._refresh)
        layout.addWidget(self._refresh_btn)

        return self._row1

    def _build_row2(self) -> QWidget:
        """Camera dropdown + media type buttons + date range + clear."""
        self._row2 = QWidget()
        self._row2.setFixedHeight(48)
        layout = QHBoxLayout(self._row2)
        layout.setContentsMargins(16, 4, 16, 8)
        layout.setSpacing(8)

        # Camera dropdown
        self._camera_combo = QComboBox()
        self._camera_combo.setFixedHeight(32)
        self._camera_combo.setMinimumWidth(140)
        self._camera_combo.addItem("All Cameras")
        self._camera_combo.currentIndexChanged.connect(self._on_filter_changed)

        layout.addWidget(self._camera_combo)

        # Media type segmented buttons
        self._type_btns: dict[str, QPushButton] = {}
        for label, value in [("All", ""), ("Photo", "photo"), ("RAW", "raw"), ("Video", "video")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setFixedWidth(52)
            btn.setProperty("filter_value", value)
            btn.clicked.connect(self._on_type_btn_clicked)
            self._type_btns[value] = btn
            layout.addWidget(btn)
        self._type_btns[""].setChecked(True)  # "All" selected by default

        layout.addSpacing(8)

        # Date From
        from_lbl = QLabel("From")
        from_lbl.setFixedWidth(34)
        layout.addWidget(from_lbl)
        self._date_from = QDateEdit()
        self._date_from.setFixedHeight(32)
        self._date_from.setFixedWidth(110)
        self._date_from.setCalendarPopup(True)
        self._date_from.setSpecialValueText("—")
        self._date_from.setMinimumDate(QDate(2000, 1, 1))
        self._date_from.setDate(self._date_from.minimumDate())
        self._date_from.dateChanged.connect(self._on_filter_changed)
        layout.addWidget(self._date_from)

        to_lbl = QLabel("To")
        to_lbl.setFixedWidth(18)
        layout.addWidget(to_lbl)
        self._date_to = QDateEdit()
        self._date_to.setFixedHeight(32)
        self._date_to.setFixedWidth(110)
        self._date_to.setCalendarPopup(True)
        self._date_to.setSpecialValueText("—")
        self._date_to.setMinimumDate(QDate(2000, 1, 1))
        self._date_to.setDate(self._date_to.minimumDate())
        self._date_to.dateChanged.connect(self._on_filter_changed)
        layout.addWidget(self._date_to)

        layout.addStretch()

        # Clear filters button
        self._clear_btn = QPushButton("Clear Filters")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.setVisible(False)
        self._clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(self._clear_btn)

        self._from_lbl = from_lbl
        self._to_lbl   = to_lbl

        return self._row2

    def _build_table(self) -> QWidget:
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["File", "Type", "Camera", "Captured", "Imported", "Destination"]
        )
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
        self._table.itemSelectionChanged.connect(self._on_row_selected)

        self._empty_lbl = QLabel(
            "No import history yet.\nFiles will appear here after your first import."
        )
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        ef = QFont()
        ef.setPixelSize(14)
        self._empty_lbl.setFont(ef)
        self._empty_lbl.hide()

        # Wrap both in a container so they stack
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(self._table)
        cl.addWidget(self._empty_lbl)
        self._table_container = container
        return container

    def _build_detail_strip(self) -> QWidget:
        """Expandable strip shown when a row is selected."""
        self._detail = QWidget()
        self._detail.setFixedHeight(80)
        self._detail.setVisible(False)

        div = QWidget()
        div.setFixedHeight(1)
        self._detail_div = div

        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        wl.addWidget(div)
        wl.addWidget(self._detail)

        dl = QVBoxLayout(self._detail)
        dl.setContentsMargins(16, 8, 16, 8)
        dl.setSpacing(4)

        # Row A: source path
        row_a = QHBoxLayout()
        row_a.setSpacing(6)
        src_lbl = QLabel("Source:")
        src_lbl.setFixedWidth(52)
        self._detail_src = QLabel("—")
        self._detail_src.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._detail_src.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._copy_src_btn = QPushButton("Copy")
        self._copy_src_btn.setFixedHeight(22)
        self._copy_src_btn.setFixedWidth(48)
        self._copy_src_btn.clicked.connect(lambda: self._copy_to_clipboard(self._detail_src.text()))
        row_a.addWidget(src_lbl)
        row_a.addWidget(self._detail_src, stretch=1)
        row_a.addWidget(self._copy_src_btn)

        # Row B: dest path + hash
        row_b = QHBoxLayout()
        row_b.setSpacing(6)
        dst_lbl = QLabel("Dest:")
        dst_lbl.setFixedWidth(52)
        self._detail_dst = QLabel("—")
        self._detail_dst.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._detail_dst.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._copy_dst_btn = QPushButton("Copy")
        self._copy_dst_btn.setFixedHeight(22)
        self._copy_dst_btn.setFixedWidth(48)
        self._copy_dst_btn.clicked.connect(lambda: self._copy_to_clipboard(self._detail_dst.text()))
        hash_sep = QLabel("·")
        self._detail_hash = QLabel("—")
        self._detail_hash.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._copy_hash_btn = QPushButton("Copy Hash")
        self._copy_hash_btn.setFixedHeight(22)
        self._copy_hash_btn.setFixedWidth(80)
        self._copy_hash_btn.clicked.connect(self._copy_full_hash)
        row_b.addWidget(dst_lbl)
        row_b.addWidget(self._detail_dst, stretch=1)
        row_b.addWidget(self._copy_dst_btn)
        row_b.addWidget(hash_sep)
        row_b.addWidget(self._detail_hash)
        row_b.addWidget(self._copy_hash_btn)

        dl.addLayout(row_a)
        dl.addLayout(row_b)

        self._src_lbl = src_lbl
        self._dst_lbl = dst_lbl
        self._full_hash: str = ""

        return wrapper

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def apply_theme(self):
        bar_bg = f"background: {T.BG_TABLE_HDR};"

        self._row1.setStyleSheet(bar_bg)
        self._row2.setStyleSheet(bar_bg)
        self._bar_div.setStyleSheet(f"background: {T.DIVIDER};")

        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {T.BG_INPUT};
                border: 1.5px solid {T.BORDER};
                border-radius: 8px;
                padding: 0 11px;
                color: {T.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1.5px solid {T.BORDER_FOCUS}; }}
        """)
        self._count_lbl.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: transparent;")
        self._refresh_btn.setStyleSheet(T.small_btn_style())
        self._clear_btn.setStyleSheet(T.small_btn_style())

        self._camera_combo.setStyleSheet(f"""
            QComboBox {{
                background: {T.BG_INPUT}; border: 1.5px solid {T.BORDER};
                border-radius: 7px; padding: 0 10px;
                color: {T.TEXT_PRIMARY}; font-size: 12px; min-height: 28px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {T.BG_INPUT}; color: {T.TEXT_PRIMARY};
                selection-background-color: {T.BG_CARD_SEL};
            }}
        """)

        for value, btn in self._type_btns.items():
            self._style_type_btn(btn)

        date_style = f"""
            QDateEdit {{
                background: {T.BG_INPUT}; border: 1.5px solid {T.BORDER};
                border-radius: 7px; padding: 0 8px;
                color: {T.TEXT_PRIMARY}; font-size: 12px; min-height: 28px;
            }}
            QDateEdit::drop-down {{ border: none; width: 20px; }}
        """
        self._date_from.setStyleSheet(date_style)
        self._date_to.setStyleSheet(date_style)

        for lbl in (self._from_lbl, self._to_lbl):
            lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; font-size: 12px; background: transparent;")

        self._table.setStyleSheet(T.TABLE_STYLE)
        self._table_container.setStyleSheet(f"background: {T.BG_TABLE};")
        self._empty_lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; background: transparent;")

        self._detail.setStyleSheet(f"background: {T.BG_TABLE_HDR};")
        self._detail_div.setStyleSheet(f"background: {T.DIVIDER};")
        detail_lbl_style = f"color: {T.TEXT_MUTED}; font-size: 11px; background: transparent;"
        detail_val_style = f"color: {T.TEXT_PRIMARY}; font-size: 11px; background: transparent;"
        for lbl in (self._src_lbl, self._dst_lbl):
            lbl.setStyleSheet(detail_lbl_style)
        for lbl in (self._detail_src, self._detail_dst, self._detail_hash):
            lbl.setStyleSheet(detail_val_style)
        for btn in (self._copy_src_btn, self._copy_dst_btn, self._copy_hash_btn):
            btn.setStyleSheet(T.small_btn_style())

        self.setStyleSheet(f"HistoryPanel {{ background: {T.BG_TABLE}; }}")

    def _style_type_btn(self, btn: QPushButton):
        if btn.isChecked():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T.ACCENT}; border: none; border-radius: 7px;
                    color: white; font-size: 11px; font-weight: 600;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T.BG_INPUT}; border: 1.5px solid {T.BORDER};
                    border-radius: 7px; color: {T.TEXT_SECONDARY};
                    font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ background: {T.BG_CARD}; }}
            """)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def load(self):
        """Called by main_window when switching to the History tab."""
        now = time.monotonic()
        if self._loaded_once and now - self._last_load_at < _LOAD_CACHE_SEC:
            return
        if not self._cameras_loaded:
            self._reload_cameras()
        self._run_search()

    # ------------------------------------------------------------------
    # Filter event handlers
    # ------------------------------------------------------------------

    def _on_search_changed(self, _text: str):
        self._debounce.start(300)
        self._update_clear_btn()

    def _on_filter_changed(self, _=None):
        self._update_clear_btn()
        self._run_search()

    def _on_type_btn_clicked(self):
        clicked = self.sender()
        for btn in self._type_btns.values():
            btn.setChecked(btn is clicked)
            self._style_type_btn(btn)
        self._update_clear_btn()
        self._run_search()

    def _refresh(self):
        self._loaded_once = False
        self._cameras_loaded = False
        self._reload_cameras()
        self._run_search()

    def _clear_filters(self):
        self._search.blockSignals(True)
        self._camera_combo.blockSignals(True)
        self._date_from.blockSignals(True)
        self._date_to.blockSignals(True)

        self._search.clear()
        self._camera_combo.setCurrentIndex(0)
        self._date_from.setDate(self._date_from.minimumDate())
        self._date_to.setDate(self._date_to.minimumDate())

        for value, btn in self._type_btns.items():
            btn.setChecked(value == "")
            self._style_type_btn(btn)

        self._search.blockSignals(False)
        self._camera_combo.blockSignals(False)
        self._date_from.blockSignals(False)
        self._date_to.blockSignals(False)

        self._clear_btn.setVisible(False)
        self._run_search()

    def _update_clear_btn(self):
        active = (
            bool(self._search.text().strip())
            or self._camera_combo.currentIndex() > 0
            or self._date_from.date() != self._date_from.minimumDate()
            or self._date_to.date() != self._date_to.minimumDate()
            or not self._type_btns[""].isChecked()
        )
        self._clear_btn.setVisible(active)

    # ------------------------------------------------------------------
    # Search execution
    # ------------------------------------------------------------------

    def _is_filter_active(self) -> bool:
        return (
            bool(self._search.text().strip())
            or self._camera_combo.currentIndex() > 0
            or self._date_from.date() != self._date_from.minimumDate()
            or self._date_to.date() != self._date_to.minimumDate()
            or not self._type_btns[""].isChecked()
        )

    def _run_search(self):
        self._search_token += 1
        token = self._search_token
        self._count_lbl.setText("Loading…")

        params = self._search_params()
        threading.Thread(
            target=self._run_search_worker,
            args=(token, params),
            daemon=True,
            name="HistorySearch",
        ).start()

    def _reload_cameras(self):
        self._camera_token += 1
        token = self._camera_token
        current = self._camera_combo.currentText()

        def _worker():
            from backend.db.repository import get_distinct_cameras
            cameras = get_distinct_cameras()
            self._sig.cameras_done.emit(token, cameras, current)

        threading.Thread(target=_worker, daemon=True, name="HistoryCameras").start()

    def _search_params(self) -> dict:
        grouped = not self._is_filter_active()
        query = self._search.text().strip()
        camera = self._camera_combo.currentText() if self._camera_combo.currentIndex() > 0 else ""
        media_type = next((v for v, b in self._type_btns.items() if b.isChecked() and v), "")

        min_date = self._date_from.minimumDate()
        date_from = None
        if self._date_from.date() != min_date:
            d = self._date_from.date()
            date_from = datetime(d.year(), d.month(), d.day())

        date_to = None
        if self._date_to.date() != min_date:
            d = self._date_to.date()
            date_to = datetime(d.year(), d.month(), d.day(), 23, 59, 59)

        return {
            "grouped": grouped,
            "query": query,
            "camera": camera,
            "media_type": media_type,
            "date_from": date_from,
            "date_to": date_to,
        }

    def _run_search_worker(self, token: int, params: dict):
        from backend.db.repository import search_history, get_history, get_sessions

        if params["grouped"]:
            records = get_history(limit=_HISTORY_LIMIT)
            sessions = get_sessions(limit=_SESSION_LIMIT)
            self._sig.search_done.emit(token, records, sessions, True)
            return

        records = search_history(
            query=params["query"],
            camera=params["camera"],
            media_type=params["media_type"],
            date_from=params["date_from"],
            date_to=params["date_to"],
            limit=_HISTORY_LIMIT,
        )
        self._sig.search_done.emit(token, records, [], False)

    def _on_search_done(self, token: int, records: list, sessions: list, grouped: bool):
        if token != self._search_token:
            return
        self._loaded_once = True
        self._last_load_at = time.monotonic()
        self._records = records
        if grouped:
            self._populate_grouped(records, sessions)
        else:
            self._populate_table(records)

    def _on_cameras_done(self, token: int, cameras: list[str], current: str):
        if token != self._camera_token:
            return
        self._cameras_loaded = True

        self._camera_combo.blockSignals(True)
        self._camera_combo.clear()
        self._camera_combo.addItem("All Cameras")
        for cam in cameras:
            self._camera_combo.addItem(cam)

        # Restore previous selection if still present
        idx = self._camera_combo.findText(current)
        self._camera_combo.setCurrentIndex(max(0, idx))
        self._camera_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Table population
    # ------------------------------------------------------------------

    def _populate_table(self, records: list):
        self._begin_table_reset()
        try:
            self._populate_table_rows(records)
        finally:
            self._end_table_reset()

    def _populate_table_rows(self, records: list):
        self._table.clearSpans()
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(records))

        has_records = bool(records)
        self._table.setVisible(has_records)
        self._empty_lbl.setVisible(not has_records)
        self._detail.setVisible(False)
        self._selected_row = -1

        for row, rec in enumerate(records):
            filename  = Path(rec.source_path).name if rec.source_path else "—"
            mtype     = rec.media_type or "—"
            camera    = " ".join(filter(None, [rec.camera_make, rec.camera_model])) or "—"
            captured  = rec.captured_at.strftime("%Y-%m-%d  %H:%M") if rec.captured_at else "—"
            imported  = rec.imported_at.strftime("%Y-%m-%d  %H:%M") if rec.imported_at else "—"
            dest      = rec.dest_path or "—"

            for col, text in enumerate([filename, mtype, camera, captured, imported, dest]):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(T.TEXT_PRIMARY if col == 0 else T.TEXT_SECONDARY))
                self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 32)

        self._table.setSortingEnabled(True)
        self._row_data = {i: rec for i, rec in enumerate(records)}
        self._group_ranges = {}
        self._collapsed = set()

        # Disconnect grouped-mode header click handler if it was connected
        try:
            self._table.cellClicked.disconnect(self._on_header_cell_clicked)
        except RuntimeError:
            pass

        n = len(records)
        self._count_lbl.setText(f"{n} record{'s' if n != 1 else ''}" if n else "No results")

    def _populate_grouped(self, records: list, sessions: list):
        """Group records by import session. Shows session header rows with expand/collapse."""
        self._begin_table_reset()
        try:
            self._populate_grouped_rows(records, sessions)
        finally:
            self._end_table_reset()

    def _populate_grouped_rows(self, records: list, sessions: list):
        self._table.clearSpans()
        self._table.setSortingEnabled(False)
        self._detail.setVisible(False)
        self._selected_row = -1
        self._row_data = {}
        self._group_ranges = {}
        self._collapsed = set()

        # Build groups: assign each record to a session by imported_at timestamp
        # Records not matching any session go into an "Other" bucket
        groups: list[tuple[object | None, list]] = []  # (session | None, [records])

        if sessions:
            groups = self._group_records_by_session(records, sessions)
        else:
            # No sessions recorded — show all as one ungrouped block
            if records:
                groups.append((None, records))

        # Count total rows = headers + data rows
        total_rows = sum(1 + len(recs) for _, recs in groups)
        self._table.setRowCount(total_rows)

        has_records = bool(records)
        self._table.setVisible(has_records)
        self._empty_lbl.setVisible(not has_records)

        row_idx = 0
        for sess, recs in groups:
            # --- Header row ---
            header_row = row_idx
            self._row_data[header_row] = None  # marks as header

            if sess is not None:
                date_str  = sess.started_at.strftime("%Y-%m-%d") if sess.started_at else "Unknown date"
                drive     = Path(sess.source_root).name if sess.source_root else "Unknown source"
                n_imp     = sess.imported  or 0
                n_ver     = sess.verified  or 0
                ver_part  = f"  ·  {n_ver} verified" if n_ver else ""
                header_text = f"  ▶  {date_str}  ·  {drive}  ·  {n_imp} imported{ver_part}"
            else:
                header_text = f"  ▶  {len(recs)} file{'s' if len(recs) != 1 else ''}  (no session data)"

            header_item = QTableWidgetItem(header_text)
            header_item.setForeground(QColor(T.TEXT_PRIMARY))
            header_item.setFlags(Qt.ItemIsEnabled)  # not selectable
            self._table.setItem(header_row, 0, header_item)
            # Span header across all columns
            self._table.setSpan(header_row, 0, 1, 6)
            self._table.setRowHeight(header_row, 28)
            self._style_header_row(header_row, collapsed=False)

            first_data = row_idx + 1
            row_idx += 1

            # --- Data rows ---
            for rec in recs:
                filename = Path(rec.source_path).name if rec.source_path else "—"
                mtype    = rec.media_type or "—"
                camera   = " ".join(filter(None, [rec.camera_make, rec.camera_model])) or "—"
                captured = rec.captured_at.strftime("%Y-%m-%d  %H:%M") if rec.captured_at else "—"
                imported = rec.imported_at.strftime("%Y-%m-%d  %H:%M") if rec.imported_at else "—"
                dest     = rec.dest_path or "—"

                self._row_data[row_idx] = rec
                for col, text in enumerate([filename, mtype, camera, captured, imported, dest]):
                    item = QTableWidgetItem(text)
                    item.setForeground(QColor(T.TEXT_PRIMARY if col == 0 else T.TEXT_SECONDARY))
                    self._table.setItem(row_idx, col, item)
                self._table.setRowHeight(row_idx, 32)
                row_idx += 1

            last_data = row_idx - 1
            self._group_ranges[header_row] = (first_data, last_data)

        n = len(records)
        self._count_lbl.setText(f"{n} record{'s' if n != 1 else ''}" if n else "No results")

        # Connect click-on-header for expand/collapse (use cellClicked signal)
        try:
            self._table.cellClicked.disconnect(self._on_header_cell_clicked)
        except RuntimeError:
            pass
        self._table.cellClicked.connect(self._on_header_cell_clicked)

    def _begin_table_reset(self):
        self._table.setUpdatesEnabled(False)
        self._table.blockSignals(True)

    def _end_table_reset(self):
        self._table.blockSignals(False)
        self._table.setUpdatesEnabled(True)
        self._table.viewport().update()

    def _group_records_by_session(self, records: list, sessions: list) -> list[tuple[object | None, list]]:
        buckets: dict[object, list] = {sess: [] for sess in sessions}
        unassigned: list = []

        valid_sessions = [
            sess for sess in sessions
            if getattr(sess, "started_at", None) and getattr(sess, "finished_at", None)
        ]

        for rec in records:
            imported_at = getattr(rec, "imported_at", None)
            matched_session = None
            if imported_at:
                # Sessions are newest-first and few after limiting, so this is
                # cheap while avoiding DB work on the UI thread.
                for sess in valid_sessions:
                    if sess.started_at <= imported_at <= sess.finished_at:
                        matched_session = sess
                        break
            if matched_session:
                buckets[matched_session].append(rec)
            else:
                unassigned.append(rec)

        groups = [(sess, buckets[sess]) for sess in sessions if buckets.get(sess)]
        if unassigned:
            groups.append((None, unassigned))
        return groups

    def _style_header_row(self, header_row: int, collapsed: bool):
        item = self._table.item(header_row, 0)
        if item is None:
            return
        text = item.text()
        # Update arrow indicator
        if "▶" in text or "▼" in text:
            text = text.replace("▶", "▼" if not collapsed else "▶")
        item.setText(text)
        item.setBackground(QColor(T.BG_TABLE_HDR))
        item.setForeground(QColor(T.TEXT_PRIMARY))

    def _on_header_cell_clicked(self, row: int, _col: int):
        if row not in self._group_ranges:
            return
        first, last = self._group_ranges[row]
        if row in self._collapsed:
            # Expand
            self._collapsed.discard(row)
            for r in range(first, last + 1):
                self._table.setRowHidden(r, False)
            self._style_header_row(row, collapsed=False)
        else:
            # Collapse
            self._collapsed.add(row)
            for r in range(first, last + 1):
                self._table.setRowHidden(r, True)
            self._style_header_row(row, collapsed=True)

    # ------------------------------------------------------------------
    # Detail strip
    # ------------------------------------------------------------------

    def _on_row_selected(self):
        rows = self._table.selectedItems()
        if not rows:
            self._detail.setVisible(False)
            self._selected_row = -1
            return

        row = self._table.currentRow()

        # Ignore clicks on header rows (they have None in _row_data when grouped)
        rec = self._row_data.get(row)
        if rec is None:
            self._table.clearSelection()
            return

        if row == self._selected_row:
            # Clicking the same row again collapses the strip
            self._detail.setVisible(False)
            self._selected_row = -1
            self._table.clearSelection()
            return

        self._selected_row = row

        src = rec.source_path or "—"
        dst = rec.dest_path   or "—"

        self._detail_src.setText(src)
        self._detail_dst.setText(dst)

        self._full_hash = rec.file_hash or ""
        short_hash = (rec.file_hash[:16] + "…") if rec.file_hash else "—"
        self._detail_hash.setText(f"SHA256: {short_hash}")

        self._detail.setVisible(True)

    def _copy_to_clipboard(self, text: str):
        if text and text != "—":
            QApplication.clipboard().setText(text)

    def _copy_full_hash(self):
        if self._full_hash:
            QApplication.clipboard().setText(self._full_hash)
