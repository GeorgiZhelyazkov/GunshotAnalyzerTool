from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTextEdit
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from src.ui_common import (
    make_button, make_panel_title, make_player_row, make_result_box,
    make_time_slider, TEXT_PROBABILITIES,
)
from src.styles import CARD_STYLE, LBL_BODY
from src.controllers import (
    handle_play, handle_pause, handle_stop, handle_slider_move,
    save_ai_analysis,
)


def build_analysis_ui(app):
    page = QWidget()
    main_h_layout = QHBoxLayout(page)
    main_h_layout.setContentsMargins(20, 20, 20, 20)
    main_h_layout.setSpacing(20)

    left_panel = QFrame()
    left_panel.setStyleSheet(CARD_STYLE)
    left_v_layout = QVBoxLayout(left_panel)
    left_v_layout.setSpacing(20)

    left_v_layout.addWidget(make_panel_title("АВТОМАТИЧЕН АНАЛИЗ"))

    app.btn_browse_ai = make_button("📁 Зареди аудио файл (.wav)", "primary")
    app.btn_browse_ai.clicked.connect(app.browse_file)
    left_v_layout.addWidget(app.btn_browse_ai)

    left_v_layout.addLayout(make_player_row(app, "ai"))
    app.btn_play_ai.clicked.connect(lambda: handle_play(app))
    app.btn_pause_ai.clicked.connect(lambda: handle_pause(app))
    app.btn_stop_ai.clicked.connect(lambda: handle_stop(app))

    lbl_time, slider = make_time_slider(app, "ai", lambda pos: handle_slider_move(app, pos))
    left_v_layout.addWidget(lbl_time)
    left_v_layout.addWidget(slider)

    from PyQt6.QtCore import Qt
    from src.ui_common import make_label

    app.lbl_class = make_label("Идентифициран клас:\n--", "color: white; font-size: 16px; font-weight: bold; border: none;")
    app.lbl_class.setAlignment(Qt.AlignmentFlag.AlignCenter)
    app.lbl_conf = make_label("Точност: --", LBL_BODY)
    app.lbl_events = make_label("Засечени изстрели: --", LBL_BODY)

    app.txt_probabilities = QTextEdit()
    app.txt_probabilities.setReadOnly(True)
    app.txt_probabilities.setFixedHeight(130)
    app.txt_probabilities.setStyleSheet(TEXT_PROBABILITIES)

    left_v_layout.addWidget(make_result_box(app.lbl_class, app.lbl_conf, app.lbl_events, app.txt_probabilities))

    app.btn_save_ai_report = make_button("📄 Запази анализа (.txt)...", "save")
    app.btn_save_ai_report.clicked.connect(lambda: save_ai_analysis(app))
    left_v_layout.addWidget(app.btn_save_ai_report)
    left_v_layout.addStretch()

    right_panel = QFrame()
    right_panel.setStyleSheet(CARD_STYLE)
    right_layout = QVBoxLayout(right_panel)

    app.fig_ai, (app.ax1_ai, app.ax2_ai) = plt.subplots(2, 1, figsize=(6, 6))
    app.fig_ai.patch.set_facecolor("none")
    app.canvas_ai = FigureCanvas(app.fig_ai)
    right_layout.addWidget(app.canvas_ai)

    app.setup_blank_plots(
        app.ax1_ai, app.ax2_ai,
        "Времеви профил на записа", "Mel-Спектрограма",
    )

    main_h_layout.addWidget(left_panel, stretch=1)
    main_h_layout.addWidget(right_panel, stretch=3)
    app.content_stack.addWidget(page)
