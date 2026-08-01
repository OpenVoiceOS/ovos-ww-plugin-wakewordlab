# ovos-ww-plugin-wakewordlab

An OVOS wake word plugin backed by [wakewordlab](https://github.com/ubermorgenland/wakewordlab).

Wakewordlab provides compact (~240 KB) neural wake word models with an integrated Silero VAD pre-filter, built for resource-constrained hardware.

## How it works

OVOS feeds raw 16 kHz mono PCM (int16) chunks to `update()`. The plugin keeps a 1-second rolling buffer and scores it every 100 ms with the wakewordlab neural model. When the score passes the configured threshold, the next `found_wake_word()` call returns `True`.

The optional VAD gate, enabled by default, skips scoring during silence frames. This cuts CPU use on idle hardware.

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
| `threshold` | model default | Confidence threshold (0.0-1.0) |
| `vad` | `true` | Enable the Silero VAD pre-filter |
| `vad_threshold` | `0.5` | VAD sensitivity (lower means more permissive) |
| `license_key` | `null` | License key for commercial models |

## Available models

```python
import wakewordlab
print(wakewordlab.list_models())
```

The plugin downloads models on first use and caches them in `~/.cache/wakewordlab/models/`.

Register custom models with `wakewordlab.register_local()`.

## Acknowledgements

This project is part of [OVOS](https://openvoiceos.org) and gets support from the
[NGI0 Commons Fund](https://nlnet.nl/commonsfund/), a fund established by
[NLnet](https://nlnet.nl) with financial support from the European Commission's
[Next Generation Internet](https://ngi.eu) programme.
