import librosa
import librosa.display
import numpy as np

from src.audio_processing import prepare_spectrogram_for_ai

MAX_SELECTED_GRAPHS = 2

GRAPH_OPTIONS = [
    ("waveform",      "Времеви профил"),
    ("mel",           "Mel-Спектрограма"),
    ("stft",          "STFT Спектрограма"),
    ("fft_spectrum",  "FFT Спектър"),
    ("rms_envelope",  "RMS Обвивка"),
    ("scalogram",     "Scalogram (CWT)"),
]

GRAPH_TITLES = {mode_id: title for mode_id, title in GRAPH_OPTIONS}


def style_blank_axis(ax, title="—", hint=None):
    ax.clear()
    ax.set_facecolor("#050d1a")
    ax.grid(True, alpha=0.2, color="#00d4ff", linestyle="--")
    for spine in ax.spines.values():
        spine.set_edgecolor("#00d4ff")
        spine.set_alpha(0.3)
    ax.set_title(title, color="white", fontsize=10, fontweight="bold")
    ax.tick_params(colors="white", labelsize=8)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    if hint:
        ax.text(
            0.5, 0.5, hint,
            transform=ax.transAxes, ha="center", va="center",
            color="#718096", fontsize=11,
        )


def render_graph(ax, mode, audio_data, sample_rate, detected_times, rms_frames, hop_length):
    style_blank_axis(ax, GRAPH_TITLES.get(mode, mode))

    if mode == "waveform":
        librosa.display.waveshow(audio_data, sr=sample_rate, ax=ax, color="#1abc9c")
        for t in detected_times:
            ax.axvline(x=t, color="#e74c3c", linestyle="--", linewidth=1.5, alpha=0.8)
        ax.set_xlabel("Време (секунди)", color="white")

    elif mode == "mel":
        _, log_mel, target_sr = prepare_spectrogram_for_ai(audio_data, sample_rate)
        librosa.display.specshow(
            log_mel, sr=target_sr, x_axis="time", y_axis="mel",
            ax=ax, cmap="viridis",
        )
        ax.set_xlabel("Време (секунди)", color="white")

    elif mode == "stft":
        stft = librosa.stft(audio_data, n_fft=1024, hop_length=256)
        stft_db = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
        librosa.display.specshow(
            stft_db, sr=sample_rate,
            x_axis="time", y_axis="linear",
            ax=ax, cmap="inferno",
        )
        ax.set_ylim(0, min(sample_rate / 2, 12000))
        ax.set_xlabel("Време (секунди)", color="white")

    elif mode == "fft_spectrum":
        fft_vals = np.abs(np.fft.rfft(audio_data))
        fft_freqs = np.fft.rfftfreq(len(audio_data), 1.0 / sample_rate)
        ax.plot(
            fft_freqs, 20 * np.log10(fft_vals + 1e-6),
            color="#9b59b6", linewidth=1,
        )
        ax.set_xlim(0, min(sample_rate / 2, 8000))
        ax.set_xlabel("Честота (Hz)", color="white")
        ax.set_ylabel("Мощност (dB)", color="white")

    elif mode == "rms_envelope":
        times = librosa.frames_to_time(
            range(len(rms_frames)), sr=sample_rate, hop_length=hop_length
        )
        ax.plot(times, rms_frames, color="#2ecc71", linewidth=2)
        ax.fill_between(times, rms_frames, color="#2ecc71", alpha=0.3)
        ax.set_xlabel("Време (секунди)", color="white")
        ax.set_ylabel("Енергия (RMS)", color="white")

    elif mode == "scalogram":
        ax.text(
            0.5, 0.5, "⠋ Изчислява се скалограмата (CWT)…",
            color="#00d4ff", ha="center", va="center",
            transform=ax.transAxes, fontsize=12,
        )
        return False

    return True


def render_scalogram(ax, scalogram, freqs, duration):
    ax.clear()
    ax.set_facecolor("#050d1a")
    times = np.linspace(0, duration, scalogram.shape[1])
    ax.pcolormesh(times, freqs, scalogram, shading="auto", cmap="magma")
    ax.set_yscale("log")
    ax.set_title(GRAPH_TITLES["scalogram"], color="white", fontsize=10, fontweight="bold")
    ax.set_ylabel("Честота (Hz, log)", color="white")
    ax.set_xlabel("Време (секунди)", color="white")
    ax.tick_params(colors="white", labelsize=8)
