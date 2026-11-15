# Decisions

Append-only log, oldest first. One entry per decision we would otherwise re-argue: approach, library, naming, how the repo works. Never edit or delete an entry; to reverse one, add a new entry that says what it replaces. The entry is the whole process: if options need comparing, compare them here (or in an `open-questions.md` row while undecided).

Entry format:

```markdown
## D<n> (YYYY-MM-DD): <title>
- **Context:** why we had to choose
- **Options:** A ..., B ..., C ... (one line each: what it would mean)
- **Chose:** X, because ...
- **Consequences:** what changes, what we give up, what to watch
- **Sources:** docs/notes/..., experiments/..., docs/approaches/...
- **Replaces:** D<m>, or none
```

---

## D1 (2026-11-14): Organize the repo as a sources → notes → docs knowledge base
- **Context:** The project needs one place for research, design decisions, a function reference, and approach documentation that stays trustworthy while the code moves fast.
- **Options:** A: a free-form `docs/` folder. B: the full HydroScout system (sources/notes/project, trade studies, requirement IDs, two open-question registers). C: HydroScout's pipeline and rules without trade studies and ID schemes.
- **Chose:** C. The pipeline (raw sources, one note per source, synthesized docs that cite notes), the append-only log, and the `TBD` rule are what keep facts traceable; trade studies and requirement IDs were the overhead for a small team.
- **Consequences:** Every fact in `docs/` traces to a note or is `TBD`. A design choice is one entry here, not a document. Approaches and functions each have one place. `/digest` files sources; `/tasks` finds what is open. Nothing checks this automatically; review does.
- **Sources:** The HydroScout repository (`CLAUDE.md`, `docs/notes/_template.md`, `docs/project/decisions.md`, `prototypes/README.md`, `.claude/skills/digest/SKILL.md`) as the model.
- **Replaces:** none

## D2 (2026-11-14): Keep Hack The Nest material in its own folder, `docs/hackathon/`
- **Context:** The team asked for the Hack The Nest (Nov 14–15, 2026) tracks and opportunities to be written down before the project is described, so the two can be compared later without bias.
- **Options:** A: fold the tracks into `overview.md`. B: keep only the note in `docs/notes/`. C: a separate `docs/hackathon/` folder built from the note, with an empty comparison page.
- **Chose:** C, because the facts are about the event, not the project, and a separate folder with `project-fit.md` keeps the comparison explicit.
- **Consequences:** `docs/hackathon/` follows the same editing rules as the other synthesized docs. Its analysis blocks are labelled as not official. Which tracks to enter stays open (Q6).
- **Sources:** docs/notes/2026-11-14-hack-the-nest-research-report.md

## D3 (2026-11-14): Recorded video and sensor files instead of live cameras and sensors
- **Context:** The dashboard should look live: a video and a movement graph that update as if in real time. With real hardware that means real cameras, real sensors, and real-time processing. The team made this choice at the whiteboard; this entry logs it, and its date is the day it was logged.
- **Options:** A: real cameras and sensors, streamed and processed in real time. B: recorded, finite files, processed ahead of time: one video the team takes of a real lizard, videos found online of other lizards in their enclosures, and finite sensor time series. The web app reads them by index, so the dashboard looks live.
- **Chose:** B, because it simplifies real-time processing (brief) and nothing requires real-time polling (board: "files not streams").
- **Consequences:** Inputs are files, not streams. Video is preprocessed: raw video in, processed video and statistics out, and the backend polls those. No hardware integration. We give up showing the system on live hardware: "real time" on the dashboard is a playback of recorded data. How the playback maps onto time is open (Q17).
- **Sources:** `docs/notes/2026-11-14-project-brief.md` § Inputs (s. 22–29); `docs/notes/2026-11-14-whiteboard-system-design.md` § Design decisions.
- **Replaces:** none

## D4 (2026-11-15): Use the Claude API as the AI provider
- **Context:** The dashboard sends each lizard's prompt chunk (PDFs of camera images plus a context chunk) to an AI and asks questions about it. Q11 left the provider open; Gemini through Vertex AI was being tried.
- **Options:** A: Gemini through Vertex AI (Google Cloud login, no key). B: the Claude API (Anthropic API key). C: keep only the offline Mock.
- **Chose:** B, the team's choice ("Now we are using claude API"). Default model `claude-opus-5-5`; replies are constrained to `prompts/response-schema.json` with structured outputs.
- **Consequences:** The API key is entered in Settings (dev mode) and kept on the computer that runs the app (`src/website/data/claude-key.json`, git-ignored), or read from `ANTHROPIC_API_KEY`. Gemini and the Mock stay selectable in Settings; the Mock remains the default until a key is saved and Claude is selected. Requests cost money per call.
- **Sources:** `docs/notes/2026-11-15-claude-provider-chat.md`
- **Replaces:** none

