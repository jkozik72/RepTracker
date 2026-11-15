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
| Uploads | — | Videos (.mp4, several at once, up to 3 GB each, with a progress bar) and sensor files (.json) into the current mode, in Settings; uploaded videos can be deleted there (× ; not samples, not while a lizard uses them) |
| Per lizard | — | Generate, inspect and send prompts for a time range |
| AI polling (Settings: interval 15 min to 6 h, images per interval, Start / Stop; stopped when the page loads) | Each interval mark of real time | Each interval mark of the dev clock (faster when sped up) |

- **Toy** (`data/toy/`): sample lizards, videos and sensors, committed.
- **Main** (`data/main/`): starts empty; the keeper uploads media and adds lizards. Git-ignored.

The dashboard shows lizards 2 per row, compact (name, alerts, video). Clicking a name opens that lizard to full width; clicking it again closes it. Open, a lizard's video has a full-screen button (Esc exits), and the AI analysis panel has **Analyze**: the last 15 min to 6 h, ending now, sent with the provider in use and the image count set under AI polling. No dev mode needed.

## Research tab: species profiles

Type a species in plain English ("crested gecko", "red-eared slider"). One call to the AI provider in use fills `prompts/profile-schema.json`: temperatures, humidity, UVB, size, lifespan, diet and feeding, droppings, shedding, what a camera can see, body condition, common conditions with their visible signs, and hazards. Up to 6 reference photos come from Wikimedia Commons, with author and licence.

- Saved in `research/<slug>/profile.json` (committed, shared by both modes); photos in `research/<slug>/images/` (git-ignored).
- A lizard whose species matches a profile (typed, common or scientific name) gets it in every analysis prompt, and its live sensor readings are checked against it: each side's temperature against its range, humidity as the average of both sides. Out-of-range readings turn red and become alerts.
- Profiles are AI-written: check them. **Edit** (the JSON) marks a profile as checked; **Regenerate** replaces it; **Delete** removes it and its photos.
- Works with Claude and the Mock (a labelled placeholder); not with Gemini yet.
- Spelling help in both species fields: autocomplete and "Did you mean" from `data/species-names.json` (63 commonly kept reptiles and amphibians with scientific names and nicknames such as "beardie") and existing profiles. It only helps with spelling: any species can be typed.

## Folders (per mode, under `data/<mode>/`)

| Path | What |
|---|---|
| `media/videos/*.mp4` | The "cameras". Each appears in the add-lizard dropdown by file name without `.mp4`. |
| `media/sensors/*.json` | Uploaded "sensors" (the shared defaults below are always available too): `{"t": <ms between samples>, "value": [samples...]}`. Starts when the lizard is added and loops. A name ending `-f`, `-c`, `-rh` or `-gm3` preselects its unit. |
| `reptiles.json` | The lizards on the dashboard. |
| `reptiles/<id>/config.json` | A lizard's configuration (below). |
| `reptiles/<id>/analyses.json` | AI results, newest last (git-ignored). |
| `reptiles/<id>/prompts/<bundle>/` | Generated prompt bundles for inspection (git-ignored). |

Shared: `research/<slug>/` (species profiles, see above), `data/defaults/sensors/*.json` (default sensor files, committed, available in every mode; an upload can't take a default's name), `prompts/` (every prompt format, see its README), `tools/make_samples.py` (regenerates the toy videos and the default sensors; `--sensors-only` skips the videos).

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

`enclosureWidthCm` is optional (`null`). Position is cm from the left wall in both camera views, or, with no enclosure width, % of the video's width from the left edge.

## AI provider

The project uses the **Claude API** ([D4](../../docs/decisions.md)). Three providers are registered in `main.py` (`PROVIDERS`, `ASKERS`); choose one under **Settings → dev mode → AI provider**. The choice is per computer (`data/ai-settings.json`, git-ignored) and applies to analyses and questions.

| Provider | What it is | Needs |
|---|---|---|
| **Mock** (default) | Offline stand-in: position from dark pixels, placeholders for everything else | Nothing |
| **Claude** | The Claude API (`claude_ai.py`); model chosen in Settings | An Anthropic API key |
| **Gemini** | Gemini through Google Vertex AI (`ai.py`) | A Google Cloud project with Vertex AI enabled, and this computer signed in to it |

### Set up Claude (once per computer)

1. Make an API key in the Claude Console (API keys page).
2. In the app: **Settings → dev mode → AI provider → Claude**, paste the key, **Save key**.
3. Pick a **Model** (below the key), select **Claude**, then **Test connection**. The same check from a terminal: `python claude_ai.py`.

The key is kept only on the computer that runs `app.py`, in `data/claude-key.json` (git-ignored), and the page only ever shows a masked version (`sk-ant-…1234`). **Remove** deletes it. Without a saved key, the `ANTHROPIC_API_KEY` environment variable is used instead.

- Models (list prices per million tokens): **Opus 5.5** $4 in / $20 out (default, most capable); **Sonnet 5.5** $2 / $10; **Haiku 5.5** $0.10 / $0.50, cheapest ($0.50 / $2.50 for prompts over 100K tokens; a 1-hour range with 60 images is close to that). The choice is kept in `data/claude-settings.json` (git-ignored).
- One analysis is one request. The reply is constrained to `prompts/response-schema.json` (structured outputs). If Claude declines a request, Anthropic's server-side fallback re-runs it on another Claude model in the same call; the saved analysis notes it. Haiku 5.5 has no fallback: a refusal there fails and nothing is saved.
- Limits checked before sending: 30 MB per request and 600 PDF pages (images). Longer ranges ask for a shorter one.
- Each call is billed to the key's Anthropic account.

| Environment variable (optional) | Default |
|---|---|
| `ANTHROPIC_API_KEY` | none; used only when no key is saved in Settings |
| `REPTRACKER_CLAUDE_MODEL` | `claude-opus-5-5`; used only when no model is chosen in Settings |

### Set up Gemini (once per computer)

There is no API key. The app uses the Google login of the computer it runs on:

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
