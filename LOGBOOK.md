# Logbook

Running log for the Riverside home assignment. Always open for edits.

Records decisions, tradeoffs, design reasoning, and "not built" items as they happen. Each entry is dated. Source material for the final writeup (Shawn turns entries into prose later).

Sections map to the writeup's required topics: strategic framing, prompt/conversation design, what we intentionally did not build, and what we'd do next with more time.

---

## Strategic framing

**Function, not cold-caller**
- Mattan said 2x: builder + strategic/PM thinker, "functions not just agents"
- Writeup bar: "outbound function, call agent is one node" = pass both halves. "I built a cold-caller" = fail strategic half.
- 6-step pipeline: discover, enrich, score, generate call context, call, handle outcome. Outcome handling is first-class, that's where "scales to 100+/day" lives.

**ICP: mid-market B2B SaaS with active podcast**
- Size: 100-1000 employees (below = PLG territory, above = named-account AE territory)
- Role: dedicated podcast owner (Head of Podcasts, Podcast Producer, Content Lead)
- Pitch: "switch from Zoom/Squadcast to Riverside" not "start a podcast" (Riverside already has Lenny, Headspace, Chili Piper, Wix, Intuit, Pega = switching market)
- Webinar ICP (Option B) rejected for build, captured in write-up as "what I'd build next." One demo call with hand-written webinar cheat sheet proves the architecture generalizes.

**Three-layer architecture (harness + cheat sheet + call context)**
- Harness = shared system prompt (persona, pitch, tone, discovery, objections, exits, safety). Never changes. One Vapi assistant config.
- Cheat sheet = intermediate build-time artifact. All structured data from pipeline (name, company, show, episodes, company size, role, cadence). The agent never sees this directly.
- Call context = LLM-generated from cheat sheet. Custom opener, pain hypotheses, predicted objections, relevance hook. Injected via Vapi variableValues. This is what the agent reads.
- Why three layers: agent stays focused (no raw data sifting). Harness defines HOW to handle objections, call context says WHICH to expect. No overlap, no conflict.

**Cheat sheet removed as stored artifact (Apr 22)**
- Was: assemble_cheat_sheet() in score.py built a JSON blob, stored on each prospect dict, uploaded to Airtable. deep_enrich.py overwrote it with a richer version.
- Problem: redundant. Every field in the cheat sheet already exists as a first-class prospect field. Storing it duplicates data and bloats Airtable.
- Now: cheat sheet is a runtime concept only. Phase 2's build_call_context_prompt() will assemble LLM input directly from prospect fields at call time. No intermediate artifact.
- The three-layer architecture still holds: harness (system prompt) + call context (LLM-generated at call time from prospect fields) + prospect data (pipeline output). We just removed the unnecessary intermediate layer.

**AI usage: exactly 3 touchpoints**
- (1) Call context generation from cheat sheet, (2) voice agent conversation, (3) post-call transcript classification.
- Everything else is deterministic code (API calls, RSS parsing, filtering, scoring, template assembly).
- Write-up talking point: "AI where it adds value, code where code is better."

**Stack (validated via research)**
- Discovery: Podcast Index API (free, unlimited requests, returns RSS URLs directly). Listen Notes free tier capped at 300 req/month, ruled out.
- RSS parsing: feedparser. Host name from itunes:owner (~80% of B2B podcasts), episode metadata, cadence, personalization signals (episode topics, guest names).
- Enrichment: Apollo free tier (10K email credits with work-email signup, company size/industry filters). RocketReach (5/mo) and Clearbit (discontinued) ruled out.
- Voice: Vapi + Claude Sonnet. $10 free credit (~60-70 min). variableValues for per-call context injection. analysisPlan for post-call classification.
- Database: Airtable free tier. Reviewer clicks a link, sees populated rows. pyairtable handles rate limits automatically.
- Budget: $10-15 cap. ~$3-5 actual spend (Anthropic API only).

**Fully automated pipeline**
- No manual steps between "run the pipeline" and "calls go out." Scoring layer IS the quality gate.
- "Human reviews list" breaks the 100+/day scalability story. Only manual thing is initial config (search params, score thresholds).

---

## Design: prompts and conversation logic
*empty, fill during Phase 3*

---

## Intentionally not built
Each: what / why not / cost.

**Automated audio/video quality classifier**
- What: AI scores production quality from a clip. Flags Zoom-sounding (target) vs studio-grade (skip).
- Why not: 30 min manual YouTube review at 20-30 seed companies is more accurate at this volume.
- Cost: ~4-6 hrs model + ~2-3 hrs integration.

**Programmatic Riverside-customer detector**
- What: auto check for "already on Riverside."
- Why not: hand-curated skip list covers 20-30 prospects exhaustively. Automation is brittle and premature here.
- Cost: ~3-5 hrs (logo-wall scrape + show-notes search + tech-stack detection).

