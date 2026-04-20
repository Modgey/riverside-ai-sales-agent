# Domain Pitfalls: AI Cold-Calling Voice Agent

**Domain:** AI-powered outbound sales voice agent (Vapi + LLM + enrichment pipeline)
**Researched:** 2026-04-20
**Scope:** Specific to this project's stack (Vapi, Claude, Airtable, Python pipeline) on a 3-day timeline

---

## Critical Pitfalls

Mistakes that cause rewrites, demo failures, or blown timelines.

---

### Pitfall 1: Vapi's `startSpeakingPlan` default adds 1.5 seconds of silent dead air

**What goes wrong:** Vapi's default turn detection waits for punctuation cues before passing the transcript to the LLM. On outbound calls, where you're doing the talking, this setting adds ~1500ms of silence before the agent responds to anything the prospect says. The call sounds like it's frozen.

**Why it happens:** The `formatTurns` setting defaults to `true`, which buffers transcript until sentence boundaries are detected. Disabling it means the raw transcript goes to the LLM immediately.

**Consequences:** Every prospect interaction has an extra 1.5-second pause before the agent responds. At that latency, prospects hang up or assume something is broken. Demo calls feel broken even if everything else works.

**Prevention:**
- Set `formatTurns: false` in the assistant's `startSpeakingPlan` before your first test call.
- Target a total pipeline latency under 1200ms per turn (STT + LLM + TTS combined). Above that, conversations feel unnatural.
- Prefer GPT-4o Mini or a Groq-hosted model over GPT-4o for lower time-to-first-token.

**Detection:** Record a test call and measure the gap between when you stop speaking and when the agent starts. More than 1.2 seconds means this setting is misconfigured.

**Phase:** Vapi setup, first test call session.

---

### Pitfall 2: Prompt written for chat, not speech

**What goes wrong:** Copy-pasting a text-based system prompt into Vapi produces responses that are grammatically correct but unnatural when spoken aloud. The agent sounds like a press release reading itself.

**Why it happens:** Chat prompts optimize for reading. Voice prompts must optimize for hearing. Numbers ("4:30 PM"), bullet-style lists, percentages, abbreviations, and long compound sentences all degrade voice quality.

**Consequences:** The demo call sounds robotic. The reviewer's first impression is that this is a low-quality AI wrapper, not a thoughtful build. This is the single easiest way to fail the "Business Context" grading axis.

**Prevention:**
- Write every agent utterance as if dictating it aloud. Read it out loud before testing it.
- Spell out numbers and times in words ("four thirty PM," not "4:30 PM").
- Keep each agent turn to 2-3 sentences max. Voice listeners can't scroll back.
- Add natural speech markers to the system prompt: allow "um," "actually," brief pauses. Do not allow lists, markdown, or structured formatting in responses.
- Explicitly instruct the model: "You are speaking on a phone call. Never use bullet points, headers, or numbered lists. Keep responses under 30 words per turn."

**Detection:** Read the agent's responses aloud. Anything that trips over your tongue in natural speech will sound wrong on the call.

**Phase:** Harness prompt design, before any Vapi integration.

---

### Pitfall 3: Vapi's free tier blocks international calls and caps at 10 outbound calls/day

**What goes wrong:** Vapi's free phone numbers cannot call international numbers and are capped at 10 outbound calls per day per organization. If your test numbers are outside the US (e.g., Shawn is in Tel Aviv), every outbound call attempt will fail silently or return an error.

**Why it happens:** Vapi's free telephony tier is US-only for outbound. International numbers require a Twilio or Vonage import.

**Consequences:** Hours lost debugging what looks like a configuration error when it's actually a tier restriction. Demo blocked if you can't reach your test phone.

