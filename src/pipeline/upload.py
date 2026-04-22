import json
import os

from dotenv import load_dotenv
from pyairtable import Api

from pipeline.models import ProspectDict

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


def prospect_to_airtable_fields(prospect: ProspectDict) -> dict:
    categories = prospect.get("categories", {})
    categories_str = ", ".join(categories.values()) if isinstance(categories, dict) else ""

    fields = {
        "podcast_name": prospect.get("podcast_name", ""),
        "first_name": prospect.get("first_name", ""),
        "last_name": prospect.get("last_name", ""),
        "company_name": prospect.get("company_name", ""),
        "company_size": prospect.get("company_size"),
        "title": prospect.get("title", ""),
        "work_email": prospect.get("work_email", ""),
        "industry": prospect.get("industry", ""),
        "episode_cadence": round(prospect["cadence_days"]) if prospect.get("cadence_days") else None,
        "recent_episode_topic": prospect.get("recent_episode_topic", ""),
        "score": prospect.get("score", 0),
        "status": prospect.get("status", ""),
        "qualification_status": prospect.get("qualification_status", ""),
        "domain": prospect.get("domain", ""),
        "episode_count": prospect.get("episode_count"),
        "language": prospect.get("language", ""),
        "categories": categories_str,
        "last_publish_time": prospect.get("last_publish_time"),
        "enrichment_status": prospect.get("enrichment_status", ""),
        "disqualify_reason": prospect.get("disqualify_reason", ""),
        "has_video": prospect.get("has_video", False),
        "phone_number": prospect.get("phone_number", ""),
        "episode_details": json.dumps(prospect.get("episode_details", []), ensure_ascii=False)[:10000],
        "podcast_profile": prospect.get("podcast_profile", "") or "",
        "company_profile": prospect.get("company_profile", "") or "",
        "production_signals": prospect.get("production_signals", "") or "",
        "call_context": prospect.get("call_context", "") or "",
    }
    return {k: v for k, v in fields.items() if v is not None}


def upload_to_airtable(prospects: list[ProspectDict]) -> dict:
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.table(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_PROSPECTS_TABLE_ID"))

    records = [{"fields": prospect_to_airtable_fields(p)} for p in prospects]
    result = table.batch_upsert(records, key_fields=["podcast_name"])

    created = len(result.get("createdRecords", []))
    updated = len(result.get("updatedRecords", []))
    print(f"  Upload complete: {len(prospects)} prospects written to Airtable ({created} created, {updated} updated)")
    return result


if __name__ == "__main__":
    test_record: ProspectDict = {
        "podcast_name": "_pipeline_test_record",
        "host_name": "Test",
        "domain": "test.example.com",
        "score": 0,
        "status": "disqualified",
        "enrichment_status": "test",
    }
    upload_to_airtable([test_record])
    print("  Test upload complete. Delete '_pipeline_test_record' from Airtable manually.")
