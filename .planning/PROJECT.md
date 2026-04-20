# Riverside AI Cold-Calling Agent

## What This Is

An end-to-end AI-powered outbound sales system for Riverside.fm prospects. It automatically discovers B2B SaaS companies with active podcasts, enriches and scores them, generates personalized call context, and places cold calls via a voice AI agent. Built as Part 2 of Riverside's GTM Engineer home assignment.

This is a repeatable GTM function, not a one-off cold-caller. The call agent is one node in a larger pipeline that handles everything from prospect discovery to post-call follow-up.

## Core Value

A fully automated pipeline from raw podcast data to a completed, logged, outcome-classified sales call, with zero manual steps between "run the pipeline" and "calls go out."

## Requirements

### Validated

(None yet, ship to validate)

### Active

- [ ] Automated podcast discovery via Podcast Index API with ICP filters (category, cadence, recency)
- [ ] RSS feed parsing for host name, episode metadata, show details
- [ ] Contact and company enrichment via Apollo free tier (email, company size, firmographics)
- [ ] Automated scoring and hard-filter disqualification (company size, cadence, geography, missing data)
- [ ] Skip-list cross-check against known Riverside customers
- [ ] Per-prospect cheat sheet assembly (structured data bundle from pipeline)
- [ ] LLM-generated call context from cheat sheet (custom opener, pain point hypotheses, predicted objections, relevance hooks)
- [ ] Shared voice agent harness (system prompt: persona, Riverside pitch, tone, discovery flow, objection handling, exit paths, safety rules)
- [ ] Voice agent receives harness + per-call context, places call via Vapi or similar platform
- [ ] Mid-call function-calling (book meeting via Calendly link, send signup link)
- [ ] Post-call outcome classification via LLM (booked, interested, not-a-fit, voicemail, no-answer, do-not-call)
- [ ] Airtable as prospect database (enrichment, scores, call status, outcomes visible to reviewer)
- [ ] 2-3 recorded demo calls covering different scenarios (interested prospect, objection handling, disqualification)
- [ ] One demo call using hand-written webinar prospect cheat sheet (proves architecture generalizes)
- [ ] Write-up: architecture, ICP defense, prompt design, "what I didn't build," "how I'd take this further," path to 100+/day

### Out of Scope

- Automated audio/video quality classifier: 4-6 hrs to build, 30 min of manual YouTube review handles the same job at demo scale
- Programmatic Riverside-customer detector: hand-curated skip list covers 20-30 prospects. Automation is brittle and premature at this volume
- Webinar enrichment pipeline: no clean single API for webinar discovery. Strategic signal captured via write-up ("what I'd build next") and one hand-written demo cheat sheet
- CRM/Gong/Snowflake integration: write-up describes how outcomes route into Riverside's stack, but no actual integration built
- Multi-step follow-up sequences: write-up describes retry scheduling and drip campaigns, not built
- Full outcome handling automation: only simple classification + Airtable update + maybe one real follow-up action (Calendly email). Write-up describes the full version

## Context

**Assignment**: Riverside.fm GTM Engineer home assignment, Part 2. Due Thursday 2026-04-23, 09:00 IDT. ~3 working days.

**ICP**: Mid-market B2B SaaS companies (100-1,000 employees) running an active weekly or biweekly podcast. Target the person in a dedicated podcast role (Head of Podcasts, Podcast Producer, Content Lead). Pitch angle is "switch from Zoom/Squadcast to Riverside," not "start a podcast."

**Reviewer context**: Mattan (hiring manager) said twice he wants a "builder AND a strategic thinker." The brief grades four axes equally: Agentic Thinking, Technical Execution, Scalability, Business Context. Creativity and original thinking are explicitly valued.

**Riverside's current position**: March 2026 product launches (Content Planner, Editor Role, Webinar data study) signal a pivot toward webinars and mid-market teams. Our write-up references this as "what I'd build next" to show we read their positioning.

**AI usage philosophy**: AI only where it adds value that deterministic code can't. Two AI touchpoints: (1) generating the creative call context from structured data, (2) the voice agent conversation itself, and (3) post-call transcript classification. Everything else is data plumbing, APIs, and code.

**Architecture model**: Harness + call context. The harness (shared system prompt) defines agent behavior, stays identical across every call. The call context (generated per prospect) provides personalized information. The cheat sheet is an intermediate build-time artifact that feeds the LLM call which produces the call context. Clean separation: pipeline generates cheat sheets, LLM produces call contexts, voice agent consumes harness + call context at runtime.

## Constraints

- **Timeline**: ~3 working days (Mon-Wed), assignment due Thursday 09:00 IDT
- **Budget**: $10-15 max for paid APIs. Free tiers wherever possible (Podcast Index free, Apollo free, Vapi free credits)
- **Demo calls**: test numbers only (Shawn's phone, friend's phone), not real prospects. Legal/TCPA compliance.
- **Airtable**: free tier, 1,000 record cap. Fine for 30-100 prospects at demo scale.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Podcast ICP over webinar ICP | Listen Notes/Podcast Index + Apollo = clean automated pipeline. Webinar discovery has no single clean API, costs 10+ hrs. Webinar signal captured in write-up + one hand-written demo. | -- Pending |
| Podcast Index API over Listen Notes | Free, unlimited requests, returns RSS URLs directly. Listen Notes free tier works (300 req/mo) but Podcast Index has no cap. | -- Pending |
| Apollo free tier for enrichment | 10K email credits on work-email signup, company size filters, $0. Sufficient for 30-100 prospects. | -- Pending |
| Airtable over SQLite/JSON | Reviewer clicks a link and sees populated data. Zero setup on their end. Rate limits irrelevant at demo scale. | -- Pending |
| Harness + call context architecture | Consistent agent behavior (harness never changes) + personalized calls (call context varies). Cheat sheet is intermediate, not what the agent sees. | -- Pending |
| AI only at 3 touchpoints | Call context generation, voice conversation, post-call classification. Everything else is deterministic code. Cheaper, faster, more debuggable. | -- Pending |
| Simple outcome handling, strategic write-up | LLM classifies transcript, updates Airtable, maybe one real follow-up action. Write-up describes full automation. Avoids burning hours on plumbing the reviewer won't see. | -- Pending |
| Fully automated pipeline, no manual steps | Brief grades Scalability. "Human reviews list before calls" breaks the 100+/day story. Scoring layer IS the quality gate. | -- Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason
2. Requirements validated? Move to Validated with phase reference
3. New requirements emerged? Add to Active
4. Decisions to log? Add to Key Decisions
5. "What This Is" still accurate? Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check, still the right priority?
3. Audit Out of Scope, reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-20 after initialization*
