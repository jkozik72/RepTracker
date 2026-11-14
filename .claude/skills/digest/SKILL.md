---
name: digest
description: Digest a source (paper, article, library docs, video, dataset page, internal doc) into docs/sources/ and a note in docs/notes/, then propose updates to the synthesized docs. Use when the user adds a new source, pastes a URL to keep, or asks to digest or summarize one.
argument-hint: <path to a file (anywhere on disk or in docs/sources/) or a URL>
---

Digest the source at `$ARGUMENTS` following `CLAUDE.md`. The user should never have to name or sort files by hand.

1. **Find the source.**
   - No argument: list files in `docs/sources/` with no matching note in `docs/notes/` and ask which to digest.
   - A file attached to the chat without a path: ask for its path (the original file is needed to add it to the repo).
   - A URL: fetch it. If it can be saved as a PDF (an article, a paper), save it and continue as a file. If it can't (a live docs site, a video, a repository), the note alone stands for it: `source:` holds the URL and `accessed:` today's date.
2. **Read the whole source.** Long PDFs in page ranges until finished. For a video, use the transcript or captions; if there are none, say what could and couldn't be read.
3. **Check for duplicates** before saving anything:
   - Same file: `sha256sum` against every file in `docs/sources/`. On a match, stop and name the existing source and note.
   - Same URL: grep `source:` in `docs/notes/`. On a match, stop, or ask whether to update that note instead.
   - Same document, different file or URL (re-download, preprint vs. published, new version): search `docs/notes/` for the title and authors. If one matches, ask: duplicate (stop), new version (continue as a new file), or different (continue).
4. **Name and place it:** `docs/sources/YYYY-MM-DD-slug.ext`.
   - Date: the source's own (published, version, release); for a saved web page, the day it was saved. If no date can be found, use today's and say so in the note.
   - Slug: a few lowercase hyphenated words; for papers, the first author's last name (or the organization) plus the topic, e.g. `2024-03-05-smith-pose-estimation.pdf`.
   - Ask only if a required detail is missing. If the name already exists, ask whether this is a new version.
   - File outside the repo: `cp` it in. File already in `docs/sources/` and not yet committed (`git ls-files --error-unmatch <path>` fails): `mv` it to the right name. Never rename, move, or modify a committed file.
5. **Set up the branch.** If the current branch is auto-named or unrelated, rename it or create one: `docs/digest-<slug>`.
6. **Write the note** at `docs/notes/<same-name>.md` from `docs/notes/_template.md`. Fill every section; cite pages, sections, or timestamps in Key points; delete `accessed:` for files. Don't add anything that isn't in the source.
7. **Compare against the docs.** What does the source add to, contradict, or change in `docs/overview.md`, `docs/architecture.md`, `docs/approaches/*.md` (evidence for or against an approach; a new approach worth a page), `docs/functions.md` (terms for the glossary), `docs/decisions.md` (a decision now in question), and `docs/open-questions.md` (a question answered or raised)?
8. **Report:**
   - where the file was saved and under what name, or that it is a URL-only note
   - a short summary
   - proposed changes to the docs, each citing the note
   - proposed issues from the note's Open questions and Actions, shaped as in `/tasks`, skipping any already tracked

   Don't edit anything outside `docs/sources/` and the new note until the user approves. The user can ask for a different file name at this point.
9. **After approval:** make the approved changes citing the note (`docs/notes/<name>.md`, page or section), create the approved issues, and record both in the note's Actions: checked items for changes made, unchecked items with issue numbers for follow-ups.
