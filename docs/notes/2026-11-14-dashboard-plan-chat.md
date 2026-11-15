---
source: docs/sources/2026-11-14-dashboard-plan-chat.md
type: internal
date: 2026-11-14
digested: 2026-11-14
relates-to: [Q11, Q13, Q15, D3]
---

# Dashboard plan (chat message)

## Summary

A team member's plan for the RepTracker web app: simulated camera and sensors from files, an add-lizard form that saves a JSON config, live camera and sensor views, AI prompts built from 1 image per minute plus a stats context, and a dev mode to control time and inspect prompts before sending.

## Key points

- (Message) Position 0 is the left wall; a top-down camera still measures left to right.
- (Message) No real hardware: the camera is a video file and each sensor a finite time series, both in folders.
- (Message) Add-lizard form: name, species, camera view (top or side), video picked from a dropdown of file names without `.mp4`.
- (Message) Two sensors, hot side and cold side; the hot side is set to left or right. Each has a temperature series and a humidity series, picked like the video, each with a unit setting.
- (Message) The configuration is saved as JSON.
- (Message) Camera and sensors are shown in real time; sensor readings are graphed with a window that grows to 5 days.
- (Message) AI: one chunk of prompts per lizard, containing image chunks (1 image per minute, stored in a single PDF) and one context chunk from the lizard's stats.
- (Message) Settings: dev mode adds clock controls above the alerts (speed, set the moment, pause, resume) and, per lizard, a time range with "generate prompts for time range" to inspect every prompt, send it, and see stats and analysis update. Must handle a video or range shorter than 60 min.
- (Message) Every prompt format is a file, so it can be inspected by hand.
- (Answers) AI provider: not known yet. Position: real distance, with an "Enclosure Width" setting in the config.

## Relevance

Defines the web app in `src/website/`. Consistent with D3 (recorded video and sensor files) on `main`. Leaves the AI provider open (Q11 on `main`).

## Open questions

- Which AI provider? Already Q11 on `main`; the app ships a Mock provider until it is chosen.
- How is "1 image per minute ... in a single PDF" split for ranges over 60 min? Implemented as one PDF per 60 images; confirm.
- Does the sensor graph window keep sliding after 5 days, or stop? Implemented as sliding.

## Actions

- [x] Built the add-lizard form, JSON config, live camera and sensor views, dev clock, and prompt inspector in `src/website/`
- [x] Prompt formats as files in `src/website/prompts/`
- [x] Added the functions to `docs/functions.md`
- [ ] Choose the AI provider (Q11) and add it to `PROVIDERS` in `src/website/main.py`
