import librosa
import numpy as np
import scipy.signal as scipy_signal
import pywt

MAX_PAD_LEN = 431

TARGET_SR = 44100
SHOT_WINDOW_PRE = 0.08
SHOT_WINDOW_POST = 0.45

def load_and_get_metadata(file_path):
    audio_data, sample_rate = librosa.load(file_path, sr=None)
    duration = librosa.get_duration(y=audio_data, sr=sample_rate)
    peak_amp = np.max(np.abs(audio_data))
    rms_energy = np.sqrt(np.mean(audio_data**2))
    return audio_data, sample_rate, duration, peak_amp, rms_energy

def _filter_by_amplitude(onset_frames, rms_frames, percentile=75):
    if len(onset_frames) == 0:
        return onset_frames
    threshold = np.percentile(rms_frames, percentile)
    peak_rms = max(float(rms_frames[f]) for f in onset_frames)
    threshold = max(threshold, peak_rms * 0.30)
    return np.array([f for f in onset_frames if rms_frames[f] >= threshold])


def _cluster_peaks(onset_frames, rms_frames, sample_rate, hop_length, cluster_gap=0.12):
    if len(onset_frames) <= 1:
        return onset_frames

    sorted_frames = sorted(onset_frames, key=lambda f: rms_frames[f], reverse=True)
    kept = []

    for frame in sorted_frames:
        frame_time = librosa.frames_to_time(frame, sr=sample_rate, hop_length=hop_length)
        too_close = False
        for kept_frame in kept:
            kept_time = librosa.frames_to_time(kept_frame, sr=sample_rate, hop_length=hop_length)
            if abs(frame_time - kept_time) < cluster_gap:
                too_close = True
                break
        if not too_close:
            kept.append(frame)

    kept.sort()
    return np.array(kept)


def _merge_echo_onsets(onset_frames, rms_frames, sample_rate, hop_length,
                        max_echo_gap=0.45, echo_drop_db=4.0):
    if len(onset_frames) <= 1:
        return onset_frames

    merged = [onset_frames[0]]
    for frame in onset_frames[1:]:
        time_gap = librosa.frames_to_time(frame - merged[-1], sr=sample_rate, hop_length=hop_length)
        amp_drop_db = 20 * np.log10(rms_frames[merged[-1]] / (rms_frames[frame] + 1e-9))
        is_echo = time_gap < max_echo_gap and amp_drop_db > echo_drop_db
        if not is_echo:
            merged.append(frame)

    return np.array(merged)


def _detect_from_rms_peaks(audio_data, sample_rate, hop_length=256, frame_length=2048):
    rms_frames = librosa.feature.rms(
        y=audio_data, frame_length=frame_length, hop_length=hop_length
    )[0]

    peak_rms = float(np.max(rms_frames))
    if peak_rms < 1e-9:
        return np.array([]), rms_frames

    height_threshold = peak_rms * 0.32
    prominence_threshold = peak_rms * 0.18
    min_distance = max(1, int(0.10 * sample_rate / hop_length))

    peak_frames, _ = scipy_signal.find_peaks(
        rms_frames,
        height=height_threshold,
        distance=min_distance,
        prominence=prominence_threshold,
    )

    if len(peak_frames) == 0:
        return np.array([]), rms_frames

    peak_frames = _cluster_peaks(peak_frames, rms_frames, sample_rate, hop_length)
    return peak_frames, rms_frames


def _detect_from_onsets(audio_data, sample_rate, hop_length=256):
    onset_env = librosa.onset.onset_strength(y=audio_data, sr=sample_rate, hop_length=hop_length)

    avg_frames = int(0.35 * sample_rate / hop_length)
    wait_frames = int(0.40 * sample_rate / hop_length)

    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sample_rate, hop_length=hop_length,
        units="frames",
        pre_avg=avg_frames, post_avg=avg_frames,
        delta=0.45, wait=wait_frames,
    )

    rms_frames = librosa.feature.rms(y=audio_data, hop_length=hop_length)[0]
    if len(onset_frames) == 0:
        return np.array([]), rms_frames

    onset_frames = _filter_by_amplitude(onset_frames, rms_frames)
    onset_frames = _cluster_peaks(onset_frames, rms_frames, sample_rate, hop_length)
    onset_frames = _merge_echo_onsets(onset_frames, rms_frames, sample_rate, hop_length)
    return onset_frames, rms_frames


