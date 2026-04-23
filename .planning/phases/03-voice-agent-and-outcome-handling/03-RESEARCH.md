# Phase 3: Voice Agent and Outcome Handling - Research

**Researched:** 2026-04-23
**Domain:** Vapi voice AI platform, outbound calling, post-call analysis, Airtable outcome writing
**Confidence:** HIGH

## Summary

Phase 3 builds the voice agent that places outbound cold calls via Vapi, handles mid-call tool invocations (simulated book_meeting, send_signup_link), classifies call outcomes using Vapi's built-in analysisPlan, and writes results back to Airtable. The existing pipeline already produces call_context.json with prospects that have an opener, prospect_context, and personalized_angles. This phase consumes that output and adds the voice execution layer.

Vapi's Python server SDK (vapi-server-sdk v1.11.0) provides `client.calls.create()` for outbound calls. The assistant can be defined inline (transient) or referenced by ID. Per-prospect personalization is injected via `assistantOverrides.variableValues` using `{{variable}}` syntax in the system prompt. Custom tools (book_meeting, send_signup_link) are defined in the assistant config with a server URL that Vapi POSTs to mid-call. Post-call analysis uses `analysisPlan` with `structuredDataSchema` and `structuredDataPrompt` to classify outcomes automatically, with results available via the API on the call object.

**Primary recommendation:** Use Vapi with an inline transient assistant per call (not a saved assistant), passing the full config including tools, analysisPlan, and variableValues in each `calls.create()` call. This avoids dashboard setup and keeps everything in code. For the demo, use Vapi's free phone number for US calls. Since Shawn is in Tel Aviv, a Twilio number ($1.15/mo) may be needed for international, but test the free number first with a US test number.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Platform choice is OPEN. Researcher must compare Vapi vs. Retell. Pick whichever gets to demo quality fastest.
- **D-02:** No Twilio setup needed for demo. Use platform-provided number. Wire code for easy Twilio swap later.
- **D-03:** Latency config matters. Document latency-critical settings.
- **D-04:** Guided framework approach. System prompt provides conversation structure (opener -> discovery -> pitch -> close), objection handling, safety rules. Claude improvises actual words.
- **D-05:** SDR persona. Agent calls from Riverside. Does not volunteer it's AI, answers honestly if asked.
- **D-06:** Core Riverside features only in prompt. 4K local recording, separate tracks, text-based editing, live streaming. Keep prompt lean.
- **D-07:** Objection handling approach is Claude's discretion.
- **D-08:** Discovery before pitch. Confirm right person, ask about workflow, editing, pain points before pitching. One question at a time.
- **D-09:** Safety rules: no pricing promises, respect DNC, 5-min time limit awareness, factual competitor comparison only.
- **D-10:** Prompt structure follows MID Construction Eddie pattern: First Message, Role, Task, Specifics, Context, Examples.
- **D-11:** Gatekeeper/voicemail handling: voicemail = hang up, gatekeeper = ask for prospect by first name, IVR = try human else hang up.
- **D-12:** Harness stays identical across all calls. Only variableValues change.
- **D-13:** Simulated tools, not real integrations. Canned success responses.
- **D-14:** Write-up explains production tool architecture.
- **D-15:** Post-call classification via platform's built-in analysis (Vapi analysisPlan).
- **D-16:** Six outcome categories: booked, interested, not-a-fit, voicemail, no-answer, do-not-call.
- **D-17:** Update existing prospect row in Airtable (not separate table).
- **D-18:** Follow-up actions logged but not actually sent.

### Claude's Discretion
- Exact objection handling style
- Voice-specific prompt optimizations
- variableValues field structure
- Webhook/polling approach for post-call data
- Whether to use SDK or raw API calls

