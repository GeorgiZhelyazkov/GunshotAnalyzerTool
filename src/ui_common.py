"""Shared UI widget factories — keeps all panels consistent with the AI panel."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.styles import (
    BOX_BANDPASS,
    BOX_META,
    BOX_RESULT,
    BTN_DANGER,
    BTN_NEUTRAL,
    BTN_PRIMARY,
    BTN_SAVE,
    BTN_SECONDARY,
    BTN_SUCCESS,
    BTN_TOGGLE,
    BTN_WARN,
    LBL_BODY,
    LBL_HINT,
    LBL_META,
    LBL_PANEL_TITLE,
    LBL_SECTION,
    LBL_SUBSECTION,
    LBL_TIME,
    SLIDER_BP_HIGH,
    SLIDER_BP_LOW,
    SLIDER_STYLE,
    TEXT_PROBABILITIES,
    TEXT_RESULT,
)
from src.drawn_buttons import PlayerButton


_BTN_VARIANTS = {
    "primary":   BTN_PRIMARY,
    "success":   BTN_SUCCESS,
    "warn":      BTN_WARN,
    "danger":    BTN_DANGER,
    "secondary": BTN_SECONDARY,
    "neutral":   BTN_NEUTRAL,
    "save":      BTN_SAVE,
    "toggle":    BTN_TOGGLE,
}


def make_button(text, variant="primary", *, checkable=False, fixed_width=None):
    btn = QPushButton(text)
    btn.setStyleSheet(_BTN_VARIANTS.get(variant, BTN_PRIMARY))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if checkable:
        btn.setCheckable(True)
    if fixed_width is not None:
        btn.setFixedWidth(fixed_width)
    return btn


def make_label(text, style=LBL_BODY, *, align_center=False):
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    if align_center:
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


def make_panel_title(text):
    return make_label(text, LBL_PANEL_TITLE, align_center=True)


def make_hint(text):
    return make_label(text, LBL_HINT, align_center=True)


def make_meta_box(labels):
    """labels: list of QLabel widgets."""
    box = QFrame()
    box.setStyleSheet(BOX_META)
    layout = QVBoxLayout(box)
    for lbl in labels:
        layout.addWidget(lbl)
    return box


def make_result_box(*widgets):
    box = QFrame()
    box.setStyleSheet(BOX_RESULT)
    layout = QVBoxLayout(box)
    for w in widgets:
        layout.addWidget(w)
    return box


def make_player_row(app, suffix):
    """suffix: 'ai' or 'cust' — creates play/pause/stop and attaches to app."""
    layout = QHBoxLayout()
    layout.setSpacing(10)
    layout.setContentsMargins(0, 4, 0, 4)

    play  = PlayerButton("play",  "#00ff88", size=44)
    pause = PlayerButton("pause", "#f1c40f", size=44)
    stop  = PlayerButton("stop",  "#ff4444", size=44)
    play.setEnabled(False)
    pause.setEnabled(False)
    stop.setEnabled(False)

    setattr(app, f"btn_play_{suffix}",  play)
    setattr(app, f"btn_pause_{suffix}", pause)
    setattr(app, f"btn_stop_{suffix}",  stop)

    layout.addStretch()
    layout.addWidget(play)
    layout.addWidget(pause)
    layout.addWidget(stop)
    layout.addStretch()
    return layout


def make_time_slider(app, suffix, on_move):
    lbl = make_label("0.00 / 0.00 сек.", LBL_TIME)
    setattr(app, f"lbl_time_{suffix}", lbl)

    from PyQt6.QtWidgets import QSlider
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setStyleSheet(SLIDER_STYLE)
    slider.sliderMoved.connect(on_move)
    setattr(app, f"slider_{suffix}", slider)
    return lbl, slider


def make_bandpass_controls(app):
    container = QFrame()
    container.setStyleSheet(BOX_BANDPASS)
    main = QVBoxLayout(container)
    main.setSpacing(6)

    low_row = QHBoxLayout()
    low_row.addWidget(make_label("Минимум:", "color: #7ab3cc; font-size: 11px; border: none; min-width: 65px;"))
    app.lbl_bp_low = make_label("100 Hz", "color: #00d4ff; font-size: 11px; font-weight: bold; border: none; min-width: 65px;")
    app.lbl_bp_low.setAlignment(Qt.AlignmentFlag.AlignRight)
    low_row.addWidget(app.lbl_bp_low)
    main.addLayout(low_row)

    from PyQt6.QtWidgets import QSlider
    app.slider_bp_low = QSlider(Qt.Orientation.Horizontal)
    app.slider_bp_low.setRange(20, 10000)
    app.slider_bp_low.setValue(100)
    app.slider_bp_low.setStyleSheet(SLIDER_BP_LOW)
    app.slider_bp_low.valueChanged.connect(lambda v: app.lbl_bp_low.setText(f"{v} Hz"))
    main.addWidget(app.slider_bp_low)
    main.addSpacing(4)

    high_row = QHBoxLayout()
    high_row.addWidget(make_label("Максимум:", "color: #1abc9c; font-size: 11px; border: none; min-width: 65px;"))
    app.lbl_bp_high = make_label("4000 Hz", "color: #1abc9c; font-size: 11px; font-weight: bold; border: none; min-width: 65px;")
    app.lbl_bp_high.setAlignment(Qt.AlignmentFlag.AlignRight)
    high_row.addWidget(app.lbl_bp_high)
    main.addLayout(high_row)

    app.slider_bp_high = QSlider(Qt.Orientation.Horizontal)
    app.slider_bp_high.setRange(100, 20000)
    app.slider_bp_high.setValue(4000)
    app.slider_bp_high.setStyleSheet(SLIDER_BP_HIGH)
    app.slider_bp_high.valueChanged.connect(lambda v: app.lbl_bp_high.setText(f"{v} Hz"))
    main.addWidget(app.slider_bp_high)

    return container


# Re-export styles used by panels for convenience
__all__ = [
    "make_button", "make_label", "make_panel_title", "make_hint",
    "make_meta_box", "make_result_box", "make_player_row",
    "make_time_slider", "make_bandpass_controls",
    "LBL_SECTION", "LBL_SUBSECTION", "LBL_META", "TEXT_RESULT", "TEXT_PROBABILITIES",
]
