# Hack The Nest (Eastern Michigan University), Nov 14-15, 2026: tracks, prizes, challenges, opportunities

Researched 2026-11-14, about 21:00-21:35 UTC (4:00-4:35 PM EST), while the event was in progress. Sections 1-4, 6 and 7 are official facts with a source tag on each; section 5 is my analysis and is labelled as such.

## 0. Which event this is, and how it was read

- **Event used:** Hack The Nest 2026 ("HACK THE NEST v1.0"), Nov 14-15, 2026, Eastern Michigan University, Ypsilanti, MI. "EMU" is confirmed as Eastern Michigan University [S1][S4]. This is the first edition ("Eastern Michigan University's first flagship hackathon" [S9]), so there is no previous EMU edition to confuse it with. Nov 14, 2026 is a Saturday, i.e. the event started today.
- **Official site:** https://hackthenest.tech/ [S1]. It is a server-rendered Next.js site with only these public pages: home (About, Tracks, Sponsors, Partners, FAQ, Team), `/login`, `/mlh/contest-terms`, `/mlh/code-of-conduct`, `/mlh/privacy-policy`, `/privacy`. `/register`, `/account` and `/checkin` require sign-in (not accessed; no account was created). `/schedule`, `/prizes`, `/rules`, `/judging`, `/sponsors`, `/faq`, `/resources`, `/workshops`, `/sitemap.xml` and similar all return 404.
- **Track details:** the "See track" panels are filled from a data module shipped in the page's JavaScript; I read that module directly [S2], so every track field quoted below is verbatim site text. No browser rendering was needed (and none was run).
- **Not this event:** an unrelated, identically named high-school hackathon in the DC/Maryland/Virginia area (hackthenest.org; Devpost pages hackthenest-2023, hack-the-nest-2025, hack-the-nest-v3) [W8]. None of its tracks or rules are used here. Note the EMU event's Linktree handle and contact email use "hackthenest.org" (`linktr.ee/hackthenest.org`, `hackthenest.org@gmail.com`) [S1][S4] even though its website is hackthenest.tech; the website hackthenest.org belongs to the unrelated event [W8].
- **Network note:** every relevant host was initially blocked by this session's egress proxy. The user approved a one-off addition of four hosts to the "RepTracker" cloud environment allowlist (`hackthenest.tech`, `hack.mlh.io`, `www.mlh.com`, `gdg.community.dev`); that change is stored on the environment and persists for future sessions until removed. Other hosts stayed blocked; see section 7.

## 1. Event basics

| Item | Official fact | Source |
|---|---|---|
| Organizer | "Google Developer Group on Campus at EMU"; footer "(c) 2026 GDG at Eastern Michigan University". "organized by a 20-person team led by five committee leads, all from GDG on Campus EMU". Official MLH Member Event (MLH 2026 Hackathon Season badge). | [S1][S4][S9] |
| Dates | "NOV 14-15, 2026" (Saturday-Sunday) | [S1] |
| Times | Not on the official site. MLH listing: "Sat, Nov 14 · 2:00 PM – Sun, Nov 15 · 9:00 PM UTC" (= Sat 9:00 AM - Sun 4:00 PM EST). GDG page: "Nov 14, 9:00 AM – Nov 15, 5:00 PM (EST)". Build window: "build time ... 24 hrs". | [S6][S9][S1] |
| Schedule items (secondary, search-summary only) | Eastern Echo, as relayed by a search summary (article not fetched): opening ceremony 11 a.m.-12 p.m. day one; g.tec session 2-3 p.m.; robotics exhibition 6-10 p.m.; project demos and closing ceremony 12-4 p.m. day two; teams stay overnight. The site itself confirms only "A 60-minute hands-on g.tec workshop (Saturday, 2 PM)". | [W1][S2] |
| Location / format | "It's a fully in-person event at Eastern Michigan University in Ypsilanti, MI. Exact venue details go out to registered hackers closer to the date." GDG page: "Eastern Michigan University Student Center, 900 Oakwood Street, Ypsilanti, 48197". Secondary sources add Halle Library. MLH: "In Person", focus tags "Software", "Hardware". | [S1][S9][W1][W4][S6] |
| Eligibility | "Hack The Nest is open to all college and high school students, whatever your major or experience level." Registration asks "whether you will be under 18 on November 14, 2026, and, if you are, how you are enrolled at Eastern Michigan University"; minors may need a parent/guardian consent form. MLH contest terms: "at least eighteen years old (or minors with parental permission)". MLH standard rules count people who "graduated within the last 12 months" as students. | [S1][S4][S3][S8] |
| Team size | "Teams can have up to 4 people, but you're welcome to come solo. We'll host a team-matching session at the start". No minimum stated. | [S1] |
| Cost | "Nothing. Hack The Nest is completely free. Meals, workspace, swag, and everything you need for the weekend are covered for you." | [S1] |
| Capacity | Site: "hackers ... up to 500". GDG page: "up to 1,000 students". Other figures in section 7. | [S1][S9] |
| Registration | Via the site: "Register now" -> `/register` (requires creating an account / Google sign-in). The button was still shown during the event. MLH page: "Registration & check-in - Managed on the event website", steps "1 Register, 2 Check In, 3 Submit Project". No registration deadline is published. | [S1][S6] |
| Submission platform | Not stated on hackthenest.tech (no Devpost, Discord or submission link anywhere on the public site). The MLH event page has a "Submit Project" step and per-category pages; at fetch time its embedded data showed `submissionsOpen: false`, `submissionDeadline: null`, `submissionsCount: 0`, and each category page said "Submissions aren't open for this event." No Devpost page for the EMU event was found. | [S6][S1] |
| Submission deadline | Not published anywhere I could read. | - |
| What must be submitted | Not published by the organizers. Applicable MLH texts: you "present to the judges an original project/prototype"; "Your code must be available publicly (ideally in a git repository)" and "must remain public post event to be eligible for prizes"; AI tools used should be listed "in their project submissions". A demo video is required by MLH only for fully digital events ("live demos at physical hackathons"). Some tracks add their own deliverables (Breez write-up, Base44 live link, SpaceXSI project-description text). | [S3][S8][S2][S6] |
| Judging process | Not published by the organizers for their own tracks. Track-level statements exist for four tracks (Best Beginner, Capture the Flag, Base44, CS Department; see sections 2-3). GDG page mentions "project demos, and a closing ceremony with awards". | [S2][S9] |
| Judging criteria with weights | Only in the MLH contest terms reproduced on the site: "originality/creativity (25%); technical complexity (25%); adherence to Theme (25%) and practical implementation (25%)". MLH standard rules (for "MLH categories at an in person event"): Technology, Design, Completion, Learning, weighed equally. Whether the organizers use either set for their own tracks is not stated. | [S3][S8] |
| Pre-existing code | MLH terms: "All work on your Application must be performed during the time window defined at the Event. You may not perform any work on your Application prior to the time window ... or your Application will be disqualified at the sole discretion of the Sponsor." MLH standard rules: ideas from before the event are allowed; libraries, frameworks and open-source code are allowed; re-using your own earlier code is not. | [S3][S8] |
| AI tool use | MLH standard rules: "Teams may use AI to assist them while coding" and "should be honest and transparent about the AI code tools they used. This includes listing them in their project submissions". The site has no statement of its own. | [S8] |
| IP / publicity | MLH terms: entrant must own the application or have written permission for third-party elements; materials "are submitted on a nonconfidential and non-proprietary basis and may be used by Major League Hacking ... for advertising and promotional purposes". Photos/video are taken; opt-out via profile checkbox or at check-in. | [S3][S4] |
| Required attendance | In person. MLH terms: "Each Participant or team must be available during the Event's judging period to demonstrate". MLH rules: "All team members should actively participate"; organizers, volunteers, judges, sponsors should not compete. | [S1][S3][S8] |
| What to bring | "Your laptop and charger, a photo ID, and anything to stay comfortable overnight (toiletries, a hoodie, maybe a sleeping bag)." | [S1] |

