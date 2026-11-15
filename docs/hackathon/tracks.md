# Organizer tracks

The 13 tracks on the official site. Each has the official facts first (§2 and §3 of the [report](../sources/2026-11-14-hack-the-nest-research-report.md), quotes verbatim from the site), then an **analysis** block (§5): the reader agent's own neutral view of how an arbitrary project could qualify. The analysis is not official, the hours are rough estimates for a team of 2 to 4 with no prior setup, and statements about sponsor products should be checked against the sponsor's docs. No track is ranked or recommended. For the MLH categories see [mlh-categories.md](mlh-categories.md).

| Track | Sponsor | Kind | Prize (1st) |
|---|---|---|---|
| [Hack The Nest](#hack-the-nest-overall) | none | overall | PlayStation 5 each |
| [Future of Intelligence](#future-of-intelligence) | OpenAI, Exa | theme | coming soon |
| [Mind and Machine](#mind-and-machine) | g.tec, PiEEG | theme | g.tec Unicorn Hybrid Black headset (one per team) |
| [Future of Money](#future-of-money) | Breez | theme, bounties | a bounty for every qualifying entry |
| [Best Beginner](#best-beginner) | none | team eligibility | Logitech MX Master 4 mouse each |
| [Capture the Flag](#capture-the-flag) | none | side competition | Flipper Zero each |
| [Beyond the Horizon](#beyond-the-horizon) | Michigan Space Grant Consortium, NASA open data | theme | Celestron Travel Scope 60 telescope each |
| [Quantum Computing](#quantum-computing) | Quantum Rings | theme | internship interview, compute credits, headset each |
| [Best Use of Base44](#best-use-of-base44) | Base44 | tool | Ray-Ban Meta glasses + Builder plan each |
| [Best Use of SSOJet](#best-use-of-ssojet) | SSOJet | tool | SSOJet business licenses for the team |
| [Code of Life](#code-of-life) | Seqera | theme | $250 credits, platform access, up to 8 h mentoring |
| [Department of Computer Science Track](#department-of-computer-science-track) | EMU Computer Science | engineering quality | $1,000 scholarship ($250 per member) |
| [Best Use of ElevenLabs](#best-use-of-elevenlabs) | ElevenLabs | tool | Scale plan for 3 months each |

## Hack The Nest (overall)

- **Official description:** none; the panel lists only prizes. (§2.1)
- **Prizes:** 1st PlayStation 5 each; 2nd Nintendo Switch each; 3rd monitors each.
- **Requirements, judging, combining:** not stated.

Analysis (not official):
- **Must show:** presumably a registered team's project, built in the event window and demonstrated to judges.
- **Ways in:** one core flow that works end to end in a live demo; a public repository whose history shows the work was done during the event; an honest list of libraries and AI tools used.
- **Extra work:** 0.5–1 h of submission paperwork.
- **Common failures:** no working demo; work done before the window; nobody present at judging; private repository; missing the unpublished deadline.

## Future of Intelligence

- **Sponsor:** "Led by OpenAI, with Exa". (§2.2)
- **Official description:** "The next wave of software will not just answer questions; it will think, search and act on its own." "Build on OpenAI's models and Exa's search engine made for AI, so your project can reason over the live web". "Build the agent, app or tool you wish already existed, and polish it like a real product".
- **Prizes:** "Coming soon".
- **Given to every hacker:** "$50 in Exa API credits".
- **Requirements:** none beyond the description. Whether both OpenAI and Exa must be used is not stated.

Analysis (not official):
- **Must show:** software built on OpenAI models and Exa search that reasons over the live web and is presented like a product.
- **Ways in:** a feature where a model answers or decides using documents fetched live through Exa, with sources shown; an agent loop where the model calls Exa as a tool and then acts on the app's own data; a background job that looks up the app's entities on the web and summarizes them.
- **Extra work:** 2–5 h for a search-plus-model feature; 5–10 h for a polished multi-step agent. Needs an OpenAI API key (credits not stated) and an Exa key.
- **Common failures:** a chat box with no role in the product; only another model provider used; no live-web component; rate limits or spent keys during the demo.

## Mind and Machine

- **Sponsor:** "Led by g.tec, with PiEEG". (§2.3)
- **Official description:** "The singularity will not wire itself: someone has to connect the mind to the machine." "Three optional directions, Video Games, Assistive Technology and Data Science, or your own idea".
- **Provided:** "g.tec Unicorn EEG hardware at the event, set up and tested by g.tec's own team"; "Seven real brain-signal datasets from g.tec"; a 60-minute g.tec workshop (Saturday, 2 PM); PiEEG "16-channel Octopus EEG boards, simulated brain-signal streams on PiEEG Cloud, and a live online workshop".
- **Prizes:** 1st g.tec Unicorn Hybrid Black headset (one for the team); 2nd two PiEEG Octopus 16 boards; 3rd Logitech MX Keys S keyboard each.
- **Requirements, judging:** not stated beyond the above.

Analysis (not official):
- **Must show:** a project whose function depends on brain-signal data, from the on-site headset, the provided datasets, PiEEG boards, or the simulated streams.
- **Ways in:** use a value derived from a dataset or live headset (for example a classifier output) as an input or control channel for a feature; an offline analysis or machine-learning pipeline over one provided dataset with a visual front end; develop against the simulated stream, then switch to hardware for the demo.
- **Extra work:** 4–8 h dataset-only; 6–12 h or more with live hardware. Needs time at the g.tec booth, shared hardware, and a signal-processing stack.
- **Common failures:** the brain signal is decorative; live demo fails on a noisy signal with no recorded fallback; hardware queue; unsupported medical claims.

## Future of Money

- **Sponsor:** "Led by Breez". (§2.4)
- **Official description:** "Money should cross the world as easily as a text message, and in most apps it still does not." "Ten bounties, each one an everyday situation where money is slow or stuck".
- **Requirements (stated):** "Build a working app with the Breez SDK and write up how you built it"; "Your project becomes an open-source guide for the next developers".
- **Provided:** "A starter template from Breez for every bounty"; "a dedicated support channel".
- **Prizes:** "Every entry that meets Breez's bar wins a bounty". The ten bounties, their amounts, and the bar are not on the public site.

Analysis (not official):
- **Must show:** a working, open-source app on the Breez SDK that addresses one of the ten bounties, with a write-up. It is threshold-based, not a single winner.
- **Ways in:** adapt the Breez starter template for one bounty; add a send or receive payment step to an existing action in the app; gate one feature behind a small payment.
- **Extra work:** 4–8 h, including 1–2 h for the write-up. Needs the Breez SDK set up and the bounty list.
- **Common failures:** mocked payments; no write-up; closed source; not matching a bounty; not meeting the unpublished bar.

## Best Beginner

- **Sponsor:** none. (§2.5)
- **Official description:** "Never been to a hackathon? This one is yours." "For teams where most members are first-timers". "Judged on how far you came and what you learned, not on polish".
- **Prize:** 1st Logitech MX Master 4 mouse each.
- **Eligibility:** by team make-up, not project content. How it is verified, and whether a team must opt in, is not stated.

Analysis (not official):
- **Must show:** that most of the team are first-timers, and what they learned.
- **Ways in:** keep a short log of starting skills and what each member learned; show progression from an early commit to the final state; have each member explain their part at the demo.
- **Extra work:** 0.5–1 h.
- **Common failures:** team does not meet "most members"; presenting polish instead of learning; not flagging the entry if opt-in is required.

## Capture the Flag

- **Sponsor:** none. (§2.6)
- **Official description:** "Running all weekend alongside the hackathon." "Crack ciphers, break into deliberately vulnerable apps and dig through hidden files". "Most flags wins".
- **Prize:** 1st Flipper Zero each.
- **Kind:** a side competition that "doesn't require shipping a prototype". Platform, team size, and whether a person may do both it and a project are not stated.

Analysis (not official):
- Not a project track; no integration with a project is possible or needed. Every hour spent here is an hour not spent building.

## Beyond the Horizon

- **Sponsor:** "With MSGC, powered by NASA open data" (Michigan Space Grant Consortium). (§3.1)
- **Official description:** "NASA satellites photograph the entire planet every day, and all of it is yours to build with this weekend." "Build an analysis, a map, a model, a game or a teaching tool; Michigan ideas like Great Lakes ice, algal blooms or Detroit heat are welcome".
- **Provided:** "Live NASA APIs with one free key" (Astronomy Picture of the Day, Mars rover photos, near-Earth asteroids, space weather, wildfires and storms); Landsat and MODIS imagery; NASA Worldview; Prithvi open AI models for Earth and weather; ISS, exoplanet, Hubble, JWST, and TESS data.
- **Prize:** 1st Celestron Travel Scope 60 telescope each.

Analysis (not official):
- **Must show:** something built on NASA open data, APIs, or models, with a clear link between the data and what the project does.
- **Ways in:** a feature that pulls a NASA API feed relevant to the app's context; a map or visualization layer over NASA Earth-observation imagery; an analysis or open-model inference on a NASA dataset whose result drives something in the app.
- **Extra work:** 1–3 h for an API-backed feature; 4–10 h for imagery analysis or model inference. Needs a free NASA API key; heavier work needs large downloads and possibly a GPU.
- **Common failures:** NASA content as decoration; large image tiles failing on venue Wi-Fi; shared demo-key rate limits.

## Quantum Computing

- **Sponsor:** "Led by Quantum Rings". (§3.2)
- **Official description:** "Run real quantum circuits on an ordinary laptop." "Build a game, a visualizer or an algorithm demo, and explain the quantum part in plain words".
- **Given to every hacker:** "A free 200-qubit Quantum Rings license ... good for a year"; a virtual workshop.
- **Prize:** 1st "Quantum Rings internship interview, compute credits and a Turtle Beach Stealth 700 headset each" (a guaranteed interview for 2027 summer internships).

Analysis (not official):
- **Must show:** quantum circuits running as part of the project, and a team that can explain the quantum part plainly.
- **Ways in:** hand one small computation in the app to a circuit on the Quantum Rings simulator; an interactive view that explains the circuit and its results; a mechanic driven by measurement outcomes.
- **Extra work:** 3–6 h for a team new to quantum SDKs. Needs a Quantum Rings account, license, and SDK install.
- **Common failures:** cannot explain the quantum part; a trivial circuit unconnected to the product; a different simulator; leaving license setup to the last hours.

## Best Use of Base44

- **Sponsor:** Base44. (§3.3)
- **Official description:** "Base44 is an AI app builder: tell it what you want in plain English and get a working app back". "Database, user login and hosting are built in". "Ship a live link people can actually use by demo time".
- **Judged by:** "Community vote". Who votes, where, and when is not stated.
- **Prizes:** 1st Ray-Ban Meta glasses + Builder plan each; 2nd AirPods + Builder plan each; 3rd Builder plan each.

Analysis (not official):
- **Must show:** an app built with Base44, live at a link by demo time.
- **Ways in:** build the whole app in Base44; build one surface of a larger project (dashboard, onboarding, admin) in Base44 that calls the project's own backend; use Base44 for the user-facing prototype while custom logic lives elsewhere. Whether partial use qualifies is not stated.
- **Extra work:** 1–4 h to a live app, plus effort to gather votes. Needs a Base44 account; plan limits not stated.
- **Common failures:** no live link at demo time; voters blocked by a login wall or mobile breakage; ignoring the vote.

## Best Use of SSOJet

- **Sponsor:** SSOJet. (§3.4)
- **Official description:** "Add real sign-in to your project in minutes." "Single sign-on and secure login with SSOJet".
- **Given to every hacker:** "SSOJet's free plan".
- **Prize:** "1st and 2nd place: SSOJet business licenses for the team".

Analysis (not official):
- **Must show:** single sign-on and login through SSOJet working in the project.
- **Ways in:** make SSOJet the app's login (standard redirect flow); add organization-level sign-on for a team or tenant concept; protect an admin area or API with the issued tokens.
- **Extra work:** 1–3 h for a standard web login; more for multi-tenant setups. Needs an SSOJet account and correct redirect URLs for wherever the app runs.
- **Common failures:** login not working in the demo; another auth provider doing the real work; redirect misconfiguration after deployment; sign-in with no purpose in the app.

## Code of Life

- **Sponsor:** "Led by Seqera" (the team behind Nextflow). (§3.5)
- **Official description:** "Biology runs on data, and this weekend you get the same tools working scientists use to process it." "Pick a suggested theme (teaching, precision medicine, single-cell, cancer, health data) or bring your own".
- **Provided:** a team workspace on the Seqera Platform with cloud compute; Seqera's AI Co-Scientist; ready-made nf-core pipelines with test data; twelve public and synthetic datasets; the Eduomics teaching pipeline to extend.
- **Restriction (stated):** "Research and education only: no medical advice, no real patient data".
- **Prize:** 1st "$250 Seqera compute and Co-Scientist credits, continued platform access, up to 8 hours of mentoring".

Analysis (not official):
- **Must show:** work using the Seqera Platform, Nextflow or nf-core pipelines, or the AI Co-Scientist on the provided biology datasets.
- **Ways in:** run a ready-made pipeline on a provided dataset and build an app or visualization on its outputs; add or modify a pipeline step and document it; wrap pipeline launch and results in a user interface.
- **Extra work:** 4–10 h; steeper with no biology background. Needs the track workspace (how to get it is not stated) and Nextflow basics.
- **Common failures:** pipeline runs that do not finish in time; biology that is nominal; real patient data or medical advice; results that cannot be reproduced.

## Department of Computer Science Track

- **Sponsor:** "Presented by the EMU Department of Computer Science". (§3.6)
- **Official description:** "For the team whose project is the most impressive piece of software, judged on what is under the hood." "Clean architecture, smart algorithms and code that actually holds up".
- **Combining (stated):** "Any idea, any stack, in any track".
- **Prize:** "Winning team: $1,000 scholarship, $250 for each member". Whether it is limited to EMU students is not stated.

Analysis (not official):
- **Must show:** engineering quality that judges can see in the code.
- **Ways in:** clear module boundaries and a README with an architecture overview; at least one non-trivial algorithm or system component the team wrote and can explain; tests, error handling, and a readable commit history.
- **Extra work:** 2–5 h of engineering hygiene spread over the event. Needs a public repository judges can read.
- **Common failures:** all logic is glue around third-party APIs; generated code the team cannot explain; undocumented repository.

## Best Use of ElevenLabs

- **Sponsor:** ElevenLabs. (§3.7)
- **Official description:** "Some ideas are better heard than read. Build the ones that talk, listen and sound alive." "Lifelike text-to-speech in dozens of languages"; "Voice agents that hold a real conversation"; "Speech-to-text, custom voices and sound effects".
- **Given to every hacker:** "The ElevenLabs Creator plan free for one month".
- **Prizes:** 1st Scale plan for 3 months each; 2nd Pro plan for 3 months each.

Analysis (not official):
- **Must show:** ElevenLabs audio used in a way that matters to the project.
- **Ways in:** spoken output for key content; a conversational voice interface to the app's main function; voice input for a hands-free flow.
- **Extra work:** 1–2 h for speech output; 3–6 h for a conversational agent wired to app data. Needs an ElevenLabs account and key.
- **Common failures:** audio as a gimmick; voice demos failing in a loud hall; quota exhaustion; no recorded fallback.
