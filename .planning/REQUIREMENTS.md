# Requirements: Riverside AI Cold-Calling Agent

**Defined:** 2026-04-20
**Core Value:** A fully automated pipeline from raw podcast data to a completed, logged, outcome-classified sales call, with zero manual steps.

## v1 Requirements

Requirements for the assignment submission. Each maps to roadmap phases.

### Discovery

- [ ] **DISC-01**: System searches Podcast Index API with ICP filters (Business/Technology/Marketing categories, weekly/biweekly cadence, minimum episode count, recent activity)
- [ ] **DISC-02**: System parses RSS feeds to extract host name, episode metadata, show description, publish dates, and cadence
- [ ] **DISC-03**: System extracts podcast-specific personalization signals (recent episode topics, guest names, cadence trends) from RSS data

### Enrichment

- [ ] **ENRI-01**: System enriches each prospect via Apollo free tier (work email, company size, industry, firmographics)
- [ ] **ENRI-02**: System assembles a structured cheat sheet per prospect (all discovery + enrichment data in one bundle)

### Scoring

- [ ] **SCOR-01**: System applies hard filters to disqualify off-ICP prospects (company size outside 100-1000, missing contact info, inactive show, non-B2B)
- [ ] **SCOR-02**: System scores remaining prospects on weighted criteria (episode cadence, company size fit, data completeness, category match)
- [ ] **SCOR-03**: System cross-checks prospects against a skip list of known Riverside customers before calling
- [ ] **SCOR-04**: Scoring layer acts as the automated quality gate (no human review step between scoring and calling)

### Deep Enrichment (Phase 1.1 -- INSERTED)

- [ ] **DEEP-01**: System re-parses RSS feeds for call-ready prospects to extract last 3 episodes with title, description, and guest name
- [ ] **DEEP-02**: System extracts guest names from episode titles using regex heuristics (patterns: "with [Name]", "ft. [Name]", "featuring [Name]", "| [Name]")
- [ ] **DEEP-03**: System scrapes company homepage (meta description, og:description, or h1) to produce raw company text, with graceful failure (blank on error, no retries)
- [ ] **DEEP-04**: System generates podcast theme summary and refined company summary via local Ollama LLM (single combined call per prospect, zero API cost)
- [ ] **DEEP-05**: System rebuilds a richer cheat sheet for call-ready prospects incorporating episode details, company summary, and podcast themes
- [ ] **DEEP-06**: ProspectDict includes episode_details, company_summary, and podcast_themes fields; Airtable upload maps all three to columns
- [ ] **DEEP-07**: Pipeline runner includes deep_enrich step between score and upload; upload reads deep_enrich.json instead of score.json

### Call Context

- [ ] **CCTX-01**: System generates a custom opening line per prospect via LLM, referencing specific podcast data (recent episode, guest, topic)
- [ ] **CCTX-02**: System generates pain point hypotheses per prospect based on their current setup and company profile
- [ ] **CCTX-03**: System generates predicted objections per prospect based on their role, company size, and likely current tool
- [ ] **CCTX-04**: System generates a relevance hook per prospect tying their situation to a specific Riverside feature
- [ ] **CCTX-05**: Call context is a separate artifact from the cheat sheet (agent receives only the distilled context, never raw enrichment data)

### Voice Agent

- [ ] **VOIC-01**: Shared harness (system prompt) defines agent persona, Riverside value prop, tone, discovery question flow, and safety rules
- [ ] **VOIC-02**: Agent handles at least 5 common objections (not interested, already have a tool, too expensive, bad timing, not the right person)
- [ ] **VOIC-03**: Agent conducts discovery by asking about recording workflow, content output, and pain points
- [ ] **VOIC-04**: Agent follows defined exit paths (book meeting, send signup link, graceful goodbye, flag for follow-up)
- [ ] **VOIC-05**: Agent uses mid-call function calling to trigger meeting booking (Calendly link) when prospect shows interest
- [ ] **VOIC-06**: Agent uses mid-call function calling to send Riverside signup link when appropriate
- [ ] **VOIC-07**: Harness stays identical across all calls; only the per-call context changes

### Outcome Handling

- [ ] **OUTC-01**: System classifies each call outcome via LLM or Vapi analysisPlan (booked, interested, not-a-fit, voicemail, no-answer, do-not-call)
- [ ] **OUTC-02**: System updates Airtable row with outcome classification, call notes, and timestamp after each call
- [ ] **OUTC-03**: System fires at least one real follow-up action (Calendly confirmation email on "booked" or "interested" outcome)

### Data & Storage

- [ ] **DATA-01**: Airtable base stores all prospects with enrichment fields, scores, call status, and outcomes
- [ ] **DATA-02**: Airtable base is shareable via link so reviewer can inspect populated data without running code

### Demo & Write-up

