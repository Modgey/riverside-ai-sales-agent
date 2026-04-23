"""
Run the curated ICP prospects through enrich -> score -> deep_enrich -> call_context.
Skips discover and qualify (already hand-curated).

Usage: py src/run_seed.py [step]
  Steps: enrich, score, deep_enrich, call_context, all (default)
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from pipeline.enrich import enrich_prospects
from pipeline.score import score_and_filter
from pipeline.deep_enrich import deep_enrich_prospects
from pipeline.call_context import generate_call_context

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PREFIX = "seed_icp"


def save(step_name: str, prospects: list[dict]):
    path = os.path.join(DATA_DIR, f"{PREFIX}_{step_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prospects, f, indent=2, ensure_ascii=False)
    print(f"  Saved: data/{PREFIX}_{step_name}.json ({len(prospects)} records)")


def load(step_name: str) -> list[dict]:
    path = os.path.join(DATA_DIR, f"{PREFIX}_{step_name}.json")
    if not os.path.exists(path):
        print(f"  Error: data/{PREFIX}_{step_name}.json not found. Run the previous step first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Loaded: data/{PREFIX}_{step_name}.json ({len(data)} records)")
    return data


def load_seed() -> list[dict]:
    path = os.path.join(DATA_DIR, f"{PREFIX}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Loaded: data/{PREFIX}.json ({len(data)} curated prospects)")
    return data


def run_enrich():
    print("\n[Seed] Enrichment")
    print("-" * 40)
    prospects = load_seed()
    enriched = enrich_prospects(prospects)
    save("enrich", enriched)
    return enriched


def run_score():
    print("\n[Seed] Scoring")
    print("-" * 40)
    enriched = load(f"enrich")
    scored = score_and_filter(enriched, skip_list_path=os.path.join(os.path.dirname(__file__), "skip_list.json"))
    save("score", scored)
    return scored


def run_deep_enrich():
    print("\n[Seed] Deep Enrichment")
    print("-" * 40)
    scored = load("score")
    enriched = deep_enrich_prospects(scored)
    save("deep_enrich", enriched)
    return enriched


def run_call_context():
    print("\n[Seed] Call Context Generation")
    print("-" * 40)
    prospects = load("deep_enrich")
    enriched = generate_call_context(prospects)
    save("call_context", enriched)
    return enriched


def run_all():
    print("=" * 60)
    print("CURATED ICP PIPELINE")
    print("=" * 60)
    run_enrich()
    run_score()
    run_deep_enrich()
    run_call_context()
    print("\n" + "=" * 60)
    print("SEED PIPELINE COMPLETE")
    print(f"Results in: data/{PREFIX}_*.json")
    print("=" * 60)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"

    if step == "enrich":
        run_enrich()
    elif step == "score":
        run_score()
    elif step == "deep_enrich":
        run_deep_enrich()
    elif step == "call_context":
        run_call_context()
    elif step == "all":
        run_all()
    else:
        print(f"Unknown step: {step}")
        print("Usage: py src/run_seed.py [enrich|score|deep_enrich|call_context|all]")
        sys.exit(1)
