# Decisions

Append-only log, oldest first. One entry per decision we would otherwise re-argue: approach, library, naming, how the repo works. Never edit or delete an entry; to reverse one, add a new entry that says what it replaces. The entry is the whole process: if options need comparing, compare them here (or in an `open-questions.md` row while undecided).

Entry format:

```markdown
## D<n> (YYYY-MM-DD): <title>
- **Context:** why we had to choose
- **Options:** A ..., B ..., C ... (one line each: what it would mean)
- **Chose:** X, because ...
- **Consequences:** what changes, what we give up, what to watch
- **Sources:** docs/notes/..., experiments/..., docs/approaches/...
- **Replaces:** D<m>, or none
```

---

## D1 (2026-11-14): Organize the repo as a sources → notes → docs knowledge base
- **Context:** The project needs one place for research, design decisions, a function reference, and approach documentation that stays trustworthy while the code moves fast.
- **Options:** A: a free-form `docs/` folder. B: the full HydroScout system (sources/notes/project, trade studies, requirement IDs, two open-question registers). C: HydroScout's pipeline and rules without trade studies and ID schemes.
- **Chose:** C. The pipeline (raw sources, one note per source, synthesized docs that cite notes), the append-only log, and the `TBD` rule are what keep facts traceable; trade studies and requirement IDs were the overhead for a small team.
- **Consequences:** Every fact in `docs/` traces to a note or is `TBD`. A design choice is one entry here, not a document. Approaches and functions each have one place. `/digest` files sources; `/tasks` finds what is open. Nothing checks this automatically; review does.
- **Sources:** The HydroScout repository (`CLAUDE.md`, `docs/notes/_template.md`, `docs/project/decisions.md`, `prototypes/README.md`, `.claude/skills/digest/SKILL.md`) as the model.
- **Replaces:** none

## D3 (2026-11-14): Recorded video and sensor files instead of live cameras and sensors
- **Context:** The dashboard should look live: a video and a movement graph that update as if in real time. With real hardware that means real cameras, real sensors, and real-time processing. The team made this choice at the whiteboard; this entry logs it, and its date is the day it was logged.
- **Options:** A: real cameras and sensors, streamed and processed in real time. B: recorded, finite files, processed ahead of time: one video the team takes of a real lizard, videos found online of other lizards in their enclosures, and finite sensor time series. The web app reads them by index, so the dashboard looks live.
- **Chose:** B, because it simplifies real-time processing (brief) and nothing requires real-time polling (board: "files not streams").
- **Consequences:** Inputs are files, not streams. Video is preprocessed: raw video in, processed video and statistics out, and the backend polls those. No hardware integration. We give up showing the system on live hardware: "real time" on the dashboard is a playback of recorded data. How the playback maps onto time is open (Q17).
- **Sources:** `docs/notes/2026-11-14-project-brief.md` § Inputs (s. 22–29); `docs/notes/2026-11-14-whiteboard-system-design.md` § Design decisions.
- **Replaces:** none
