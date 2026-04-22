import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
import podcastindex
from dotenv import load_dotenv

from pipeline.enrich import is_hosting_platform, looks_like_person_name
from pipeline.models import ProspectDict

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

ICP_CATEGORIES = {"Business", "Technology", "Marketing", "Entrepreneurship", "Management"}

DEFAULT_SEARCH_TERMS = [
    "B2B SaaS",
    "SaaS founder",
    "demand generation",
    "revenue operations",
    "marketing agency",
    "venture capital",
    "startup founders",
    "cybersecurity",
    "fintech",
    "healthtech",
    "ecommerce DTC",
    "creator economy",
]


def detect_video_podcast(feed) -> bool:
    """Check RSS feed for video podcast signals (enclosures, YouTube links, title keywords)."""
    entries = feed.entries[:10]

    for entry in entries:
        # Signal 1: Video enclosure MIME type
        for enc in entry.get("enclosures", []):
            if enc.get("type", "").startswith("video/"):
                return True

        # Signal 3: Episode title keywords
        title = entry.get("title", "")
        if re.search(r'\b(video|watch|youtube|clips)\b', title, re.IGNORECASE):
            return True

        # Signal 4: YouTube links in description/content
        summary = entry.get("summary", "")
        content_list = entry.get("content", [{}])
        content_val = content_list[0].get("value", "") if content_list else ""
        combined = summary + content_val
        if "youtube.com" in combined or "youtu.be" in combined:
            return True

        # Signal 2 (entry-level): YouTube in entry links
        for link in entry.get("links", []):
            href = link.get("href", "")
            if "youtube.com" in href or "youtu.be" in href:
                return True

    # Signal 2 (feed-level): YouTube in feed links
    for link in feed.feed.get("links", []):
        href = link.get("href", "")
        if "youtube.com" in href or "youtu.be" in href:
            return True

    return False


def parse_rss(rss_url: str) -> dict | None:
    try:
        feed = feedparser.parse(rss_url)
    except Exception:
        return None

    if not feed.feed:
        return None

    host_name = (
        feed.feed.get("itunes_author")
        or feed.feed.get("author")
        or feed.feed.get("title", "Unknown")
    )

    podcast_name = feed.feed.get("title", "")
    entries = feed.entries[:10]

    pub_dates = []
    for entry in entries:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_dates.append(datetime(*entry.published_parsed[:6], tzinfo=timezone.utc))

    cadence_days = None
    if len(pub_dates) >= 2:
        deltas = [(pub_dates[i] - pub_dates[i + 1]).days for i in range(len(pub_dates) - 1)]
        cadence_days = sum(deltas) / len(deltas) if deltas else None

    recent_episode_topic = entries[0].get("title", "") if entries else ""
    episode_count = len(feed.entries)

    link = feed.feed.get("link", rss_url)
    domain = urlparse(link).netloc or urlparse(rss_url).netloc

    return {
        "host_name": host_name,
        "podcast_name": podcast_name,
        "cadence_days": cadence_days,
        "recent_episode_topic": recent_episode_topic,
        "episode_count": episode_count,
        "domain": domain,
        "has_video": detect_video_podcast(feed),
    }


def discover_prospects(keywords: list[str] | None = None, max_per_term: int = 50) -> list[ProspectDict]:
    config = {
        "api_key": os.getenv("PODCAST_INDEX_API_KEY"),
        "api_secret": os.getenv("PODCAST_INDEX_API_SECRET"),
    }
    index = podcastindex.init(config)

    search_terms = keywords or DEFAULT_SEARCH_TERMS
    all_feeds = []
    seen = set()

    for term in search_terms:
        try:
            results = index.search(term, clean=False)
        except Exception as e:
            print(f"  Warning: search for '{term}' failed ({e}), skipping")
            continue

        feeds = results.get("feeds", [])
        count = 0
        for feed in feeds:
            url = feed.get("url", "")
            if url and url not in seen and count < max_per_term:
                seen.add(url)
                all_feeds.append(feed)
                count += 1
        print(f"  Searching '{term}'... found {len(feeds)} feeds ({count} new)")

    print(f"  Discovery: {len(all_feeds)} unique feeds collected")

    cutoff = time.time() - (90 * 24 * 60 * 60)
    active = [f for f in all_feeds if f.get("lastUpdateTime", 0) > cutoff]
    print(f"  Recency filter: {len(all_feeds)} -> {len(active)} feeds (dropped {len(all_feeds) - len(active)} inactive)")

    before_cat = len(active)
    filtered = []
    for feed in active:
        categories = feed.get("categories", {}) or {}
        if not categories or any(v in ICP_CATEGORIES for v in categories.values()):
            filtered.append(feed)
    print(f"  Category filter: {before_cat} -> {len(filtered)} feeds (dropped {before_cat - len(filtered)} off-ICP)")

    rss_urls = [f.get("url", "") for f in filtered]
    feed_by_url = {f.get("url", ""): f for f in filtered}

    print(f"  Parsing {len(rss_urls)} RSS feeds (parallel)...")
    parsed_results: dict[str, dict | None] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(parse_rss, url): url for url in rss_urls if url}
        done = 0
        for future in as_completed(futures):
            url = futures[future]
            parsed_results[url] = future.result()
            done += 1
            if done % 50 == 0:
                print(f"  Parsed {done}/{len(futures)} feeds...")

    seen_domains: set[str] = set()
    prospects: list[ProspectDict] = []
    for feed in filtered:
        rss_url = feed.get("url", "")
        parsed = parsed_results.get(rss_url)
        if not parsed:
            continue

        domain_key = parsed["domain"].lower().removeprefix("www.")
        if domain_key in seen_domains:
            continue
        if is_hosting_platform(parsed["domain"]):
            continue
        if not looks_like_person_name(parsed["host_name"]):
            continue
        seen_domains.add(domain_key)

        prospect: ProspectDict = {
            "podcast_name": parsed["podcast_name"],
            "host_name": parsed["host_name"],
            "rss_url": rss_url,
            "domain": parsed["domain"],
            "cadence_days": parsed["cadence_days"],
            "recent_episode_topic": parsed["recent_episode_topic"],
            "episode_count": parsed["episode_count"],
            "categories": feed.get("categories", {}),
            "last_publish_time": feed.get("lastUpdateTime", 0),
            "has_video": parsed.get("has_video", False),
        }
        prospects.append(prospect)

    print(f"  Discovery complete: {len(seen)} unique feeds, {len(active)} active, {len(prospects)} parsed successfully")
    return prospects


if __name__ == "__main__":
    results = discover_prospects()
    print(f"\nTotal prospects: {len(results)}")
    for p in results[:3]:
        print(f"  {p['podcast_name']} | {p['host_name']} | cadence={p.get('cadence_days')} days")
