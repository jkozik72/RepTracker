# Prompt formats

Every prompt RepTracker sends is built from the files here, so they can be read and edited by hand. `{{name}}` marks a value filled in by `main.py` (`FillTemplate`).

| File | Used for | Filled by |
|---|---|---|
| `system.txt` | System prompt for every analysis request | `GeneratePrompts` |
| `context-chunk.txt` | The CONTEXT chunk: lizard config, sensor summary for the range, species research, previous analysis | `GeneratePrompts` |
| `images-chunk.txt` | Text sent with each IMAGES chunk; the chunk's PDF holds up to 60 images, spread evenly over the range (at most 1 per minute); `{{image_spacing}}` says how far apart | `GeneratePrompts` |
| `response-schema.json` (base) | JSON Schema the AI's answer must match; also pasted into `system.txt`. It is not sent to the provider as a separate schema; `ai.NormalizeResult` forces the reply into it | `GeneratePrompts`, `SendPrompt` |
| `research.txt` | Asks for a species profile; `{{species}}` is the species as typed | `CreateProfile` |
| `profile-schema.json` | JSON Schema of a species profile; also pasted into `research.txt` | `CreateProfile`, `research.NormalizeProfile` |
| `ask.txt` | A keeper's question from the dashboard; `{{image_note}}` says whether the current camera picture is attached (vision) | `AskQuestion` |

## One prompt chunk per lizard

```
lizard chunk (one request)
├── system.txt + response-schema.json
├── CONTEXT chunk      context-chunk.txt
├── IMAGES chunk 1     images-chunk.txt + images-01.pdf  (minutes 0-59)
├── IMAGES chunk 2     images-chunk.txt + images-02.pdf  (minutes 60-119)
└── ...
```

A range shorter than 60 min gives one IMAGES chunk with fewer images (at least 1). No video moment is sent twice: the live "camera" loops, so when the range is longer than the video, only the last part of the range that fits in one pass of the video is analysed (the bundle's notes say so).

Keep the "can't tell" answer as the **last** option of every enum in `response-schema.json` ("can't see lizard", "no bowl visible"): a missing or off-list answer from a real provider is replaced by the last option.

Generated bundles are written to `data/<mode>/reptiles/<id>/prompts/<bundle>/` (git-ignored) with a `manifest.json`, so every prompt can be inspected before it is sent.

`response-schema.json` is the animal-neutral base. Each bundle gets its own copy, built from the animal's species profile (`research.BuildResponseSchema`): the species' activities, its species checks under "Species checks", and its named conditions under "Conditions seen".
