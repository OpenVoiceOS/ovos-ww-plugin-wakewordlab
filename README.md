# ovos-ww-plugin-wakewordlab

An OVOS wake word plugin that uses [wakewordlab](https://github.com/ubermorgenland/wakewordlab). Wakewordlab runs compact neural wake word models with a Silero VAD pre-filter, so the plugin can detect wake words while it uses little CPU.

## Install

```bash
pip install ovos-ww-plugin-wakewordlab
```

## Configuration

Add the plugin to `mycroft.conf`:

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
| `threshold` | model default | Confidence threshold (0.0-1.0) |
| `vad` | `true` | Enable the Silero VAD pre-filter |
| `vad_threshold` | `0.5` | VAD sensitivity |
| `license_key` | `null` | License key for commercial models |

## Available models

```python
import wakewordlab
print(wakewordlab.list_models())
```

The plugin downloads models on first use and caches them in `~/.cache/wakewordlab/models/`.

See [docs/index.md](docs/index.md) for more detail on how the plugin scores audio.

## Related projects

- [wakewordlab](https://github.com/ubermorgenland/wakewordlab) - the wake word detection library this plugin wraps
- [OpenVoiceOS](https://github.com/OpenVoiceOS) - the voice assistant platform this plugin serves

---

## Credits

Developed by [TigreGótico](https://tigregotico.pt) for
[OpenVoiceOS](https://openvoiceos.org).

[![NGI0 Commons Fund](./ngi.png)](https://nlnet.nl/project/OpenVoiceOS)

This project was funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund),
a fund established by [NLnet](https://nlnet.nl) with financial support from the
European Commission's [Next Generation Internet](https://ngi.eu) programme, under
the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en)
under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429).