Caveat on the MLH texts: the contest terms on the site are a copy made "on October 18, 2026" of MLH's terms whose stated term is "July 1, 2025 ... June 30, 2026"; the site says "if the two ever differ, MLH's applies" [S3]. The MLH standard hackathon rules say "Not all MLH Member Event Hackathons will use these rules, as organizers can choose to use them or their own" [S8]; the site does not say which it uses.

## 2. Tracks "On the street" (the site's prize tracks)

The site's own framing: "Depot Town, Ypsilanti. Every shop on the street is a prize track, and the train at the end of it carries the sponsor, academic and MLH tracks." [S1]. All tracks have status "open". Source for every quoted field in sections 2 and 3: [S2] (https://hackthenest.tech/#tracks). No track panel carries a "Who can enter", "Everyone gets" or resources-link field, and only Base44 carries a "Judged by" field. No track states whether it can be combined with others, except the CS Department track.

### 2.1 Hack The Nest (overall)
- Sponsor: none listed. Description: none (the panel has only prizes).
- Prizes: 1st place "PlayStation 5 each"; 2nd place "Nintendo Switch each"; 3rd place "Monitors each".
- Requirements / judging: not stated. Combinability: not stated.

### 2.2 Future of Intelligence
- Credit: "Led by OpenAI, with Exa".
- Summary: "AI is writing the future. Build the part nobody has thought of yet."
- Description: "The next wave of software will not just answer questions; it will think, search and act on its own."
- Points: "Build on OpenAI's models and Exa's search engine made for AI, so your project can reason over the live web" / "$50 in Exa API credits for every hacker" / "Build the agent, app or tool you wish already existed, and polish it like a real product" / "Top teams take home prizes".
- Prizes: "Prizes: Coming soon" (not yet published at fetch time).
- Requirements / judging: none beyond the points above. Whether both OpenAI and Exa must be used is not stated.

### 2.3 Mind and Machine
- Credit: "Led by g.tec, with PiEEG".
- Summary: "The singularity starts with a brain signal. Build it."
- Description: "The singularity will not wire itself: someone has to connect the mind to the machine. Led by g.tec, a world leader in brain-computer interfaces."
- Points: "g.tec Unicorn EEG hardware at the event, set up and tested by g.tec's own team" / "Seven real brain-signal datasets from g.tec, from a P300 speller and SSVEP to stroke rehab and ECoG hand pose" / "A 60-minute hands-on g.tec workshop (Saturday, 2 PM) and the g.tec booth" / "The winning team takes home a g.tec Unicorn Hybrid Black headset" / "With PiEEG: 16-channel Octopus EEG boards, simulated brain-signal streams on PiEEG Cloud, and a live online workshop" / "Three optional directions, Video Games, Assistive Technology and Data Science, or your own idea".
- Prizes: 1st place "g.tec Unicorn Hybrid Black headset" (note: "one for the team"); 2nd place "Two PiEEG Octopus 16 boards"; 3rd place "Logitech MX Keys S keyboard each".
- Requirements / judging: not stated beyond the above.

### 2.4 Future of Money
- Credit: "Led by Breez".
- Summary: "Ten everyday problems. One global money. Build the fix."
- Description: "Money should cross the world as easily as a text message, and in most apps it still does not."
- Points: "Ten bounties, each one an everyday situation where money is slow or stuck" / "A starter template from Breez for every bounty" / "Build a working app with the Breez SDK and write up how you built it" / "Your project becomes an open-source guide for the next developers, and their AI coding agents, to follow" / "Help from the Breez team in a dedicated support channel" / "Every entry that meets Breez's bar wins a bounty".
- Prizes: "Bounties: A Breez bounty for every entry that meets Breez's bar". Bounty amounts, the list of ten bounties and the "bar" are not published on the site.
- Track-specific requirements (stated): a working app using the Breez SDK, a write-up, open source.

### 2.5 Best Beginner
- Sponsor: none listed.
- Summary: "First hack. First win." Description: "Never been to a hackathon? This one is yours."
- Points: "For teams where most members are first-timers" / "Judged on how far you came and what you learned, not on polish".
- Prize: 1st place "Logitech MX Master 4 mouse each".
- Eligibility (stated): teams where most members are first-timers. How that is verified, and whether a team must opt in, is not stated.