### Deferred Ideas (OUT OF SCOPE)
- Real Calendly integration
- Real email sending
- Twilio number setup for international
- Separate Call Outcomes table
- Per-role prompt templates
- Voicemail drop
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VOIC-01 | Shared harness defines persona, value prop, tone, discovery flow, safety rules | Vapi system prompt with `{{variable}}` placeholders, Eddie/MID Construction pattern, voice prompting guide |
| VOIC-02 | Agent handles 5+ common objections | Objection strategies embedded in system prompt specifics section |
| VOIC-03 | Agent conducts discovery (recording workflow, content output, pain points) | System prompt task section with step-by-step conversation flow and `<wait for user response>` markers |
| VOIC-04 | Agent follows defined exit paths (book meeting, send signup, goodbye, flag follow-up) | Custom tools for book_meeting and send_signup_link, plus conversational exit patterns |
| VOIC-05 | Mid-call function calling for meeting booking | Vapi custom tools with server URL, tool schema definition, canned response |
| VOIC-06 | Mid-call function calling for signup link | Same tool mechanism as VOIC-05 |
| VOIC-07 | Harness identical across calls, only per-call context changes | `assistantOverrides.variableValues` injection at call time |
| OUTC-01 | Classify each call outcome (6 categories) | Vapi `analysisPlan.structuredDataSchema` with enum classification |
| OUTC-02 | Update Airtable with outcome, notes, timestamp | Extend `upload.py` field mapping, use pyairtable `batch_upsert()` |
| OUTC-03 | Fire at least one real follow-up action | Log follow-up action to console and Airtable field (simulated, per D-18) |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Voice conversation (STT/LLM/TTS) | Vapi Platform | -- | Vapi owns the real-time audio stack, turn-taking, and Claude integration |
| Call placement (outbound dial) | Vapi Platform | -- | `calls.create()` API handles telephony |
| System prompt / harness | Python call runner | Vapi Platform | Defined in Python code, sent to Vapi as inline assistant config |
| Per-call personalization | Python call runner | Vapi Platform | Python reads call_context, passes as variableValues to Vapi |
| Mid-call tool execution | Python HTTP server | Vapi Platform | Vapi POSTs tool calls to server URL, server returns canned response |
| Post-call outcome classification | Vapi Platform | -- | analysisPlan runs on Vapi infra automatically |
| Outcome persistence (Airtable) | Python call runner | -- | Python reads call results from Vapi API, writes to Airtable |
| Prospect data | Airtable / local JSON | -- | Existing pipeline output, read by call runner |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vapi-server-sdk | 1.11.0 | Vapi API client: create calls, retrieve call results | Official Python SDK, handles auth and typing [VERIFIED: GitHub VapiAI/server-sdk-python] |
| pyairtable | 3.3.0 | Airtable API client for outcome writes | Already in project, handles rate limiting [VERIFIED: existing requirements.txt] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| flask | 3.x | Lightweight HTTP server for mid-call tool webhooks | Only if testing tool calls locally. For demo, can use a simple HTTP handler |
| pydantic | 2.x | Structured data models for call config and outcomes | Already in project [VERIFIED: existing requirements.txt] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vapi | Retell AI | Retell has slightly lower latency (2.1s vs 2.6s) but no free credits, less mature Python SDK, and no clear advantage for a 3-day demo. Vapi's $10 free credit and confirmed Claude support make it the faster path. [CITED: STACK.md, D-01 research] |
| vapi-server-sdk | Raw requests | SDK handles auth, typing, and retries. Raw requests add boilerplate for no benefit. |
| Flask for webhooks | No webhook server | Simulated tools can return canned responses without a real server. Vapi tools can be configured without a server URL if we accept the limitation. However, tool calls require a server URL endpoint. |

**Installation:**
```bash
pip install vapi-server-sdk
```

## Architecture Patterns

### System Architecture Diagram

```
CALL TIME FLOW
==============

[call_context.json] --> [Call Runner (Python)]
                              |
                              | client.calls.create(
                              |   assistant={inline config},
                              |   phoneNumberId=...,
                              |   customer={number: "+1..."},
                              |   assistantOverrides={
                              |     variableValues: {opener, prospect_context, angles}
                              |   }
                              | )
                              v
                        [Vapi Platform]
                         STT (Deepgram)
                         LLM (Claude Sonnet 4)
                         TTS (provider TBD)
                              |
                    +---------+---------+
                    |                   |
              [Mid-Call Tool]     [Call Ends]
              Vapi POSTs to           |
              webhook server          v
                    |           [analysisPlan runs]
                    v           structuredData extracted
              [Tool Server]           |
              Returns canned          v
              response          [Call Runner polls]
                    |           GET /calls/{id}
                    v                 |
              Agent speaks            v
              confirmation      [Airtable Update]
                                outcome, notes, timestamp
```

### Recommended Project Structure
```
src/
  pipeline/
    voice_agent.py      # Vapi assistant config builder + call placement
    outcome_handler.py  # Poll Vapi for results, classify, write Airtable
    prompts/
      harness.txt       # System prompt for voice agent (plain text, not JSON)
  call_runner.py        # CLI entry point: place calls + handle outcomes
  tool_server.py        # Simple HTTP server for mid-call tool webhooks (optional)
```

