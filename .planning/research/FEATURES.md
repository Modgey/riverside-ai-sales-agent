# Feature Landscape: AI Cold-Calling / Outbound Sales System

**Domain:** AI-powered outbound sales pipeline with voice agent
**Researched:** 2026-04-20
**Context:** Home assignment for Riverside.fm GTM Engineer role. 3-day build. Reviewer grades Agentic Thinking, Technical Execution, Scalability, Business Context equally.

---

## Table Stakes

Features a reviewer will expect to see. Missing any of these = system looks incomplete or unserious.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| ICP-filtered prospect list | Every outbound system starts here. Calling random companies is not a system. | Low | Podcast Index API + category/cadence/recency filters. Already scoped. |
| Contact enrichment (name, email, company size) | Without this, the agent has nothing to personalize. Bare minimum for credibility. | Low | Apollo free tier. 10K credits, sufficient for 30-100 prospects. |
| Hard-filter disqualification before calling | Scoring without filtering wastes calls and burns budget. Every real system has a no-fly gate. | Low | Rules-based: company size, episode cadence, geography, missing data. |
| Skip/DNC (do not call) list | Legal and operational hygiene. Missing this in any real system is a red flag. | Low | Hand-curated at demo scale. Cross-check before dialing. |
| Shared system prompt (agent persona + pitch + rules) | Table stakes for any voice agent. Without this, the agent has no consistent behavior. | Medium | The "harness." Persona, Riverside pitch, tone, discovery questions, exit paths, safety rules. One prompt, all calls. |
| Per-call context injection | Without personalization, you have a robocall, not an AI agent. Every serious platform does dynamic variable injection. | Medium | Generated per prospect from cheat sheet. Opener, pain hypotheses, objection prep, relevance hooks. |
| Natural-sounding voice | Reviewers in 2026 expect sub-second response latency and human-like synthesis. A stilted robot voice disqualifies the demo immediately. | Low (platform handles it) | Vapi handles TTS + STT pipeline. Pick a good voice preset. |
| Basic objection handling (3-5 common objections) | "I'm not interested," "We already use X," "Send me info," "I'm busy." Missing handlers = agent gets stuck or sounds broken. | Medium | Scripted branches in system prompt. Not LLM-improvised for every edge case at this stage. |
| Call outcome classification | Without this, there is no post-call record. Unclassified calls are worthless data. | Low-Medium | LLM classifies transcript into: booked, interested, not-a-fit, voicemail, no-answer, do-not-call. |
| Persistent prospect database with call status | Reviewer needs to see populated data without running code. Static JSON fails this. | Low | Airtable free tier. Enrichment fields, score, call status, outcome, timestamp. |
| 2-3 recorded demo calls covering distinct outcomes | Without demos, there is nothing to evaluate. This IS the submission artifact for Part 2. | Low (effort) | Interested + objection + voicemail/disqualify scenarios minimum. |

---

## Differentiators

Features that go beyond expectations. These are what separate "built a thing" from "strategic builder."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Harness + call context architecture (clean separation) | Shows architectural thinking, not just "big system prompt." Reviewers who understand LLM systems will immediately recognize this as the right pattern. Harness = stable, context = variable. | Medium | Cheat sheet is the intermediate artifact. LLM generates call context from cheat sheet. Agent consumes harness + context. Three distinct layers with clear responsibilities. |
| LLM-generated call context from structured cheat sheet | Most demos inject raw CRM fields as variables. Generating a narrative opener, pain hypotheses, and predicted objections from structured data is a harder, more impressive step. | Medium | GPT-4o or Claude call. Input: enriched prospect record. Output: opener sentence, 2-3 pain angles, 2-3 objection predictions, one relevance hook (e.g., recent episode topic). |
| Mid-call function calling (Calendly + signup link) | Turns the agent from a data-collector into a transaction-completer. Reviewers evaluating Agentic Thinking will look for this. | Medium | Vapi tools/webhooks. On meeting-interest signal, agent triggers Calendly link delivery via SMS or email. On signup-intent, sends Riverside trial link. |
| Scoring layer as the quality gate (not human review) | This is the Scalability story. "Human reviews list before calls go out" does not scale. Scoring IS the filter. Demonstrating that the pipeline runs end-to-end without human in the loop is the claim. | Low-Medium | Weighted score: episode cadence (40%), company size fit (30%), data completeness (20%), category match (10%). Threshold gate before dialing. |
| Generalizable architecture demonstrated by hand-written webinar demo | Shows the reviewer that the pipeline abstracts beyond the podcast ICP without building the full webinar pipeline. One hand-written cheat sheet run through the same LLM call-context step and voice agent proves the architecture. | Low (effort, high strategic signal) | One call using a manually built webinar-company cheat sheet. Identical harness, identical call context format, different input data. |
| Outcome handling that does something real (not just logging) | Most demos classify and stop. If the "booked" path actually sends a Calendly confirmation email, that is a working workflow, not a demo. | Medium | Single real action: post-call email with Calendly link on "interested" outcome. Everything else described in write-up. |
| Podcast-specific personalization signals | Generic enrichment (company size, industry) is what every outbound tool does. Using podcast metadata (episode topic, guest names, cadence trends, host LinkedIn bio) as personalization signals is domain-specific and shows research depth. | Low-Medium | Pull from RSS feed: episode title, description, guest names, episode count, last publish date. Feed into cheat sheet. LLM generates opener like: "I listened to your episode on [topic], and noticed you've been covering [angle]." |

---

## Anti-Features

