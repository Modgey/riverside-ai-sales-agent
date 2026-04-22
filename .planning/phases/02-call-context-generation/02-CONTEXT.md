# Phase 2: Call Context Generation - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate personalized call briefings for each call-ready prospect using an LLM. Each briefing includes a custom opener, pain hypotheses, predicted objections, and Riverside relevance hooks, synthesized from all enrichment data (episode details, podcast profile, company profile, production signals, role/title). Output is a hybrid structure: JSON fields for discrete items plus a short narrative briefing for conversational flow. Stored in both Airtable (reviewer-visible) and local JSON.

</domain>

<decisions>
## Implementation Decisions

### LLM Provider and Model
- **D-01:** OpenRouter, same provider as deep_enrich. Consistent pattern across the pipeline. No new SDK dependency.
- **D-02:** Model: Kimi K2.6 (moonshotai/kimi-k2.6), same as deep_enrich. Proven in the pipeline, cost-effective at demo scale.
- **D-03:** Temperature: 0.5-0.7 (warmer than deep_enrich's 0.3). Call context is creative writing, not extraction. Higher temperature produces more variety across prospects so each call sounds distinct.

### Prompt Design and Output Structure
- **D-04:** Hybrid output structure. Structured JSON fields for discrete items (opening_line, pain_hypotheses, objections, riverside_hooks) plus a short narrative briefing for conversational flow. The voice agent gets both precision (specific fields to reference) and natural flow (narrative to guide tone).
- **D-05:** Full Riverside product knowledge baked into the system prompt. At demo scale, features are static. The LLM needs to draw specific connections between prospect signals and Riverside capabilities (e.g., "remote video interviews" -> "Riverside records locally at 4K"). RIVERSIDE-CONTEXT.md content feeds into the system prompt.
- **D-06:** Config file pattern: prompts/call_context.json with model, temperature, system_prompt, response_schema. Same pattern as deep_enrich.json and qualify.json. Prompt is iterable without touching code.

### Pipeline Wiring
- **D-07:** Batch-for-selected-prospects approach, not a pipeline step. Call context is generated for a selected set of prospects right before calling, not for all qualified prospects during the main pipeline run. Decoupled from the pipeline so you can inspect, tweak the prompt, regenerate, and then dial.
- **D-08:** Scalability rationale: at 100+ calls/day, batch generation + batch dialing is how real outbound operations work. Just-in-time per-call generation adds 5-10s latency per dial, killing throughput. The batch approach is the scalable pattern even though we're only doing 3 demo calls.
- **D-09:** Storage: both Airtable (call_context field, reviewer-visible) and local JSON (call_context.json). Shows the three-layer architecture in the data: enrichment -> call context -> harness. Call runner reads from the local JSON or Airtable.
- **D-10:** Only Qualified prospects get call context generated. Same scoping pattern as deep_enrich.
- **D-11:** New module: src/pipeline/call_context.py. Follows the established pattern: separate script, structured progress logging, JSON config for prompt, Pydantic response model.

### Role-Based Pitch Adaptation
- **D-12:** Role/title passed as a prompt input. Single prompt instructs the LLM to adapt framing based on role. No separate templates per role. One prompt, role-aware output.
- **D-13:** Two role buckets: Executive (VP, Head of, Director, C-level) gets strategic pitch (ROI, team efficiency, brand elevation). Practitioner (Producer, Editor, Content Manager) gets workflow pitch (recording quality, editing speed, guest experience).
- **D-14:** Intentionally not building: separate prompt templates per role persona. At demo scale, a single role-aware prompt is sufficient. Per-role templates would be a future improvement for production (noted for write-up "what I'd build next").

### Claude's Discretion
- Exact output fields beyond the core four (opening_line, pain_hypotheses, objections, riverside_hooks) and narrative briefing
- How much of RIVERSIDE-CONTEXT.md to include in the system prompt (full or summarized key features)
- Narrative briefing length and tone
- Pydantic response model field names and types
- Error handling pattern (follow deep_enrich's graceful failure approach)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Riverside product knowledge
- `RIVERSIDE-CONTEXT.md` -- Full Riverside positioning, pricing, product features, competitor context. Content feeds into the call context system prompt so the LLM can generate specific hooks.

### ICP and targeting
- `ICP-DECISION.md` -- Defines target audience. Call context should be framed for mid-market B2B SaaS podcast hosts.

### Architecture and stack
- `.planning/research/STACK.md` -- OpenRouter pattern, anthropic SDK (for future reference), cost estimates.
- `.planning/research/ARCHITECTURE.md` -- Pipeline flow, harness + call context separation, hard boundary rules.

### Existing pipeline code (patterns to follow)
- `src/pipeline/deep_enrich.py` -- OpenRouter + Pydantic pattern. Call context should follow this exact integration pattern (call_llm function, config loading, response model).
- `src/pipeline/prompts/deep_enrich.json` -- Config file pattern to replicate for call_context.json.
- `src/pipeline/models.py` -- ProspectDict TypedDict. Needs call_context field added.
- `src/pipeline/upload.py` -- Airtable field mapping. Needs call_context field mapped.
- `src/run_pipeline.py` -- Pipeline orchestrator. Call context is NOT a pipeline step (see D-07), but the generate_context command may be added as an optional invocation.

### Prior phase context
- `.planning/phases/01-prospect-pipeline/01-CONTEXT.md` -- D-08 (demo-grade Airtable polish), D-11 (cheat sheet visible), D-13 (separate scripts), D-16 (structured logging).
- `.planning/phases/01.1-deep-enrichment/01.1-CONTEXT.md` -- D-09 (Pydantic structured response pattern), D-10 (merge into prospect dicts).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `deep_enrich.py:call_llm_deep()` -- OpenRouter integration pattern with JSON mode, config loading, Pydantic response parsing. Call context module should follow this exact pattern.
- `deep_enrich.py:load_config()` -- Config file loading from prompts/ directory.
- `models.py:ProspectDict` -- TypedDict with all enrichment fields already available as input.
- `upload.py:prospect_to_airtable_fields()` -- Field mapping function to extend with call_context.

### Established Patterns
- JSON config per LLM step: prompts/{step}.json with model, temperature, system_prompt, response_schema
- Pydantic BaseModel for structured LLM responses
- OpenRouter API via requests (not SDK)
- ThreadPoolExecutor for parallel processing (deep_enrich uses 4 workers)
- Structured progress logging with summary stats

### Integration Points
- Input: phone_enrich.json (or deep_enrich.json as fallback) -- all enrichment data available
- Output: call_context.json + Airtable call_context field
- ProspectDict needs new field: call_context (string or dict)
- upload.py needs call_context mapped to Airtable column
- Phase 3's call runner reads call_context from Airtable or local JSON to populate Vapi variableValues

</code_context>

<specifics>
## Specific Ideas

- Hybrid output: structured fields give the voice agent specific things to reference mid-call, narrative briefing gives it conversational flow. Avoids robotic-sounding responses that come from purely structured prompts.
- Full Riverside knowledge in prompt because features don't change at demo scale. Enables the LLM to draw specific lines like "your remote video interviews -> Riverside's local 4K recording."
- Batch-then-call architecture is the scalable pattern even at demo scale. Lets you preview and iterate on context quality before burning Vapi minutes.
- Separate templates per role persona noted as "what I'd build next" for the write-up.

</specifics>

<deferred>
## Deferred Ideas

- Per-role prompt templates (separate system prompts for exec vs. practitioner personas) -- future improvement for production scale. Noted for write-up "what I'd build next" section.
- A/B testing different opener styles -- v2 requirement (AUTO-03).
- Context freshness/staleness detection (regenerate if enrichment data changed since last generation) -- production concern, irrelevant at demo scale.

</deferred>

---

*Phase: 02-call-context-generation*
*Context gathered: 2026-04-22*