### Pattern 1: Inline Transient Assistant
**What:** Pass the full assistant config (system prompt, model, tools, analysisPlan) directly in `calls.create()` instead of pre-creating a saved assistant.
**When to use:** Always, for this project. Keeps everything in code, no dashboard state.
**Example:**
```python
# Source: https://docs.vapi.ai/calls/outbound-calling
from vapi import Vapi

client = Vapi(token=os.getenv("VAPI_API_KEY"))

call = client.calls.create(
    assistant={
        "model": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": HARNESS_PROMPT}
            ],
        },
        "voice": {
            "provider": "11labs",  # or "cartesia"
            "voiceId": "some-voice-id",
        },
        "firstMessage": "{{opener}}",
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
        },
        "tools": [BOOK_MEETING_TOOL, SEND_SIGNUP_TOOL],
        "analysisPlan": ANALYSIS_PLAN,
        "silenceTimeoutSeconds": 30,
        "startSpeakingPlan": {
            "waitSeconds": 0.2,
        },
    },
    assistant_overrides={
        "variable_values": {
            "opener": prospect_context["opener"],
            "prospect_context": prospect_context["prospect_context"],
            "angle_1": prospect_context["personalized_angles"][0],
            "angle_2": prospect_context["personalized_angles"][1] if len(prospect_context["personalized_angles"]) > 1 else "",
        }
    },
    phone_number_id=os.getenv("VAPI_PHONE_NUMBER_ID"),
    customer={"number": target_phone},
)
```

### Pattern 2: Dynamic Variable Injection
**What:** Use `{{variableName}}` in the system prompt, replaced at call time via `variableValues`.
**When to use:** For all per-prospect personalization.
**Example:**
```python
# Source: https://docs.vapi.ai/assistants/dynamic-variables
# In the system prompt:
HARNESS = """
## Prospect Context
The person you're calling: {{prospect_context}}

## Your Opening Line
Start the call with: {{opener}}

## Personalized Angles
Use these observations naturally during discovery:
- {{angle_1}}
- {{angle_2}}
"""

# At call time, pass:
assistant_overrides = {
    "variable_values": {
        "opener": "Hey Noah, saw your recent episode with Meghan Joyce. Quick question for you.",
        "prospect_context": "Noah hosts Code Story, a founder interview show...",
        "angle_1": "Other hosts interviewing external founders...",
        "angle_2": "",
    }
}
```

### Pattern 3: Custom Tool Definition
**What:** Define tools the agent can invoke mid-call. Vapi POSTs to your server URL.
**When to use:** For book_meeting and send_signup_link simulated actions.
**Example:**
```python
# Source: https://docs.vapi.ai/tools/custom-tools
BOOK_MEETING_TOOL = {
    "type": "function",
    "function": {
        "name": "book_meeting",
        "description": "Book a demo meeting with the prospect. Call this when the prospect agrees to a meeting or demo.",
        "parameters": {
            "type": "object",
            "properties": {
                "prospect_name": {"type": "string", "description": "The prospect's name"},
                "preferred_time": {"type": "string", "description": "When they want to meet, if mentioned"},
            },
            "required": ["prospect_name"],
        },
    },
    "server": {
        "url": "https://your-server.com/tool-handler",
    },
}

# Server response format:
# POST body includes: toolCallId, function name, arguments
# Response:
{
    "results": [
        {
            "toolCallId": "call_abc123",
            "result": "Meeting booked! I've sent a calendar invite to their email."
        }
    ]
}
```

### Pattern 4: analysisPlan for Outcome Classification
**What:** Configure Vapi to automatically classify the call after it ends.
**When to use:** For OUTC-01, classifying into the 6 outcome categories.
**Example:**
```python
# Source: https://docs.vapi.ai/assistants/call-analysis
ANALYSIS_PLAN = {
    "structuredDataPrompt": (
        "Classify this sales call outcome into exactly one category. "
        "Analyze the full transcript and determine:\n"
        "- 'booked': prospect agreed to a meeting or demo\n"
        "- 'interested': prospect showed interest but didn't commit to a meeting\n"
        "- 'not-a-fit': prospect is not a good fit or declined the offer\n"
        "- 'voicemail': call went to voicemail\n"
        "- 'no-answer': nobody answered the call\n"
        "- 'do-not-call': prospect explicitly asked not to be called again\n\n"
        "Also provide a 1-2 sentence summary of the call outcome."
    ),
    "structuredDataSchema": {
        "type": "object",
        "properties": {
            "outcome": {
                "type": "string",
                "enum": ["booked", "interested", "not-a-fit", "voicemail", "no-answer", "do-not-call"],
                "description": "The classified outcome of the call"
            },
            "call_notes": {
                "type": "string",
                "description": "1-2 sentence summary of what happened on the call"
            },
            "follow_up_action": {
                "type": "string",
                "description": "What follow-up action should be taken based on the outcome"
            }
        },
        "required": ["outcome", "call_notes"]
    },
    "successEvaluationPrompt": "Did the agent successfully follow the sales script, handle objections well, and reach a clear next step?",
    "successEvaluationRubric": "PassFail",
}
```

