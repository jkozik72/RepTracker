# RepTracker Judge Synthesis & Filtered Zookeeper Data Specification (Updated for Commit `354b76a`)

## 1. Judge Synthesis: RepTracker Data Architecture & Latest Repository Updates

To establish an up-to-date technical baseline of [jkozik72/RepTracker](https://github.com/jkozik72/RepTracker/), the repository was re-inspected in strictly read-only mode through its latest commit history ([`commits/main`](https://github.com/jkozik72/RepTracker/commits/main/)). RepTracker is a reptile-husbandry monitoring application built for Hack The Nest that combines looping simulated environmental sensor streams, enclosure video feeds, and multimodal AI vision analysis across three selectable providers: **Mock** (offline pixel-darkness estimator), **Gemini** ([src/website/ai.py](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/ai.py) via Vertex AI), and **Claude** ([src/website/claude\_ai.py](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/claude_ai.py) supporting Opus 5.5, Sonnet 5.5, and Haiku 5.5).

### 1.1 What Changed in the Latest Repository Updates (Commits `e66f664` & `354b76a`)

The latest commits—particularly [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3) (*"Dashboard: AI polling, Claude model choice, editing, deletes, full screen"*, 19 files changed, +640 / -111) and `e66f664` (*"Add Claude as the AI provider; vision questions, hourly AI call, no looped frames"*)—introduced several architectural upgrades that directly affect which zookeeper recommendations can be built right now:

1. **In-Place Lizard Editing (`UpdateLizard` & `LizardConfigFromForm`):** Added in [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py), [`src/website/app.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/app.py) (`PUT /api/<mode>/lizards/<lizard_id>`), and documented in [`docs/functions.md`](https://github.com/jkozik72/RepTracker/blob/main/docs/functions.md) and [docs/notes/2026-11-15-delete-cameras-edit-lizards-chat.md](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/docs/notes/2026-11-15-delete-cameras-edit-lizards-chat.md). Editing a lizard updates its `config.json` **without wiping its `id`, `createdAt` start timestamp, or `analyses.json` history**.
2. **Configurable AI Polling & Variable Frame Spacing:** Documented in [docs/notes/2026-11-15-ai-polling-chat.md](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/docs/notes/2026-11-15-ai-polling-chat.md), the fixed hourly toggle was replaced with a configurable polling interval (`15 min` to `6 h`), user-chosen **images per interval** (spread evenly across the window, at least 1 minute apart, with `{{image_spacing}}` injected into [src/website/prompts/images-chunk.txt](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/images-chunk.txt)), and explicit Start/Stop controls.
3. **No Looped Video Frames:** Frame extraction no longer wraps around and samples duplicate looped video frames past the end of a clip (`e66f664`), preventing artificial repetition in `Movement Data`.
4. **Dashed Null-Position Movement Graph with Unseen-Frame Ticks:** When `position` is `null` (`"can't see lizard"`), the movement graph in [src/website/templates/index.html](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/templates/index.html) now bridges unseen gaps with a **dashed line and tick marks** for the missing frames rather than hiding the gap or treating it as zero.
5. **Always-On Vision for Keeper Q&A:** Per [docs/notes/2026-11-15-vision-always-on-chat.md](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/docs/notes/2026-11-15-vision-always-on-chat.md), asking a question via [src/website/prompts/ask.txt](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/ask.txt) now **always attaches the current live camera frame** and renders the AI response as Markdown.
6. **Direct "Analyze" & Full-Screen Video Outside Dev Mode:** Per [docs/notes/2026-11-15-fullscreen-analyze-chat.md](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/docs/notes/2026-11-15-fullscreen-analyze-chat.md), keepers can run on-demand analyses (15 min to 6 h ending now) and open full-screen video directly from the expanded lizard card, while uploaded videos can be deleted via `DELETE /api/<mode>/media/videos/<name>` (`DeleteVideo`, which protects `SAMPLE_VIDEOS = {"toy": {"gecko-top", "skink-side", "short-clip-top"}}` and active lizards).
7. **Both Species Research Files Are Confirmed Empty (`0 Bytes`):** Both [`src/website/research/leopardgecko.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/leopardgecko.json) and [`src/website/research/skink.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/skink.json) are currently **0 lines (`0 Bytes`)**, even though [`src/website/prompts/context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) injects `Species reference (research/{{species_file}}): {{research}}` into every prompt bundle.

### 1.2 Repository Component & Data File Map

| Component Layer | Repository Path | Data Format & Key Constants | Current Role & Constraints |
| :--- | :--- | :--- | :--- |
| **Core Backend & Orchestrator** | [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py), [`src/website/app.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/app.py), [`docs/functions.md`](https://github.com/jkozik72/RepTracker/blob/main/docs/functions.md) | `MODES = ["toy", "main"]`, `SPECIES = ["leopard gecko", "skink"]`, `CAMERA_VIEWS = ["top", "side"]`, `SIDES = ["left", "right"]`, `TEMP_UNITS = ["F", "C"]`, `HUMIDITY_UNITS = ["%RH", "g/m3"]`, `IMAGES_PER_CHUNK = 60`, `MAX_RANGE_MIN = 360`, `MAX_UPLOAD_GB = 3` | Manages simulated clock playback, sensor time-series slicing, non-looping video frame extraction into PDF chunks, `LizardConfigFromForm`, `UpdateLizard`, `DeleteVideo`, `GeneratePrompts`, and AI provider routing. |
| **Simulated Sensor Streams** | [src/website/data/defaults/sensors/](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/tree/main/src/website/data/defaults/sensors) (`cold-humidity-rh.json`, `cold-temp-c.json`, `cold-temp-f.json`, `hot-humidity-rh.json`, `hot-temp-c.json`, `hot-temp-f.json`) | JSON time-series: `{"t": <ms between samples>, "value": [<float>, ...]}` generated via [src/website/tools/make\_samples.py](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/tools/make_samples.py) | Shared via `DEFAULT_SENSORS` across modes. Simulates **two stations** (`hot` and `cold`), each with **two channels** (`temperature` and `humidity`). Does not simulate surface probes, UV meters, or inside-hide sensors by default. |
| **Simulated Camera Feeds** | [src/website/data/toy/media/videos/](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/tree/main/src/website/data/toy/media/videos) (`gecko-top.mp4`, `short-clip-top.mp4`, `skink-side.mp4`) | `.mp4` video files up to 3 GB; evenly spaced frames (`>= 1 min` apart, up to `IMAGES_PER_CHUNK = 60` per PDF) without looping past video end | Extracts still frames into chronological PDFs for AI vision inspection, plus attaches the current live frame to every `AskQuestion` call ([ask.txt](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/ask.txt)). |
| **Per-Reptile Index & Config** | [`src/website/data/toy/reptiles.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/data/toy/reptiles.json), [`reptiles/cheeto/config.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/data/toy/reptiles/cheeto/config.json), [reptiles/joules/config.json](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/data/toy/reptiles/joules/config.json) | `name`, `species`, `enclosureWidthCm` (nullable), `createdAt`, `camera` (`view`, `video`), and `sensors` (`hotSide`: `"left"` or `"right"`, plus `hot` and `cold` series mappings) | Editable in place via `PUT /api/<mode>/lizards/<lizard_id>` (`UpdateLizard`). Tracks 1D horizontal width (`cm` from left wall, or `%` of video width if `enclosureWidthCm` is `null`). |
| **Prompt Pipeline & Output Schema** | [`src/website/prompts/`](https://github.com/jkozik72/RepTracker/tree/main/src/website/prompts) ([`system.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/system.txt), [`context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt), [images-chunk.txt](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/images-chunk.txt), [ask.txt](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/ask.txt), [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json)) | Strict JSON response schema (`additionalProperties: false`): `Weight`, `Shed`, `Food in bowl`, `Current activity`, `Hazardous conditions`, `Movement Data`, `Analysis` | Injects `{{sensor_summary}}` (min/mean/max/latest), `{{research}}`, and `{{previous_analysis}}` into `context-chunk.txt`. Enforces `"can't see lizard"` when hidden rather than guessing. |
| **Species Knowledge Base** | [`src/website/research/`](https://github.com/jkozik72/RepTracker/tree/main/src/website/research) ([`leopardgecko.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/leopardgecko.json), [`skink.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/skink.json)) | Per-species JSON files loaded into `{{research}}` in [`context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) | **Both files are currently 0 bytes (`empty`)**, meaning populating them is the single highest-leverage zero-code improvement available right now. |

## 2. New Ideas Unlocked by the Latest Repo Updates (`354b76a` & `e66f664`)

Because the latest commits added **in-place lizard editing (`UpdateLizard`)**, **always-on vision Q&A (`ask.txt`)**, **dashed unseen-frame movement graphs**, and **non-looping variable-spacing frame chunks**, you can now implement several high-impact ideas that bridge the zookeeper's advice with your exact codebase:

1. **Zero-Code Immediate Upgrade — Populate Both 0-Byte Research Files (`leopardgecko.json` & `skink.json`):**
   * Because [`context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) already injects `Species reference (research/{{species_file}}): {{research}}`, pasting the structured zookeeper thresholds, body-condition landmarks, and normal-vs-alarming behavior rules into [`src/website/research/leopardgecko.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/leopardgecko.json) and [`src/website/research/skink.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/skink.json) immediately gives Gemini and Claude species-specific temperature, humidity, gradient, and false-alarm rules **without changing a single line of Python**. (Complete ready-to-paste JSON payloads for both files are provided in Section 7 below.)
2. **Piggyback Husbandry & Health Fields onto the New `UpdateLizard` Edit Modal (`LizardConfigFromForm`):**
   * Commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3) added `UpdateLizard` (`PUT /api/<mode>/lizards/<lizard_id>`) so editing a lizard preserves its `analyses.json` history. You can add 5 lightweight optional fields to `LizardConfigFromForm` in [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py) and the Edit Lizard form in [src/website/templates/index.html](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/templates/index.html):
     * `scaleWeightGrams` (number) + `lastWeighedAt`
     * `lastFedAt` (date/time) -> automatically displays **"Days since last meal"**
     * `baskingSurfaceTempSpotCheck` (number, from a handheld IR thermometer)
     * `uvbInstalledAt` (date) -> automatically flags bulbs older than 6–12 months
     * `brumationMode` (boolean toggle to suppress appetite/hiding false alarms in winter)
3. **Turn the New Dashed Null-Position Graph into a "Zone Time Budget + Visibility Coverage" Bar:**
   * Commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3) already detects `position == null` frames in [src/website/templates/index.html](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/templates/index.html) to draw dashed segments and ticks. Using that exact same `Movement Data` array and `config.sensors.hotSide` (`"left"` or `"right"`), you can render a 4-segment horizontal bar right above the chart showing:
     * **Hot Third %** (`[0, max/3)` if `hotSide == "left"`, else `(2*max/3, max]`)
     * **Middle Third %** (`[max/3, 2*max/3]`)
     * **Cool Third %** (opposite third)
     * **Not Visible / Hidden %** (`position == null` count / total frames) — directly satisfying the zookeeper's #4 priority and Data Quality requirement in ~15 lines of frontend JS.
4. **Computed Sensor Gradient & Day/Night Split Inside `{{sensor_summary}}`:**
   * Right now, `{{sensor_summary}}` in [`context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) reports `min / mean / max / latest` for `hot` and `cold` temperature and humidity. In [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py), you can append two derived lines to `{{sensor_summary}}`:
     * `Thermal gradient (hot - cold): min / mean / max / latest` (warming the keeper if the gradient collapses below `3 °C` / `5.4 °F`).
     * `Misting spikes detected: <count>` (counting sharp humidity jumps of `>= 15 %RH` between adjacent samples).
5. **Quick-Tap Zookeeper Prompts for the New Always-On Vision Q&A (`ask.txt`):**
   * Because [ask.txt](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/ask.txt) now **always sends the current live camera frame** (`2026-11-15-vision-always-on-chat.md`), you can add 3–4 one-click "Keeper Check" preset chips next to the question input in [index.html](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/templates/index.html):
     * *"Check body condition landmarks (tail base vs. neck width)"*
     * *"Check water bowl & substrate hazards in current frame"*
     * *"Is my lizard's current posture or hiding normal for its species at this hour?"*
6. **Leverage `{{previous_analysis}}` for Rolling Trend Comparison:**
   * Notice that [`context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) already passes `Previous analysis: {{previous_analysis}}`! With the new AI polling loop (`354b76a`), you can pass a compact summary of the last N analyses from `analyses.json` (average hot-zone %, average visibility %, previous shed state) into `{{previous_analysis}}` so the LLM can flag behavioral shifts across consecutive polling windows.

## 3. Filtering the Zookeeper's Top 10 Ranked Priorities Against Current Repo

| Rank | Zookeeper Priority | Status in RepTracker (`354b76a`) | How to Realize or Filter in [jkozik72/RepTracker](https://github.com/jkozik72/RepTracker/) |
| :--- | :--- | :--- | :--- |
| **1** | **Zone-by-zone & time-of-day heat evaluation against species ranges** (basking surface, warm air, cool air, night) | **Realizable Now (Air & Gradient) / Simulated or Form Input (Basking Surface)** | Warm-side air (`hot.temperature`) and cool-side air (`cold.temperature`) already exist in [data/defaults/sensors/](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/tree/main/src/website/data/defaults/sensors). Populate [`leopardgecko.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/leopardgecko.json) and [`skink.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/skink.json) so the AI checks warm-side air, cool-side air, night air, and `hot - cold` gradient separately. Add a `baskingSurfaceTemp` field to `UpdateLizard` (or a 3rd simulated `basking-temp` JSON in [make\_samples.py](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/tools/make_samples.py)). |
| **2** | **Feeding record with "days since last confirmed meal"** | **Realizable via `UpdateLizard` Form + `"Food in bowl"`** | Video sampled at `>= 1 min` spacing (`IMAGES_PER_CHUNK = 60`) misses 2-second insect strikes. Keep `"Food in bowl"` from [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json) for salad/pellet dishes, and add `lastFedAt` to the `UpdateLizard` modal (`354b76a`) to display `daysSinceLastMeal`. |
| **3** | **Body weight in grams from a scale + rename camera `"Weight"` label** | **Realizable Now (UI Label Rename + `UpdateLizard` Field)** | In [index.html](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/templates/index.html) (or [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json)), relabel the AI's `"Weight"` output (`"obese" \| "overweight" \| "healthy" \| "underweight" \| "emaciated" \| "can't see lizard"`) as **"Body Condition (Camera Estimate)"**, and add a manual `scaleWeightGrams` input to `UpdateLizard`. |
| **4** | **Zone occupancy time budget vs. baseline + visibility %** | **Realizable Now from `Movement Data` & `previous_analysis`** | Commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3) already parses `Movement Data` (`position` vs. `null`) for the dashed movement plot. Bucket non-null positions into Hot Third, Middle Third, and Cool Third using `sensors.hotSide`, display `Visibility %` (`non_null / total`), and compare against prior runs stored in `analyses.json`. |
| **5** | **Faeces and urates log (date & appearance)** | **Realizable via `UpdateLizard` Form Only** | Whole-enclosure cameras on bark/soil substrate (`skink-side.mp4`, `gecko-top.mp4`) cannot distinguish urate color or faecal consistency. Add `lastFaecesAt` and `urateNormal` to the `UpdateLizard` form. |
| **6** | **Lighting record (day length delivered, UVB lamp type, distance, age)** | **Realizable Now (Frame Brightness + `UpdateLizard` UVB Date)** | Optical cameras cannot measure UV degradation, so instruct [`system.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/system.txt) never to infer UVB adequacy from bulb brightness. Add `uvbInstalledAt` to `UpdateLizard` for a 6-month replacement alert, and compute lights-on vs. lights-off from frame brightness in [`main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py). |
| **7** | **Humidity day/night cycle vs. species pattern + humid retreat check** | **Realizable Now** | `hot.humidity` and `cold.humidity` (`%RH`) are simulated in [data/defaults/sensors/](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/tree/main/src/website/data/defaults/sensors). Compare against day/night humidity targets in `research/<species>.json` and add a `hasHumidHide` checkbox in `UpdateLizard`. |
| **8** | **Shed record with completeness check of toes, tail tip, and eyes** | **Realizable Now (Coarse AI Shed + Keeper Prompt)** | Keep `"Shed": "soon" \| "now" \| "not shedding" \| "can't see lizard"` in [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json), and show a reminder banner on the lizard card to inspect toes, tail tip, and eyes whenever `"Shed"` is `"now"` or recently completed. |
| **9** | **Animal identity & history (`species` dropdown, `sex`, `age`, `morph`, notes)** | **Realizable Now** | `SPECIES = ["leopard gecko", "skink"]` is already a dropdown in [`main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py)! Add optional `sex`, `ageClass`, `morphFlags`, and `keeperNotes` to `LizardConfigFromForm` (`354b76a`). |
| **10** | **Reproductive status of females (gravid, digging, lay box)** | **Realizable via `UpdateLizard` + AI Digging Hint** | Relevant to egg-layers (`leopard gecko`), whereas northern blue-tongued skinks ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)) are live-bearers and need no lay box. Document this distinction in `research/skink.json` and `research/leopardgecko.json`. |

