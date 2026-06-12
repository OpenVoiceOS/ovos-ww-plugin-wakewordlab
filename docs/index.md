# ovos-ww-plugin-wakewordlab

OVOS wake word plugin backed by [wakewordlab](https://github.com/ubermorgenland/wakewordlab).

Wakewordlab provides compact (~240 KB) neural wake word models with integrated Silero VAD pre-filtering, designed for resource-constrained hardware.

## How it works

OVOS feeds raw 16 kHz mono PCM (int16) chunks to `update()`. The plugin maintains a 1-second rolling buffer and scores it every 100 ms using the wakewordlab neural model. When the score exceeds the configured threshold, the next `found_wake_word()` call returns `True`.

The optional VAD gate (enabled by default) skips scoring during silence frames, significantly reducing CPU usage on idle hardware.

## Installation

```bash
pip install ovos-ww-plugin-wakewordlab
```

## Configuration

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
| `model` | key phrase | Wake word slug or path to a `.wkw`/`.onnx` model |
| `threshold` | model default | Confidence threshold (0.0–1.0) |
| `vad` | `true` | Enable Silero VAD pre-filter |
| `vad_threshold` | `0.5` | VAD sensitivity (lower = more permissive) |
| `license_key` | `null` | License key for commercial models |

## Available models

```python
import wakewordlab
print(wakewordlab.list_models())
```

Models are downloaded and cached in `~/.cache/wakewordlab/models/` on first use.

Custom models can be registered with `wakewordlab.register_local()`.

## Acknowledgements

This project is part of [OVOS](https://openvoiceos.org) and supported by the
[NGI0 Commons Fund](https://nlnet.nl/commonsfund/), a fund established by
[NLnet](https://nlnet.nl) with financial support from the European Commission's
[Next Generation Internet](https://ngi.eu) programme.
