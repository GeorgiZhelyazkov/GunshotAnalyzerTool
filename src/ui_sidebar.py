from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

from src.drawn_buttons import SidebarButton
from src.styles import ACCENT, BTN_ICON, SIDEBAR_BTN, TEXT_HINT


def create_sidebar(app):
    app.sidebar_frame = QFrame()
    app.sidebar_frame.setObjectName("Sidebar")
    app.sidebar_frame.setStyleSheet(f"""
        QFrame#Sidebar {{
            background-color: #050c1c;
            border-right: 2px solid {ACCENT};
        }}
        {SIDEBAR_BTN}
    """)

    layout = QVBoxLayout(app.sidebar_frame)
    layout.setContentsMargins(15, 30, 15, 30)
    layout.setSpacing(15)

    header = QHBoxLayout()
    app.btn_toggle = QPushButton("☰")
    app.btn_toggle.setFixedWidth(40)
    app.btn_toggle.setStyleSheet(BTN_ICON)
    app.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
    app.btn_toggle.clicked.connect(app.animate_sidebar)

    app.lbl_logo = QLabel("БАЛИСТИЧЕН АНАЛИЗ НА ИЗСТРЕЛИ")
    app.lbl_logo.setStyleSheet(f"""
        color: {ACCENT}; font-size: 15px; font-weight: bold; text-align: center;
        font-family: 'Consolas'; border: none; letter-spacing: 1px;
    """)
    header.addWidget(app.btn_toggle)
    header.addWidget(app.lbl_logo)
    layout.addLayout(header)
    layout.addSpacing(30)

    app.btn_ai = SidebarButton("ai", "Автоматичен режим")
    app.btn_ai.setChecked(True)
    app.btn_ai.clicked.connect(lambda: app.switch_screen(0))
    layout.addWidget(app.btn_ai)

    app.btn_custom = SidebarButton("custom", "Ръчен режим")
    app.btn_custom.clicked.connect(lambda: app.switch_screen(1))
    layout.addWidget(app.btn_custom)

    app.btn_comparison = SidebarButton("compare", "Сравнителен режим")
    app.btn_comparison.clicked.connect(lambda: app.switch_screen(2))
    layout.addWidget(app.btn_comparison)

    layout.addStretch()
    app.lbl_version = QLabel("v1.0")
    app.lbl_version.setStyleSheet(f"color: {TEXT_HINT}; font-size: 11px; font-style: italic; border: none;")
    app.lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(app.lbl_version)

    app.menu_buttons = [app.btn_ai, app.btn_custom, app.btn_comparison]
