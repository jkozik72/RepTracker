---
source: docs/sources/2026-11-15-zookeeper-advice.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [Q12, Q13, Q14, Q15, Q18]
---

# Zookeeper advice, filtered against the repo

## Summary

A report a team member got from an AI "zookeeper" agent, filtered against `main` at commit `354b76a`: which reptile-care data points RepTracker can capture now, which need a keeper to enter them, and which a camera cannot give. It proposes six additions, a species reference table for five lizards, alert rules, and two ready-made species files. Section 8 was added on 2026-11-15, in a Claude Code chat with the same team member, to fit the advice to the unmerged `src/species-profiles` branch. No date is printed in the source; 2026-11-15 is the day it was saved.

## Key points

- (§1.1) Both species files, `src/website/research/leopardgecko.json` and `skink.json`, are empty on `main`, although `prompts/context-chunk.txt` puts their content into every analysis.
- (§2) Six proposals: fill the two species files; keeper-entered fields on the edit form (scale weight in g, last fed, basking spot check, UVB bulb date, brumation); a bar with the share of time in the hot, middle and cool third plus the share of images where the animal is not visible; hot-minus-cold gradient and humidity spikes in the sensor summary; one-click question buttons; a rolling summary of earlier analyses in "Previous analysis".
- (§3) Ten priorities from the zookeeper, each marked as realizable now, by keeper entry, or only in part. Rank 3: the camera's "Weight" answer is a body-condition estimate, not a weight; real weight comes from a scale.
- (§4.1) Derived from data the app already saves: zone time budget, visibility in % of images, distance moved along the enclosure width.
- (§4.3) Excluded from camera or sensor automation: weight in grams; whether UVB output is adequate; events shorter than the spacing between images (feeding strikes, drinking); tremors, limps and breathing sounds; fine detail such as retained shed on toes; humidity inside a hide; water chemistry for aquatic animals.
- (§5) Reference ranges for leopard gecko and northern blue-tongued skink (in the repo now) and for bearded dragon, crested gecko and veiled chameleon: air temperature by side and at night, overheating thresholds, humidity, UV index, enclosure size, body-condition landmarks, and normal versus alarming behaviour. Each figure cites an outside page (RSPCA, ReptiFiles, Merck, LafeberVet and others).
- (§6) Eight alert rules, for example overheating or under-heating for 30 min or more, and a collapsed gradient.
- (§7) Two JSON payloads meant to be pasted into the two empty species files.
- (§8.1) "Food in bowl" is a lasting state, so one image per interval is enough. "Eating seen: not eating" and "Droppings seen: none seen" on the species branch only mean "not caught in these images"; the source says to reword the first, never alert on either, and keep keeper-entered dates as the record.
- (§8.2) The hot-side and cool-side air checks should run only for profiles with `animalType: "lizard"`. Other animals keep their readings on screen with no alerts. Each animal is checked against its own profile only. The section lists the places on the species branch that would change.

## Relevance

Candidate answers for several open questions: statistics to compute (Q13: zone time, visibility, distance moved), the report's fields (Q12: body condition instead of weight), species reference content (Q14), which sensors (Q15: a basking surface reading), and scope (Q18: the source keeps the air-sensor checks to lizards). None of it is decided or built.

The source was written against `main` and predates `src/species-profiles`, which replaces the two species files with AI-written profiles, renames "Weight" to "Body condition", and opens the app to any reptile or amphibian. §7 does not fit that branch; §8 is the bridge.

## Open questions

- The care figures have not been checked by us against the pages the source cites. Do they hold?
- The source disagrees with itself in places: the minimum gradient is 3 °C in §2 and 4 °C in §6 and §7; leopard gecko humidity is 30 to 40 % RH with 20 to 30 % given beside it (§5). Which values do we use?
- Which of the six proposals in §2 does the team want, and in what order?
- §8.2 leaves out snakes and tortoises, although a warm-to-cool gradient applies to them, because nothing in the source covers them. Should they be included, and on whose figures?
- Many links in §1 to §4 are wrapped in a Google search address and do not open directly.

## Actions

- [ ] Decide which §2 proposals to build
- [ ] Check the §5 figures against their cited pages before any alert uses them
- [ ] Do not paste the §7 files while `src/species-profiles` is unmerged (it deletes both); use §5 and §7 to review the AI-written profiles instead
- [ ] Raise §8.1 and §8.2 with whoever owns `src/species-profiles`
