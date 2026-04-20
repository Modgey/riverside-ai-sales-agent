# Architecture Patterns: AI Cold-Calling Pipeline

**Domain:** AI-powered outbound sales pipeline with voice agent
**Researched:** 2026-04-20
**Confidence:** HIGH (Vapi docs verified, pipeline patterns corroborated by multiple sources)

---

## Recommended Architecture

The system splits into two runtime phases: **build time** (runs once per batch, no user interaction) and **call time** (runs per call, real-time constraints).

```
BUILD TIME
==========

[Podcast Index API]
        |
        | search by category, recency, cadence
        v
[RSS Parser]
        |
        | host name, episode count, show metadata
        v
[Apollo Enrichment]
        |
        | company size, employee count, email, title
        v
[Scoring + Hard Filters]
        |
        | disqualify by size, cadence, geo, data gaps
        | cross-check skip list
        v
[Cheat Sheet Builder]          <-- intermediate artifact, not what agent sees
        |
        | structured dict: show name, host, company, size,
        | episode titles, tech stack signals, pain guesses
        v
[LLM Call Context Generator]  <-- one LLM call per passing prospect
        |
        | input: cheat sheet
        | output: opener line, 2-3 pain hypotheses,
        |         predicted objections + responses, relevance hook
        v
[Airtable]                    <-- call_context stored here alongside prospect record
        |
        | status: queued, called, outcome


CALL TIME
=========

[Orchestrator / Call Runner]
        |
        | reads prospect from Airtable (status=queued)
        | assembles Vapi API payload
        v
[Vapi POST /call]
  - assistantId: shared harness assistant
  - assistantOverrides.variableValues: per-call context (opener, pains, objections, hook)
  - customer.number: prospect phone
  - phoneNumberId: our outbound number
        |
        v
[Vapi Platform]  <-- owns the real-time audio stack
  STT (Deepgram) -> LLM (Claude/GPT-4o) -> TTS (ElevenLabs/PlayHT)
  turn-taking, interruption handling, latency optimization (<700ms target)
        |
        | mid-call function calls (when agent decides to act)
        v
[Tool Endpoints (webhook server)]
  - book_meeting: generate Calendly link, confirm to prospect
  - send_signup: deliver Riverside trial link via SMS or email
  - disqualify: silent flag, agent exits gracefully
        |
        v (call ends)
[Vapi end-of-call-report webhook]
  - full transcript
  - messages array (role + content)
  - call metadata (duration, ended_reason)
        |
        v
[Post-Call Classifier]
  - LLM reads transcript
  - outputs: booked | interested | not_a_fit | voicemail | no_answer | do_not_call
  - writes outcome + transcript excerpt to Airtable
```

---

## Component Boundaries

| Component | Responsibility | Input | Output | Talks To |
|-----------|---------------|-------|--------|----------|
| Discovery | Find B2B SaaS podcasts matching ICP | Podcast Index API | Raw podcast records | RSS Parser |
| RSS Parser | Extract host identity and show metadata | RSS feed URLs | Structured show dict | Apollo Enrichment |
| Apollo Enrichment | Add company firmographics and contact info | Host name + domain | Enriched prospect dict | Scoring layer |
| Scoring + Filter | Disqualify noise, rank remaining | Enriched dict | Qualified prospect list | Cheat Sheet Builder |
| Cheat Sheet Builder | Assemble structured build-time data bundle | Qualified prospect | Cheat sheet dict | LLM Context Generator |
| LLM Context Generator | Generate personalized call context from data | Cheat sheet | Call context block | Airtable |
| Airtable | Persistent store, demo-visible dashboard | All stages write | Prospect records with full history | Call Runner, Post-Call Classifier |
| Call Runner (Orchestrator) | Read queued prospects, fire Vapi calls | Airtable queue | Vapi API call per prospect | Vapi |
| Vapi Platform | Real-time voice conversation | Harness + call context | Audio call, transcripts, webhooks | Tool Endpoints, Webhook receiver |
| Tool Endpoints | Handle mid-call function calls | Vapi tool call payloads | Action confirmations back to Vapi | Calendly, SMS/email APIs |
| Post-Call Classifier | Classify outcome from transcript | Vapi end-of-call webhook | Outcome label + excerpt | Airtable |

**Hard boundary:** Nothing from build time touches call time except via Airtable. The call runner reads from Airtable, not from any in-memory pipeline state. This makes retries, reruns, and manual overrides straightforward.

