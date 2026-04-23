# Phase 3: Voice Agent and Outcome Handling - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the voice agent that places outbound cold calls using a voice AI platform (Vapi or Retell -- researcher to compare), wire simulated mid-call tooling (book_meeting, send_signup_link), handle post-call outcome classification via the platform's built-in analysis, and update the prospect's Airtable row with outcome, notes, and timestamp. The agent uses a fixed harness (system prompt) for every call and receives per-prospect call context via variable injection. Output: a working voice agent that can place demo calls to test numbers, handle objections, trigger simulated tool calls, and log classified outcomes to Airtable.

</domain>

<decisions>
## Implementation Decisions

### Voice Platform
- **D-01:** Platform choice is OPEN. Researcher must compare Vapi vs. Retell head-to-head on: time-to-first-working-outbound-call, Claude model support, function-calling mechanism, latency characteristics, Python SDK quality, and free credit/trial availability. Pick whichever gets to demo quality fastest.
- **D-02:** No Twilio setup needed. This is a demo -- use whatever phone number the platform provides out of the box. The code should be wired correctly so Twilio integration is straightforward in production, but don't burn time on it now.
- **D-03:** Latency config matters. BUILD-PLAN.md flags Vapi's formatTurns default adding 1.5s dead air. Whichever platform is chosen, researcher should document the latency-critical settings to tune.

### Harness (System Prompt)
- **D-04:** Guided framework approach. The system prompt provides conversation structure (opener -> discovery -> pitch -> close), objection handling strategies, safety rules, and Riverside product knowledge. Claude improvises the actual words. Not heavily scripted -- relies on Claude's conversational ability for natural-sounding calls.
- **D-05:** SDR persona. Agent introduces itself as calling from Riverside. Does not volunteer that it's AI, but if the prospect asks directly, it answers honestly. No deception.
- **D-06:** Core Riverside features only in the prompt. Key differentiators: 4K local recording, separate audio tracks, text-based editing, live streaming. Enough for discovery pivots and objection handling. Does NOT include full pricing tiers, competitor deep dives, or recent feature launches. Keeps the prompt lean for voice latency.
- **D-07:** Objection handling approach is Claude's discretion. The harness includes the 5 required objections (not interested, already have a tool, too expensive, bad timing, wrong person) with either specific counters or handling strategies -- Claude picks what sounds most natural.
- **D-08:** Discovery before pitch. Agent confirms it's speaking to the right person, then asks about their recording workflow, editing setup, and pain points before pitching Riverside. One question at a time.
- **D-09:** Safety rules (hard boundaries):
  - No pricing promises. Agent mentions pricing tiers exist but never commits to discounts or custom deals. Escape: "I can connect you with someone who handles pricing."
  - Respect do-not-call. If prospect says "don't call me again," agent agrees, apologizes, ends call, flags the record.
  - Time limit awareness. If call runs 5+ minutes, agent wraps up.
  - Competitor comparison is allowed if factual ("Riverside records locally at 4K, unlike Zoom which compresses") but no trash-talk.
- **D-10:** Prompt structure follows the MID Construction Eddie pattern: First Message, Role, Task, Specifics (with rules), Context (Riverside info), Examples (few-shot call transcripts). This is a proven format for voice cold call agents.
- **D-11:** Gatekeeper and voicemail handling: If voicemail, hang up (no message). If gatekeeper, ask for the prospect by first name without explaining the offer. If blocked, thank them and end. If IVR, try to reach a human, otherwise hang up.
- **D-12:** Harness stays identical across all calls (VOIC-07). Only the per-call variableValues block changes. Call context fields (opener, prospect_context, personalized_angles) are injected as variables.

### Mid-Call Tooling
- **D-13:** Simulated tools, not real integrations. Agent triggers tool calls (book_meeting, send_signup_link), the platform logs the tool invocation, and the tool returns a canned success response ("Meeting link sent!", "Signup link sent!"). Proves the function-calling wiring works without burning time on Calendly/email integration.
- **D-14:** Write-up explains the production architecture: what each tool would actually do (Calendly API, SendGrid email, CRM update), how the webhook server processes requests, and how latency is managed.

### Outcome Handling
- **D-15:** Post-call classification via the voice platform's built-in analysis feature (Vapi's analysisPlan / structuredDataSchema, or Retell's equivalent). Platform processes the transcript and returns structured outcome data. No separate LLM call needed.
- **D-16:** Six outcome categories (locked from BUILD-PLAN.md): booked, interested, not-a-fit, voicemail, no-answer, do-not-call.
- **D-17:** Update the existing prospect row in Airtable (not a separate Call Outcomes table). Add outcome classification, call notes, and timestamp directly to the prospect's row. Simpler, everything in one place, reviewer sees the full story per prospect.
- **D-18:** Follow-up actions logged wherever relevant (console output, Airtable field). System logs what follow-up would fire (e.g., "would send Calendly link to [email]") but doesn't actually send anything. Write-up describes the full follow-up architecture.