def detect_gunshot_events(audio_data, sample_rate):
    hop_length = 256

    peak_frames, rms_frames = _detect_from_rms_peaks(audio_data, sample_rate, hop_length)

    if len(peak_frames) == 0:
        peak_frames, rms_frames = _detect_from_onsets(audio_data, sample_rate, hop_length)

    detected_times = librosa.frames_to_time(peak_frames, sr=sample_rate, hop_length=hop_length)
    return detected_times, rms_frames, hop_length

def prepare_spectrogram_for_ai(audio_data, sample_rate):
    if sample_rate != 44100:
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=44100)
        sample_rate = 44100
    
    audio_norm = librosa.util.normalize(audio_data)

    mel_spec = librosa.feature.melspectrogram(y=audio_norm, sr=sample_rate, n_mels=64)
    log_mel = librosa.power_to_db(mel_spec, ref=np.max)


    if log_mel.shape[1] < MAX_PAD_LEN:
        pad_width = MAX_PAD_LEN - log_mel.shape[1]
        log_mel_fixed = np.pad(log_mel, pad_width=((0, 0), (0, pad_width)), mode='constant')
    else:
        log_mel_fixed = log_mel[:, :MAX_PAD_LEN]

    input_tensor = np.expand_dims(log_mel_fixed, axis=0)
    input_tensor = np.expand_dims(input_tensor, axis=-1)

    return input_tensor, log_mel_fixed, sample_rate

def apply_muzzle_blast_filter(audio_data, sample_rate):
    if audio_data is None: return None
    nyquist = 0.5 * sample_rate
    normal_cutoff = 500.0 / nyquist
    b, a = scipy_signal.butter(4, normal_cutoff, btype='low', analog=False)
    return scipy_signal.lfilter(b, a, audio_data)

def apply_sonic_crack_filter(audio_data, sample_rate):
    if audio_data is None: return None
    nyquist = 0.5 * sample_rate
    normal_cutoff = 1200.0 / nyquist
    b, a = scipy_signal.butter(4, normal_cutoff, btype='high', analog=False)
    return scipy_signal.lfilter(b, a, audio_data)

def apply_custom_bandpass_filter(audio_data, sample_rate, low_hz, high_hz):
    if audio_data is None: return None
    nyquist = 0.5 * sample_rate
    if low_hz >= high_hz:
        return audio_data
    b, a = scipy_signal.butter(4, [low_hz/nyquist, min(0.99, high_hz/nyquist)], btype='band', analog=False)
    return scipy_signal.lfilter(b, a, audio_data)

def apply_ballistic_shot_gate(audio_data, sample_rate):
    if audio_data is None: return None
    rms = librosa.feature.rms(y=audio_data, frame_length=512, hop_length=256)[0]
    threshold = np.mean(rms) + 0.3 * np.std(rms)
    
    active_frames = np.nonzero(rms > threshold)[0]
    if len(active_frames) == 0:
        return audio_data
        
    start_sample = max(0, int(librosa.frames_to_samples(active_frames[0], hop_length=256) - 0.1 * sample_rate))
    end_sample = min(len(audio_data), int(librosa.frames_to_samples(active_frames[-1], hop_length=256) + 0.2 * sample_rate))
    
    return audio_data[start_sample:end_sample]

def _resample_to_target(audio_data, sample_rate, target_sr=TARGET_SR):
    if sample_rate != target_sr:
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=target_sr)
        sample_rate = target_sr
    return audio_data, sample_rate


