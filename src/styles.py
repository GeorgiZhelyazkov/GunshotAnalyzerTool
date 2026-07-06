"""Central design tokens and QSS styles for the application."""

# ── Palette (AI panel reference) ─────────────────────────────────────────────
BG_DARK = "#050d1a"
BG_CARD = "#0a192fd9"
BG_PANEL = "#0a1628"
BG_BORDER = "#1a3a5c"

ACCENT = "#00d4ff"
ACCENT_TEAL = "#1abc9c"
ACCENT_GREEN = "#00ff88"
ACCENT_MUTED = "#7ab3cc"
ACCENT_DIM = "#00b4dc"

TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a0aec0"
TEXT_HINT = "#718096"
TEXT_MUTED = "#bdc3c7"

STATUS_OK = "#2ecc71"
STATUS_WARN = "#f1c40f"
STATUS_DANGER = "#e74c3c"
RECORD_A = "#e74c3c"
RECORD_B = ACCENT_TEAL

# ── Sliders ──────────────────────────────────────────────────────────────────
SLIDER_STYLE = """
    QSlider::groove:horizontal {
        height: 5px; background: #0a1628; border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #00d4ff; width: 13px; height: 13px;
        margin: -4px 0; border-radius: 6px;
    }
    QSlider::handle:horizontal:hover { background: #33ddff; }
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #0066cc, stop:1 #00d4ff);
        border-radius: 2px;
    }
"""

SLIDER_BP_LOW = """
    QSlider::groove:horizontal { height: 4px; background: #1a3a5c; border-radius: 2px; }
    QSlider::handle:horizontal {
        background: #00d4ff; width: 14px; height: 14px;
        margin: -5px 0; border-radius: 7px;
    }
    QSlider::handle:horizontal:hover { background: #33ddff; }
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #0066cc, stop:1 #00d4ff);
        border-radius: 2px;
    }
"""

SLIDER_BP_HIGH = """
    QSlider::groove:horizontal { height: 4px; background: #1a3a5c; border-radius: 2px; }
    QSlider::handle:horizontal {
        background: #1abc9c; width: 14px; height: 14px;
        margin: -5px 0; border-radius: 7px;
    }
    QSlider::handle:horizontal:hover { background: #48d1b5; }
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #117a65, stop:1 #1abc9c);
        border-radius: 2px;
    }
"""

# ── Layout ───────────────────────────────────────────────────────────────────
CARD_STYLE = """
    QFrame {
        background-color: transparent;
        border-radius: 16px;
        padding: 15px;
    }
"""

BOX_RESULT = """
    background-color: transparent;
    border-radius: 8px;
    border: 2px solid #00b4dc;
"""

BOX_META = """
    background-color: #0a1628;
    border-radius: 8px;
    border: 2px solid #1a3a5c;
    padding: 5px;
"""

BOX_BANDPASS = """
    QFrame {
        background-color: #0a1628;
        border: 2px solid #1a3a5c;
        border-radius: 10px;
        padding: 8px;
    }
"""

# ── Labels ───────────────────────────────────────────────────────────────────
LBL_PANEL_TITLE = (
    f"color: {ACCENT_TEAL}; font-size: 16px; font-weight: bold;"
    " border: none; qproperty-alignment: 'AlignCenter';"
)

LBL_SECTION = f"color: {TEXT_PRIMARY}; font-weight: bold; border: none; margin-top: 2px;"
LBL_HINT = f"color: {TEXT_HINT}; font-size: 11px; border: none; qproperty-alignment: 'AlignCenter';"
LBL_BODY = f"color: {TEXT_PRIMARY}; border: none;"
LBL_META = f"color: {TEXT_SECONDARY}; font-family: 'Segoe UI'; border: none;"
LBL_TIME = f"color: {TEXT_PRIMARY}; border: none;"
LBL_SUBSECTION = f"color: {TEXT_MUTED}; font-size: 11px; border: none; margin-top: 2px;"

TEXT_RESULT = (
    "background-color: transparent; color: #1abc9c;"
    " font-family: 'Consolas', 'Courier New'; font-size: 13px;"
    f" border: 2px solid {ACCENT_DIM};"
)

