import os
import time

import requests
from dotenv import load_dotenv

from pipeline.models import ProspectDict

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

HUNTER_EMAIL_FINDER_URL = "https://api.hunter.io/v2/email-finder"
HUNTER_COMPANY_URL = "https://api.hunter.io/v2/company-enrichment"

HOSTING_PLATFORM_DOMAINS = {
    "anchor.fm",
    "podcasters.spotify.com",
    "spotify.com",
    "buzzsprout.com",
    "www.buzzsprout.com",
    "sites.libsyn.com",
    "libsyn.com",
    "rss.com",
    "podbean.com",
    "transistor.fm",
    "simplecast.com",
    "megaphone.fm",
    "omnystudio.com",
    "spreaker.com",
    "captivate.fm",
    "fireside.fm",
    "blubrry.com",
    "podigee.io",
    "art19.com",
    "acast.com",
    "shows.acast.com",
    "podcast.ausha.co",
    "open.firstory.me",
    "redcircle.com",
    "www.facebook.com",
    "facebook.com",
    "www.youtube.com",
    "youtube.com",
    "substack.com",
    "podcasts.apple.com",
    "soundcloud.com",
    "podfollow.com",
    "linktr.ee",
    "casted.us",
    "repodcast.com",
    "ivoox.com",
    "podpage.com",
}

ENRICHMENT_CAP = 75


def is_hosting_platform(domain: str) -> bool:
    d = domain.lower().strip()
    if d in HOSTING_PLATFORM_DOMAINS:
        return True
    for platform in HOSTING_PLATFORM_DOMAINS:
        if d.endswith("." + platform):
            return True
    return False


NON_PERSON_WORDS = {
    "podcast", "podcasts", "show", "radio", "network", "media", "studio",
    "studios", "productions", "llc", "inc", "ltd", "corp", "company",
    "group", "team", "daily", "weekly", "exchange", "metals", "money",
    "marketing", "digital", "startup", "life", "the",
    "agency", "capital", "solutions", "ventures", "club", "university", "partners",
}


def looks_like_person_name(full_name: str) -> bool:
    cleaned = full_name.split("&")[0].split(",")[0].split("|")[0].split("-")[0].strip()
    parts = cleaned.lower().split()
    if len(parts) < 2 or len(parts) > 4:
        return False
    if any(w in NON_PERSON_WORDS for w in parts):
        return False
    if len(parts[0]) == 1:
        return False
    if all(c.islower() for c in cleaned if c.isalpha()):
        return False
    return True


def split_name(full_name: str) -> tuple[str, str]:
    cleaned = full_name.split("&")[0].split(",")[0].split("|")[0].split("-")[0].strip()
    parts = cleaned.split()
    if len(parts) == 0:
        return ("Unknown", "")
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], parts[-1])


def _hunter_get(url: str, params: dict, api_key: str) -> dict | str:
    params["api_key"] = api_key
    try:
        resp = requests.get(url, params=params, timeout=15)
    except requests.RequestException:
        return {}

    if resp.status_code in (401, 403):
        return "AUTH_ERROR"
    if resp.status_code == 429:
        return "RATE_LIMITED"
    if resp.status_code != 200:
        return {}

    return resp.json().get("data") or {}


def enrich_via_hunter(first_name: str, last_name: str, domain: str, api_key: str) -> dict | str:
    person = _hunter_get(
        HUNTER_EMAIL_FINDER_URL,
        {"first_name": first_name, "last_name": last_name, "domain": domain},
        api_key,
    )
    if isinstance(person, str):
        return person
    if not person:
        return {}

    verification = person.get("verification") or {}

    company = _hunter_get(HUNTER_COMPANY_URL, {"domain": domain}, api_key)
    if isinstance(company, str):
        company = {}

    employees_range = company.get("employees_range", "") if company else ""
    company_size = _parse_employees_range(employees_range)

    return {
        "work_email": person.get("email"),
        "email_status": verification.get("status"),
        "title": person.get("position"),
        "company_name": person.get("company") or (company.get("name") if company else None),
        "company_size": company_size,
        "industry": company.get("industry") if company else None,
    }


def _parse_employees_range(range_str: str) -> int | None:
    if not range_str:
        return None
    range_str = range_str.strip().replace(",", "").replace("+", "")
    parts = range_str.split("-")
    try:
        if len(parts) == 2:
            return (int(parts[0]) + int(parts[1])) // 2
        return int(parts[0])
    except ValueError:
        return None


