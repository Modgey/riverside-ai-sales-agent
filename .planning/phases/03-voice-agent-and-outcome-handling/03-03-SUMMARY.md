---
phase: "03"
plan: "03"
subsystem: call-runner-integration
tags: [vapi, call-runner, tool-server, pipeline-integration, cli]
dependency_graph:
  requires: [voice_agent.py, outcome_handler.py, call_context.json]
  provides: [tool_server.py, call_runner.py, pipeline-call-step]
  affects: [run_pipeline.py]
tech_stack:
  added: [flask]
  patterns: [webhook-simulation, cli-argparse, sequential-call-placement]
key_files:
  created:
    - src/tool_server.py
    - src/call_runner.py
  modified:
    - src/run_pipeline.py
decisions:
  - "Call step excluded from run_all() because calls are interactive, take minutes, and cost money"
  - "Tool server uses canned responses per D-13 (simulated, not real integrations)"
  - "Call runner saves results after each call for crash resilience"
metrics:
  duration: "152s"
  completed: "2026-04-23"
---

# Phase 03 Plan 03: Call Runner and Pipeline Integration Summary

Flask tool webhook server with canned responses for simulated mid-call tools, CLI call runner with prospect selection and dry-run mode, and pipeline integration with call step excluded from automatic runs.

## Task Results

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create tool webhook server and call runner CLI | 09b8be3 | src/tool_server.py, src/call_runner.py |
| 2 | Wire call step into run_pipeline.py | 35b6cbc | src/run_pipeline.py |
| 3 | Human verification checkpoint | pending | -- |

## What Was Built

### tool_server.py (new)
Minimal Flask server for mid-call tool webhooks (per D-13, simulated):
- `POST /tools`: Handles Vapi tool call POSTs, returns canned responses for book_meeting and send_signup_link
- `GET /health`: Health check endpoint listing available tools
- Runs on port 3000, designed for ngrok exposure during demo

### call_runner.py (new)
CLI entry point for placing calls and handling outcomes. 6 functions:
- `load_call_ready_prospects()`: Loads from call_context.json, filters to Qualified with call_context
- `find_prospect()`: Case-insensitive substring search by podcast name
- `run_call()`: Places single call via voice_agent.place_call, processes outcome via outcome_handler
- `run_all_calls()`: Sequential batch calling with per-call result saving
- `list_prospects()`: Tabular display of call-ready prospects
- CLI flags: `--prospect NAME`, `--all`, `--number NUM`, `--list`, `--dry-run`

### run_pipeline.py (modified)
- Added "call" as last entry in STEPS list
- `run_call_step()`: Prints call_runner.py usage instructions (does NOT place calls)
- `print_status()`: Shows call_results.json outcomes when available
- `print_usage()`: Lists call step with explanation
- Call step intentionally excluded from `run_all()` per design decision

## Deviations from Plan

None. Plan executed exactly as written.

## Decisions Made

1. **Call step not in run_all()**: Calls are interactive, take minutes per prospect, and cost real money. They must be a deliberate action, not part of the automated pipeline.
2. **Per-call result saving**: call_runner.py saves results to call_results.json after each call completes, so if the batch is interrupted, prior results are preserved.
3. **Canned tool responses**: Tool server returns static success text per D-13. Production version would integrate with Calendly and SendGrid.

## Verification Results

All checks passed:
- `py src/call_runner.py --dry-run`: Prints complete assistant config JSON with model, voice, tools, analysisPlan
- `py src/call_runner.py --list`: Shows 19 call-ready prospects from call_context.json
- `py src/run_pipeline.py call`: Prints call_runner.py usage instructions
- `py src/run_pipeline.py status`: Shows pipeline status including call step ("not run yet")
- `py src/run_pipeline.py help`: Lists call step with description
- tool_server.py: TOOL_RESPONSES has exactly 2 entries (book_meeting, send_signup_link)

## Self-Check: PASSED
