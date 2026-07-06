import os, sys, tempfile, matplotlib, numpy as np
import tensorflow as tf
import soundfile as sf
import librosa.display

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QEvent, QRect
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QFileDialog, QMessageBox, QGraphicsOpacityEffect
)
from PyQt6.QtGui import QFont, QCursor

from src.ui_titlebar import TitleBar
from src.animated_background import AnimatedBackground
from src.audio_player import AudioPlayer
from src.workers import AIAnalysisWorker, ComparisonWorker, ScalogramWorker
from src.audio_processing import (
    load_and_get_metadata, detect_gunshot_events, prepare_spectrogram_for_ai,
    mel_for_aligned_shot_display, build_same_source_report,
)
from src.styles import MATPLOTLIB_THEME, ACCENT, ACCENT_TEAL, STATUS_OK, STATUS_DANGER
from src.ui_sidebar import create_sidebar
from src.controllers import (
    handle_stop, reset_sliders_on_stop
)
from src.ui_ai_panel import build_analysis_ui
from src.ui_custom_panel import build_custom_ui
from src.ui_comparison_panel import build_comparison_ui
from src.custom_graphs import (
    MAX_SELECTED_GRAPHS, render_graph, render_scalogram, style_blank_axis,
)

MODEL_PATH = "./models/gunshot_cnn_model.h5"
LABELS_PATH = "./models/class_labels.txt"

class GunshotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интегрирана Система за Анализ на изстрели")
        self.showFullScreen()
        
        # Контрол на плеъра
        self.player = AudioPlayer(
            on_tick_callback=self.sync_sliders_on_tick,
            on_stop_callback=lambda: reset_sliders_on_stop(self)
        )
        
        self.current_file_path = None
        self.audio_data = None          
        self.raw_audio_data = None      
        self.sample_rate = None
        self.audio_duration = 0.0 

        self._applied_filters = []
        self._pulse_timer = None   
        
        self._ai_worker         = None
        self._comparison_worker = None
        self._scalogram_worker  = None
        self._scalogram_target_ax = None

        self._temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self.temp_output_path = self._temp_file.name
        self._temp_file.close()
        self.is_sidebar_expanded = True
        self.sidebar_width = 260
        
        self.slider_timer = QTimer()
        self.slider_timer.timeout.connect(lambda: self.player.update_tick(self.audio_duration))
        
        self.bg_dark = "#050d1a"
        self.bg_card = "#0a192fd9"
        self.accent = ACCENT
        self.accent2 = ACCENT_TEAL

        matplotlib.rcParams.update(MATPLOTLIB_THEME)

        self.load_model_and_labels()

        self.root_widget = QWidget(self)
        self.root_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.root_widget)

        self.bg_widget = AnimatedBackground(self.root_widget)
        self.bg_widget.lower()

        self.central_widget = QWidget(self.root_widget)
        self.central_widget.setStyleSheet("background: transparent;")

        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(70, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.create_content_area()

        self.dim_overlay = QWidget(self.root_widget)
        self.dim_overlay.setStyleSheet("background-color: black; border: none;")
        self.dim_effect = QGraphicsOpacityEffect(self.dim_overlay)
        self.dim_effect.setOpacity(0.45)
        self.dim_overlay.setGraphicsEffect(self.dim_effect)
        self.dim_overlay.mousePressEvent = lambda e: self.animate_sidebar()

        create_sidebar(self)
        self.sidebar_frame.setParent(self.root_widget)

        self.dim_overlay.raise_()
        self.sidebar_frame.raise_()

        self.title_bar = TitleBar(self.root_widget)
        self.title_bar.setGeometry(0, -40, self.width(), 40) # Начална позиция извън екрана
        self.title_bar.raise_() # Да е винаги най-отгоре

        self.mouse_tracker = QTimer(self)
        self.mouse_tracker.timeout.connect(self.check_mouse_position)
        self.mouse_tracker.start(100)
        
        self._update_overlay_geometry()
        self.root_widget.installEventFilter(self)

    def check_mouse_position(self):
        # Взимаме локалната позиция на мишката спрямо прозореца
        pos = self.mapFromGlobal(QCursor.pos())
        
        # Ако мишката е в горните 20 пиксела, покажи менюто
        if pos.y() <= 20 and 0 <= pos.x() <= self.width():
            self.title_bar.slide_in()
        # Ако мишката слезе под 45 пиксела (извън менюто), скрий го
        elif pos.y() > 45 or pos.x() < 0 or pos.x() > self.width():
            self.title_bar.slide_out()
    
    def load_model_and_labels(self):
        try:
            if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
                raise FileNotFoundError("Липсва моделът или файлът с етикети в папка ./models/")
            self.model = tf.keras.models.load_model(MODEL_PATH)
            self.embedding_model = tf.keras.Model(
                inputs=self.model.inputs,
                outputs=self.model.layers[-2].output,
            )
            self.class_labels = {}
            pretty_names = {
                "handgun": "Пистолет (Handgun)",
                "rifle": "Пушка (Rifle)",
                "shotgun": "Ловна пушка (Shotgun)",
                "automatic_submachine": "Автоматично оръжие (Submachine)",
                "other": "Други (Other)",
                "other_impulse": "Други импулсни (Other Impulse)"
            }

            with open(LABELS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and ":" in line:
                        idx, name = line.split(":")
                        raw_name = name.strip()
                        display_name = pretty_names.get(raw_name, raw_name)
                        self.class_labels[int(idx.strip())] = display_name
        except Exception as e:
            QMessageBox.critical(self, "Грешка при стартиране", f"Неуспешно зареждане на ИИ компоненти:\n{e}")
            sys.exit(1)

    def create_content_area(self):
        self.content_stack = QStackedWidget()
        build_analysis_ui(self)
        build_custom_ui(self)
        build_comparison_ui(self)
        self.main_layout.addWidget(self.content_stack)

    def _update_overlay_geometry(self):
        rect = self.root_widget.rect()
        self.bg_widget.setGeometry(rect)
        self.central_widget.setGeometry(rect)
        self.dim_overlay.setGeometry(70, 0, max(0, rect.width() - 70), rect.height())
        self.sidebar_frame.setGeometry(0, 0, self.sidebar_width, rect.height())

        if hasattr(self, 'title_bar'):
            if self.title_bar.is_visible:
                self.title_bar.setGeometry(0, 0, rect.width(), 40)
            else:
                self.title_bar.setGeometry(0, -40, rect.width(), 40)
    
    def load_evidence_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Зареди запис А", "", "Audio Files (*.wav *.mp3)"
        )
        if not file_path:
            return
        try:
            self.ev_audio, self.ev_sr, duration, _, _ = load_and_get_metadata(file_path)
            self.ev_path = file_path

            filename = os.path.basename(file_path)
            self.lbl_evidence_meta.setText(
                f"Файл: {filename}\n"
                f"Продължителност: {duration:.2f} сек.\n"
                f"Честота: {self.ev_sr} Hz"
            )
            self.ax_ev.clear()
            mel = mel_for_aligned_shot_display(self.ev_audio, self.ev_sr)
            librosa.display.specshow(
                mel, sr=44100, x_axis="time", y_axis="mel",
                ax=self.ax_ev, cmap="Reds",
            )
            self.ax_ev.set_title(
                "Подравнен изстрел #1 — Запис А", color="white", fontsize=10
            )
            self.canvas_ev.draw()
            self.execute_ballistic_comparison()
        except Exception as exc:
            QMessageBox.warning(
                self, "Грешка",
                f"Неуспешно зареждане на запис А:\n{exc}",
            )

    def load_reference_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Зареди запис Б", "", "Audio Files (*.wav *.mp3)"
        )
        if not file_path:
            return
        try:
            self.ref_audio, self.ref_sr, duration, _, _ = load_and_get_metadata(file_path)
            self.ref_path = file_path

            filename = os.path.basename(file_path)
            self.lbl_reference_meta.setText(
                f"Файл: {filename}\n"
                f"Продължителност: {duration:.2f} сек.\n"
                f"Честота: {self.ref_sr} Hz"
            )
            self.ax_ref.clear()
            mel = mel_for_aligned_shot_display(self.ref_audio, self.ref_sr)
            librosa.display.specshow(
                mel, sr=44100, x_axis="time", y_axis="mel",
                ax=self.ax_ref, cmap="Greens",
            )
            self.ax_ref.set_title(
                "Подравнен изстрел #1 — Запис Б", color="white", fontsize=10
            )
            self.canvas_ref.draw()
            self.execute_ballistic_comparison()
        except Exception as exc:
            QMessageBox.warning(
                self, "Грешка",
                f"Неуспешно зареждане на запис Б:\n{exc}",
            )

    def execute_ballistic_comparison(self):
        """Launch same-source comparison in background. Non-blocking."""
        if self.ev_audio is None or self.ref_audio is None:
            return

        if self._comparison_worker is not None and self._comparison_worker.isRunning():
            self._comparison_worker.finished.disconnect()
            self._comparison_worker.error.disconnect()

        self.text_analysis_results.setText("⠋ Извършва се сравнение на записите…")

        self._comparison_worker = ComparisonWorker(
            self.ev_audio.copy(),  self.ev_sr,
            self.ref_audio.copy(), self.ref_sr,
            embedding_model=self.embedding_model,
        )
        self._comparison_worker.finished.connect(self._on_comparison_done)
        self._comparison_worker.error.connect(self._on_comparison_error)
        self._comparison_worker.start()

    def _on_comparison_done(self, result):
        report = build_same_source_report(result)
        self.text_analysis_results.setText(report)

        mel_ev = result["mel_ev"]
        mel_ref = result["mel_ref"]
        composite = result["composite_score"]

        self.ax_comp.clear()
        librosa.display.specshow(
            mel_ev, sr=44100, x_axis="time", y_axis="mel",
            ax=self.ax_comp, cmap="Reds", alpha=0.6,
        )
        librosa.display.specshow(
            mel_ref, sr=44100, x_axis="time", y_axis="mel",
            ax=self.ax_comp, cmap="Greens", alpha=0.4,
        )
        self.ax_comp.set_title(
            f"Подравнени изстрели (Червено: А | Зелено: Б)"
            f" • Обобщена оценка: {composite:.1f}%",
            color="white", fontsize=11,
        )
        self.canvas_comp.draw()
 
    def _on_comparison_error(self, error_msg: str):
        self.text_analysis_results.setText(f"❌ Грешка при анализ:\n{error_msg}")

    def setup_blank_plots(self, ax1, ax2, t1, t2):
        for ax, title in zip([ax1, ax2], [t1, t2]):
            ax.clear()
            ax.set_facecolor('#050d1a')
            ax.grid(True, alpha=0.2, color='#00d4ff', linestyle='--')
            for spine in ax.spines.values():
                spine.set_edgecolor('#00d4ff')
                spine.set_alpha(0.3)
            ax.set_title(title, color='white', fontsize=10, fontweight='bold')
            ax.tick_params(colors='white', labelsize=8)
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
        if hasattr(self, 'fig_cust'): self.fig_cust.tight_layout()
        if hasattr(self, 'fig_ai'): self.fig_ai.tight_layout()

    def setup_blank_custom_plots(self):
        """Empty custom panel plots — no graph selected."""
        style_blank_axis(
            self.ax1_cust, "Графика 1",
            hint="Изберете графика от бутоните по-горе",
        )
        style_blank_axis(
            self.ax2_cust, "Графика 2",
            hint="Можете да изберете до 2 едновременно",
        )
        self.fig_cust.tight_layout(pad=1)
        self.canvas_cust.draw()

    def _update_graph_hint_label(self):
        if not hasattr(self, "lbl_graph_hint"):
            return
        n = len(self.selected_graphs)
        if n == 0:
            self.lbl_graph_hint.setText(
                f"Няма избрани графики — изберете до {MAX_SELECTED_GRAPHS}."
            )
        elif n == 1:
            self.lbl_graph_hint.setText("Избрана 1 графика — можете да добавите още 1.")
        else:
            self.lbl_graph_hint.setText("Избрани 2 графики — максимум достигнат.")

    def toggle_graph_mode(self, mode_id: str, checked: bool):
        if checked:
            if mode_id not in self.selected_graphs:
                if len(self.selected_graphs) >= MAX_SELECTED_GRAPHS:
                    oldest = self.selected_graphs.pop(0)
                    old_btn = self.graph_mode_buttons[oldest]
                    old_btn.blockSignals(True)
                    old_btn.setChecked(False)
                    old_btn.blockSignals(False)
                self.selected_graphs.append(mode_id)
        else:
            if mode_id in self.selected_graphs:
                self.selected_graphs.remove(mode_id)

        self._update_graph_hint_label()
        if self.audio_data is not None:
            self.draw_plots()
        elif not self.selected_graphs:
            self.setup_blank_custom_plots()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Зареди Балистичен Запис", "", "Audio Files (*.wav)")
        if not file_path: return
        
        self.current_file_path = file_path
        handle_stop(self)
        
        self.raw_audio_data, self.sample_rate, self.audio_duration, _, _ = load_and_get_metadata(file_path)
        self.audio_data = self.raw_audio_data.copy()
        
        for slider in [self.slider_ai, self.slider_cust]:
            slider.setRange(0, int(self.audio_duration * 1000))
        
        self.btn_play_ai.setEnabled(True)
        self.btn_play_cust.setEnabled(True)
        self.btn_save_audio.setEnabled(True)
        
        self.update_audio_environment()
        self.run_ai_classification()

    def update_audio_environment(self):
        if self.audio_data is None: return
        
        peak_amp = np.max(np.abs(self.audio_data))
        clipping_warn = "Има клипинг!" if peak_amp >= 0.98 else "Няма клипинг"
        clipping_color = STATUS_DANGER if peak_amp >= 0.98 else STATUS_OK
        
        self.lbl_duration.setText(f"Продължителност: {self.audio_duration:.4f} сек.")
        self.lbl_sr.setText(f"Честота на дискретизация: {self.sample_rate} Hz")
        self.lbl_peak.setText(f"Макс. амплитуда: {peak_amp:.4f} -> {clipping_warn}")
        self.lbl_peak.setStyleSheet(f"color: {clipping_color}; border:none;")
        
        sf.write(self.temp_output_path, self.audio_data, self.sample_rate)
        self.draw_plots()

    def _pulse_ai_label(self):
        self.lbl_class.setStyleSheet(
            "color: #00d4ff; font-size: 16px; font-weight: bold; border:none;"
        )
        self._pulse_phase = 0
        frames = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]
 
        def tick():
            self._pulse_phase += 1
            self.lbl_class.setText(
                f"{frames[self._pulse_phase % len(frames)]} АНАЛИЗИРА СЕ…"
            )
 
        if self._pulse_timer is None:
            self._pulse_timer = QTimer()
        else:
            self._pulse_timer.stop()
            try:
                self._pulse_timer.timeout.disconnect()
            except RuntimeError:
                pass  # no connections
 
        self._pulse_timer.timeout.connect(tick)
        self._pulse_timer.start(120)
    
    def _update_classification_labels(self, predictions):
        max_idx = np.argmax(predictions)
        confidence = predictions[max_idx] * 100
        class_name = self.class_labels.get(max_idx, f"Клас {max_idx}")

        if confidence < 50.0:
            self.lbl_class.setText("Идентифициран клас:\n Неопределен")
            self.lbl_conf.setText(f"Вероятност: {confidence:.2f}% (недостатъчна)")
            self.lbl_class.setStyleSheet("color: #e74c3c; font-size: 16px; font-weight: bold; border:none;")
        else:
            self.lbl_class.setText(f"Идентифициран клас:\n {class_name}")
            self.lbl_conf.setText(f"Вероятност / Точност: {confidence:.2f}%")
            self.lbl_class.setStyleSheet("color: #2ecc71; font-size: 16px; font-weight: bold; border:none;")

        prob_text = "Разпределение на вероятностите:\n" + "-" * 30 + "\n"
        sorted_preds = sorted(enumerate(predictions), key=lambda x: x[1], reverse=True)
        for idx, prob in sorted_preds:
            label = self.class_labels.get(idx, f"Клас {idx}")
            bar = "█" * int(prob * 20)
            prob_text += f"{label:<22} {prob*100:5.1f}% {bar}\n"

        return prob_text

    def _draw_ai_plots(self, log_mel_fixed, target_sr, detected_times):
        self.setup_blank_plots(self.ax1_ai, self.ax2_ai, "Времеви профил на записа", "Mel-Спектрограма (AI Анализ)")
        librosa.display.waveshow(self.raw_audio_data, sr=self.sample_rate, ax=self.ax1_ai, color='#1abc9c')

        for t in detected_times:
            self.ax1_ai.axvline(x=t, color='#e74c3c', linestyle='--', linewidth=1.5, alpha=0.8)

        librosa.display.specshow(log_mel_fixed, sr=target_sr, x_axis='time', y_axis='mel', ax=self.ax2_ai, cmap='viridis')

        self.fig_ai.tight_layout(pad=1)
        self.canvas_ai.draw()
    
    def run_ai_classification(self):
        """Launch AI pipeline in background. Non-blocking — UI stays live."""
        # If a previous worker is still running, sever its signal connections
        # so stale results are silently discarded.
        if self._ai_worker is not None and self._ai_worker.isRunning():
            self._ai_worker.finished.disconnect()
            self._ai_worker.error.disconnect()
 
        self._pulse_ai_label()
        # Disable browse buttons while analysis runs
        self.btn_browse_ai.setEnabled(False)
        self.btn_browse_cust.setEnabled(False)
 
        self._ai_worker = AIAnalysisWorker(
            self.raw_audio_data.copy(),  # copy → no race with filter ops
            self.sample_rate,
            self.model,
        )
        self._ai_worker.finished.connect(self._on_ai_done)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()
 
    def _on_ai_done(
        self,
        predictions,
        log_mel_fixed,
        target_sr: float,
        detected_times,
        multishot_report: str,
    ):
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
 
        prob_text = self._update_classification_labels(predictions)
        self.lbl_events.setText(f"Засечени изстрели: {len(detected_times)}")
        if multishot_report:
            prob_text += multishot_report
        self.txt_probabilities.setText(prob_text)
 
        self._draw_ai_plots(log_mel_fixed, target_sr, detected_times)
 
        self.btn_browse_ai.setEnabled(True)
        self.btn_browse_cust.setEnabled(True)
 
    def _on_ai_error(self, error_msg: str):
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
        self.lbl_class.setText("Грешка при AI анализ")
        self.lbl_conf.setText(error_msg)
        self.btn_browse_ai.setEnabled(True)
        self.btn_browse_cust.setEnabled(True)

    def draw_plots(self):
        if self.audio_data is None:
            return

        detected_times, rms_frames, hop_length = detect_gunshot_events(
            self.audio_data, self.sample_rate
        )
        if hasattr(self, "lbl_events"):
            self.lbl_events.setText(f"Засечени изстрели: {len(detected_times)}")

        axes = [self.ax1_cust, self.ax2_cust]

        if not self.selected_graphs:
            self.setup_blank_custom_plots()
            return

        if self._scalogram_worker is not None and self._scalogram_worker.isRunning():
            self._scalogram_worker.finished.disconnect()
            self._scalogram_worker.error.disconnect()

        scalogram_ax = None
        for i, ax in enumerate(axes):
            if i < len(self.selected_graphs):
                mode = self.selected_graphs[i]
                if mode == "scalogram":
                    scalogram_ax = ax
                render_graph(
                    ax, mode, self.audio_data, self.sample_rate,
                    detected_times, rms_frames, hop_length,
                )
            else:
                style_blank_axis(
                    ax, f"Графика {i + 1}",
                    hint="Изберете втори тип графика" if len(self.selected_graphs) == 1 else None,
                )

        if scalogram_ax is not None:
            self._scalogram_target_ax = scalogram_ax
            self.fig_cust.tight_layout(pad=1)
            self.canvas_cust.draw()

            self._scalogram_worker = ScalogramWorker(
                self.audio_data.copy(), self.sample_rate
            )
            self._scalogram_worker.finished.connect(self._on_scalogram_done)
            self._scalogram_worker.error.connect(self._on_scalogram_error)
            self._scalogram_worker.start()
            return

        self.fig_cust.tight_layout(pad=1)
        self.canvas_cust.draw()

    def _on_scalogram_done(self, scalogram, freqs, duration: float):
        ax = self._scalogram_target_ax or self.ax2_cust
        render_scalogram(ax, scalogram, freqs, duration)
        self.fig_cust.tight_layout(pad=1)
        self.canvas_cust.draw()

    def _on_scalogram_error(self, error_msg: str):
        ax = self._scalogram_target_ax or self.ax2_cust
        style_blank_axis(ax, "Scalogram (CWT)")
        ax.text(
            0.5, 0.5, f"❌ Грешка при скалограма:\n{error_msg}",
            color="#e74c3c", ha="center", va="center",
            transform=ax.transAxes, fontsize=11,
        )
        self.canvas_cust.draw()

    def sync_sliders_on_tick(self, current_pos):
        self.slider_ai.blockSignals(True)
        self.slider_cust.blockSignals(True)
        self.slider_ai.setValue(int(current_pos * 1000))
        self.slider_cust.setValue(int(current_pos * 1000))
        self.slider_ai.blockSignals(False)
        self.slider_cust.blockSignals(False)
        
        lbl_str = f"{current_pos:.2f} / {self.audio_duration:.2f} сек."
        self.lbl_time_ai.setText(lbl_str)
        self.lbl_time_cust.setText(lbl_str)

    def switch_screen(self, index):
        for i, btn in enumerate(self.menu_buttons): 
            btn.setChecked(i == index)
        self.content_stack.setCurrentIndex(index)
        QApplication.processEvents()

        if index == 0 and hasattr(self, 'canvas_ai'):
            self.fig_ai.tight_layout(pad=1)
            self.canvas_ai.draw()
        elif index == 1 and hasattr(self, 'canvas_cust'):
            self.fig_cust.tight_layout(pad=1)
            self.canvas_cust.draw()

        handle_stop(self)

    def animate_sidebar(self):
        target_width = 70 if self.is_sidebar_expanded else 260
        target_dim = 0.0 if self.is_sidebar_expanded else 0.45

        if self.is_sidebar_expanded:
            self.lbl_logo.hide()
            for btn in self.menu_buttons:
                btn.set_compact(True)
            self.lbl_version.hide()
            self.dim_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        else:
            self.lbl_logo.show()
            for btn in self.menu_buttons:
                btn.set_compact(False)
            self.lbl_version.show()
            self.dim_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        current_geo = self.sidebar_frame.geometry()
        target_geo = QRect(0, 0, target_width, self.root_widget.height())

        self.sidebar_animation = QPropertyAnimation(self.sidebar_frame, b"geometry", self)
        self.sidebar_animation.setDuration(220)
        self.sidebar_animation.setStartValue(current_geo)
        self.sidebar_animation.setEndValue(target_geo)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.sidebar_animation.start()

        self.dim_animation = QPropertyAnimation(self.dim_effect, b"opacity", self)
        self.dim_animation.setDuration(220)
        self.dim_animation.setStartValue(self.dim_effect.opacity())
        self.dim_animation.setEndValue(target_dim)
        self.dim_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.dim_animation.start()

        self.sidebar_width = target_width
        self.is_sidebar_expanded = not self.is_sidebar_expanded

    def eventFilter(self, obj, event):
        if obj == self.root_widget and event.type() == QEvent.Type.Resize:
            self._update_overlay_geometry()
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event):
        try:
            self.player.stop()
            # Cleanly stop background workers before exit
            for worker in (
                self._ai_worker,
                self._comparison_worker,
                self._scalogram_worker,
            ):
                if worker is not None and worker.isRunning():
                    worker.quit()
                    worker.wait(2000)   # up to 2 s per worker
            if os.path.exists(self.temp_output_path):
                os.remove(self.temp_output_path)
        except Exception:
            pass
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

def start_integrated_app():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = GunshotApp()
    window.show()
    sys.exit(app.exec())