# MLH categories

Eight categories "run and paid for by Major League Hacking" (MLH), entered through the MLH event page (§3.8 of the [report](../sources/2026-11-14-hack-the-nest-research-report.md)). Rule for all of them: one application per category per event; a team may submit more than one application. No cap on the number of categories is stated, and whether one project may enter several is not explicitly stated (§6). The official site lists only the names; prizes and requirements are from the MLH page.

## Official facts

| Category | Prize | Qualifies by |
|---|---|---|
| Build Your Hackathon A-Team with SpaceXSI | Mechanical keyboard each (a raffle) | "Use Cursor as your core AI coding agent"; "Integrate a Grok Bot automation into your workflow"; describe both in the project description; opt in to the raffle at submission |
| Best Use of Gemini API | MLH swag kits | Build an AI-powered app with the Google Gemini API |
| Best Use of Solana | Hardware wallets each | Use Solana's "blazing fast execution and near-zero transaction costs": a game, social app, or consumer product; trading or lending; supply chain, identity, or payments |
| Best Use of Tiger Data | Stream Deck Mini | "the most innovative, impactful, and performance-driven use of Tiger Data" (PostgreSQL extended for real-time, time-series, and analytics) |
| Best Use of Vultr | Assorted prizes | Run the project on Vultr cloud (compute, GPUs); free credits on sign-up |
| DEV Writing Challenge | $100 | After the event: publish what you built on DEV. Monthly selection on "technical substance, originality, clear storytelling, and community popularity" |
| Best Use of MongoDB Atlas | M5Stack IoT kit each | "Build a hack using MongoDB Atlas"; $50 student credit or the free tier |
| Best Domain Name from GoDaddy Registry | Digital gift card | Register a domain through GoDaddy Registry with the MLH code (one per account; claim by Nov 19, 2026) |

## Analysis (not official, §5)

The reader agent's neutral view of how an arbitrary project could qualify. Hours are rough estimates.

| Category | Ways in | Extra work | Common failures |
|---|---|---|---|
| SpaceXSI raffle | Develop in Cursor; set up one Grok Bot automation in the team's workflow; write two or three sentences about both | 0.5–2 h; needs Cursor and Grok access | Forgetting the opt-in; description omits one of the two tools |
| Gemini API | Summarize, classify, or generate text for an existing feature; understand image, audio, or document input; an assistant with tool calls into the app | 1–3 h; needs a Google AI Studio key | Thin wrapper; another model doing the main work; quota limits |
| Solana | Record an app event or proof on a test network; wallet-based payments or tipping; token-based access or ownership | 3–8 h; needs a wallet, test funds, client libraries | Blockchain unrelated to the product; mock transactions; network trouble at demo |
| Tiger Data | Use it as the primary database; store an event or metric stream and chart it live; an analytics view over app activity | 1–3 h if the app already uses PostgreSQL; needs a cloud account | Used as plain PostgreSQL with no time-series feature; too little data to show anything |
| Vultr | Deploy the backend or app on an instance; use a GPU for inference; use managed storage or a database | 1–3 h; account may need a payment method | Static page only; not live at demo; account approval delays |
| DEV Writing Challenge | Publish a write-up through the challenge page | 1–3 h after the event | Not publishing through the challenge page; thin post |
| MongoDB Atlas | Atlas as the primary datastore; Atlas search or vector search for a find or recommend feature; aggregation for analytics | 1–3 h; needs an Atlas account | Local MongoDB instead of Atlas; network allowlist problems on venue Wi-Fi; trivial use |
| GoDaddy Registry domain | Register a fitting name; point it at the deployed project; list it in the submission | 0.5–1 h plus DNS propagation | Code already used on the account; domain not pointed anywhere; DNS not live by demo |
