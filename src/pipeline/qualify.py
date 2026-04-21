"""AI qualification step: classifies prospects via LLM (Ollama) with heuristic fallback."""

import json
import os

import ollama
from pydantic import BaseModel

from pipeline.enrich import is_hosting_platform, looks_like_person_name, split_name
from pipeline.models import ProspectDict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompts", "qualify.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CONFIG = load_config()


class QualifyResponse(BaseModel):
    is_person: bool
    first_name: str
    last_name: str
    language: str
    is_hosting_domain: bool


def call_ollama(host_name: str, podcast_name: str, domain: str) -> QualifyResponse | None:
    user_msg = json.dumps({
        "host_name": host_name,
        "podcast_name": podcast_name,
        "domain": domain,
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
        return QualifyResponse(**parsed)
    except Exception:
        return None


def heuristic_fallback(host_name: str, domain: str) -> QualifyResponse:
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

    retries = CONFIG.get("max_retries", 1)
    attempts = 0
    while result is None and attempts < retries:
        result = call_ollama(host_name, podcast_name, domain)
        attempts += 1

    if result is None:
        result = heuristic_fallback(host_name, domain)
        used_fallback = True
        safe_name = podcast_name.encode("ascii", "replace").decode()
        print(f"  Warning: Ollama failed for '{safe_name}', using heuristic fallback")

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
    total = len(prospects)
    counts = {"qualified": 0, "disqualified": 0, "existing_riverside_customer": 0}
    reasons = {}
    fallback_count = 0

    print(f"  Using model: {CONFIG['model']} (temperature={CONFIG['temperature']}, max_retries={CONFIG.get('max_retries', 1)})")

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

    print(f"\n  Qualification complete:")
    print(f"    Qualified:          {counts.get('qualified', 0)}")
    print(f"    Disqualified:       {counts.get('disqualified', 0)}")
    for reason, count in sorted(reasons.items()):
        print(f"      - {reason}: {count}")
    print(f"    Riverside customers: {counts.get('existing_riverside_customer', 0)}")
    if fallback_count > 0:
        print(f"    Heuristic fallbacks: {fallback_count}")

    return prospects
