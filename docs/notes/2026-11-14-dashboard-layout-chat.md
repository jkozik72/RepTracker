---
source: docs/sources/2026-11-14-dashboard-layout-chat.md
type: internal
date: 2026-11-14
digested: 2026-11-14
relates-to: [Q13]
---

# Dashboard layout changes (chat message)

## Summary

Follow-up requests for the dashboard: multi-file uploads, a "Source:" label on the video, position as a percentage when no enclosure width is given, and one layout (2 per row, compact by default, click a name to expand) instead of a Full/Compact toggle.

## Key points

- (Message) Allow uploading several videos at once.
- (Message) Show "Source:" next to the video's name on the video.
- (Message) With no enclosure width, position is a percent of the video's width.
- (Message) Always 2 per row; clicking a lizard's name expands it; compact is the default.

## Relevance

Makes the enclosure width optional, so position (Q13) has two units: cm from the left wall, or % of the video width.

## Open questions

None.

## Actions

- [x] Upload inputs take several files; each uploads in turn with its own progress and result
- [x] Video badge reads "Source: <video>"
- [x] Enclosure width optional; prompts, response schema (`position`) and the position chart use cm or %
- [x] Full/Compact toggle replaced by click-to-expand, compact by default