- [ ] **DEMO-01**: 2-3 recorded demo calls covering distinct scenarios (interested prospect, objection handling, disqualification/dead-end)
- [ ] **DEMO-02**: One demo call uses a hand-written webinar-prospect cheat sheet to prove architecture generalizes beyond podcast ICP
- [ ] **DEMO-03**: Write-up covers system architecture (description or diagram)
- [ ] **DEMO-04**: Write-up defends ICP choice with evidence
- [ ] **DEMO-05**: Write-up explains prompt and conversation design decisions
- [ ] **DEMO-06**: Write-up includes "what I intentionally did not build" with rationale for each item
- [ ] **DEMO-07**: Write-up includes "how I would take this further" (webinar pipeline, CRM integration, quality classifier, A/B testing, etc.)
- [ ] **DEMO-08**: Write-up describes path to 100+ calls/day (scalability narrative)

## v2 Requirements

Deferred to future. Tracked but not in current scope.

### Integrations

- **INTG-01**: Route outcomes into HubSpot (contact creation, deal stage, next-step sync)
- **INTG-02**: Upload Vapi recordings to Gong for conversation intelligence
- **INTG-03**: Warehouse call data in Snowflake for analytics

### Advanced Automation

- **AUTO-01**: Multi-step follow-up sequences (email drip on "interested," retry on "no-answer" at +48h)
- **AUTO-02**: Parallel dialing for production volume
- **AUTO-03**: A/B testing framework for openers and pitch variants
- **AUTO-04**: Voicemail drop (detect voicemail, leave personalized message)

### Intelligence

- **INTL-01**: Automated audio quality classifier to detect Zoom-quality recordings
- **INTL-02**: Programmatic Riverside-customer detector to replace hand-curated skip list
- **INTL-03**: Per-prospect tone override (adjust communication style by persona type)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Webinar discovery pipeline | No clean single API. Strategic signal captured via write-up + one hand-written demo cheat sheet. |
| CRM/Gong/Snowflake integration | 4-8 hrs on auth and field mapping. Reviewer evaluates the concept, not the plumbing. Described in write-up. |
| Full outcome automation (all 6 paths) | 6-12 hrs. Only booked/interested path matters for demo. Rest described in write-up. |
| TCPA/compliance automation | Necessary in production, irrelevant for demo using test phone numbers. Noted in write-up. |
| Lead routing to human closer | No human closer to route to in a demo. Described in write-up. |
| Real-time rep coaching / call whisper | Different product entirely (Gong-style). Out of scope. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DISC-01 | Phase 1 | Pending |
| DISC-02 | Phase 1 | Pending |
| DISC-03 | Phase 1 | Pending |
| ENRI-01 | Phase 1 | Pending |
| ENRI-02 | Phase 1 | Pending |
| SCOR-01 | Phase 1 | Pending |
| SCOR-02 | Phase 1 | Pending |
| SCOR-03 | Phase 1 | Pending |
| SCOR-04 | Phase 1 | Pending |
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DEEP-01 | Phase 1.1 | Pending |
| DEEP-02 | Phase 1.1 | Pending |
| DEEP-03 | Phase 1.1 | Pending |
| DEEP-04 | Phase 1.1 | Pending |
| DEEP-05 | Phase 1.1 | Pending |
| DEEP-06 | Phase 1.1 | Pending |
| DEEP-07 | Phase 1.1 | Pending |
| CCTX-01 | Phase 2 | Pending |
| CCTX-02 | Phase 2 | Pending |
| CCTX-03 | Phase 2 | Pending |
| CCTX-04 | Phase 2 | Pending |
| CCTX-05 | Phase 2 | Pending |
| VOIC-01 | Phase 3 | Pending |
| VOIC-02 | Phase 3 | Pending |
| VOIC-03 | Phase 3 | Pending |
| VOIC-04 | Phase 3 | Pending |
| VOIC-05 | Phase 3 | Pending |
| VOIC-06 | Phase 3 | Pending |
| VOIC-07 | Phase 3 | Pending |
| OUTC-01 | Phase 3 | Pending |
| OUTC-02 | Phase 3 | Pending |
| OUTC-03 | Phase 3 | Pending |
| DEMO-01 | Phase 4 | Pending |
| DEMO-02 | Phase 4 | Pending |
| DEMO-03 | Phase 4 | Pending |
| DEMO-04 | Phase 4 | Pending |
| DEMO-05 | Phase 4 | Pending |
| DEMO-06 | Phase 4 | Pending |
| DEMO-07 | Phase 4 | Pending |
| DEMO-08 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 41 total (34 original + 7 DEEP-xx added for Phase 1.1)
- Mapped to phases: 41
- Unmapped: 0

---
*Requirements defined: 2026-04-20*
*Last updated: 2026-04-22 after Phase 1.1 planning*
