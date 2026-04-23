"""Post-call outcome handling: poll Vapi, classify, write to Airtable."""

import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from pyairtable import Api

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

VALID_OUTCOMES = {"follow-up-scheduled", "warm-lead", "not-a-fit", "voicemail", "no-answer", "do-not-contact"}

FOLLOW_UP_ACTIONS = {
    "follow-up-scheduled": "Route to AE for personalized follow-up with {email}",
    "warm-lead": "Add {email} to nurture sequence with personalized follow-up",
    "not-a-fit": "No follow-up needed",
    "voicemail": "Schedule retry call in 48 hours",
    "no-answer": "Schedule retry call in 24 hours",
    "do-not-contact": "Add to suppression list, no further contact",
}


def wait_for_call_result(client, call_id: str, timeout: int = 600, poll_interval: int = 5) -> object:
    """Poll Vapi until call completes and analysis is ready.

    Args:
        client: Vapi client instance.
        call_id: The Vapi call ID to poll.
        timeout: Max seconds to wait for call to end.
        poll_interval: Seconds between polls.

    Returns:
        The Vapi call object with status "ended" (analysis may or may not be populated).

    Raises:
        TimeoutError: If call does not end within timeout seconds.
    """
    start = time.time()
    poll_count = 0

    while True:
        elapsed = int(time.time() - start)
        if elapsed >= timeout:
            raise TimeoutError(f"Call {call_id} did not complete within {timeout}s")

        call = client.calls.get(call_id)
        poll_count += 1

        if poll_count % 3 == 0:
            print(f"  Waiting for call {call_id} to complete... ({elapsed}s)")

        if call.status == "ended":
            # Analysis runs async after call ends. Wait a bit then re-poll.
            time.sleep(5)
            call = client.calls.get(call_id)
            if call.analysis and call.analysis.structured_data:
                return call

            # Retry for up to 30 seconds for analysis to appear
            analysis_start = time.time()
            while time.time() - analysis_start < 25:
                time.sleep(5)
                call = client.calls.get(call_id)
                if call.analysis and call.analysis.structured_data:
                    return call

            # Graceful degradation: return call without analysis
            print(f"  Warning: analysis not available for call {call_id} after 30s post-end polling")
            return call

        time.sleep(poll_interval)


def extract_outcome(call_result) -> dict:
    """Extract structured outcome from a Vapi call result.

    Args:
        call_result: Vapi call object (or any object with .analysis.structured_data).

    Returns:
        Dict with keys: outcome, call_notes, follow_up_action.
    """
    defaults = {
        "outcome": "unknown",
        "call_notes": "Analysis not available",
        "follow_up_action": "",
    }

    analysis = getattr(call_result, "analysis", None)
    if analysis is None:
        return defaults

    structured = getattr(analysis, "structured_data", None)
    if structured is None:
        return defaults

    # structured_data can be a dict or an object with attributes
    if isinstance(structured, dict):
        data = structured
    else:
        data = vars(structured) if hasattr(structured, "__dict__") else {}

    outcome = data.get("outcome", "unknown")
    if outcome not in VALID_OUTCOMES:
        outcome = "unknown"

    return {
        "outcome": outcome,
        "call_notes": data.get("call_notes", "Analysis not available"),
        "follow_up_action": data.get("follow_up_action", ""),
    }


def log_follow_up(prospect: dict, outcome: str) -> str:
    """Log the follow-up action for a given outcome.

    Args:
        prospect: Prospect dict (needs work_email for formatting).
        outcome: The classified call outcome string.

    Returns:
        The formatted follow-up action string.
    """
    action_template = FOLLOW_UP_ACTIONS.get(outcome, "No follow-up action defined for this outcome")
    email = prospect.get("work_email", "no-email")
    formatted = action_template.format(email=email)
    print(f"  Follow-up [{outcome}]: {formatted}")
    return formatted


def update_prospect_outcome(prospect: dict, outcome_data: dict):
    """Write call outcome back to the prospect's Airtable row.

    Args:
        prospect: Prospect dict (needs podcast_name for upsert key).
        outcome_data: Dict with outcome, call_notes, follow_up_action keys.
    """
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.table(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_PROSPECTS_TABLE_ID"))

    fields = {
        "podcast_name": prospect.get("podcast_name", ""),
        "call_outcome": outcome_data.get("outcome", "unknown"),
        "call_notes": outcome_data.get("call_notes", ""),
        "call_timestamp": datetime.now(timezone.utc).isoformat(),
        "follow_up_action": outcome_data.get("follow_up_action", ""),
        "status": "Called",
    }

    table.batch_upsert([{"fields": fields}], key_fields=["podcast_name"])
    print(f"  Airtable updated: {prospect.get('podcast_name', 'unknown')} -> {outcome_data.get('outcome', 'unknown')}")


def process_call_outcome(client, call_id: str, prospect: dict) -> dict:
    """Orchestrate the full post-call outcome flow.

    Polls Vapi for the call result, extracts the structured outcome,
    logs the follow-up action, and writes everything to Airtable.

    Args:
        client: Vapi client instance.
        call_id: The Vapi call ID.
        prospect: Prospect dict to update.

    Returns:
        The prospect dict updated with outcome fields.
    """
    outcome_data = {
        "outcome": "unknown",
        "call_notes": "Processing failed",
        "follow_up_action": "",
    }

    try:
        call_result = wait_for_call_result(client, call_id)
        outcome_data = extract_outcome(call_result)
    except TimeoutError as e:
        print(f"  Error polling call result: {e}")
    except Exception as e:
        print(f"  Error extracting outcome: {e}")

    try:
        follow_up = log_follow_up(prospect, outcome_data["outcome"])
        outcome_data["follow_up_action"] = follow_up
    except Exception as e:
        print(f"  Error logging follow-up: {e}")

    try:
        update_prospect_outcome(prospect, outcome_data)
    except Exception as e:
        print(f"  Error updating Airtable: {e}")

    # Update the prospect dict with outcome fields
    prospect["call_outcome"] = outcome_data["outcome"]
    prospect["call_notes"] = outcome_data["call_notes"]
    prospect["call_timestamp"] = datetime.now(timezone.utc).isoformat()
    prospect["follow_up_action"] = outcome_data.get("follow_up_action", "")
    prospect["call_id"] = call_id

    return prospect


if __name__ == "__main__":
    print("Follow-up action templates:")
    print("-" * 50)
    for outcome, action in FOLLOW_UP_ACTIONS.items():
        print(f"  {outcome:15s} -> {action}")
