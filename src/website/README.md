# RepTracker website

Flask app: dashboard of lizards with a simulated camera and sensors, AI prompts, and a dev mode.

## Run

```
cd src/website
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python app.py
```

Open http://127.0.0.1:5000.

## Modes

| | Dev mode off | Dev mode on (Settings) |
|---|---|---|
| Data shown | Main | Toy or Main (switch in Settings) |
| Clock | Real time | Clock bar above the alerts: speed, set time, pause, resume |
| Uploads | — | Videos (.mp4) and sensor files (.json) into the current mode, in Settings |
| Per lizard | — | Generate, inspect and send prompts for a time range |

- **Toy** (`data/toy/`): sample lizards, videos and sensors, committed.
- **Main** (`data/main/`): starts empty; the keeper uploads media and adds lizards. Git-ignored.

The dashboard has a **Full / Compact** view toggle. Compact shows each lizard's name, alerts and video, 2 per row.

## Folders (per mode, under `data/<mode>/`)

| Path | What |
|---|---|
| `media/videos/*.mp4` | The "cameras". Each appears in the add-lizard dropdown by file name without `.mp4`. |
| `media/sensors/*.json` | The "sensors": `{"t": <ms between samples>, "value": [samples...]}`. Starts when the lizard is added and loops. A name ending `-f`, `-c`, `-rh` or `-gm3` preselects its unit. |
| `reptiles.json` | The lizards on the dashboard. |
| `reptiles/<id>/config.json` | A lizard's configuration (below). |
| `reptiles/<id>/analyses.json` | AI results, newest last (git-ignored). |
| `reptiles/<id>/prompts/<bundle>/` | Generated prompt bundles for inspection (git-ignored). |

Shared: `prompts/` (every prompt format, see its README), `research/<species>.json` (species reference for the context chunk, empty for now), `tools/make_samples.py` (regenerates the toy videos and sensors; `--sensors-only` skips the videos).

`data/toy/reptiles/<id>/data.json` is the earlier sample format and is no longer read.

## Lizard config

```json
{
  "name": "Cheeto",
  "species": "leopard gecko",
  "enclosureWidthCm": 90,
  "createdAt": "2026-11-12T00:00:00Z",
  "camera": {"view": "top", "video": "gecko-top"},
  "sensors": {
    "hotSide": "left",
    "hot":  {"temperature": {"series": "hot-temp-f",  "unit": "F"}, "humidity": {"series": "hot-humidity-rh",  "unit": "%RH"}},
    "cold": {"temperature": {"series": "cold-temp-f", "unit": "F"}, "humidity": {"series": "cold-humidity-rh", "unit": "%RH"}}
  }
}
```

Position is cm from the left wall in both camera views.

## AI provider

Not chosen yet (Q11), so every request goes to the offline **Mock** provider (`PROVIDER` in `main.py`). Add a real one as a function in `PROVIDERS`; it will also need a way to supply its API key.