## D5 (2026-11-15): AI-written species profiles, stored and reused, with the species typed in plain English
- **Context:** Analyses need to know what is normal for a species (temperatures, humidity, feeding, shedding, common diseases and their signs) to judge an animal well. The species was picked from a fixed list of two with no stored knowledge; Q14 left research open.
- **Options:** A: a fixed species list with hand-written care data. B: ask the AI about the species in every analysis. C: one AI call per species writes a structured profile, stored, shown to the keeper, editable, and reused by every analysis and for sensor alerts.
- **Chose:** C. The keeper types the species in plain English on the Research tab; the AI provider in use fills `prompts/profile-schema.json` once; the profile is saved in `src/website/research/<slug>/profile.json` (committed) with reference photos from Wikimedia Commons (git-ignored, with author and licence). It goes into the CONTEXT chunk of every analysis, and the dashboard compares live sensor readings with its ranges.
- **Consequences:** Any species can be typed; one research call per species instead of extra tokens in every analysis. Alerts depend on AI-written ranges, so the Research tab marks a profile "not checked yet" until a keeper edits it, and shows the AI's own confidence note. Research works with Claude and the Mock; Gemini is not supported for research yet.
- **Sources:** `docs/notes/2026-11-15-species-profiles-chat.md`; `docs/notes/2026-11-14-project-brief.md` § Research and image analysis
- **Replaces:** none

## D6 (2026-11-15): Any reptile or amphibian, called "animal"; what to track comes from the species profile
- **Context:** RepTracker was built for lizards: a fixed answer format (weight, shed, food bowl, basking/exploring/hiding) and "lizard" in the UI. Keepers want it for any reptile, and frogs; what to check differs by species (turtles do not shed like lizards). Q18 asked whether other reptiles are in scope.
- **Options:** A: lizards only. B: any reptile, called "reptile", with one answer format. C: any reptile or amphibian, called "animal", with common stats for every animal plus checks defined per species in its profile (D5).
- **Chose:** C. Every analysis asks for: visible, activity (the species' own list), body condition, eating, droppings, food dish, hazards, conditions seen (the species' named conditions), position; plus 1 to 4 species checks ("trackedStats") that the AI writes into the profile at research time, each with its answers and which answers are a concern. "Animal" because frogs and salamanders are amphibians.
- **Consequences:** `prompts/response-schema.json` is the animal-neutral base; each bundle gets its own copy built from the profile. The dashboard shows whatever the analysis holds, with alerts for concern answers and named conditions, and Watch for in-between answers. Profiles made before this change have no checks until regenerated. Code names (`lizards`, `/lizards` routes, `data/<mode>/reptiles/`) stay as they are.
- **Sources:** `docs/notes/2026-11-15-species-checks-chat.md`; `docs/notes/2026-11-15-species-profiles-chat.md`
- **Replaces:** none

## D7 (2026-11-15): One sign-in account, and HTTPS with a self-signed certificate on the LAN
- **Context:** The team wants to open RepTracker from other devices on the local network without it being easy to break into: the API key, the animals' data and the camera videos are behind it.
- **Options:** A: no sign-in, local only. B: a sign-in over plain HTTP. C: a sign-in, and HTTPS with a self-signed certificate when served on the LAN. D: user accounts with roles.
- **Chose:** C. The first visit creates the only account (username, password of 10+ characters, stored as a salted scrypt hash); after that every page, API call, video and photo needs a signed session cookie (HttpOnly, SameSite=Strict, Secure on HTTPS) tied to the account's id. Repeated wrong passwords lock that address out, doubling from 30 s to 15 min. `python app.py --lan` serves 0.0.0.0 over HTTPS with a certificate made once for this computer's names and addresses, with Flask's debug mode off.
- **Consequences:** Browsers warn once about the self-signed certificate. There is no password reset: deleting `src/website/data/auth.json` removes the account and signs everyone out, and the next visit creates a new one. Without `--lan`, the app still listens on 127.0.0.1 only, with debug on, and still needs the sign-in.
- **Sources:** `docs/notes/2026-11-15-care-tracking-chat.md`
- **Replaces:** none

