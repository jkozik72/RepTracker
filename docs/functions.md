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

Names follow the existing PascalCase in this file. Source for the behaviour: `docs/notes/2026-11-14-dashboard-plan-chat.md`, `docs/notes/2026-11-14-dashboard-changes-chat.md`.

Every function that touches lizard data takes `mode` first: `toy` or `main`, each under `data/<mode>/` (`ModeRoot`).

| Function | Does | In → out |
|---|---|---|
| `CreateNewLizard` | Validates the add-lizard form, writes `reptiles/<id>/config.json`, adds it to `reptiles.json` | mode, form dict → `{id, config, latest}` |
| `RemoveLizard` | Takes a lizard off `reptiles.json`; its folder stays | mode, id → none |
| `ListLizards` | Every listed lizard with its config and latest analysis | mode → list |
| `ListMedia` | Video and sensor file names without extension; sensors include the defaults | mode → `{videos, sensors, defaultSensors}` |
| `SaveUpload` | Saves an uploaded .mp4 (streamed to disk, up to 3 GB) or sensor .json (up to 50 MB) into the mode's media; rejects duplicates, default names, unreadable videos, bad JSON | mode, kind, uploaded file → `{kind, name}` |
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
| `GeneratePrompts` | Builds the lizard's prompt chunk for a range: context + one IMAGES chunk per 60 images (1/min); writes a bundle with `manifest.json` | mode, id, start, end (ISO) → manifest |
| `SendPrompt` | Sends a bundle to `PROVIDER` (Mock until Q11), appends the answer to `analyses.json` | mode, id, bundle id → analysis entry |
| `MockProvider` | Offline stand-in for the AI (Q11): position from the darkest pixels of each frame, every other field "can't see" | bundle → schema-shaped result |
| `AskQuestion` | Answers a keeper's question from `prompts/ask.txt` | mode, id, question, now → `{answer, prompt}` |

### `src/website/templates/index.html`

| Function | Does |
|---|---|
| `mode` | The data set on screen: Toy or Main in dev mode, always Main otherwise |
| `loadMode` | Loads the current mode's media and lizards and redraws everything |
| `toggleExpand` | Opens a lizard from compact to full width, or closes it |
| `positionScale` | Client-side twin of `PositionScale`: the position chart's unit and maximum |
| `simNow` | The dashboard clock in ms: real time, or the dev-mode clock (speed, set moment, pause) |
| `syncVideo` | Keeps the camera video at the moment matching the clock; loops like a live feed |
| `readSeries` | Client-side twin of `ReadSensor` |
| `renderSensorCharts` | Temperature and humidity graphs, window growing to 5 days then sliding |
| `renderPositionChart` | Position (cm from the left wall) from the latest analysis' Movement Data |
| `uploadWithProgress` | Uploads a file with a progress callback (XMLHttpRequest, since fetch can't report upload progress) |
| `showBundle` | The dev-mode prompt inspector: system prompt, schema, context chunk, each IMAGES chunk with its PDF and frames |