## 4. Complete Data Point Filtering Matrix (All 43 Zookeeper Data Points)

### 4.1 Immediately Realizable Data Points (Tier 1 — Implementable in Current Repo)

| Data Point | Capture Source | How It Maps to RepTracker (`main.py`, `config.json`, `prompts/`, `index.html`) |
| :--- | :--- | :--- |
| **1. Species (exact pick-list)** | `manual_entry` (`config.json`) | Already enforced in [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py) as `SPECIES = ["leopard gecko", "skink"]`. Can be expanded to `"bearded dragon"`, `"crested gecko"`, and `"veiled chameleon"` by adding matching JSON files in [`src/website/research/`](https://github.com/jkozik72/RepTracker/tree/main/src/website/research). |
| **2. Air temperature, hot side & cool side** | `sensor_existing` (`data/defaults/sensors/*.json`) | Already implemented via `hot.temperature` and `cold.temperature` series (`hot-temp-c.json`, `hot-temp-f.json`, `cold-temp-c.json`, `cold-temp-f.json`) summarized as `min / mean / max / latest` in `{{sensor_summary}}`. |
| **3. Thermal gradient (`hot - cold`)** | `derived` (`main.py`) | Compute directly in [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py) by subtracting `cold.temperature` from `hot.temperature` across the requested time window and passing `gradient_min / mean / max / latest` into `{{sensor_summary}}`. |
| **4. Relative humidity, both stations** | `sensor_existing` (`data/defaults/sensors/*.json`) | Already implemented via `hot.humidity` and `cold.humidity` (`hot-humidity-rh.json`, `cold-humidity-rh.json`). |
| **5. Zone occupancy time budget** | `derived` (`main.py` / `index.html` from `Movement Data`) | Using `Movement Data` and `sensors.hotSide`, divide `0..position_max` into three equal zones (`[0, max/3)`, `[max/3, 2*max/3]`, `(2*max/3, max]`) to display % time in `Hot Third`, `Middle Third`, `Cool Third`, and `Not Visible` (`position == null`). |
| **6. Data quality & visibility coverage** | `derived` (`main.py` / `index.html`) | Building on commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3)'s dashed unseen-frame graph, compute `visible_frames_pct = 100 * count(position != null) / len(Movement Data)` and display it prominently on the lizard card. |
| **7. Distance moved (1D horizontal)** | `derived` (`main.py` / `index.html` from `Movement Data`) | Sum `abs(position[i] - position[i-1])` across consecutive non-null frames in `Movement Data` (in `cm` when `enclosureWidthCm` is set, or `% width` when `enclosureWidthCm` is `null`). |
| **8. Photoperiod (lights-on / lights-off)** | `camera_ai` / `derived` (frame brightness) | In [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py), compute mean pixel luminance for each sampled video frame so `context-chunk.txt` knows whether the frame window is lights-on, lights-off, or mixed. |
| **9. Body condition score (relabeled from `"Weight"`)** | `camera_ai` ([`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json)) | Already in [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json) as `"Weight": "obese" \| "overweight" \| "healthy" \| "underweight" \| "emaciated" \| "can't see lizard"`. Relabel as `"Body Condition"` in the UI (or schema) and supply species landmarks via `research/<species>.json`. |
| **10. Shed stage (coarse visual)** | `camera_ai` ([`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json)) | Already implemented as `"Shed": "soon" \| "now" \| "not shedding" \| "can't see lizard"`. |
| **11. Bowl state (food & water)** | `camera_ai` ([`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json) & `ask.txt`) | `"Food in bowl"` (`"true" \| "false" \| "no bowl visible"`) is already implemented. Water bowl state can be added to [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json) or checked on-demand via the always-on vision Q&A ([ask.txt](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/ask.txt)). |
| **12. Coarse behaviour state** | `camera_ai` ([`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json)) | Currently `"Current activity": "basking" \| "exploring" \| "hiding" \| "can't see lizard"`. Can expand enum to include `"resting in open"`, `"climbing"`, `"digging"`, `"soaking"`, and `"glass-surfing"`. |
| **13. Position-based abnormal behaviour flags** | `camera_ai` + `derived` | Detectable across multi-frame PDF chunks and reported in `"Hazardous conditions" -> "Other"` or `"Signs of disease"`: `glass-surfing`, `persistent digging`, `pressed against cool wall all window`, `under lamp all window`. |
| **14–26. Keeper Husbandry & Health Metadata (`sex`, `ageClass`, `morphFlags`, `origin`, `animalCount`, `enclosureDepthCm`/`HeightCm`, `substrateType`, `heatSource`/`onThermostat`, `uvbInstalledAt`, `hasHumidHide`, `waterDelivery`, `lastFedAt`, `scaleWeightGrams`, `lastFaecesAt`, `brumationMode`, `keeperNotes`)** | `manual_entry` via `LizardConfigFromForm` & `UpdateLizard` (`354b76a`) | Because commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3) added `LizardConfigFromForm` and `UpdateLizard` (`PUT /api/<mode>/lizards/<lizard_id>`), any subset of these manual keeper fields can be stored directly in `config.json` and passed into [`context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) without altering the sensor simulator. |

### 4.2 Partially Realizable / Simulation-Extendable Data Points (Tier 2 — Requires Simulated Series Addition or Caveats)

| Data Point | Why It Is Constrained in Current Repo | Realistic Path in RepTracker |
| :--- | :--- | :--- |
| **27. Basking surface temperature** | Current sensor JSONs ([hot-temp-f.json](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/data/defaults/sensors/hot-temp-f.json), [hot-temp-c.json](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/data/defaults/sensors/hot-temp-c.json)) represent ambient hot-side air, whereas basking surfaces under a lamp run 8–15 °C hotter ([ReptiFiles Leopard Gecko Care Sheet](https://reptifiles.com/wp-content/uploads/2020/10/Leopard-Gecko-Care-Sheet-PDF.pdf)). | **Option A (Manual):** Add `baskingSurfaceTemp` to `UpdateLizard` (keeper IR thermometer reading). **Option B (Simulated Sensor):** Generate `basking-temp-c.json` / `basking-temp-f.json` via [make\_samples.py](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/tools/make_samples.py). |
| **28. Night-time temperature minimum & night drop** | Analysis range is capped at `MAX_RANGE_MIN = 360` (6 hours). | When the simulated clock in Dev Mode runs across night hours (or over a 6-hour evening-to-night window), compare `sensor_summary` against the species' night temperature range in `research/<species>.json`. |
| **29. Activity by hour of day (24-hour rhythm)** | Single analysis calls cap at 6 hours, and `gecko-top.mp4` is a daytime visible-light recording (no infrared night vision for nocturnal leopard geckos). | Aggregate `Movement Data` across sequential polling runs stored in `analyses.json` (enabled by commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3)'s AI polling loop), and note in `research/leopardgecko.json` that daytime inactivity is normal. |
| **30. Vertical position / perch height** | `Movement Data` in [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json) only tracks 1D horizontal `position` (`0` to `position_max`). | Only meaningful when `camera.view == "side"` (e.g., `skink-side.mp4` or arboreal species). Can be described qualitatively in `Analysis` or queried via `ask.txt` when `camera_view == "side"`. |
| **31. Change from the animal's own baseline** | Toy mode starts with short video clips (`gecko-top.mp4`, `skink-side.mp4`) and no 14-day history. | Use `{{previous_analysis}}` in [`context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) (or summarize the last N entries of `analyses.json`) to compare the current window against earlier polling windows. |
| **32–34. Estimated UVI, Static Posture Anomalies & Colour State** | No UV sensor exists; 1-fpm frames show only static posture; lamp tint distorts color. | Estimate UVI from manual bulb type + distance; instruct the AI in `research/skink.json` that skinks naturally carry their bellies low ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)); treat color changes as context in `Analysis` rather than hard alerts. |

