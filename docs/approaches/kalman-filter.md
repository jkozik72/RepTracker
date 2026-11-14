# Kalman filter

- **Status:** Candidate
- **Decision:** none yet
- **Open questions:** Q6, Q7, Q8
- **Lives in:** n/a

## What it is

A recursive estimator that tracks a state, here the lizard's position and velocity, from noisy measurements. It assumes a linear motion model and Gaussian noise, which makes it a special case of the [Bayes filter](bayes-filter.md). It produces a smoothed position and a speed for every frame. It does not detect the lizard: it needs positions from a detector such as [frame differencing](frame-differencing.md).

## How it works

1. State: the position and velocity of the lizard in the frame.
2. Predict: move the state forward by one frame interval. Its uncertainty grows.
3. Update: when the detector gives a position, pull the estimate toward it, weighted by the two uncertainties. The uncertainty shrinks.
4. No measurement (lizard not on screen, lizard still, repeated frame): predict only.

## Pros

- Keeps an estimate while measurements are missing. The brief asks for tracking over time because the lizard is sometimes not on screen.
- Speed is part of the state, and speed is one of the wanted statistics.
- Small and cheap: a few matrix operations per frame.

## Cons

- One Gaussian estimate cannot say "either here or gone", so it does not answer lizard present by itself (Q8).
- With predictions only, the estimate keeps moving at the last velocity. A still lizard and an absent lizard look the same to it.
- Its noise parameters have to be tuned to our video.

These follow from how the method works. None has been measured on our video.

## Evidence

Notes and experiments, with what each showed.

- [`docs/notes/2026-11-14-project-brief.md`](../notes/2026-11-14-project-brief.md#motion-tracking) § Motion tracking: names a Kalman filter as one of two options for tracking position (s. 34).
- [`docs/notes/2026-11-14-whiteboard-system-design.md`](../notes/2026-11-14-whiteboard-system-design.md#video-processing-bottom-centre) § Video processing: "Kalman filter" written next to the lizard outline.
- Experiments: none yet.