def prioritize_prospects(prospects: list[ProspectDict]) -> tuple[list[ProspectDict], list[ProspectDict]]:
    enrichable = []
    skipped = []

    for p in prospects:
        if is_hosting_platform(p.get("domain", "")):
            p["enrichment_status"] = "enrichment-failed"
            p["disqualify_reason"] = "hosting_platform_domain"
            skipped.append(p)
        else:
            enrichable.append(p)

    enrichable.sort(key=lambda p: (
        p.get("episode_count", 0),
        1 if any(v in {"Business", "Technology", "Marketing", "Entrepreneurship"} for v in (p.get("categories") or {}).values()) else 0,
    ), reverse=True)

    print(f"  Filtered: {len(skipped)} hosting platforms removed, {len(enrichable)} enrichable prospects")

    if len(enrichable) > ENRICHMENT_CAP:
        overflow = enrichable[ENRICHMENT_CAP:]
        enrichable = enrichable[:ENRICHMENT_CAP]
        for p in overflow:
            p["enrichment_status"] = "enrichment-failed"
            p["disqualify_reason"] = "over_enrichment_cap"
            skipped.append(p)
        print(f"  Capped at {ENRICHMENT_CAP} prospects (sorted by episode count + category match)")

    return enrichable, skipped


def enrich_prospects(prospects: list[ProspectDict]) -> list[ProspectDict]:
    api_key = os.getenv("HUNTER_API_KEY")
    if not api_key:
        print("  Warning: HUNTER_API_KEY not set, marking all as enrichment-failed")
        for p in prospects:
            p["enrichment_status"] = "enrichment-failed"
        return prospects

    enrichable, skipped = prioritize_prospects(prospects)

    total = len(enrichable)
    enriched_count = 0
    failed_count = 0
    credits_dead = False

    for i, prospect in enumerate(enrichable):
        if credits_dead:
            prospect["enrichment_status"] = "enrichment-failed"
            failed_count += 1
            continue

        host_name = prospect.get("host_name", "")
        if not looks_like_person_name(host_name):
            prospect["enrichment_status"] = "enrichment-failed"
            prospect["disqualify_reason"] = "non_person_name"
            failed_count += 1
            continue

        first_name, last_name = split_name(host_name)
        domain = prospect.get("domain", "")

        result = enrich_via_hunter(first_name, last_name, domain, api_key)

        if result == "AUTH_ERROR":
            print(f"  Enrichment auth error at prospect {i+1}/{total}. Marking remaining as failed.")
            credits_dead = True
            prospect["enrichment_status"] = "enrichment-failed"
            failed_count += 1
            continue

        if result == "RATE_LIMITED":
            print(f"  Rate limited at prospect {i+1}/{total}. Waiting 30s then retrying...")
            time.sleep(30)
            result = enrich_via_hunter(first_name, last_name, domain, api_key)
            if result == "RATE_LIMITED":
                print(f"  Still rate limited. Waiting 60s then retrying once more...")
                time.sleep(60)
                result = enrich_via_hunter(first_name, last_name, domain, api_key)
            if result in ("AUTH_ERROR", "RATE_LIMITED"):
                print(f"  Enrichment unavailable after retries. Marking remaining as failed.")
                credits_dead = True
                prospect["enrichment_status"] = "enrichment-failed"
                failed_count += 1
                continue

        if isinstance(result, dict) and (result.get("work_email") or result.get("company_size")):
            for key, value in result.items():
                if value is not None and key != "email_status":
                    prospect[key] = value
            prospect["enrichment_status"] = "enriched"
            enriched_count += 1
        else:
            prospect["enrichment_status"] = "enrichment-failed"
            failed_count += 1
            name = prospect["podcast_name"].encode("ascii", "replace").decode()
            print(f"  No match: {name} ({domain})")

        if (i + 1) % 10 == 0:
            print(f"  Enriching... {i + 1}/{total} ({enriched_count} enriched so far)")

        time.sleep(1)

    all_prospects = enrichable + skipped
    skipped_count = len(skipped)
    print(f"  Enrichment complete: {enriched_count} enriched, {failed_count} failed, {skipped_count} filtered out")
    return all_prospects


if __name__ == "__main__":
    samples: list[ProspectDict] = [
        {"podcast_name": "Test HubSpot Show", "host_name": "Brian Halligan", "domain": "hubspot.com",
         "rss_url": "", "cadence_days": 7.0, "recent_episode_topic": "Growth", "episode_count": 100,
         "categories": {}, "last_publish_time": 0},
        {"podcast_name": "Test Drift Show", "host_name": "David Cancel", "domain": "drift.com",
         "rss_url": "", "cadence_days": 14.0, "recent_episode_topic": "Sales", "episode_count": 50,
         "categories": {}, "last_publish_time": 0},
    ]
    results = enrich_prospects(samples)
    for r in results:
        print(f"  {r['podcast_name']}: {r['enrichment_status']} | email={r.get('work_email')} | company={r.get('company_name')}")
