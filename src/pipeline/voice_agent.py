"""Voice agent: Vapi assistant config builder and outbound call placement."""

import json
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

HARNESS_PATH = os.path.join(os.path.dirname(__file__), "prompts", "harness.txt")


def load_harness() -> str:
    """Read and return the voice agent system prompt from harness.txt."""
    with open(HARNESS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_tool_definitions() -> list[dict]:
    """Return tool definitions for book_meeting and send_signup_link.

    Each tool is a Vapi custom tool that POSTs to a server URL mid-call.
    For demo, the server returns canned success responses.
    """
    server_url = os.getenv("TOOL_SERVER_URL", "http://localhost:3000/tools")

    return [
        {
            "type": "function",
            "function": {
                "name": "book_meeting",
                "description": (
                    "Book a demo meeting with the prospect. Call this when "
                    "the prospect agrees to a meeting or demo."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prospect_name": {
                            "type": "string",
                            "description": "The prospect's name",
                        },
                    },
                    "required": ["prospect_name"],
                },
            },
            "server": {"url": server_url},
        },
        {
            "type": "function",
            "function": {
                "name": "send_signup_link",
                "description": (
                    "Send a Riverside free trial signup link to the prospect. "
                    "Call this when they want to try Riverside on their own."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prospect_name": {
                            "type": "string",
                            "description": "The prospect's name",
                        },
                    },
                    "required": ["prospect_name"],
                },
            },
            "server": {"url": server_url},
        },
    ]


def build_analysis_plan() -> dict:
    """Return the Vapi analysisPlan for post-call outcome classification.

    Classifies calls into 6 outcome categories and extracts a summary.
    Runs automatically on Vapi infra after each call ends.
    """
    return {
        "structuredDataPrompt": (
            "Classify this sales call outcome into exactly one category. "
            "Analyze the full transcript and determine:\n"
            "- 'booked': prospect agreed to a meeting or demo\n"
            "- 'interested': prospect showed interest but didn't commit to a meeting\n"
            "- 'not-a-fit': prospect is not a good fit or declined the offer\n"
            "- 'voicemail': call went to voicemail\n"
            "- 'no-answer': nobody answered the call\n"
            "- 'do-not-call': prospect explicitly asked not to be called again\n\n"
            "Also provide:\n"
            "- call_notes: a 1-2 sentence summary of the call outcome\n"
            "- follow_up_action: what follow-up should happen (e.g., "
            "'send calendar link', 'add to nurture sequence', 'remove from list')"
        ),
        "structuredDataSchema": {
            "type": "object",
            "properties": {
                "outcome": {
                    "type": "string",
                    "enum": [
                        "booked",
                        "interested",
                        "not-a-fit",
                        "voicemail",
                        "no-answer",
                        "do-not-call",
                    ],
                    "description": "The classified outcome of the call",
                },
                "call_notes": {
                    "type": "string",
                    "description": "1-2 sentence summary of what happened on the call",
                },
                "follow_up_action": {
                    "type": "string",
                    "description": "What follow-up action should be taken",
                },
            },
            "required": ["outcome", "call_notes"],
        },
        "successEvaluationRubric": "PassFail",
    }


def build_assistant_config() -> dict:
    """Build a complete inline Vapi assistant config for outbound cold calls.

    Returns a transient assistant dict with model, voice, transcriber,
    tools, analysisPlan, and latency settings. Passed directly to
    client.calls.create(assistant=...).
    """
    return {
        "model": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "messages": [{"role": "system", "content": load_harness()}],
        },
        "voice": {
            "provider": "11labs",
            "voiceId": os.getenv("VAPI_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"),
        },
        "firstMessage": "{{opener}}",
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
        },
        "silenceTimeoutSeconds": 30,
        "startSpeakingPlan": {"waitSeconds": 0.2},
        "stopSpeakingPlan": {"voiceSeconds": 0.2, "backoffSeconds": 0.5},
        "tools": build_tool_definitions(),
        "analysisPlan": build_analysis_plan(),
    }


def place_call(prospect: dict, target_number: str) -> object:
    """Place an outbound call to a prospect via Vapi.

    Reads the prospect's call_context JSON to extract opener, prospect_context,
    and personalized angles, then injects them as variableValues.

    Args:
        prospect: ProspectDict with call_context field populated.
        target_number: Phone number to call (E.164 format, e.g. +15551234567).

    Returns:
        The Vapi call object from client.calls.create().
    """
    # Import here so config inspection works without vapi installed
    from vapi import Vapi

    client = Vapi(token=os.getenv("VAPI_API_KEY"))

    # Parse call_context JSON. Fields come from CallContextResponse:
    # opening_line, pain_hypotheses, objections, riverside_hooks, narrative_briefing
    ctx = json.loads(prospect.get("call_context", "{}"))

    # Map CallContextResponse fields to harness variable placeholders.
    # The harness uses {{opener}}, {{prospect_context}}, {{angle_1}}, {{angle_2}}.
    # CallContextResponse provides opening_line, narrative_briefing, riverside_hooks.
    hooks = ctx.get("riverside_hooks", [])

    variable_values = {
        "opener": ctx.get("opening_line", "Hey, this is Alex from Riverside."),
        "prospect_context": ctx.get("narrative_briefing", ""),
        "angle_1": hooks[0] if hooks else "",
        "angle_2": hooks[1] if len(hooks) > 1 else "",
        "first_name": prospect.get("first_name", ""),
    }

    # NOTE on SDK parameter casing: Vapi API uses camelCase (assistantOverrides,
    # variableValues). The Python SDK (vapi-server-sdk) may use snake_case.
    # Using snake_case first per SDK convention. If the SDK expects camelCase,
    # switch to assistant_overrides={"variableValues": {...}}.
    call = client.calls.create(
        assistant=build_assistant_config(),
        assistant_overrides={"variable_values": variable_values},
        phone_number_id=os.getenv("VAPI_PHONE_NUMBER_ID"),
        customer={"number": target_number},
    )

    podcast = prospect.get("podcast_name", "unknown")
    call_id = getattr(call, "id", "unknown")
    print(f"  Call placed: {call_id} to {target_number} for {podcast}")

    return call


if __name__ == "__main__":
    # Print the assistant config as formatted JSON for inspection.
    # Does NOT place a real call (just shows config).
    config = build_assistant_config()
    print(json.dumps(config, indent=2))
