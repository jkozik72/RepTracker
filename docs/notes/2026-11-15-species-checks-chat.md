---
source: docs/sources/2026-11-15-species-checks-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [Q12, Q13, Q18, D5, D6]
---

# Stats from species profiles, "add reptile" (chat messages)

## Summary

The dashboard's stats should come from the species profile, because what to track differs by species (turtles do not shed like lizards). The species-specific checks are created with the profile and shown on the Research page. The button should not say "lizard".

## Key points

- (Message 1) Stats made from the profiles.
- (Message 1) Turtles have something other than shedding to track.
- (Message 1) "Add reptile" instead of "add lizard"; asks for an opinion.
- (Message 2) The checks are created during profile creation and displayed on the Research page.

## Relevance

Answers Q18 (D6). Narrows Q12 (statuses and report fields) and Q13 (statistics): a fixed set common to every animal plus per-species checks from the profile.

## Open questions

- "Animal" was chosen over "reptile" because frogs and salamanders are amphibians; the team can change the word (one place in the UI text).

## Actions

- [x] `trackedStats` in `prompts/profile-schema.json`, written in the research call and shown on the Research page
- [x] Each analysis gets an answer format built from the profile (activities, species checks, named conditions); the base format is animal-neutral
- [x] Dashboard stats, alerts and Watch status from the profile; older analyses still show their fields
- [x] "Animal" instead of "lizard" in the UI and prompts; D6; Q18 answered; glossary updated
