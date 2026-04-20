# Project Research Summary

**Project:** Riverside AI Cold-Calling Agent
**Domain:** AI-powered outbound sales pipeline with voice agent
**Researched:** 2026-04-20
**Confidence:** MEDIUM-HIGH

## Executive Summary

This is a two-part system: a data pipeline that discovers, enriches, scores, and prepares prospect call packages, and a real-time voice agent that places personalized outbound calls. The right way to build this is with a hard separation between build time (pipeline, runs once per batch) and call time (voice agent, runs per call with real-time constraints). Vapi is the only platform with clean Claude support, a Python SDK, and a dynamic variable injection mechanism that makes harness + per-call context separation straightforward. A single Python pipeline script with no orchestration framework is the correct approach at 3-day demo scale.

The recommended architecture threads through Podcast Index API to find B2B SaaS podcast hosts, RSS parsing for episode metadata and host identity, Apollo enrichment for firmographics and contact info, a scoring gate that disqualifies non-ICP prospects before any calls go out, an LLM step (Claude Sonnet) that generates personalized call context from a structured cheat sheet, and finally Vapi for the actual voice calls. The key architectural move is that the cheat sheet never reaches the voice agent. The LLM distills it into a compact call context block (opener, pain hypotheses, predicted objections, hook) that gets injected into a shared assistant harness via Vapi variableValues. This separation is the strategic demonstration the reviewer is looking for.

The primary risks are technical, not architectural. Vapi default turn detection adds 1.5 seconds of dead air unless explicitly disabled. The harness prompt must be written for speech, not text, or the demo sounds like a press release. Free tier Vapi telephony is US-only, which matters because Shawn is in Tel Aviv. The webhook server for mid-call function calls has a hard 7.5-second response deadline. All of these are known, preventable, and must be handled on day 1 of Vapi setup.

---

## Key Findings

### Recommended Stack

The stack is lean and appropriate for a 3-day demo build. Every component is either free at demo scale or within the $10-15 budget. Vapi $10 free credit covers 40-60 minutes of demo calls. Apollo free tier handles 30-100 enrichments. Airtable free tier holds up to 1,000 records and gives the reviewer a live, inspectable database without any setup.

**Core technologies:**
- Vapi (pay-as-you-go, ~$0.15-0.25/min all-in): voice platform, STT/TTS/telephony, Claude support, dynamic variable injection, mid-call tool calling
- Claude Sonnet (claude-sonnet-4-20250514): LLM for both pipeline call context generation and voice agent real-time conversation; Sonnet tier balances quality vs. cost correctly
- Podcast Index API (free, no published rate cap): podcast discovery by category and recency; genuinely free unlike Listen Notes (300 req/mo free cap)
- feedparser 6.0.12: RSS parsing for host identity, episode metadata, iTunes extension tags; the standard library for this job
- Apollo.io free tier: person and org enrichment via /v1/people/match and /v1/organizations/enrich; 10K email credits/month, sufficient for 30-100 prospects
- pyairtable 3.3.0: Airtable client with automatic 429 retry and batch_upsert() support
- Python 3.11+ with plain pipeline.py: no LangGraph, no n8n; a sequential ETL (extract, transform, load) pipeline is more auditable and faster to build than adding a framework

**What not to use:** Bland AI (no free trial), Retell AI (no meaningful advantage over Vapi here), Listen Notes (capped), Hunter.io (25 searches/mo free tier), LangGraph or n8n (framework overhead for a linear pipeline), SQLite or JSON files (reviewer cannot inspect without running code), Postgres (overkill for 30-100 records).

### Expected Features

**Must have (table stakes, no exceptions):**
- ICP-filtered prospect list via Podcast Index category, cadence, and recency filters
- Contact enrichment (name, email, company size) via Apollo
- Hard-filter disqualification gate before any calls go out
- Skip/DNC list cross-check
- Shared system prompt (harness: persona, pitch, rules, objection handling, exit paths)
- Per-call context injection (opener, pain hypotheses, objection prep, relevance hook)
- Natural-sounding voice with sub-second response latency (Vapi platform handles this)
- Basic objection handling for 3-5 common objections
- Call outcome classification (booked, interested, not-a-fit, voicemail, no-answer, DNC)
- Persistent Airtable database with call status, visible to reviewer without running code
- 2-3 recorded demo calls covering distinct outcomes

**Should have (differentiators with high signal-to-effort ratio):**
- Harness + call context architecture with clean separation (this IS the strategic demonstration)
- LLM-generated call context from structured cheat sheet (shows AI used correctly, not as a crutch)
- Mid-call function calling for meeting booking and signup link delivery (proves the agent transacts, not just talks)
- Podcast-specific personalization signals from RSS (episode topics, guest names, cadence trends)
- One webinar demo call using a hand-written cheat sheet (proves architecture generalizes without building a second pipeline)

**Defer to write-up description only (anti-features):**
- Automated audio/video quality classifier (manual spot-check covers demo scale)
- CRM integration (Gong, Salesforce, HubSpot)
- Multi-step follow-up sequences
- Full automation of all 6 outcome paths (build one real action, describe the rest)
- Parallel dialing, A/B testing, TCPA compliance automation, lead routing to human closer

