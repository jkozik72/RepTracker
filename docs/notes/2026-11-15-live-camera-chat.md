---
source: docs/sources/2026-11-15-live-camera-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [D3, Q16, Q17, Q21]
---

# Live camera: team message

## Summary

The team wants a Raspberry Pi Camera Module 3 (standard lens, CSI) on a Raspberry Pi 5 (8 GB) to act as a live camera in RepTracker. Two ways were discussed and not decided: a rolling (circular) buffer of video, or image captures at the analysis interval kept in a circular buffer. The demo films a laptop screen playing a reptile video.

## Key points

- Hardware: Raspberry Pi 5, 8 GB RAM; Pi Camera Module 3, standard (not Wide), on CSI.
- Today a camera is an uploaded MP4, often 1, 2 or up to 10 h long.
- Option 1: a rolling video buffer, about 1 h; the oldest footage is erased, and data derived from it is kept. Reason given: "the current architecture expects a video".
- Option 2: one image capture per interval (about once a minute) into a circular buffer: much less data, so a longer history.
- The owner leans to option 1 ("I think that we could create a long video and it's not going to be a problem"). Lowering the frame rate was mentioned.
- Demo: the camera records a laptop screen showing a reptile video, to show RepTracker working on live capture and as a product.

## Relevance

Partly reverses D3 (recorded files, not live cameras) for cameras. Sensors stay simulated.

## Open questions

- Which capture design, and how long to keep frames: Q21.

## Actions

- [x] Added Q21 to `docs/open-questions.md`
- [x] Built the live camera as a frame store (`src/website/camera.py`), branch `src/live-camera`; documented in `docs/functions.md` and `src/pi/README.md`
- [ ] Owner to answer Q21; then add D9 (Replaces: D3, for cameras only) and update `overview.md` and `architecture.md`
- [ ] Measure frame size (kB) and CPU load on the Pi; until then both are TBD
