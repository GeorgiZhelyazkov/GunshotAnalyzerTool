import numpy as np
import librosa
from PyQt6.QtCore import QThread, pyqtSignal

from src.audio_processing import (
    prepare_spectrogram_for_ai,
    detect_gunshot_events,
    compare_same_source_recordings,
    cosine_similarity_pct,
    apply_muzzle_blast_filter,
    apply_sonic_crack_filter,
    align_to_first_event,
    compute_scalogram,
)

class AIAnalysisWorker(QThread):
    finished = pyqtSignal(
        object,  # predictions       – np.ndarray  shape (n_classes,)
        object,  # log_mel_fixed     – np.ndarray  shape (64, MAX_PAD_LEN)
        float,   # target_sr
        object,  # detected_times    – np.ndarray  shape (n_shots,)
        str,     # multishot_report  – plain text, "" when < 2 shots
    )
    error = pyqtSignal(str)

    def __init__(self, audio_data: np.ndarray, sample_rate: int, model, parent=None):
        super().__init__(parent)
        self.audio_data  = audio_data
        self.sample_rate = sample_rate
        self.model       = model

    def run(self):
        try:
            input_tensor, log_mel_fixed, target_sr = prepare_spectrogram_for_ai(
                self.audio_data, self.sample_rate
            )
            predictions = self.model.predict(input_tensor, verbose=0)[0]

            detected_times, _, _ = detect_gunshot_events(self.audio_data, self.sample_rate)

            multishot_report = (
                self._build_multishot_report(detected_times)
                if len(detected_times) > 1
                else ""
            )

            self.finished.emit(
                predictions,
                log_mel_fixed,
                float(target_sr),
                detected_times,
                multishot_report,
            )
        except Exception as exc:
            self.error.emit(str(exc))

    def _extract_shot_features(self, segment: np.ndarray):
        """
        Returns (mel_flat, peak_amp, centroid_hz, crack_ratio) for one
        shot segment.
        """
        _, mel, _ = prepare_spectrogram_for_ai(segment, self.sample_rate)
        peak_amp = float(np.max(np.abs(segment)))
        centroid = float(
            np.mean(librosa.feature.spectral_centroid(y=segment, sr=self.sample_rate))
        )
        low_band   = apply_muzzle_blast_filter(segment, self.sample_rate)
        high_band  = apply_sonic_crack_filter(segment, self.sample_rate)
        low_energy = np.sqrt(np.mean(low_band  ** 2))
        high_energy= np.sqrt(np.mean(high_band ** 2))
        crack_ratio = float(high_energy / (low_energy + 1e-9))
        return mel.flatten(), peak_amp, centroid, crack_ratio

    def _collect_shot_data(self, detected_times: np.ndarray):
        window_samples = int(0.5 * self.sample_rate)
        shots = []
        for t in detected_times:
            start   = max(0, int(t * self.sample_rate) - window_samples // 2)
            end     = min(len(self.audio_data), start + window_samples)
            segment = self.audio_data[start:end]
            if len(segment) < 1000:
                continue
            shots.append((t,) + self._extract_shot_features(segment))
        return shots

    def _build_multishot_report(self, detected_times: np.ndarray) -> str:
        shots = self._collect_shot_data(detected_times)
        if len(shots) < 2:
            return ""

        times        = [s[0] for s in shots]
        avg_interval = np.mean(np.diff(times))
        rpm          = 60.0 / avg_interval if avg_interval > 0 else 0.0

        similarities = [
            cosine_similarity_pct(shots[i - 1][1], shots[i][1])
            for i in range(1, len(shots))
        ]
        sim_strs = ["  --"] + [
            f"{s:5.1f}%{' ⚠' if s < 85.0 else ''}" for s in similarities
        ]

        text  = f"\n{'=' * 30}\n"
        text += (
            f"Темп на стрелба: ~{rpm:.0f} изстр./мин."
            f" (среден интервал {avg_interval:.3f}s)\n\n"
        )
        text += (
            f"{'Изстрел':<8}{'Време':<7}{'Ампл.':<8}"
            f"{'Центр(Hz)':<11}{'Crack':<7}{'Сходство':<9}\n"
        )
        text += "-" * 50 + "\n"
        for i, (t, _, amp, cen, crk) in enumerate(shots):
            text += (
                f"#{i + 1:<7}{t:<7.2f}{amp:<8.3f}"
                f"{cen:<11.0f}{crk:<7.2f}{sim_strs[i]}\n"
            )

        flagged = sum(1 for s in similarities if s < 85.0)
        avg_sim = np.mean(similarities)
        if flagged == 0:
            text += (
                f"\n→ Записът е консистентен ({avg_sim:.1f}% средно сходство)"
                f" — вероятно едно оръжие.\n"
            )
        else:
            text += (
                f"\n→ {flagged} преход(а) с понижено сходство"
                f" ({avg_sim:.1f}% средно) — възможни няколко източници.\n"
            )
        return text

class ComparisonWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self,
        ev_audio:  np.ndarray, ev_sr:  int,
        ref_audio: np.ndarray, ref_sr: int,
        embedding_model=None,
        parent=None,
    ):
        super().__init__(parent)
        self.ev_audio  = ev_audio
        self.ev_sr     = ev_sr
        self.ref_audio = ref_audio
        self.ref_sr    = ref_sr
        self.embedding_model = embedding_model

    def run(self):
        try:
            result = compare_same_source_recordings(
                self.ev_audio,  self.ev_sr,
                self.ref_audio, self.ref_sr,
                embedding_model=self.embedding_model,
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))

class ScalogramWorker(QThread):
    """
    Runs the heavy CWT computation for the scalogram display mode.

    Signals
    -------
    finished(scalogram, freqs, duration_secs)
    error(message)
    """

    finished = pyqtSignal(
        object,  # scalogram    – np.ndarray  shape (scales, time)
        object,  # freqs        – np.ndarray  shape (scales,)
        float,   # duration_secs
    )
    error = pyqtSignal(str)

    def __init__(self, audio_data: np.ndarray, sample_rate: int, parent=None):
        super().__init__(parent)
        self.audio_data  = audio_data
        self.sample_rate = sample_rate

    def run(self):
        try:
            detected_times, _, _ = detect_gunshot_events(self.audio_data, self.sample_rate)

            if len(detected_times) > 0:
                audio_to_analyze = align_to_first_event(
                    self.audio_data,
                    self.sample_rate,
                    pre_event_seconds=0.2,
                    window_seconds=5.0,
                )
            else:
                audio_to_analyze = self.audio_data

            scalogram, freqs, target_sr = compute_scalogram(audio_to_analyze, self.sample_rate)
            duration = len(audio_to_analyze) / target_sr
            self.finished.emit(scalogram, freqs, float(duration))
        except Exception as exc:
            self.error.emit(str(exc))