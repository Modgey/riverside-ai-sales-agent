---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/pipeline/models.py
  - src/pipeline/qualify.py
  - src/pipeline/enrich.py
  - src/run_pipeline.py
  - pipeline.bat
  - requirements.txt
autonomous: true
requirements: []
must_haves:
  truths:
    - "Running `py src/run_pipeline.py qualify` reads discover.json, classifies each prospect via Gemma 4, and writes qualified.json"
    - "Prospects with riverside.fm in rss_url are flagged existing_riverside_customer and skipped from LLM call"
    - "Pydantic validation failure triggers one retry then falls back to heuristic functions"
    - "Enrich step now reads qualified.json instead of discover.json"
  artifacts:
    - path: "src/pipeline/qualify.py"
      provides: "AI qualification step using Ollama + Gemma 4"
    - path: "src/data/qualified.json"
      provides: "Classified prospects with qualification_status, first_name, last_name, language fields"
  key_links:
    - from: "src/run_pipeline.py"
      to: "src/pipeline/qualify.py"
      via: "import qualify_prospects, called in run_qualify()"
    - from: "src/pipeline/qualify.py"
      to: "ollama.chat"
      via: "ollama Python client, model=gemma3:4b"
    - from: "src/run_pipeline.py run_enrich()"
      to: "src/data/qualified.json"
      via: "load('qualified') instead of load('discover')"
---

<objective>
Build the AI qualification step (qualify.py) that sits between discover and enrich in the pipeline. Uses Gemma 3 4B via Ollama to classify each prospect as person vs org, detect language, and identify hosting domains. Pydantic validates LLM responses with heuristic fallback.

Purpose: Replace brittle regex heuristics with LLM classification for higher accuracy on messy podcast host names, while keeping the heuristics as a safety net.
Output: Working qualify step integrated into pipeline runner and batch menu.
</objective>

<execution_context>
@.claude/CLAUDE.md
</execution_context>

<context>
@src/pipeline/models.py
@src/pipeline/enrich.py
@src/pipeline/discover.py
@src/run_pipeline.py
@pipeline.bat
@requirements.txt

<interfaces>
From src/pipeline/models.py:
```python
class ProspectDict(TypedDict, total=False):
    podcast_name: str
    host_name: str
    rss_url: str
    domain: str
    cadence_days: Optional[float]
    recent_episode_topic: str
    episode_count: int
    categories: dict
    last_publish_time: int
    work_email: Optional[str]
    title: Optional[str]
    company_name: Optional[str]
    company_size: Optional[int]
    industry: Optional[str]
    enrichment_status: str
    score: int
    status: str
    disqualify_reason: Optional[str]
    cheat_sheet: Optional[str]
```

From src/pipeline/enrich.py (fallback functions):
```python
def is_hosting_platform(domain: str) -> bool: ...
def looks_like_person_name(full_name: str) -> bool: ...
def split_name(full_name: str) -> tuple[str, str]: ...

HOSTING_PLATFORM_DOMAINS: set  # 22 domains
NON_PERSON_WORDS: set  # 18 words
```

