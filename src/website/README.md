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

Not decided yet (Q11). Two providers are registered in `main.py` (`PROVIDERS`, `ASKERS`); choose one under **Settings → dev mode → AI provider**. The choice is per computer (`data/ai-settings.json`, git-ignored) and applies to analyses and questions.

| Provider | What it is | Needs |
|---|---|---|
| **Mock** (default) | Offline stand-in: position from dark pixels, placeholders for everything else | Nothing |
| **Gemini** | Gemini through Google Vertex AI (`ai.py`), being tried | A Google Cloud project with Vertex AI enabled, and this computer signed in to it |

### Set up Gemini (once per computer)

There is no API key (Q20). The app uses the Google login of the computer it runs on:

```
gcloud auth application-default login
gcloud auth application-default set-quota-project <project id>
```

Then restart `app.py`. In Settings, Gemini shows **Ready** when the package, the login and a project are found; **Test connection** sends one short request to prove it works. The same check from a terminal: `python ai.py`.

Never commit a project ID, a key, or a credentials file. Nothing in this folder needs one.

| Environment variable (optional) | Default |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | the quota project of the login above |
| `GOOGLE_CLOUD_LOCATION` | `global` |
| `REPTRACKER_MODEL` | `gemini-3.8-flash` |

### What one analysis sends

One HTTPS request per "Send to AI": `system.txt` as the system instruction, then `context.txt` and each IMAGES chunk's text and PDF, in order. No retries and no follow-up requests. The reply must be JSON; `ai.NormalizeResult` forces it into `prompts/response-schema.json`, and nothing is saved if the call fails or the reply cannot be used. Limits set in `ai.py`, not measured against Google's: 18 MB per request (`MAX_REQUEST_MB`), 300 s per analysis (`ANALYSIS_TIMEOUT_S`).

### Tests

```
python -m unittest test_ai -v
```

They never call Google. The tests that drive the real `google-genai` package are skipped when it is not installed.
