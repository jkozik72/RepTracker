---
source: docs/sources/2026-11-14-dashboard-changes-chat.md
type: internal
date: 2026-11-14
digested: 2026-11-14
relates-to: [Q11, Q15]
---

# Dashboard changes (chat message)

## Summary

Changes to the dashboard plan in `2026-11-14-dashboard-plan-chat.md`: Settings holds only dev mode; dev mode adds uploads and a Toy / Main data switch; sensor files become JSON; the dashboard gets a compact view.

## Key points

- (Message) Remove the AI section from Settings; keep only dev mode.
- (Message) With dev mode on: upload videos (cameras) and JSON sensor files.
- (Message) Sensor JSON: a `t` key, the time between samples in ms, and a `value` field.
- (Message) With dev mode on: switch between toy mode (the sample setup) and main mode (starts with no lizards or data; the user adds them).
- (Message) Dashboard: a control at the top to switch between compressed and full views.
- (Message) Compressed view: one block per lizard with the name on top, alerts to the right of the name, the video below; 2 per row, so 4 lizards fit on screen.

## Relevance

Answers part of Q15 (sensor file format) for the simulated sensors. With the API key gone from Settings, a real provider (Q11) will need another way to get its key.

## Open questions

- Where does a real provider's API key come from once Q11 is decided (server environment variable, or back in Settings)?
- `value` is read as a list of samples, sample i at i × `t`; confirm.

## Actions

- [x] Settings: dev mode only; Toy / Main switch and uploads appear when it is on
- [x] Sensor files are JSON `{"t", "value"}`; toy samples converted
- [x] Data split into `src/website/data/toy/` and `src/website/data/main/`
- [x] Full / Compact view toggle on the dashboard
