---
phase: "03"
plan: "02"
subsystem: outcome-handling
tags: [vapi, airtable, post-call, outcome-classification]
dependency_graph:
  requires: [call_context.py, upload.py, models.py]
  provides: [outcome_handler.py, extended-upload-fields, env-example]
  affects: [run_pipeline.py, call_runner]
tech_stack:
  added: [vapi-server-sdk]
  patterns: [polling-with-retry, graceful-degradation, batch-upsert]
key_files:
  created:
    - src/pipeline/outcome_handler.py
    - src/.env.example
  modified:
    - src/pipeline/upload.py
decisions:
  - "Used polling (not webhooks) for post-call result retrieval per research recommendation"
  - "30s post-end analysis retry window with graceful degradation to unknown outcome"
  - "Follow-up actions logged to console per D-18 (not actually sent)"
metrics:
  duration: "108s"
  completed: "2026-04-23"
---

# Phase 03 Plan 02: Outcome Handler and Airtable Field Mapping Summary

Post-call outcome polling via Vapi API with structured extraction, follow-up logging, and Airtable persistence for the complete prospect lifecycle.

## What Was Built

### outcome_handler.py (new)
Complete post-call handling module with 5 exported functions:
- `wait_for_call_result`: Polls Vapi `calls.get()` with configurable timeout, 30s post-end retry for analysis data, progress logging
- `extract_outcome`: Extracts structured outcome from `call.analysis.structured_data` with validation against 6 categories, graceful fallback to "unknown"
- `log_follow_up`: Formats and prints follow-up action to console (per D-18, logged not sent)
- `update_prospect_outcome`: Writes outcome fields to prospect's existing Airtable row via `batch_upsert` with `podcast_name` key
- `process_call_outcome`: Orchestrator that chains all steps with per-step error handling

Constants: `VALID_OUTCOMES` (6 categories), `FOLLOW_UP_ACTIONS` (template strings per outcome).

### upload.py (extended)
Added 5 outcome fields to `prospect_to_airtable_fields()`: `call_outcome`, `call_notes`, `call_timestamp`, `follow_up_action`, `call_id`. These map the complete prospect lifecycle (discovery through call outcome) to Airtable columns.

### .env.example (new)
Single reference for all environment variables: Podcast Index, Hunter, Airtable, OpenRouter, and Vapi (API key, phone number ID, voice ID, tool server URL) with comments explaining where to find each value.

## Deviations from Plan

None. Plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 6108b79 | outcome_handler.py with polling, extraction, Airtable writing |
| 2 | d234ca7 | upload.py field mapping + .env.example with Vapi keys |

## Verification

- outcome_handler.py: All 5 functions import, VALID_OUTCOMES has 6 entries, extract_outcome handles None analysis gracefully
- upload.py: prospect_to_airtable_fields maps all 5 new outcome fields correctly
- .env.example: Contains VAPI_API_KEY, VAPI_PHONE_NUMBER_ID, VAPI_VOICE_ID, TOOL_SERVER_URL

## Self-Check: PASSED
