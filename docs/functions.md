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

Names in `src/website/` are written as the code has them (PascalCase); the case style is not decided yet (Q2).

### `src/website/main.py`

### `SendPrompt`
- **Does:** Makes one poll: sends the newest images of an enclosure and the species research to Gemini and returns the report.
- **Lives in:** `src/website/main.py`
- **In / out:** lizard name, path to the species research file, path to a PDF, an image, or a folder of images → `dataSchema` filled out (temperatures in °F, humidity in %)
- **Notes:** One AI call per poll. The third parameter is still called `pathToPDF`, but a folder of images works and needs no PDF step.

### `src/website/ai.py`

### `AnalyzeEnclosure`
- **Does:** Builds the request (images, prompt, schema, research), calls Gemini once, and returns the normalized report.
- **Lives in:** `src/website/ai.py`
- **In / out:** media paths, species, research text, schema, allowed options, prompt template → report dict
- **Notes:** Uses Vertex AI with the machine's Google login; no key in the repo. Project, location, and model come from `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `REPTRACKER_MODEL`.

### `CollectMedia`
- **Does:** Chooses the files to send for a path: a PDF, one image, or the newest 8 images of a folder.
- **Lives in:** `src/website/ai.py`
- **In / out:** path → list of file paths, oldest first

### `NormalizeReport`
- **Does:** Forces the model's reply into the shape of the schema, so the rest of the app can trust the keys and values.
- **Lives in:** `src/website/ai.py`
- **In / out:** raw reply, schema, allowed options → report dict
- **Notes:** A value outside its options becomes "can't see lizard" where the field has that option, otherwise the schema default.