**Hard boundary:** The cheat sheet never reaches the voice agent. It is an intermediate artifact. Only the LLM-generated call context (opener, pains, objections, hook) passes to Vapi via `variableValues`. This keeps the context block compact and avoids dumping raw data into the LLM context window at call time.

---

## How Vapi Handles the Harness + Call Context Split

Vapi's per-call injection mechanism maps cleanly to this architecture.

**Shared harness** = a saved Vapi assistant (`assistantId`) with a static system prompt containing:
- Persona (name, role at Riverside)
- Product pitch and positioning
- Tone and pace guidelines
- Discovery flow (question sequence)
- Objection handling framework (don't argue, acknowledge, pivot)
- Exit paths (graceful decline, voicemail script, DNC trigger)
- Safety rules (no false urgency, no fake credentials)
- Variable placeholders: `{{opener}}`, `{{pain_1}}`, `{{pain_2}}`, `{{predicted_objection}}`, `{{hook}}`

**Per-call context** = injected at call time via `assistantOverrides.variableValues`:
```json
{
  "opener": "I noticed your Operators podcast dropped to monthly episodes last quarter...",
  "pain_1": "Managing remote guests without quality control",
  "pain_2": "Post-production eating 4-6 hours per episode",
  "predicted_objection": "We already use Zoom and it's fine",
  "hook": "Three of your Operators guests have switched to Riverside in the last six months"
}
```

The harness then references `{{opener}}` in the `firstMessage` field. Result: one saved assistant, fully personalized calls, zero per-call assistant creation overhead.

**Confidence:** HIGH. Directly verified in [Vapi dynamic variables docs](https://docs.vapi.ai/assistants/dynamic-variables).

---

## Mid-Call Tool Calling

Vapi supports function calling during live conversations. The LLM decides when to invoke a tool based on conversational cues.

Pattern:
1. Prospect says "sure, send me more info" or "yeah let's find a time"
2. LLM emits a tool call (not spoken aloud)
3. Vapi POSTs to the tool endpoint with a `toolCallList` payload
4. Endpoint executes the action (generate Calendly link, trigger SMS)
5. Endpoint returns confirmation text
6. LLM speaks the confirmation to the prospect

Tool definitions live in the assistant config. For this project: `book_meeting` and `send_signup_link` are the two tools needed.

**Silence rule:** Tool invocations should not produce spoken filler ("One moment while I..."). The Vapi prompting guide confirms this pattern: instruct the agent to silently call the tool and only speak after the result returns.

---

## Post-Call Data Flow

Vapi fires an `end-of-call-report` webhook after every call. The payload includes:
- `artifact.transcript`: full conversation text
- `artifact.messages`: array with role + content per turn
- `call.endedReason`: why the call terminated (customer-ended, no-answer, silence, etc.)
- `analysis.summary`: auto-generated AI summary (Claude Sonnet, GPT-4o fallback)

The post-call classifier receives this webhook, runs one LLM call (or uses Vapi's built-in `analysisPlan` with `structuredDataSchema`) to produce a classification label, and writes it back to Airtable.

Two options for classification:
1. **Vapi built-in analysis plan** (`structuredDataSchema` + `structuredDataPrompt` on the assistant): runs automatically, result included in the webhook. Simpler, but less control.
2. **Separate classifier script**: receives webhook, calls Claude with the transcript, writes to Airtable. More control, one extra LLM call per call.

Recommendation: use Vapi's built-in `analysisPlan` for outcome classification. It runs on Vapi's infra (no extra webhook server needed), the result is in the webhook payload, and it keeps the post-call handler to a simple Airtable write. If classification logic gets complex later, migrate to separate classifier.

---

## Suggested Build Order

Dependencies determine order. Each layer consumes the output of the previous one.

```
Phase 1: Data Foundation
  1a. Podcast Index API wrapper (search + category filter)
  1b. RSS parser (host extraction, episode metadata)
  1c. Airtable schema setup (prospect table, all fields)
  -- Validates: can we get clean prospect data? Before writing enrichment code.

Phase 2: Enrichment + Scoring
  2a. Apollo enrichment (people + org endpoints)
  2b. Scoring rules + hard filter logic
  2c. Skip-list cross-check
  2d. Write qualified prospects to Airtable
  -- Validates: are we getting the right companies through the filter?

Phase 3: Cheat Sheet + Call Context Generation
  3a. Cheat sheet assembler (dict from Airtable record)
  3b. LLM call context generator (prompt + structured output)
  3c. Write call_context back to Airtable
  -- Validates: does the generated opener/pains feel right for a real call?

Phase 4: Voice Agent
  4a. Vapi assistant creation (harness system prompt, variableValues schema)
  4b. Call runner (read Airtable, fire Vapi calls with assistantOverrides)
  4c. Tool endpoint (book_meeting, send_signup_link)
  4d. Vapi analysisPlan config (structuredDataSchema for outcome classification)
  4e. Webhook receiver (write outcome to Airtable)
  -- Validates: does the agent sound natural? Does the opener land?

Phase 5: Demo + Write-up
  5a. Record 2-3 demo calls (interested, objection, voicemail scenarios)
  5b. Hand-write webinar cheat sheet for one demo (shows architecture generalizes)
  5c. Write src/README.md (architecture, ICP defense, prompt design, what I didn't build)
```

**Why this order:**
- Phase 1 before Phase 2: no point enriching what you can't discover
- Phase 2 before Phase 3: the cheat sheet is built from enriched + scored data
- Phase 3 before Phase 4: the call runner needs call_context already in Airtable
- Phase 4 before Phase 5: you need working calls to record demos

The only parallel work possible: Airtable schema (1c) can be set up in parallel with API wrappers (1a, 1b) since they're independent. Similarly, the harness system prompt (4a) can be drafted during Phase 3 since it doesn't depend on actual call context output.

---

## Data Flow Summary

```
Podcast Index API
  -> raw_podcasts (list of show dicts)
  -> RSS feeds parsed
  -> enriched by Apollo (company size, email, title)
  -> scored + filtered
  -> written to Airtable (status: enriched)

Airtable (enriched record)
  -> cheat sheet assembled in memory
  -> LLM produces call_context
  -> call_context written back to Airtable (status: ready)

Airtable (ready record)
  -> call runner reads prospect + call_context
  -> fires Vapi /call with harness + variableValues
  -> Vapi places call, handles real-time audio

Call completes
  -> Vapi fires end-of-call-report webhook
  -> analysisPlan runs (or separate classifier)
  -> outcome + transcript written to Airtable (status: called)
```

---

## Scalability Notes

For demo (30-100 prospects): single-threaded pipeline, Airtable free tier, Vapi free credits. No queue needed.

For production (100+/day):
- Replace single-threaded call runner with a queue (SQS or simple Redis queue). Vapi handles concurrent calls; the queue just manages dispatch rate and retries.
- Apollo rate limits (per-minute caps) require throttled enrichment. Pre-validate inputs (need at least 2 of: email, domain, name) to avoid wasting credits on bad records.
- Airtable hits limits at 1,000 records (free) or 50,000 (paid). At scale, replace with Postgres + keep Airtable as a reviewer-facing view only.
- Vapi's voice pipeline is already horizontally scaled on their infra. No work needed there until 10,000+ concurrent calls.

---

## Sources

- [Vapi Dynamic Variables docs](https://docs.vapi.ai/assistants/dynamic-variables) - HIGH confidence
- [Vapi Outbound Calling docs](https://docs.vapi.ai/calls/outbound-calling) - HIGH confidence
- [Vapi Tool Calling Integration](https://docs.vapi.ai/customization/tool-calling-integration) - HIGH confidence
- [Vapi Call Analysis](https://docs.vapi.ai/assistants/call-analysis) - HIGH confidence
- [Vapi Voice AI Prompting Guide](https://docs.vapi.ai/prompting-guide) - HIGH confidence
- [Vapi Server Events / Webhooks](https://docs.vapi.ai/server-url/events) - MEDIUM confidence (doc content inferred from search result snippets)
- [Voice AI Agent Architecture Patterns - Bluejay](https://getbluejay.ai/resources/voice-ai-agent-architecture) - MEDIUM confidence (corroborates Vapi docs on pipeline structure)
- [Apollo People Enrichment API](https://docs.apollo.io/reference/people-enrichment) - HIGH confidence
- [ElevenLabs Outbound AI Calling Guide](https://elevenlabs.io/blog/outbound-ai-calling-strategy-guide-for-2025) - MEDIUM confidence (strategic patterns, not deep technical detail)