### 2.6 Capture the Flag
- Sponsor: none listed.
- Summary: "Find the flags. Own the scoreboard." Description: "Running all weekend alongside the hackathon."
- Points: "Crack ciphers, break into deliberately vulnerable apps and dig through hidden files" / "Every flag you find puts points on the board" / "Most flags wins".
- Prize: 1st place "Flipper Zero each".
- Nature: a side competition, not a project track. GDG page: "a capture the flag competition running alongside the main build, so if security is your thing there's a track for you that doesn't require shipping a prototype" [S9]. Platform, team size and whether one person may do both CTF and a project are not stated.

## 3. Tracks "On the train" (sponsor, academic and MLH tracks) and other prizes

Site label: "Sponsor, academic and MLH tracks, one to a carriage." [S1]

### 3.1 Beyond the Horizon
- Credit: "With MSGC, powered by NASA open data" (Michigan Space Grant Consortium; NASA).
- Summary: "With MSGC and NASA's open data, build something out of this world."
- Description: "NASA satellites photograph the entire planet every day, and all of it is yours to build with this weekend. Thanks to the Michigan Space Grant Consortium."
- Points: "Live NASA APIs with one free key: Astronomy Picture of the Day, Mars rover photos, near-Earth asteroids, space weather, wildfires and storms" / "Landsat: more than 50 years of satellite images of Earth's surface, sharp enough to see a single farm field" / "MODIS: the whole planet imaged every one to two days, from ice and clouds to wildfire smoke" / "NASA Worldview: browse all of it on an interactive globe, right in your browser" / "Prithvi: NASA's open AI foundation models for Earth and weather, with ready versions for flood mapping and burn scars" / "Beyond Earth: real ISS experiment data, exoplanet light curves, and Hubble, JWST and TESS data" / "Build an analysis, a map, a model, a game or a teaching tool; Michigan ideas like Great Lakes ice, algal blooms or Detroit heat are welcome" / "Supported by the Michigan Space Grant Consortium, NASA grant 80NSSC20M0124".
- Prize: 1st place "Celestron Travel Scope 60 telescope each".

### 3.2 Quantum Computing
- Credit: "Led by Quantum Rings".
- Summary: "Bend reality, one qubit at a time." Description: "Run real quantum circuits on an ordinary laptop."
- Points: "A free 200-qubit Quantum Rings license for every hacker, good for a year" / "Build a game, a visualizer or an algorithm demo, and explain the quantum part in plain words" / "A virtual workshop from the Quantum Rings team" / "The winning team gets a guaranteed interview for Quantum Rings' 2027 summer internships".
- Prize: 1st place "Quantum Rings internship interview, compute credits and a Turtle Beach Stealth 700 headset each".

### 3.3 Best Use of Base44
- Sponsor: Base44.
- Summary: "Think it. Prompt it. Build it." Description: "Describe the app in your head, and Base44 builds it."
- Points: "Base44 is an AI app builder: tell it what you want in plain English and get a working app back" / "Database, user login and hosting are built in, so your weekend goes into the idea, not the setup" / "Keep shaping it by chatting with it until it looks and works the way you pictured" / "Ship a live link people can actually use by demo time" / "Winners are chosen by community vote: 1st takes home Ray-Ban Meta glasses, 2nd AirPods, and the top three teams get Base44 Builder plans".
- Prizes: 1st "Ray-Ban Meta glasses + Builder plan each"; 2nd "AirPods + Builder plan each"; 3rd "Builder plan each".
- Judged by: "Community vote" (who votes, where and when is not stated). Stated deliverable: a live link by demo time.

### 3.4 Best Use of SSOJet
- Sponsor: SSOJet.
- Summary: "Log in like the big leagues." Description: "Add real sign-in to your project in minutes."
- Points: "Single sign-on and secure login with SSOJet" / "SSOJet's free plan for every hacker".
- Prize: "1st and 2nd place: SSOJet business licenses for the team".

### 3.5 Code of Life
- Credit: "Led by Seqera".
- Summary: "Real data. Real pipelines. An AI co-scientist at your side."
- Description: "Biology runs on data, and this weekend you get the same tools working scientists use to process it. Led by Seqera, the team behind Nextflow."
- Points: "Your own team workspace on the Seqera Platform, running on an AWS cloud compute environment set up for this track" / "Seqera's AI Co-Scientist, which helps you write, run and debug bioinformatics pipelines" / "Ready-made nf-core pipelines with their test data, so you can run a real analysis in your first hour" / "Twelve public and synthetic datasets from beginner to advanced: immune cells from single-cell RNA sequencing, disease-linked gene variants (ClinVar), synthetic patient records (Synthea) and drug-gene guidelines, up to cancer genomics (TCGA) and gene dependency screens (DepMap)" / "Or take Eduomics, a pipeline from Seqera's community that generates simulated data for teaching genomics, and extend it to new kinds of biology data, even bioimaging" / "Pick a suggested theme (teaching, precision medicine, single-cell, cancer, health data) or bring your own" / "The winning team gets up to 8 hours of mentoring from Seqera's bioinformaticians, continued platform access and $250 in compute and Co-Scientist credits" / "Research and education only: no medical advice, no real patient data".
- Prize: 1st place "$250 Seqera compute and Co-Scientist credits, continued platform access, up to 8 hours of mentoring".
- Stated restriction: research and education only; no medical advice; no real patient data.

### 3.6 Department of Computer Science Track (academic)
- Credit: "Presented by the EMU Department of Computer Science".
- Summary: "The best code wins." Description: "For the team whose project is the most impressive piece of software, judged on what is under the hood."
- Points: "Clean architecture, smart algorithms and code that actually holds up" / "Any idea, any stack, in any track" / "The winning team earns a $1,000 scholarship, $250 for each member".
- Prize: "Winning team: $1,000 scholarship, $250 for each member".
- Combinability (stated): "Any idea, any stack, in any track". Whether the scholarship is limited to EMU students is not stated.

### 3.7 Best Use of ElevenLabs
- Sponsor: ElevenLabs.
- Summary: "Give your idea a voice." Description: "Some ideas are better heard than read. Build the ones that talk, listen and sound alive."
- Points: "Lifelike text-to-speech in dozens of languages" / "Voice agents that hold a real conversation" / "Speech-to-text, custom voices and sound effects" / "Build a study partner, a game character, an accessibility tool or a podcast that writes itself" / "The ElevenLabs Creator plan free for one month for every hacker".
- Prizes: 1st "Scale plan for 3 months each"; 2nd "Pro plan for 3 months each".
- Note: MLH's season-wide prize page also lists a "Best Use of ElevenLabs" category (prize "Wireless Earbuds") [S7], but it is not among the eight MLH categories on the Hack The Nest MLH page [S6]; the prizes above are the ones on the event's own site.

