import os
import datetime

import librosa
import soundfile as sf
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from src.audio_processing import (
    apply_muzzle_blast_filter, apply_sonic_crack_filter,
    apply_custom_bandpass_filter, apply_ballistic_shot_gate,
)


def _set_player_visual_state(app, state: str):
    """state: 'stopped' | 'playing' | 'paused'"""
    for suffix in ("ai", "cust"):
        play  = getattr(app, f"btn_play_{suffix}")
        pause = getattr(app, f"btn_pause_{suffix}")
        play.set_active(state == "playing")
        pause.set_active(state == "paused")


def handle_play(app):
    if not app.current_file_path:
        return
    target = app.temp_output_path if os.path.exists(app.temp_output_path) else app.current_file_path
    app.player.play(target)
    for btn in [app.btn_play_ai, app.btn_play_cust]:
        btn.setEnabled(False)
    for btn in [app.btn_pause_ai, app.btn_pause_cust]:
        btn.setEnabled(True)
    for btn in [app.btn_stop_ai, app.btn_stop_cust]:
        btn.setEnabled(True)
    _set_player_visual_state(app, "playing")
    app.slider_timer.start(50)


def handle_pause(app):
    app.player.pause()
    app.slider_timer.stop()
    for btn in [app.btn_play_ai, app.btn_play_cust]:
        btn.setEnabled(True)
    for btn in [app.btn_pause_ai, app.btn_pause_cust]:
        btn.setEnabled(False)
    _set_player_visual_state(app, "paused")


def handle_stop(app):
    app.player.stop()


def handle_slider_move(app, position):
    if not app.current_file_path:
        return
    new_time = position / 1000.0
    target = app.temp_output_path if os.path.exists(app.temp_output_path) else app.current_file_path
    app.player.set_position(target, new_time)
    lbl_str = f"{new_time:.2f} / {app.audio_duration:.2f} сек."
    app.lbl_time_ai.setText(lbl_str)
    app.lbl_time_cust.setText(lbl_str)


def reset_sliders_on_stop(app):
    app.slider_timer.stop()
    for btn in [app.btn_play_ai, app.btn_play_cust]:
        btn.setEnabled(True)
    for btn in [app.btn_pause_ai, app.btn_pause_cust]:
        btn.setEnabled(False)
    for btn in [app.btn_stop_ai, app.btn_stop_cust]:
        btn.setEnabled(False)
    _set_player_visual_state(app, "stopped")
    app.slider_ai.setValue(0)
    app.slider_cust.setValue(0)
    lbl_str = f"0.00 / {app.audio_duration:.2f} сек."
    app.lbl_time_ai.setText(lbl_str)
    app.lbl_time_cust.setText(lbl_str)

def _update_filter_status_label(app):
    """Refreshes the small status label that shows the current filter chain."""
    if not hasattr(app, 'lbl_filter_status'):
        return
    if app._applied_filters:
        app.lbl_filter_status.setText(
            f"Активни филтри: {' → '.join(app._applied_filters)}"
        )
        app.lbl_filter_status.setStyleSheet(
            "color: #ff9900; font-size: 12px; border: none; padding: 2px 0;"
        )
    else:
        app.lbl_filter_status.setText("Активни филтри: няма (оригинален сигнал)")
        app.lbl_filter_status.setStyleSheet(
            "color: #2ecc71; font-size: 10px; border: none; padding: 2px 0;"
        )


