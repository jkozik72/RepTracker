# Functions

Naming conventions, the glossary, and the reference of named functions: what each does, where it lives. Update the entry in the same PR as the code. Conventions change only through a decision in `decisions.md`.

## Conventions

Proposed starting conventions; confirm or change them with a decision entry, then cite it in the last column.

| Rule | Convention | Decision |
|---|---|---|
| Case style | TBD: follows the language (Q2) | — |
| Functions | Verb first; the name says what it does (`detect…`, `smooth…`, `count…`) | proposed |
| Predicates | `is…`, `has…`, `should…` | proposed |
| One concept, one word | One term per concept, used everywhere; the glossary is the list | proposed |
| Abbreviations | Only those in the glossary | proposed |
| Units in names | When a value's unit could be confused, put it in the name (`…Ms`, `…Deg`, or the language's equivalent) | proposed |

### Glossary

One term per concept. Add a row before using a new domain word in code.

Terms and meanings come from the 2026-11-14 notes: the [brief](notes/2026-11-14-project-brief.md), the [board](notes/2026-11-14-whiteboard-system-design.md), and the [UI board](notes/2026-11-14-whiteboard-ui.md). Where those use several words for one concept, the word kept is the term and the others are under "Don't use": a proposal until the team confirms it.

| Term | Meaning | Don't use |
|---|---|---|
| lizard | The tracked animal. One section of the dashboard each. Whether other reptiles are in scope: Q18. | animal, pet |
| species | A lizard's species: a field of the add-lizard form and the input to research. | |
| web app | The local website as a whole: UI, web interface, backend. | website, app |
| dashboard | The page with the status and alerts bar and one section per lizard. | |
| raw video | A recorded video file, before motion tracking. | |
| processed video | The video that motion tracking outputs. | |
| motion tracking | Video in, position of the lizard out. | |
| position | Where the lizard is in a frame. Units: TBD (Q13). | |
| speed | How fast the position changes. Units: TBD (Q13). | |
| lizard present | Whether the lizard is in the frame. | in frame, on screen |
| statistics | Values computed per lizard: position, speed, lizard present, and others (Q13). | |
| movement graph | The dashboard graph of how much a lizard moved throughout the day. | |
| research | The LLM's information gathering for one species. | |
| structured information | What research outputs, per species. | knowledge base, research files |
| poll | One request to the AI model to analyze a frame. Poll rate: how often that happens. | |
| report | The structured result of one poll. It gives the status. | |
| status | A lizard's condition, from a finite set (examples: shedding, overweight). The set: Q12. | |
| alert | A notice to the user at the top of the dashboard. | |
| LLM, VLM | Large language model; vision-language model. | |
| DSP | Digital signal processing. The board's label for the motion-tracking stage. | |

## Reference

Grouped by module or file. Entry format:

```markdown
### `functionName`
- **Does:** one sentence
- **Lives in:** `src/<path>`
- **In / out:** inputs → output, with units where they matter
- **Notes:** why this name, if not obvious; link the approach page or decision
```

### `src/website/main.py`

Names follow the existing PascalCase in this file. Source for the behaviour: `docs/notes/2026-11-14-dashboard-plan-chat.md`, `docs/notes/2026-11-14-dashboard-changes-chat.md`; for the provider functions, `docs/notes/2026-11-15-gemini-provider-chat.md`.

Every function that touches lizard data takes `mode` first: `toy` or `main`, each under `data/<mode>/` (`ModeRoot`).

| Function | Does | In → out |
|---|---|---|
| `CreateNewLizard` | Validates the add-lizard form, writes `reptiles/<id>/config.json`, adds it to `reptiles.json` | mode, form dict → `{id, config, latest}` |
| `RemoveLizard` | Takes a lizard off `reptiles.json`; its folder stays | mode, id → none |
| `ListLizards` | Every listed lizard with its config and latest analysis | mode → list |
| `ListMedia` | Video and sensor file names without extension | mode → `{videos, sensors}` |
| `SaveUpload` | Saves an uploaded .mp4 or sensor .json into the mode's media; rejects duplicates, unreadable videos, bad JSON | mode, kind, file name, bytes → `{kind, name}` |
| `CheckSeries` | Raises unless the sensor JSON is `{"t": ms > 0, "value": [numbers]}` | dict → none |
| `SourceOffsetSeconds` | Seconds since the lizard's camera and sensors started; `None` before `createdAt` | config, datetime → s |
| `ReadSensor` | Sensor value at an offset: sample `floor(s / (t/1000))`, looping | mode, series name, s → value in the series' unit |
| `SummarizeSensors` | Min / mean / max / latest of each channel over a range, sampled each minute | mode, config, start, end → text |
| `TakeAPicture` | One frame from the camera video | mode, video name, s into the video → PIL image |
| `ParsePDF` | Images into one PDF, one page each, labelled with its timestamp | images, labels, path → PDF file |
| `FillTemplate` | Fills `{{key}}` in a file from `prompts/` | file name, values → text |
| `GeneratePrompts` | Builds the lizard's prompt chunk for a range: context + one IMAGES chunk per 60 images (1/min); writes a bundle with `manifest.json` | mode, id, start, end (ISO) → manifest |
| `SendPrompt` | Sends a bundle to the provider in use and appends the answer to `analyses.json`. Saves nothing if the provider fails | mode, id, bundle id → analysis entry: `{bundleId, provider, range, sentAt, result}`, plus `model`, `seconds`, `tokens`, `notes` when the provider gives them |
| `MockProvider` | Offline stand-in for the AI (Q11): position from the darkest pixels of each frame, every other field "can't see" | bundle → schema-shaped result |
| `GeminiProvider` | The real provider being tried (Q11): hands the bundle to `ai.AnalyzeBundle` | bundle → schema-shaped result with `_details` |
| `AskQuestion` | Answers a keeper's question from `prompts/ask.txt` with the provider in use | mode, id, question, now → `{answer, prompt, provider}` |
| `CurrentProvider` | The provider chosen for this computer, from `data/ai-settings.json` (git-ignored); `mock` if none | none → `mock` or `gemini` |
| `AiStatus` | What Settings shows: the provider in use, and for each provider whether it is ready and why | none → `{provider, providers: [{name, label, ready, detail}]}` |
| `SetProvider` | Chooses the provider for this computer; refuses one that is not ready | name → same as `AiStatus` |
| `TestProvider` | One tiny request to the provider in use, to prove the connection | none → `{provider, ok, message}` |