### 3.8 MLH Tracks
- Credit on the event site: "Run and paid for by Major League Hacking". The site lists eight names and no prizes: "Build Your Hackathon A-Team with SpaceXSI", "Best Use of Gemini API", "Best Use of Solana", "Best Use of Tiger Data", "Best Use of Vultr", "DEV Writing Challenge", "Best Use of MongoDB Atlas", "Best Domain Name from GoDaddy Registry" [S2]. Details below are from the MLH event page, which lists the same "8 categories" [S6] (each at `https://www.mlh.com/events/hack-the-nest-96/challenges/<id>`).
- Rule for all MLH categories: "Individuals and Teams are limited to one (1) Application for each Category in each Event." and "You may participate with more than one (1) Application at each Event" [S3]. No cap on the number of categories is stated.

| MLH category | Prize | Official description (verbatim excerpts) and stated requirements | Page id |
|---|---|---|---|
| Build Your Hackathon A-Team with SpaceXSI (sponsor shown: xAI) | "Mechanical Keyboard" | "Build your hackathon project with Cursor and Grok Bot this weekend to qualify for the SpaceXSI raffle. Every member on the winning team walks away with a custom-branded Cursor mechanical keyboard. Here's how you qualify: Use Cursor as your core AI coding agent / Integrate a Grok Bot automation into your workflow / In your project description, describe how you use both Cursor and Grok Bot. / Submit your project and be sure to opt-in to the Make it Legendary with SpaceXSI raffle." Freebie: promo code for "one month of X Premium", "Claim by Jan 10, 2027" (MLH login needed). This one is a raffle. | 01a15a90-5b3e-62db-908a-f44b209c9a5e |
| Best Use of Gemini API | "MLH Swag Kits" | "It's time to push the boundaries of what's possible with AI using Google Gemini. Check out the Gemini API to build AI-powered apps that make your friends say WHOA. ... Understand language like a human and build a chatbot that gives personalized advice / Analyze info like a supercomputer and create an app that summarizes complex research papers / Generate creative content like code, scripts, music, and more" | 01953de4-ee8b-0807-88b1-86bb6abbf410 |
| Best Use of Solana | "Unruggable Hardware Wallets" | "Harness Solana's core advantages like blazing fast execution and near-zero transaction costs ... Create a game, social app, or consumer product that relies on instant, high-frequency transactions. / Design a sophisticated trading, lending, or decentralized exchange (DEX). / Build a prototype for supply chain, identity, or payments that can handle massive, real-world volume. Show us how you can innovate with Solana for a chance to win Unruggable Hardware Wallets for you and each member of your team!" | 019a2bd6-b180-c2c1-8b01-cd7998ac0c8d |
| Best Use of Tiger Data | "Stream Deck Mini" | "Tiger Data extends PostgreSQL to give student developers an ultra-fast foundation for real-time data, time-series metrics, and complex analytics. ... The team that demonstrates the most innovative, impactful, and performance-driven use of Tiger Data will take home some great prizes!" | 019fcfdb-abbc-d470-b762-e73f1ee414d2 |
| Best Use of Vultr | "Assorted Prizes" | "Vultr empowers hackers to bring their high-performance projects to life instantly; providing everything from the speed of one-click deployment and scalable cloud compute, to specialized Vultr Cloud GPUs ... Sign up for a Vultr account today and claim your free cloud credits! Take your next hack to the cloud with Vultr for a chance to win some awesome prizes for you and your team!" | 019a0ccc-7154-9378-095c-2a7be06a0378 |
| DEV Writing Challenge | "$100" | "Publish what you built on DEV and help other developers learn from your process. Each month, the DEV editorial team will select at least one favorite project. ... Selections consider technical substance, originality, clear storytelling, and community popularity." Post-event; link: dev.to/mlh-hackathon. | 01a120eb-00a4-1251-a834-e3c3be34055d |
| Best Use of MongoDB Atlas | "M5Stack IoT Kit" | "Get started with a $50 credit for students or sign up for the Atlas free forever tier (no credit card required). ... Build a hack using MongoDB Atlas for a chance to win a M5Stack IoT Kit for you and each member of your group." | 01952051-cd69-c851-c19b-592551464587 |
| Best Domain Name from GoDaddy Registry | "Digital Gift Card" | "Register your domain name with GoDaddy Registry for a chance to win some amazing prizes!" Freebie: "Redeem a domain name at tech.study. Available domain name extensions are: .us, .biz, .tv, .courses, .study, .club, .design, .compare, .select, and .co", "Claim by Nov 19, 2026", "Each code is valid for one free domain per account. The code will not work if you have previously redeemed a domain name using a GoDaddy Registry promo code on your account." (MLH login needed). | 019398d8-108f-4f26-102c-4fe01a9ec5ed |

### 3.9 Prizes that do NOT exist on the official pages (checked)
- No people's choice, design, hardware, or social-good prize is listed on the site [S1][S2]. (Base44 is the only community-vote prize.)
- No IBM, Kawasaki Robotics, Logitech, Turtle Beach or Google challenge is listed as its own track, although IBM and Kawasaki Robotics are listed sponsors and Logitech and Turtle Beach are listed partners (their products appear as prizes) [S1][S2]. Gemini appears only as an MLH category.
- A "Best use of the Perplexity API" track was only proposed by an organizer in a public forum post (search summary; page not fetched) and is not on the site [W5].
- Counts differ by source: the site shows 6 street tracks + 8 train carriages (one of which is the 8-category MLH group) [S1]; the Eastern Echo reportedly says "eight prize tracks ... along with other prize tracks that are for best beginner, the capture the flag side game and more" [W1]; the older GDG text says "Four prize tracks are being revealed soon" [S9]. The site invites visitors to "Follow all our socials for what's next" [S1], so the list may still change.

## 4. Other opportunities