def _check_destructive_stacking(app, new_filter_key):
    muzzle_applied = any("Muzzle Blast" in f for f in app._applied_filters)
    sonic_applied  = any("Sonic Crack"  in f for f in app._applied_filters)

    if new_filter_key == "sonic_crack" and muzzle_applied:
        reply = QMessageBox.warning(
            app,
            "⚠ Акустично противоречие",
            "Вече е приложен Muzzle Blast (< 500 Hz).\n"
            "В аудиото не са останали честоти над 500 Hz.\n\n"
            "Прилагането на Sonic Crack (> 1200 Hz) ще доведе до\n"
            "почти пълна тишина — резултатът е безсмислен.\n\n"
            f"Текуща история: {' → '.join(app._applied_filters)}\n\n"
            "Натиснете 'Нулирай' за да работите върху оригинала.\n"
            "Продължаване все пак?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    if new_filter_key == "muzzle_blast" and sonic_applied:
        reply = QMessageBox.warning(
            app,
            "⚠ Акустично противоречие",
            "Вече е приложен Sonic Crack (> 1200 Hz).\n"
            "В аудиото не са останали честоти под 1200 Hz.\n\n"
            "Прилагането на Muzzle Blast (< 500 Hz) ще доведе до\n"
            "почти пълна тишина — резултатът е безсмислен.\n\n"
            f"Текуща история: {' → '.join(app._applied_filters)}\n\n"
            "Натиснете 'Нулирай' за да работите върху оригинала.\n"
            "Продължаване все пак?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    return True

def filter_muzzle_blast(app):
    if app.audio_data is None:
        return
    if not _check_destructive_stacking(app, "muzzle_blast"):
        return
    app.player.stop()
    app.audio_data = apply_muzzle_blast_filter(app.audio_data, app.sample_rate)
    app._applied_filters.append("Muzzle Blast (<500Hz)")
    _update_filter_status_label(app)
    app.update_audio_environment()
    QMessageBox.information(app, "Балистичен Анализ", "Изолиран е Muzzle Blast (< 500 Hz).")


def filter_sonic_crack(app):
    if app.audio_data is None:
        return
    if not _check_destructive_stacking(app, "sonic_crack"):
        return
    app.player.stop()
    app.audio_data = apply_sonic_crack_filter(app.audio_data, app.sample_rate)
    app._applied_filters.append("Sonic Crack (>1200Hz)")
    _update_filter_status_label(app)
    app.update_audio_environment()
    QMessageBox.information(app, "Балистичен Анализ", "Изолиран е Sonic Crack (> 1200 Hz).")


def apply_custom_bandpass(app):
    if app.audio_data is None:
        return
    low  = float(app.slider_bp_low.value())
    high = float(app.slider_bp_high.value())
    if low >= high:
        QMessageBox.warning(
            app, "Грешка в обхвата",
            f"Минималната честота ({low:.0f} Hz) трябва да бъде "
            f"по-малка от максималната ({high:.0f} Hz)!",
        )
        return
    if not _check_destructive_stacking(app, "bandpass"):
        return
    app.player.stop()
    app.audio_data = apply_custom_bandpass_filter(app.audio_data, app.sample_rate, low, high)
    app._applied_filters.append(f"BandPass({low:.0f}-{high:.0f}Hz)")
    _update_filter_status_label(app)
    app.update_audio_environment()
    QMessageBox.information(app, "Балистичен Анализ",
                            f"Честотен филтър: {low:.0f} Hz – {high:.0f} Hz.")


def apply_shot_gate(app):
    if app.audio_data is None:
        return
    if not _check_destructive_stacking(app, "shot_gate"):
        return
    app.player.stop()
    app.audio_data = apply_ballistic_shot_gate(app.audio_data, app.sample_rate)
    app.audio_duration = librosa.get_duration(y=app.audio_data, sr=app.sample_rate)
    for slider in [app.slider_ai, app.slider_cust]:
        slider.setRange(0, int(app.audio_duration * 1000))
    app._applied_filters.append("Shot Gate")
    _update_filter_status_label(app)
    app.update_audio_environment()
    QMessageBox.information(app, "Успех", "Фоновият шум беше изрязан.")


def reset_audio(app):
    if app.raw_audio_data is None:
        return
    app.player.stop()
    app.audio_data = app.raw_audio_data.copy()
    app.audio_duration = librosa.get_duration(y=app.audio_data, sr=app.sample_rate)
    for slider in [app.slider_ai, app.slider_cust]:
        slider.setRange(0, int(app.audio_duration * 1000))
    app._applied_filters.clear()
    _update_filter_status_label(app)
    app.update_audio_environment()


def save_processed_audio(app):
    if app.audio_data is None:
        return
    save_path, _ = QFileDialog.getSaveFileName(app, "Запази аудио", "", "WAV Files (*.wav)")
    if save_path:
        if not save_path.lower().endswith(".wav"):
            save_path += ".wav"
        sf.write(save_path, app.audio_data, app.sample_rate)
        QMessageBox.information(app, "Успешен запис", f"Файлът е съхранен в:\n{save_path}")

def save_ai_analysis(app):
    """Saves the current AI panel results to a .txt file."""
    if app.raw_audio_data is None:
        QMessageBox.warning(app, "Няма данни",
                            "Заредете аудио файл и изчакайте AI анализа.")
        return

    save_path, _ = QFileDialog.getSaveFileName(
        app, "Запази AI Анализ", "", "Text Files (*.txt)"
    )
    if not save_path:
        return
    if not save_path.lower().endswith(".txt"):
        save_path += ".txt"

    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = os.path.basename(app.current_file_path) if app.current_file_path else "Неизвестен"

        lines = [
            "=" * 55,
            "   СИСТЕМА ЗА АНАЛИЗ НА ИЗСТРЕЛИ — AI ДОКЛАД",
            "=" * 55,
            f"Дата:              {ts}",
            f"Файл:              {filename}",
            f"Продължителност:   {app.audio_duration:.4f} сек.",
            f"Честота:           {app.sample_rate} Hz",
            "",
            "-" * 55,
            app.lbl_class.text(),
            app.lbl_conf.text(),
            app.lbl_events.text(),
            "",
            "-" * 55,
            app.txt_probabilities.toPlainText(),
        ]

        with open(save_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        QMessageBox.information(app, "Успех", f"Анализът е запазен:\n{save_path}")
    except Exception as e:
        QMessageBox.warning(app, "Грешка при запис",
                            f"Не може да се запази файлът:\n{e}")


def save_comparison_analysis(app):
    report_text = app.text_analysis_results.toPlainText()
    if not report_text or "Заредете двата записа" in report_text:
        QMessageBox.warning(
            app, "Няма данни",
            "Заредете запис А и запис Б и изчакайте сравнителния анализ.",
        )
        return

    save_path, _ = QFileDialog.getSaveFileName(
        app, "Запази Сравнителен Доклад", "", "Text Files (*.txt)"
    )
    if not save_path:
        return
    if not save_path.lower().endswith(".txt"):
        save_path += ".txt"

    try:
        ts      = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ev_name  = os.path.basename(app.ev_path)  if app.ev_path  else "Запис А"
        ref_name = os.path.basename(app.ref_path) if app.ref_path else "Запис Б"

        header = "\n".join([
            "=" * 55,
            "   СИСТЕМА ЗА АНАЛИЗ НА ИЗСТРЕЛИ — СРАВНИТЕЛЕН ДОКЛАД",
            "=" * 55,
            f"Дата:          {ts}",
            f"Запис А:       {ev_name}",
            f"Запис Б:       {ref_name}",
            "",
        ])

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(header + "\n" + report_text)

        QMessageBox.information(app, "Успех", f"Докладът е запазен:\n{save_path}")
    except Exception as e:
        QMessageBox.warning(app, "Грешка при запис",
                            f"Не може да се запази файлът:\n{e}")