From src/run_pipeline.py:
```python
STEPS = ["discover", "enrich", "score", "upload"]
def save(step_name: str, prospects: list[dict]): ...
def load(step_name: str) -> list[dict]: ...
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create qualify.py with Pydantic model and Ollama integration</name>
  <files>src/pipeline/qualify.py, src/pipeline/models.py, requirements.txt</files>
  <action>
**requirements.txt:** Add `ollama>=0.4.0` and `pydantic>=2.0.0` to requirements.

**src/pipeline/models.py:** Add four new optional fields to ProspectDict:
- `first_name: Optional[str]`
- `last_name: Optional[str]`
- `language: Optional[str]`
- `qualification_status: Optional[str]`

**src/pipeline/qualify.py:** Create the qualification module:

1. **Pydantic response model** `QualifyResponse(BaseModel)`:
   - `is_person: bool`
   - `first_name: str`
   - `last_name: str`
   - `language: str` (ISO 639-1 two-letter code)
   - `is_hosting_domain: bool`

2. **System prompt** (constant string, no few-shot). Classification spec telling the model:
   - You classify podcast prospects. Given host_name, podcast_name, domain.
   - Determine if host_name is a real person (not org/show name/multiple people).
   - Extract first_name and last_name from host_name (best effort, empty string if unclear).
   - Detect the primary language of the podcast_name (return ISO 639-1 code, default "en").
   - Determine if domain is a podcast hosting platform (not the podcast's own website).
   - Return ONLY valid JSON matching the schema. No markdown, no explanation.

3. **`call_ollama(host_name, podcast_name, domain) -> QualifyResponse | None`**:
   - Build user message: `{"host_name": host_name, "podcast_name": podcast_name, "domain": domain}`
   - Call `ollama.chat(model="gemma3:4b", messages=[system, user], format="json", options={"temperature": 0})`
   - Parse response content as JSON, validate with `QualifyResponse(**parsed)`
   - On any exception (JSON decode, Pydantic validation, ollama error): return None

4. **`heuristic_fallback(host_name, domain) -> QualifyResponse`**:
   - Import `looks_like_person_name`, `split_name`, `is_hosting_platform` from `pipeline.enrich`
   - `is_person = looks_like_person_name(host_name)`
   - `first_name, last_name = split_name(host_name) if is_person else ("", "")`
   - `is_hosting_domain = is_hosting_platform(domain)`
   - `language = "en"` (heuristic cannot detect language, assume English)
   - Return `QualifyResponse(...)` with these values

5. **`qualify_prospect(prospect: ProspectDict) -> ProspectDict`**:
   - If "riverside.fm" in prospect.get("rss_url", "").lower(): set qualification_status="existing_riverside_customer", disqualify_reason="existing_riverside_customer", return immediately
   - Call `call_ollama(host_name, podcast_name, domain)`
   - If None (first failure): retry once with `call_ollama` again
   - If still None: use `heuristic_fallback(host_name, domain)`, print warning
   - Apply qualification logic from QualifyResponse:
     - `not result.is_person` -> qualification_status="disqualified", disqualify_reason="org_not_person"
     - `result.language != "en"` -> qualification_status="disqualified", disqualify_reason="non_english"
     - `result.is_hosting_domain` -> qualification_status="disqualified", disqualify_reason="hosting_domain"
     - Otherwise -> qualification_status="qualified"
   - Set prospect fields: first_name, last_name, language, qualification_status, disqualify_reason (None if qualified)
   - Return prospect

6. **`qualify_prospects(prospects: list[ProspectDict]) -> list[ProspectDict]`**:
   - Public entry point. Iterates all prospects, calls qualify_prospect on each.
   - Print progress every 10 prospects: `f"  Qualifying... {i+1}/{total}"`
   - Print summary at end: counts of qualified, disqualified (by reason), riverside customers, fallbacks used.
   - Return full list (qualified + disqualified, all included).

**Expanded HOSTING_PLATFORM_DOMAINS in enrich.py:** Add these missing domains to the existing set: "substack.com", "podcasts.apple.com", "soundcloud.com", "podfollow.com", "linktr.ee", "casted.us", "repodcast.com", "ivoox.com", "podpage.com".

**Expanded NON_PERSON_WORDS in enrich.py:** Add: "agency", "capital", "solutions", "ventures", "club", "university", "partners".
  </action>
  <verify>
    <automated>cd "C:/Users/modge/OneDrive/Desktop/Repos/Riverside_Assignment" && py -c "from pipeline.qualify import qualify_prospects, QualifyResponse; print('imports OK')" 2>&1 || echo "IMPORT FAILED"</automated>
  </verify>
  <done>
  - qualify.py exists with all 4 functions and the Pydantic model
  - ProspectDict has the 4 new optional fields
  - requirements.txt includes ollama and pydantic
  - enrich.py has expanded domain and non-person word sets
  - Module imports cleanly
  </done>
</task>

<task type="auto">
  <name>Task 2: Wire qualify step into pipeline runner and batch menu</name>
  <files>src/run_pipeline.py, pipeline.bat</files>
  <action>
**src/run_pipeline.py:**

1. Add import: `from pipeline.qualify import qualify_prospects`
2. Update STEPS: `["discover", "qualify", "enrich", "score", "upload"]`
3. Add `run_qualify()` function (follows exact pattern of run_discover/run_enrich):
   ```python
   def run_qualify():
       print("\n[Stage 2/5] Qualification")
       print("-" * 40)
       raw = load("discover")
       qualified = qualify_prospects(raw)
       save("qualified", qualified)
       q_count = sum(1 for p in qualified if p.get("qualification_status") == "qualified")
       dq_count = sum(1 for p in qualified if p.get("qualification_status") == "disqualified")
       rs_count = sum(1 for p in qualified if p.get("qualification_status") == "existing_riverside_customer")
       print(f"\n  Done: {q_count} qualified, {dq_count} disqualified, {rs_count} riverside customers")
       return qualified
   ```
4. Update `run_enrich()`:
   - Change stage label to `[Stage 3/5] Enrichment`
   - Change `load("discover")` to `load("qualified")`
   - Add filter: only pass prospects where `qualification_status == "qualified"` to `enrich_prospects()`, then recombine with disqualified at the end before save
5. Update `run_score()` stage label to `[Stage 4/5] Scoring`
6. Update `run_upload()` stage label to `[Stage 5/5] Upload to Airtable`
7. Update `run_all()` to call `run_qualify()` between discover and enrich
8. Add elif for "qualify" in the `__main__` dispatch block
9. Update `print_usage()` to include qualify step
10. Update `print_status()`: add "qualified" to the STEPS list, add summary line for qualified step showing qualified/disqualified/riverside counts

**pipeline.bat:**

1. Add `if /i "%~1"=="qualify" goto qualify` in the argument parsing section (after discover, before enrich)
2. Update menu display. Renumber: 1=discover, 2=qualify, 3=enrich, 4=score, 5=upload, 6=all, 7=status, 0=exit
3. Update choice routing to match new numbers
4. Add `:qualify` label block (same pattern as :discover):
   ```
   :qualify
   echo.
   py -X utf8 src/run_pipeline.py qualify
   echo.
   pause
   goto menu
   ```
  </action>
  <verify>
    <automated>cd "C:/Users/modge/OneDrive/Desktop/Repos/Riverside_Assignment" && py -c "from run_pipeline import run_qualify, STEPS; assert 'qualify' in STEPS; assert STEPS.index('qualify') == 1; print('wiring OK')" 2>&1 || echo "WIRING FAILED"</automated>
  </verify>
  <done>
  - `py src/run_pipeline.py qualify` runs the qualification step end to end (reads discover.json, writes qualified.json)
  - `py src/run_pipeline.py enrich` reads qualified.json (not discover.json) and only enriches qualified prospects
  - `py src/run_pipeline.py all` runs all 5 steps in order
  - `py src/run_pipeline.py status` shows qualify step status
  - pipeline.bat menu has qualify as option 2
  - STEPS list is ["discover", "qualify", "enrich", "score", "upload"]
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>AI qualification step using Gemma 3 4B via Ollama. Reads discover.json (87 prospects), classifies each via LLM, writes qualified.json with qualification_status and name fields.</what-built>
  <how-to-verify>
    1. Make sure Ollama is running locally with gemma3:4b model (`ollama list` should show it)
    2. Run: `py -X utf8 src/run_pipeline.py qualify`
    3. Check the console output:
       - Should process 87 prospects
       - Should show counts of qualified, disqualified (by reason), riverside customers
       - Should show if any fallbacks were used
    4. Open `src/data/qualified.json` and spot-check:
       - Prospects should have first_name, last_name, language, qualification_status fields
       - Org names (like "Podcast Network") should be disqualified with reason "org_not_person"
       - Non-English podcasts should be disqualified with reason "non_english"
       - Hosting platform domains should be disqualified with reason "hosting_domain"
       - Normal person-hosted English podcasts should be "qualified"
    5. Run: `py -X utf8 src/run_pipeline.py status` to confirm qualified step shows in status
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues</resume-signal>
</task>

</tasks>

<verification>
- `py -c "from pipeline.qualify import qualify_prospects"` imports without error
- `py src/run_pipeline.py qualify` produces qualified.json from discover.json
- `py src/run_pipeline.py enrich` reads qualified.json (not discover.json)
- qualified.json contains all 87 prospects with qualification_status field
- Pydantic validation works (test by checking QualifyResponse instantiation)
</verification>

<success_criteria>
- qualify.py exists and integrates Ollama (gemma3:4b) with Pydantic validation
- Pipeline runs 5 steps: discover -> qualify -> enrich -> score -> upload
- Fallback to heuristics works when Ollama is unavailable or returns bad JSON
- qualified.json written with qualification_status, first_name, last_name, language for every prospect
</success_criteria>

<output>
After completion, update LOGBOOK.md with the qualify step addition and any observations about LLM classification accuracy vs heuristics.
</output>