Free tooling and credits "for every hacker" (how to claim is not stated on the site unless noted):
- "$50 in Exa API credits for every hacker" [S2]
- "A free 200-qubit Quantum Rings license for every hacker, good for a year" [S2]
- "SSOJet's free plan for every hacker" [S2]
- "The ElevenLabs Creator plan free for one month for every hacker" [S2]
- Seqera: "Your own team workspace on the Seqera Platform, running on an AWS cloud compute environment set up for this track", plus the AI Co-Scientist (for the Code of Life track) [S2]
- Breez: "A starter template from Breez for every bounty" and "a dedicated support channel" [S2]
- NASA: "Live NASA APIs with one free key" [S2]
- Via MLH: free domain code from GoDaddy Registry (claim by Nov 19, 2026), one month of X Premium promo code (claim by Jan 10, 2027), MongoDB "$50 credit for students" / Atlas free tier, Vultr "free cloud credits" [S6]

Hardware and datasets:
- "g.tec Unicorn EEG hardware at the event, set up and tested by g.tec's own team"; "Seven real brain-signal datasets from g.tec"; PiEEG "16-channel Octopus EEG boards, simulated brain-signal streams on PiEEG Cloud" [S2]
- Twelve public and synthetic biology datasets (Code of Life) [S2]
- The MLH event page lists "Digi-key Hardware Lab" under Sponsors, with no details; MLH tags the event focus as "Software" and "Hardware" [S6]. The organizer site does not mention a hardware lab.

Workshops, mentoring, people:
- "We'll run beginner-friendly workshops and have mentors on the floor all weekend" [S1]; "mentors from industry on the floor the whole time ... Sponsor engineers will be in the building at booths and in one-on-one sessions" [S9]
- g.tec: "A 60-minute hands-on g.tec workshop (Saturday, 2 PM) and the g.tec booth"; PiEEG: "a live online workshop"; Quantum Rings: "A virtual workshop from the Quantum Rings team" [S2]
- MLH page lists "Intro to Google AI Studio" (links to events.mlh.com/events/15872) and "Gemini Demo" [S6]
- Team-matching session at the start [S1]
- Robotics exhibition, 6-10 p.m. on day one (search summary of the Eastern Echo only) [W1]; Kawasaki Robotics is a listed sponsor [S1]

Recruiting / career:
- Optional resume book (18 or older): partners receive resume, name, email, school, level of study, graduate degree and LinkedIn/portfolio link of those who opt in; "Some partners may receive the resume book before the event and others after" [S4]
- Quantum Computing winners: "a guaranteed interview for Quantum Rings' 2027 summer internships" [S2]
- Code of Life winners: "up to 8 hours of mentoring from Seqera's bioinformaticians" [S2]
- CS Department track: $1,000 scholarship [S2]
- Networking: "a lot of space to meet people from other schools and other majors" [S9]

Food, swag, logistics:
- Free "Meals, workspace, swag" [S1]; "a merch table, food throughout" [S9]; midnight snack sponsors Sweetwaters Coffee & Tea and Eagles Market; partners include Madras Masala, Red Bull, Celsius, RYSE, Pure Buttons [S1]
- Overnight stay is expected ("maybe a sleeping bag") [S1]
- Travel reimbursement: not mentioned on any official page.
- After the event: DEV Writing Challenge ($100, monthly selection) [S6]; MLH standard rules mention an "I Demoed" sticker for teams that demo [S8].

Listed sponsors [S1]: OpenAI, IBM, ElevenLabs, SSOJet, Base44, Exa, Breez, Kawasaki Robotics, g.tec, Quantum Rings, NASA / Michigan Space Grant Consortium, Pure Buttons. Additional names on the partner wall: PiEEG, Seqera, Logitech, Turtle Beach, Eastern Michigan University, EMU Computer Science, Compass Detroit, Madras Masala, Red Bull, Celsius, RYSE, Major League Hacking, SpaceX, Gemini, Solana, Tiger Data, Vultr, MongoDB, GoDaddy Registry.

## 5. ANALYSIS (mine, not official): how an arbitrary project could qualify for each track

Everything in this section is my own neutral analysis. Statements about how a sponsor's product works come from general knowledge, not from the event site, and should be checked against the sponsor's docs. Hour figures are rough estimates for a 2-4 person team with no prior setup. No track is recommended or ranked; the order follows sections 2-3.

**Hack The Nest (overall).** Official requirements: none published. To be eligible a project presumably needs to be a registered team's submission built within the event window and demonstrated to judges (MLH texts). Generic patterns: (1) one core flow that works end to end in a live demo; (2) a public repository whose history shows the work was done during the event; (3) a short, honest list of the libraries and AI tools used. Extra work: only submission paperwork, about 0.5-1 h. Common failures: no working demo; work done before the window; nobody available at judging time; repo left private; missing the (unpublished) deadline.

**Future of Intelligence (OpenAI, Exa).** Must show: software built "on OpenAI's models and Exa's search engine" that can "reason over the live web", presented "like a real product". Patterns: (1) a feature where a model answers or decides using documents fetched live through Exa search, with sources shown; (2) an agent loop in which the model calls Exa as a tool and then acts on the app's own data; (3) a background enrichment job that looks up entities from the app on the web and summarizes them. Extra work: about 2-5 h for a search-plus-model feature, 5-10 h for a multi-step agent with polish. Prerequisites: OpenAI API key (whether OpenAI credits are provided is not stated), Exa key with the $50 credit (claim path not stated). Common failures: a chat box bolted on with no role in the product; using only a different model provider; no live-web component; rate limits or exhausted keys during the demo. Open question: prizes are "Coming soon", and it is not stated whether both sponsors' APIs are mandatory.

**Mind and Machine (g.tec, PiEEG).** Must show: a project whose function depends on brain-signal data, from the on-site Unicorn EEG hardware, the seven g.tec datasets, PiEEG boards, or the simulated PiEEG Cloud streams. Patterns: (1) use a value derived from a provided dataset or live headset (for example a classifier output) as an input or control channel for a feature; (2) an offline analysis or ML pipeline over one provided dataset with a visual front end; (3) develop against the simulated stream as a real-time data source, then switch to hardware for the demo if available. Extra work: about 4-8 h dataset-only, 6-12 h or more with live hardware. Prerequisites: time at the g.tec booth and the Saturday 2 PM workshop, shared hardware availability, a signal-processing stack. Common failures: the brain signal is decorative; a live demo fails on noisy signal with no recorded fallback; hardware queue; unsupported medical claims.

