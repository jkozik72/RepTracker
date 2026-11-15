---
source: docs/sources/2026-11-15-claude-provider-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [Q11, Q20, D4]
---

# Claude API as the AI provider (chat message)

## Summary

The team now uses the Claude API. It is to be added as an AI provider, with a place in the app to enter the API key.

## Key points

- (Message) "Now we are using claude API": the provider choice.
- (Message) Add it as an AI provider, next to the existing ones.
- (Message) The app needs a place to put the API key.

## Relevance

Answers Q11 (which provider) and Q20 (how the app authenticates); recorded as D4.

## Open questions

- Which Claude model? Not stated; the app uses `claude-opus-5-5` by default, changeable with `REPTRACKER_CLAUDE_MODEL`.
- Does research (species reference) also use Claude? Not stated.

## Actions

- [x] `src/website/claude_ai.py`: Claude provider (analyses, questions, connection test), tests in `test_claude_ai.py`
- [x] Settings (dev mode): Claude option with an API key field; the key is kept in `src/website/data/claude-key.json` (git-ignored)
- [x] D4 in `decisions.md`; Q11 and Q20 moved to Answered
