# Phase 2: Call Context Generation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 02-call-context-generation
**Areas discussed:** LLM provider and model, Prompt design and output structure, Pipeline wiring, Role-based pitch adaptation

---

## LLM Provider and Model

| Option | Description | Selected |
|--------|-------------|----------|
| Anthropic Claude Sonnet 4 | Per CLAUDE.md spec. ~$0.90 for 30 prospects. Best writing quality. | |
| OpenRouter (same as deep_enrich) | Reuse existing pattern. Consistent provider across pipeline. | ✓ |
| Local Ollama (free) | Zero cost. Quality may suffer for creative writing. | |

**User's choice:** OpenRouter for consistency across the pipeline.

| Option | Description | Selected |
|--------|-------------|----------|
| Claude Sonnet 4 via OpenRouter | Best creative writing quality. $3/$15 per M tokens. | |
| Same Kimi K2.6 as deep_enrich | Already proven. Cheaper. Keeps codebase simpler. | ✓ |
| You decide | Claude picks best model. | |

**User's choice:** Kimi K2.6. User initially noted "Opus 4.6" but confirmed Kimi K2.6 on follow-up.

| Option | Description | Selected |
|--------|-------------|----------|
| 0.3 (same as deep_enrich) | Predictable, structured output. | |
| 0.5-0.7 (warmer) | More variety in openers. Each call feels distinct. | ✓ |
| You decide | Claude picks. | |

**User's choice:** Warmer temperature for creative variety.

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, same config pattern | prompts/call_context.json. Consistent. Easy to tweak. | ✓ |
| Inline in code | Simpler but breaks the pattern. | |

**User's choice:** Same config file pattern as deep_enrich and qualify.

---

## Prompt Design and Output Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Structured JSON fields | Separate fields for opener, pain, objections, hooks. | |
| Single narrative block | One prose paragraph covering everything. | |
| Hybrid: structured + narrative | JSON fields for discrete items plus a narrative briefing. | ✓ |

**User's choice:** Hybrid. User reasoning: "If the prompt is too structured, the voice agent's responses can feel structured and robotic." Structured fields for precision, narrative for conversational flow.

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt knows Riverside deeply | Full product knowledge. Richest hooks per prospect. | ✓ |
| Prospect-focused only | Clean separation. Generic hooks. | |
| Light Riverside context | 5-6 key features. Middle ground. | |

**User's choice:** Full Riverside knowledge. User reasoning: "Features aren't changing in this demo." Maximum personalization quality.

---

## Pipeline Wiring

| Option | Description | Selected |
|--------|-------------|----------|
| After phone_enrich, before upload | Standard pipeline step. | |
| Part of the upload step | Inline during upload. | |
| Standalone script | Run separately. | |

**User's choice:** User rejected all three. Wanted call context generated "right before the AI phone call agent calls. So we are only doing it for prospects we are about to call."

| Option | Description | Selected |
|--------|-------------|----------|
| Call runner generates per-prospect | Generate right before dialing. Tightly coupled. | |
| Batch for selected prospects | Generate for selected set, then call. Decoupled, inspectable. | ✓ |
| Pipeline step for top N | Standard step but scoped to top N. | |

**User's choice:** Batch for selected prospects. User asked for "cleanest and most reliable/scalable" approach. Claude explained batch-then-call is the scalable pattern (100+ calls/day, parallel dialing) and most debuggable for demo iteration.

| Option | Description | Selected |
|--------|-------------|----------|
| Both Airtable + JSON | Reviewer-visible + local file. Shows three-layer architecture. | ✓ |
| Airtable only | Simpler but slower for call runner. | |
| JSON only | Reviewer can't see it. | |

**User's choice:** Both. Consistent with Phase 1's "demo-grade Airtable" principle.

---

## Role-Based Pitch Adaptation

| Option | Description | Selected |
|--------|-------------|----------|
| Role as prompt input, LLM adapts | Single prompt, role-aware output. | ✓ |
| Separate prompt templates per role | Maximum control. More code. | |
| Minimal role awareness | Include role but don't instruct adaptation. | |

**User's choice:** Role as prompt input. User explicitly noted: "I decided not to do separate templates but would for future improvements." Captured as deferred idea for write-up.

| Option | Description | Selected |
|--------|-------------|----------|
| Two buckets: executive vs. practitioner | Strategic pitch vs. workflow pitch. | ✓ |
| Three buckets: exec, manager, practitioner | More nuanced but may over-segment. | |
| You decide | Claude picks based on actual titles. | |

**User's choice:** Two buckets. Executive (VP, Head of, Director, C-level) vs. Practitioner (Producer, Editor, Content Manager).

---

## Claude's Discretion

- Exact output fields beyond core four + narrative briefing
- RIVERSIDE-CONTEXT.md summarization level for system prompt
- Narrative briefing length and tone
- Pydantic response model details
- Error handling pattern

## Deferred Ideas

- Per-role prompt templates -- future improvement (user-requested deferral for write-up)
- A/B testing opener styles -- v2 requirement
- Context freshness/staleness detection -- production concern