**Future of Money (Breez).** Must show (stated): a working app using the Breez SDK that addresses one of ten bounties, plus a write-up, as open source; "Every entry that meets Breez's bar wins a bounty", so it is threshold-based rather than a single winner. Patterns: (1) start from the Breez starter template for one bounty and adapt it; (2) add a send/receive payment step to an existing action in the app; (3) gate one feature behind a small payment. Extra work: about 4-8 h including 1-2 h for the write-up. Prerequisites: Breez SDK setup and any API key it needs (via the support channel), a public repo, the bounty list (not on the public site). Common failures: mocked payments; no write-up; closed source; not matching one of the ten bounties; not meeting an unpublished "bar".

**Best Beginner.** Eligibility is about the team, not the project: "teams where most members are first-timers", judged "on how far you came and what you learned, not on polish". Patterns (content-agnostic): (1) keep a short log of starting skills and what each member learned; (2) show progression (early commit versus final state); (3) have each member explain their part at the demo. Extra work: about 0.5-1 h. Prerequisites: team composition; verification method not stated (registration records "previous hackathons" [S4]). Common failures: team does not meet the "most members" condition; presenting polish instead of learning; not flagging the entry for this prize if opt-in is required (not stated).

**Capture the Flag.** Not a project track; flags found decide it ("Most flags wins"). No integration with a project is possible or needed. Cost: every hour spent here is an hour not spent building. Prerequisites: access to the CTF platform (not published), basic security tooling. Unknowns: team size, whether project teams may also play, tie-breaks.

**Beyond the Horizon (MSGC, NASA open data).** Must show: "an analysis, a map, a model, a game or a teaching tool" built on NASA open data, APIs or models. Patterns: (1) a feature that pulls a NASA open API feed relevant to the app's context; (2) a map or visualization layer over NASA Earth-observation imagery; (3) an analysis or open-model inference on a NASA dataset whose result drives something in the app. Extra work: about 1-3 h for an API-backed feature; 4-10 h for imagery analysis or foundation-model inference. Prerequisites: a free NASA API key; for heavier work, large downloads and possibly a GPU. Common failures: NASA content as decoration only; large tiles failing on venue Wi-Fi; shared demo-key rate limits; no clear link between the data and what the project does.

**Quantum Computing (Quantum Rings).** Must show: "a game, a visualizer or an algorithm demo" that runs quantum circuits, with the team able to "explain the quantum part in plain words". Patterns: (1) hand one small computation in the app to a circuit run on the Quantum Rings simulator; (2) an interactive view inside the app that explains the circuit and its results; (3) a mechanic driven by measurement outcomes. Extra work: about 3-6 h for a team new to quantum SDKs. Prerequisites: Quantum Rings account and license, SDK install, the virtual workshop. Common failures: unable to explain the quantum part; the circuit is trivial and unconnected to the product; using a different simulator; leaving license setup to the last hours.

**Best Use of Base44.** Must show: an app built with Base44 and "a live link people can actually use by demo time"; winners "chosen by community vote". Patterns: (1) build the whole app in Base44; (2) build one surface of a larger project (dashboard, onboarding, admin) in Base44, calling the project's own backend; (3) use Base44 for the user-facing prototype while custom logic lives elsewhere. Whether partial use qualifies is not stated. Extra work: about 1-4 h to a live app, plus effort to gather votes. Prerequisites: Base44 account; plan limits not stated. Common failures: no live link at demo time; voters blocked by login walls or mobile breakage; ignoring the vote; unknown voting mechanics.

**Best Use of SSOJet.** Must show: "Single sign-on and secure login with SSOJet" working in the project. Patterns: (1) make SSOJet the app's login (standard OIDC redirect flow); (2) add organization-level SSO for a tenant or team concept; (3) protect an admin area or API with the issued tokens. Extra work: about 1-3 h for a standard web login, more for multi-tenant setups. Prerequisites: SSOJet free-plan account, correct redirect URLs for wherever the app runs. Common failures: login not functioning in the demo; another auth provider doing the real work; redirect misconfiguration after deployment; sign-in with no purpose in the app.

**Code of Life (Seqera).** Must show: work using the Seqera Platform, Nextflow / nf-core pipelines or the AI Co-Scientist on the provided biology datasets (or an Eduomics extension), within "Research and education only: no medical advice, no real patient data". Patterns: (1) run a ready-made pipeline on a provided dataset and build an app or visualization on its outputs; (2) add or modify a pipeline step and document it; (3) wrap pipeline launch and results in a user interface. Extra work: about 4-10 h; steeper for teams with no biology background. Prerequisites: the track's team workspace (how to obtain it is not stated), Nextflow basics. Common failures: pipeline runs that do not finish in time; biology that is nominal; real patient data or medical advice (explicitly excluded); results that cannot be reproduced.

**Department of Computer Science Track.** Must show: "the most impressive piece of software, judged on what is under the hood" with "Clean architecture, smart algorithms and code that actually holds up"; open to "Any idea, any stack, in any track". Patterns (content-agnostic): (1) clear module boundaries and a README with an architecture overview; (2) at least one non-trivial algorithm or system component the team wrote and can explain; (3) tests, error handling and a readable commit history. Extra work: about 2-5 h of engineering hygiene spread over the event. Prerequisites: a public repo judges can read. Common failures: all logic is glue around third-party APIs; generated code the team cannot explain; undocumented repo; scholarship eligibility assumptions (not stated).

**Best Use of ElevenLabs.** Must show: the project uses ElevenLabs audio (text-to-speech, voice agents, speech-to-text, custom voices or sound effects) in a way that matters to it. Patterns: (1) spoken output for key content; (2) a conversational voice interface to the app's main function; (3) voice input for a hands-free flow. Extra work: about 1-2 h for speech output, 3-6 h for a conversational agent wired to app data. Prerequisites: ElevenLabs account and key; Creator plan free for a month (claim path not stated). Common failures: audio as a gimmick; voice demos failing in a loud hall; quota exhaustion; no recorded fallback.

