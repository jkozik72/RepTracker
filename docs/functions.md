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
| animal | The tracked reptile or amphibian (D6). One section of the dashboard each. Code names still say `lizard` (`lizards`, `/lizards`). | lizard (in the UI), pet |
| species check | A species-specific thing to check in every analysis, with its answers and concern answers, from the species profile (`trackedStats`). | tracked stat |
| species | A lizard's species: a field of the add-lizard form and the input to research. | |
| web app | The local website as a whole: UI, web interface, backend. | website, app |
| dashboard | The page with the status and alerts bar and one section per lizard. | |
| raw video | A recorded video file, before motion tracking. | |
| processed video | The video that motion tracking outputs. | |
| motion tracking | Video in, position of the lizard out. | |
| position | Where the animal is in a frame. Units: TBD (Q13). | |
| speed | How fast the position changes. Units: TBD (Q13). | |
| animal visible | Whether the animal is in the frame ("Animal visible": yes, partly, no). | lizard present, in frame, on screen |
| statistics | Values computed per lizard: position, speed, lizard present, and others (Q13). | |
| movement graph | The dashboard graph of how much a lizard moved throughout the day. | |
| research | The LLM's information gathering for one species. | |
| structured information | What research outputs, per species. | knowledge base, research files |
| poll | One request to the AI model to analyze a frame. Poll rate: how often that happens. | |
| report | The structured result of one poll. It gives the status. | |
| status | An animal's condition, from a finite set (examples: shedding, overweight). The set: Q12. | |
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
| `LizardConfigFromForm` | Validates the add/edit-lizard form into a config (name, species, width, camera, sensors) | mode, form dict, createdAt → config |
| `UpdateLizard` | Edits a lizard: new config from the form; keeps its id, `createdAt` and analyses; renames it in `reptiles.json` | mode, id, form dict → `{id, config, latest}` |
| `DeleteVideo` | Deletes an uploaded camera video for good; refuses the committed samples and a video a lizard still uses | mode, name → same as `ListMedia` |
| `ProfileBrief` | A lizard's species profile as the dashboard needs it: name and the ranges for sensor alerts | species text → dict or None |
| `CreateProfile` | Researches a species with the provider in use (`RESEARCHERS`), checks the reply, fetches photos, saves it; refuses a duplicate unless regenerating | species, regenerate → record with `usedBy` |
| `UpdateProfile` / `DeleteProfile` / `GetProfile` / `ListProfiles` | A keeper's edit (marks it checked); delete with its photos; one profile; all profiles, each with the animals that use it | |
| `AddFeeding` / `DeleteFeeding` | The feeding log (`reptiles/<id>/feedings.json`, time order): when, food, amount, notes | |
| `FeedingContext` | The feeding log as the AI sees it, relative to the end of the analysed range | mode, id, end → text |
| `KeeperPhoto` | A photo the keeper took or attached (a data: URL) as a JPEG of at most 1568 px, turned upright; refuses anything that isn't an image. `AskQuestion` sends it instead of the camera picture | data URL → bytes |
| `Notifications` | Neutral events, newest first: AI notable moments, eating, droppings, changes between analyses, feedings | analyses, feedings → list |
| `MovementData` | Every analysed position of an animal with the seconds each image stands for | mode, id → `{points: [{t, p, w}], positionMax, unit, hotSide}` |
| `GenerateSensors` | Dev mode: four sensor files for a mode from a profile's ranges and a pattern | mode, slug, pattern → names |
| `RemoveLizard` | Takes a lizard off `reptiles.json`; its folder stays | mode, id → none |
| `ListLizards` | Every listed lizard with its config and latest analysis | mode → list |
| `ListMedia` | Video and sensor file names without extension; sensors include the defaults | mode → `{videos, sensors, defaultSensors}` |
| `SaveUpload` | Saves an uploaded .mp4 (up to 3 GB) or sensor .json (up to 50 MB) into the mode's media. The request body is the file itself (name in `X-File-Name`), streamed straight to a `.part` file and renamed when complete; rejects duplicates, default names, cut-off uploads, unreadable videos, bad JSON | mode, kind, file name, body stream, length → `{kind, name}` |
| `DefaultSensorNames` | Names of the shared default sensor files in `data/defaults/sensors/` | → list |
| `SensorPath` | Where a sensor file lives: the mode's uploads first, then the defaults | mode, name → path |
| `CheckSeries` | Raises unless the sensor JSON is `{"t": ms > 0, "value": [numbers]}` | dict → none |
| `SourceOffsetSeconds` | Seconds since the lizard's camera and sensors started; `None` before `createdAt` | config, datetime → s |
| `ReadSensor` | Sensor value at an offset: sample `floor(s / (t/1000))`, looping | mode, series name, s → value in the series' unit |
| `SummarizeSensors` | Min / mean / max / latest of each channel over a range, sampled each minute | mode, config, start, end → text |
| `TakeAPicture` | One frame from the camera video | mode, video name, s into the video → PIL image |
| `ParsePDF` | Images into one PDF, one page each, labelled with its timestamp | images, labels, path → PDF file |
| `PositionScale` | Prompt values for the position unit: cm from the left wall, or % of the image width when no enclosure width is set | config → `{enclosure_width, position_unit, position_max}` |
| `FillTemplate` | Fills `{{key}}` in a file from `prompts/` | file name, values → text |
| `GeneratePrompts` | Builds the lizard's prompt chunk for a range: context + one IMAGES chunk per 60 images; writes a bundle with `manifest.json`. Images: `imageCount` spread evenly, at least 1 min apart (None: 1 per minute). Never sends a video moment twice: a range longer than the video is cut to its last part that fits in one pass | mode, id, start, end (ISO), imageCount or None → manifest (with `imageSpacingS`) |
| `SendPrompt` | Sends a bundle to the provider in use and appends the answer to `analyses.json`. Saves nothing if the provider fails | mode, id, bundle id → analysis entry: `{bundleId, provider, range, sentAt, result}`, plus `model`, `seconds`, `tokens`, `notes` when the provider gives them |
| `MockProvider` | Offline stand-in for the AI (Q11): position from the darkest pixels of each frame, every other field "can't see" | bundle → schema-shaped result |
| `ClaudeProvider` | The project's provider (D4): hands the bundle to `claude_ai.AnalyzeBundle` | bundle → schema-shaped result with `_details` |
| `GeminiProvider` | The Gemini provider, still selectable: hands the bundle to `ai.AnalyzeBundle` | bundle → schema-shaped result with `_details` |
| `AskQuestion` | Answers a keeper's question from `prompts/ask.txt` with the provider in use, always with the current camera picture (none before the camera starts) | mode, id, question, now, vision (default on) → `{answer, prompt, provider}`, plus `image` (a `data:` URL) with vision |
| `CurrentPicture` | The camera picture at a moment, as JPEG bytes (at most 1280 px wide), for a question with vision | mode, config, datetime → bytes |
| `CurrentProvider` | The provider chosen for this computer, from `data/ai-settings.json` (git-ignored); `mock` if none | none → `mock`, `claude` or `gemini` |
| `AiStatus` | What Settings shows: the provider in use, and for each provider whether it is ready and why | none → `{provider, providers: [{name, label, ready, detail}]}`; Claude's entry adds `apiKey: {saved, mask}`, never the key |
| `SetProvider` | Chooses the provider for this computer; refuses one that is not ready | name → same as `AiStatus` |
| `TestProvider` | One tiny request to the provider in use (`PINGS`), to prove the connection | none → `{provider, ok, message}` |
| `SaveClaudeKey` | Saves the Anthropic API key on this computer through `claude_ai.SaveKey` | key → same as `AiStatus` |
| `SetClaudeModel` | Chooses the Claude model through `claude_ai.SetModel` | model id → same as `AiStatus` |
| `RemoveClaudeKey` | Deletes the saved key; switches back to the Mock if Claude was in use and is no longer ready | none → same as `AiStatus` |

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
| `Answer` | Sends a keeper's question, with the camera picture first when vision is on | prompt text, JPEG bytes or None → answer text |
| `Ping` | One tiny request that proves login, project, location and model | none → a sentence with the time taken in s |
| `ReadReply` | The reply's text; `AiError` if it was blocked, cut off or empty | response → text |
| `ParseJson` | The reply as JSON; accepts a Markdown code fence around it | text → object |
| `_Nested` | Cleans an object or list in the answer (species checks, conditions seen): enums matched, else their last option; at most 20 list entries | value, spec → value |
| `NormalizeResult` | Forces a reply into `prompts/response-schema.json`: off-list or missing values become the field's last enum option, `False` or `"none"`; repairs are listed in `notes`. Refuses a reply with none of the schema's fields | reply, schema, image labels, enclosure width in cm → result |
| `NormalizeMovement` | One position per image sent: matched by timestamp, or by order when there is one entry per image | reply's Movement Data, image labels, maximum position (enclosure width in cm, or 100 for % of the image) → `[{time, position}]`; also reads the older `position_cm` key |
| `FrameLabels` | Timestamp labels of a bundle's images, in the order sent | manifest → list |
| `Explain` | Turns an error from the Google libraries into an `AiError` a keeper can act on | exception, time limit in s → `AiError` |

