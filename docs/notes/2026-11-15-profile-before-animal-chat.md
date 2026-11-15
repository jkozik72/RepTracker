---
source: docs/sources/2026-11-15-profile-before-animal-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [D5, D6]
---

# Create the profile before the animal (chat message)

## Summary

Adding an animal whose species has no profile should create the profile first, then the animal's card.

## Key points

- (Message) No profile for the species: create the profile, then make the board (the animal's card).

## Relevance

The card's stats and checks come from the profile (D6), so it should exist before the first analysis.

## Open questions

None.

## Actions

- [x] The add/edit form researches a species with no profile before saving the animal; on failure nothing is added and "Add without a profile" is offered
