# Roadmap: Riverside AI Cold-Calling Agent

## Overview

Four phases that mirror the system's dependency chain. Phase 1 builds the data pipeline that populates Airtable with scored, enriched prospects. Phase 2 generates personalized call context from those prospects. Phase 3 stands up the voice agent, wires in mid-call tooling, and handles post-call classification. Phase 4 records the demo calls and writes the submission document. Nothing in a later phase can work without the earlier phases being solid, so the order is non-negotiable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Prospect Pipeline** - Discover, enrich, score, and store prospects in Airtable
- [x] **Phase 1.1: Deep Enrichment** - Episode content, company about pages, podcast pattern analysis (INSERTED)
- [ ] **Phase 2: Call Context Generation** - Generate personalized call context from cheat sheets via LLM
- [ ] **Phase 3: Voice Agent and Outcome Handling** - Build Vapi agent, wire tooling, classify and store outcomes
- [ ] **Phase 4: Demos and Write-up** - Record demo calls and write the submission document

## Phase Details

### Phase 1: Prospect Pipeline
**Goal**: Airtable is populated with ICP-qualified, enriched prospects ready for call context generation
**Depends on**: Nothing (first phase)
**Requirements**: DISC-01, DISC-02, DISC-03, ENRI-01, ENRI-02, SCOR-01, SCOR-02, SCOR-03, SCOR-04, DATA-01, DATA-02
**Success Criteria** (what must be TRUE):
  1. Running the pipeline script produces a populated Airtable base with at least 10 enriched prospect rows visible via shareable link, no manual steps required
  2. Each row contains host name, company name, company size, work email, episode cadence, recent episode topic, and a numeric score
  3. Prospects outside the 50-2000 employee range, missing contact info, or with inactive shows are absent from the output (hard filter working)
  4. At least one prospect is marked as skipped because they appear on the Riverside customer skip list
  5. Airtable base is shareable via link and a reviewer can inspect all fields without running any code
**Plans**: 3 plans
Plans:
- [ ] 01-01-PLAN.md -- Discovery and enrichment modules (Podcast Index search, RSS parsing, Apollo enrichment)
- [ ] 01-02-PLAN.md -- Scoring, filtering, skip list, and cheat sheet assembly
- [ ] 01-03-PLAN.md -- Airtable upload, pipeline orchestrator, and end-to-end verification

### Phase 1.1: Deep Enrichment (INSERTED)
**Goal**: Every call-ready prospect has deep context (recent episode content, company description, podcast themes) that enables genuinely personalized cold call openers
**Depends on**: Phase 1 (specifically: runs after score, only on call-ready prospects)
**Requirements**: DEEP-01, DEEP-02, DEEP-03, DEEP-04, DEEP-05, DEEP-06, DEEP-07
**Success Criteria** (what must be TRUE):
  1. Each call-ready prospect record includes last 3 episode descriptions with guest names and topics extracted from their existing RSS feed
  2. Each call-ready prospect record includes a 2-3 sentence company summary scraped from their domain's homepage or about page
  3. Each call-ready prospect record includes a podcast theme summary derived from analyzing the last 10 episode titles/descriptions
  4. Deep enrichment data is saved to data/deep_enrich.json and the pipeline runner includes a `deep_enrich` step between `score` and `upload`
  5. Zero additional API costs (all data from RSS feeds and public web pages)
  6. Only call-ready prospects are deep-enriched (disqualified/below-threshold prospects are skipped to save time)
**Pipeline position**: discover -> qualify -> enrich -> score -> **deep_enrich** -> upload
**Plans**: 2 plans

Plans:
- [ ] 01.1-01-PLAN.md -- Deep enrichment module (RSS re-parsing, company scraping, Ollama theme/company summaries)
- [ ] 01.1-02-PLAN.md -- Pipeline wiring (ProspectDict fields, upload mapping, run_pipeline integration)

### Phase 2: Call Context Generation
**Goal**: Every call-ready prospect has an AI-generated personalized call briefing (custom opener, pain hypotheses, objections, Riverside hooks) synthesized from all enrichment data
**Depends on**: Phase 1.1 (consumes deep enrichment data + scored prospect data)
**Requirements**: CCTX-01, CCTX-02, CCTX-03, CCTX-04, CCTX-05
**Success Criteria** (what must be TRUE):
  1. Each prospect's Airtable row contains a call_context field with a custom opener referencing a specific recent episode, two or more pain hypotheses, at least one predicted objection, and a Riverside relevance hook
  2. The call context is a separate field from the cheat sheet; the raw cheat sheet data is never the field that the call runner reads
  3. Running the context generation step against a 10-prospect batch completes without error and updates all rows
**Implementation Notes**:
  - MUST include prospect `title` (role) in call context prompt. Agent adjusts pitch based on role: strategic pitch for VP/Head of, workflow pitch for producer/editor. Data already available from Hunter enrichment.
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md -- Call context module, config, ProspectDict + Airtable wiring
- [ ] 02-02-PLAN.md -- CLI command wiring and end-to-end verification

### Phase 3: Voice Agent and Outcome Handling
**Goal**: The agent places calls, handles objections, triggers mid-call actions, and writes classified outcomes back to Airtable
**Depends on**: Phase 2
**Requirements**: VOIC-01, VOIC-02, VOIC-03, VOIC-04, VOIC-05, VOIC-06, VOIC-07, OUTC-01, OUTC-02, OUTC-03
**Success Criteria** (what must be TRUE):
  1. A call placed to a test number connects, the agent introduces itself using the prospect's custom opener, and the conversation sounds natural with no dead air gaps
  2. When a test caller raises at least one of the five scripted objections (not interested, already have a tool, too expensive, bad timing, wrong person), the agent responds with a relevant counter instead of going silent or looping
  3. When a test caller expresses interest, the agent fires the book_meeting tool call and the Calendly link arrives within the call or immediately after
  4. After the call ends, the Airtable row for that prospect is updated with an outcome classification (booked, interested, not-a-fit, voicemail, no-answer, or do-not-call), call notes, and a timestamp
  5. The harness system prompt is identical across all test calls; only the variableValues block changes per call
**Plans**: TBD
**UI hint**: yes

### Phase 4: Demos and Write-up
**Goal**: The submission is complete with recorded demo calls covering distinct scenarios and a write-up that explains the system, defends decisions, and demonstrates strategic thinking
**Depends on**: Phase 3
**Requirements**: DEMO-01, DEMO-02, DEMO-03, DEMO-04, DEMO-05, DEMO-06, DEMO-07, DEMO-08
**Success Criteria** (what must be TRUE):
  1. Three recorded demo calls exist covering at minimum: an interested prospect who gets a Calendly link, a prospect who raises objections, and a call that ends without conversion
  2. One of the recorded calls uses a hand-written webinar-prospect cheat sheet, and the same pipeline (harness + call context injection) handles it without code changes
  3. src/README.md exists and covers system architecture, ICP defense with evidence, prompt and conversation design decisions, a named list of things intentionally not built with rationale for each, a "how I'd take this further" section, and a path to 100+ calls per day
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 1.1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Prospect Pipeline | 3/3 | Done | 2026-04-22 |
| 1.1. Deep Enrichment (INSERTED) | 2/2 | Done | 2026-04-22 |
| 2. Call Context Generation | 0/2 | Planned | - |
| 3. Voice Agent and Outcome Handling | 0/TBD | Not started | - |
| 4. Demos and Write-up | 0/TBD | Not started | - |