**Prevention:**
- If testing with an Israeli phone number, import a Twilio number immediately (not "later"). Twilio has international coverage and Vapi supports Twilio import directly.
- Budget $1-2 for a Twilio number and a handful of test call minutes. This is within the $10-15 project budget.
- Confirm the call flow works on a US number (use Google Voice or a friend's US number) before troubleshooting international issues.

**Detection:** Vapi call logs will show a failed call event. If the call never rings on your end, check whether the destination number is international.

**Phase:** Vapi account setup, day 1.

---

### Pitfall 4: Voicemail detection misfires and breaks the demo scenario

**What goes wrong:** Vapi's voicemail detection has two failure modes: (1) false positive, where a live human is classified as voicemail and the agent immediately hangs up or leaves a canned message, and (2) false negative, where the agent starts its live pitch into a voicemail inbox. For demo recordings, a false positive on a live call is embarrassing.

**Why it happens:** Twilio-based voicemail detection is explicitly documented as "prone to false positives." The LLM-based detection (recommended) still requires good prompting and is in beta.

**Consequences:** Demo recording shows agent hanging up on a live human. Or the demo shows the agent delivering a pitch to a beep. Neither is what the reviewer wants to see.

**Prevention:**
- Use the LLM-based detection method (not Twilio's built-in), and set `maxDetectionRetries: 3`.
- For demo calls to known numbers (your phone, a friend's phone), you can disable voicemail detection entirely and just handle the call as live. The demo doesn't need to prove voicemail logic if it distracts from the pitch.
- If you record a "voicemail demo scenario," set it up deliberately with a real voicemail greeting and script the expected behavior. Don't leave it to chance.
- Set `beepMaxAwaitSeconds` to at least 20 seconds to avoid cutting off long voicemail greetings mid-message.

**Detection:** Run a test where you intentionally let the call go to voicemail and observe what the agent does.

**Phase:** Vapi integration, before demo recording sessions.

---

### Pitfall 5: Webhook server isn't reachable during call, causing tool calls to silently hang

**What goes wrong:** Vapi calls your `serverURL` webhook for function calling (booking a meeting, sending a link). If your server isn't running, returns an error, or takes more than 7.5 seconds to respond, the tool call times out. The agent either freezes or continues without completing the action.

**Why it happens:** Vapi enforces a hard 7.5-second response deadline on webhook calls (with another 7.5 seconds reserved for call setup within the telephony provider's 15-second cap). A cold-start on a free-tier cloud function, a sleeping Render instance, or a local server behind ngrok with a slow tunnel all blow this deadline.

**Consequences:** The agent says "I'll send you a signup link" and then nothing happens. Or the agent freezes mid-call. This is a critical demo failure because the mid-call function call (booking, link send) is a core feature.

**Prevention:**
- For demo purposes, use a pre-warmed server or a simple FastAPI endpoint on a $0 Railway or Render instance that stays awake.
- If using ngrok locally, start it before the call and test the tunnel round-trip latency first.
- Set your webhook response to return quickly with a stub value during development, then wire up real logic once the call flow works.
- Keep the webhook server collocated near Vapi's infrastructure (us-west-2) to minimize network round-trip.

**Detection:** Check Vapi call logs for `tool-call-failed` or `tool-call-timeout` events after any demo call that included a function call.

**Phase:** Function calling integration (mid-call Calendly/link-send feature).

---

## Moderate Pitfalls

These don't block the build but produce bad demos or wasted hours.

---

### Pitfall 6: Agent goes off-script when prospect says something unexpected

**What goes wrong:** The agent handles the scripted scenarios fine (opener, pitch, standard objections) but falls apart when a prospect says something unexpected: "wait, are you a robot?", "I use Streamyard, not Zoom," or a long tangent. The LLM improvises, sometimes fabricating pricing details, feature claims, or Riverside product capabilities it doesn't actually have.

**Why it happens:** The harness prompt defines behavior but the LLM's default is to be helpful, which means filling gaps with plausible-sounding (but potentially wrong) information.

**Consequences:** Agent makes a claim Riverside doesn't support. Reviewer catches it and the "Business Context" score drops. Or the agent gives a rambling non-answer that kills conversation flow.

**Prevention:**
- Explicitly include a "what to do when you don't know" rule in the harness: "If asked a question you don't have an answer for, say 'That's a great question, I'd want to connect you with someone from our team who can answer that specifically' and route to booking."
- Constrain temperature to 0.3-0.5 for the voice agent. Lower temperature means less improvisation.
- Include the actual Riverside pricing tiers and feature list in the harness as a hard-reference block. The agent can only cite what's in the prompt.
- Test with adversarial inputs before recording demos.

**Detection:** During test calls, deliberately ask off-script questions: "What's the price?", "Do you integrate with X?", "Can you guarantee X quality?"

**Phase:** Harness prompt design and testing.

---

### Pitfall 7: Endpointing cuts the prospect off mid-sentence, creating awkward demo moments

**What goes wrong:** Vapi's voice activity detection (VAD) treats a natural mid-sentence pause as "end of turn" and starts the agent's response before the prospect finishes speaking. The agent talks over the prospect. On demo recordings this looks like a broken interrupt system.

**Why it happens:** The default endpointing sensitivity is aggressive. A 200ms silence triggers a turn switch, but natural speech has pauses longer than 200ms within sentences (especially when someone is thinking).

**Consequences:** Demo recording shows the agent cutting off a sentence. This is one of the most visible quality signals a reviewer will use to evaluate the build.

**Prevention:**
- Set endpointing to ~255ms (documented sweet spot for English in Vapi's own testing across 50k+ calls).
- Enable smart endpointing if available on your Vapi plan.
- During test calls, vary your speaking pace and include deliberate pauses to validate the setting works.
- Script demo calls so prospects (you or your friend) speak in complete, short sentences without long pauses. This reduces the chance of a mid-sentence cutoff appearing in the recording.

**Detection:** Record a test call and watch for any moment where the agent responds before you finish a sentence.

**Phase:** Vapi assistant configuration, before demo recording.

---

### Pitfall 8: Webhook for call context injection adds latency to call start

**What goes wrong:** If you inject per-call context by fetching it dynamically at call start via a webhook, and that webhook does database reads, LLM calls, or external API calls, the call setup time increases. The prospect hears dead air for 2-5 seconds before the agent speaks.

**Why it happens:** The harness + call context architecture is correct, but if the call context isn't pre-generated and cached before the call is placed, it must be fetched live, adding to call setup latency.

**Consequences:** Dead air at call start. Prospects hang up. Demo recording starts with a multi-second silence.

**Prevention:**
- Pre-generate all call context (the LLM-generated opener, pain point hypotheses, objection handlers) at pipeline time, before the call is placed. Store the generated text in Airtable.
- At call time, the Vapi assistant configuration includes the pre-built call context inline. No webhook fetch needed at call start.
- This matches the intended architecture (pipeline generates cheat sheets -> LLM produces call contexts -> voice agent consumes at call time). Don't shortcut this by doing it live.

**Detection:** Measure time from "call placed" to "agent says first word." More than 3 seconds means something is happening at call start that should happen earlier.

**Phase:** Pipeline integration, call context assembly step.

---

### Pitfall 9: Apollo free tier enrichment returns empty or wrong company size data

**What goes wrong:** Apollo's free tier provides company size data, but the underlying signal is often stale or missing for smaller companies. A prospect that should score as "too small" passes enrichment with no company size data, gets scored as "unknown," and ends up in the call queue. The agent calls someone who is clearly not ICP.

**Why it happens:** Apollo's free tier doesn't guarantee data completeness, especially for companies under 200 employees. The scoring model needs to handle null enrichment gracefully.

**Consequences:** Demo pipeline processes non-ICP prospects. If one of those calls gets recorded, the reviewer sees an off-target pitch. The "Agentic Thinking" score drops because the filtering is clearly not working.

**Prevention:**
- In the scoring layer, treat missing company size as a hard disqualification ("unknown = out"). Don't default to in-range.
- Cross-check company size with a second signal from the RSS feed or podcast metadata where possible (e.g., sponsor categories often correlate with company tier).
- For demo purposes, hand-validate the final call list of 5-10 prospects before placing calls. The write-up notes "scoring IS the quality gate," but for a 3-day build, a 5-minute manual spot-check is acceptable and doesn't break the scalability story.

**Detection:** After enrichment, log and inspect how many records have null company size. If more than 30%, the enrichment step has a reliability problem worth addressing.

**Phase:** Enrichment and scoring pipeline.

---

## Minor Pitfalls

Known annoyances that are manageable but worth knowing upfront.

---

### Pitfall 10: Vapi dashboard changes don't save reliably

**What goes wrong:** About 50% of the time, modifying an assistant field in the Vapi dashboard appears to save but silently reverts on reload. Configuration changes you think are live are not.

**Prevention:** Always configure assistants via the API or SDK, not the dashboard UI. Treat the dashboard as read-only for inspection. All configuration should live in code (or a config file) and be applied programmatically.

**Phase:** Vapi setup.

---

### Pitfall 11: Call context prompt length blows the practical token budget

**What goes wrong:** The per-prospect call context (opener, pain points, objections, relevance hooks) is injected into the harness. If this block is too long, it crowds out the harness instructions, and the agent prioritizes the wrong instructions or forgets behavioral rules.

**Why it happens:** LLMs process earlier tokens with higher weight. If a large call context block comes before behavioral rules in the prompt, those rules get deprioritized under token pressure.

**Prevention:**
- Harness first, call context second. Behavioral rules and guardrails always precede the per-call data.
- Keep the call context injection under ~300 tokens (roughly a paragraph of opener + 3 bullet pain points + 2 objections).
- The LLM-generated call context step should explicitly output a constrained format, not free-form text.

**Phase:** Harness design and call context generation step.

---

### Pitfall 12: Podcast Index API returns inactive or defunct shows

**What goes wrong:** Podcast Index includes shows that haven't published in 6-24 months. The RSS feed is still accessible, which passes the "has an RSS feed" filter, but the company is no longer actively podcasting. The prospect gets a call referencing their podcast, which ended a year ago.

**Prevention:**
- Filter on `lastPublishTime` in the Podcast Index response. Require an episode within the last 60 days to qualify as "active."
- Parse the RSS feed's most recent episode date as a hard filter, not advisory.

**Phase:** Discovery and filtering pipeline.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Vapi first setup | International call blocking, free tier limit | Import Twilio number on day 1 |
| Harness prompt writing | Chat-style prose sounds robotic | Read every response aloud before testing |
| First test call | Dead air from `startSpeakingPlan` default | Disable `formatTurns` before first call |
| Function calling setup | Webhook timeout (7.5s hard limit) | Pre-warm server, test round-trip before recording |
| Demo recording | Endpointing cuts off speech | Set 255ms, test with varied pacing |
| Voicemail scenario | Detection misfire | Disable detection for known-live demo numbers |
| Pipeline enrichment | Null company size passes filter | Treat null as hard disqualification |
| Call context generation | Prompt too long, crowds harness | Cap context block at ~300 tokens, harness first |
| Podcast discovery | Inactive shows pass RSS filter | Hard filter on `lastPublishTime` within 60 days |
| Demo day | Agent improvises off-script | Low temperature (0.3), explicit "I don't know" rule |

---

## Sources

- Vapi Prompting Guide: https://docs.vapi.ai/prompting-guide
- Vapi Outbound Calling docs: https://docs.vapi.ai/calls/outbound-calling
- Vapi Voicemail Detection docs: https://docs.vapi.ai/calls/voicemail-detection
- Vapi Free Telephony: https://docs.vapi.ai/free-telephony
- Vapi Server URLs: https://docs.vapi.ai/server-url
- AssemblyAI: Biggest challenges in building AI voice agents: https://www.assemblyai.com/blog/biggest-challenges-building-ai-voice-agents-how-assemblyai-vapi-are-solving-them
- AssemblyAI: How to build the lowest latency voice agent in Vapi: https://www.assemblyai.com/blog/how-to-build-lowest-latency-voice-agent-vapi
- Vapi: How we solved latency: https://vapi.ai/blog/how-we-solved-latency-at-vapi
- Vapi: Speech latency guide: https://vapi.ai/blog/speech-latency
- Sayna AI: Handling barge-in: https://sayna.ai/blog/handling-barge-in-what-happens-when-users-interrupt-your-ai-mid-sentence
- AlterSquare: VAD end-of-speech detection in production: https://altersquare.io/vad-end-of-speech-detection-hardest-problem-production-voice-agents/
- Retell AI: Guide to AI hallucinations in voice agents: https://www.retellai.com/blog/the-ultimate-guide-to-ai-hallucinations-in-voice-agents-and-how-to-mitigate-them
- Hamming AI: Voice agent incident response runbook: https://hamming.ai/resources/voice-agent-incident-response-runbook
- Dograh: Vapi pricing hidden costs: https://blog.dograh.com/vapi-pricing-breakdown-2025-plans-hidden-costs-what-to-expect/