**MLH: Build Your Hackathon A-Team with SpaceXSI.** A raffle about workflow, not product content. Qualification is fully stated: Cursor as the core coding agent, a Grok Bot automation in the workflow, both described in the project description, and opt-in at submission. Patterns: (1) develop in Cursor; (2) set up one Grok Bot automation in the team's workflow; (3) write two or three sentences about both in the description. Extra work: about 0.5-2 h. Prerequisites: Cursor and Grok/X access (X Premium promo via MLH login). Common failures: forgetting the opt-in; description omits one of the two tools.

**MLH: Best Use of Gemini API.** Must show: a feature powered by the Gemini API. Patterns: (1) summarize, classify or generate text for an existing feature; (2) multimodal input (image, audio, document) understanding; (3) an assistant with tool calls into the app. Extra work: about 1-3 h. Prerequisites: a Google AI Studio key. Common failures: a thin wrapper; another model doing the main work; quota limits.

**MLH: Best Use of Solana.** Must show: a project that uses Solana for something that benefits from fast, cheap transactions. Patterns: (1) record an app event or proof on-chain on a test network; (2) wallet-based payments or tipping; (3) token-based access or ownership. Extra work: about 3-8 h. Prerequisites: wallet, test-network funds, client libraries. Common failures: blockchain unrelated to the product; mock transactions; network or RPC trouble at demo.

**MLH: Best Use of Tiger Data.** Must show: "innovative, impactful, and performance-driven use" of Tiger Data (PostgreSQL extended for time-series and analytics). Patterns: (1) use it as the primary database; (2) store an event or metric stream and chart it in real time; (3) an analytics view over app activity. Extra work: about 1-3 h if the app already uses PostgreSQL. Prerequisites: a Tiger Data cloud account. Common failures: using it as plain PostgreSQL with no time-series feature; too little data to show anything.

**MLH: Best Use of Vultr.** Must show: the project running on, or using, Vultr cloud. Patterns: (1) deploy the backend or app on a Vultr instance; (2) use a Vultr GPU for inference; (3) use managed storage or database. Extra work: about 1-3 h. Prerequisites: Vultr account and credits (account verification may need a payment method). Common failures: static page only; not live at demo; account approval delays.

**MLH: DEV Writing Challenge.** Post-event: publish a write-up on DEV; monthly editorial selection on "technical substance, originality, clear storytelling, and community popularity". Extra work: about 1-3 h after the event. Common failures: not publishing through the challenge page; thin post.

**MLH: Best Use of MongoDB Atlas.** Must show: "a hack using MongoDB Atlas". Patterns: (1) Atlas as the primary datastore; (2) Atlas search or vector search for a find/recommend feature; (3) aggregation for analytics. Extra work: about 1-3 h. Prerequisites: Atlas account (free tier). Common failures: local MongoDB instead of Atlas; network allowlist problems on venue Wi-Fi; trivial use.

**MLH: Best Domain Name from GoDaddy Registry.** Must show: a domain registered through GoDaddy Registry (code via MLH login; one per account; claim by Nov 19, 2026). Patterns: (1) register a fitting name; (2) point it at the deployed project; (3) list it in the submission. Extra work: about 0.5-1 h plus DNS propagation. Common failures: code already used on the account; domain not pointed anywhere; DNS not live by demo.

## 6. Compatibility matrix (stated rules only)

Explicit statements found:
1. Department of Computer Science Track: "Any idea, any stack, in any track" [S2].
2. Capture the Flag: "Running all weekend alongside the hackathon" [S2]; "doesn't require shipping a prototype" [S9].
3. MLH categories: "limited to one (1) Application for each Category in each Event"; more than one application per event is allowed [S3]. The MLH event page's data model has a per-submission list of category ids (`submittedChallengeIds`) [S6], which is consistent with one project opting into several MLH categories, but no explicit statement was found.
4. Nothing on the site states a maximum number of tracks per team, whether a project must pick one primary track, or whether the overall "Hack The Nest" prize considers every project automatically.

| Combination in one submission | Stated? |
|---|---|
| CS Department Track + any other track | Yes, stated: "in any track" [S2] |
| Overall "Hack The Nest" + any themed/sponsor track | Not stated |
| One themed track (Future of Intelligence, Mind and Machine, Future of Money, Beyond the Horizon, Quantum Computing, Code of Life) + another themed track | Not stated |
| Themed track + a "Best Use of" track (Base44, SSOJet, ElevenLabs) | Not stated |
| Two or three "Best Use of" tracks together | Not stated |
| Best Beginner + any other track | Not stated (eligibility is by team composition, not project content) |
| Any organizer track + MLH categories | Not stated by the organizers; MLH terms do not prohibit it [S3] |
| Several MLH categories with one project | Not explicitly stated; one application per category [S3] |
| Capture the Flag + a project track (same people) | Not stated; CTF "runs alongside" and is not a project submission [S2][S9] |
| DEV Writing Challenge + anything | Separate post-event activity [S6]; combination rules not stated |
| Limit on number of tracks/categories per team | Not stated |

Structural constraints implied by the track texts (my reading, not a stated rule): Base44 requires the app, or at least the linked live app, to be built with Base44 [S2]; Future of Money requires the Breez SDK, a write-up and open source [S2]; Code of Life excludes real patient data and medical advice [S2]; the SpaceXSI raffle requires Cursor as the core coding agent [S6].

## 7. Unknowns, blocked hosts, and disagreements between sources

Not found on any page I could read:
- Official hour-by-hour schedule, hacking start/stop times, and the submission deadline.
- The submission platform for organizer tracks, the required submission contents (repo, video, slides), and how a team selects tracks. The MLH page showed submissions not open and no deadline at about 21:30 UTC on Nov 14 [S6]. No Devpost page for this event was found; no Discord link is on the public site.
- Judging process, judges and criteria for the organizers' own tracks (only the per-track phrases quoted above), and whether the MLH standard rules are adopted.
- Any rule on combining tracks or on a maximum number of tracks (section 6).
- Prizes for Future of Intelligence ("Coming soon") [S2].
- Breez bounty list, amounts and qualifying "bar"; Base44 community-vote mechanics; CTF platform, format and team size; how to claim Exa, Quantum Rings, SSOJet, ElevenLabs and Seqera access.
- The exact rule for under-18 participants (the privacy notice implies an EMU-enrollment question and a consent form, but the rule itself is on the sign-in-only registration form) [S4].
- Registration deadline or whether registration was still accepted during the event; travel reimbursement (no mention).
- Whether an IBM, Kawasaki Robotics or Perplexity challenge exists (none on the site).
- Contents of `/register`, `/account`, `/checkin` (sign-in required; not accessed).

