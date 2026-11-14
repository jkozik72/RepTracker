---
source: docs/sources/2026-11-14-whiteboard-ui.jpg
type: internal
date: 2026-11-14        # the day the photo was received; the file carries no capture date
digested: 2026-11-14
relates-to: [Q1, Q12, Q13, Q17]
---

# Whiteboard: UI (photo, received 2026-11-14)

## Summary

A photo of a whiteboard headed "UI". It sketches the dashboard layout and a settings page, and lists the fields of the add-lizard form. It was attached to the [project brief](2026-11-14-project-brief.md), which says the board shows the same content (s. 40–41). The photo does not say when or by whom the board was drawn. Everything is handwritten; `[?]` marks an uncertain reading.

## Key points

Each heading names a part of the board.

### Dashboard

- A question at the top, with an arrow to the dashboard: "Should it display results of Research?"
- "Dashboard": a "Status / Alerts" bar across the top. Under it one panel: "Name", "Stats", and "AI questions" [?] in the left column; "Videos" and "Movement graph" in the right column.
- An "Add" button under the panel.
- Caption: "Add and Monitor Lizards".

### Settings

- "Settings": one box, "Keys".

### Add lizard form

- "Add Lizard – Form".
- "Lizard": "Name", "Age", "Species", "previous data, optional".
- "Hardware" (in quotation marks on the board): "Cameras: T, S"; "Sensors: H, C".

## Relevance

The layout of the web app's pages. It matches the brief (s. 18–21) and adds a settings page for keys, an "AI questions" area on the dashboard, and a hardware part of the add-lizard form with cameras and sensors. "T, S" lines up with the top and side cameras on the [system-design board](2026-11-14-whiteboard-system-design.md) (Add lizard; AI pipeline).

## Open questions

- Should the dashboard display the results of research? (asked on the board) → Q12
- What are the sensors "H, C"? (Add lizard form) → Q13
- What is "AI questions" [?]: does the user ask the AI about a lizard? (Dashboard) → Q17
- What is the optional "previous data"? (Add lizard form) → Q17

## Actions

- [x] `docs/overview.md`: Dashboard, Add-lizard form, Settings and secrets
- [x] `docs/architecture.md`: the pages table under Web app
- [x] `docs/open-questions.md`: Q12 (display research results), Q13 (sensors "H, C"), Q17 ("previous data", "AI questions")