### `src/website/research.py`

Species profiles (D5): storage, schema checks, photos and prompt text. No AI calls (main.py makes them). Source: `docs/notes/2026-11-15-species-profiles-chat.md`.

| Function | Does | In → out |
|---|---|---|
| `Slug` | A safe folder name from a species name | text → slug |
| `FindRecord` | The profile for a species as typed: matches the typed name, common name or scientific name | species text → record or None |
| `ListRecords` / `ReadRecord` / `WriteRecord` | All profiles; one profile; save one (`research/<slug>/profile.json`) | → records / slug → record / record → none |
| `NewRecord` | A record around a profile: species as typed, slug, time, provider, model | species, profile, provider, model → record |
| `NormalizeProfile` | Forces an AI reply or a keeper's edit into `prompts/profile-schema.json`: off-list enums become "other" (or the last option), non-numbers 0, backwards ranges swapped; refuses a profile with no common name | dict → (profile, notes) |
| `FetchImages` | Up to 6 reference photos from Wikimedia Commons (search by scientific name), saved with author, licence and source; never raises | record → (images, note) |
| `CleanTrackedStats` | Species checks the dashboard can use: unique snake_case ids, 2+ options, concern options that are real options, "can't see animal" last; at most 6 | stats, notes → stats |
| `BuildResponseSchema` | The answer format for one animal: the base `response-schema.json` with the species' activities, checks and named conditions; base as is without a profile | base schema, record → schema |
| `SensorSeries` / `SensorSet` | A sensor series for a range and a pattern (in-bounds, under, over, variance); the four series for a profile | |
| `SexConditions` | Sex-specific conditions for an animal: its sex's, or both when unknown | profile, sex → list |
| `PromptText` | The profile as plain text for the CONTEXT chunk | record → text |
| `Summary` | What the Research list shows for a profile | record → dict |

