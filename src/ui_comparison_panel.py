from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTextEdit
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from src.ui_common import make_button, make_hint, make_label, TEXT_RESULT
from src.styles import CARD_STYLE, LBL_META, RECORD_A, RECORD_B
from src.controllers import save_comparison_analysis


def build_comparison_ui(app):
    page = QWidget()
    main_v_layout = QVBoxLayout(page)
    main_v_layout.setContentsMargins(20, 20, 20, 20)
    main_v_layout.setSpacing(15)

    panels_layout = QHBoxLayout()
    panels_layout.setSpacing(20)

    app.evidence_frame = QFrame()
    app.evidence_frame.setStyleSheet(CARD_STYLE)
    evidence_layout = QVBoxLayout(app.evidence_frame)

    evidence_layout.addWidget(make_label(
        "ЗАПИС А (напр. CCTV / далечен микрофон)",
        f"color: {RECORD_A}; font-size: 15px; font-weight: bold;"
        " border: none; qproperty-alignment: 'AlignCenter';",
        align_center=True,
    ))
    evidence_layout.addWidget(make_hint("Първи подравнен изстрел — спектрална визуализация"))

    app.btn_load_evidence = make_button("Зареди запис А", "primary")
    app.btn_load_evidence.clicked.connect(app.load_evidence_file)
    evidence_layout.addWidget(app.btn_load_evidence)

    app.lbl_evidence_meta = make_label("Файл: Не е зареден\nПродължителност: ---\nЧестота: ---", LBL_META)
    evidence_layout.addWidget(app.lbl_evidence_meta)

    app.fig_ev, app.ax_ev = plt.subplots(figsize=(5, 2.5))
    app.fig_ev.patch.set_facecolor("none")
    app.ax_ev.set_facecolor("none")
    app.ax_ev.tick_params(colors="white")
    app.canvas_ev = FigureCanvas(app.fig_ev)
    evidence_layout.addWidget(app.canvas_ev)
    panels_layout.addWidget(app.evidence_frame)

    app.reference_frame = QFrame()
    app.reference_frame.setStyleSheet(CARD_STYLE)
    reference_layout = QVBoxLayout(app.reference_frame)

    reference_layout.addWidget(make_label(
        "ЗАПИС Б (напр. телефон / близък микрофон)",
        f"color: {RECORD_B}; font-size: 15px; font-weight: bold;"
        " border: none; qproperty-alignment: 'AlignCenter';",
        align_center=True,
    ))
    reference_layout.addWidget(make_hint("Първи подравнен изстрел — спектрална визуализация"))

    app.btn_load_reference = make_button("Зареди запис Б", "success")
    app.btn_load_reference.clicked.connect(app.load_reference_file)
    reference_layout.addWidget(app.btn_load_reference)

    app.lbl_reference_meta = make_label("Файл: Не е зареден\nПродължителност: ---\nЧестота: ---", LBL_META)
    reference_layout.addWidget(app.lbl_reference_meta)

    app.fig_ref, app.ax_ref = plt.subplots(figsize=(5, 2.5))
    app.fig_ref.patch.set_facecolor("none")
    app.ax_ref.set_facecolor("none")
    app.ax_ref.tick_params(colors="white")
    app.canvas_ref = FigureCanvas(app.fig_ref)
    reference_layout.addWidget(app.canvas_ref)
    panels_layout.addWidget(app.reference_frame)

    main_v_layout.addLayout(panels_layout)

    app.result_frame = QFrame()
    app.result_frame.setStyleSheet(CARD_STYLE)
    result_layout = QHBoxLayout(app.result_frame)

    app.text_analysis_results = QTextEdit()
    app.text_analysis_results.setReadOnly(True)
    app.text_analysis_results.setFixedWidth(400)
    app.text_analysis_results.setStyleSheet(TEXT_RESULT)
    app.text_analysis_results.setText(
        "Заредете двата записа за проверка..."
    )
    result_layout.addWidget(app.text_analysis_results)

    app.fig_comp, app.ax_comp = plt.subplots(figsize=(7, 3))
    app.fig_comp.patch.set_facecolor("none")
    app.ax_comp.set_facecolor("none")
    app.ax_comp.tick_params(colors="white")
    app.canvas_comp = FigureCanvas(app.fig_comp)
    result_layout.addWidget(app.canvas_comp)
    main_v_layout.addWidget(app.result_frame)

    app.btn_save_comparison = make_button("📄 Запази сравнителния доклад (.txt)...", "save", fixed_width=400)
    app.btn_save_comparison.clicked.connect(lambda: save_comparison_analysis(app))
    main_v_layout.addWidget(app.btn_save_comparison)

    app.content_stack.addWidget(page)

    app.ev_audio, app.ev_sr, app.ev_path = None, None, None
    app.ref_audio, app.ref_sr, app.ref_path = None, None, None