### Pattern 5: Polling for Call Results
**What:** After placing a call, poll the Vapi API to get the call result and analysis.
**When to use:** Instead of setting up a webhook server for end-of-call-report. Simpler for demo.
**Example:**
```python
import time

def wait_for_call_result(client, call_id, timeout=600, poll_interval=5):
    """Poll Vapi until call completes and analysis is ready."""
    start = time.time()
    while time.time() - start < timeout:
        call = client.calls.get(call_id)
        if call.status == "ended":
            # Analysis runs in background, may take a few seconds after call ends
            if call.analysis and call.analysis.structured_data:
                return call
            time.sleep(2)  # Give analysis time to complete
            call = client.calls.get(call_id)
            return call
        time.sleep(poll_interval)
    raise TimeoutError(f"Call {call_id} did not complete within {timeout}s")
```

### Anti-Patterns to Avoid
- **Long system prompts:** Voice latency increases with prompt length. Keep the harness under 1500 tokens. No full product manuals, competitor matrices, or pricing tables. [CITED: docs.vapi.ai/prompting-guide]
- **Written-English formatting in prompts:** No lists, bullet points, parenthetical asides, semicolons, or em dashes in the system prompt. Everything will be spoken aloud. Use short sentences, contractions, conversational phrasing. [CITED: docs.vapi.ai/prompting-guide]
- **formatTurns default adding dead air:** Vapi's default endpointing adds 1.5s+ per turn. Set `startSpeakingPlan.waitSeconds` to 0.2 and tune from there. [CITED: docs.vapi.ai/customization/voice-pipeline-configuration]
- **Mentioning tools to the user:** Never say "let me use my booking tool" or "I'll call the function." Instruct the agent to silently invoke tools and speak only after the result returns. [CITED: docs.vapi.ai/prompting-guide]
- **Saved assistant with dashboard state:** For a code-first demo, inline transient assistants keep everything version-controlled and reproducible.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Voice conversation (STT+LLM+TTS) | Custom WebSocket audio pipeline | Vapi platform | Turn-taking, interruption handling, endpointing are extremely complex. Vapi handles all of this. |
| Post-call transcript classification | Separate Claude API call on transcript | Vapi analysisPlan with structuredDataSchema | Runs automatically on Vapi infra, result included in call data. Zero extra code or cost. |
| Phone number provisioning | Twilio setup + SIP trunking | Vapi free number (or import Twilio via dashboard) | One click in Vapi dashboard. $0 for US calls on free credit. |
| Endpointing / silence detection | Custom VAD (voice activity detection) | Vapi startSpeakingPlan config | Configurable via JSON, multiple providers, tuned presets available. |

**Key insight:** The entire voice pipeline (STT, LLM routing, TTS, telephony, turn-taking, recording) is Vapi's core product. Every hour spent building custom audio handling is an hour not spent on the harness prompt and demo quality.

## Common Pitfalls

### Pitfall 1: Vapi Free Number Limitations
**What goes wrong:** Free Vapi numbers have limited outbound calls per day and cannot make international calls.
**Why it happens:** Free tier restriction to prevent abuse.
**How to avoid:** For demo to US test numbers, the free number should work. If calling Tel Aviv or other international numbers, import a Twilio number ($1.15/mo). Test early.
**Warning signs:** Call creation returns an error about the phone number.
[CITED: docs.vapi.ai/phone-calling, docs.vapi.ai/phone-numbers/import-twilio]

### Pitfall 2: Endpointing Adding 1.5s+ Dead Air
**What goes wrong:** Default Vapi settings add significant delay before the agent responds, making conversation feel unnatural.
**Why it happens:** Conservative defaults prioritize not interrupting the user over response speed.
**How to avoid:** Set `startSpeakingPlan.waitSeconds` to 0.2. Use smart endpointing with an aggressive wait function for English. Set `silenceTimeoutSeconds` to 30 (not too low or calls drop during pauses).
**Warning signs:** Agent waits noticeably long after user stops speaking.
[CITED: docs.vapi.ai/customization/voice-pipeline-configuration]

### Pitfall 3: Tool Server Timeout (7.5s)
**What goes wrong:** Mid-call tool calls that hit a cold-starting server silently fail. Vapi has a 7.5-second timeout for tool webhook responses.
**Why it happens:** Server cold starts (especially on free hosting) exceed the timeout.
**How to avoid:** For simulated tools, the response is instant (canned JSON). If using a real server, pre-warm it. For demo, consider running a local server with ngrok.
**Warning signs:** Agent says something like "I wasn't able to do that" or just continues without confirming the action.
[CITED: BUILD-PLAN.md risks section]

### Pitfall 4: System Prompt Too Long for Voice
**What goes wrong:** Long prompts increase LLM inference time, adding latency to every turn.
**Why it happens:** Porting a text-style prompt with full product docs, competitor matrices, pricing tables.
**How to avoid:** Keep harness under 1500 tokens. Only include: persona, conversation flow, objection handling strategies (not scripts), safety rules, variable placeholders. Product features as brief bullet-level mentions, not paragraphs.
**Warning signs:** First response takes 3+ seconds, subsequent turns feel sluggish.
[CITED: docs.vapi.ai/prompting-guide]