def extract_shot_window(audio_data, sample_rate, shot_time,
                        pre_seconds=SHOT_WINDOW_PRE, post_seconds=SHOT_WINDOW_POST):
    start = max(0, int((shot_time - pre_seconds) * sample_rate))
    end = min(len(audio_data), int((shot_time + post_seconds) * sample_rate))
    return audio_data[start:end]


def get_first_shot_context(audio_data, sample_rate):
    detected_times, _, _ = detect_gunshot_events(audio_data, sample_rate)
    if len(detected_times) == 0:
        return audio_data, None, detected_times

    shot_time = float(detected_times[0])
    segment = extract_shot_window(audio_data, sample_rate, shot_time)
    return segment, shot_time, detected_times


def extract_shot_acoustic_features(segment, sample_rate):
    if segment is None or len(segment) < 64:
        return {
            "peak_amp": 0.0,
            "centroid_hz": 0.0,
            "bandwidth_hz": 0.0,
            "crack_ratio": 0.0,
            "attack_ms": 0.0,
        }

    segment, sample_rate = _resample_to_target(segment, sample_rate)
    peak_amp = float(np.max(np.abs(segment)))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=segment, sr=sample_rate)))
    bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=segment, sr=sample_rate)))

    low_band = apply_muzzle_blast_filter(segment, sample_rate)
    high_band = apply_sonic_crack_filter(segment, sample_rate)
    low_energy = np.sqrt(np.mean(low_band ** 2))
    high_energy = np.sqrt(np.mean(high_band ** 2))
    crack_ratio = float(high_energy / (low_energy + 1e-9))

    hop = 256
    rms = librosa.feature.rms(y=segment, hop_length=hop)[0]
    peak_frame = int(np.argmax(rms))
    attack_ms = float(librosa.frames_to_time(peak_frame, sr=sample_rate, hop_length=hop) * 1000)

    return {
        "peak_amp": peak_amp,
        "centroid_hz": centroid,
        "bandwidth_hz": bandwidth,
        "crack_ratio": crack_ratio,
        "attack_ms": attack_ms,
    }


def _prepare_mel_pair(seg1, sr1, seg2, sr2):
    seg1, sr1 = _resample_to_target(seg1, sr1)
    seg2, sr2 = _resample_to_target(seg2, sr2)

    norm1 = librosa.util.normalize(seg1)
    norm2 = librosa.util.normalize(seg2)

    mel1 = librosa.feature.melspectrogram(y=norm1, sr=sr1, n_mels=64)
    mel2 = librosa.feature.melspectrogram(y=norm2, sr=sr2, n_mels=64)
    shared_ref = max(float(np.max(mel1)), float(np.max(mel2)), 1e-9)
    log_mel1 = librosa.power_to_db(mel1, ref=shared_ref)
    log_mel2 = librosa.power_to_db(mel2, ref=shared_ref)
    return log_mel1, log_mel2


def compute_envelope_correlation(seg1, sr1, seg2, sr2):
    seg1, sr1 = _resample_to_target(seg1, sr1)
    seg2, sr2 = _resample_to_target(seg2, sr2)

    hop = 256
    env1 = librosa.feature.rms(y=seg1, hop_length=hop)[0]
    env2 = librosa.feature.rms(y=seg2, hop_length=hop)[0]
    n = min(len(env1), len(env2))
    if n < 3:
        return 0.0

    env1 = (env1[:n] - np.mean(env1[:n])) / (np.std(env1[:n]) + 1e-9)
    env2 = (env2[:n] - np.mean(env2[:n])) / (np.std(env2[:n]) + 1e-9)
    return float(np.corrcoef(env1, env2)[0, 1])