**Webinar enrichment pipeline**
- What: full 2nd-audience pipeline. Two paths considered: (a) scrape LinkedIn + company sites for "mentions webinar" signal, (b) Apollo/BuiltWith tech-stack filter ("uses ON24 / Goldcast / Zoom Webinars") + Apollo contact lookup.
- Why not: (a) ~10+ hrs, brittle, weak signal. (b) ~3-4 hrs unvalidated + extra paid account. Demo cheat sheet + writeup carry the strategic signal at near-zero cost.

**Full outcome handling automation (all 6 paths)**
- What: every outcome (booked, interested, not-a-fit, voicemail, no-answer, DNC) triggers a real downstream action.
- Why not: 6-12 hrs. Only booked/interested path matters for demo. One real action (Calendly email) proves the pattern. Rest described in write-up.

**CRM/Gong/Snowflake integration**
- What: route outcomes into Riverside's stack.
- Why not: 4-8 hrs on auth and field mapping. Reviewer evaluates the concept, not the plumbing. Described in write-up.

---

## Would take further

- Ship webinar ICP as 2nd pipeline (Apollo/BuiltWith tech-stack filter + Apollo contact lookup). Unlocks Riverside's Mar 2026 webinar push.
- Route outcomes into Riverside's stack: HubSpot (contact + next-step sync), Gong (upload Vapi recording for conversation intelligence), Snowflake (warehouse call data).
- Automated quality classifier into scoring layer.
- Programmatic Riverside-customer detector to replace skip list.
- Multi-step follow-up: "interested, needs team" triggers auto email + Calendly 48h later.
- A/B testing harness: ship 2 prompt variants, split calls, measure meeting-book rate.
- Voicemail drop: detect voicemail tone, leave personalized voicemail from same cheat sheet.
- Per-prospect tone override layer between harness and call context (VP Mktg Boston vs podcast producer Austin sound different).
- Parallel dialing for production volume via Vapi's concurrent call API.
- Smarter discovery funnel: filter by minimum episode count, require B2B categories upfront, cross-reference domains against a company database before enrichment. Current funnel converts 14% (115 discovered -> 16 call-ready). Most loss is at discovery-to-enrichment: Podcast Index returns solo creators and hobby podcasts without real company domains. Tighter discovery could push the enrichable ratio from ~19% to 60-70%, meaning fewer wasted enrichment credits and more call-ready output per run.

---

## Log

### 2026-04-20 afternoon
- GSD project initialized. Full research cycle completed (7 parallel research agents across stack, features, architecture, pitfalls, and enrichment options).
- All strategic decisions locked: ICP (podcast), stack (Podcast Index + RSS + Apollo + Vapi + Airtable), architecture (three-layer: harness + cheat sheet + call context), AI usage (3 touchpoints only), outcome handling (simple + write-up), budget ($10-15 cap, ~$3-5 actual).
- 4-phase roadmap locked: (1) Prospect Pipeline, (2) Call Context Generation, (3) Voice Agent + Outcome Handling, (4) Demos + Write-up. 34 requirements mapped.
- Vapi gotchas captured: formatTurns default adds 1.5s dead air (set false day 1), free tier US-only outbound (need Twilio number, Shawn in Tel Aviv), webhook 7.5s timeout (pre-warm server), voicemail detection false positives (disable for demos), write prompts for voice not text.
- Scoring signals still open. Decide after seeing real pipeline data. Candidates: company size, cadence, data completeness, category match. "Likely current recording tool" detection TBD.
- Phase 1 context discussion completed. Key choices: category-first discovery, company size weighted heaviest in scoring (40%), moderate hard filters (50-2000 employees), two Airtable tables (Prospects + Call Outcomes linked), demo-grade polish, full-funnel visibility, separate scripts per pipeline stage, idempotent upserts.
- **Deferred idea: Dashboard UI.** Web frontend to visualize pipeline progress, show database state, let reviewer trigger steps interactively. Streamlit or simple React, format TBD. Only if Phase 3 finishes early on Wednesday. Not planned, not scoped, just a note.

### 2026-04-20 evening
- Phase 1 code complete. All 3 plans executed across 3 waves.
- Wave 1: models.py (ProspectDict TypedDict), discover.py (Podcast Index search + RSS parsing), enrich.py (Apollo people/match + org enrichment). feedparser itunes_author prioritized over author (Pitfall 4). Category filter lenient on empty categories dict.
- Wave 2: score.py (hard filters, 4-weight scoring summing to 100, skip list, cheat sheet assembly), skip_list.json (Riverside + 3 competitors). Threshold: 60/100 for call-ready.
- Wave 3: upload.py (Airtable batch_upsert keyed on podcast_name), run_pipeline.py (4-stage orchestrator with structured output).
- All imports verified. No input() calls (fully automated). .env protected via .gitignore.
- **Pending:** Run pipeline with real API keys, set up Airtable views/colors/Call Outcomes table manually, create shareable link.

