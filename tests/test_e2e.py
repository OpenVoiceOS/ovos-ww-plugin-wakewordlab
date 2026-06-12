"""End-to-end tests for ovos-ww-plugin-wakewordlab.

Requires: wakewordlab, edge-tts, ffmpeg, numpy.

Strategy
--------
1. Synthesise a WAV containing the wake word phrase ("hey jarvis") via edge-tts.
2. Feed the PCM bytes through the plugin's update() in realistic chunk sizes.
3. Assert found_wake_word() triggers at least once.
4. Repeat with silence and an unrelated utterance and assert no trigger.
"""

import os
import subprocess
import wave

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1600          # 100 ms — typical OVOS chunk size
CHUNK_BYTES = CHUNK_SAMPLES * 2  # int16

WAKE_WORD = "hey_jarvis"
WAKE_PHRASE = "hey jarvis"
NEGATIVE_PHRASE = "good morning, please play some music"
TTS_VOICE = "en-US-GuyNeural"


def _skip_if_missing(*tools: str) -> None:
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, timeout=5, check=False)
        except FileNotFoundError:
            pytest.skip(f"{tool} not found")


def _tts_to_wav(text: str, voice: str, path: str, timeout: int = 60) -> None:
    mp3 = path.replace(".wav", ".mp3")
    subprocess.run(
        ["edge-tts", "--voice", voice, "--text", text, "--write-media", mp3],
        check=True, timeout=timeout, capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", mp3,
            "-ar", str(SAMPLE_RATE), "-ac", "1",
            "-f", "wav", path,
        ],
        check=True, timeout=30, capture_output=True,
    )
    os.unlink(mp3)


def _wav_to_pcm_int16(path: str) -> bytes:
    with wave.open(path, "rb") as wf:
        assert wf.getsampwidth() == 2, "expected 16-bit PCM"
        assert wf.getnchannels() == 1, "expected mono"
        return wf.readframes(wf.getnframes())


def _silence_pcm(seconds: float = 2.0) -> bytes:
    n = int(SAMPLE_RATE * seconds)
    return (np.zeros(n, dtype=np.int16)).tobytes()


def _feed_plugin(plugin, pcm: bytes) -> bool:
    """Feed all PCM bytes through update() in CHUNK_BYTES pieces; return True if any detection."""
    detected = False
    for i in range(0, len(pcm), CHUNK_BYTES):
        chunk = pcm[i : i + CHUNK_BYTES]
        if len(chunk) < CHUNK_BYTES:
            # pad last chunk to full size
            chunk = chunk + b"\x00" * (CHUNK_BYTES - len(chunk))
        plugin.update(chunk)
        if plugin.found_wake_word():
            detected = True
    return detected


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def tools_available():
    _skip_if_missing("edge-tts", "ffmpeg")


@pytest.fixture(scope="session")
def audio_clips(tmp_path_factory, tools_available):
    d = tmp_path_factory.mktemp("wakewordlab_audio")
    wake_path = str(d / "wake.wav")
    negative_path = str(d / "negative.wav")

    _tts_to_wav(WAKE_PHRASE, TTS_VOICE, wake_path)
    _tts_to_wav(NEGATIVE_PHRASE, TTS_VOICE, negative_path)

    return {
        "wake": wake_path,
        "negative": negative_path,
    }


@pytest.fixture(scope="session")
def plugin():
    pytest.importorskip("wakewordlab")
    from ovos_ww_plugin_wakewordlab import WakewordLabHotwordPlugin
    p = WakewordLabHotwordPlugin(
        key_phrase=WAKE_PHRASE,
        config={"model": WAKE_WORD, "vad": True},
    )
    yield p
    p.stop()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPluginLifecycle:
    def test_instantiation(self):
        pytest.importorskip("wakewordlab")
        from ovos_ww_plugin_wakewordlab import WakewordLabHotwordPlugin
        p = WakewordLabHotwordPlugin(key_phrase=WAKE_PHRASE, config={"model": WAKE_WORD})
        assert p is not None
        p.stop()

    def test_no_detection_on_silence(self, plugin):
        plugin.reset()
        pcm = _silence_pcm(seconds=2.0)
        detected = _feed_plugin(plugin, pcm)
        assert not detected, "Silence should not trigger wake word"

    def test_found_wake_word_resets_after_read(self, plugin):
        """found_wake_word() must return False on the second call without new audio."""
        plugin.reset()
        plugin._detected = True
        assert plugin.found_wake_word() is True
        assert plugin.found_wake_word() is False

    def test_reset_clears_state(self, plugin):
        plugin._detected = True
        plugin.reset()
        assert plugin._detected is False
        assert np.all(plugin._buffer == 0.0)


class TestE2EDetection:
    def test_wake_word_detected(self, plugin, audio_clips):
        """Feeding the wake phrase should trigger at least one detection."""
        plugin.reset()
        pcm = _wav_to_pcm_int16(audio_clips["wake"])
        detected = _feed_plugin(plugin, pcm)
        assert detected, (
            f"Expected detection for '{WAKE_PHRASE}' but got none. "
            "Check model threshold or TTS pronunciation."
        )

    def test_negative_phrase_not_detected(self, plugin, audio_clips):
        """An unrelated utterance should not trigger the wake word."""
        plugin.reset()
        pcm = _wav_to_pcm_int16(audio_clips["negative"])
        detected = _feed_plugin(plugin, pcm)
        assert not detected, (
            f"False positive: '{NEGATIVE_PHRASE}' triggered wake word detection."
        )

    def test_scores_printed(self, plugin, audio_clips):
        """Print raw scores to help tune threshold."""
        import wakewordlab
        import numpy as np

        def _pcm_to_float32(path: str) -> np.ndarray:
            pcm = _wav_to_pcm_int16(path)
            return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

        # Score the full 1-second window with max signal
        wake_audio = _pcm_to_float32(audio_clips["wake"])
        neg_audio = _pcm_to_float32(audio_clips["negative"])

        # Grab the window that contains peak energy
        def _peak_score(audio: np.ndarray) -> float:
            window = plugin.WINDOW_SAMPLES
            best = 0.0
            for start in range(0, max(1, len(audio) - window), plugin.STRIDE_SAMPLES):
                s = plugin.detector.score(audio[start : start + window])
                if s > best:
                    best = s
            return best

        wake_score = _peak_score(wake_audio)
        neg_score = _peak_score(neg_audio)
        threshold = plugin.detector.threshold

        print(f"\n[e2e wakewordlab] wake_peak_score={wake_score:.4f}")
        print(f"[e2e wakewordlab] neg_peak_score={neg_score:.4f}")
        print(f"[e2e wakewordlab] threshold={threshold:.4f}")
        print(f"[e2e wakewordlab] wake_detected={wake_score>=threshold}  neg_detected={neg_score>=threshold}")

        assert wake_score > neg_score, (
            f"Wake score {wake_score:.4f} should exceed negative score {neg_score:.4f}"
        )
