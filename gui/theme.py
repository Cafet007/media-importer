"""
Central theme — supports light (gray glossy) and dark mode.
Import T and use T.BG_BASE etc. in apply_theme() methods.
Module-level names are aliases to T for backward compat at import time.
"""


class Theme:
    """Mutable theme singleton. Call T.set_dark(bool) then apply_theme() on widgets."""

    def __init__(self, dark: bool = False):
        self.dark = dark
        self._load()

    def set_dark(self, dark: bool) -> None:
        self.dark = dark
        self._load()

    def _load(self) -> None:
        if self.dark:
            self.BG_BASE       = "#1c1c1e"
            self.BG_PANEL      = "#2c2c2e"
            self.BG_HEADER     = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a3a3c, stop:1 #2c2c2e)"
            self.BG_CARD       = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a3a3c, stop:1 #2c2c2e)"
            self.BG_CARD_SEL   = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1c3c6e, stop:1 #0a2848)"
            self.BG_TABLE      = "#1c1c1e"
            self.BG_TABLE_ALT  = "#252527"
            self.BG_TABLE_HDR  = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a3a3c, stop:1 #2c2c2e)"
            self.BG_INPUT      = "#2c2c2e"
            self.BG_BOTTOM     = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2c2c2e, stop:1 #1c1c1e)"

            self.BORDER        = "#48484a"
            self.BORDER_FOCUS  = "#4a9eff"
            self.BORDER_CARD   = "#48484a"
            self.BORDER_CARD_SEL = "#4a9eff"

            self.TEXT_PRIMARY   = "#f0f0f0"
            self.TEXT_SECONDARY = "#a0a0a8"
            self.TEXT_MUTED     = "#68686e"
            self.TEXT_LABEL     = "#c0c0c8"

            self.ACCENT         = "#4a9eff"
            self.ACCENT_HOVER   = "#5aaeff"
            self.SUCCESS        = "#32d266"
            self.WARNING        = "#f0a030"
            self.DANGER         = "#ff5050"
            self.CONFLICT       = "#f0a030"

            self.SPLITTER       = "#48484a"
            self.DIVIDER        = "#3a3a3c"

            self._PROGRESS_BG   = "#3a3a3c"
            self._PROGRESS_BORDER = "#48484a"
            self._TAB_HOVER_BG  = "#3a3a3c"
            self._HEADER_SECTION_HOVER = "#3a3a3c"
        else:
            self.BG_BASE       = "#dcdcdc"
            self.BG_PANEL      = "#e8e8e8"
            self.BG_HEADER     = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ebebeb, stop:1 #d4d4d4)"
            self.BG_CARD       = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f5f5f5, stop:1 #e8e8e8)"
            self.BG_CARD_SEL   = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #cce0ff, stop:1 #a8c8f8)"
            self.BG_TABLE      = "#f2f2f2"
            self.BG_TABLE_ALT  = "#eaeaea"
            self.BG_TABLE_HDR  = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e6e6e6, stop:1 #d6d6d6)"
            self.BG_INPUT      = "#fafafa"
            self.BG_BOTTOM     = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #dedede, stop:1 #cacaca)"

            self.BORDER        = "#bbbbbb"
            self.BORDER_FOCUS  = "#3d7dd8"
            self.BORDER_CARD   = "#c4c4c4"
            self.BORDER_CARD_SEL = "#3d7dd8"

            self.TEXT_PRIMARY   = "#1a1a1a"
            self.TEXT_SECONDARY = "#606060"
            self.TEXT_MUTED     = "#999999"
            self.TEXT_LABEL     = "#444444"

            self.ACCENT         = "#3d7dd8"
            self.ACCENT_HOVER   = "#5090e8"
            self.SUCCESS        = "#2e9e5a"
            self.WARNING        = "#c07800"
            self.DANGER         = "#c0392b"
            self.CONFLICT       = "#c07800"

            self.SPLITTER       = "#b8b8b8"
            self.DIVIDER        = "#cccccc"

            self._PROGRESS_BG   = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #d0d0d0, stop:1 #c0c0c0)"
            self._PROGRESS_BORDER = "#b0b0b0"
            self._TAB_HOVER_BG  = "#e8e8e8"
            self._HEADER_SECTION_HOVER = "#e0e0e0"

    # ------------------------------------------------------------------
    # Composite style strings (computed from current palette)
    # ------------------------------------------------------------------

    @property
    def HEADER_STYLE(self) -> str:
        return f"""
            QWidget {{
                background: {self.BG_HEADER};
                border-bottom: 1px solid {self.DIVIDER};
            }}
        """

    @property
    def PANEL_TITLE_STYLE(self) -> str:
        return f"color: {self.TEXT_SECONDARY}; letter-spacing: 1px;"

    @property
    def INPUT_STYLE(self) -> str:
        return f"""
            QLineEdit {{
                background: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                color: {self.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {self.BORDER_FOCUS}; }}
        """

    @property
    def TABLE_STYLE(self) -> str:
        return f"""
            QTableWidget {{
                background: {self.BG_TABLE};
                alternate-background-color: {self.BG_TABLE_ALT};
                color: {self.TEXT_PRIMARY};
                font-size: 12px;
                border: none;
                gridline-color: {self.DIVIDER};
            }}
            QHeaderView::section {{
                background: {self.BG_TABLE_HDR};
                color: {self.TEXT_SECONDARY};
                font-size: 11px;
                font-weight: bold;
                padding: 6px 8px;
                border: none;
                border-right: 1px solid {self.DIVIDER};
                border-bottom: 1px solid {self.BORDER};
                text-transform: uppercase;
            }}
            QHeaderView::section:hover {{
                background: {self._HEADER_SECTION_HOVER};
                color: {self.TEXT_PRIMARY};
            }}
            QTableWidget::item {{ padding: 4px 8px; color: {self.TEXT_PRIMARY}; }}
            QTableWidget::item:selected {{
                background: {self.BG_CARD_SEL};
                color: {self.TEXT_PRIMARY};
            }}
        """

    @property
    def TAB_STYLE(self) -> str:
        return f"""
            QTabWidget::pane {{ border: none; background: {self.BG_TABLE}; }}
            QTabBar::tab {{
                background: {self.BG_HEADER};
                color: {self.TEXT_MUTED};
                padding: 8px 20px;
                border: 1px solid {self.DIVIDER};
                border-bottom: none;
                font-size: 12px;
                font-weight: bold;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: {self.BG_TABLE};
                color: {self.TEXT_PRIMARY};
                border-bottom: 2px solid {self.ACCENT};
            }}
            QTabBar::tab:hover {{ color: {self.TEXT_PRIMARY}; background: {self._TAB_HOVER_BG}; }}
        """

    @property
    def PROGRESS_STYLE(self) -> str:
        return f"""
            QProgressBar {{
                background: {self._PROGRESS_BG};
                border: 1px solid {self._PROGRESS_BORDER}; border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #60a0f0, stop:1 #3468c0);
                border-radius: 4px;
            }}
        """

    @property
    def FILE_PROGRESS_STYLE(self) -> str:
        return f"""
            QProgressBar {{
                background: {self.BORDER}; border-radius: 2px; border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #50c878, stop:1 {self.SUCCESS});
                border-radius: 2px;
            }}
        """

    # ------------------------------------------------------------------
    # Button style helpers
    # ------------------------------------------------------------------

    def btn_primary(self, h: int = 40) -> str:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #5090e8, stop:1 #3468c0);
                border: 1px solid #2858a8; border-radius: 8px;
                color: white; font-size: 13px; font-weight: bold;
                padding: 0 18px; min-height: {h}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #60a0f8, stop:1 #4878d0);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #3468c0, stop:1 #5090e8);
            }}
            QPushButton:disabled {{
                background: {'#3a3a3c' if self.dark else '#c8c8c8'};
                color: {'#555' if self.dark else '#999'};
                border: 1px solid {'#48484a' if self.dark else '#bbb'};
            }}
        """

    def btn_secondary(self, h: int = 40) -> str:
        if self.dark:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #3a3a3c, stop:1 #2c2c2e);
                    border: 1px solid #48484a; border-radius: 8px;
                    color: {self.TEXT_PRIMARY}; font-size: 13px; font-weight: bold;
                    padding: 0 16px; min-height: {h}px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #48484a, stop:1 #3a3a3c);
                    border: 1px solid #606062;
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #2c2c2e, stop:1 #3a3a3c);
                }}
                QPushButton:disabled {{ background: #2c2c2e; color: #555; border: 1px solid #3a3a3c; }}
            """
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #f0f0f0, stop:1 #d8d8d8);
                border: 1px solid #b0b0b0; border-radius: 8px;
                color: #333; font-size: 13px; font-weight: bold;
                padding: 0 16px; min-height: {h}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #f8f8f8, stop:1 #e4e4e4);
                border: 1px solid #999;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #d8d8d8, stop:1 #f0f0f0);
            }}
            QPushButton:disabled {{ background: #d4d4d4; color: #aaa; border: 1px solid #c0c0c0; }}
        """

    def btn_danger(self, h: int = 40) -> str:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #e05050, stop:1 #b83030);
                border: 1px solid #982828; border-radius: 8px;
                color: white; font-size: 13px; font-weight: bold;
                padding: 0 16px; min-height: {h}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #f06060, stop:1 #c84040);
            }}
            QPushButton:disabled {{
                background: {'#3a3a3c' if self.dark else '#d4d4d4'};
                color: {'#555' if self.dark else '#aaa'};
            }}
        """

    def small_btn_style(self) -> str:
        """Compact button for panel headers (Refresh, browse …)."""
        if self.dark:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #3a3a3c, stop:1 #2c2c2e);
                    border: 1px solid #48484a; border-radius: 5px;
                    color: {self.TEXT_PRIMARY}; font-size: 11px; padding: 0 10px;
                }}
                QPushButton:hover {{ background: #48484a; color: {self.TEXT_PRIMARY}; }}
            """
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #f0f0f0, stop:1 #d8d8d8);
                border: 1px solid #b0b0b0; border-radius: 5px;
                color: #444; font-size: 11px; padding: 0 10px;
            }}
            QPushButton:hover {{ background: #e0e0e0; color: #111; }}
        """


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
T = Theme()

# ---------------------------------------------------------------------------
# Module-level aliases — correct for default (light) theme at import time.
# In apply_theme() methods always use T.xxx directly.
# ---------------------------------------------------------------------------
BG_BASE        = T.BG_BASE
BG_PANEL       = T.BG_PANEL
BG_HEADER      = T.BG_HEADER
BG_CARD        = T.BG_CARD
BG_CARD_SEL    = T.BG_CARD_SEL
BG_TABLE       = T.BG_TABLE
BG_TABLE_ALT   = T.BG_TABLE_ALT
BG_TABLE_HDR   = T.BG_TABLE_HDR
BG_INPUT       = T.BG_INPUT
BG_BOTTOM      = T.BG_BOTTOM
BORDER         = T.BORDER
BORDER_FOCUS   = T.BORDER_FOCUS
BORDER_CARD    = T.BORDER_CARD
BORDER_CARD_SEL = T.BORDER_CARD_SEL
TEXT_PRIMARY   = T.TEXT_PRIMARY
TEXT_SECONDARY = T.TEXT_SECONDARY
TEXT_MUTED     = T.TEXT_MUTED
TEXT_LABEL     = T.TEXT_LABEL
ACCENT         = T.ACCENT
ACCENT_HOVER   = T.ACCENT_HOVER
SUCCESS        = T.SUCCESS
WARNING        = T.WARNING
DANGER         = T.DANGER
CONFLICT       = T.CONFLICT
SPLITTER       = T.SPLITTER
DIVIDER        = T.DIVIDER
HEADER_STYLE   = T.HEADER_STYLE
PANEL_TITLE_STYLE = T.PANEL_TITLE_STYLE
INPUT_STYLE    = T.INPUT_STYLE
TABLE_STYLE    = T.TABLE_STYLE
TAB_STYLE      = T.TAB_STYLE


def btn_primary(h: int = 40) -> str:
    return T.btn_primary(h=h)


def btn_secondary(h: int = 40) -> str:
    return T.btn_secondary(h)


def btn_danger(h: int = 40) -> str:
    return T.btn_danger(h)