### Pitfall 5: Analysis Not Ready When Polling
**What goes wrong:** Call ends but `call.analysis.structuredData` is null.
**Why it happens:** Analysis runs asynchronously after call end. "Typically completes within a few seconds" but not instant.
**How to avoid:** After detecting `call.status == "ended"`, wait 3-5 seconds and re-poll. Add a retry loop with exponential backoff up to 30 seconds.
**Warning signs:** Structured data is null on first poll after call ends.
[CITED: docs.vapi.ai/assistants/call-analysis]

### Pitfall 6: Voicemail Detection False Positives
**What goes wrong:** Vapi's voicemail detection triggers on a live person, hanging up a real call.
**Why it happens:** Voicemail detection algorithms have false positives, especially on certain phone systems.
**How to avoid:** For demo calls to known-live test numbers, consider disabling voicemail detection. The agent's prompt handles voicemail via D-11 (hang up on voicemail).
**Warning signs:** Calls to test numbers end immediately after connecting.
[CITED: BUILD-PLAN.md risks section]

## Code Examples

### Complete Call Placement Flow
```python
# Source: Synthesized from docs.vapi.ai/calls/outbound-calling + /assistants/dynamic-variables
import json
import os
import time
from vapi import Vapi

client = Vapi(token=os.getenv("VAPI_API_KEY"))

def load_harness() -> str:
    """Load the voice agent system prompt."""
    with open("src/pipeline/prompts/harness.txt", "r") as f:
        return f.read()

def build_assistant_config(harness: str) -> dict:
    """Build inline assistant config with tools and analysis plan."""
    return {
        "model": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "messages": [{"role": "system", "content": harness}],
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "TBD",  # Pick a natural male/female voice
        },
        "firstMessage": "{{opener}}",
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
        },
        "silenceTimeoutSeconds": 30,
        "startSpeakingPlan": {
            "waitSeconds": 0.2,
        },
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "book_meeting",
                    "description": "Book a demo meeting when prospect agrees",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prospect_name": {"type": "string"},
                        },
                        "required": ["prospect_name"],
                    },
                },
                "server": {"url": os.getenv("TOOL_SERVER_URL", "https://your-server/tools")},
            },
            {
                "type": "function",
                "function": {
                    "name": "send_signup_link",
                    "description": "Send Riverside free trial signup link when prospect wants to try it",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prospect_name": {"type": "string"},
                        },
                        "required": ["prospect_name"],
                    },
                },
                "server": {"url": os.getenv("TOOL_SERVER_URL", "https://your-server/tools")},
            },
        ],
        "analysisPlan": {
            "structuredDataPrompt": (
                "Classify this sales call. Categories:\n"
                "booked: agreed to meeting/demo\n"
                "interested: showed interest, no commitment\n"
                "not-a-fit: declined or not relevant\n"
                "voicemail: reached voicemail\n"
                "no-answer: nobody answered\n"
                "do-not-call: asked not to be called\n"
                "Provide outcome category and 1-2 sentence summary."
            ),
            "structuredDataSchema": {
                "type": "object",
                "properties": {
                    "outcome": {
                        "type": "string",
                        "enum": ["booked", "interested", "not-a-fit",
                                 "voicemail", "no-answer", "do-not-call"],
                    },
                    "call_notes": {"type": "string"},
                    "follow_up_action": {"type": "string"},
                },
                "required": ["outcome", "call_notes"],
            },
            "successEvaluationRubric": "PassFail",
        },
    }

def place_call(prospect: dict, target_number: str) -> dict:
    """Place an outbound call to a prospect."""
    harness = load_harness()
    config = build_assistant_config(harness)
    
    # Parse call context
    ctx = json.loads(prospect["call_context"])
    angles = ctx.get("personalized_angles", [])
    
    call = client.calls.create(
        assistant=config,
        assistant_overrides={
            "variable_values": {
                "opener": ctx["opener"],
                "prospect_context": ctx["prospect_context"],
                "angle_1": angles[0] if angles else "",
                "angle_2": angles[1] if len(angles) > 1 else "",
                "first_name": prospect.get("first_name", ""),
            }
        },
        phone_number_id=os.getenv("VAPI_PHONE_NUMBER_ID"),
        customer={"number": target_number},
    )
    return call
```

### Tool Webhook Server (Simulated)
```python
# Source: docs.vapi.ai/tools/custom-tools + docs.vapi.ai/server-url/events
from flask import Flask, request, jsonify

app = Flask(__name__)

TOOL_RESPONSES = {
    "book_meeting": "Meeting booked! I've sent a calendar invite to their email with a link to schedule.",
    "send_signup_link": "Done! I've sent them a link to sign up for a free Riverside trial.",
}

@app.route("/tools", methods=["POST"])
def handle_tool_call():
    data = request.json
    # Vapi sends tool calls in the message payload
    tool_calls = data.get("message", {}).get("toolCallList", [])
    
    results = []
    for tc in tool_calls:
        func_name = tc.get("function", {}).get("name", "")
        response_text = TOOL_RESPONSES.get(func_name, "Action completed.")
        results.append({
            "toolCallId": tc["id"],
            "result": response_text,
        })
    
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(port=3000)
```

