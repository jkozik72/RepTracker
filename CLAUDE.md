# Claude Guide

RepTracker is a motion-tracking project. What it tracks, for whom, and on what input is still being written down (see `docs/open-questions.md`, Q1). This file describes how the repo is organized and how information flows through it. Claude Code reads it every session; people should read it once.

## Layout

```
README.md            the project: what it is, status, how to run it
CLAUDE.md            this file: how the repo is organized, the workflow, the rules
CONTRIBUTING.md      how we work: branches, PRs, review
.github/             pull request template
.claude/skills/      Claude skills: /digest, /tasks
.gitignore           OS/editor junk, secrets, large experiment data; language entries once tooling is decided
docs/
├── sources/         1. RAW: files as received, named YYYY-MM-DD-slug.ext. Add only; never edited.
├── notes/           2. DIGESTED: one note per source, same name with .md, from _template.md
├── overview.md      3. SYNTHESIZED (current state only): what we're building; goals and requirements, each with a source
├── architecture.md     how it's built; undecided parts link an open question or an approach page
├── approaches/         one page per motion-tracking approach: what, how, pros/cons, evidence, status. _template.md
├── functions.md        naming conventions, glossary, and the reference of named functions: what each does, where it lives
├── decisions.md        append-only log of decisions, D1, D2, ...
└── open-questions.md   every open question in one table, Q1, Q2, ...; answered rows move to the bottom
experiments/         quick spikes, one folder each, README with Question / Setup / Result / Conclusion
src/                 the code. Language and tooling: TBD (Q2)
```

## Workflow: sources → notes → docs

Information moves one way.

1. **Add.** Put the raw file in `docs/sources/` as `YYYY-MM-DD-slug.ext`. The date is the source's own (published, version, or the day a web page was saved). The slug is a few lowercase words; for papers, the first author or organization plus the topic (`2024-03-05-smith-pose-estimation.pdf`). Save web pages as PDF when you can. If a source has no file (a live docs site, a video), the note alone stands for it, with the URL and the date accessed in its frontmatter. `/digest` does all of this.
2. **Digest.** Write `docs/notes/<same-name>.md` from `docs/notes/_template.md`: summary, key points with page/section/timestamp references, relevance, open questions, actions. Nothing that isn't in the source.
3. **Apply.** If the note changes what we know or plan, update the synthesized docs and cite the note. List each change in the note's Actions.

A source with no matching note has not been digested yet. A fact with no source is `TBD` or a row in `open-questions.md`.

## Decisions

A decision is anything we would otherwise re-argue: which approach, which library, how to name things, how the repo works. The entry in `docs/decisions.md` is the whole process; there are no separate trade-study documents. Format (also in the file):

```
## D<n> (YYYY-MM-DD): <title>
- **Context:** why we had to choose
- **Options:** A ..., B ..., C ...
- **Chose:** X, because ...
- **Consequences:** what changes, what we give up
- **Sources:** docs/notes/..., experiments/..., docs/approaches/...
- **Replaces:** D<m>, or none
```

Not ready to decide? Add a row to `open-questions.md` with the candidate options. Run an experiment if evidence is missing. Then decide. After a decision: update `architecture.md`, the approach page's Status or `functions.md`, and move the open question to Answered with a link to D<n>.

## Approaches

One file per motion-tracking approach in `docs/approaches/<name>.md`, from `_template.md`. Status: Candidate | Trying | In use | Dropped. The page is the one place that says what the approach is, how it works, its pros and cons, the evidence (notes, experiments), and the decision that set its status. Dropped approaches stay; their page says why. Don't treat a Candidate or Trying approach as decided.

## Functions

`docs/functions.md` holds the naming conventions, a glossary (one term per concept), and one entry per named function worth looking up: what it does, where it lives, anything about the name that isn't obvious. Add or update the entry in the same PR as the code. Conventions change only through a decision entry.

## Editing rules

| Location | Rule |
|---|---|
| `docs/sources/` | **Add only.** Never edit, rename, or delete a committed file. A new version is a new file. (Renaming a just-added, uncommitted file is fine.) |
| `docs/notes/` | Edit to fix or add detail; must stay faithful to the source. Strike answered open questions, check off done actions. |
| `docs/overview.md`, `architecture.md`, `functions.md`, `approaches/` | Current state only, through PRs. History lives in `decisions.md`, the notes, and git. |
| `docs/decisions.md` | **Append only.** Never edit or delete an entry. Reverse one with a new entry that names what it replaces. |
| `docs/open-questions.md` | Add rows at the bottom; never reuse an ID. Answered rows move to the Answered table with the answer and its source. |
| `experiments/` | Anything goes, but every experiment has a README with a Result and a Conclusion. Never delete; dropped ideas stay. |
| `src/` | Through PRs, with the matching `functions.md` entries. |
| `CLAUDE.md`, `CONTRIBUTING.md`, `.github/`, `.claude/` | Change rarely, with team agreement, in a `repo/` PR. |

## Branches and PRs

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: branch `<area>/<short-name>` where the area is `docs`, `src`, `exp`, or `repo`; one task per PR; one approval; reviewers check that the docs match the change.

**Auto-named branches:** the Claude app gives sessions generated branch names. Before the first push, rename to the convention (`git branch -m <area>/<short-name>`). Never push an auto-named branch. Rename before opening a PR: renaming a branch on GitHub closes its open PRs.

## Rules

- **Don't invent facts.** Unknown values are `TBD`; questions go in `docs/open-questions.md`.
- **Every goal, requirement, and decision cites its source:** a note path with page or section, an experiment, or a decision. Something said in a meeting or chat becomes a source first (save the message or minutes to `docs/sources/`), then a note.
- **Prefer notes over re-reading sources.** Open the source when the note lacks detail, then improve the note.
- **Don't reverse a decision silently.** Add a new entry that says what it replaces and why.
- **Synthesized docs describe the current state only.**
- File names are lowercase and hyphen-separated. Diagrams are Mermaid. State units (ms, fps, deg, m).
- Keep every doc short. A template beats prose; a table beats paragraphs.
