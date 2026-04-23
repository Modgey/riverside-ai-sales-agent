# Riverside AI Cold-Calling Agent

Automated outbound sales pipeline for Riverside.fm. Finds B2B SaaS companies with active podcasts, figures out who's worth calling, builds personalized briefings, and hands them to a voice AI agent that dials the prospect. You run the pipeline, calls go out. No manual steps in between.

The call agent is one piece of a bigger system. Discovery, qualification, enrichment, scoring, call prep, outcome tracking -- all automated.

## Architecture

![System Architecture](Riverside%20Demo%20Diagram.jpg)

## How it works

### Prospect research pipeline

Finds raw business podcast data and turns it into scored, enriched, call-ready prospects. Each stage saves output to `src/data/<step>.json` and to a database (Airtable for the demo, Postgres for production), so you can inspect results between steps or rerun any stage without starting over.

**1. Discover** -- Searches Podcast Index for B2B podcasts in target categories (Choose the following for this demo: Business, Technology, Marketing, Entrepreneurship, Management). Parses RSS feeds for host names, episode metadata, publishing cadence, and recent episode topics.

**2. Qualify (AI)** -- A local LLM (Gemma4 via Ollama) classifies each prospect: Are they real person or organization? What language do they speak? Is the domain a hosting platform (Spotify, Apple Podcasts, YouTube, etc.) or an actual company? This filters out junk before it hits paid APIs.

**3. Enrich** -- Looks up work emails and company data (industry, employee count, etc.) via an API enrichment service.

**4. Score** -- Weighted scoring model. Company size in the 100-1,000 employee range carries the most weight, then publishing cadence, data completeness, and category match. Podcasts already doing video get a bonus since Riverside's most valuable features are video based. Above the set threshold = qualified for next step.

**5. Deep enrich** -- Qualified prospects only. Pulls full episode details from RSS, scrapes company websites, and runs an LLM to build prospect profiles and production signal analysis.

**6. Phone enrich** -- Finds the mobile numbers for the remaining qualified prospects.

**7. Call context (AI)** -- An LLM reads all the enrichment data and writes a personalized call briefing: opening line, prospect context, pitch angles, predicted objections with responses, and Riverside hooks. Adapts tone based on role (executive gets strategy, practitioner gets workflow).

**8. Upload** -- Pushes everything to the database for review and call tracking.

### AI cold caller

The voice agent is a qualifier, not a closer. Its primary job is discovery: learning about the prospect's recording workflow, content output, and pain points. If there's a natural fit with Riverside, it soft-closes. If not, it wraps up gracefully. No hard pitching, no pushing past a no.

The agent runs on two layers: a fixed **harness** and a per-prospect **call context**. The harness is the same for every call: who the agent is, how it speaks, discovery questions, objection handling, and rules for wrapping up. The call context is what makes each call personal. Before dialing, the pipeline generates a briefing with a custom opening line referencing their podcast, context about their company and role, and discovery hooks the agent uses to ask smarter questions.

Discovery is the call, not a preamble to a pitch. The agent asks about recording setup, editing workflow, and what the prospect would change about their current process. It listens, follows up naturally, and only connects what it hears to Riverside if the prospect's answers reveal a genuine fit. If they mention pain around video quality, it leans into Riverside's 4K local recording. If they're happy with their current tool, it respects that. When calls go off-script, the agent adapts. It can answer questions about Riverside (pricing, features, comparisons), steer back from tangents, and recognize when someone wants off the phone.

The agent can take actions mid-call: schedule a follow-up with someone on the Riverside team, or send a signup link so the prospect can explore on their own. These happen during the conversation, not after, so the prospect gets what they need while they're still engaged.

Every call ends in one of six outcomes:

- **Meeting booked** -- prospect wants a follow-up conversation with the team
- **Interested** -- positive signal but didn't commit, goes into a nurture sequence
- **Not a fit** -- prospect declined or wrong target, logged and moved on
- **Voicemail** -- no one picked up, schedule retry
- **No answer** -- didn't connect, schedule retry
- **Do not call** -- prospect asked to be removed, added to suppression list

Outcomes get classified and written back to the database. A post-call workflow handles next steps: routing booked meetings to an AE for personalized follow-up, adding interested prospects to a nurture sequence, scheduling retries for voicemails and no-answers, and respecting suppression requests immediately.

## Tech stack

| Component | Technology |
|-----------|-----------|
| Podcast discovery | Podcast Index API (free, unlimited) |
| RSS parsing | feedparser |
| AI qualification | Ollama (local, free) |
| Contact enrichment | Hunter.io & Apollo.io |
| Phone enrichment | Datagma |
| Deep enrichment + call context | OpenRouter (Kimi K2.6) |
| Scoring | Python Algorithm |
| Database | Airtable or Postgres |
| Telephony | Twilio |
| Voice agent | _TBD_ |

## Setup

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.ai) with a model pulled.

**Install:**

```
pip install -r requirements.txt
```

**Environment variables:** Copy `src/.env.example` to `src/.env` and add your API keys.

**Run the full pipeline:**

```
py src/run_pipeline.py all
```

**Run a single step:**

```
py src/run_pipeline.py discover
py src/run_pipeline.py qualify
py src/run_pipeline.py enrich
py src/run_pipeline.py score
py src/run_pipeline.py deep_enrich
py src/run_pipeline.py phone_enrich
py src/run_pipeline.py call_context
py src/run_pipeline.py upload
```

**Check status:**

```
py src/run_pipeline.py status
```

Windows users can also run `pipeline.bat` for an interactive menu.

# Future notes

## Scaling to production

The pipeline is a straight modular line mapping cleanly to containers. Each stage becomes a Docker container pulling from a shared queue instead of passing Python dicts in memory.

The cheaper LLM steps (qualify, deep enrich) move to self-hosted models via Ollama, cutting per-token costs to zero. Steps where quality matters most (call context, voice conversation, post-call classification) stay on paid API models.

Airtable swaps out for Postgres. Voice stays on a managed platform because running your own real-time STT/TTS/telephony is not worth the effort at this scale.

The codebase already leans into this: the enrichment is provider-agnostic, prompts live in JSON config files (easily swap models without touching code), and every stage is safe to rerun.