def compute_active_mel_similarity(seg1, sr1, seg2, sr2, energy_threshold_db=-35.0):
    mel1, mel2 = _prepare_mel_pair(seg1, sr1, seg2, sr2)
    n_cols = min(mel1.shape[1], mel2.shape[1])
    mel1 = mel1[:, :n_cols]
    mel2 = mel2[:, :n_cols]

    active = (np.max(mel1, axis=0) > energy_threshold_db) | (np.max(mel2, axis=0) > energy_threshold_db)
    if not np.any(active):
        return 0.0, mel1, mel2

    v1 = mel1[:, active].flatten()
    v2 = mel2[:, active].flatten()
    v1 = v1 - np.mean(v1)
    v2 = v2 - np.mean(v2)
    norm_a = np.linalg.norm(v1)
    norm_b = np.linalg.norm(v2)
    if norm_a == 0 or norm_b == 0:
        return 0.0, mel1, mel2

    cosine = float(np.dot(v1, v2) / (norm_a * norm_b))
    return cosine, mel1, mel2


def compute_embedding_similarity(embedding_model, seg1, sr1, seg2, sr2):
    if embedding_model is None:
        return None

    tensor1, _, _ = prepare_spectrogram_for_ai(seg1, sr1)
    tensor2, _, _ = prepare_spectrogram_for_ai(seg2, sr2)
    emb1 = embedding_model.predict(tensor1, verbose=0)[0]
    emb2 = embedding_model.predict(tensor2, verbose=0)[0]

    norm_a = np.linalg.norm(emb1)
    norm_b = np.linalg.norm(emb2)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(max(0.0, np.dot(emb1, emb2) / (norm_a * norm_b))) * 100.0


def _compare_shot_intervals(ev_times, ref_times):
    if len(ev_times) < 2 or len(ref_times) < 2:
        return None

    ev_intervals = np.diff(ev_times[: min(len(ev_times), len(ref_times))])
    ref_intervals = np.diff(ref_times[: min(len(ev_times), len(ref_times))])
    n = min(len(ev_intervals), len(ref_intervals))
    if n == 0:
        return None

    ev_intervals = ev_intervals[:n]
    ref_intervals = ref_intervals[:n]
    if np.std(ev_intervals) < 1e-6 or np.std(ref_intervals) < 1e-6:
        return float(abs(np.mean(ev_intervals) - np.mean(ref_intervals)))

    return float(np.corrcoef(ev_intervals, ref_intervals)[0, 1])


def _feature_delta_pct(value_a, value_b):
    denom = max(abs(value_a), abs(value_b), 1e-9)
    return abs(value_a - value_b) / denom * 100.0


def _build_same_source_verdict(composite_score, shot_count_match, envelope_corr, embedding_pct):
    mismatch_note = ""
    if not shot_count_match:
        mismatch_note = (
            "\n\n(Забележка: различен брой засечени изстрели — често при различна "
            "чувствителност на микрофона или фонов шум, не непременно различно събитие.)"
        )

    if composite_score >= 75.0 and envelope_corr >= 0.55:
        return (
            "strong",
            "✅ ВИСОКА ВЕРОЯТНОСТ ЗА ЕДИН И СЪЩ ИЗТОЧНИК.\n"
            "Въпреки различните условия на запис (микрофон, разстояние, шум), "
            "временният профил и акустичният отпечатък на изстрела са съгласувани."
            + mismatch_note,
        )

    if composite_score >= 52.0:
        return (
            "moderate",
            "⚠ УМЕРЕНО СХОДСТВО — ВЪЗМОЖНО СЪЩО СЪБИТИЕ.\n"
            "Има общи акустични белези, но разликите в качеството на записа, "
            "ехото или ъгъла на заснемане пречат на категорично заключение."
            + mismatch_note,
        )

    return (
        "weak",
        "❌ НИСКО СХОДСТВО — ВЕРОЯТНО РАЗЛИЧНИ ЗАПИСИ.\n"
        "Подравнените изстрели не показват достатъчно съвпадение във формата "
        "на импулса и спектралната структура, за да се приемат за един източник."
        + mismatch_note,
    )


