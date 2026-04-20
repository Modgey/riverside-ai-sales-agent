# Phase 1: Prospect Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-20
**Phase:** 01-prospect-pipeline
**Areas discussed:** Discovery strategy, Scoring and filtering, Airtable presentation, Pipeline execution

---

## Discovery Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Category-first | Search by Business/Technology/Marketing categories, filter in code | ✓ |
| Keyword-first | Search for terms like 'SaaS', 'B2B' directly | |
| Hybrid | Category + keyword, deduplicate | |

**User's choice:** Category-first
**Notes:** Casts a wider net, scoring layer handles precision.

| Option | Description | Selected |
|--------|-------------|----------|
| 20-30 call-ready rows | Enough for demo, keeps Airtable clean | ✓ |
| 50+ call-ready rows | Bigger pool, more Apollo credits used | |
| You decide | Claude picks | |

**User's choice:** 20-30 call-ready rows

| Option | Description | Selected |
|--------|-------------|----------|
| Drop silently | Hard filter catches solo creators | ✓ |
| Flag as 'unverified' | Keep with flag column | |
| You decide | Claude picks | |

**User's choice:** Drop silently

| Option | Description | Selected |
|--------|-------------|----------|
| All three categories | Business + Technology + Marketing | |
| Business only, expand if thin | Start narrow, widen if needed | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide (Claude's discretion)

---

## Scoring and Filtering

| Option | Description | Selected |
|--------|-------------|----------|
| Episode cadence heaviest | Cadence 40%, size 30%, completeness 20%, category 10% | |
| Company size heaviest | Size 40%, cadence 30%, completeness 20%, category 10% | ✓ |
| Even split | 25% each | |
| You decide | Claude picks | |

**User's choice:** Company size heaviest

| Option | Description | Selected |
|--------|-------------|----------|
| Strict | 100-1000 employees, 60-day recency, 10+ episodes | |
| Moderate | 50-2000 employees, 90-day recency, any contact info | ✓ |
| You decide | Claude picks | |

**User's choice:** Moderate

| Option | Description | Selected |
|--------|-------------|----------|
| JSON file | External skip_list.json, configurable | ✓ |
| Hard-coded list | Python list in scoring module | |
| You decide | Claude picks | |

**User's choice:** JSON file

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, with 'below-threshold' status | Full funnel visible to reviewer | ✓ |
| No, only call-ready rows | Cleaner Airtable | |
| You decide | Claude picks | |

**User's choice:** Yes, with 'below-threshold' status

---

## Airtable Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Demo-grade | Named views, color-coded status, ordered columns | ✓ |
| Functional | All fields present, default grid view | |
| You decide | Claude picks | |

**User's choice:** Demo-grade

| Option | Description | Selected |
|--------|-------------|----------|
| One table | All data in single table, views handle filtering | |
| Two tables | Prospects + Call Outcomes, linked | ✓ |
| You decide | Claude picks | |

**User's choice:** Two tables

| Option | Description | Selected |
|--------|-------------|----------|
| Call-Ready view | Filtered to call-ready only | |
| Full Pipeline view | All prospects, all statuses | ✓ |
| You decide | Claude picks | |

**User's choice:** Full Pipeline view

| Option | Description | Selected |
|--------|-------------|----------|
| Visible as long text field | Reviewer can expand and inspect | ✓ |
| Hidden (separate artifact) | Only call_context in Airtable | |
| You decide | Claude picks | |

**User's choice:** Visible (free text: "I think having it visible somewhere would look more impressive")

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, color-coded | Green/Yellow/Red/Blue/Grey by status | ✓ |
| Plain text | Functional but less visual | |
| You decide | Claude picks | |

**User's choice:** Yes, color-coded

| Option | Description | Selected |
|--------|-------------|----------|
| Prospects: enrichment+score, Outcomes: call data | Clean separation by concern | ✓ |
| You decide | Claude designs field split | |

**User's choice:** Prospects: enrichment + score. Outcomes: call data only.

---

## Pipeline Execution

| Option | Description | Selected |
|--------|-------------|----------|
| Single script, staged | One pipeline.py with function boundaries | |
| Separate scripts per stage | discover.py, enrich.py, score.py, upload.py | ✓ |
| You decide | Claude picks | |

**User's choice:** Separate scripts (free text: wants clean, self-documenting code a technical reviewer can scan without comments)

| Option | Description | Selected |
|--------|-------------|----------|
| Idempotent upserts | batch_upsert() keyed on unique ID | ✓ |
| Wipe and recreate | Delete all rows each run | |
| You decide | Claude picks | |

**User's choice:** Idempotent upserts

| Option | Description | Selected |
|--------|-------------|----------|
| Log and skip | Warning + 'enrichment-failed' status in Airtable | ✓ |
| Drop entirely | Prospect disappears from output | |
| You decide | Claude picks | |

**User's choice:** Log and skip

| Option | Description | Selected |
|--------|-------------|----------|
| Structured logging | Per-stage summary stats | ✓ |
| Minimal | Errors and final summary only | |
| You decide | Claude picks | |

**User's choice:** Structured logging

---

## Claude's Discretion

- Category selection strategy (all three vs. start narrow)
- Exact score threshold for call-ready cutoff

## Deferred Ideas

None -- discussion stayed within phase scope.