### Architecture Approach

The system has two hard runtime phases separated by Airtable as the state store. Build time is a linear Python pipeline. Call time reads from Airtable and fires Vapi calls with pre-generated context already embedded. Nothing from build time touches call time except via Airtable. The cheat sheet never reaches the voice agent; it is an intermediate artifact that the LLM distills into a compact call context block.

**Major components:**
1. Discovery (Podcast Index API): finds B2B SaaS podcast shows by category, recency, episode cadence
2. RSS Parser (feedparser): extracts host identity, episode metadata, iTunes extension tags
3. Apollo Enrichment: adds company size, employee count, work email, title
4. Scoring + Filter Gate: disqualifies non-ICP prospects; null company size is hard disqualification
5. Cheat Sheet Builder: assembles structured data bundle per prospect; never sent to the agent
6. LLM Call Context Generator (Claude Sonnet): one call per prospect; outputs opener, pain hypotheses, predicted objections, relevance hook
7. Airtable: persistent store, status transitions (enriched, ready, called, outcome written)
8. Call Runner: reads Airtable queue, assembles Vapi payload with assistantOverrides.variableValues
9. Vapi Platform: owns real-time audio, STT, LLM, TTS, turn-taking, tool dispatch
10. Tool Endpoints (FastAPI or Flask via ngrok/Railway): handle book_meeting and send_signup_link within the 7.5-second deadline
11. Post-Call Classifier: Vapi built-in analysisPlan with structuredDataSchema; writes outcome to Airtable

### Critical Pitfalls

1. **Vapi formatTurns default adds 1.5 seconds of dead air.** Set formatTurns: false in the assistant startSpeakingPlan before any test call. Target total turn latency under 1200ms.
2. **Prompt written for chat, not speech.** Read every agent utterance aloud. No bullet points, no markdown, no digit-form numbers, max 2-3 sentences per turn.
3. **Vapi free tier is US-only for outbound (10 calls/day cap).** Shawn is in Tel Aviv. Import a Twilio number on day 1. Budget $1-2.
4. **Webhook server for tool calls has a hard 7.5-second response deadline.** Use a pre-warmed Railway or Render instance. Test tunnel round-trip before demo recording.
5. **Vapi dashboard changes silently revert about 50% of the time.** Configure all assistants via SDK or API only. Treat the dashboard as read-only.
6. **Apollo free tier may return null company size for smaller companies.** Treat null as hard disqualification in the scoring layer.
7. **Voicemail detection false positives will hang up on live humans during demo recording.** For known-live demo numbers, disable voicemail detection entirely.

---

## Implications for Roadmap

The dependency chain is fixed and non-negotiable. Each phase consumes the output of the previous one.

### Phase 1: Data Foundation
**Rationale:** Nothing downstream works without clean prospect data. Validate discovery and RSS parsing before writing any enrichment or scoring code.
**Delivers:** Airtable schema, Podcast Index search results, parsed RSS records with host name, episode metadata, cadence, recency
**Addresses:** ICP-filtered prospect list (table stakes); hard filter on lastPublishTime within 60 days (avoids inactive shows)
**Avoids:** Discovering enrichment is broken after spending time on scoring logic
**Research flag:** Standard patterns. No additional research needed.

### Phase 2: Enrichment and Scoring
**Rationale:** Contact data and company firmographics are required before scoring can run. Scoring gate must be validated before call context generation starts.
**Delivers:** Apollo-enriched prospects in Airtable; scored and filtered call list; skip/DNC list applied
**Addresses:** Contact enrichment, hard-filter disqualification, DNC list (all table stakes)
**Avoids:** Null company size passing the filter (treat null as hard disqualification)
**Research flag:** Apollo free tier credit behavior and data completeness for companies under 200 employees is underdocumented. Validate with a small batch of 5-10 records before running the full pipeline.

### Phase 3: Cheat Sheet and Call Context Generation
**Rationale:** The cheat sheet is the dependency bridge between enriched data and the voice agent. Call context must be pre-generated and stored in Airtable before the call runner can use it.
**Delivers:** Per-prospect cheat sheet (structured dict) and LLM-generated call context block stored in Airtable; status updated to ready
**Addresses:** Per-call context injection (table stakes), LLM-generated call context from cheat sheet (differentiator), podcast-specific personalization signals (differentiator)
**Avoids:** Live call context generation at call time that adds 2-5 seconds of dead air
**Research flag:** Validate that Claude Sonnet output stays under ~300 tokens and hits the intended format. Iterate on the generation prompt during this phase.

### Phase 4: Voice Agent
**Rationale:** The voice agent is the last component. All upstream data must be validated before call setup.
**Delivers:** Working Vapi assistant (harness prompt with variableValues), call runner, mid-call tool endpoints, outcome classification via analysisPlan, Airtable outcome writes
**Addresses:** Shared system prompt, objection handling, mid-call function calling (differentiator), call outcome classification (all table stakes or differentiators)
**Avoids:** Dead air from formatTurns default, chat-style prompt, US-only telephony issue, webhook timeout, Vapi dashboard revert, endpointing cutoffs
**Research flag:** Needs hands-on testing. Vapi latency configuration requires iteration against real calls. Allocate a dedicated test session before demo recording.

