# ICP Decision

Read-only reference. Who we're calling and why. Decision is locked.

ICP = ideal customer profile: the specific type of company and person we're targeting with the cold-calling agent.

---

## ICP Decision

### Summary

Target: mid-market B2B SaaS companies (100-1,000 employees) running an active weekly or biweekly podcast. Target the person in a dedicated podcast role (Head of Podcasts, Podcast Producer, Content Lead), not a generic Head of Content. Pitch angle is "switch from Zoom/Squadcast to Riverside," not "start a podcast."

### What Changed from the Initial Guess

The original guess ("B2B SaaS with a podcast, target the host or Head of Content") mostly held up, but research surfaced four refinements:

1. **Company size narrowed** to 100-1,000 employees. Below that is PLG (product-led growth) territory. Above that is named-account AE territory.
2. **Target person narrowed** to a dedicated podcast role (not a broader Head of Content). Research showed hosts with titles like "Head of Podcasts" or "Podcast Producer" are both more findable and more relevant than generic content leaders.
3. **Publishing frequency narrowed** to weekly or biweekly. Monthly and ad-hoc shows dropped. Active publishing is the enrichment signal.
4. **Pitch reframed as competitive switch**, not new adoption. Riverside already has significant penetration in this ICP, so the remaining market is mostly people who use a competitor (Zoom, Squadcast, etc.), not people who haven't started a podcast yet.

### Why Option A (Podcast) Wins

**Data pipeline is clean.** Listen Notes returns podcast data, Apollo finds the host's contact info, we generate the cheat sheet, done. The agent can say very specific things on the call ("saw your episode with X last Thursday on Y"). The research data supports every step. Hosts are findable. The math works.

**Grading alignment.** The brief grades four things equally (Agentic Thinking, Technical Execution, Scalability, Business Context) and explicitly prizes creativity and original thinking. Option A wins the Technical Execution grade because the pipeline actually works reliably.

### Two Strategic Additions

1. **The write-up explicitly calls out the webinar pivot** as "what I would build next." It references Riverside's March 2026 product launches (Content Planner, Editor Role, the Webinar data study) as evidence we read their current positioning.
2. **One of the 2-3 demo calls uses a hand-written webinar-prospect cheat sheet** (a JSON file, no enrichment pipeline needed). This proves the harness + cheat-sheet architecture generalizes to a different audience without building a second pipeline.

---

## Option B (Webinar): What It Is and Why We Didn't Build It

### The Option

Mid-market B2B SaaS companies (100-1,000 employees) running a recurring webinar series (monthly or more often). Target the Demand Gen or Content Marketing leader. Pitch angle is tool consolidation (Riverside replaces Zoom Webinars + editing + publishing) plus native HubSpot integration.

### Why It's Strategically Interesting

- Matches Riverside's actual 2026 growth push. March 2026 product launches (Content Planner, Editor Role, the March 31 data study reframing webinars as a "tool consolidation" play) all signal webinars are where Riverside is trying to grow next.
- Most applicants will default to podcasts, so this would stand out.
- Stronger alignment signal that we read their recent positioning.

### Why We Didn't Build It

- **Data pipeline is messier.** Webinar signals require checking a company's tech stack (using BuiltWith or similar, to detect Zoom Webinars / On24 / Goldcast) plus scraping company blogs and events pages. No single clean API like Listen Notes exists for webinars.
- **More engineering time** for a 4-day project.
- **Weaker personalization on the call.** A webinar signal is less specific than "your most recent podcast episode." The agent can't say "saw your webinar on X last Thursday" with the same confidence.

### How We Reference It

1. The write-up calls out the webinar pivot as "what I would build next," referencing Riverside's March 2026 product launches as evidence we read their positioning.
2. One of the 2-3 demo calls uses a hand-written webinar-prospect cheat sheet (a JSON file, no enrichment pipeline needed). This proves the harness + cheat-sheet architecture generalizes to a different audience without building a second pipeline.
