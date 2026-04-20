# Phase 1: Prospect Pipeline - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the automated data pipeline that discovers B2B SaaS podcasts via Podcast Index, parses RSS feeds for host and episode data, enriches contacts via Apollo, scores and filters against ICP criteria, cross-checks a skip list of known Riverside customers, and populates an Airtable base with call-ready prospect rows. Output: a reviewer-inspectable Airtable base with 20-30 qualified prospects and full-funnel visibility.

</domain>

<decisions>
## Implementation Decisions

### Discovery
- **D-01:** Category-first search strategy. Query Podcast Index by category (Business, Technology, Marketing), then filter results by recency and cadence in code. Cast a wide net (~200-300 raw candidates), let the scoring layer handle precision.
- **D-02:** Target 20-30 call-ready rows in the final output. The candidate pool will be larger; scoring and hard filters reduce it.
- **D-03:** Solo creators (no company behind the podcast) are dropped silently by hard filters. No flagging, no 'unverified' status.

### Scoring and Filtering
- **D-04:** Scoring weights: company size fit 40%, episode cadence 30%, data completeness 20%, category match 10%. Company size is the strongest signal for this ICP.
- **D-05:** Moderate hard filters: company size outside 50-2000 employees is disqualified, last episode older than 90 days is disqualified, prospects with zero contact info are disqualified. Wider band than strict filters to keep more candidates in the funnel.
- **D-06:** Skip list loaded from an external `skip_list.json` file (not hard-coded). Contains known Riverside customer names/domains. Configurable, referenceable in the write-up.
- **D-07:** Prospects that pass hard filters but score below the call-ready threshold remain in Airtable with status 'below-threshold'. Full-funnel visibility for the reviewer.

### Airtable
- **D-08:** Demo-grade polish. Named views (Full Pipeline, Call-Ready), color-coded status field (Green=call-ready, Yellow=below-threshold, Red=disqualified, Blue=called, Grey=skipped), columns ordered by story flow (prospect info, enrichment, score, status).
- **D-09:** Two tables: Prospects table (enrichment + score data) and Call Outcomes table (call data only, linked to prospect). Shows data model thinking.
- **D-10:** Default view is Full Pipeline (all prospects, all statuses, sorted by score). Reviewer sees the full funnel on first click.
- **D-11:** Cheat sheet visible in Airtable as a long text field. Reviewer can expand and inspect the intermediate artifact. Shows the three-layer architecture (cheat sheet, call context, harness) in the data.
- **D-12:** Prospects table fields: host name, company name, company size, work email, podcast name, episode cadence, recent episode topic, score, status, cheat_sheet (long text). Call Outcomes table fields: outcome classification, call notes, timestamp, transcript excerpt, linked prospect.

### Pipeline Execution
- **D-13:** Separate scripts per stage (discover, enrich, score, upload). Clean, self-documenting code. No comments. Each module readable on its own by a technical reviewer.
- **D-14:** Idempotent upserts via pyairtable's `batch_upsert()` keyed on a unique identifier (podcast name or domain). Safe to rerun during development without creating duplicates.
- **D-15:** When Apollo returns no data for a prospect, log a warning and mark the prospect as 'enrichment-failed' in Airtable. Pipeline continues. Failure rate is visible to the reviewer.
- **D-16:** Structured progress logging per stage. Each stage prints summary stats (e.g., "Discovering... found 187 candidates", "Enriching... 42/187 complete", "Scoring... 28 call-ready, 14 below-threshold, 145 disqualified"). Clean terminal output.

### Claude's Discretion
- Category selection strategy: Claude picks whether to query all three categories (Business, Technology, Marketing) or start with one and expand based on result volume.
- Exact score threshold for call-ready vs. below-threshold: Claude picks a sensible cutoff based on the score distribution.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ICP and targeting
- `ICP-DECISION.md` -- Defines the target audience (mid-market B2B SaaS, 100-1000 employees, active podcast, dedicated podcast role). Decision is locked.
- `RIVERSIDE-CONTEXT.md` -- Riverside positioning, pricing, product features. Needed for skip list and understanding the pitch angle.

### Architecture and stack
- `.planning/research/STACK.md` -- API choices (Podcast Index, Apollo, pyairtable, feedparser), versions, cost estimates, installation commands.
- `.planning/research/ARCHITECTURE.md` -- Full pipeline flow diagram, component boundaries, data flow, Vapi integration pattern. The "hard boundary" rules (cheat sheet never reaches voice agent, nothing from build time touches call time except via Airtable).
- `.planning/research/FEATURES.md` -- Table stakes vs. differentiators, anti-features list. Guides what to build vs. skip.
- `.planning/research/PITFALLS.md` -- Known risks and mitigations for the stack.

### Scope and decisions
- `BUILD-PLAN.md` -- Master scope document. Decisions table, "intentionally not building" list, risks, conversation design skeleton.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing application code. `src/` contains only `README.md` (placeholder for final write-up).

### Established Patterns
- No established patterns yet. This is the first phase. Code conventions will be set here.
- Per user preference: self-documenting code, no comments, separate modules per pipeline stage.

### Integration Points
- Airtable base (created in this phase) is the integration point for all subsequent phases. Phase 2 reads enriched prospects from Airtable to generate call context. Phase 3 reads call context from Airtable to place calls.

</code_context>

<specifics>
## Specific Ideas

- User wants the Airtable to look impressive on first click. Demo-grade polish is a requirement, not a nice-to-have.
- Cheat sheet visible in Airtable because "having it visible somewhere would look more impressive." The three-layer architecture should be evident in the data.
- Code should be clean enough that a technical reviewer can understand each module without comments. Self-documenting function and variable names.
- Full-funnel visibility: the reviewer should see what got disqualified, what scored low, and what's call-ready. The pipeline tells a story.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 01-prospect-pipeline*
*Context gathered: 2026-04-20*