### `src/website/ai.py`

The Gemini provider being tried (Q11): Gemini through Vertex AI, signed in with the Google login of the computer that runs the app (Q20). Source: `docs/notes/2026-11-15-gemini-provider-chat.md`. It imports `google-genai` only when Gemini is used. One analysis is one HTTPS request: no retries, no follow-up requests. Every failure leaves this file as `AiError` with one sentence for the dashboard.

| Function | Does | In → out |
|---|---|---|
| `Status` | Whether Gemini is set up on this computer (package, Google login, project), without calling it | none → `{ready, detail}` |
| `Login` | Reads the computer's Google login once. Project: `GOOGLE_CLOUD_PROJECT`, else the login's quota project, else gcloud's default | none → credentials, project, where the project came from |
| `GetClient` | The `google-genai` client, made on first use | none → client |
| `Forget` | Drops the remembered login and client, so a new `gcloud` login is picked up | none → none |
| `Settings` | Model and location: `REPTRACKER_MODEL`, `GOOGLE_CLOUD_LOCATION`, else the defaults | none → `{model, location}` |
| `BuildAnalysisRequest` | A bundle as one request: `system.txt` as the system instruction; one user turn with `context.txt`, then each IMAGES chunk's text and PDF. Refuses a request over `MAX_REQUEST_MB` | folder, manifest → request (plain dict) |
| `AnalyzeBundle` | Sends one bundle in one call and returns the normalized result | folder, manifest, config, schema → schema-shaped result plus `_details`: `{model, seconds, tokens, notes}` |
| `Answer` | Sends a keeper's question | prompt text → answer text |
| `Ping` | One tiny request that proves login, project, location and model | none → a sentence with the time taken in s |
| `ReadReply` | The reply's text; `AiError` if it was blocked, cut off or empty | response → text |
| `ParseJson` | The reply as JSON; accepts a Markdown code fence around it | text → object |
| `NormalizeResult` | Forces a reply into `prompts/response-schema.json`: off-list or missing values become the field's last enum option, `False` or `"none"`; repairs are listed in `notes`. Refuses a reply with none of the schema's fields | reply, schema, image labels, enclosure width in cm → result |
| `NormalizeMovement` | One position per image sent: matched by timestamp, or by order when there is one entry per image | reply's Movement Data, image labels, width in cm → `[{time, position_cm}]` |
| `FrameLabels` | Timestamp labels of a bundle's images, in the order sent | manifest → list |
| `Explain` | Turns an error from the Google libraries into an `AiError` a keeper can act on | exception, time limit in s → `AiError` |

### `src/website/templates/index.html`

| Function | Does |
|---|---|
| `mode` | The data set on screen: Toy or Main in dev mode, always Main otherwise |
| `loadMode` | Loads the current mode's media and lizards and redraws everything |
| `loadAi` | Loads the AI provider status on its own, so a slow check never delays the lizards: at start, when Settings opens, after a test or a refused switch |
| `renderAi` | The AI provider choice in Settings (dev mode): one radio per provider with Ready / Not ready and why |
| `setView` | Switches the dashboard between Full and Compact view |
| `simNow` | The dashboard clock in ms: real time, or the dev-mode clock (speed, set moment, pause) |
| `syncVideo` | Keeps the camera video at the moment matching the clock; loops like a live feed |
| `readSeries` | Client-side twin of `ReadSensor` |
| `renderSensorCharts` | Temperature and humidity graphs, window growing to 5 days then sliding |
| `renderPositionChart` | Position (cm from the left wall) from the latest analysis' Movement Data |
| `showBundle` | The dev-mode prompt inspector: system prompt, schema, context chunk, each IMAGES chunk with its PDF and frames |