TEXT_PROBABILITIES = (
    "background-color: transparent; color: #ecf0f1; border: none;"
    " font-family: 'Courier New'; font-size: 11px;"
)

# ── Button QSS builder ───────────────────────────────────────────────────────
def _button_qss(normal, hover, pressed, *, checked=None, disabled="#263040"):
    checked_rule = ""
    if checked is not None:
        checked_rule = f"""
        QPushButton:checked {{
            {checked}
        }}
        """
    return f"""
        QPushButton {{
            {normal}
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px;
            border: none;
            font-size: 13px;
        }}
        QPushButton:hover {{
            {hover}
        }}
        QPushButton:pressed {{
            {pressed}
        }}
        QPushButton:disabled {{
            background: {disabled};
            color: #4a5568;
        }}
        {checked_rule}
    """


BTN_PRIMARY = _button_qss(
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0066cc, stop:1 #00aaff);",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0077dd, stop:1 #33bbff);"
    " border: 1px solid #00d4ff88;",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0055aa, stop:1 #0088cc);",
)

BTN_SUCCESS = _button_qss(
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00aa55, stop:1 #00ff88);",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00bb66, stop:1 #33ffaa);"
    " border: 1px solid #00ff8888;",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #008844, stop:1 #00cc77);",
)

BTN_WARN = _button_qss(
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #cc6600, stop:1 #ff9900);",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #dd7700, stop:1 #ffaa33);"
    " border: 1px solid #ff990088;",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #aa5500, stop:1 #cc7700);",
)

BTN_DANGER = _button_qss(
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #cc2200, stop:1 #ff4422);",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #dd3311, stop:1 #ff5533);"
    " border: 1px solid #ff442288;",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #aa1100, stop:1 #cc3311);",
)

BTN_SECONDARY = _button_qss(
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1a5276, stop:1 #2980b9);",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #21618c, stop:1 #3498db);"
    " border: 1px solid #00d4ff66;",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #154360, stop:1 #1f618d);",
)

BTN_NEUTRAL = _button_qss(
    "background: #5d6d7e;",
    "background: #7f8c8d; border: 1px solid #00d4ff44;",
    "background: #566573;",
)

BTN_SAVE = _button_qss(
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6c3483, stop:1 #9b59b6);",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7d3c98, stop:1 #af7ac5);"
    " border: 1px solid #bb8fce88;",
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5b2c6f, stop:1 #884ea0);",
)

BTN_TOGGLE = _button_qss(
    "background-color: #263040; color: #bdc3c7;",
    "background-color: #2e3f54; color: white; border: 1px solid #00d4ff66;",
    "background-color: #1e2a3a;",
    checked=(
        "background-color: #0a3040;"
        " color: #00d4ff;"
        " border: 2px solid #00d4ff;"
        " font-weight: bold;"
    ),
)

BTN_ICON = """
    QPushButton {
        background-color: transparent;
        color: #1abc9c;
        border: none;
        font-size: 20px;
        border-radius: 8px;
        padding: 4px;
    }
    QPushButton:hover {
        background-color: #00d4ff22;
        color: #00d4ff;
    }
    QPushButton:pressed {
        background-color: #00d4ff33;
    }
"""

SIDEBAR_BTN = """
    QPushButton {
        background-color: transparent;
        color: #7ab3cc;
        font-family: 'Consolas';
        font-size: 13px;
        font-weight: bold;
        text-align: center;
        border: none;
        border-radius: 10px;
        min-height: 40px;
    }
    QPushButton:hover {
        background-color: #00d4ff26;
        color: #00d4ff;
        border: 1px solid #00d4ff66;
    }
    QPushButton:checked {
        background-color: #00d4ff33;
        color: #00d4ff;
        border-left: 3px solid #00d4ff;
    }
"""

MATPLOTLIB_THEME = {
    "axes.facecolor":   "none",
    "figure.facecolor": "none",
    "axes.edgecolor":   ACCENT,
    "axes.labelcolor":  ACCENT,
    "xtick.color":      "#008899",
    "ytick.color":      "#008899",
    "text.color":       "white",
    "grid.color":       "#0a2040",
    "grid.linestyle":   "--",
    "grid.alpha":       0.4,
    "axes.grid":        True,
    "axes.spines.top":  False,
    "axes.spines.right": False,
}
