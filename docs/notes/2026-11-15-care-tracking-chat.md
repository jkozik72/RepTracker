---
source: docs/sources/2026-11-15-care-tracking-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [Q12, Q13, D5, D6, D7]
---

# Notifications, card sections, feeding, zones, sex, sign-in (chat messages)

## Summary

A list of additions: neutral notifications next to alerts; an expanded card organised into Environment and Movement sections (movement per interval as a bar chart); a feeding log with manual entry in dev mode; time spent on each side and by time of day; the animal's sex and sex-specific profile information; dev-mode sensor data generated from a profile (in bounds, under, over, high variance) with the profile's ranges as dotted lines; and a sign-in page so the site can be served on a LAN.

## Key points

- (Message 1) Notifications that are neither good nor bad: starts shedding, active, anything interesting.
- (Message 1) An Environment section that expands to the humidity (and temperature) readings and graph.
- (Message 1) A Movement section: position graph and movement stats, including total movement per interval as a bar chart with a settable interval.
- (Message 1) In dev mode, with a profile: a feeding record with manual entry, related to time.
- (Message 1) Time spent on each side; time of day (answer: a day/night split and a 24-hour chart).
- (Message 1) Sex ("gender") per animal, and sex-specific information in profiles.
- (Message 1) A sign-in page for LAN hosting: the first sign-in creates the account, everyone after signs in (answer: over self-signed HTTPS).
- (Message 2) In dev mode, on a profile: generate sensor data from it that stays in bounds, goes under, goes over, or varies a lot; show the bounds on the graphs as dotted lines.

## Relevance

Adds statistics (Q13: zone time, movement per interval, by hour, days since fed) and a neutral notification level next to alerts (Q12). The sign-in is D7.

## Open questions

- Day is 7:00 to 19:00 local time for the day/night split; a per-enclosure light schedule would be more accurate.
- The dev server (Werkzeug) serves the LAN; a production WSGI server would be sturdier for long-running use.

## Actions

- [x] Notifications: AI "Notable moments", eating, droppings, changes between analyses, feedings; in the summary bar and per animal
- [x] Card sections: Environment (readings, graphs with dotted profile ranges), Movement (position, time on each side by day and night, movement per interval, by hour of day), Notifications, Feeding
- [x] Feeding log with manual entry (dev mode, with a profile); days since fed and Fed / Due / Overdue from the profile
- [x] Sex per animal; sex notes and conditions in profiles, used in prompts and checks
- [x] Dev-mode sensor generator on the Research page (in bounds, under, over, high variance)
- [x] Sign-in (first visit creates the one account), `--lan` with self-signed HTTPS; D7
