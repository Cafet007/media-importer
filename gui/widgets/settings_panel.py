"""
Settings Panel — folder naming rule templates + live preview.
Opens as a dialog from the main window's settings button.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QFrame, QScrollArea, QGridLayout
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, QColor

from gui.theme import (
    BG_PANEL, BG_INPUT, BORDER, BORDER_FOCUS, ACCENT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    INPUT_STYLE, btn_primary, btn_secondary,
)


class TemplateRow(QWidget):
    """One editable template row with a live preview label."""

    changed = Signal()

    def __init__(self, label: str, key: str, template: str, parent=None):
        super().__init__(parent)
        self._key = key
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setFont(QFont("Arial", 11, QFont.Bold))
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(lbl)

        self._edit = QLineEdit(template)
        self._edit.setStyleSheet(INPUT_STYLE + "QLineEdit { font-family: Menlo, Courier, monospace; }")
        self._edit.textChanged.connect(self._update_preview)
        self._edit.textChanged.connect(self.changed)
        layout.addWidget(self._edit)

        self._preview = QLabel()
        self._preview.setFont(QFont("Menlo, Courier", 10))
        self._preview.setStyleSheet(f"color: {ACCENT}; padding-left: 2px;")
        layout.addWidget(self._preview)

        self._update_preview()

    def _update_preview(self):
        from backend.core.rules import preview_template
        try:
            result = preview_template(self._edit.text(), self._key)
            self._preview.setText(f"  → {result}")
            self._preview.setStyleSheet(f"color: {ACCENT}; padding-left: 2px;")
        except Exception as e:
            self._preview.setText(f"  ⚠ {e}")
            self._preview.setStyleSheet("color: #c0392b; padding-left: 2px;")

    def template(self) -> str:
        return self._edit.text().strip()

    def set_template(self, t: str):
        self._edit.setText(t)


class SettingsDialog(QDialog):
    """Modal dialog for editing folder naming rule templates."""

    rules_saved = Signal(dict)  # emits updated rules dict

    def __init__(self, rules: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings — Folder Naming Rules")
        self.setMinimumWidth(640)
        self.setStyleSheet(f"QDialog {{ background: {BG_PANEL}; }}")
        self._build(rules)

    def _build(self, rules: dict):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("Folder Naming Rules")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        subtitle = QLabel("Templates are relative to your Photos and Videos destination folders.")
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(subtitle)

        # Template rows
        self._photo_row = TemplateRow("Photos  (.jpg .heic .png)", "photo", rules.get("photo", ""))
        self._raw_row   = TemplateRow("RAW  (.arw .cr3 .nef .dng …)", "raw",   rules.get("raw",   ""))
        self._video_row = TemplateRow("Videos  (.mp4 .mov .mts …)", "video", rules.get("video", ""))

        layout.addWidget(self._photo_row)
        layout.addWidget(self._raw_row)
        layout.addWidget(self._video_row)

        # Variable reference
        layout.addWidget(self._build_variable_ref())

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet(btn_secondary(h=36))
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(btn_secondary(h=36))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(btn_primary(h=36))
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _build_variable_ref(self) -> QWidget:
        from backend.core.rules import TEMPLATE_VARIABLES

        box = QWidget()
        box.setStyleSheet(f"background: #dcdcdc; border: 1px solid #c4c4c4; border-radius: 8px;")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(8)

        hdr = QLabel("Available variables")
        hdr.setFont(QFont("Arial", 11, QFont.Bold))
        hdr.setStyleSheet(f"color: {TEXT_SECONDARY};")
        inner.addWidget(hdr)

        grid = QGridLayout()
        grid.setSpacing(4)
        for row, (var, example, desc) in enumerate(TEMPLATE_VARIABLES):
            v = QLabel(var)
            v.setFont(QFont("Menlo, Courier", 11))
            v.setStyleSheet(f"color: {ACCENT};")
            e = QLabel(example)
            e.setFont(QFont("Menlo, Courier", 11))
            e.setStyleSheet("color: #2e9e5a;")
            d = QLabel(desc)
            d.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            grid.addWidget(v, row, 0)
            grid.addWidget(e, row, 1)
            grid.addWidget(d, row, 2)

        inner.addLayout(grid)
        return box

    def _reset(self):
        from backend.core.rules import DEFAULT_TEMPLATES
        self._photo_row.set_template(DEFAULT_TEMPLATES["photo"])
        self._raw_row.set_template(DEFAULT_TEMPLATES["raw"])
        self._video_row.set_template(DEFAULT_TEMPLATES["video"])

    def _save(self):
        from backend.utils.config import save_rules
        rules = {
            "photo": self._photo_row.template(),
            "raw":   self._raw_row.template(),
            "video": self._video_row.template(),
        }
        save_rules(rules)
        self.rules_saved.emit(rules)
        self.accept()
