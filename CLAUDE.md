<!-- GSD:project-start source:PROJECT.md -->
## Project

**Riverside AI Cold-Calling Agent**

An end-to-end AI-powered outbound sales system for Riverside.fm prospects. It automatically discovers B2B SaaS companies with active podcasts, enriches and scores them, generates personalized call context, and places cold calls via a voice AI agent. Built as Part 2 of Riverside's GTM Engineer home assignment.

This is a repeatable GTM function, not a one-off cold-caller. The call agent is one node in a larger pipeline that handles everything from prospect discovery to post-call follow-up.

**Core Value:** A fully automated pipeline from raw podcast data to a completed, logged, outcome-classified sales call, with zero manual steps between "run the pipeline" and "calls go out."

### Constraints

- **Timeline**: ~3 working days (Mon-Wed), assignment due Thursday 09:00 IDT
- **Budget**: $10-15 max for paid APIs. Free tiers wherever possible (Podcast Index free, Apollo free, Vapi free credits)
- **Demo calls**: test numbers only (Shawn's phone, friend's phone), not real prospects. Legal/TCPA compliance.
- **Airtable**: free tier, 1,000 record cap. Fine for 30-100 prospects at demo scale.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Voice AI Platform
| Technology | Version/Tier | Purpose | Why |
|------------|-------------|---------|-----|
| Vapi | Pay-as-you-go, ~$0.15/min all-in | Orchestrates voice calls: STT, LLM, TTS, telephony | Only platform with first-class Claude support, a Python server SDK (v1.10.0), and clean function-calling via webhooks. $10 free credit on signup covers ~60-70 demo minutes. |
### LLM
| Technology | Model ID | Purpose | Why |
|------------|----------|---------|-----|
| Anthropic Claude | `claude-sonnet-4-20250514` | Powers the voice agent conversation AND generates per-prospect call context at pipeline time | This is Shawn's native stack. Sonnet 4 is the right tier: Haiku is too thin for real-time conversation quality, Opus is cost-overkill at $5/M tokens input. Sonnet hits $3/$15 per M tokens (input/output). Vapi confirmed Claude 4 models available as of May 2025. |
### Podcast Discovery
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Podcast Index API | Free (no rate cap published) | Discover B2B podcasts by keyword and category | Truly free, no monthly request cap (unlike Listen Notes 300 req/mo on free tier). Returns RSS URLs directly, so no secondary lookup needed. |
| `python-podcastindex` | Latest (PyPI) | Python wrapper for Podcast Index API | Thin wrapper that handles HMAC auth headers (required by Podcast Index). Simpler than rolling raw `requests` calls for auth. |
### RSS Parsing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `feedparser` | 6.0.12 (stable) | Parse RSS feeds to extract host name, episode metadata, episode cadence, show description | The standard Python library for this job. Handles RSS 2.0, Atom, and Apple iTunes podcast extensions (which carry `itunes:author`, episode counts, etc.) in one parse call. No auth needed. |
### Contact and Company Enrichment
| Technology | Version/Tier | Purpose | Why |
|------------|-------------|---------|-----|
| Apollo.io API | Free tier | Given a person name + company domain, return work email, company size, industry, LinkedIn URL | 10K email credits/month on the free tier (verified-domain accounts). The `/v1/people/match` endpoint handles a name + domain and returns enriched contact data. No SDK needed, plain `requests` calls. |
- `POST /v1/people/match` - person enrichment (name + domain in, email + title + firmographics out)
- `POST /v1/organizations/enrich` - company enrichment (domain in, headcount + industry + funding out)
### Prospect Database
| Technology | Version/Tier | Purpose | Why |
|------------|-------------|---------|-----|
| Airtable | Free tier (1,000 records/base) | Store prospects, enrichment data, scores, call status, call outcomes | Reviewer-inspectable without any setup. One Airtable link in the write-up and Mattan can see every prospect row. pyairtable handles upserts cleanly. |
| `pyairtable` | 3.3.0 (released 2025-11-05) | Python client for Airtable API | Handles 429 rate-limit retries automatically (Airtable's 5 req/sec per base limit). `batch_upsert()` is cleaner than individual creates when re-running the pipeline. |
### Orchestration / Pipeline
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python 3.11+ | - | Pipeline script: discovery, enrichment, scoring, Airtable upsert, Vapi call dispatch | No framework needed at this scale. A single `pipeline.py` with clean function boundaries is more debuggable and faster to build in 3 days than LangGraph or n8n for this use case. |
| `anthropic` (Python SDK) | Latest (PyPI) | Call Claude API for per-prospect call context generation | Shawn's native stack. Direct SDK call at pipeline time, not real-time. |
| `requests` | 2.x | Apollo API calls, any raw HTTP needed | Standard. |
| `python-dotenv` | Latest | Load `.env` for API keys | Standard. |
## What NOT to Use and Why
| Category | Avoid | Reason |
|----------|-------|--------|
| Voice platform | Bland AI | No free trial. Billed from first minute. More expensive to experiment with in a 3-day window. Pathways builder adds a UI layer that slows iteration. |
| Voice platform | Retell AI | No meaningful advantage over Vapi for this use case. Vapi has better Python SDK and is already in the plan. Retell's latency advantage (2.1s vs 2.6s) is irrelevant at demo scale. |
| LLM (pipeline) | GPT-4o | Shawn's native stack is Claude. No switching cost benefit. |
| LLM (pipeline) | Claude Haiku | Thin reasoning for call context generation. The context generation step is offline/batch so cost savings don't matter much; Sonnet quality is worth it. |
| Podcast discovery | Listen Notes | 300 req/mo free cap. At 100 candidate podcasts that's fine, but the cap adds friction. Podcast Index is uncapped and free. |
| Enrichment | Hunter.io, Clearbit | Hunter.io free tier is very limited (25 searches/mo). Clearbit is expensive. Apollo's free tier is genuinely workable. |
| Database | SQLite / JSON files | Reviewer can't inspect it without running the code. Airtable link solves this. |
| Database | Postgres | Massive overkill for 30-100 records over 3 days. |
| Orchestration | LangGraph | Adds framework weight for a linear pipeline. Justified for multi-step agent loops; wrong for a sequential ETL (extract, transform, load) pipeline. |
| Orchestration | n8n | GUI workflow builder adds a setup step and makes the code harder to show in the write-up. Pure Python is more auditable. |
## Installation
# Core pipeline
# Vapi voice layer
# Optional: for RSS auth if needed separately
## Cost Estimate
| Service | Usage at demo scale | Cost |
|---------|---------------------|------|
| Vapi | ~3 calls x 5 min avg | ~$2.25 from free credit ($10 included) |
| Anthropic (call context gen) | ~30 prospects x ~2K tokens out | ~$0.90 |
| Anthropic (post-call classification) | ~3 transcripts x ~500 tokens | ~$0.02 |
| Podcast Index | Unlimited | $0 |
| Apollo free tier | 30-100 enrichments | $0 |
| Airtable free tier | 30-100 rows | $0 |
| **Total** | | **~$3.17 from own budget, rest from Vapi credit** |
## Architecture Wiring
## Sources
- Vapi pricing and credits: https://vapi.ai/pricing, https://blog.dograh.com/vapi-pricing-breakdown-2025-plans-hidden-costs-what-to-expect/
- Vapi Claude model support: https://vapi.ai/blog/claude-4-models-now-available-in-vapi, https://docs.vapi.ai/changelog/2025/5/22
- Vapi Python SDK: https://pypi.org/project/vapi-server-sdk/ (v1.10.0, April 2026)
- Vapi custom tools: https://docs.vapi.ai/tools/custom-tools
- Bland vs Vapi vs Retell comparison: https://www.whitespacesolutions.ai/content/bland-ai-vs-vapi-vs-retell-comparison
- Anthropic model pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Podcast Index API: https://podcastindex-org.github.io/docs-api/
- python-podcastindex: https://pypi.org/project/python-podcastindex/
- feedparser: https://feedparser.readthedocs.io/en/stable/introduction.html
- Apollo API enrichment: https://docs.apollo.io/reference/people-enrichment, https://docs.apollo.io/docs/api-pricing
- pyairtable: https://pypi.org/project/pyairtable/ (v3.3.0, Nov 2025)
- Airtable rate limits: https://airtable.com/developers/web/api/rate-limits
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