### Outcome Writing to Airtable
```python
# Source: Existing upload.py pattern + pyairtable docs
from pyairtable import Api
from datetime import datetime, timezone

def update_prospect_outcome(prospect: dict, call_result: dict):
    """Write call outcome back to Airtable prospect row."""
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.table(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_PROSPECTS_TABLE_ID"))
    
    analysis = call_result.get("analysis", {})
    structured = analysis.get("structuredData", {})
    
    outcome_fields = {
        "call_outcome": structured.get("outcome", "unknown"),
        "call_notes": structured.get("call_notes", ""),
        "call_timestamp": datetime.now(timezone.utc).isoformat(),
        "follow_up_action": structured.get("follow_up_action", ""),
        "status": "Called",
    }
    
    # Upsert by podcast_name (existing key)
    record = {"fields": {
        "podcast_name": prospect["podcast_name"],
        **outcome_fields,
    }}
    table.batch_upsert([record], key_fields=["podcast_name"])
```

## Vapi vs Retell Comparison (D-01 Resolution)

| Factor | Vapi | Retell |
|--------|------|--------|
| Free credits | $10 on signup (~60-70 min) | No free trial/credits |
| Claude support | Confirmed, Claude 4 models | Supported but less documented |
| Python SDK | vapi-server-sdk v1.11.0, actively maintained | retell-ai v4.x, available |
| Function calling | Custom tools with server URL, well documented | Function calling supported |
| Post-call analysis | Built-in analysisPlan with structuredDataSchema | Post-call webhook with transcript, no built-in classification |
| Dynamic variables | `{{variable}}` syntax, injected via assistantOverrides | Custom LLM variables supported |
| Latency | ~2.3s typical (configurable down to ~1.9s) | ~2.1s typical |
| Phone number | Free US number included, Twilio import supported | Twilio import required |

**Recommendation: Vapi.** The free credits, built-in analysisPlan (saves building a separate classifier), and well-documented Python SDK make it the fastest path to demo quality. Retell's slight latency advantage is irrelevant at demo scale. The $10 free credit alone covers 60+ minutes of demo calls. [VERIFIED: vapi.ai/pricing, docs.vapi.ai, GitHub VapiAI/server-sdk-python]

## Latency Configuration Reference

Critical settings to tune for natural conversation:

| Setting | Default | Recommended | Effect |
|---------|---------|-------------|--------|
| `startSpeakingPlan.waitSeconds` | 0.4 | 0.2 | Delay after user stops speaking before agent responds |
| Smart endpointing (English) | Normal curve | Aggressive curve | How quickly Vapi decides user is done speaking |
| `silenceTimeoutSeconds` | 30 | 30 | How long silence before call auto-ends (keep at 30) |
| `stopSpeakingPlan.voiceSeconds` | 0.2 | 0.2 | How quickly agent stops when interrupted |
| `stopSpeakingPlan.backoffSeconds` | 1.0 | 0.5 | How long before agent resumes after interruption |

[CITED: docs.vapi.ai/customization/voice-pipeline-configuration]

**Total expected response time with aggressive settings:** ~1.9s (endpointing 0.4s + LLM 0.8s + TTS 0.5s + wait 0.2s)

## Voice Agent Prompt Structure (Eddie/MID Construction Pattern)

Based on D-10 and voice prompting best practices:

```
[First Message]
{{opener}}

[Role]
You are [name], a sales development rep at Riverside.fm...

[Task]
Your goal is to book a demo meeting or get them to try Riverside's free plan...
Step 1: Confirm you're speaking to the right person
Step 2: Ask about their recording setup
<wait for user response>
Step 3: Ask about editing workflow
<wait for user response>
Step 4: Based on pain points, pivot to Riverside
Step 5: Handle objections
Step 6: Close (book meeting or send signup link)

[Specifics / Rules]
- One question at a time. Never stack questions.
- Short sentences. Contractions. Conversational.
- Never mention the word "function" or "tool."
- If they ask if you're AI, answer honestly.
- No pricing commitments. Say "I can connect you with someone for pricing."
- If they say "don't call me again," apologize, end the call.
- After 5 minutes, start wrapping up.
- On voicemail, hang up immediately.
- Gatekeeper: ask for {{first_name}} by name, don't explain the offer.

[Objection Handling]
"Not interested": Acknowledge, ask what they're using now, one discovery question.
"Already have a tool": "Oh nice, what are you using?" Then contrast with Riverside's key differentiator.
"Too expensive": "Totally fair. Riverside has a free plan that lets you try it. No commitment."
"Bad timing": "I get it. Can I send you a quick link so you have it when the timing's better?"
"Not the right person": "No problem. Who handles the podcast/recording side of things?"

[Context - Riverside]
Riverside.fm is a recording and editing platform.
Key features: records locally at 4K, separate audio tracks per guest, text-based editing, live streaming.
Unlike Zoom, recordings don't depend on internet quality. Each guest's audio and video is captured locally.

[Prospect Context]
{{prospect_context}}

[Personalized Angles]
{{angle_1}}
{{angle_2}}
```

