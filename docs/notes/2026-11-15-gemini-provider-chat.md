---
source: docs/sources/2026-11-15-gemini-provider-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [Q11, Q20]
---

# Gemini provider (chat messages)

## Summary

A team member asked for the real AI to be implemented in the dashboard, on a separate branch, to see how it works. Earlier in the same chat, tests on that team member's laptop showed that Gemini answers through Vertex AI with the laptop's Google login and no API key, for model `gemini-3.8-flash` at location `global`.

## Key points

- (§ Request) Implement the AI in the dashboard (`src/website/`), on a different branch, and see how it works. Report anything that is missing.
- (§ Terminal tests, test 2) `gemini-3.8-flash` at location `global` answered a one-sentence request through Vertex AI (`google-genai` package, `vertexai=True`).
- (§ Terminal tests, test 1) The same model at location `us-central1` returned 404 NOT_FOUND.
- (§ Terminal tests, test 2) The pasted output has one line. What the other five models and `us-central1` returned in that run is not in the source.
- (§ Terminal tests) Sign-in was the laptop's Google login (Application Default Credentials). No API key was used.
- (§ API keys) When the team member tried to create an API key for the project, the Google Cloud console said API keys are disallowed and pointed to ADC.
- (§ Who runs it) One team member runs the AI calls on their own laptop.

## Relevance

Gives Q11 a first candidate that is known to answer: Gemini (`gemini-3.8-flash`, location `global`) through Vertex AI. It is being tried, not decided. It also changes the question in `2026-11-14-dashboard-changes-chat.md` about where a provider's API key comes from: on this path there is no key, and the sign-in is set up outside the app (Q20).

## Open questions

- Is Gemini through Vertex AI the provider we keep (Q11)? It has only answered a one-sentence text request so far; an analysis with PDFs has not been sent.
- How does the app authenticate, and where is that set up (Q20)? `overview.md` and `architecture.md` still describe an API key set at runtime.
- How long does a real analysis take, and how large a request does Google accept? Neither has been measured.

## Actions

- [x] `src/website/ai.py`: Gemini through Vertex AI as a second provider next to the Mock; the provider is chosen in Settings (dev mode)
- [x] `docs/functions.md`: entries for `ai.py`, the provider functions in `main.py`, and `loadAi` / `renderAi`
- [x] `docs/open-questions.md`: Q11 lists Gemini as the candidate being tried; added Q20
- [x] `src/website/README.md`: AI provider section with the set-up commands
- [ ] Try it on the laptop with the real Gemini: Test connection, then one analysis of a short range
