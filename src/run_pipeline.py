import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from pipeline.discover import discover_prospects
from pipeline.qualify import qualify_prospects
from pipeline.enrich import enrich_prospects
from pipeline.score import score_and_filter
from pipeline.upload import upload_to_airtable
from pipeline.deep_enrich import deep_enrich_prospects

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STEPS = ["discover", "qualify", "enrich", "score", "deep_enrich", "upload"]


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save(step_name: str, prospects: list[dict]):
    ensure_data_dir()
    path = os.path.join(DATA_DIR, f"{step_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prospects, f, indent=2, ensure_ascii=False)
    print(f"  Saved: data/{step_name}.json ({len(prospects)} records)")


def load(step_name: str) -> list[dict]:
    path = os.path.join(DATA_DIR, f"{step_name}.json")
    if not os.path.exists(path):
        print(f"  Error: data/{step_name}.json not found. Run the previous step first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Loaded: data/{step_name}.json ({len(data)} records)")
    return data


def run_discover():
    print("\n[Stage 1/6] Discovery")
    print("-" * 40)
    print("  Searching Podcast Index for podcasts matching our ICP...")
    print("  Parsing RSS feeds to extract host names, domains, cadence...\n")
    raw = discover_prospects()
    save("discover", raw)
    print(f"\n  Done: {len(raw)} candidates discovered")
    return raw


def run_qualify():
    print("\n[Stage 2/6] Qualification (AI)")
    print("-" * 40)
    print("  Classifying each prospect with a local LLM (Ollama).")
    print("  Checking: is the host a real person? What language? Is the domain legit?\n")
    raw = load("discover")
    qualified = qualify_prospects(raw)
    save("qualified", qualified)
    q_count = sum(1 for p in qualified if p.get("qualification_status") == "qualified")
    dq_count = sum(1 for p in qualified if p.get("qualification_status") == "disqualified")
    rs_count = sum(1 for p in qualified if p.get("qualification_status") == "existing_riverside_customer")
    print(f"\n  Done: {q_count} qualified, {dq_count} disqualified, {rs_count} existing Riverside customers")
    print(f"  Only the {q_count} qualified prospects will be sent to enrichment.")
    return qualified


def run_enrich():
    print("\n[Stage 3/6] Enrichment")
    print("-" * 40)
    raw = load("qualified")
    qualified_only = [p for p in raw if p.get("qualification_status") == "qualified"]
    disqualified = [p for p in raw if p.get("qualification_status") != "qualified"]
    print(f"  Enriching {len(qualified_only)} qualified prospects via Prospeo API...")
    print(f"  ({len(disqualified)} disqualified prospects skipped, saving API credits)\n")
    enriched = enrich_prospects(qualified_only)
    all_prospects = enriched + disqualified
    save("enrich", all_prospects)
    enriched_ok = sum(1 for p in all_prospects if p.get("enrichment_status") == "enriched")
    enriched_fail = sum(1 for p in all_prospects if p.get("enrichment_status") == "enrichment-failed")
    print(f"\n  Done: {enriched_ok} enriched with email/company data, {enriched_fail} no match found")
    return all_prospects


def run_score():
    print("\n[Stage 4/6] Scoring")
    print("-" * 40)
    print("  Ranking prospects by episode count, cadence, category fit...\n")
    enriched = load("enrich")
    scored = score_and_filter(enriched, skip_list_path=os.path.join(os.path.dirname(__file__), "skip_list.json"))
    save("score", scored)
    call_ready = sum(1 for p in scored if p["status"] == "call-ready")
    below = sum(1 for p in scored if p["status"] == "below-threshold")
    disqualified = sum(1 for p in scored if p["status"] == "disqualified")
    skipped = sum(1 for p in scored if p["status"] == "skipped")
    print(f"\n  Done: {call_ready} call-ready, {below} below threshold, {disqualified} disqualified, {skipped} skipped")
    return scored


def run_deep_enrich():
    print("\n[Stage 5/6] Deep Enrichment")
    print("-" * 40)
    print("  Pulling episode details, company pages, and LLM theme summaries for call-ready prospects...\n")
    scored = load("score")
    enriched = deep_enrich_prospects(scored)
    save("deep_enrich", enriched)
    call_ready = [p for p in enriched if p.get("status") == "call-ready"]
    with_themes = sum(1 for p in call_ready if p.get("podcast_themes"))
    with_company = sum(1 for p in call_ready if p.get("company_summary"))
    print(f"\n  Done: {len(call_ready)} call-ready prospects deep enriched")
    print(f"    Podcast themes: {with_themes}/{len(call_ready)}")
    print(f"    Company summaries: {with_company}/{len(call_ready)}")
    return enriched


def run_upload():
    print("\n[Stage 6/6] Upload to Airtable")
    print("-" * 40)
    print("  Pushing scored prospects to Airtable for review...\n")
    prospects = load("deep_enrich")
    upload_to_airtable(prospects)
    print("\n  Done: Airtable populated")


def run_all():
    print("=" * 60)
    print("PROSPECT PIPELINE (full run)")
    print("=" * 60)
    run_discover()
    run_qualify()
    run_enrich()
    run_score()
    run_deep_enrich()
    run_upload()
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


def print_usage():
    print("Usage: py src/run_pipeline.py [step]")
    print()
    print("Steps (run in order):")
    print("  discover  - Search Podcast Index + parse RSS feeds")
    print("  qualify   - AI classification via Ollama (person/org, language, domain)")
    print("  enrich    - Enrich qualified prospects via Prospeo API")
    print("  score     - Apply hard filters + weighted scoring")
    print("  deep_enrich - Pull episode details, company pages, LLM summaries for call-ready prospects")
    print("  upload    - Push scored prospects to Airtable")
    print()
    print("  all       - Run all steps end-to-end (default)")
    print("  status    - Show what data files exist and record counts")
    print()
    print("Each step saves its output to src/data/<step>.json")
    print("so you can inspect results before running the next step.")


def print_status():
    print("\nPipeline Status")
    print("-" * 40)
    ensure_data_dir()
    for step in STEPS:
        # qualify saves as "qualified.json" not "qualify.json"
        file_name = "qualified" if step == "qualify" else step
        path = os.path.join(DATA_DIR, f"{file_name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            size_kb = os.path.getsize(path) / 1024
            if step == "qualify":
                q = sum(1 for p in data if p.get("qualification_status") == "qualified")
                dq = sum(1 for p in data if p.get("qualification_status") == "disqualified")
                rs = sum(1 for p in data if p.get("qualification_status") == "existing_riverside_customer")
                print(f"  {step:10} : {len(data):4} records ({size_kb:.1f} KB) | {q} qualified, {dq} disqualified, {rs} riverside")
            elif step == "score":
                call_ready = sum(1 for p in data if p.get("status") == "call-ready")
                below = sum(1 for p in data if p.get("status") == "below-threshold")
                disqualified = sum(1 for p in data if p.get("status") == "disqualified")
                skipped = sum(1 for p in data if p.get("status") == "skipped")
                print(f"  {step:10} : {len(data):4} records ({size_kb:.1f} KB) | {call_ready} ready, {below} below, {disqualified} disq, {skipped} skip")
            elif step == "deep_enrich":
                call_ready = [p for p in data if p.get("status") == "call-ready"]
                with_themes = sum(1 for p in call_ready if p.get("podcast_themes"))
                with_company = sum(1 for p in call_ready if p.get("company_summary"))
                print(f"  {step:10} : {len(data):4} records ({size_kb:.1f} KB) | {len(call_ready)} call-ready, {with_themes} themes, {with_company} summaries")
            elif step == "enrich":
                enriched_ok = sum(1 for p in data if p.get("enrichment_status") == "enriched")
                failed = sum(1 for p in data if p.get("enrichment_status") == "enrichment-failed")
                print(f"  {step:10} : {len(data):4} records ({size_kb:.1f} KB) | {enriched_ok} enriched, {failed} failed")
            else:
                print(f"  {step:10} : {len(data):4} records ({size_kb:.1f} KB)")
        else:
            print(f"  {step:10} : not run yet")
    print()


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"

    if step == "discover":
        run_discover()
    elif step == "qualify":
        run_qualify()
    elif step == "enrich":
        run_enrich()
    elif step == "score":
        run_score()
    elif step == "deep_enrich":
        run_deep_enrich()
    elif step == "upload":
        run_upload()
    elif step == "all":
        run_all()
    elif step == "status":
        print_status()
    elif step in ("--help", "-h", "help"):
        print_usage()
    else:
        print(f"Unknown step: {step}")
        print_usage()
        sys.exit(1)
