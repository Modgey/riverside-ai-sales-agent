---
phase: 03-voice-agent-and-outcome-handling
plan: 01
subsystem: voice-agent
tags: [vapi, voice-agent, harness, system-prompt, cold-calling]
dependency_graph:
  requires: [call_context.py, models.py]
  provides: [voice_agent.py, harness.txt, extended ProspectDict]
  affects: [outcome_handler (plan 02), call_runner (plan 03), upload.py]
tech_stack:
  added: [vapi-server-sdk]
  patterns: [inline-transient-assistant, variable-injection, custom-tools, analysisPlan]
key_files:
  created:
    - src/pipeline/prompts/harness.txt
    - src/pipeline/voice_agent.py
  modified:
    - src/pipeline/models.py
decisions:
  - Used Eddie/MID Construction pattern for harness structure (role, task, specifics, context)
  - Mapped CallContextResponse fields to harness variables (opening_line to opener, narrative_briefing to prospect_context, riverside_hooks to angle_1/angle_2)
  - ElevenLabs George voice (JBFqnCBsd6RMkjVDRZzb) as default, configurable via VAPI_VOICE_ID env var
  - Lazy import of vapi SDK in place_call() so config inspection works without the SDK installed
metrics:
  duration: 3m
  completed: 2026-04-23
---

# Phase 3 Plan 01: Voice Agent Harness and Vapi Integration Summary

Voice agent system prompt (harness.txt) with SDR persona, discovery-first conversation flow, 5 objection handlers, and safety rules, plus voice_agent.py that builds a complete inline Vapi assistant config with Claude Sonnet 4, ElevenLabs TTS, Deepgram STT, custom tools, and post-call analysisPlan.

## Task Results

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Write voice agent harness prompt | 13a85e9 | src/pipeline/prompts/harness.txt |
| 2 | Build voice_agent.py + extend ProspectDict | c084ea0 | src/pipeline/voice_agent.py, src/pipeline/models.py |

## What Was Built

**harness.txt** (51 lines, ~1020 tokens): Complete voice agent system prompt following the Eddie/MID Construction pattern. Includes:
- Alex persona (SDR at Riverside, honest about AI if asked)
- 7-step conversation flow: confirm person, context, recording setup, editing, pivot to Riverside, handle pushback, close
- 5 objection handlers: not interested, already have a tool, too expensive, bad timing, wrong person
- Safety rules: no pricing commits, respect DNC, voicemail hangup, 5-min time awareness, factual competitor comparison only
- Riverside product context: 4K local recording, separate tracks, text-based editing, live streaming, AI clips
- Variable placeholders: opener, first_name, prospect_context, angle_1, angle_2

**voice_agent.py** (5 exported functions):
- `load_harness()`: reads harness.txt
- `build_tool_definitions()`: book_meeting and send_signup_link custom tools with configurable server URL
- `build_analysis_plan()`: 6-category outcome classification (booked, interested, not-a-fit, voicemail, no-answer, do-not-call) via Vapi structuredDataSchema
- `build_assistant_config()`: complete inline transient assistant config (Claude Sonnet 4, ElevenLabs, Deepgram nova-2, latency tuning)
- `place_call()`: outbound call via Vapi SDK with variableValues injection from call_context

**ProspectDict extensions**: call_outcome, call_notes, call_timestamp, follow_up_action, call_id

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CallContextResponse field name mismatch**
- **Found during:** Task 2
- **Issue:** Plan assumed call_context JSON has fields `opener`, `prospect_context`, `personalized_angles`. The actual CallContextResponse model (from call_context.py) uses `opening_line`, `narrative_briefing`, `riverside_hooks`.
- **Fix:** Mapped actual fields to harness variables: opening_line -> opener, narrative_briefing -> prospect_context, riverside_hooks[0] -> angle_1, riverside_hooks[1] -> angle_2. Added comment documenting the mapping.
- **Files modified:** src/pipeline/voice_agent.py
- **Commit:** c084ea0

## Decisions Made

1. **Lazy vapi import**: `from vapi import Vapi` is inside `place_call()` not at module top, so `build_assistant_config()` and config inspection work without the SDK installed. KISS for development.
2. **Variable mapping**: CallContextResponse.opening_line maps to {{opener}}, narrative_briefing maps to {{prospect_context}}, riverside_hooks maps to {{angle_1}} and {{angle_2}}. This bridges the call_context generation output to the voice agent harness.
3. **Default fallback opener**: If call_context is missing or parsing fails, opener defaults to "Hey, this is Alex from Riverside." so the call can still proceed.

## Verification Results

All automated checks passed:
- harness.txt: all 5 variable placeholders present, all 5 objection types covered, Riverside features mentioned, safety rules present, under 1500 tokens
- voice_agent.py: all 5 functions importable, config has correct provider/model/tools/analysis, latency settings correct
- ProspectDict: all 5 new fields present in type hints

## Self-Check: PASSED