### `src/website/auth.py`

Sign-in (D7). Files: `data/auth.json` (account, password hash), `data/secret_key` (cookie signing), `data/tls/` (LAN certificate); all git-ignored.

| Function | Does | In → out |
|---|---|---|
| `AccountExists` / `AccountId` | Whether the one account exists; its random id (sessions are tied to it) | → bool / id or None |
| `CreateAccount` | The first visit's account: username 3 to 40, password 10+ and confirmed, stored as a scrypt hash; refused once one exists | username, password, confirm → (username, id) |
| `CheckLogin` | Checks a sign-in; repeated wrong passwords lock that address out (30 s doubling to 15 min) | username, password, address → (username, id) |
| `SecretKey` | The cookie signing key, made once | → text |
| `Certificate` / `LanAddresses` | A self-signed certificate for this computer's names and LAN addresses; made once, and again when the computer is renamed. The addresses | → (cert, key paths) / list |
| `HostNames` | The computer's name and its `.local` name | → list |

### `src/website/system.py`

This installation (D8). Update, restart and uninstall only where `src/pi/install.sh` set it up (`REPTRACKER_MANAGED=1` and `/usr/local/sbin/reptracker-admin` exist).

| Function | Does | In → out |
|---|---|---|
| `Managed` | Whether the Pi installer set this up | → bool |
| `Info` | Branch, commit, the last task's log | → dict |
| `Branches` | The branches on GitHub, main first | → list |
| `Run` | Starts `reptracker-admin` through `sudo -n` (it runs detached) | action, branch, deleteData → dict |

