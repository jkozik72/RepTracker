---
source: docs/sources/2026-11-14-hack-the-nest-research-report.md
type: internal
date: 2026-11-14        # research done 2026-11-14, about 21:00–21:35 UTC, while the event was running
digested: 2026-11-14
relates-to: [hackathon, Q6, Q7]
---

# Hack The Nest 2026: research report on tracks, prizes, and opportunities

## Summary

A research report written by a Claude reader agent that was told nothing about our project. It read the official site (hackthenest.tech), the Major League Hacking (MLH) event pages, and the organizer's Google Developer Group pages, and lists every track, prize, sponsor challenge, and participant opportunity, with a URL for each fact. Its section 5 is the agent's own analysis of how an arbitrary project could qualify for each track; everything else is quoted or paraphrased from the pages. News and social sites were blocked, so facts from those are search summaries and marked unverified in the report.

## Key points

- (§0) The event is Hack The Nest 2026 at Eastern Michigan University, Ypsilanti, MI, the first edition. An unrelated high-school hackathon uses the same name (hackthenest.org); none of its rules apply.
- (§1) Nov 14–15, 2026, in person, 24 h build time, teams of up to 4, free, open to college and high school students. Organized by Google Developer Group on Campus at EMU; an MLH Member Event.
- (§1) Sources disagree on the Sunday end time: 4:00 PM EST (MLH page) or 5:00 PM EST (GDG page).
- (§1) MLH terms reproduced on the site: all work must be done in the event window; code must be public and stay public to be eligible for prizes; AI coding tools are allowed and should be listed in the submission; the team must be present at judging.
- (§1) Not published: submission platform, submission deadline, what must be submitted, and the judging process and criteria for the organizers' own tracks.
- (§2) Six "street" tracks: Hack The Nest (overall), Future of Intelligence (OpenAI, Exa), Mind and Machine (g.tec, PiEEG), Future of Money (Breez), Best Beginner, Capture the Flag.
- (§3) Seven "train" tracks: Beyond the Horizon (Michigan Space Grant Consortium, NASA open data), Quantum Computing (Quantum Rings), Best Use of Base44, Best Use of SSOJet, Code of Life (Seqera), Department of Computer Science Track, Best Use of ElevenLabs. Plus eight MLH categories (§3.8).
- (§3.9) No people's choice, design, hardware, or social-good prize is listed. IBM and Kawasaki Robotics are sponsors without a track of their own.
- (§4) Free credits and tools for every hacker (Exa, Quantum Rings, SSOJet, ElevenLabs, and several through MLH), EEG hardware on site, workshops, mentors, an optional resume book.
- (§5, analysis) For each track: what a submission must demonstrate, two or three generic ways to integrate it, a rough estimate of extra work in hours, and common ways teams fail to qualify.
- (§6) Only the Department of Computer Science Track states that it combines with others ("Any idea, any stack, in any track"). MLH allows one application per category. Every other combination, and any cap on tracks per team, is not stated.
- (§7) Unknowns, source disagreements (capacity, start and end times, track count), and the hosts that could not be read.

## Relevance

This is the input for deciding which tracks, if any, the project enters. The facts are organized for that comparison in `docs/hackathon/`. Two rules constrain any project regardless of track: work must happen inside the event window, and the repository must be public.

## Open questions

- Which tracks and categories should the project enter, if any? (Q6 in `docs/open-questions.md`)
- Where and by when are projects submitted, what must a submission contain, and can one project enter several tracks? (Q7)
- Do the organizers apply the MLH standard rules to their own tracks? The site does not say (§1).
- What are the Future of Intelligence prizes ("Coming soon", §2.2), the ten Breez bounties and their qualifying bar (§2.4), and the Base44 community-vote mechanics (§3.3)?

## Actions

- [x] Created `docs/hackathon/` (`README.md`, `tracks.md`, `mlh-categories.md`, `opportunities.md`, `project-fit.md`) from this note
- [x] Added Q6 and Q7 to `docs/open-questions.md`
- [x] Added D2 to `docs/decisions.md`; added `docs/hackathon/` to the layout in `CLAUDE.md` and to `README.md`
- [ ] Fill in `docs/hackathon/project-fit.md` once the project is described (Q6)
- [ ] Get the submission platform, deadline, and track-combining rule from the organizers (Q7)
