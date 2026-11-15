# Bayes filter

- **Status:** Candidate
- **Decision:** none yet
- **Open questions:** Q8, Q9, Q10
- **Lives in:** n/a

## What it is

The general recursive estimator: it keeps a probability distribution (a belief) over where the lizard is, and updates it every frame with a motion model and a measurement model. The [Kalman filter](kalman-filter.md) is the special case with a linear model and Gaussian noise. As a separate candidate it means a form without those assumptions, such as a histogram filter over a grid of cells, or a particle filter. Which form the team has in mind is not written down. Like the Kalman filter it needs measurements from a detector such as [frame differencing](frame-differencing.md).

## How it works

1. Belief: a probability for each possible state. For example each cell of a grid over the frame, plus one state for "not on screen".
2. Predict: spread the belief according to how far the lizard can move in one frame interval.
3. Update: weight each state by how well it explains the new measurement, then normalize.
4. Report the most probable state as the position. The probability of "not on screen" can serve as lizard present.

## Pros

- Holds several hypotheses at once, including "not on screen", so lizard present (Q10) can come out of the filter.
- No linear or Gaussian assumption.

## Cons

- More computation and more to design than a Kalman filter: the grid or the number of particles, the motion model, the measurement model.
- In the histogram form, the position is only as fine as the grid.

These follow from how the method works. None has been measured on our video.

## Evidence

Notes and experiments, with what each showed.

- [`docs/notes/2026-11-14-project-brief.md`](../notes/2026-11-14-project-brief.md#motion-tracking) § Motion tracking: names a Bayes filter as the alternative to a Kalman filter for tracking position (s. 34).
- [`docs/notes/2026-11-14-whiteboard-system-design.md`](../notes/2026-11-14-whiteboard-system-design.md#video-processing-bottom-centre) § Video processing: "Bayes" written under "Kalman filter".
- Experiments: none yet.
