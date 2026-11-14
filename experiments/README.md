# Experiments

Quick spikes that answer one question: does approach X work on our input, how fast is library Y, what happens at the edges. Code here doesn't need to be clean or complete. Results feed approach pages and decisions.

## Layout

One flat folder per experiment, named `<topic>-<what-it-tests>` (e.g. `pose-model-fps`, `optical-flow-occlusion`). Inside: `README.md` (required) plus whatever it needs: `code/`, small `samples/`, `results/`. Large inputs go in `data/` and outputs in `out/`, both git-ignored; link them instead.

## README template

```markdown
# <Experiment name>

- **Status:** Planned | In progress | Done
- **Approach / question:** docs/approaches/<name>.md, or Q<n> in docs/open-questions.md
- **Question:** what this experiment is meant to find out
- **Setup:** what was run, on what data and hardware, and how to reproduce it
- **Result:** what happened, with numbers, plots, or screenshots
- **Conclusion:** what this means for the approach or decision
- **Became:** (if it turned into real code) where it lives in src/
```

## Rules

- **Self-contained:** someone can rerun it from the README alone.
- **Done means documented:** Done requires a Result and a Conclusion.
- **Iterate in place:** a new version updates the same folder; a fundamentally different idea gets a new one.
- **Never delete:** dropped ideas stay, because their results justify the decision.
- Branches: `exp/<short-name>`.

Once an approach is chosen, the real implementation goes in `src/`, not here.
