# Contributing

How we work: branches, pull requests, review. For the folder layout, the documentation workflow, and the editing rules, see [CLAUDE.md](CLAUDE.md).

## Getting started

1. Clone the repo. Install [Claude Code](https://claude.com/claude-code) (recommended: it reads `CLAUDE.md` and provides `/digest` and `/tasks`).
2. Read [CLAUDE.md](CLAUDE.md).
3. Never commit directly to `main`. Every change goes through a pull request.
4. Running the code: TBD until language and tooling are decided ([Q2](docs/open-questions.md)).

## Branches

`<area>/<short-name>`, or `<area>/<issue#>-<short-name>` when there is an issue. The area is the top-level folder you're changing:

| Area | Use for |
|---|---|
| `docs` | sources, notes, anything in `docs/` |
| `src` | code |
| `exp` | experiments |
| `repo` | the workflow itself: CLAUDE.md, CONTRIBUTING.md, templates, skills |

Examples: `docs/digest-blazepose-paper`, `src/14-smooth-landmarks`, `exp/optical-flow-spike`.

Issues are optional. If a task has one, its number goes in the branch name and the PR body says `Closes #<n>`.

## Commits and PRs

- Commit summary lines in imperative mood (`Add X`, not `Added X`).
- One task per PR; keep PRs small. Draft PRs for work in progress.
- Fill in the PR template: what changed and why (link notes, decisions, approach pages), how you verified it, and the checkbox: docs match the change, or no design impact.

## Review and merging

- One teammate approves before merging.
- Reviewers check the change **and** that the docs match it: a new or changed function has its `docs/functions.md` entry, a design choice has its `decisions.md` entry, an approach's Status is current. This is our only enforcement.
- Squash merge, then delete the branch.

## Editing rules

One table, in [CLAUDE.md § Editing rules](CLAUDE.md#editing-rules).

## Working with Claude

- Claude follows `CLAUDE.md`. Its changes go through PRs and review like anyone else's.
- `/digest <file or URL>`: file a source, write its note, propose doc updates.
- `/tasks`: scan for open questions, `TBD`s, unchecked actions, undigested sources; propose issues.
- Review what Claude proposes before approving changes to the synthesized docs or creating issues.
