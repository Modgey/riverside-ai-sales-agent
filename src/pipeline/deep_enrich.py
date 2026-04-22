"""Deep enrichment: RSS episode details, company scraping, and LLM theme/summary generation."""

import json
import os
import re

import feedparser
import ollama
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from pipeline.models import ProspectDict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompts", "deep_enrich.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CONFIG = load_config()


class DeepEnrichResponse(BaseModel):
    podcast_themes: str
    company_summary: str


# Guest name regex patterns: match "with John Smith", "ft. Jane Doe", "featuring Bob",
# "| Sarah Jones" in episode titles. Avoids itunes_author (unreliable per research).
GUEST_PATTERNS = [
    r'\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
    r'\bft\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
    r'\bfeat(?:uring)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
    r'\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
]


def extract_guest_name(entry: dict) -> str | None:
    """Extract guest name from episode title using regex heuristics."""
    title = entry.get("title", "")
    for pattern in GUEST_PATTERNS:
        match = re.search(pattern, title)
        if match:
            return match.group(1)
    return None


def clean_description(raw: str, max_chars: int = 500) -> str:
    """Strip HTML tags and collapse whitespace, truncate to max_chars."""
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


def extract_episode_details(rss_url: str) -> tuple[list[dict], list[str]]:
    """Parse RSS feed for recent episode details and broader title list.

    Returns:
        Tuple of (episode_details for top 3, episode_titles for top 10).
    """
    feed = feedparser.parse(rss_url)
    entries = feed.entries

    episode_details = []
    for entry in entries[:3]:
        raw_desc = entry.get("summary", "") or entry.get("description", "")
        episode_details.append({
            "title": entry.get("title", ""),
            "description": clean_description(raw_desc),
            "guest_name": extract_guest_name(entry),
            "published": entry.get("published", ""),
        })

    episode_titles = [e.get("title", "") for e in entries[:10]]

    return episode_details, episode_titles


def scrape_company_text(domain: str, timeout: int = 8) -> str:
    """Scrape company description from homepage meta tags, falling back to /about.

    Returns empty string on any failure (prospect stays call-ready per D-06).
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    for path in ["", "/about"]:
        url = f"https://{domain}{path}"
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "lxml")

            # Priority: og:description, meta description, h1 text
            og = soup.find("meta", property="og:description")
            if og and og.get("content", "").strip():
                return og["content"].strip()

            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content", "").strip():
                return meta["content"].strip()

            h1 = soup.find("h1")
            if h1 and h1.get_text(strip=True):
                return h1.get_text(strip=True)

        except Exception:
            if path == "":
                continue  # Try /about before giving up
            return ""

    return ""


def call_ollama_deep(
    episode_titles: list[str],
    episode_descriptions: list[str],
    raw_company_text: str,
) -> DeepEnrichResponse | None:
    """Call Ollama for combined podcast theme + company summary generation.

    Returns None on any failure (same pattern as qualify.py).
    """
    user_msg = json.dumps({
        "episode_titles": episode_titles[:10],
        "episode_descriptions": episode_descriptions[:3],
        "company_raw": raw_company_text[:800],
    })

    try:
        response = ollama.chat(
            model=CONFIG["model"],
            messages=[
                {"role": "system", "content": CONFIG["system_prompt"]},
                {"role": "user", "content": user_msg},
            ],
            format="json",
            options={"temperature": CONFIG["temperature"]},
        )
        parsed = json.loads(response["message"]["content"])
        return DeepEnrichResponse(**parsed)
    except Exception:
        return None


def deep_enrich_prospects(prospects: list[ProspectDict]) -> list[ProspectDict]:
    """Deep enrich call-ready prospects with episode details, company text, and LLM summaries."""
    call_ready = [p for p in prospects if p.get("status") == "call-ready"]
    others = [p for p in prospects if p.get("status") != "call-ready"]

    print(f"  Deep enriching {len(call_ready)} call-ready prospects ({len(others)} others skipped)")

    scraped_fail = 0
    llm_fail = 0

    for i, prospect in enumerate(call_ready):
        safe_name = prospect.get("podcast_name", "").encode("ascii", "replace").decode()[:50]
        print(f"  Deep enriching {i + 1}/{len(call_ready)}: {safe_name}")

        # 1. Extract episode details from RSS
        rss_url = prospect.get("rss_url", "")
        episode_details, episode_titles = extract_episode_details(rss_url) if rss_url else ([], [])
        prospect["episode_details"] = episode_details

        # 2. Scrape company homepage
        domain = prospect.get("domain", "")
        raw_company = scrape_company_text(domain) if domain else ""
        if not raw_company:
            scraped_fail += 1

        # 3. Call Ollama for theme + company summary
        episode_descriptions = [ep.get("description", "") for ep in episode_details]
        result = call_ollama_deep(episode_titles, episode_descriptions, raw_company)

        if result:
            prospect["podcast_themes"] = result.podcast_themes
            prospect["company_summary"] = result.company_summary
        else:
            llm_fail += 1
            prospect["podcast_themes"] = None
            prospect["company_summary"] = raw_company[:300] if raw_company else None

    print(f"  Deep enrich complete: {len(call_ready)} processed, {scraped_fail} scrape failures, {llm_fail} LLM failures")

    return call_ready + others


if __name__ == "__main__":
    import glob

    # Minimal test: load scored prospects from JSON if available
    score_files = glob.glob(os.path.join(os.path.dirname(__file__), "..", "data", "score.json"))
    if score_files:
        with open(score_files[0], "r", encoding="utf-8") as f:
            prospects = json.load(f)
        call_ready = [p for p in prospects if p.get("status") == "call-ready"][:2]
        if call_ready:
            print(f"Testing deep enrichment on {len(call_ready)} prospects...")
            enriched = deep_enrich_prospects(call_ready)
            for p in enriched:
                print(f"\n--- {p.get('podcast_name', 'unknown')} ---")
                print(f"  Themes: {p.get('podcast_themes', 'N/A')}")
                print(f"  Company: {p.get('company_summary', 'N/A')}")
                print(f"  Episodes: {len(p.get('episode_details', []))}")
        else:
            print("No call-ready prospects found in score.json")
    else:
        print("No score.json found. Run the pipeline first to generate scored prospects.")
