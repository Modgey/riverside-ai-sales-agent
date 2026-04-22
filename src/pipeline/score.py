import json
import os

from pipeline.models import ProspectDict

B2B_CATEGORIES = {"Business", "Technology", "Marketing", "Entrepreneurship", "Management"}


def size_fit_score(size: int | None) -> float:
    if size is None:
        return 0
    if 100 <= size <= 1000:
        return 40
    if 50 <= size < 100 or 1000 < size <= 2000:
        return 20
    return 0


def cadence_fit_score(cadence_days: float) -> float:
    if cadence_days <= 7:
        return 30
    if cadence_days <= 16:
        return 25
    if cadence_days <= 35:
        return 15
    return 5


def data_completeness_score(prospect: ProspectDict) -> float:
    fields = ["work_email", "host_name", "company_name", "company_size", "recent_episode_topic"]
    present = sum(1 for f in fields if prospect.get(f))
    return round((present / 5) * 20)


def category_match_score(prospect: ProspectDict) -> float:
    categories = prospect.get("categories", {}) or {}
    if any(v in B2B_CATEGORIES for v in categories.values()):
        return 10
    return 0


def score_and_filter(
    prospects: list[ProspectDict],
    skip_list_path: str = "skip_list.json",
) -> list[ProspectDict]:
    with open(skip_list_path) as f:
        skip_list = json.load(f)

    skip_domains = {entry["domain"].lower() for entry in skip_list}
    skip_names = {entry["name"].lower() for entry in skip_list}

    call_ready = 0
    below_threshold = 0
    disqualified = 0
    skipped = 0

    for prospect in prospects:
        domain = prospect.get("domain", "").lower()
        company = prospect.get("company_name", "").lower()

        if domain in skip_domains or company in skip_names:
            prospect["status"] = "skipped"
            prospect["score"] = 0
            skipped += 1
            continue

        if prospect.get("enrichment_status") == "enrichment-failed":
            prospect["status"] = "disqualified"
            prospect["disqualify_reason"] = "enrichment_failed"
            prospect["score"] = 0
            disqualified += 1
            continue

        cadence = prospect.get("cadence_days")
        if cadence is None or cadence > 90:
            prospect["status"] = "disqualified"
            prospect["disqualify_reason"] = "inactive_or_infrequent_show"
            prospect["score"] = 0
            disqualified += 1
            continue

        email = prospect.get("work_email")
        if not email:
            prospect["status"] = "disqualified"
            prospect["disqualify_reason"] = "no_contact_info"
            prospect["score"] = 0
            disqualified += 1
            continue

        total = (
            size_fit_score(prospect.get("company_size"))
            + cadence_fit_score(cadence)
            + data_completeness_score(prospect)
            + category_match_score(prospect)
        )
        prospect["score"] = round(total)

        if total >= 40:
            prospect["status"] = "call-ready"
            call_ready += 1
        else:
            prospect["status"] = "below-threshold"
            below_threshold += 1

    print(f"  Scoring complete: {call_ready} call-ready, {below_threshold} below-threshold, {disqualified} disqualified, {skipped} skipped")
    return prospects


if __name__ == "__main__":
    samples: list[ProspectDict] = [
        {"podcast_name": "Great SaaS Show", "host_name": "Jane Doe", "domain": "example.com",
         "work_email": "jane@example.com", "company_size": 500, "company_name": "ExampleCo",
         "industry": "SaaS", "cadence_days": 7.0, "recent_episode_topic": "Growth Hacks",
         "episode_count": 200, "categories": {"77": "Business"}, "enrichment_status": "enriched",
         "last_publish_time": 0},
        {"podcast_name": "Edge Case Pod", "host_name": "Bob Smith", "domain": "edgy.io",
         "work_email": "bob@edgy.io", "company_size": 80, "company_name": "Edgy Inc",
         "industry": "Tech", "cadence_days": 30.0, "recent_episode_topic": "Scaling",
         "episode_count": 50, "categories": {}, "enrichment_status": "enriched",
         "last_publish_time": 0},
        {"podcast_name": "Too Big Corp", "host_name": "Alice", "domain": "mega.com",
         "work_email": "alice@mega.com", "company_size": 5000, "company_name": "MegaCorp",
         "industry": "Enterprise", "cadence_days": 7.0, "recent_episode_topic": "Scale",
         "episode_count": 100, "categories": {}, "enrichment_status": "enriched",
         "last_publish_time": 0},
        {"podcast_name": "No Email Show", "host_name": "Charlie", "domain": "nomail.com",
         "work_email": None, "company_size": 200, "company_name": "NoMail Inc",
         "industry": "Tech", "cadence_days": 14.0, "recent_episode_topic": "Tips",
         "episode_count": 30, "categories": {}, "enrichment_status": "enriched",
         "last_publish_time": 0},
        {"podcast_name": "Riverside Show", "host_name": "River", "domain": "riverside.fm",
         "work_email": "river@riverside.fm", "company_size": 300, "company_name": "Riverside.fm",
         "industry": "Media", "cadence_days": 7.0, "recent_episode_topic": "Recording",
         "episode_count": 150, "categories": {"77": "Business"}, "enrichment_status": "enriched",
         "last_publish_time": 0},
    ]

    skip_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skip_list.json")
    results = score_and_filter(samples, skip_list_path=skip_path)
    for r in results:
        print(f"  {r['podcast_name']}: status={r['status']}, score={r['score']}, reason={r.get('disqualify_reason', 'n/a')}")