### 4.3 Unrealistic Data Points to Exclude from Camera/Sensor Automation (Tier 3)

| Excluded Camera/Sensor Feature | Why It Is Unrealistic in RepTracker | Required Safe Handling |
| :--- | :--- | :--- |
| **True body weight in grams from camera** | A 2D monocular camera (`gecko-top.mp4`, `skink-side.mp4`) cannot measure mass in grams or detect a 10% weight loss. | Never output grams from [ai.py](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/ai.py) or [claude\_ai.py](https://www.google.com/search?q=https://github.com/jkozik72/RepTracker/blob/main/src/website/claude_ai.py); treat camera `"Weight"` strictly as a visual body-condition score and use manual scale entry for grams. |
| **Camera-inferred UVB adequacy** | UVB phosphor decays over 6–12 months while visible light remains bright ([RSPCA Leopard Gecko Care Sheet](https://www.rspca.org.uk/adviceandwelfare/pets/other/leopardgecko)). | Instruct [`system.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/system.txt) that `"Unsafe lighting"` may only flag visibly unguarded bulbs inside the enclosure, light during dark hours, or failed bulbs—never whether UVB output is sufficient. |
| **Sub-minute events at `>= 1 min` frame spacing (feeding strikes, drinking, defecation, gecko shedding)** | Commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3) spaces frames at least 1 minute apart (`IMAGES_PER_CHUNK = 60`); feeding strikes and drinking take seconds, and geckos shed at night and eat the skin ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/leopardgecko)). | Do not claim `"lizard did not drink or eat"` from frame chunks; rely on bowl state and manual feeding logs. |
| **Gait tremors, limps, and breathing acoustics** | Still frames compiled into a PDF (`images-chunk.txt`) have `>= 1 min` gaps between frames and no audio track. | Exclude tremor, limp, and wheezing detection from automated PDF chunk analysis; reserve for manual keeper check. |
| **Fine anatomical resolution (retained toe shed, mites, nostril/vent mucus)** | Whole-enclosure 360p/720p videos lack the pixel resolution to resolve 1–2 mm constriction rings on gecko toes or mites. | Prompt the keeper to inspect toes, tail tip, and eyes in person 48 hours after a shed. |
| **Inside-hide microclimate humidity & soil faecal consistency** | The two simulated hygrometers measure open enclosure air, not the 70–80% RH inside an enclosed moist hide ([Zen Habitats / ReptiFiles](https://www.zenhabitats.com/pages/leopard-gecko-care-sheet-provided-by-reptifiles)). | Track moist-hide re-wetting and faecal consistency via keeper form entries rather than open-air sensors. |
| **Aquatic / Amphibian Water Chemistry (Turtles, Frogs, Axolotls, Fish)** | Aquatic species require water temperature, ammonia, nitrite, nitrate, and pH sensors not present in the hot/cold air sensor architecture. | Keep active support focused on lizards (`leopard gecko`, `skink`, plus expansion lizard profiles) and treat aquatic sensor templates as future roadmap items. |

## 5. Species Reference Summary Table (Current Repo Species + 3 Expansion Lizards)

| Parameter / Threshold | Leopard Gecko (*Eublepharis macularius*) — **In Repo Now** | Northern Blue-Tongued Skink (*Tiliqua scincoides intermedia*) — **In Repo Now** | Bearded Dragon (*Pogona vitticeps*) — **Expansion** | Crested Gecko (*Correlophus ciliatus*) — **Expansion** | Veiled Chameleon (*Chamaeleo calyptratus*) — **Expansion** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lifestyle & Recommended Camera** | Terrestrial, crepuscular/nocturnal (`top` camera; invisible in hide all day is normal) ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/leopardgecko)) | Terrestrial burrower, diurnal (`side` or `top` camera; buries in substrate for hours) ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)) | Terrestrial + climber, diurnal (`side` or `top` camera; invisible all day outside brumation is abnormal) ([RSPCA](https://rspca.org.uk/adviceandwelfare/pets/other/beardeddragon)) | Arboreal, crepuscular/nocturnal (`side` camera; sleeps motionless all day; floor = emergency) ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/crestedgecko)) | Strictly arboreal, diurnal (`side` camera; sensors at perch height; floor = emergency except egg-laying) ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet)) |
| **Hot-Side Air Temp (Lights-On)** | **28–30 °C** (82–86 °F); POTZ 25–30 °C ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/leopardgecko), [Merck](https://www.merckvetmanual.com/multimedia/table/important-husbandry-requirements-for-selected-reptiles)) | **28–32 °C** air (basking spot 33–38 °C / 92–100 °F) ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)) | **25–32 °C** POTZ air (basking surface 38–42 °C) ([Merck](https://www.merckvetmanual.com/multimedia/table/important-husbandry-requirements-for-selected-reptiles), [RSPCA](https://rspca.org.uk/adviceandwelfare/pets/other/beardeddragon)) | **26–28 °C** (78–82 °F) at top perch ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/crestedgecko), [ReptiFiles](https://reptifiles.com/crested-gecko-care/crested-gecko-temperatures-humidity)) | **29–35 °C** at top basking perch; **22–26 °C** mid-enclosure air ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet)) |
| **Cool-Side Air Temp (Lights-On)** | **21–26 °C** (70–79 °F) ([ReptiFiles PDF](https://reptifiles.com/wp-content/uploads/2020/10/Leopard-Gecko-Care-Sheet-PDF.pdf), [RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/leopardgecko)) | **21–29 °C** (70–85 °F) ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)) | **22–26 °C** (RSPCA) / **21–29 °C** ([ReptiFiles 2026 PDF](https://reptifiles.com/wp-content/uploads/2026/01/Bearded-Dragon-Care-Sheet-ReptiFiles.pdf)) | **20–24 °C** (68–75 °F) at bottom ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/crestedgecko)) | **22–26 °C** (72–78 °F) ambient ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet)) |
| **Night Air Temp (Lights-Off)** | **18–24 °C** (min **16 °C** / 60 °F) ([The Bio Dude](https://www.google.com/search?q=https://thebiodude.com/blogs/gecko-caresheets/leopard-gecko-caresheet-2024-updated)) | **21–24 °C** (min **18 °C**) ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)) | **18–24 °C** (not below **20–22 °C** per [RSPCA](https://rspca.org.uk/adviceandwelfare/pets/other/beardeddragon), [Phoenix Herp](https://www.phoenixherp.com/assistance/reptile-care-guides/bearded-dragon-care-guide.html)) | **18–22 °C** (64–72 °F); night drop beneficial ([ReptiFiles](https://reptifiles.com/crested-gecko-care/crested-gecko-temperatures-humidity)) | **13–18 °C** (55–65 °F); mandatory night drop, zero night heat/light ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet), [Dubia Roaches](https://dubiaroaches.com/blogs/chameleon-care/veiled-chameleon-care-sheet)) |
| **Emergency Overheating Threshold (Air, 30+ min)** | Cool side **> 30 °C** (86 °F) or hot air **> 34 °C** (93 °F) ([Merck](https://www.merckvetmanual.com/multimedia/table/important-husbandry-requirements-for-selected-reptiles)) | Cool side **> 32 °C** (90 °F) ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)) | Cool side **> 32 °C** (90 °F) ([Merck](https://www.merckvetmanual.com/multimedia/table/important-husbandry-requirements-for-selected-reptiles)) | Any zone **> 29 °C** (85 °F) — high heat-stroke risk ([ReptiFiles](https://reptifiles.com/crested-gecko-care/crested-gecko-temperatures-humidity)) | Mid-enclosure air **> 30 °C** (86 °F) with no cool shade ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet)) |
| **Humidity (%RH) & Humid Hide** | **30–40 %RH** day (20–30% Merck); **humid hide at 70–80 %RH required** ([The Bio Dude](https://www.google.com/search?q=https://thebiodude.com/blogs/gecko-caresheets/leopard-gecko-caresheet-2024-updated), [Zen Habitats](https://www.zenhabitats.com/pages/leopard-gecko-care-sheet-provided-by-reptifiles)) | **40–60 %RH** (Northern); deep slightly moist substrate 10–15 cm ([Zen Habitats / ReptiFiles](https://www.zenhabitats.com/blogs/reptile-care-sheets-resources/blue-tongued-skink-care-sheet-reptifiles)) | **30–40 %RH** (keep **< 60 %RH**) ([Merck](https://www.merckvetmanual.com/multimedia/table/important-husbandry-requirements-for-selected-reptiles), [Fluker Farms](https://flukerfarms.com/reptile-u/care-sheets/bearded-dragon-care-sheet)) | **50 %RH** day dry-out to **80+ %RH** night spike (60–80% avg) ([Reptile Supply](https://reptilesupply.com/blogs/care-sheets/how-to-care-for-your-crested-gecko), [PetMD](https://www.petmd.com/reptile/crested-gecko-care-sheet)) | **30–50 %RH** day, **75–100 %RH** night wet-dry cycle ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet), [Dubia Roaches](https://dubiaroaches.com/blogs/chameleon-care/veiled-chameleon-care-sheet)) |
| **Target UVI & Ferguson Zone** | Zone 1: **UVI 0.7** (1.0–2.0 normal; **0.5–0.7 albino**) ([Baines et al. 2016](https://jzar.org/jzar/article/view/150), [ReptiFiles PDF](https://reptifiles.com/wp-content/uploads/2020/10/Leopard-Gecko-Care-Sheet-PDF.pdf)) | Zone 2–3: **UVI 2.0–4.0** ([Baines et al. 2016](https://jzar.org/jzar/article/view/150)) | Zone 3: **UVI 3.0–5.0** (essential) ([RSPCA](https://rspca.org.uk/adviceandwelfare/pets/other/beardeddragon), [ReptiFiles 2026 PDF](https://reptifiles.com/wp-content/uploads/2026/01/Bearded-Dragon-Care-Sheet-ReptiFiles.pdf)) | Zone 1: **UVI 0.7–2.0** (beneficial) ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/crestedgecko), [ReptiFiles PDF](https://reptifiles.com/wp-content/uploads/2020/10/Crested-Gecko-Care-Sheet-PDF.pdf)) | Zone 3: **UVI ~3.0** at top perch (essential) ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet)) |
| **Min Adult Enclosure (`L x D x H` cm)** | **60 x 30 x 40 cm** min (**90 x 45 x 45 cm** rec.) ([Creatures.com](https://creatures.com/learn/care/leopard-gecko-care-guide)) | **120 x 60 x 60 cm** (floor area critical) ([ReptiFiles PDF](https://reptifiles.com/wp-content/uploads/2020/08/Northern-Blue-Tongue-Skink-Care-Sheet-PDF.pdf)) | **120 x 60 x 60 cm** ([RSPCA](https://rspca.org.uk/adviceandwelfare/pets/other/beardeddragon)) | **45 x 45 x 60 cm** (vertical height critical) ([RSPCA](https://www.rspca.org.uk/adviceandwelfare/pets/other/crestedgecko)) | **60 x 60 x 120 cm** tall mesh/ventilated ([ReptiFiles](https://reptifiles.com/veiled-chameleon-care-sheet)) |
| **Body Condition Landmarks (for Vision AI)** | Tail width vs. neck: ideal tail as wide as neck; pencil-thin = emaciated; wider than head = obese ([LafeberVet](https://lafeber.com/vet/basic-information-for-leopard-gecko/)) | Heavy cylindrical body with short legs carried low (**do not misclassify normal low belly as belly-dragging**); check fat rolls at limbs ([LafeberVet](https://lafeber.com/vet/basic-information-for-the-northern-blue-tongued-skink/)) | Check fat pads on head, hip bones, and tail base; 300–550 g adult ([Chewy](https://www.chewy.com/education/reptile-and-amphibian/bearded-dragon/how-big-can-a-bearded-dragon-get), [WSU Vet](https://hospital.vetmed.wsu.edu/2026/01/02/metabolic-bone-disease-in-bearded-dragons/)) | 35–55 g adult; tailless adult is normal (dropped tail never regrows) ([PangoVet](https://www.google.com/search?q=https://info.pangovet.com/pet-health-wellness/geckos/crested-geckos-size-weight-growth-chart), [Creatures.com](https://creatures.com/species/crested-gecko/crested-gecko-lifespan)) | Check casque fat, ribs, and sunken eyes; gravid females show dark color with bright spots ([Chameleon Academy](https://chameleonacademy.com/s7-e2-caring-for-egg-laying-female-chameleons/)) |
| **Normal vs. Alarming False-Alarm Prevention** | **Normal:** Hidden all day, pale pre-shed, regrown smooth tail. **Serious:** Motionless in open by day, pencil tail, circling/Enigma syndrome ([MorphMarket](https://www.google.com/search?q=https://morphmarket.com/morphpedia/leopard-geckos/enigma)). | **Normal:** Buried for hours, low belly carriage, blue-tongue hiss bluff, live-bearer (no lay box). **Serious:** Open-mouth breathing at rest, dark/missing toe tips ([Bio Dude PDF](https://cdn.shopify.com/s/files/1/1654/9443/files/6-2022_-_Bioactive_Northern_Blue_Tongue_Skink_Care_Sheet.pdf)). | **Normal:** Open-mouth gaping **while under basking lamp**, morning darkening, winter brumation. **Serious:** Gaping **away from heat**, persistent black beard, hidden all day outside brumation ([PetMD](https://www.petmd.com/reptile/bearded-dragon-care-101)). | **Normal:** Motionless on glass/leaves all day, tailless adult. **Serious:** On floor during day, open mouth above 27–29 °C ([Pangea Reptile](https://www.pangeareptile.com/blogs/blog/basic-care-for-crested-geckos)). | **Normal:** Rocking gait, high perch basking, female digging tunnel to lay within hours. **Serious:** Eyes closed in daytime, sitting on floor, digging for 2–3+ days without laying ([PetMD](https://www.petmd.com/reptile/veiled-chameleon-care-sheet), [ReptileDirect](https://reptiledirect.com/how-to-tell-if-a-lizard-is-pregnant/)). |

## 6. Filtered Alert Rules & Guardrails for RepTracker

| Alert Category | Severity | Trigger Condition in RepTracker | Data Source Used |
| :--- | :--- | :--- | :--- |
| **Critical Overheating** | `emergency` | `hot.temperature` or `cold.temperature` exceeds species critical max (e.g., `> 30 °C` / `86 °F` cool side for leopard gecko; `> 32 °C` / `90 °F` cool side for skink) for `>= 30` minutes. | Simulated sensor series (`*-temp-c.json` / `*-temp-f.json`) + `research/<species>.json` |
| **Critical Under-Heating / Heat Failure** | `emergency` | Both `hot.temperature` and `cold.temperature` drop below species critical minimum (`16 °C` / `60 °F` for leopard gecko; `18 °C` / `64 °F` for skink) outside brumation. | Simulated sensor series + `research/<species>.json` |
| **Collapsed Thermal Gradient** | `warning` | Mean `hot.temperature - cold.temperature < 4.0 °C` (`7.2 °F`) during lights-on so the lizard cannot thermoregulate. | Derived subtraction in [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py) |
| **Humidity Out of Range / Stuck Wet** | `warning` | `hot.humidity` or `cold.humidity` outside species `%RH` range (`30–40 %RH` for leopard gecko; `40–60 %RH` for northern blue-tongued skink), or continuously `> 80 %RH`. | Simulated sensor series (`*-humidity-rh.json`) + `research/<species>.json` |
| **Collapsed / Abnormal Posture in Open** | `emergency` | Vision AI sees lizard in the exact same exposed coordinate (`Movement Data` delta `= 0`) across an entire active window on its side/back or with splayed limbs. | PDF image chunks + `Movement Data` in [`response-schema.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/response-schema.json) |
| **Gaping Away from Basking Zone** | `emergency` | Vision AI detects open-mouth breathing without a threat display or while outside the basking zone (`cool_third` / `middle_third`). | Vision AI + `Movement Data` zone + `sensors.hotSide` |
| **Zone Occupancy Shift** | `warning` | Diurnal basking species (`skink`) spends `> 80%` of lights-on visible frames in `cool_third`, or any lizard stays pressed in `hot_third` 100% of the window. | Derived zone time budget from `Movement Data` |
| **Data Blindness / Visibility Coverage** | `warning` | Sensor series has no reading for 15+ minutes, or `visible_frames_pct == 0%` (reported transparently via the dashed unseen-frame graph from commit [`354b76a`](https://github.com/jkozik72/RepTracker/commit/354b76a28f51644ff16e84044d66a0cefeea26a3)). | Derived coverage check in [`src/website/main.py`](https://github.com/jkozik72/RepTracker/blob/main/src/website/main.py) |

## 7. Ready-to-Paste JSON Payloads for `src/website/research/`

Because [`src/website/research/leopardgecko.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/leopardgecko.json) and [`src/website/research/skink.json`](https://github.com/jkozik72/RepTracker/blob/main/src/website/research/skink.json) are both 0 bytes right now and [`src/website/prompts/context-chunk.txt`](https://github.com/jkozik72/RepTracker/blob/main/src/website/prompts/context-chunk.txt) injects `{{research}}` directly into the AI context, pasting the two JSON objects below into those files will immediately activate species-aware AI evaluation with zero Python changes:

### 7.1 `src/website/research/leopardgecko.json`

```json
{
  "species_id": "leopard-gecko",
  "common_name": "Leopard gecko",
  "scientific_name": "Eublepharis macularius",
  "native_climate": "arid to semi-arid rocky scrub and dry grassland",
  "lifestyle": "terrestrial",
  "activity_pattern": "crepuscular and nocturnal (normally hidden and asleep inside a hide throughout the daytime lights-on period)",
  "temperatures": {
    "basking_surface_day": {"c": [34, 36], "f": [94, 97], "note": "Surface temperature under lamp; 8-15 C hotter than air sensors"},
    "hot_side_air_day": {"c": [28, 30], "f": [82, 86], "potz_c": [25, 30], "potz_f": [77, 86]},
    "cool_side_air_day": {"c": [21, 26], "f": [70, 79]},
    "night_air": {"c": [18, 24], "f": [64, 75], "critical_min_c": 16, "critical_min_f": 60},
    "emergency_overheating_air": {"cool_side_max_c": 30, "cool_side_max_f": 86, "hot_side_max_c": 34, "hot_side_max_f": 93},
    "min_thermal_gradient": {"c": 4, "f": 7.2}
  },
  "humidity_rh_pct": {
    "ambient_day": [30, 40],
    "humid_hide_required": true,
    "humid_hide_target_rh_pct": [70, 80]
  },
  "lighting_and_uvb": {
    "ferguson_zone": 1,
    "target_uvi_basking": [0.7, 2.0],
    "albino_uvi_basking": [0.5, 0.7],
    "photoperiod_hours": 12,
    "camera_note": "A camera cannot measure UVB output; never infer adequate UVB from a bright lamp."
  },
  "enclosure_and_substrate": {
    "min_enclosure_cm": {"length": 60, "depth": 30, "height": 40},
    "recommended_enclosure_cm": {"length": 90, "depth": 45, "height": 45},
    "recommended_substrates": ["paper towel", "slate or ceramic tile", "soil-sand mix (packed)"],
    "avoid_substrates": ["calcium sand", "loose fine sand", "crushed walnut shell", "wood shavings"]
  },
  "diet_and_feeding": {
    "type": "strict insectivore (no plant matter)",
    "feeding_interval": "juveniles daily; adults every 2 days",
    "water_bowl": "shallow clean water dish required; food bowl only holds mealworms or calcium, as crickets/roaches are often hand-fed or free-roaming"
  },
  "body_condition_landmarks": "Tail is the primary fat store: an ideal healthy tail is plump and roughly as wide as the neck; a pencil-thin tail indicates emaciation; a tail wider than the head or armpit fat bubbles indicates obesity.",
  "shedding": "Sheds whole skin at once, usually at night, and eats the shed skin so no shed remnants are typically left in the enclosure. Skin turns pale/dull 1-2 days pre-shed. Retained shed most commonly constricts toes and tail tip.",
  "normal_behaviours_do_not_alarm": [
    "Hidden inside a hide and not visible ('can't see lizard') for most or all daytime frames",
    "Pale or dull skin 1-2 days before shedding and skipping a meal during shed",
    "Shorter, smoother regrown tail from a past tail drop",
    "Using one fixed corner of the enclosure for droppings"
  ],
  "serious_signs_for_vet_review": [
    "Lying motionless out in the open during the daytime for hours",
    "Pencil-thin tail or rapid tail thinning",
    "Swollen limbs, soft/rubbery jaw, or belly-dragging while walking",
    "Head tilt, circling, or stargazing (especially in Enigma morph lines)",
    "Skin tumours or white/iridescent masses (associated with Lemon Frost morph)",
    "Retained rings of old shed on toes, tail tip, or over the eyes"
  ],
  "non_diagnostic_rule": "Never name a medical diagnosis as fact or recommend home treatment; describe visible signs objectively and advise consulting an exotic veterinarian."
}
```

### 7.2 `src/website/research/skink.json`

```json
{
  "species_id": "northern-blue-tongued-skink",
  "common_name": "Northern blue-tongued skink",
  "scientific_name": "Tiliqua scincoides intermedia",
  "record_level_note": "Applies to Australian northern blue-tongued skink (Tiliqua scincoides intermedia). Indonesian blue-tongued skink species require higher humidity (60-80%+).",
  "native_climate": "tropical savanna woodland",
  "lifestyle": "terrestrial and burrowing",
  "activity_pattern": "diurnal (basks and patrols by day, but routinely buries itself in deep substrate or hides for hours)",
  "temperatures": {
    "basking_surface_day": {"c": [33, 38], "f": [92, 100], "surface_max_c": 42, "surface_max_f": 108},
    "hot_side_air_day": {"c": [28, 32], "f": [82, 90]},
    "cool_side_air_day": {"c": [21, 29], "f": [70, 85]},
    "night_air": {"c": [21, 24], "f": [70, 75], "critical_min_c": 18, "critical_min_f": 64},
    "emergency_overheating_air": {"cool_side_max_c": 32, "cool_side_max_f": 90},
    "min_thermal_gradient": {"c": 4, "f": 7.2}
  },
  "humidity_rh_pct": {
    "ambient_day": [40, 60],
    "humid_hide_required": false,
    "substrate_note": "Requires 10-15 cm of diggable substrate (soil, coconut fibre, or cypress mulch mix) that holds slight moisture."
  },
  "lighting_and_uvb": {
    "ferguson_zone": "2-3",
    "target_uvi_basking": [2.0, 4.0],
    "photoperiod_hours": 12,
    "camera_note": "A camera cannot measure UVB output; never infer adequate UVB from a bright lamp."
  },
  "enclosure_and_substrate": {
    "min_enclosure_cm": {"length": 120, "depth": 60, "height": 60},
    "recommended_substrates": ["soil-sand-bark mix (10-15 cm deep)", "cypress mulch", "coconut fibre mix"],
    "avoid_substrates": ["calcium sand", "cedar or pine shavings", "shallow carpet that prevents burrowing"]
  },
  "diet_and_feeding": {
    "type": "omnivore (approx. 50% leafy greens/vegetables, 40% animal protein/insects/snails, 10% fruit)",
    "feeding_interval": "juveniles daily to every other day; adults 1-3 times per week (highly prone to obesity)",
    "reproduction_note": "Live-bearer (viviparous): gives birth to live young and never needs an egg-laying box."
  },
  "body_condition_landmarks": "Heavy, cylindrical body with naturally short legs. Ideal condition shows smooth body contours; obesity is very common and shows as bulging fat rolls near the forelimbs and hindlimbs; emaciation shows protruding hip bones and spine.",
  "shedding": "Sheds in large patches over several days every 1-3 months as an adult. Retained shed on the short toes and tail tip is a common husbandry hazard.",
  "normal_behaviours_do_not_alarm": [
    "Carrying the heavy belly low to the ground on short legs (do not misclassify normal skink anatomy as pathological belly-dragging)",
    "Spending hours buried under substrate or inside a hide ('can't see lizard')",
    "Flattening the body, hissing, and displaying the bright blue tongue when startled (normal defensive bluff)",
    "Seasonal winter slowdown or brumation with reduced appetite while maintaining body condition"
  ],
  "serious_signs_for_vet_review": [
    "Open-mouth breathing at rest, wheezing, or mucus/bubbles around nostrils or mouth",
    "Darkened, constricted, or missing toe tips after a shed",
    "Lying continuously under the heat lamp for days without thermoregulating",
    "Severe obesity with pronounced limb fat rolls or emaciation with visible pelvic bones",
    "Crusty, discoloured, or lifted scales indicating potential skin infection or burns"
  ],
  "non_diagnostic_rule": "Never name a medical diagnosis as fact or recommend home treatment; describe visible signs objectively and advise consulting an exotic veterinarian."
}
```
## 8. Fitting This Advice to the `src/species-profiles` Branch

Sections 1 to 7 were written against `main` at commit `354b76a`. The branch `src/species-profiles` (4 commits ahead of `main` at `ae49c92`, not merged yet) changes two things this advice depends on. It opens RepTracker to any reptile or amphibian (decision D6 on that branch), and it adds two camera answers to every analysis: `"Eating seen"` and `"Droppings seen"`. This section says how the advice applies once that branch is merged.

### 8.1 Eating and Droppings: What the Camera Can and Cannot Say

Looking at the bowl works, and this advice keeps it. A bowl is a lasting state: food that is in the dish at 10:00 is still there in the 10:01 image, so one image a minute is enough for `"Food in bowl"`. What one image a minute cannot do is prove that something brief did *not* happen. A feeding strike or a few licks last seconds, so the animal can eat between two images and never be caught. The bowl also only covers part of the diet: a leopard gecko's crickets and roaches are hand-fed or loose in the enclosure, so an empty or missing bowl says nothing about whether it ate. Droppings are similar. A new dropping is a lasting state and can sometimes be seen, but on bark or soil, at whole-enclosure resolution, it is easy to miss, it may be inside a hide or buried, and the camera cannot judge what a keeper needs to know about it (urate colour, consistency).

So the two new answers are reliable in one direction only:

| Answer on the species branch | Trust it? | How to read it |
| :--- | :--- | :--- |
| `"Food in bowl"`: `"true"` / `"false"` | Yes | A lasting state the camera sees well. Compare it across analyses: food that was there and is gone was eaten or removed. Meaningful for bowl-fed diets (a skink's salad or pellets), not for insects fed by hand. |
| `"Eating seen"`: `"eating"` | Yes | The animal was caught at the food in at least one image. |
| `"Eating seen"`: `"not eating"` | **No, as written** | It only means "not caught eating in these images". Reword the option to `"not seen eating"`, never raise an alert from it, and never count it toward "days since last meal". |
| `"Droppings seen"`: `"new droppings"` | Mostly | Presence only. Say nothing about appearance. |
| `"Droppings seen"`: `"none seen"` | **No** | Not evidence that there were none. Never alert on it. |

The keeper-entered fields in Section 2 (`lastFedAt`, `lastFaecesAt`) stay the record of truth for "days since last meal" and "days since last droppings". A camera `"eating"` or `"new droppings"` answer can be offered to the keeper as a suggestion to confirm, not written into that record by itself.

### 8.2 Hot-Side and Cool-Side Air Sensor Checks Apply to Lizards Only

**The rule:** the two air stations (`hot` and `cold`, each with temperature and humidity) are checked against a species' ranges only when that species' profile says `animalType: "lizard"`. For every other animal type the readings are still shown, but nothing turns red, no alert is raised from them, and the AI is told not to judge the animal by them.

**Why lizards only.** The two-station layout measures one thing: a warm-to-cool air gradient across the enclosure floor. That is how a ground-dwelling lizard controls its body temperature, and every threshold, zone rule and false-alarm rule in Sections 3 to 7 was written for lizards. For other groups the same numbers mislead:

| Animal type in the profile (`animalType`) | Why hot-side / cool-side air readings mislead | What RepTracker should do |
| :--- | :--- | :--- |
| `lizard` | They are the right measurement for ground-dwelling lizards. | Check both stations against the profile, as the branch does now. |
| `lizard` with `habitat: "arboreal"` (crested gecko, chameleon) | The gradient runs top to bottom, not left to right (Section 5: readings at perch height). | Check only if the two stations are placed high and low; otherwise show the readings without alerts. |
| `turtle`, `crocodilian`, or any profile with `habitat: "aquatic"` / `"semi-aquatic"` | Water temperature and water quality decide their health. RepTracker has no water sensor. | Show air readings, labelled "air only; water is not measured". No alerts. |
| `frog`, `toad`, `salamander` | Many need cool, damp conditions and have no basking gradient. A "hot side" range has no meaning for them, and a warm reading that is fine for a lizard can be dangerous. | No range check. Do not apply any lizard threshold. |
| `snake`, `tortoise` | A warm-to-cool gradient does apply to them, but nothing in this document was written or checked for them. | No alerts until their ranges and false-alarm rules are reviewed the way Section 5 does for lizards. |
| `other`, or no profile | Unknown. | No check. |

**So one species never affects another.** Three rules keep the lizard checks from leaking:

1. **Each animal is checked against its own profile only.** There is no shared or default range. An animal with no profile gets no sensor check (the branch already does this).
2. **Never fall back from one species to another.** A species that is not in Section 5 does not borrow the leopard gecko's or the skink's numbers, even if it is also a lizard.
3. **The lizard-only derived values stay lizard-only.** The thermal gradient (`hot - cold`), the hot / middle / cool third time budget, and the overheating, under-heating and collapsed-gradient alerts in Section 6 are computed and shown for `animalType: "lizard"` only.

**Where this goes in the code on the species branch** (as of `ae49c92`):

| Place | Today | Change |
| :--- | :--- | :--- |
| `ProfileBrief` in `src/website/main.py` | Gives the page `temperaturesF` and `humidityPercent`, but not the animal type. | Also pass `animalType` and `habitat`. |
| `checkSensorRanges` and `rangeFor` in `src/website/templates/index.html` | Compare both stations with the profile for every animal. | Run only when `animalType` is `"lizard"`. For other types clear the red marking and show one line: "Air sensors are not checked for this animal." |
| `src/website/prompts/context-chunk.txt` (sensor readings block) | Sends the hot / cold summary for every animal. | For non-lizards add: "These are air readings from two stations set up for a lizard's warm-to-cool gradient. Do not judge this animal's temperature or humidity from them." |
| `"Hazardous conditions"` in `src/website/prompts/response-schema.json` | `"Temperature too high"`, `"Temperature too low"` and `"Humidity too high"` can be raised for any animal. | For non-lizards these three stay `false`; anything the AI sees in the images goes under `"Other"`. |
| `src/website/prompts/profile-schema.json` | Requires `temperaturesF.hotSide` and `coldSide` for every species. | No change. The values stay in the profile for the keeper to read on the Research page; they are only *checked* for lizards. |

This replaces the last row of Section 4.3 ("keep active support focused on lizards"): with D6 the camera analysis and species profiles cover any reptile or amphibian, and only the air-sensor checks stay limited to lizards.
