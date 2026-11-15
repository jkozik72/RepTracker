---
source: docs/sources/2026-11-15-hourly-vision-loop-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [D4]
---

# Hourly AI call, vision questions, looped video (chat message)

## Summary

Three requests: a Settings option for an hourly AI call (off by default); a vision option when asking the AI a question, using the current picture; and a bug report: a 60-min range on a 30-min video sent the looped video, so the position data repeated.

## Key points

- (Message) Settings: "Hourly AI call", disabled by default.
- (Message) Ask a question: an option to use vision with the current picture.
- (Message, screenshot) Range 10:50 to 11:50 on a 30-min video: the video was sent looped and the position looked wrong. In the screenshot the position graph's second half repeats its first, and the AI itself reported a looping feed.

## Relevance

Changes how prompt bundles are built (no repeated video moments) and adds two AI features on top of D4.

## Open questions

- Should the hourly call run without the page open (on the server)? Not asked; it runs in the page for now.

## Actions

- [x] `GeneratePrompts` never sends a video moment twice; a range longer than the video is cut to its last part that fits in one pass
- [x] Position graph times in local time, like the rest of the page
- [x] Ask a question: "Use vision" sends the current camera picture (Claude and Gemini; the Mock ignores it)
- [x] Settings: "Hourly AI call", off by default
