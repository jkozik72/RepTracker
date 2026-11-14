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
| lizard | The tracked animal. One section of the dashboard each. Whether other reptiles are in scope: Q16. | animal, pet |
| species | A lizard's species: a field of the add-lizard form and the input to research. | |
| web app | The local website as a whole: UI, web interface, backend. | website, app |
| dashboard | The page with the status and alerts bar and one section per lizard. | |
| raw video | A recorded video file, before motion tracking. | |
| processed video | The video that motion tracking outputs. | |
| motion tracking | Video in, position of the lizard out. | |
| position | Where the lizard is in a frame. Units: TBD (Q11). | |
| speed | How fast the position changes. Units: TBD (Q11). | |
| lizard present | Whether the lizard is in the frame. | in frame, on screen |
| statistics | Values computed per lizard: position, speed, lizard present, and others (Q11). | |
| movement graph | The dashboard graph of how much a lizard moved throughout the day. | |
| research | The LLM's information gathering for one species. | |
| structured information | What research outputs, per species. | knowledge base, research files |
| poll | One request to the AI model to analyze a frame. Poll rate: how often that happens. | |
| report | The structured result of one poll. It gives the status. | |
| status | A lizard's condition, from a finite set (examples: shedding, overweight). The set: Q10. | |
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

### `src/` (TBD, Q2)

No functions yet.
