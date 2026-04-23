"""Call runner: place outbound calls and handle outcomes.

Usage:
  py src/call_runner.py --prospect "Podcast Name" --number "+1234567890"
  py src/call_runner.py --all --number "+1234567890"
  py src/call_runner.py --list
  py src/call_runner.py --dry-run
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from pipeline.voice_agent import place_call, build_assistant_config
from pipeline.outcome_handler import process_call_outcome

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_call_ready_prospects() -> list[dict]:
    """Load prospects that are qualified and have call context."""
    path = os.path.join(DATA_DIR, "call_context.json")
    if not os.path.exists(path):
        print("  Error: data/call_context.json not found. Run the call_context step first.")
        return []

    with open(path, "r", encoding="utf-8") as f:
        prospects = json.load(f)

    ready = [
        p for p in prospects
        if p.get("status") == "Qualified" and p.get("call_context")
    ]
    return ready


def find_prospect(prospects: list[dict], name: str) -> dict | None:
    """Find a prospect by podcast name (case-insensitive substring match)."""
    name_lower = name.lower()
    for p in prospects:
        if name_lower in p.get("podcast_name", "").lower():
            return p
    return None


def run_call(prospect: dict, target_number: str) -> dict:
    """Place a call to a single prospect and handle the outcome."""
    print(f"\n{'=' * 60}")
    print(f"CALLING: {prospect.get('podcast_name', 'Unknown')}")
    print(f"{'=' * 60}")
    print(f"  Host: {prospect.get('host_name', 'Unknown')}")
    print(f"  Company: {prospect.get('company_name', prospect.get('domain', 'Unknown'))}")
    print(f"  Title: {prospect.get('title', 'Unknown')}")

    call = place_call(prospect, target_number)
    call_id = getattr(call, "id", "unknown")

    print(f"  Call initiated: {call_id}")
    print(f"  Waiting for call to complete (this may take several minutes)...")

    # Import here so the module loads without vapi installed
    from vapi import Vapi
    client = Vapi(token=os.getenv("VAPI_API_KEY"))

    updated = process_call_outcome(client, call_id, prospect)

    print(f"\n  Result: {updated.get('call_outcome', 'unknown')}")
    print(f"  Notes: {updated.get('call_notes', 'N/A')}")

    return updated


def run_all_calls(prospects: list[dict], target_number: str) -> list[dict]:
    """Place calls to all qualified prospects sequentially."""
    print(f"\nPlacing {len(prospects)} calls (one at a time)...")
    results = []

    for i, prospect in enumerate(prospects, 1):
        print(f"\n[{i}/{len(prospects)}]")
        try:
            updated = run_call(prospect, target_number)
            results.append(updated)
        except Exception as e:
            print(f"  Error calling {prospect.get('podcast_name', 'Unknown')}: {e}")
            prospect["call_outcome"] = "error"
            prospect["call_notes"] = str(e)
            prospect["call_timestamp"] = datetime.now(timezone.utc).isoformat()
            results.append(prospect)

        # Save after each call so results are preserved if something fails
        _save_results(results)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"CALL SESSION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Total calls: {len(results)}")
    outcomes = {}
    for p in results:
        o = p.get("call_outcome", "unknown")
        outcomes[o] = outcomes.get(o, 0) + 1
    for outcome, count in outcomes.items():
        print(f"  {outcome}: {count}")

    return results


def list_prospects(prospects: list[dict]):
    """Print a table of call-ready prospects."""
    if not prospects:
        print("  No call-ready prospects found.")
        print("  Run the pipeline through call_context first:")
        print("    py src/run_pipeline.py call_context")
        return

    print(f"\nCall-Ready Prospects ({len(prospects)} total)")
    print("-" * 70)
    print(f"  {'#':>3}  {'Podcast Name':<30}  {'Host':<15}  {'Context'}")
    print(f"  {'---':>3}  {'---':<30}  {'---':<15}  {'---'}")

    for i, p in enumerate(prospects, 1):
        name = p.get("podcast_name", "Unknown")[:30]
        host = p.get("host_name", "Unknown")[:15]
        has_ctx = "yes" if p.get("call_context") else "no"
        print(f"  {i:3d}  {name:<30}  {host:<15}  {has_ctx}")


def _save_results(results: list[dict]):
    """Save call results to data/call_results.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "call_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Place outbound calls via Vapi")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prospect", type=str, help="Call a specific prospect by podcast name")
    group.add_argument("--all", action="store_true", help="Call all qualified prospects")
    group.add_argument("--list", action="store_true", help="Show available prospects")
    group.add_argument("--dry-run", action="store_true", help="Print assistant config without placing a call")

    parser.add_argument("--number", type=str, help="Target phone number (required for --prospect and --all)")

    args = parser.parse_args()

    if args.dry_run:
        config = build_assistant_config()
        print(json.dumps(config, indent=2))
        return

    prospects = load_call_ready_prospects()

    if args.list:
        list_prospects(prospects)
        return

    if not args.number:
        print("Error: --number is required when placing calls.")
        print("  Example: py src/call_runner.py --prospect 'Name' --number '+15551234567'")
        sys.exit(1)

    if args.prospect:
        match = find_prospect(prospects, args.prospect)
        if not match:
            print(f"  No prospect found matching '{args.prospect}'")
            print("  Available prospects:")
            list_prospects(prospects)
            sys.exit(1)
        result = run_call(match, args.number)
        _save_results([result])

    elif args.all:
        if not prospects:
            print("  No call-ready prospects. Run the pipeline first.")
            sys.exit(1)
        results = run_all_calls(prospects, args.number)
        _save_results(results)


if __name__ == "__main__":
    main()
