import struct
from typing import Optional, Dict, Any

import numpy as np
from ovos_plugin_manager.templates.hotwords import HotWordEngine

try:
    import wakewordlab
except ImportError:
    wakewordlab = None


class WakewordLabHotwordPlugin(HotWordEngine):
    """Wake word plugin backed by wakewordlab (https://github.com/ubermorgenland/wakewordlab).

    Config keys (under hotwords.<name> in mycroft.conf):
      model         - wake word slug or path to a .wkw/.onnx model file (default: key_phrase)
      threshold     - detection confidence threshold 0.0–1.0 (default: model suggested_threshold)
      vad           - enable Silero VAD pre-filter (default: True)
      vad_threshold - VAD sensitivity (default: 0.5)
      license_key   - license key for commercial models (default: None)
    """

    # OVOS delivers 16 kHz signed-int16 mono PCM; wakewordlab needs float32 @16 kHz.
    # We accumulate chunks into a 1-second (16 000 sample) rolling buffer and score
    # on every stride_samples boundary, matching wakewordlab's default windowing.
    SAMPLE_RATE = 16000
    WINDOW_SAMPLES = 16000       # 1 second
    STRIDE_SAMPLES = 1600        # 100 ms

    def __init__(self, key_phrase: str = "hey jarvis",
                 config: Optional[Dict[str, Any]] = None,
                 lang: str = "en-us"):
        config = config or {}
        super().__init__(key_phrase, config, lang)

        if wakewordlab is None:
            raise ImportError("wakewordlab is not installed. Run: pip install wakewordlab")

        model_name = config.get("model", key_phrase)
        license_key = config.get("license_key")
        threshold = config.get("threshold")
        vad = config.get("vad", True)
        vad_threshold = config.get("vad_threshold", 0.5)

        wakewordlab.download(model_name)
        self.detector = wakewordlab.WakewordDetector(
            model_name,
            license_key=license_key,
            threshold=threshold,
            vad=vad,
            vad_threshold=vad_threshold,
            window_sec=self.WINDOW_SAMPLES / self.SAMPLE_RATE,
            stride_sec=self.STRIDE_SAMPLES / self.SAMPLE_RATE,
        )

        self._buffer = np.zeros(self.WINDOW_SAMPLES, dtype=np.float32)
        self._pending_samples = 0  # new samples not yet scored
        self._detected = False

    # ------------------------------------------------------------------
    # HotWordEngine interface
    # ------------------------------------------------------------------

    def update(self, chunk: bytes) -> None:
        """Receive a raw PCM chunk (int16, 16 kHz) and check for detection."""
        # Convert int16 bytes → float32 [-1, 1]
        n_samples = len(chunk) // 2
        samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

        # Append to rolling buffer
        if n_samples >= self.WINDOW_SAMPLES:
            self._buffer[:] = samples[-self.WINDOW_SAMPLES:]
            self._pending_samples = self.WINDOW_SAMPLES
        else:
            self._buffer = np.roll(self._buffer, -n_samples)
            self._buffer[-n_samples:] = samples
            self._pending_samples = min(self._pending_samples + n_samples, self.WINDOW_SAMPLES)

        # Only score once we have at least one stride of new data
        if self._pending_samples >= self.STRIDE_SAMPLES:
            score = self.detector.score(self._buffer.copy())
            self._pending_samples = 0
            if score >= self.detector.threshold:
                self._detected = True

    def found_wake_word(self, frame_data: bytes = b"") -> bool:
        """Return True if a wake word was detected since the last call."""
        result = self._detected
        self._detected = False
        return result

    def reset(self) -> None:
        self._buffer[:] = 0.0
        self._pending_samples = 0
        self._detected = False

    def stop(self) -> None:
        self.reset()
