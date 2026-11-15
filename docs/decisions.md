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

## D2 (2026-11-14): Keep Hack The Nest material in its own folder, `docs/hackathon/`
- **Context:** The team asked for the Hack The Nest (Nov 14–15, 2026) tracks and opportunities to be written down before the project is described, so the two can be compared later without bias.
- **Options:** A: fold the tracks into `overview.md`. B: keep only the note in `docs/notes/`. C: a separate `docs/hackathon/` folder built from the note, with an empty comparison page.
- **Chose:** C, because the facts are about the event, not the project, and a separate folder with `project-fit.md` keeps the comparison explicit.
- **Consequences:** `docs/hackathon/` follows the same editing rules as the other synthesized docs. Its analysis blocks are labelled as not official. Which tracks to enter stays open (Q6).
- **Sources:** docs/notes/2026-11-14-hack-the-nest-research-report.md
- **Replaces:** none
