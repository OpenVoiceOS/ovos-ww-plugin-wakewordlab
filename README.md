# ovos-ww-plugin-wakewordlab

OVOS wake word plugin using [wakewordlab](https://github.com/ubermorgenland/wakewordlab) — compact neural wake word detection with Silero VAD pre-filtering.

## Install

```bash
pip install ovos-ww-plugin-wakewordlab
```

## Configuration

In `mycroft.conf`:

```json
{
  "hotwords": {
    "hey jarvis": {
      "module": "ovos-ww-plugin-wakewordlab",
      "model": "hey_jarvis",
      "threshold": 0.5,
      "vad": true,
      "vad_threshold": 0.5
    }
  }
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `model` | key phrase | Wake word slug or path to a `.wkw`/`.onnx` model file |
| `threshold` | model default | Confidence threshold (0.0–1.0) |
| `vad` | `true` | Enable Silero VAD pre-filter |
| `vad_threshold` | `0.5` | VAD sensitivity |
| `license_key` | `null` | License key for commercial models |

## Available models

```python
import wakewordlab
print(wakewordlab.list_models())
```

Models are downloaded and cached in `~/.cache/wakewordlab/models/` on first use.
