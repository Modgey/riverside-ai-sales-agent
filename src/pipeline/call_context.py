"""Call context generation: personalized call briefings from enrichment data."""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from pydantic import BaseModel

from pipeline.models import ProspectDict

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompts", "call_context.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CONFIG = load_config()


class CallContextResponse(BaseModel):
    opener: str
    prospect_context: str
    personalized_angles: list[str]


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm_context(prospect: ProspectDict) -> CallContextResponse | None:
    """Call OpenRouter to generate a personalized call briefing for a prospect.

    Returns None on any failure (graceful degradation).
    """
    user_msg = json.dumps({
        "podcast_name": prospect.get("podcast_name", ""),
        "host_name": prospect.get("host_name", ""),
        "first_name": prospect.get("first_name", ""),
        "title": prospect.get("title", ""),
        "company_name": prospect.get("company_name", ""),
        "company_size": prospect.get("company_size"),
        "industry": prospect.get("industry", ""),
        "recent_episode_topic": prospect.get("recent_episode_topic", ""),
        "episode_details": [
            {
                "title": ep.get("title", ""),
                "description": ep.get("description", ""),
                "guest_name": ep.get("guest_name"),
            }
            for ep in (prospect.get("episode_details") or [])[:5]
        ],
        "podcast_profile": prospect.get("podcast_profile", ""),
        "company_profile": prospect.get("company_profile", ""),
        "production_signals": prospect.get("production_signals", ""),
        "has_video": prospect.get("has_video", False),
        "domain": prospect.get("domain", ""),
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
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if not content:
            finish = data["choices"][0].get("finish_reason", "unknown")
            raise ValueError(f"Empty LLM response (finish_reason={finish})")
        parsed = json.loads(content)
        return CallContextResponse(**parsed)
    except Exception as e:
        print(f"    LLM error for {prospect.get('podcast_name', '?')}: {e}")
        return None


def _generate_one(prospect: ProspectDict) -> ProspectDict:
    """Generate call context for a single prospect (designed to run in a thread)."""
    result = call_llm_context(prospect)
    if result:
        prospect["call_context"] = json.dumps(result.model_dump(), ensure_ascii=False)
    else:
        prospect["call_context"] = None
    return prospect


def generate_call_context(prospects: list[ProspectDict], workers: int = 4) -> list[ProspectDict]:
    """Generate call context for Qualified prospects in parallel."""
    call_ready = [p for p in prospects if p.get("status") == "Qualified"]
    others = [p for p in prospects if p.get("status") != "Qualified"]

    print(f"  Generating call context for {len(call_ready)} Qualified prospects ({len(others)} others skipped, {workers} workers)")

    enriched = []
    done = 0
    llm_fail = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_generate_one, p): p for p in call_ready}
        for future in as_completed(futures):
            done += 1
            p = future.result()
            enriched.append(p)
            safe_name = p.get("podcast_name", "").encode("ascii", "replace").decode()[:50]
            status = "ok" if p.get("call_context") else "LLM failed"
            if status != "ok":
                llm_fail += 1
            print(f"  [{done}/{len(call_ready)}] {safe_name} - {status}")

    print(f"  Call context complete: {len(call_ready)} processed, {llm_fail} LLM failures")

    return enriched + others


if __name__ == "__main__":
    import glob

    # Load from phone_enrich.json or deep_enrich.json as fallback
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    phone_files = glob.glob(os.path.join(data_dir, "phone_enrich.json"))
    deep_files = glob.glob(os.path.join(data_dir, "deep_enrich.json"))

    source = phone_files[0] if phone_files else (deep_files[0] if deep_files else None)
    if source:
        with open(source, "r", encoding="utf-8") as f:
            prospects = json.load(f)
        call_ready = [p for p in prospects if p.get("status") == "Qualified"][:2]
        if call_ready:
            print(f"Testing call context generation on {len(call_ready)} prospects from {os.path.basename(source)}...")
            result = generate_call_context(call_ready)
            for p in result:
                print(f"\n--- {p.get('podcast_name', 'unknown')} ---")
                ctx = p.get("call_context")
                if ctx:
                    parsed = json.loads(ctx)
                    print(f"  Opener: {parsed.get('opener', 'N/A')}")
                    print(f"  Context: {parsed.get('prospect_context', 'N/A')}")
                    print(f"  Angles: {parsed.get('personalized_angles', [])}")
                else:
                    print("  No call context generated (LLM failed)")

            # Save output
            out_path = os.path.join(data_dir, "call_context.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nSaved to {out_path}")
        else:
            print("No Qualified prospects found.")
    else:
        print("No phone_enrich.json or deep_enrich.json found. Run the pipeline first.")
