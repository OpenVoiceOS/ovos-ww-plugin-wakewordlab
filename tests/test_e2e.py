"""End-to-end tests for ovos-ww-plugin-wakewordlab.

Bundled fixture WAVs (16 kHz mono int16) are in tests/fixtures/:
  wake.wav     — "hey jarvis" (en-US-GuyNeural via edge-tts)
  negative.wav — "good morning please play some music"

No TTS or network access required at test time.
"""

import wave
from pathlib import Path

import numpy as np
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1600       # 100 ms — typical OVOS VAD chunk size
CHUNK_BYTES = CHUNK_SAMPLES * 2

WAKE_WORD = "hey_jarvis"
WAKE_PHRASE = "hey jarvis"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wav_to_pcm_int16(path: Path) -> bytes:
    with wave.open(str(path), "rb") as wf:
        assert wf.getsampwidth() == 2, f"{path.name}: expected 16-bit PCM"
        assert wf.getnchannels() == 1, f"{path.name}: expected mono"
        assert wf.getframerate() == SAMPLE_RATE, f"{path.name}: expected {SAMPLE_RATE} Hz"
        return wf.readframes(wf.getnframes())


def _silence_pcm(seconds: float = 2.0) -> bytes:
    return (np.zeros(int(SAMPLE_RATE * seconds), dtype=np.int16)).tobytes()


def _feed_plugin(plugin, pcm: bytes) -> bool:
    """Stream PCM through update() in CHUNK_BYTES pieces; return True on any detection."""
    detected = False
    for i in range(0, len(pcm), CHUNK_BYTES):
        chunk = pcm[i : i + CHUNK_BYTES]
        if len(chunk) < CHUNK_BYTES:
            chunk = chunk + b"\x00" * (CHUNK_BYTES - len(chunk))
        plugin.update(chunk)
        if plugin.found_wake_word():
            detected = True
    return detected


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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

    def test_lang_is_kept_although_the_base_does_not_take_it(self):
        # HotWordEngine.__init__ takes (key_phrase, config). Passing lang on
        # to it raised TypeError before any assertion in this file could run,
        # so the plugin keeps lang itself. This pins that it is still kept,
        # rather than quietly dropped along with the argument.
        pytest.importorskip("wakewordlab")
        from ovos_ww_plugin_wakewordlab import WakewordLabHotwordPlugin
        p = WakewordLabHotwordPlugin(key_phrase=WAKE_PHRASE,
                                     config={"model": WAKE_WORD},
                                     lang="pt-pt")
        try:
            assert p.lang == "pt-pt"
        finally:
            p.stop()

    def test_no_detection_on_silence(self, plugin):
        plugin.reset()
        assert not _feed_plugin(plugin, _silence_pcm(2.0))

    def test_found_wake_word_resets_after_read(self, plugin):
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
    def test_wake_word_detected(self, plugin):
        plugin.reset()
        pcm = _wav_to_pcm_int16(FIXTURES / "wake.wav")
        assert _feed_plugin(plugin, pcm), (
            f"Expected detection for '{WAKE_PHRASE}' but got none."
        )

    def test_negative_phrase_not_detected(self, plugin):
        plugin.reset()
        pcm = _wav_to_pcm_int16(FIXTURES / "negative.wav")
        assert not _feed_plugin(plugin, pcm), (
            "False positive: negative phrase triggered wake word detection."
        )

    def test_scores_printed(self, plugin):
        """Print peak scores and threshold — useful for PR review."""
        def _pcm_to_float32(path: Path) -> np.ndarray:
            raw = _wav_to_pcm_int16(path)
            return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        def _peak_score(audio: np.ndarray) -> float:
            best = 0.0
            stride = plugin.STRIDE_SAMPLES
            window = plugin.WINDOW_SAMPLES
            for start in range(0, max(1, len(audio) - window), stride):
                s = plugin.detector.score(audio[start : start + window])
                if s > best:
                    best = s
            return best

        wake_score = _peak_score(_pcm_to_float32(FIXTURES / "wake.wav"))
        neg_score = _peak_score(_pcm_to_float32(FIXTURES / "negative.wav"))
        threshold = plugin.detector.threshold

        print(f"\n[e2e] wake_peak={wake_score:.4f}  neg_peak={neg_score:.4f}  threshold={threshold:.4f}")
        assert wake_score > neg_score, (
            f"Wake score {wake_score:.4f} should exceed negative score {neg_score:.4f}"
        )
