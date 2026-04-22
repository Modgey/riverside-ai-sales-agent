import json
import os

from dotenv import load_dotenv
from pyairtable import Api

from pipeline.models import ProspectDict

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


def prospect_to_airtable_fields(prospect: ProspectDict) -> dict:
    fields = {
        "podcast_name": prospect.get("podcast_name", ""),
        "host_name": prospect.get("host_name", ""),
        "company_name": prospect.get("company_name", ""),
        "company_size": prospect.get("company_size"),
        "work_email": prospect.get("work_email", ""),
        "industry": prospect.get("industry", ""),
        "episode_cadence": round(prospect["cadence_days"]) if prospect.get("cadence_days") else None,
        "recent_episode_topic": prospect.get("recent_episode_topic", ""),
        "score": prospect.get("score", 0),
        "status": prospect.get("status", ""),
        "domain": prospect.get("domain", ""),
        "episode_count": prospect.get("episode_count"),
        "enrichment_status": prospect.get("enrichment_status", ""),
        "disqualify_reason": prospect.get("disqualify_reason", ""),
        "has_video": prospect.get("has_video", False),
        "episode_details": json.dumps(prospect.get("episode_details", []), ensure_ascii=False)[:10000],
        "company_summary": prospect.get("company_summary", "") or "",
        "podcast_themes": prospect.get("podcast_themes", "") or "",
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
