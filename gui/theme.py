"""
Central theme — gray glossy palette for all widgets.
Import this module and use the constants + helpers throughout the GUI.
"""

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BG_BASE       = "#dcdcdc"   # main window background
BG_PANEL      = "#e8e8e8"   # panel bodies
BG_HEADER     = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ebebeb, stop:1 #d4d4d4)"
BG_CARD       = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f5f5f5, stop:1 #e8e8e8)"
BG_CARD_SEL   = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #cce0ff, stop:1 #a8c8f8)"
BG_TABLE      = "#f2f2f2"
BG_TABLE_ALT  = "#eaeaea"
BG_TABLE_HDR  = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e6e6e6, stop:1 #d6d6d6)"
BG_INPUT      = "#fafafa"
BG_BOTTOM     = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #dedede, stop:1 #cacaca)"

BORDER        = "#bbbbbb"
BORDER_FOCUS  = "#3d7dd8"
BORDER_CARD   = "#c4c4c4"
BORDER_CARD_SEL = "#3d7dd8"

TEXT_PRIMARY   = "#1a1a1a"
TEXT_SECONDARY = "#606060"
TEXT_MUTED     = "#999999"
TEXT_LABEL     = "#444444"

ACCENT         = "#3d7dd8"
ACCENT_HOVER   = "#5090e8"
SUCCESS        = "#2e9e5a"
WARNING        = "#c07800"
DANGER         = "#c0392b"
CONFLICT       = "#c07800"

SPLITTER       = "#b8b8b8"
DIVIDER        = "#cccccc"

# ---------------------------------------------------------------------------
# Button styles
# ---------------------------------------------------------------------------

def btn_primary(w=None, h=40) -> str:
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
        QPushButton:disabled {{ background: #c8c8c8; color: #999; border: 1px solid #bbb; }}
    """


def btn_secondary(h=40) -> str:
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


def btn_danger(h=40) -> str:
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
        QPushButton:disabled {{ background: #d4d4d4; color: #aaa; }}
    """


# ---------------------------------------------------------------------------
# Panel header style (shared)
# ---------------------------------------------------------------------------

HEADER_STYLE = f"""
    QWidget {{
        background: {BG_HEADER};
        border-bottom: 1px solid {DIVIDER};
    }}
"""

PANEL_TITLE_STYLE = f"color: {TEXT_SECONDARY}; letter-spacing: 1px;"

# ---------------------------------------------------------------------------
# Input field
# ---------------------------------------------------------------------------

INPUT_STYLE = f"""
    QLineEdit {{
        background: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
        font-size: 12px;
    }}
    QLineEdit:focus {{ border: 1px solid {BORDER_FOCUS}; }}
"""

# ---------------------------------------------------------------------------
# Table style
# ---------------------------------------------------------------------------

TABLE_STYLE = f"""
    QTableWidget {{
        background: {BG_TABLE};
        alternate-background-color: {BG_TABLE_ALT};
        color: {TEXT_PRIMARY};
        font-size: 12px;
        border: none;
        gridline-color: {DIVIDER};
    }}
    QHeaderView::section {{
        background: {BG_TABLE_HDR};
        color: {TEXT_SECONDARY};
        font-size: 11px;
        font-weight: bold;
        padding: 6px 8px;
        border: none;
        border-right: 1px solid {DIVIDER};
        border-bottom: 1px solid {BORDER};
        text-transform: uppercase;
    }}
    QHeaderView::section:hover {{ background: #e0e0e0; color: {TEXT_PRIMARY}; }}
    QTableWidget::item {{ padding: 4px 8px; color: {TEXT_PRIMARY}; }}
    QTableWidget::item:selected {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 #cce0ff, stop:1 #b0ccf8);
        color: {TEXT_PRIMARY};
    }}
"""

# ---------------------------------------------------------------------------
# Tab widget
# ---------------------------------------------------------------------------

TAB_STYLE = f"""
    QTabWidget::pane {{ border: none; background: {BG_TABLE}; }}
    QTabBar::tab {{
        background: {BG_HEADER};
        color: {TEXT_MUTED};
        padding: 8px 20px;
        border: 1px solid {DIVIDER};
        border-bottom: none;
        font-size: 12px;
        font-weight: bold;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{
        background: {BG_TABLE};
        color: {TEXT_PRIMARY};
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover {{ color: {TEXT_PRIMARY}; background: #e8e8e8; }}
"""
