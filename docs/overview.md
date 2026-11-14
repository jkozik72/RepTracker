# Overview

> Reflects: [`notes/2026-11-14-project-brief.md`](notes/2026-11-14-project-brief.md) (cited below as "brief"), [`notes/2026-11-14-whiteboard-system-design.md`](notes/2026-11-14-whiteboard-system-design.md) ("board"), [`notes/2026-11-14-whiteboard-ui.md`](notes/2026-11-14-whiteboard-ui.md) ("UI board")

## What we're building

RepTracker is a dashboard for keeping track of your reptiles ([brief § Product][b-product]). It runs on a single computer as a local website. For each lizard it shows a video, a movement graph, statistics, and a status with alerts. The status comes from an AI model that looks at frames of the video, with what an LLM has researched about the species as its reference. The video and sensor data are recorded files, played back so that the dashboard looks live ([D2](decisions.md)).

## Goals and requirements

What it must do. One bullet each, with its source: a note path and page or section, a decision (D<n>), or `TBD`.

- **Dashboard.** Status and alerts at the top. A section per lizard with its name, video, stats, and movement graph. A way to add a lizard. ([brief § Web app][b-web]; [UI board § Dashboard][u-dash])
- **Add-lizard form.** Name, age, species, and optionally previous data; then its "hardware": cameras (top, side) and sensors. ([brief § Web app][b-web]; [UI board § Add lizard form][u-form]; [board § Add lizard][s-add])
- **Movement graph.** How much the lizard moved throughout the day, to track its cycles. Health is read from it. ([brief § Product][b-product])
- **Motion tracking.** Video in, position of the lizard out, also when the lizard is not on screen and when frames repeat. Approach: not decided ([Q6](open-questions.md), [Q7](open-questions.md)). ([brief § Motion tracking][b-motion])
- **Statistics.** From the processed video: position, speed, lizard present. Also events, such as when the lizard last shed and how long it took. Full list: TBD ([Q11](open-questions.md)). ([brief § Statistics][b-stats])
- **Research.** Given a species, an LLM produces structured information about it, which the image analysis uses. Contents: TBD ([Q12](open-questions.md)). ([brief § Research and image analysis][b-ai]; [board § AI pipeline][s-ai])
- **Image analysis.** At a poll rate, while the lizard is present, a frame goes to an AI model. It returns a structured report with a status from a finite set (examples: shedding, overweight), or says the lizard is not in frame. Preferably one AI API call per poll. Model, poll rate, statuses: TBD ([Q8](open-questions.md), [Q9](open-questions.md), [Q10](open-questions.md)). ([brief § Research and image analysis][b-ai])
- **Alerts.** Flags from the analysis reach the user as alerts in the web app. ([board § AI pipeline][s-ai])
- **Settings and secrets.** A settings page takes the AI API key. The key is set at runtime and not stored. ([board § Secrets and settings][s-secrets]; [UI board § Settings][u-settings])

## Scope

- **In scope:** the web dashboard, motion tracking on recorded video, statistics, species research, AI image analysis with alerts.
- **Out of scope:** real cameras and sensors, and live streams ([D2](decisions.md)).
- **Not settled:** lizards only, or other reptiles too ([Q16](open-questions.md)).

## Constraints

| Constraint | Value | Source |
|---|---|---|
| Input | Recorded, finite video files (one filmed by the team, others found online) and finite sensor time series. No live cameras or sensors. | [brief § Inputs][b-inputs]; [D2](decisions.md) |
| Platform | A single computer, serving a local website | [brief § Product][b-product] |
| Language and tooling | TBD. The board sketches a Flask backend with an HTML and CSS web interface. | [Q2](open-questions.md); [board § High level][s-high] |
| AI access | Through an API, with a key set at runtime and not stored | [board § Secrets and settings][s-secrets], [§ AI pipeline][s-ai] |

[b-product]: notes/2026-11-14-project-brief.md#product
[b-ai]: notes/2026-11-14-project-brief.md#research-and-image-analysis
[b-stats]: notes/2026-11-14-project-brief.md#statistics
[b-web]: notes/2026-11-14-project-brief.md#web-app
[b-inputs]: notes/2026-11-14-project-brief.md#inputs
[b-motion]: notes/2026-11-14-project-brief.md#motion-tracking
[s-secrets]: notes/2026-11-14-whiteboard-system-design.md#secrets-and-settings-top-left
[s-add]: notes/2026-11-14-whiteboard-system-design.md#add-lizard-middle-left
[s-high]: notes/2026-11-14-whiteboard-system-design.md#high-level-bottom-left
[s-ai]: notes/2026-11-14-whiteboard-system-design.md#ai-pipeline-top-right
[u-dash]: notes/2026-11-14-whiteboard-ui.md#dashboard
[u-settings]: notes/2026-11-14-whiteboard-ui.md#settings
[u-form]: notes/2026-11-14-whiteboard-ui.md#add-lizard-form
