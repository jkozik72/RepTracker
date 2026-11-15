# YOLO detector

- **Status:** Candidate
- **Decision:** none yet
- **Open questions:** Q8
- **Lives in:** n/a

## What it is

A trained object-detection model that looks at a single frame and returns bounding boxes for the objects it recognizes. YOLO is the model family named in the brief. The position of the lizard would be the centre of its box. The brief does not want this unless it is necessary, so it is the fallback if [frame differencing](frame-differencing.md) with a position filter is not enough.

## How it works

1. Run the model on a frame. It returns boxes, each with a class and a confidence.
2. Take the lizard's box as the measured position. No box means not detected.
3. Optionally smooth the positions with a [Kalman filter](kalman-filter.md) or a [Bayes filter](bayes-filter.md).

## Pros

- Works on a single frame, so a still lizard and repeated frames are not a problem.
- Gives lizard present directly: a box or no box.

## Cons

- A model to obtain, possibly to train on lizard images, and to run on every analyzed frame. This is the cost the brief wants to avoid.
- Whether an existing model detects lizards in enclosures well enough is unknown.

These follow from how the method works. None has been measured on our video.

## Evidence

Notes and experiments, with what each showed.

- [`docs/notes/2026-11-14-project-brief.md`](../notes/2026-11-14-project-brief.md#motion-tracking) § Motion tracking: "I don't want to do a whole like YOLO model if it's not necessary" (s. 32).
- Experiments: none yet.