Sources that disagree:
- **Capacity:** site "up to 500" [S1]; GDG page "up to 1,000 students" [S9]; EMU Today calendar "up to 500" [W6]; Eastern Echo (Nov) "around 1,000 registrations" [W1]; forum post "up to 600" [W5]. (W-sources are search summaries.)
- **End time:** MLH 9:00 PM UTC = 4:00 PM EST Sunday [S6]; GDG page 5:00 PM EST Sunday [S9]; Purdue announcement Sunday 4:00 PM [W4].
- **Start time:** MLH and GDG 9:00 AM EST Saturday [S6][S9]; Eastern Echo opening ceremony at 11 a.m. [W1].
- **Weekdays:** the search summary of the Eastern Echo article says "11 a.m. Friday to 4 p.m. Saturday" [W1], but Nov 14-15, 2026 are Saturday and Sunday, and the site says the g.tec workshop is "Saturday, 2 PM" [S2]. I could not open the article to see whether the error is the article's or the summary's.
- **Track count:** 14 entries on the site [S1] versus "eight prize tracks" plus extras [W1] versus "Four prize tracks are being revealed soon" [S9].
- **"Hardware track":** a Purdue CS announcement reportedly says "A hardware track runs alongside the software work" [W4] and MLH tags the event "Hardware" and lists "Digi-key Hardware Lab" [S6]; the official site has no track with that name (the EEG-hardware track is "Mind and Machine") [S2].
- **Eligibility:** site "college and high school students" [S1]; Purdue announcement reportedly adds "anyone who graduated within the past year" [W4]; MLH terms 18+ or minors with parental permission [S3].
- **Pre-event date:** GDG page says Saturday Nov 7, 2026 [S10]; an aggregator listing reportedly said Oct 29, 2026 [W7].
- **MLH contest terms validity:** the copy on the site covers a term ending June 30, 2026 [S3], before this event.
- **ElevenLabs prize:** site lists Scale/Pro plans [S2]; MLH's season page lists "Wireless Earbuds" for its own ElevenLabs category, which is not among this event's MLH categories [S6][S7].

Hosts and errors:
- Before the allowlist change, via the proxy, every one of these returned `curl: (56) CONNECT tunnel failed, response 403` (proxy note: "connect_rejected (the egress proxy refused the connection; a refusal most often means that the host is not allowed for this session)"): hackthenest.tech, www.mlh.com, hack.mlh.io, devpost.com, www.easternecho.com, today.emich.edu, gdg.community.dev, x.com, www.cs.purdue.edu, community.perplexity.ai, web.archive.org.
- The WebFetch tool failed with `getaddrinfo ENOTFOUND <host>` for hackthenest.tech, allai.events and gdg.community.dev, and still failed that way for hackthenest.tech after the allowlist change (curl worked).
- After the user-approved change, these were read directly: hackthenest.tech, www.mlh.com (hack.mlh.io/prizes redirects to www.mlh.com/events/prizes), gdg.community.dev. raw.githubusercontent.com was reachable without any change (HTTP 200).
- github.com: `https://github.com/` returned HTTP 400; the MLH policies page returned HTTP 403 with "GitHub access to this repository is not enabled for this session" (the same file was read from raw.githubusercontent.com instead).
- Still blocked and therefore known only through search-engine summaries (not verified against the pages): www.easternecho.com, today.emich.edu, www.cs.purdue.edu, community.perplexity.ai, x.com, allai.events, devpost.com. Not attempted: linktr.ee, Instagram, LinkedIn, TikTok, YouTube, Threads, Facebook (the organizers' socials, where late announcements such as schedule or submission links may live).

## Sources

Read directly:
- [S1] https://hackthenest.tech/ (home page: hero, About terminal, Tracks list, Sponsors, Partners, FAQ, Team, footer)
- [S2] https://hackthenest.tech/#tracks ("See track" panel data, read from the site's script https://hackthenest.tech/_next/static/chunks/2dkil34c7e6c6.js, deployment dpl_9L12S4GmZ4UPC1z8mQ8X23peVSto)
- [S3] https://hackthenest.tech/mlh/contest-terms
- [S4] https://hackthenest.tech/privacy (last updated October 18, 2026)
- [S5] https://hackthenest.tech/mlh/code-of-conduct
- [S6] https://www.mlh.com/events/hack-the-nest-96 and its eight `/challenges/<id>` pages
- [S7] https://www.mlh.com/events/prizes (target of https://hack.mlh.io/prizes)
- [S8] https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md (the rules referenced by [S3])
- [S9] https://gdg.community.dev/events/details/google-gdg-on-campus-eastern-michigan-university-presents-hack-the-nest/
- [S10] https://gdg.community.dev/events/details/google-gdg-on-campus-eastern-michigan-university-presents-hack-the-nest-pre-event-info-session-amp-build-with-ai/

Known only through search-engine summaries (hosts blocked; treat as unverified):
- [W1] https://www.easternecho.com/article/2026/11/what-to-know-about-the-first-ever-student-led-hackathon-at-emu-hack-the-nest
- [W2] https://www.easternecho.com/article/2026/10/eastern-students-launch-website-recruit-builders-for-november-hack-the-nest-hackathon
- [W3] https://today.emich.edu/story/story/13394
- [W4] https://www.cs.purdue.edu/corporate/announcements/hackthenest11.14_15.html
- [W5] https://community.perplexity.ai/t/hack-the-nest-at-emu-nov-14-15-who-should-i-talk-to-about-api-credits-for-student-hackers/6307
- [W6] https://today.emich.edu/calendar/2026/11/14/16746
- [W7] https://allai.events/event/hack-the-nest-pre-event-info-session--build-with-ai
- [W8] Unrelated event with the same name: https://hackthenest-2023.devpost.com/ , https://hack-the-nest-2025.devpost.com/ , https://hack-the-nest-v3.devpost.com/ , https://www.hackthenest.org/recap
