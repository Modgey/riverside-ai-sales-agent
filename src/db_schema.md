# Database schema

This is the demo-scale schema. Everything lives in one Airtable table to keep things simple and easily-inspectable (one link, full visibility).

## Fields

| Field | Type | Set by | Description |
|-------|------|--------|-------------|
| podcast_name | text | discover | Name of the podcast (primary key for upserts) |
| host_name | text | discover | Raw host name from RSS feed |
| first_name | text | qualify | Cleaned first name extracted by AI |
| last_name | text | qualify | Cleaned last name extracted by AI |
| domain | text | discover | Company domain parsed from RSS |
| qualification_status | text | qualify | qualified, disqualified, or existing_riverside_customer |
| language | text | qualify | Detected podcast language |
| categories | text | discover | Podcast categories (comma-separated) |
| episode_count | number | discover | Total episodes in the RSS feed |
| episode_cadence | number | discover | Average days between episodes |
| last_publish_time | number | discover | Unix timestamp of most recent episode |
| recent_episode_topic | text | discover | Title of the most recent episode |
| has_video | checkbox | discover | True if video signals detected in RSS feed |
| work_email | email | enrich | Prospect's work email |
| title | text | enrich | Job title from enrichment provider |
| company_name | text | enrich | Company name from enrichment provider |
| company_size | number | enrich | Employee count |
| industry | text | enrich | Company industry |
| enrichment_status | text | enrich | enriched or enrichment-failed |
| score | number | score | Weighted fit score (0-100) |
| status | text | score | Qualified, Nurture, Disqualified, or Skipped |
| disqualify_reason | text | score | Why the prospect was disqualified (if applicable) |
| episode_details | long text | deep_enrich | JSON array of recent episodes (title, description, guest) |
| podcast_profile | long text | deep_enrich | LLM-generated podcast niche, format, guest patterns |
| company_profile | long text | deep_enrich | LLM-generated company product, market, content signals |
| production_signals | long text | deep_enrich | LLM-observed video, remote guests, tools, quality signals |
| phone_number | phone | phone_enrich | Mobile number for dialing |
| call_context | long text | call_context | JSON string of AI-generated call briefing (opener, angles, objections) |

## Production notes

In production, this splits into separate tables: prospects (contact info, role), companies (shared across prospects at the same org), podcasts (RSS metadata, cadence), episodes (individual episode rows instead of a JSON blob in a text field), calls (one row per call attempt with outcome, duration, transcript), and call context (briefing fields broken out properly instead of a JSON string).

A few things are deliberately rough here:

- `podcast_name` is the upsert key. Two podcasts could share a name. Production would use a unique ID.
- Status fields are free text. Would be enums with constraints.
- `last_publish_time` is a raw Unix timestamp. Would be a datetime.
- Airtable caps at 1K records and 5 req/sec. Postgres removes both limits.
- No indexes beyond the upsert key. Would add indexes on status, score, domain, and company.
