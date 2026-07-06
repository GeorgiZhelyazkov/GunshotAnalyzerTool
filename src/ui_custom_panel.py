from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from src.custom_graphs import GRAPH_OPTIONS, MAX_SELECTED_GRAPHS
from src.ui_common import (
    make_button, make_label, make_panel_title, make_player_row,
    make_time_slider, make_meta_box, make_bandpass_controls,
    LBL_SECTION, LBL_SUBSECTION, LBL_META,
)
from src.styles import CARD_STYLE, STATUS_OK, TEXT_HINT
from src.controllers import (
    handle_play, handle_pause, handle_stop, handle_slider_move,
    filter_muzzle_blast, filter_sonic_crack, apply_custom_bandpass,
    apply_shot_gate, reset_audio, save_processed_audio,
)


def build_custom_ui(app):
    page = QWidget()
    main_h_layout = QHBoxLayout(page)
    main_h_layout.setContentsMargins(20, 20, 20, 20)
    main_h_layout.setSpacing(20)

    left_panel = QFrame()
    left_panel.setStyleSheet(CARD_STYLE)
    left_v_layout = QVBoxLayout(left_panel)
    left_v_layout.setSpacing(10)

    left_v_layout.addWidget(make_panel_title("РЪЧЕН АНАЛИЗ"))

    app.btn_browse_cust = make_button("📁 Зареди аудио файл (.wav)", "primary")
    app.btn_browse_cust.clicked.connect(app.browse_file)
    left_v_layout.addWidget(app.btn_browse_cust)

    left_v_layout.addLayout(make_player_row(app, "cust"))
    app.btn_play_cust.clicked.connect(lambda: handle_play(app))
    app.btn_pause_cust.clicked.connect(lambda: handle_pause(app))
    app.btn_stop_cust.clicked.connect(lambda: handle_stop(app))

    lbl_time, slider = make_time_slider(app, "cust", lambda pos: handle_slider_move(app, pos))
    left_v_layout.addWidget(lbl_time)
    left_v_layout.addWidget(slider)

    app.lbl_duration = make_label("Продължителност: --", LBL_META)
    app.lbl_sr = make_label("Честота на дискретизация: --", LBL_META)
    app.lbl_peak = make_label("Пикова амплитуда: --", LBL_META)
    left_v_layout.addWidget(make_meta_box([app.lbl_duration, app.lbl_sr, app.lbl_peak]))

    app.lbl_filter_status = make_label(
        "Активни филтри: няма (оригинален сигнал)",
        f"color: {STATUS_OK}; font-size: 10px; border: none; padding: 2px 0;",
    )
    app.lbl_filter_status.setWordWrap(True)
    left_v_layout.addWidget(app.lbl_filter_status)

    left_v_layout.addWidget(make_label("Изолиране на компоненти на изстрела:", LBL_SECTION))

    btn_muzzle = make_button("Изолирай Muzzle Blast (< 500 Hz)", "warn")
    btn_muzzle.clicked.connect(lambda: filter_muzzle_blast(app))
    left_v_layout.addWidget(btn_muzzle)

    btn_sonic = make_button("Изолирай Sonic Crack (> 1200 Hz)", "warn")
    btn_sonic.clicked.connect(lambda: filter_sonic_crack(app))
    left_v_layout.addWidget(btn_sonic)

    left_v_layout.addWidget(make_label("Персонализиран Честотен Обхват (Band-Pass):", LBL_SUBSECTION))
    left_v_layout.addWidget(make_bandpass_controls(app))

    btn_bandpass = make_button("Приложи Специфичен Обхват", "secondary")
    btn_bandpass.clicked.connect(lambda: apply_custom_bandpass(app))
    left_v_layout.addWidget(btn_bandpass)

    btn_gate = make_button("Автоматично изолиране на изстрел", "success")
    btn_gate.clicked.connect(lambda: apply_shot_gate(app))
    left_v_layout.addWidget(btn_gate)

    btn_reset = make_button("↺  Нулирай всички промени", "neutral")
    btn_reset.clicked.connect(lambda: reset_audio(app))
    left_v_layout.addWidget(btn_reset)

    app.btn_save_audio = make_button("💾 Запази обработения запис...", "save")
    app.btn_save_audio.setEnabled(False)
    app.btn_save_audio.clicked.connect(lambda: save_processed_audio(app))
    left_v_layout.addWidget(app.btn_save_audio)
    left_v_layout.addStretch()

    right_panel = QFrame()
    right_panel.setStyleSheet(CARD_STYLE)
    right_layout = QVBoxLayout(right_panel)

    right_layout.addWidget(make_label("Графики (изберете до 2):", LBL_SECTION))

    app.graph_mode_buttons = {}
    app.selected_graphs = []

    btn_row_1 = QHBoxLayout()
    btn_row_2 = QHBoxLayout()
    for i, (mode_id, label) in enumerate(GRAPH_OPTIONS):
        btn = make_button(label, "toggle", checkable=True)
        btn.toggled.connect(lambda checked, m=mode_id: app.toggle_graph_mode(m, checked))
        app.graph_mode_buttons[mode_id] = btn
        (btn_row_1 if i < 3 else btn_row_2).addWidget(btn)

    right_layout.addLayout(btn_row_1)
    right_layout.addLayout(btn_row_2)

    app.lbl_graph_hint = make_label(
        f"Няма избрани графики — изберете до {MAX_SELECTED_GRAPHS}.",
        f"color: {TEXT_HINT}; font-size: 11px; border: none;",
    )
    right_layout.addWidget(app.lbl_graph_hint)

    app.fig_cust, (app.ax1_cust, app.ax2_cust) = plt.subplots(2, 1, figsize=(6, 6))
    app.fig_cust.patch.set_facecolor("none")
    app.canvas_cust = FigureCanvas(app.fig_cust)
    right_layout.addWidget(app.canvas_cust)

    app.setup_blank_custom_plots()

    main_h_layout.addWidget(left_panel, stretch=1)
    main_h_layout.addWidget(right_panel, stretch=3)
    app.content_stack.addWidget(page)
