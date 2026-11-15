---
source: docs/sources/2026-11-15-ai-polling-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [D4]
---

# AI polling interval (chat message)

## Summary

Replaces the on/off "Hourly AI call" setting with a configurable AI polling interval and Start / Stop controls, stopped at first.

## Key points

- (Message) Not a bool: configure the AI polling interval.
- (Message) Start and stop controls; initially stopped.
- (Message) Several intervals to choose from.
- (Follow-up) Images per interval.
- (Follow-up, screenshot) The position graph still has holes: positions for 21 of 30 images. The saved analysis shows the AI matched all 30 images and reported the lizard not visible in 9.

## Relevance

Sets the poll rate for analyses (the brief's "poll", see the glossary in `functions.md`) from the dashboard instead of a fixed hour.

## Open questions

None.

## Actions

- [x] Images per interval: 1 per minute, or 5 to 60 spread evenly (at least 1 min apart), in AI polling and the dev panel
- [x] Position graph: a dashed line joins the positions seen before and after hidden images; ticks mark the hidden images
- [x] Settings: AI polling with intervals 15 min, 30 min, 1 h, 2 h, 3 h, 6 h and Start / Stop; stopped whenever the page loads
