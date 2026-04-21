"""AI qualification step: classifies prospects via Gemma 3 4B (Ollama) with heuristic fallback."""

import json

import ollama
from pydantic import BaseModel

from pipeline.enrich import is_hosting_platform, looks_like_person_name, split_name
from pipeline.models import ProspectDict


class QualifyResponse(BaseModel):
    is_person: bool
    first_name: str
    last_name: str
    language: str
    is_hosting_domain: bool


SYSTEM_PROMPT = (
    "You classify podcast prospects. Given host_name, podcast_name, and domain, determine:\n"
    "1. Whether host_name is a real person (not an org name, show name, or multiple people).\n"
    "2. Extract first_name and last_name from host_name (best effort, empty string if unclear).\n"
    "3. The primary language of podcast_name (return ISO 639-1 two-letter code, default 'en').\n"
    "4. Whether domain is a podcast hosting platform (not the podcast's own website).\n"
    "Return ONLY valid JSON matching this schema: "
    '{"is_person": bool, "first_name": str, "last_name": str, "language": str, "is_hosting_domain": bool}. '
    "No markdown, no explanation."
)


def call_ollama(host_name: str, podcast_name: str, domain: str) -> QualifyResponse | None:
    """Call Gemma 3 4B via Ollama to classify a prospect. Returns None on any failure."""
    user_msg = json.dumps({
        "host_name": host_name,
        "podcast_name": podcast_name,
        "domain": domain,
    })
    try:
        response = ollama.chat(
            model="gemma3:4b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            format="json",
            options={"temperature": 0},
        )
        parsed = json.loads(response["message"]["content"])
        return QualifyResponse(**parsed)
    except Exception:
        return None


def heuristic_fallback(host_name: str, domain: str) -> QualifyResponse:
    """Fall back to rule-based classification when Ollama is unavailable."""
    is_person = looks_like_person_name(host_name)
    first_name, last_name = split_name(host_name) if is_person else ("", "")
    is_hosting = is_hosting_platform(domain)
    return QualifyResponse(
        is_person=is_person,
        first_name=first_name,
        last_name=last_name,
        language="en",
        is_hosting_domain=is_hosting,
    )


def qualify_prospect(prospect: ProspectDict) -> tuple[ProspectDict, bool]:
    """Classify a single prospect and set qualification fields.

    Returns (prospect, used_fallback) tuple.
    """
    rss_url = prospect.get("rss_url", "").lower()
    if "riverside.fm" in rss_url:
        prospect["qualification_status"] = "existing_riverside_customer"
        prospect["disqualify_reason"] = "existing_riverside_customer"
        return prospect, False

    host_name = prospect.get("host_name", "")
    podcast_name = prospect.get("podcast_name", "")
    domain = prospect.get("domain", "")

    result = call_ollama(host_name, podcast_name, domain)
    used_fallback = False

    if result is None:
        # One retry
        result = call_ollama(host_name, podcast_name, domain)

    if result is None:
        result = heuristic_fallback(host_name, domain)
        used_fallback = True
        safe_name = podcast_name.encode("ascii", "replace").decode()
        print(f"  Warning: Ollama failed for '{safe_name}', using heuristic fallback")

    # Apply qualification logic
    if not result.is_person:
        prospect["qualification_status"] = "disqualified"
        prospect["disqualify_reason"] = "org_not_person"
    elif result.language != "en":
        prospect["qualification_status"] = "disqualified"
        prospect["disqualify_reason"] = "non_english"
    elif result.is_hosting_domain:
        prospect["qualification_status"] = "disqualified"
        prospect["disqualify_reason"] = "hosting_domain"
    else:
        prospect["qualification_status"] = "qualified"
        prospect["disqualify_reason"] = None

    prospect["first_name"] = result.first_name
    prospect["last_name"] = result.last_name
    prospect["language"] = result.language

    return prospect, used_fallback


def qualify_prospects(prospects: list[ProspectDict]) -> list[ProspectDict]:
    """Public entry point. Qualifies all prospects, prints progress and summary."""
    total = len(prospects)
    counts = {"qualified": 0, "disqualified": 0, "existing_riverside_customer": 0}
    reasons = {}
    fallback_count = 0

    for i, prospect in enumerate(prospects):
        prospect, used_fallback = qualify_prospect(prospect)
        if used_fallback:
            fallback_count += 1

        status = prospect.get("qualification_status", "unknown")
        counts[status] = counts.get(status, 0) + 1

        if status == "disqualified":
            reason = prospect.get("disqualify_reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

        if (i + 1) % 10 == 0:
            print(f"  Qualifying... {i + 1}/{total}")

    # Print summary
    print(f"\n  Qualification complete:")
    print(f"    Qualified:          {counts.get('qualified', 0)}")
    print(f"    Disqualified:       {counts.get('disqualified', 0)}")
    for reason, count in sorted(reasons.items()):
        print(f"      - {reason}: {count}")
    print(f"    Riverside customers: {counts.get('existing_riverside_customer', 0)}")
    if fallback_count > 0:
        print(f"    Heuristic fallbacks: {fallback_count}")

    return prospects