`app.PhoneLinks` lists the addresses a phone on the network can open (IP addresses first, then `name.local`; none without `--lan`); `/api/phone/qr.svg` draws one of them as a QR code (segno).

`app.ServeLan` serves `--lan`: cheroot over HTTPS, plus a plain-HTTP port that only redirects (`--http-redirect`).

### `src/pi/`

| File | Does |
|---|---|
| `install.sh` | Installs or updates RepTracker on a Pi: packages, `reptracker` user, repo, venv, `/etc/reptracker.env`, hostname, sudo rule, service |
| `reptracker-admin` | `update [branch]`, `restart`, `uninstall [--delete-data]`, `status`, `log`; long tasks run as a `systemd-run` unit and log to `/opt/reptracker/task.log` |
| `reptracker.service` | The systemd unit: runs `app.py --lan` as `reptracker`, restarts on exit |

### `src/website/claude_ai.py`

The Claude provider (D4): the Claude API through the `anthropic` package, imported only when Claude is used. Source: `docs/notes/2026-11-15-claude-provider-chat.md`. Reuses `ParseJson`, `NormalizeResult` and `FrameLabels` from `ai.py`. One analysis is one request (`max_retries=0`); refusals go to Anthropic's server-side fallback (`fallbacks: "default"`). Every failure leaves this file as `AiError` with one sentence for the dashboard.

| Function | Does | In → out |
|---|---|---|
| `ApiKey` | The key to use: the one saved in Settings, else `ANTHROPIC_API_KEY` | none → (key, where it came from) |
| `SaveKey` | Checks the key looks like an Anthropic key (`sk-ant-…`) and writes `data/claude-key.json` (git-ignored) | key → none |
| `RemoveKey` | Deletes the saved key | none → none |
| `Settings` | The model: the one chosen in Settings (`MODELS`), else `REPTRACKER_CLAUDE_MODEL`, else `claude-opus-5-5` | none → `{model}` |
| `SetModel` | Saves the model choice in `data/claude-settings.json` (git-ignored); only ids from `MODELS` | model id → none |
| `MaskKey` | First 7 and last 4 characters, for showing on screen | key → text |
| `Status` | Whether Claude is set up (package, key), without calling it | none → `{ready, detail, keySaved, keyMask}` |
| `GetClient` | The `anthropic` client for the current key, made on first use | none → client |
| `StructuredSchema` | `response-schema.json` in the form structured outputs accept: drops `$schema` and `title`, writes a list of types as `anyOf` | schema → schema |
| `BuildAnalysisRequest` | A bundle as one request: `system.txt` as the system prompt; one user turn with each chunk's PDF then text; reply constrained to the schema. Refuses over 30 MB or 600 PDF pages | folder, manifest, schema → keyword arguments for `beta.messages.create` |
| `AnalyzeBundle` | Sends one bundle in one call and returns the normalized result | folder, manifest, config, schema → schema-shaped result plus `_details`: `{model, seconds, tokens, notes}` |
| `Answer` | Sends a keeper's question (effort `low`), with the camera picture first when vision is on | prompt text, JPEG bytes or None → answer text |
| `Research` | Writes a species profile: `research.txt` in, a dict shaped like `profile-schema.json` out (structured outputs) | prompt, schema → (profile, details) |
| `Ping` | One tiny request that proves the key and model | none → a sentence with the time taken in s |
| `ReadReply` | The reply's text; `AiError` if refused, cut off or empty | response → text |
| `Explain` | Turns an `anthropic` error into an `AiError` a keeper can act on | exception, time limit in s → `AiError` |

### `src/website/templates/index.html`