Things to deliberately not build. Each one has a legitimate reason that can be stated in the write-up.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Automated audio/video quality classifier | 4-6 hours to build. 30 minutes of manual YouTube review covers the same ground at demo scale. ROI is negative. | Manual spot-check. Note in write-up: "At 100+/day scale, add a classifier node trained on Riverside's quality bar." |
| Programmatic Riverside-customer detector | Brittle (LinkedIn scraping, domain matching against unknown customer list). Hand-curated skip list of 20-30 known customers is faster and more reliable for a demo. | Hand-curated skip list. Write-up describes the automation path. |
| Webinar discovery pipeline | No clean single API for webinar discovery. Would cost 10+ hours. Strategic value captured in write-up + one hand-written demo cheat sheet. | Write-up: "Next I'd build X using Y signals." One demo call proves the architecture generalizes. |
| CRM integration (Gong, Salesforce, HubSpot) | Real integration would consume 4-8 hours on auth, field mapping, error handling. Reviewer cannot evaluate the plumbing anyway, only the concept. | Write-up describes routing: "Booked outcomes post to Salesforce via webhook. Gong transcript sync for coaching." Airtable is the visible demo database. |
| Multi-step follow-up sequences (email drip, retry scheduling) | Outbound sequencing is a solved problem (Outreach, Salesloft). Adding it here adds no new signal for the reviewer and burns time. | Write-up describes retry logic ("No-answer prospects retry at +48h with different caller ID"). Not built. |
| Full outcome handling automation (all 6 outcome paths wired) | Building all 6 automated paths (booked, interested, not-a-fit, voicemail, no-answer, DNC) each with real downstream actions is 6-12 hours. Only one path (interested / booked) matters for the demo story. | Build one real action (Calendly email on interested). Describe the rest. |
| Parallel dialing / power dialer | Production feature for scale. Irrelevant at demo scale (30-100 prospects). Adds infrastructure complexity with zero demo value. | Vapi places calls sequentially. Write-up: "Production version runs N simultaneous calls via Vapi's concurrent call API." |
| Real-time rep coaching / call whisper | A different product (Gong-style assist). Out of scope entirely for an outbound agent. | Not mentioned. |
| Lead routing to human closer | Valid production feature. But for this demo, there is no human closer to route to. | Write-up: "On hot-lead signal, agent says 'Let me get you with our team' and triggers a Slack alert to the AE on duty." |
| A/B testing framework for messages/openers | Relevant at scale. Requires call volume to produce statistically meaningful data. 30 calls produces nothing useful. | Write-up: "At 500+/day volume, track open rate by opener variant and feed signal back into prompt selection." |
| Compliance/TCPA automation (do-not-call registry scrub, opt-out handling) | Necessary in production, irrelevant for a demo using test phone numbers. Over-engineering. | Note in write-up: "Production version scrubs against TCPA DNC registry pre-dial via API." Demo uses controlled test numbers only. |

---

## Feature Dependencies

```
Podcast Index API discovery
  → RSS feed parsing (host name, episode metadata)
    → Apollo enrichment (email, company size, firmographics)
      → Scoring + hard-filter gate
        → Skip list cross-check
          → Cheat sheet assembly (structured data bundle)
            → LLM call context generation (opener, pain angles, objections, hooks)
              → Voice agent call (harness + call context)
                → Mid-call function calling (Calendly, signup link)  [optional, differentiator]
                  → Post-call transcript + outcome classification
                    → Airtable update (status, outcome, timestamp)
                      → One real follow-up action on "interested" outcome  [optional, differentiator]
```

Key dependency: scoring/filter gate MUST run before calling. Call context generation MUST happen after enrichment. These cannot be reordered.

Cheat sheet is the dependency bridge: pipeline writes it, LLM reads it, agent never sees it directly. This clean boundary is load-bearing for the architecture story.

---

## MVP Recommendation

Given 3-day timeline and a reviewer evaluating strategy as heavily as code:

**Build all table stakes.** No exceptions. Missing any one of these undermines the submission.

**Build these differentiators (high signal-to-effort ratio):**
1. Harness + call context architecture (the clean separation IS the strategic demonstration)
2. LLM-generated call context from cheat sheet (shows AI used correctly, not as a crutch)
3. Mid-call function calling for meeting booking (proves the agent transacts, not just talks)
4. Podcast-specific personalization signals from RSS (domain-specific, distinguishes from generic outbound demo)
5. Generalizable architecture via one webinar demo call (strategic signal with low build cost)

**Defer or skip these differentiators:**
- Real follow-up email action: build only if time permits after core pipeline works
- Sophisticated scoring formula: simple weighted score is fine, don't tune it

**Do not build any anti-features.** Each one goes in the write-up with a crisp reason. The write-up is half the grade.

---

## Sources

- [AI Cold Calling Complete Guide 2026 | Auto Interview AI](https://www.autointerviewai.com/blog/ai-cold-calling-complete-guide-outbound-sales-2026)
- [Vapi Tools Documentation](https://docs.vapi.ai/tools)
- [Vapi Prompting Guide](https://docs.vapi.ai/prompting-guide)
- [AI Cold Calling: Synthflow 2026](https://synthflow.ai/blog/ai-in-cold-calling)
- [10 Mistakes Deploying AI Agents | SaaStr](https://www.saastr.com/weve-deployed-20-ai-agents-here-are-the-10-mistakes-almost-everyone-makes/)
- [Outbound AI: Hype vs Real | Reply.io](https://reply.io/blog/outbound-ai/)
- [AI Voice Agent Prompting | Aloware 2025](https://aloware.com/blog/how-to-prompt-your-ai-voice-agent)
- [ICP Scoring Strategy 2026 | Prospeo](https://prospeo.io/s/icp-sales-strategy)
- [Best Enrichment Tools for Outbound 2026 | SyncGTM](https://syncgtm.com/blog/best-enrichment-tools-for-outbound-sales-2026)
