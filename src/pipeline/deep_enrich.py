"""Deep enrichment: RSS episode details, company scraping, and LLM profile generation."""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic import BaseModel

from pipeline.models import ProspectDict

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompts", "deep_enrich.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CONFIG = load_config()


class DeepEnrichResponse(BaseModel):
    podcast_profile: str
    company_profile: str
    production_signals: str


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


def extract_episode_details(rss_url: str) -> tuple[list[dict], list[str], str]:
    """Parse RSS feed for recent episode details, broader title list, and feed description.

    Returns:
        Tuple of (episode_details for top 5, episode_titles for top 15, feed_description).
    """
    # Stream and cap at 2MB to avoid pulling massive feeds
    try:
        resp = requests.get(rss_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}, stream=True)
        resp.raise_for_status()
        chunks = []
        size = 0
        for chunk in resp.iter_content(8192):
            chunks.append(chunk)
            size += len(chunk)
            if size > 2_000_000:
                break
        feed = feedparser.parse(b"".join(chunks))
    except Exception:
        return [], [], ""
    entries = feed.entries

    feed_desc = ""
    if hasattr(feed, "feed"):
        feed_desc = feed.feed.get("subtitle", "") or feed.feed.get("description", "") or ""
        feed_desc = clean_description(feed_desc, max_chars=800)

    episode_details = []
    for entry in entries[:5]:
        raw_desc = entry.get("summary", "") or entry.get("description", "")

        video_urls = []
        for enc in entry.get("enclosures", []):
            if enc.get("type", "").startswith("video/"):
                video_urls.append(enc.get("href", ""))
        for link in entry.get("links", []):
            href = link.get("href", "")
            if "youtube.com" in href or "youtu.be" in href:
                video_urls.append(href)
        for url_match in re.findall(r'https?://(?:www\.)?(?:youtube\.com/watch\S+|youtu\.be/\S+)', raw_desc):
            video_urls.append(url_match)

        episode_details.append({
            "title": entry.get("title", ""),
            "description": clean_description(raw_desc, max_chars=800),
            "guest_name": extract_guest_name(entry),
            "published": entry.get("published", ""),
            "video_url": video_urls[0] if video_urls else None,
        })

    episode_titles = [e.get("title", "") for e in entries[:15]]

    return episode_details, episode_titles, feed_desc


def scrape_company_text(domain: str) -> str:
    """Grab meta description from homepage. Fast, single request.

    Returns empty string on any failure (prospect stays call-ready per D-06).
    """
    try:
        resp = requests.get(
            f"https://{domain}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=3,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")

        for tag in [
            soup.find("meta", property="og:description"),
            soup.find("meta", attrs={"name": "description"}),
        ]:
            if tag and tag.get("content", "").strip():
                return tag["content"].strip()[:500]

    except Exception:
        pass

    return ""


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm_deep(
    episode_titles: list[str],
    episode_details: list[dict],
    feed_description: str,
    raw_company_text: str,
) -> DeepEnrichResponse | None:
    """Call OpenRouter for podcast profile, company profile, and production signals.

    Returns None on any failure (same pattern as qualify.py).
    """
    user_msg = json.dumps({
        "feed_description": feed_description,
        "episode_titles": episode_titles[:15],
        "recent_episodes": [
            {
                "title": ep.get("title", ""),
                "description": ep.get("description", ""),
                "guest_name": ep.get("guest_name"),
                "has_video": bool(ep.get("video_url")),
            }
            for ep in episode_details[:5]
        ],
        "company_homepage_text": raw_company_text[:1200],
    })

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "model": CONFIG["model"],
                "temperature": CONFIG["temperature"],
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": CONFIG["system_prompt"]},
                    {"role": "user", "content": user_msg},
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return DeepEnrichResponse(**parsed)
    except Exception:
        return None


def _enrich_one(prospect: ProspectDict) -> ProspectDict:
    """Enrich a single prospect (designed to run in a thread)."""
    rss_url = prospect.get("rss_url", "")
    if rss_url:
        episode_details, episode_titles, feed_desc = extract_episode_details(rss_url)
    else:
        episode_details, episode_titles, feed_desc = [], [], ""
    prospect["episode_details"] = episode_details

    domain = prospect.get("domain", "")
    raw_company = scrape_company_text(domain) if domain else ""

    result = call_llm_deep(episode_titles, episode_details, feed_desc, raw_company)

    if result:
        prospect["podcast_profile"] = result.podcast_profile
        prospect["company_profile"] = result.company_profile
        prospect["production_signals"] = result.production_signals
    else:
        prospect["podcast_profile"] = None
        prospect["company_profile"] = raw_company[:500] if raw_company else None
        prospect["production_signals"] = None

    return prospect


def deep_enrich_prospects(prospects: list[ProspectDict], workers: int = 4) -> list[ProspectDict]:
    """Deep enrich Qualified prospects in parallel."""
    call_ready = [p for p in prospects if p.get("status") == "Qualified"]
    others = [p for p in prospects if p.get("status") != "Qualified"]

    print(f"  Deep enriching {len(call_ready)} Qualified prospects ({len(others)} others skipped, {workers} workers)")

    enriched = []
    done = 0
    llm_fail = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_enrich_one, p): p for p in call_ready}
        for future in as_completed(futures):
            done += 1
            p = future.result()
            enriched.append(p)
            safe_name = p.get("podcast_name", "").encode("ascii", "replace").decode()[:50]
            status = "ok" if p.get("podcast_profile") else "LLM failed"
            if status != "ok":
                llm_fail += 1
            print(f"  [{done}/{len(call_ready)}] {safe_name} - {status}")

    print(f"  Deep enrich complete: {len(call_ready)} processed, {llm_fail} LLM failures")

    return enriched + others


if __name__ == "__main__":
    import glob

    # Minimal test: load scored prospects from JSON if available
    score_files = glob.glob(os.path.join(os.path.dirname(__file__), "..", "data", "score.json"))
    if score_files:
        with open(score_files[0], "r", encoding="utf-8") as f:
            prospects = json.load(f)
        call_ready = [p for p in prospects if p.get("status") == "Qualified"][:2]
        if call_ready:
            print(f"Testing deep enrichment on {len(call_ready)} prospects...")
            enriched = deep_enrich_prospects(call_ready)
            for p in enriched:
                print(f"\n--- {p.get('podcast_name', 'unknown')} ---")
                print(f"  Profile: {p.get('podcast_profile', 'N/A')}")
                print(f"  Company: {p.get('company_profile', 'N/A')}")
                print(f"  Signals: {p.get('production_signals', 'N/A')}")
                print(f"  Episodes: {len(p.get('episode_details', []))}")
        else:
            print("No Qualified prospects found in score.json")
    else:
        print("No score.json found. Run the pipeline first to generate scored prospects.")