### Phase 5: Demos and Write-up
**Rationale:** The demos are the submission artifact. The write-up is graded as heavily as the code.
**Delivers:** 2-3 recorded demo calls (interested, objection, voicemail scenarios), one webinar call using a hand-written cheat sheet, src/README.md
**Addresses:** Demo artifacts (table stakes), generalizable architecture demonstration (differentiator)
**Avoids:** Voicemail detection misfires on live demo numbers
**Research flag:** No additional research needed.

### Phase Ordering Rationale

- Discovery before enrichment: no point enriching what you cannot find.
- Enrichment before scoring: the scoring formula requires company size and firmographics.
- Scoring before call context: non-ICP prospects must be out of the queue before context is generated.
- Call context before voice agent: the call runner reads call_context from Airtable; if it is not there, the call has no personalization.
- Voice agent before demos: you need working calls to record demos.
- Parallel opportunities: Airtable schema can be set up alongside API wrappers in Phase 1. The harness system prompt can be drafted during Phase 3 since it does not depend on specific call context outputs.

### Research Flags

Needs hands-on validation during execution:
- **Phase 2:** Apollo free tier data completeness for companies under 200 employees. Run a small test batch early.
- **Phase 4:** Vapi latency configuration (formatTurns, endpointing, voicemail detection). Docs alone are insufficient. Allocate a real test session.

Standard patterns, skip additional research:
- **Phase 1:** Podcast Index and feedparser are well-documented.
- **Phase 3:** Claude Sonnet structured output generation is Shawn native stack. Prompt iteration is expected but not a research problem.
- **Phase 5:** Demos follow from working Phase 4. Write-up structure is defined in CLAUDE.md.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Vapi pricing is a moving target. Apollo free tier credit limits inconsistently documented. All other components verified via official docs and PyPI. |
| Features | HIGH | Clear signal from multiple sources. Table stakes, differentiator, and anti-feature split is well-grounded for this build context. |
| Architecture | HIGH | Vapi dynamic variables, tool calling, and webhook patterns verified directly in official docs. Build-time vs. call-time separation is the correct pattern and well-corroborated. |
| Pitfalls | HIGH | Most pitfalls verified from official Vapi docs with specific configuration values (255ms endpointing, 7.5s webhook deadline, formatTurns default behavior). |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Apollo free tier data completeness:** Underdocumented for companies under 200 employees. Validate early in Phase 2. Mitigation (null = disqualify) is already in the scoring logic.
- **Vapi per-minute cost:** The $0.15-0.25/min range is an estimate. Actual cost depends on TTS provider selected. The $10 free credit provides sufficient buffer at demo scale.
- **Twilio import for international calling:** Required given Shawn Tel Aviv location. Standard per Vapi docs. Handle on day 1 and budget $1-2.

---

## Sources

### Primary (HIGH confidence)
- Vapi dynamic variables: https://docs.vapi.ai/assistants/dynamic-variables
- Vapi outbound calling: https://docs.vapi.ai/calls/outbound-calling
- Vapi tool calling: https://docs.vapi.ai/customization/tool-calling-integration
- Vapi call analysis / analysisPlan: https://docs.vapi.ai/assistants/call-analysis
- Vapi free telephony: https://docs.vapi.ai/free-telephony
- Vapi Claude 4 model support: https://vapi.ai/blog/claude-4-models-now-available-in-vapi
- Anthropic model pricing: https://platform.claude.com/docs/en/about-claude/pricing
- feedparser docs: https://feedparser.readthedocs.io/en/stable/introduction.html
- Apollo people enrichment API: https://docs.apollo.io/reference/people-enrichment
- pyairtable PyPI v3.3.0: https://pypi.org/project/pyairtable/
- Airtable rate limits: https://airtable.com/developers/web/api/rate-limits

### Secondary (MEDIUM confidence)
- Vapi pricing hidden costs: https://blog.dograh.com/vapi-pricing-breakdown-2025-plans-hidden-costs-what-to-expect/
- AssemblyAI lowest latency voice agent: https://www.assemblyai.com/blog/how-to-build-lowest-latency-voice-agent-vapi
- Podcast Index API docs: https://podcastindex-org.github.io/docs-api/
- python-podcastindex PyPI: https://pypi.org/project/python-podcastindex/
- Apollo API pricing: https://docs.apollo.io/docs/api-pricing
- Bland vs Vapi vs Retell: https://www.whitespacesolutions.ai/content/bland-ai-vs-vapi-vs-retell-comparison

### Tertiary (MEDIUM-LOW confidence)
- AI cold calling guides (Synthflow, AutoInterviewAI, Reply.io): feature landscape validation only, not technical specs
- Voice AI architecture patterns (Bluejay, ElevenLabs): corroborates Vapi-specific patterns, not primary source

---
*Research completed: 2026-04-20*
*Ready for roadmap: yes*