def compare_same_source_recordings(audio_ev, sr_ev, audio_ref, sr_ref, embedding_model=None):
    """
    Cross-recording same-source check (e.g. CCTV vs phone).
    Compares aligned first-shot windows — not weapon class.
    """
    ev_segment, ev_shot_time, ev_times = get_first_shot_context(audio_ev, sr_ev)
    ref_segment, ref_shot_time, ref_times = get_first_shot_context(audio_ref, sr_ref)

    if len(ev_times) == 0 or len(ref_times) == 0:
        missing = []
        if len(ev_times) == 0:
            missing.append("Запис А")
        if len(ref_times) == 0:
            missing.append("Запис Б")
        return {
            "composite_score": 0.0,
            "envelope_correlation": 0.0,
            "envelope_pct": 0.0,
            "mel_cosine": 0.0,
            "mel_pct": 0.0,
            "embedding_pct": None,
            "ev_shot_count": len(ev_times),
            "ref_shot_count": len(ref_times),
            "shot_count_match": False,
            "ev_shot_time": ev_shot_time,
            "ref_shot_time": ref_shot_time,
            "interval_corr": None,
            "ev_features": {},
            "ref_features": {},
            "feature_rows": [],
            "mel_ev": np.zeros((64, 1)),
            "mel_ref": np.zeros((64, 1)),
            "verdict_level": "invalid",
            "verdict_text": (
                "❌ НЕ СА ЗАСЕЧЕНИ ИЗСТРЕЛИ.\n"
                f"Липсват импулси в: {', '.join(missing)}.\n"
                "Заредете записи с ясно чуваем изстрел или приложете Shot Gate "
                "в персонализирания панел преди сравнение."
            ),
        }

    ev_features = extract_shot_acoustic_features(ev_segment, sr_ev)
    ref_features = extract_shot_acoustic_features(ref_segment, sr_ref)

    envelope_corr = compute_envelope_correlation(ev_segment, sr_ev, ref_segment, sr_ref)
    mel_cosine, mel_ev, mel_ref = compute_active_mel_similarity(ev_segment, sr_ev, ref_segment, sr_ref)
    embedding_pct = compute_embedding_similarity(
        embedding_model, ev_segment, sr_ev, ref_segment, sr_ref
    )

    envelope_pct = max(0.0, envelope_corr) * 100.0
    mel_pct = max(0.0, mel_cosine) * 100.0

    composite_score = envelope_pct * 0.55 + mel_pct * 0.45

    shot_count_match = len(ev_times) == len(ref_times)
    interval_corr = _compare_shot_intervals(ev_times, ref_times)

    verdict_level, verdict_text = _build_same_source_verdict(
        composite_score, shot_count_match, envelope_corr, embedding_pct
    )

    feature_rows = []
    for key, label, unit in [
        ("centroid_hz", "Спектрален центроид", "Hz"),
        ("bandwidth_hz", "Честотна лента", "Hz"),
        ("crack_ratio", "Crack / Blast", ""),
        ("attack_ms", "Време до пик", "ms"),
    ]:
        ev_val = ev_features[key]
        ref_val = ref_features[key]
        feature_rows.append({
            "label": label,
            "ev": ev_val,
            "ref": ref_val,
            "delta_pct": _feature_delta_pct(ev_val, ref_val),
            "unit": unit,
        })

    return {
        "composite_score": composite_score,
        "envelope_correlation": envelope_corr,
        "envelope_pct": envelope_pct,
        "mel_cosine": mel_cosine,
        "mel_pct": mel_pct,
        "embedding_pct": embedding_pct,
        "ev_shot_count": len(ev_times),
        "ref_shot_count": len(ref_times),
        "shot_count_match": shot_count_match,
        "ev_shot_time": ev_shot_time,
        "ref_shot_time": ref_shot_time,
        "interval_corr": interval_corr,
        "ev_features": ev_features,
        "ref_features": ref_features,
        "feature_rows": feature_rows,
        "mel_ev": mel_ev,
        "mel_ref": mel_ref,
        "verdict_level": verdict_level,
        "verdict_text": verdict_text,
    }


