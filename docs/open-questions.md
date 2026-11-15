# Open questions

Every open question in one place. Add rows at the bottom with the next ID; never reuse an ID. A question about **what** we're building is answered by a fact with a source, then recorded in `overview.md`. A question about **how** is answered by a decision in `decisions.md`. When answered, move the row to **Answered** with the answer and its source.

## Open

| ID | Question | Why it matters | Candidate answers / options | Raised by |
|---|---|---|---|---|
| Q2 | Which language and tooling for `src/` and `experiments/`? | Sets the case style in `functions.md`, how experiments run, and `.gitignore`. | Python with a Flask backend and an HTML and CSS web interface, as sketched on the board ([board § High level][s-high]). Not yet a decision. | repo setup, 2026-11-14 |
| Q8 | Which motion-tracking pipeline do we build? | It produces position, speed, and the movement graph. The brief wants no YOLO model unless it is necessary. | [Frame differencing](approaches/frame-differencing.md) with a [Kalman filter](approaches/kalman-filter.md) or a [Bayes filter](approaches/bayes-filter.md); a [YOLO detector](approaches/yolo-detector.md) as the fallback. Needs an experiment on our video. | [brief § Motion tracking][b-motion], 2026-11-14 |
| Q9 | How do we detect and handle repeated frames? | A repeated frame makes the frame difference zero. That reads as no motion and disturbs the position. | TBD | [brief § Motion tracking][b-motion] (s. 35–36); [board § Video processing][s-video], 2026-11-14 |
| Q10 | What decides "lizard present", and what is the poll rate? | The backend polls the AI only if the lizard is present, and the brief prefers one AI API call per poll. | Lizard present from the motion statistics; from the VLM or LLM; from both ("Speed and VLM check" on the board). Poll rate: TBD. | [brief § Research and image analysis][b-ai], [§ Statistics][b-stats]; [board § Design decisions][s-dd], 2026-11-14 |
| Q11 | Which AI model or models, from which provider? Must the image model be a VLM? One model for research and image analysis, or two? | Sets the API, the cost of a poll, and the structured-output format. | TBD | [brief § Research and image analysis][b-ai] (s. 5, 8), 2026-11-14 |
| Q12 | What is the finite set of statuses, and which fields does the structured report have? | Status, alerts, and statistics such as the last shed are built from the report. | Examples so far: shedding, overweight; "not in frame". | [brief § Research and image analysis][b-ai] (s. 10–14), 2026-11-14 |
| Q13 | Which statistics do we compute, and in what units? | They fill the stats panel and the movement graph, and they go to the AI. | Named so far: position, speed, lizard present, last shed, shed duration. | [brief § Statistics][b-stats], 2026-11-14 |
| Q14 | What does research produce: which fields, images or not, stored where? Does the UI display it? | It is the AI's reference for the species. The UI board asks whether to display it. | TBD | [brief § Research and image analysis][b-ai] (s. 6–8); [UI board § Dashboard][u-dash], 2026-11-14 |
| Q15 | Which sensors, and what do their files look like: format, sample rate, length? | The add-lizard form selects them and the AI receives them. | "H, C" on the UI board, not spelled out. | [brief § Inputs][b-inputs] (s. 24); [UI board § Add lizard form][u-form], 2026-11-14 |
| Q16 | Which videos do we use, and in what form: source, length, resolution, frame rate, top or side view, the JSON that lists the cameras? | Motion tracking is designed and tested on them. | One video filmed by the team; others found online. | [brief § Inputs][b-inputs] (s. 23); [board § Add lizard][s-add], 2026-11-14 |
| Q17 | How does a finite video map onto dashboard time: played once, looped, sped up? | The movement graph is meant to show movement throughout the day, and the dashboard should look real-time. | TBD | [brief § Product][b-product] (s. 3), [§ Inputs][b-inputs] (s. 25–28), 2026-11-14 |
| Q18 | Lizards only, or other reptiles too? | Research, statuses, and motion tracking depend on the animal. | The brief says "reptiles" once and "lizard" everywhere else. | [brief § Product][b-product] (s. 2), 2026-11-14 |
| Q19 | What are "previous data" in the add-lizard form and "AI questions" on the dashboard? | Both are UI elements that no source describes. | TBD | [brief § Web app][b-web] (s. 21); [UI board § Dashboard][u-dash], [§ Add lizard form][u-form], 2026-11-14 |

## Answered

| ID | Answer | Source |
|---|---|---|
| Q1 | It tracks the user's reptiles (a lizard in every example; scope: Q18), for the person who keeps them. On a dashboard it reports status and alerts, and per lizard a video, stats, and a movement graph. | [`overview.md`](overview.md); [brief § Product][b-product], [§ Web app][b-web] |
| Q3 | Recorded, finite video files and finite sensor time series. No live cameras or sensors. | [D3](decisions.md); [brief § Inputs][b-inputs] |
| Q4 | Frame differencing to detect motion, with a Kalman filter or a Bayes filter to track position; a YOLO detector only if necessary. Each has a page in [`approaches/`](approaches/). Which pipeline we build is Q8. | [brief § Motion tracking][b-motion] |
| Q5 | A single computer, serving a local website. | [brief § Product][b-product] |

[b-product]: notes/2026-11-14-project-brief.md#product
[b-ai]: notes/2026-11-14-project-brief.md#research-and-image-analysis
[b-stats]: notes/2026-11-14-project-brief.md#statistics
[b-web]: notes/2026-11-14-project-brief.md#web-app
[b-inputs]: notes/2026-11-14-project-brief.md#inputs
[b-motion]: notes/2026-11-14-project-brief.md#motion-tracking
[s-add]: notes/2026-11-14-whiteboard-system-design.md#add-lizard-middle-left
[s-high]: notes/2026-11-14-whiteboard-system-design.md#high-level-bottom-left
[s-video]: notes/2026-11-14-whiteboard-system-design.md#video-processing-bottom-centre
[s-dd]: notes/2026-11-14-whiteboard-system-design.md#design-decisions-bottom-right
[u-dash]: notes/2026-11-14-whiteboard-ui.md#dashboard
[u-form]: notes/2026-11-14-whiteboard-ui.md#add-lizard-form
