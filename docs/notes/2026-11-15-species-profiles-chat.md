---
source: docs/sources/2026-11-15-species-profiles-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [Q12, Q13, Q14, Q18, D5]
---

# Species profiles and a generic animal tracker (chat messages)

## Summary

The team wants RepTracker to work for any reptile or amphibian, with the species typed in plain English. An AI researches the species once (the stats to track, diseases and problems) and the result is stored and reused by later analyses. New stats are wanted: hunger with days since last fed, droppings, sex, and time in the hot and cold zones. Work starts with species profiles on a new Research tab, with data and images.

## Key points

- (Message 1) Work with any reptile, for example lizards, turtles and frogs (frogs are amphibians).
- (Message 1) New stats: hunger status with days since last fed, poop, sex, time spent in the hot and cold zones.
- (Message 1) Type the species in plain English instead of choosing from a list.
- (Message 1) An AI creates the stats and the diseases and problems for the species; this is stored and used in future polled analyses for more accurate results.
- (Message 2) Start with species profiles, on a new Research tab that shows the profile's data and images.
- (Message 2) Commit the current work to main and do this on a branch.

## Relevance

Answers Q14 (what research produces, where it is stored, whether the UI shows it): recorded as D5. Feeds Q12 and Q13 (statuses and statistics) and Q18 (other reptiles), which stay open for the later steps.

## Open questions

- Q18 (animals beyond lizards) needs its own decision, with the glossary change from "lizard" to a general term.
- Hunger, droppings, sex and zone time: which come from the AI and which from the keeper or the app (proposed: a "Fed" log, keeper-set sex, zone time computed from positions).

## Actions

- [x] Research tab: create, list, inspect (data, conditions, photos), edit, regenerate and delete species profiles
- [x] `prompts/research.txt` and `prompts/profile-schema.json`; profiles in `src/website/research/<slug>/profile.json`
- [x] Species typed in plain English in the add/edit form, matched to a profile
- [x] Profiles in the CONTEXT chunk of every analysis, and sensor alerts from the profile's ranges
- [x] D5; Q14 answered
- [ ] Sex, a "Fed" log and hunger status
- [ ] Per-species answer format: activities, droppings, eating, named conditions
- [ ] Time in hot and cold zones
- [ ] Q18 decision and the rename from "lizard"