### Claude's Discretion
- Exact objection handling style (specific counters vs. strategy-per-type vs. hybrid)
- Voice-specific prompt optimizations (short sentences, no lists, conversational phrasing)
- How to structure the variableValues injection (field names, format)
- Webhook/polling approach for receiving post-call data from the platform
- Whether to use the platform's Python SDK or raw API calls

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Voice agent prompt patterns
- `https://github.com/parvbhullar/unpod` -- GitHub repo with voice agent prompt examples and best practices. Researcher MUST study this for prompt structure and voice-specific patterns.
- The MID Construction "Eddie" cold call prompt (captured in DISCUSSION-LOG.md) -- proven prompt format with First Message, Role, Task, Specifics, Context, Examples sections. Use as structural template for our harness.

### Riverside product knowledge
- `RIVERSIDE-CONTEXT.md` -- Core features for the harness prompt. Key differentiators: 4K local recording, separate audio tracks, text-based editing, live streaming.

### ICP and targeting
- `ICP-DECISION.md` -- Target audience definition. Agent pitch should be framed for mid-market B2B SaaS podcast hosts.

### Architecture and stack
- `.planning/research/STACK.md` -- Vapi details (SDK, pricing, Claude support, latency config). Researcher to also investigate Retell.
- `.planning/research/ARCHITECTURE.md` -- Three-layer model (harness + call context + cheat sheet), hard boundary rules.
- `BUILD-PLAN.md` -- Conversation design skeleton (section: "Reference: conversation design skeleton"), demo call scenarios, risks (Vapi latency, webhook timeout, voicemail detection).

### Existing pipeline code
- `src/pipeline/call_context.py` -- Call context generation module. Output fields: opener, prospect_context, personalized_angles. These become variableValues for the voice agent.
- `src/pipeline/models.py` -- ProspectDict TypedDict. Needs outcome fields added (call_outcome, call_notes, call_timestamp).
- `src/pipeline/upload.py` -- Airtable field mapping. Needs outcome fields mapped.
- `src/run_pipeline.py` -- Pipeline orchestrator. May need a `call` and `classify` step or a separate call runner script.

### Prior phase context
- `.planning/phases/01-prospect-pipeline/01-CONTEXT.md` -- D-08 (demo-grade Airtable), D-09 (table structure), D-14 (idempotent upserts).
- `.planning/phases/02-call-context-generation/02-CONTEXT.md` -- D-04 (hybrid output structure), D-07 (batch-then-call), D-09 (storage in both Airtable and local JSON).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `call_context.py` -- CallContextResponse model with opener, prospect_context, personalized_angles. These map directly to variableValues for the voice agent.
- `upload.py:prospect_to_airtable_fields()` -- Field mapping function to extend with outcome fields.
- `models.py:ProspectDict` -- TypedDict to extend with call_outcome, call_notes, call_timestamp.
- `run_pipeline.py` -- Pipeline orchestrator with existing step pattern (load JSON -> process -> save JSON).

### Established Patterns
- JSON file per pipeline step (discover.json, qualified.json, ..., call_context.json)
- OpenRouter API via requests for LLM calls (if separate classification is needed as fallback)
- ThreadPoolExecutor for parallel processing
- Structured progress logging with summary stats
- Pydantic BaseModel for structured responses
- .env for API keys (dotenv pattern)

### Integration Points
- Input: call_context.json -- prospects with call_context field populated
- Output: Airtable row updates (outcome, notes, timestamp) + local call_results.json
- ProspectDict needs new fields: call_outcome, call_notes, call_timestamp
- upload.py needs outcome fields mapped to Airtable columns
- New module(s): src/pipeline/voice_agent.py (or src/call_runner.py) for call placement + outcome handling

</code_context>

<specifics>
## Specific Ideas

- Prompt structure follows the Eddie/MID Construction pattern (First Message, Role, Task, Specifics, Context, Examples) -- proven in production voice cold calling
- The unpod GitHub repo should be studied for voice agent prompt best practices before writing the harness
- Discovery-first flow: confirm right person -> ask about recording workflow -> ask about editing -> ask about pain points -> pivot to Riverside based on pain -> handle objections -> close (book meeting or graceful exit)
- Voice-specific writing: short sentences, contractions, no lists or numbers in speech, conversational phrasing. "Read it aloud" test before integrating
- Simulated tools prove the architecture works without Calendly/email setup time. Write-up explains production wiring
- Platform choice (Vapi vs Retell) should be decided by researcher based on fastest path to demo quality, not brand loyalty

</specifics>

<deferred>
## Deferred Ideas

- Real Calendly integration for book_meeting tool -- production improvement, simulated for demo
- Real email sending for follow-up actions -- production improvement, logged for demo
- Twilio number setup for international calling -- demo uses platform-provided number
- Separate Call Outcomes table in Airtable (Phase 1 D-09) -- simplified to updating prospect row for demo scale
- Per-role prompt templates (separate harness variants for exec vs. practitioner) -- noted in Phase 2 deferred
- Voicemail drop (leave personalized message) -- v2 requirement (AUTO-04)

</deferred>

---

*Phase: 03-voice-agent-and-outcome-handling*
*Context gathered: 2026-04-23*
