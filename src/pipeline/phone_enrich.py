import os
import time

import requests
from dotenv import load_dotenv

from pipeline.models import ProspectDict

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

DATAGMA_URL = "https://gateway.datagma.net/api/ingress/v2/full"
PHONE_ENRICHMENT_LIMIT = 3 #Low limit for this demo


def enrich_phone_via_datagma(full_name: str, domain: str, api_key: str) -> str | None:
    params = {
        "apiId": api_key,
        "fullName": full_name,
        "data": domain,
        "phoneFull": "true",
    }
    try:
        resp = requests.get(DATAGMA_URL, params=params, timeout=20)
    except requests.RequestException as e:
        print(f"    Request failed: {e}")
        return None

    if resp.status_code != 200:
        print(f"    API returned {resp.status_code}")
        return None

    data = resp.json()

    for key in ("phoneNumber", "phone_number", "mobilePhone", "mobile_phone", "phone", "directPhone"):
        if data.get(key):
            return data[key]

    person = data.get("data", {})
    if isinstance(person, dict):
        for key in ("phoneNumber", "phone_number", "mobilePhone", "mobile_phone", "phone", "directPhone"):
            if person.get(key):
                return person[key]

    print(f"    No phone found in response. Top-level keys: {list(data.keys())[:10]}")
    return None


def phone_enrich_prospects(prospects: list[ProspectDict]) -> list[ProspectDict]:
    api_key = os.getenv("DATAGMA_API_KEY")
    if not api_key:
        print("  Warning: DATAGMA_API_KEY not set. Skipping phone enrichment.")
        return prospects

    qualified = sorted(
        [p for p in prospects if p.get("status") == "Qualified"],
        key=lambda p: p.get("score", 0),
        reverse=True,
    )

    candidates = qualified[:PHONE_ENRICHMENT_LIMIT]
    print(f"  Enriching top {len(candidates)} qualified prospects with phone numbers...\n")

    found = 0
    for p in candidates:
        full_name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        domain = p.get("domain", "")
        if not full_name or not domain:
            print(f"    Skipping {p.get('podcast_name')}: missing name or domain")
            continue

        print(f"    Looking up {full_name} @ {domain}...")
        phone = enrich_phone_via_datagma(full_name, domain, api_key)
        if phone:
            p["phone_number"] = phone
            print(f"    Found: {phone}")
            found += 1
        else:
            print(f"    No number found")

        time.sleep(1)

    print(f"\n  Phone enrichment complete: {found}/{len(candidates)} numbers found")
    return prospects


if __name__ == "__main__":
    test: ProspectDict = {
        "podcast_name": "Test",
        "first_name": "Brian",
        "last_name": "Halligan",
        "domain": "hubspot.com",
        "status": "Qualified",
        "score": 90,
    }
    result = phone_enrich_prospects([test])
    print(f"  Phone: {result[0].get('phone_number', 'not found')}")
