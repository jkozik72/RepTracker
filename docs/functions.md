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

| Term | Meaning | Don't use |
|---|---|---|
| TBD | | |

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
| `SendPrompt` | Sends a bundle to `PROVIDER` (Mock until Q11), appends the answer to `analyses.json` | mode, id, bundle id → analysis entry |
| `MockProvider` | Offline stand-in for the AI (Q11): position from the darkest pixels of each frame, every other field "can't see" | bundle → schema-shaped result |
| `AskQuestion` | Answers a keeper's question from `prompts/ask.txt` | mode, id, question, now → `{answer, prompt}` |

### `src/website/templates/index.html`

| Function | Does |
|---|---|
| `mode` | The data set on screen: Toy or Main in dev mode, always Main otherwise |
| `loadMode` | Loads the current mode's media and lizards and redraws everything |
| `setView` | Switches the dashboard between Full and Compact view |
| `simNow` | The dashboard clock in ms: real time, or the dev-mode clock (speed, set moment, pause) |
| `syncVideo` | Keeps the camera video at the moment matching the clock; loops like a live feed |
| `readSeries` | Client-side twin of `ReadSensor` |
| `renderSensorCharts` | Temperature and humidity graphs, window growing to 5 days then sliding |
| `renderPositionChart` | Position (cm from the left wall) from the latest analysis' Movement Data |
| `showBundle` | The dev-mode prompt inspector: system prompt, schema, context chunk, each IMAGES chunk with its PDF and frames |