def build_same_source_report(result):
    lines = [
        "=== ВЕРИФИКАЦИЯ: ===",
        "(сравнение на записи от различни устройства/условия)",
        "",
        "ПОДРАВНЯВАНЕ НА ИЗСТРЕЛИ:",
        f"  Запис А: {result['ev_shot_count']} изстрел(а)"
        + (f", първи на {result['ev_shot_time']:.2f}s" if result['ev_shot_time'] is not None else ""),
        f"  Запис Б: {result['ref_shot_count']} изстрел(а)"
        + (f", първи на {result['ref_shot_time']:.2f}s" if result['ref_shot_time'] is not None else ""),
    ]

    if not result["shot_count_match"]:
        lines.append("  ⚠ Различен брой засечени изстрели")

    if result["interval_corr"] is not None:
        lines.append(f"  Корелация на интервалите: {result['interval_corr']:.2f}")

    lines.extend([
        "",
        "МЕТРИКИ (след подравняване на първия изстрел):",
        f"  Импулсен профил (огибваща):  {result['envelope_pct']:.1f}%"
        f"  (r={result['envelope_correlation']:.2f})",
        f"  Активен спектър (mel):        {result['mel_pct']:.1f}%"
        f"  (cos={result['mel_cosine']:.2f})",
    ])

    if result["embedding_pct"] is not None:
        lines.append(
            f"  CNN профил (спомагателно):  {result['embedding_pct']:.1f}%"
            "  — не определя тип оръжие тук"
        )

    lines.extend([
        f"  ► Обобщена оценка:            {result['composite_score']:.1f}%"
        "  (импулс 55% + спектър 45%)",
        "",
        "АКУСТИЧНИ ПАРАМЕТРИ (изстрел #1):",
        f"  {'Параметър':<22}{'Запис А':<12}{'Запис Б':<12}{'Δ%':<8}",
        "  " + "-" * 50,
    ])

    for row in result["feature_rows"]:
        unit = f" {row['unit']}" if row["unit"] else ""
        lines.append(
            f"  {row['label']:<22}"
            f"{row['ev']:<12.1f}"
            f"{row['ref']:<12.1f}"
            f"{row['delta_pct']:<8.1f}"
            + (unit if unit.strip() else "")
        )

    lines.extend([
        "",
        "ЗАКЛЮЧЕНИЕ:",
        result["verdict_text"],
        "",
        "Забележка: Този модул не определя тип оръжие — той проверява",
        "дали два записа (CCTV, телефон, диктофон и т.н.) вероятно",
        "засичат един и същ изстрел/събитие.",
    ])
    return "\n".join(lines)


def mel_for_aligned_shot_display(audio_data, sample_rate):
    """Mel spectrogram of the first aligned shot window (for UI preview)."""
    segment, _, _ = get_first_shot_context(audio_data, sample_rate)
    _, mel, _ = prepare_spectrogram_for_ai(segment, sample_rate)
    return mel


def align_to_first_event(audio_data, sample_rate, pre_event_seconds=0.2, window_seconds=2.5):
    detected_times, _, _ = detect_gunshot_events(audio_data, sample_rate)
    if len(detected_times) == 0:
        return audio_data

    event_time = detected_times[0]
    start_sample = max(0, int((event_time - pre_event_seconds) * sample_rate))
    end_sample = min(len(audio_data), start_sample + int(window_seconds * sample_rate))
    return audio_data[start_sample:end_sample]

def compute_scalogram(audio_data, sample_rate, target_sr=11025, num_scales=128):
    if sample_rate != target_sr:
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=target_sr)

    scales = np.arange(1, num_scales + 1)
    coefficients, frequencies = pywt.cwt(audio_data, scales, 'morl', sampling_period=1.0 / target_sr)
    return np.abs(coefficients), frequencies, target_sr

def cosine_similarity_pct(vec_a, vec_b):

    a = vec_a - np.mean(vec_a)
    b = vec_b - np.mean(vec_b)
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return (np.dot(a, b) / (norm_a * norm_b) + 1) / 2 * 100