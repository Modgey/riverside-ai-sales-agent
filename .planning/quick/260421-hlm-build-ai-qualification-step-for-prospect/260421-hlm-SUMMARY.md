---
status: complete
---

# Quick Task 260421-hlm: AI Qualification Step

## What was built

AI qualification step (`src/pipeline/qualify.py`) that sits between discover and enrich in the prospect pipeline. Uses Gemma 3 4B via Ollama to classify each prospect from discover.json.

Per prospect, sends only host_name, podcast_name, and domain to the model. Model returns structured JSON validated by Pydantic: is_person, first_name, last_name, language, is_hosting_domain.

## Changes

| Task | Commit | Files |
|------|--------|-------|
| Create qualify.py with Pydantic + Ollama | 93f810e | src/pipeline/qualify.py, src/pipeline/models.py, src/pipeline/enrich.py, requirements.txt |
| Wire into pipeline runner + batch menu | d5309ff | src/run_pipeline.py, pipeline.bat |

## Key details

- **Fallback**: If Ollama fails (retry once), falls back to existing heuristic functions (looks_like_person_name, split_name, is_hosting_platform)
- **Disqualification reasons**: org_not_person, non_english, hosting_domain, existing_riverside_customer
- **Pipeline is now 5 stages**: discover -> qualify -> enrich -> score -> upload
- **Enrich reads qualified.json** and only spends Prospeo credits on qualified prospects
- **Expanded blocklists**: Added 9 missing hosting platform domains and 7 non-person words to enrich.py