[ASSUMED: Prompt structure based on MID Construction Eddie pattern from DISCUSSION-LOG.md and Vapi prompting guide. Exact wording needs iteration during implementation.]

## Phone Number Setup

**For US test calls (demo to Shawn's US test number or friend):**
- Use Vapi's free phone number. Available in dashboard under Phone Numbers.
- Limited outbound calls/day on free tier, but sufficient for 2-3 demo calls.
- Cannot make international calls.
[CITED: docs.vapi.ai/phone-calling]

**For international calls (if needed):**
- Import a Twilio number: $1.15/mo for a US number.
- Setup: Twilio Account SID + Auth Token in Vapi dashboard.
- Steps: Buy number in Twilio console, import in Vapi dashboard (Phone Numbers > Import).
[CITED: docs.vapi.ai/phone-numbers/import-twilio]

**Recommendation per D-02:** Start with Vapi's free number. Only set up Twilio if the free number doesn't work for the demo scenario.

## Webhook vs Polling Decision

**Options:**
1. **Webhook server** (end-of-call-report event): Requires a public URL. Vapi POSTs call data when call ends. More real-time.
2. **Polling** (GET /calls/{id}): No server needed. Call runner polls after call ends. Simpler.

**Recommendation:** Use polling for outcome retrieval. The call runner already has the call ID. Poll every 5 seconds until call status is "ended," then wait 3 more seconds for analysis to complete. This avoids needing a public webhook server just for the end-of-call report.

For mid-call tool calls, a webhook server IS required (Vapi POSTs tool invocations to a server URL). Options:
- **Local Flask server + ngrok:** Simple, works for demo. `ngrok http 3000` gives a public URL.
- **Skip tool server entirely:** If tool calls are not critical for demo, the agent can verbally confirm actions without actually calling a server. However, this means VOIC-05 and VOIC-06 won't be fully demonstrated.

**Recommendation:** Set up a minimal Flask server + ngrok for tool calls. It's ~20 lines of code and proves the function-calling wiring works. [ASSUMED: ngrok availability on this machine - not detected, may need install]

## ProspectDict Extensions Needed

New fields to add to `models.py`:
```python
call_outcome: Optional[str]       # booked, interested, not-a-fit, voicemail, no-answer, do-not-call
call_notes: Optional[str]         # 1-2 sentence summary from analysisPlan
call_timestamp: Optional[str]     # ISO 8601 timestamp of call completion
follow_up_action: Optional[str]   # What follow-up would be triggered
call_id: Optional[str]            # Vapi call ID for reference
```

New Airtable field mappings to add to `upload.py`:
```python
"call_outcome": prospect.get("call_outcome", ""),
"call_notes": prospect.get("call_notes", ""),
"call_timestamp": prospect.get("call_timestamp", ""),
"follow_up_action": prospect.get("follow_up_action", ""),
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate LLM call for post-call classification | Vapi analysisPlan with structuredDataSchema | March 2025 (structuredDataMultiPlan added) | No extra LLM cost, no extra code for classification |
| formatTurns: true (default, adds 1.5s delay) | startSpeakingPlan with configurable waitSeconds | 2025 | Configurable latency, aggressive settings get to ~1.9s total |
| Webhook-only for call results | Polling GET /calls/{id} + webhooks | Available since early 2025 | Simpler architectures possible without public URL for results |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Inline transient assistant config works with tools and analysisPlan in calls.create() | Architecture Patterns | Would need to pre-create assistant via dashboard/API, adding a setup step |
| A2 | Vapi free number allows enough outbound calls for 2-3 demo recordings | Phone Number Setup | Would need Twilio import, adding $1.15 cost and setup time |
| A3 | call.analysis.structuredData is populated within 30 seconds of call ending | Pattern 5: Polling | Would need webhook server for end-of-call-report instead of polling |
| A4 | vapi-server-sdk Python SDK uses snake_case for parameters (assistant_overrides, variable_values) | Code Examples | May need camelCase (assistantOverrides, variableValues) - check SDK types |
| A5 | ngrok or similar tool available for exposing local tool server | Webhook vs Polling | Would need to deploy tool server to a cloud endpoint or skip tool demo |
| A6 | Claude Sonnet 4 model ID is `claude-sonnet-4-20250514` in Vapi's provider config | Standard Stack | May need different model string - check Vapi model list |
| A7 | Prompt structure (Eddie pattern) will produce natural voice conversation | Voice Agent Prompt Structure | May need significant iteration during testing |

## Open Questions

1. **Exact Vapi SDK parameter casing**
   - What we know: Vapi API uses camelCase (assistantOverrides, variableValues). Python SDKs often convert to snake_case.
   - What's unclear: Whether vapi-server-sdk v1.11.0 uses snake_case or camelCase in the Python interface.
   - Recommendation: Check the SDK types after installing. Try snake_case first, fall back to camelCase dict.

2. **Voice selection for the agent**
   - What we know: Vapi supports ElevenLabs, Cartesia, PlayHT, and others for TTS.
   - What's unclear: Which specific voice ID produces the most natural cold-call SDR tone.
   - Recommendation: Pick a standard male or female ElevenLabs voice. Test with one call and iterate if needed.

3. **Tool server hosting for demo**
   - What we know: Mid-call tools require a server URL that Vapi can POST to. Local Flask + ngrok works.
   - What's unclear: Whether ngrok is installed on this machine.
   - Recommendation: Check ngrok availability. If not available, use a free cloud function (e.g., Replit) or skip tool server and have agent handle tools conversationally.

4. **OUTC-03 interpretation for simulated follow-up**
   - What we know: D-18 says follow-up actions are logged but not sent. OUTC-03 says "fire at least one real follow-up action."
   - What's unclear: Whether logging qualifies as "firing" a follow-up action.
   - Recommendation: Log the follow-up action to console AND write it to the Airtable row. The write-up can describe what the production version would do.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 | Everything | Yes | 3.11.0 | -- |
| vapi-server-sdk | Call placement + results | No (not installed) | -- | `pip install vapi-server-sdk` |
| Flask | Tool webhook server | No (not installed) | -- | `pip install flask` or use http.server |
| ngrok | Expose local tool server | Not detected | -- | Use free cloud function, or skip tool server |
| pyairtable | Outcome writes | Yes (in requirements.txt) | 3.x | -- |
| pydantic | Data models | Yes (in requirements.txt) | 2.x | -- |

**Missing dependencies with no fallback:**
- vapi-server-sdk must be installed (`pip install vapi-server-sdk`)

**Missing dependencies with fallback:**
- Flask: can use Python's built-in `http.server` for a minimal tool handler
- ngrok: can use a cloud function (Replit, Railway) or test tools via Vapi dashboard

## Sources

### Primary (HIGH confidence)
- [Vapi Outbound Calling docs](https://docs.vapi.ai/calls/outbound-calling) - call creation API, assistant config
- [Vapi Dynamic Variables docs](https://docs.vapi.ai/assistants/dynamic-variables) - `{{variable}}` syntax, assistantOverrides
- [Vapi Custom Tools docs](https://docs.vapi.ai/tools/custom-tools) - tool definition schema, server URL, response format
- [Vapi Call Analysis docs](https://docs.vapi.ai/assistants/call-analysis) - analysisPlan, structuredDataSchema
- [Vapi Voice Pipeline Configuration](https://docs.vapi.ai/customization/voice-pipeline-configuration) - latency settings, startSpeakingPlan
- [Vapi Prompting Guide](https://docs.vapi.ai/prompting-guide) - voice prompt best practices
- [Vapi Server URL Events](https://docs.vapi.ai/server-url/events) - webhook event types, tool-calls format
- [Vapi Phone Numbers / Import Twilio](https://docs.vapi.ai/phone-numbers/import-twilio) - Twilio setup
- [VapiAI/server-sdk-python GitHub](https://github.com/VapiAI/server-sdk-python) - SDK v1.11.0

### Secondary (MEDIUM confidence)
- [Vapi Cold Calling Campaign Agent](https://vapi.ai/custom-agents/cold-calling-campaign-agent) - example prompt structure
- [AssemblyAI: Lowest Latency Voice Agent in Vapi](https://www.assemblyai.com/blog/how-to-build-lowest-latency-voice-agent-vapi) - latency optimization techniques

### Tertiary (LOW confidence)
- unpod GitHub repo (https://github.com/parvbhullar/unpod) - no usable prompt patterns found in README, would need to examine source files

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Vapi SDK and API verified via official docs and GitHub
- Architecture: HIGH - all patterns verified against Vapi official documentation
- Pitfalls: HIGH - latency settings, webhook timeouts, phone limitations all documented
- Prompt structure: MEDIUM - Eddie pattern is from discussion context, voice optimization from Vapi guide, but exact prompt needs iteration

**Research date:** 2026-04-23
**Valid until:** 2026-05-07 (Vapi API is stable but evolving)
