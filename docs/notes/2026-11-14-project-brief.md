---
source: docs/sources/2026-11-14-project-brief.md
type: internal
date: 2026-11-14        # the day the message was sent
digested: 2026-11-14
relates-to: [Q1, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, D2, approaches/frame-differencing, approaches/kalman-filter, approaches/bayes-filter, approaches/yolo-detector]
---

# Project brief: what RepTracker is (chat message, 2026-11-14)

## Summary

A team member's description of the whole project, sent to Claude Code as one chat message. RepTracker is a dashboard, hosted on a single computer as a local website, for tracking the user's reptiles: per lizard it shows a video, a movement graph, statistics, and a status produced by an AI model. An LLM researches the species, and an AI model (a VLM or something else, not yet known) analyzes frames at a poll rate. Video and sensor data are recorded, finite files, not live hardware. Motion tracking is the part still to be figured out: the idea is the derivative between frames plus a Kalman or Bayes filter, without a YOLO model unless one is necessary. Two whiteboard photos came with the message and have their own notes: [system design](2026-11-14-whiteboard-system-design.md) and [UI](2026-11-14-whiteboard-ui.md).

## Key points

`(s. N)` is the numbered sentence in the source.

### Product

- (s. 1) The project is called "Rep Tracker". It is hosted on a single computer, as a local website.
- (s. 2) Purpose: a dashboard that can "track your reptiles".
- (s. 3) Wanted per animal: a video, and a movement graph showing how much movement there was throughout the day, to track its cycles.
- (s. 4) Health is read from the movement graph.

### Research and image analysis

- (s. 5) An LLM does research. A VLM analyzes images.
- (s. 6) The input to research is the species. The LLM researches, preferably with structured output, and creates structured information from the research.
- (s. 7–8) Not committed ("perhaps", "might"): research collects images of the species, diseased and healthy, and compiles the information into a folder.
- (s. 8–9) At a poll rate, when the lizard is detected as present, an image is sent to an AI. Which model, and whether it has to be a VLM, is not known yet.
- (s. 10–11) Perhaps the AI first works out whether the lizard is in the frame: if it is, it does its analysis; if not, it says so.
- (s. 12–14) The analysis creates a structured report that gives a status of the lizard. The set of statuses is finite. Examples: shedding, overweight.
- (s. 39) Preference: one AI API call per poll.

### Statistics

- (s. 15–17) Statistics are wanted. Examples: when the lizard last shed, and how long it took. The full list is not given.
- (s. 37) Statistics from the processed video: position, speed, and maybe lizard present.
- (s. 38) Lizard present may come from the VLM or LLM analyzing an image from the video.

### Web app

- (s. 18) The dashboard has status and alerts at the very top.
- (s. 19–20) It has sections where a lizard can be added. A lizard is displayed with its name, video, stats, and movement graph.
- (s. 21) Adding a lizard means filling out a form: name, age, species, and maybe previous data.

### Inputs

- (s. 22) No real cameras and no real sensors.
- (s. 23) Video: one video the team takes of a real lizard, plus videos found online of other lizards in their enclosures.
- (s. 24) Sensors: a finite time series.
- (s. 25–26) The web app pulls from the indexes of the video: a frame, and the sensor values.
- (s. 27–28) On the dashboard the video and the movement graph look real-time, but every video is fully recorded and finite.
- (s. 29) Reason given: this simplifies real-time processing.

### Motion tracking

- (s. 30) Motion tracking still has to be figured out.
- (s. 31) Input: a video. Output: a position of the lizard.
- (s. 32) A YOLO model is not wanted if it is not necessary.
- (s. 33) Idea: take the derivative between frames to detect motion, then track the lizard's motion over time, because the lizard is sometimes not on screen.
- (s. 34) For tracking position: a Kalman filter or a Bayes filter.
- (s. 35–36) Frames may stay the same because of how the video is produced. Then the derivative is zero, which causes problems for detecting where the lizard is. This has to be accounted for.

### The whiteboard photos

- (s. 40–41) The photos show the same content as the message.

## Relevance

This is the first statement of what RepTracker is. It answers Q1 (what it tracks, for whom, what it reports), Q3 (the input), and Q5 (where it runs), and it names the approaches to document first (Q4): frame differencing, a Kalman filter, a Bayes filter, with a YOLO model only as a fallback. It states one design choice together with its reason: recorded files instead of live cameras and sensors (s. 22–29). It says nothing about language or tooling (Q2).

## Open questions

All are in `docs/open-questions.md` under the ID shown.

- Is a YOLO model necessary, or are frame derivatives plus a Kalman or Bayes filter enough? (s. 32–34) → Q6
- How are repeated frames detected and handled? (s. 35–36) → Q7
- Where does "lizard present" come from: motion tracking, the VLM or LLM, or both (s. 8, 37–38)? It decides when to poll, and the preference is one AI call per poll (s. 39). And what is the poll rate (s. 8–9)? → Q8
- Which AI model analyzes the images, and does it have to be a VLM? (s. 8) → Q9
- What is the finite set of statuses, and what is in the structured report? (s. 12–14) → Q10
- Which statistics, beyond the examples? (s. 15–17, 37) → Q11
- Does research collect images, and what goes in the folder? (s. 7–8) → Q12
- Which sensors does the time series hold? (s. 24) → Q13
- Which videos, and in what form? (s. 23) → Q14
- The movement graph covers a day (s. 3) and the dashboard looks real-time (s. 27), but the videos are finite (s. 27–28): how does a video map onto dashboard time? → Q15
- "Reptiles" (s. 2) but "lizard" everywhere else: lizards only, or other reptiles too? → Q16
- What is the "previous data" in the add-lizard form? (s. 21) → Q17

## Actions

- [x] Rewrote `docs/overview.md`, and the description and Status in `README.md`: what we're building, nine requirements, scope, constraints
- [x] Rewrote `docs/architecture.md`: block diagram and six components
- [x] Added `docs/approaches/frame-differencing.md`, `kalman-filter.md`, `bayes-filter.md`, `yolo-detector.md`, all Candidate, with this note under Evidence
- [x] Logged D2 in `docs/decisions.md`: recorded files instead of live cameras and sensors (s. 22–29)
- [x] `docs/open-questions.md`: answered Q1, Q3, Q4, Q5; added Q6–Q17
- [x] Added the domain terms to the glossary in `docs/functions.md`
- [ ] Experiment: locate the lizard with frame differencing on a sample video, including repeated frames (Q6, Q7)
- [ ] Experiment: Kalman filter against Bayes filter for tracking position while the lizard is not on screen (Q6)
