---
name: tasks
description: Scan the docs for open questions, TBDs, unchecked actions, undigested sources, and unfinished experiments, and propose GitHub issues for anything not already tracked. Use when the user asks to find, generate, or update tasks.
argument-hint: "[optional: folder or file to limit the scan]"
---

Propose tasks following `CONTRIBUTING.md`. If `$ARGUMENTS` is given, limit the scan to that path.

1. **Scan for candidate work:**
   - `docs/open-questions.md`: rows in the Open table
   - `docs/**/*.md`: `TBD` values
   - `docs/notes/*.md`: unchecked Actions items without an issue link; Open questions not yet in `open-questions.md`
   - `docs/sources/` files with no matching note (task: digest it)
   - `docs/approaches/*.md` with Status Trying and an empty Evidence section (task: an experiment)
   - `experiments/*/README.md` with Status not Done and an empty Result or Conclusion
2. **Check consistency** while scanning and list what you find as tasks too: a note whose `source:` file doesn't exist; a relative link to a missing file; a function in `src/` with no `functions.md` entry.
3. **Check what's already tracked:** `gh issue list --state all --limit 500 --json number,title,body,state,labels`. Drop candidates an open or closed issue already covers.
4. **Shape each task** to fit one PR: a short title; one label from `docs`, `src`, `exp`, `repo`; a body with Goal, Done when, and Context (link the doc and section it came from).
5. **Propose, don't create.** Show a numbered table: title, label, source. Ask which to create, merge, split, or reword.
6. **After approval,** run `gh issue create --title ... --label ... --body ...` for each, list the numbers and links, and add the number to the note's Actions item it came from.