### 2026-04-21 morning
- Reviewed discover.json (87 raw prospects). Data quality issues identified: messy host names (person name + title soup, org names slipping through heuristics), missing hosting platforms in blocklist (substack.com, soundcloud.com, podcasts.apple.com, linktr.ee, etc.), non-English podcasts (German, Italian, Portuguese, Vietnamese), 2 existing Riverside customers in the data (rss_url contains riverside.fm).
- **Decision: AI qualification step between discover and enrich.** Heuristic name parsing is whack-a-mole. Local LLM (Gemma 4 via Ollama) classifies each prospect: person vs org, extracts clean first/last name, detects language, flags hosting platform domains. Pydantic validates every response. Heuristics stay as fallback if Ollama fails.
- **Tradeoff: local LLM vs API call.** Ollama is free (no budget hit), fast enough for 87 prospects, and keeps the pipeline runnable offline. Downside: requires Ollama installed locally. Acceptable for a demo.
- Pipeline is now 5 stages: discover -> qualify -> enrich -> score -> upload. Qualify acts as a gate, saving Prospeo credits by filtering out orgs, non-English, and hosting platform domains before enrichment.
- Config extracted to `src/pipeline/prompts/qualify.json`. System prompt, model name, temperature, max retries all in one file. Code is pure execution logic. Swap models or tweak prompts without touching Python.
- Expanded hosting platform blocklist (+9 domains) and non-person word list (+7 words) in enrich.py.
- Pipeline messaging improved. Each stage now prints plain-English context about what it's doing and why, not just "Stage 2/5" headers.
- **Intentionally not built: few-shot examples in qualify prompt.** Zero-shot with a tight schema spec is sufficient for this classification task. Few-shot would bloat the prompt and slow inference on a 4B model for marginal accuracy gain.
- **Pending:** Run qualify step on real data, spot-check qualified.json accuracy, then proceed to enrichment with real Prospeo keys.

### 2026-04-21 afternoon
- Ran qualify step on 115 discovered prospects. Results: 43 qualified, 70 disqualified, 2 existing Riverside customers. Spot-checked all 43 qualified records: clean first/last name extraction, correct language detection, domains all present. Quality is solid.
- Found ~5-6 false DQs in org_not_person bucket. Prospects like "Jon Bradshaw, Peter Harris" or "Dean Denny, Founder + Director at Owendenny Digital" were DQ'd because the LLM treated any extra text (titles, multiple hosts, org names) as "not a person." Fixed the qualify prompt to say: if a real person name is extractable, qualify it and extract just the first person's name. Prompt-only fix, no code changes.
- **Enrichment provider swap: Prospeo -> Hunter.io.** Prospeo free credits exhausted during testing. Evaluated alternatives: Apollo free tier (API access unclear on free plan), Hunter.io (25 searches/month free, full API), Datagma (50 credits free). Chose Hunter: reliable API, returns email + title + company name via email-finder endpoint, company size + industry via company-enrichment endpoint. Two calls per prospect but company enrichment is cached per domain.
- **Design decision: provider-agnostic enrichment layer.** The enrich function signature stayed constant through three provider swaps (Prospeo -> Apollo -> Hunter): `(first_name, last_name, domain) -> dict`. Same output schema, same downstream contract. Pipeline doesn't care which provider fills the fields. This is intentional, not accidental. Writeup talking point: "enrichment is a commodity, the pipeline abstracts over it."
- Qualify prompt updated to handle messy host_name strings (names with titles, multiple hosts, credentials). Same model, same schema, just clearer instructions about when is_person should be true.

### 2026-04-22 early morning
- **Scoring fix: company_size now a bonus, not a hard gate.** Hunter free tier returns emails but not company size for most prospects. All 115 prospects were getting disqualified (94 missing_company_size, 21 enrichment_failed). Changed size_fit_score to return 0 for None (no penalty, no boost), removed the hard disqualification gate. Lowered call-ready threshold from 60 to 40 so prospects without size data can still qualify on cadence + completeness + category. Result: 16 call-ready, 3 below-threshold. Prospects with known size in the sweet spot still get up to 40 bonus points.
- **Funnel analysis:** 115 discovered -> 22 enriched -> 16 call-ready (14% overall conversion). Biggest drop is discovery-to-enrichment (81% lost). Root cause: Podcast Index returns many solo creators, hobby podcasts, hosting platform domains. Logged in "would take further" as a discovery quality improvement.
