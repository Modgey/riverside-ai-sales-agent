# Phase 3: Voice Agent and Outcome Handling - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 03-voice-agent-and-outcome-handling
**Areas discussed:** Harness design, Vapi wiring, Mid-call tooling, Outcome handling

---

## Voice Platform Choice

| Option | Description | Selected |
|--------|-------------|----------|
| Latency concerns | Retell claims lower latency (2.1s vs 2.6s avg) | |
| Setup complexity | Want path of least resistance for 3-day build | |
| Cost or credits | Questioning Vapi's $10 free credit sufficiency | |
| Open to either | Want researcher to compare and recommend | ✓ |

**User's choice:** Open to either -- researcher should compare Vapi vs Retell head-to-head
**Notes:** User is not committed to Vapi. Platform choice should be based on fastest path to demo quality.

---

## Telephony (Twilio)

| Option | Description | Selected |
|--------|-------------|----------|
| Have Twilio account | Already have account, just provision number | |
| No Twilio yet | Need to set up from scratch | |
| Use platform number | Use whatever platform provides out of box | ✓ |

**User's choice:** No Twilio needed for demo. Use platform-provided number. Functionality should be wired correctly for production but don't burn setup time.

---

## Webhook Server

| Option | Description | Selected |
|--------|-------------|----------|
| Local + ngrok | Flask/FastAPI locally, ngrok for demo | |
| Serverless | Deploy to free hosting tier | |
| You decide | Claude picks fastest path | |

**User's choice:** Questioned whether webhook server is needed at all for demo. Led to simulated tools decision.

---

## Mid-Call Tool Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Verbal only | Agent says it'll send a link but nothing fires | |
| Simulated tools | Agent triggers tool call, returns canned response | ✓ |
| One real action | Real Calendly link sent during call | |
| You decide | Claude picks based on time remaining | |

**User's choice:** Simulated tools -- proves function-calling wiring works without Calendly/email integration.

---

## Agent Tone / Scripting Level

| Option | Description | Selected |
|--------|-------------|----------|
| Guided framework | Framework with guidelines, Claude improvises words | ✓ |
| Scripted with flex | Specific phrases for key moments, flex in between | |
| Heavily scripted | Every major moment has specific script | |
| You decide | Claude picks most natural approach | |

**User's choice:** Provided detailed vision (pasted as free text). Two-layer model: fixed harness (persona, tone, value prop, objections, discovery flow, wrap-up rules) + per-prospect call context (opener, company/role context, pitch angles, predicted objections). Discovery before pitch. Pain-driven pivots. Graceful exits. Adapts to off-script moments.

---

## Agent Persona

| Option | Description | Selected |
|--------|-------------|----------|
| SDR persona | Introduces as sales rep from Riverside | ✓ |
| AI-transparent | Upfront about being AI | |
| You decide | Claude picks most natural approach | |

**User's choice:** SDR persona by default. Doesn't volunteer being AI, but if asked directly, answers honestly. No deception.

---

## Product Knowledge Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Core features only | Key differentiators, lean prompt | ✓ |
| Full product knowledge | Pricing, competitors, recent features | |
| You decide | Claude picks right depth | |

**User's choice:** Core features only -- 4K local recording, separate tracks, text-based editing, live streaming. Lean prompt for voice latency.

---

## Objection Handling Style

| Option | Description | Selected |
|--------|-------------|----------|
| Specific counters | Concrete counter-argument per objection | |
| Strategy per type | Handling strategy, Claude generates words | |
| You decide | Claude picks most natural approach | ✓ |

**User's choice:** Claude's discretion.

---

## Safety Rules

| Option | Description | Selected |
|--------|-------------|----------|
| No pricing promises | Never commit to discounts/custom deals | ✓ |
| Respect do-not-call | Immediately agree and flag record | ✓ |
| No competitor trash-talk | Factual comparison only, no disparagement | |
| Time limit awareness | Wrap up after 5+ minutes | ✓ |

**User's choice:** Three of four. Competitor factual comparison is allowed (not selected as a hard rule).

---

## Reference Materials Provided

User provided two reference resources for harness prompt design:
1. **unpod GitHub repo** (https://github.com/parvbhullar/unpod) -- voice agent prompt patterns and structure
2. **MID Construction "Eddie" prompt** -- complete cold call voice agent prompt with: First Message, Role, Task, Specifics, Context, Examples, Notes sections. Includes full example call transcripts for ideal call, objection handling, gatekeeper, and IVR scenarios.

---

## Post-Call Classification

| Option | Description | Selected |
|--------|-------------|----------|
| Vapi analysisPlan | Platform's built-in transcript analysis | ✓ |
| Separate LLM call | Send transcript to Claude/OpenRouter | |
| You decide | Claude picks based on platform support | |

**User's choice:** Platform's built-in analysis feature.

---

## Outcome Storage

| Option | Description | Selected |
|--------|-------------|----------|
| Update prospect row | Add outcome directly to existing row | ✓ |
| Separate outcomes table | Write to linked Call Outcomes table | |
| Both | Update row AND write to outcomes table | |

**User's choice:** Update prospect row directly. Simpler, everything in one place.

---

## Follow-Up Actions

| Option | Description | Selected |
|--------|-------------|----------|
| Log only | Log "would send" but don't send | |
| Console output | Print follow-up action to terminal | |
| You decide | Claude picks strongest demo impression | |

**User's choice:** Log wherever relevant. Since calls happen on the voice platform, logging should be in whatever script handles post-call processing. Airtable + console.

---

## Claude's Discretion

- Objection handling style (specific counters vs strategy vs hybrid)
- Voice-specific prompt optimizations
- variableValues injection structure
- Webhook/polling approach for post-call data
- Platform SDK vs raw API calls

## Deferred Ideas

- Real Calendly integration
- Real email follow-up
- Twilio number setup
- Separate Call Outcomes table
- Voicemail drop
