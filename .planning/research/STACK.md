# Technology Stack

**Project:** Riverside AI Cold-Calling Agent
**Researched:** 2026-04-20
**Confidence:** MEDIUM-HIGH (verified with official docs and PyPI where possible; Vapi pricing is a moving target)

---

## Recommended Stack

### Voice AI Platform

| Technology | Version/Tier | Purpose | Why |
|------------|-------------|---------|-----|
| Vapi | Pay-as-you-go, ~$0.15/min all-in | Orchestrates voice calls: STT, LLM, TTS, telephony | Only platform with first-class Claude support, a Python server SDK (v1.10.0), and clean function-calling via webhooks. $10 free credit on signup covers ~60-70 demo minutes. |

Vapi's `vapi-server-sdk` (PyPI, v1.10.0, released April 2026) exposes `client.calls.create()` for outbound calls and a webhook format for mid-call tool use. The assistant definition takes a `model` block (provider: `anthropic`, model: `claude-sonnet-4-20250514`) plus a `tools` array where each tool has a name, description, parameters, and a server URL that Vapi POSTs to when the agent invokes it.

**Confidence: MEDIUM.** Vapi's docs confirm Claude model support and custom tools. Exact per-minute all-in cost is variable because STT (Deepgram) and TTS (ElevenLabs or Cartesia) are billed separately per provider rates. Budget $0.15-0.25/min total for a 3-5 minute demo call.

### LLM

| Technology | Model ID | Purpose | Why |
|------------|----------|---------|-----|
| Anthropic Claude | `claude-sonnet-4-20250514` | Powers the voice agent conversation AND generates per-prospect call context at pipeline time | This is Shawn's native stack. Sonnet 4 is the right tier: Haiku is too thin for real-time conversation quality, Opus is cost-overkill at $5/M tokens input. Sonnet hits $3/$15 per M tokens (input/output). Vapi confirmed Claude 4 models available as of May 2025. |

For call context generation (pipeline step, not real-time), use the Anthropic Python SDK directly. For the voice agent, use Claude via Vapi's Anthropic provider integration.

**Confidence: HIGH.** Confirmed via Anthropic pricing page and Vapi changelog (May 22, 2025).

### Podcast Discovery

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Podcast Index API | Free (no rate cap published) | Discover B2B podcasts by keyword and category | Truly free, no monthly request cap (unlike Listen Notes 300 req/mo on free tier). Returns RSS URLs directly, so no secondary lookup needed. |
| `python-podcastindex` | Latest (PyPI) | Python wrapper for Podcast Index API | Thin wrapper that handles HMAC auth headers (required by Podcast Index). Simpler than rolling raw `requests` calls for auth. |

**Important gap:** The Podcast Index API's search endpoint does not natively filter by employee count or company size. Category filter (e.g., `Business`, `Technology`, `Marketing`) and language filter are available in the API. Recency is available via `since` parameter on episode endpoints. Company size filtering happens downstream in the scoring layer using Apollo enrichment data, not at the discovery step.

**Confidence: MEDIUM.** API is confirmed free with no published rate limit. Filter parameters verified via PyPI wrapper docs and community examples; category/language filters confirmed in API response metadata if not all as query params.

### RSS Parsing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `feedparser` | 6.0.12 (stable) | Parse RSS feeds to extract host name, episode metadata, episode cadence, show description | The standard Python library for this job. Handles RSS 2.0, Atom, and Apple iTunes podcast extensions (which carry `itunes:author`, episode counts, etc.) in one parse call. No auth needed. |

Use `feedparser` over the podcast-specific wrappers (`podcastparser`, `pyPodcastParser`). The podcast-specific ones are built for media player use cases. `feedparser` gives richer access to all iTunes extension tags relevant here (author, owner, category, explicit flag).

**Confidence: HIGH.** feedparser 6.0.12 is stable, well-documented, actively maintained.

### Contact and Company Enrichment