| Function | Does |
|---|---|
| `mode` | The data set on screen: Toy or Main in dev mode, always Main otherwise |
| `loadMode` | Loads the current mode's media and lizards and redraws everything |
| `renderVideoBox` | The camera video with its time and source labels; in the expanded card, a full-screen button (the browser's Fullscreen API) |
| `openEdit` | Opens the add-lizard form filled in with a lizard's settings, to save changes to it |
| `aiStatsHtml` | The AI part of the stats panel: activity, body condition, eating, droppings, visible, food dish, then the species checks (concerns in red); older analyses show their own fields | animal → HTML |
| `checkInfo` | A species check's label, answers and concern answers, from the profile (or a plain label for an older analysis) | animal, id → check |
| `checkSensorRanges` | Live sensor readings against the lizard's species profile: temperatures per side, humidity as the average of both sides; out-of-range values turn red and become alerts | lizard, now → none |
| `loadProfiles` / `showProfile` / `renderProfile` | The Research tab: the profile list, and one profile with photos, husbandry facts, conditions, hazards, and Edit / Regenerate / Delete | |
| `suggestSpecies` / `renderSuggestions` | Spelling help for species: up to 3 "Did you mean" suggestions from profiles and `data/species-names.json` (names, scientific names, nicknames), or a ✓ when the name is known | typed text → `{exact, list}` |
| `nameScore` / `editDistance` | How far a typed name is from a known one: edit distance with swapped letters as one edit, word by word, prefixes, and a single word matching part of a name (a group such as "gecko") | |
| `findProfile` | The profile for a typed species, matched like the server (typed, common or scientific name); the add/edit form researches the species first when there is none | species text → profile summary or undefined |
| `speciesHint` | Under the species field: whether the typed species has a profile | |
| `section` | A collapsible card section; which are open is remembered per animal | |
| `renderMovement` / `barChart` / `zoneOf` | The Movement section: time on each side (all, day, night), movement per interval, by hour of day; bar charts; which third a position is in | |
| `feedingStatus` | Days since the last feeding (dashboard clock) and Fed / Due / Overdue from the profile | animal → status or null |
| `noteText` | A notification's text with species check labels from the profile | |
| `shrinkPhoto` / `clearAskPhoto` | Ask: the camera / attach button's photo, shrunk on the device to 1568 px JPEG before it is sent; removing it | |
| `loadPhone` / `showPhoneQr` | Settings, Open on your phone: the server's addresses and a QR code for the one picked | |
| `narrowScreen` | Phones (600px wide or less): charts are drawn 360 wide with fewer labels, so their text stays readable; crossing it redraws | |
| `loadSystem` / `renderSystem` / `startSystem` | Settings, This installation: branch and commit; update, restart, uninstall, following the task log through the restart | |
| `toggleExpand` | Opens a lizard from compact to full width, or closes it |
| `positionScale` | Client-side twin of `PositionScale`: the position chart's unit and maximum |
| `loadAi` | Loads the AI provider status on its own, so a slow check never delays the lizards: at start, when Settings opens, after a test or a refused switch |
| `renderApiKey` | The Anthropic API key form under Claude in Settings: save, show/hide, remove; shows only the masked key |
| `renderAi` | The AI provider choice in Settings (dev mode): one radio per provider with Ready / Not ready and why |
| `simNow` | The dashboard clock in ms: real time, or the dev-mode clock (speed, set moment, pause) |
| `syncVideo` | Keeps the camera video at the moment matching the clock; loops like a live feed |
| `readSeries` | Client-side twin of `ReadSensor` |
| `renderSensorCharts` | Temperature and humidity graphs, window growing to 5 days then sliding |
| `renderPositionChart` | Position (cm from the left wall, or %) from the latest analysis' Movement Data, times in local time. Images where the lizard was not visible: a dashed line joins the positions before and after, and a tick on the bottom marks each one |
| `renderMarkdown` | An AI answer's Markdown as HTML (headings, paragraphs, lists, code, bold, italic, http links); escapes everything first | text → HTML |
| `labelToLocal` | An image label ("2026-11-14 10:54 UTC") as a local time |
| `pollTick` | AI polling: at each interval mark of the dashboard clock, starts `runPoll` for each lizard that has no call in flight |
| `runPoll` | Generates and sends the prompts for the interval that just ended, updates the lizard, and reports in the status line under the summary |
| `setPolling` | Starts or stops AI polling (always stopped when the page loads); Start waits for the next interval mark |
| `renderPolling` | The AI polling controls in Settings: interval, images per interval, Start / Stop, and the next mark |
| `imageOptions` | The Images menu (1 per minute, or 5 to 60 spread evenly), shared by AI polling and the dev panel |
| `uploadWithProgress` | Uploads a file with a progress callback (XMLHttpRequest, since fetch can't report upload progress) |
| `showBundle` | The dev-mode prompt inspector: system prompt, schema, context chunk, each IMAGES chunk with its PDF and frames |