| Technology | Version/Tier | Purpose | Why |
|------------|-------------|---------|-----|
| Apollo.io API | Free tier | Given a person name + company domain, return work email, company size, industry, LinkedIn URL | 10K email credits/month on the free tier (verified-domain accounts). The `/v1/people/match` endpoint handles a name + domain and returns enriched contact data. No SDK needed, plain `requests` calls. |

Apollo endpoints used:
- `POST /v1/people/match` - person enrichment (name + domain in, email + title + firmographics out)
- `POST /v1/organizations/enrich` - company enrichment (domain in, headcount + industry + funding out)

Credit consumption: people search (`/v1/people/search`) does NOT consume credits per Apollo's docs. People enrichment (`/v1/people/match`) DOES consume credits when it reveals an email. Budget: 30-100 prospects at demo scale = well within free tier.

**Confidence: MEDIUM.** Free tier email credit limits are inconsistently documented across sources. The 10K figure comes from multiple third-party sources; exact limit may depend on domain verification status. Test with a small batch first before running the full pipeline.

### Prospect Database

| Technology | Version/Tier | Purpose | Why |
|------------|-------------|---------|-----|
| Airtable | Free tier (1,000 records/base) | Store prospects, enrichment data, scores, call status, call outcomes | Reviewer-inspectable without any setup. One Airtable link in the write-up and Mattan can see every prospect row. pyairtable handles upserts cleanly. |
| `pyairtable` | 3.3.0 (released 2025-11-05) | Python client for Airtable API | Handles 429 rate-limit retries automatically (Airtable's 5 req/sec per base limit). `batch_upsert()` is cleaner than individual creates when re-running the pipeline. |

Rate limit note: Airtable free tier is 5 requests/sec per base, applies to all tiers. At demo scale (30-100 prospects), this is not a problem. `pyairtable` retries 429s up to 5 times by default.

**Confidence: HIGH.** Rate limits and pyairtable version confirmed via PyPI and official Airtable docs.

### Orchestration / Pipeline

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python 3.11+ | - | Pipeline script: discovery, enrichment, scoring, Airtable upsert, Vapi call dispatch | No framework needed at this scale. A single `pipeline.py` with clean function boundaries is more debuggable and faster to build in 3 days than LangGraph or n8n for this use case. |
| `anthropic` (Python SDK) | Latest (PyPI) | Call Claude API for per-prospect call context generation | Shawn's native stack. Direct SDK call at pipeline time, not real-time. |
| `requests` | 2.x | Apollo API calls, any raw HTTP needed | Standard. |
| `python-dotenv` | Latest | Load `.env` for API keys | Standard. |

**Confidence: HIGH.**

---

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

---

## Installation

```bash
# Core pipeline
pip install python-podcastindex feedparser anthropic requests python-dotenv pyairtable

# Vapi voice layer
pip install vapi-server-sdk

# Optional: for RSS auth if needed separately
pip install hashlib  # stdlib, already available
```

---

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

Well within the $10-15 budget constraint.

---

## Architecture Wiring

```
pipeline.py
  1. Podcast Index API  -->  candidate podcasts (name, RSS URL, category)
  2. feedparser         -->  host name, episode cadence, last episode date
  3. Apollo /people/match  -->  work email, title, company size, industry
  4. Scoring function   -->  fit score, hard-filter disqualification
  5. Airtable upsert    -->  prospect rows visible to reviewer
  6. Claude API         -->  per-prospect call context (opener, pain points, objections)
  7. Vapi calls.create  -->  outbound call placed with harness + call context

  On call end:
  8. Vapi webhook       -->  transcript delivered to outcome_handler.py
  9. Claude API         -->  outcome classification (booked/interested/voicemail/etc.)
  10. Airtable update   -->  outcome + notes written back to prospect row
```

Mid-call function calls (book meeting, send signup link) go via Vapi's custom tools webhook to a lightweight FastAPI or Flask endpoint, or a Replit/ngrok tunnel for the demo.

---

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
