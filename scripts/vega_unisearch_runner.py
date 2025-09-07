import argparse, os, json, time, yaml, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="US")
    parser.add_argument("--profile", default="SmartMoney_NA_Level2")
    args = parser.parse_args()

    regions = load_yaml(ROOT / "config" / "regions.yaml")
    tv = load_yaml(ROOT / "config" / "tradingview_prefilters.yaml")
    scores = load_yaml(ROOT / "modules" / "rules" / "_vega_scores.yaml")

    # Discover rules
    rules_dir = ROOT / "modules" / "rules"
    rule_files = [p for p in rules_dir.glob("*.yaml") if p.name != "_vega_scores.yaml"]

    # Skeleton "plan" (no data pulls here)
    plan = {
        "ts": datetime.datetime.utcnow().isoformat()+"Z",
        "region": args.region,
        "tv_profile": args.profile,
        "region_settings": regions["regions"].get(args.region, {}),
        "rules": [p.name for p in rule_files],
        "notes": [
            "This runner is a skeleton. Replace with your data client to compute signals.",
            "Vega Smart Money A-to-Z and earnings blackout are enforced in the main app.",
        ],
    }

    outdir = ROOT / "outputs"
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "last_run_summary.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print("Planned run for region:", args.region)
    print("Rules:", len(rule_files))
    for p in rule_files:
        print(" -", p.name)
    print("TV Profile:", args.profile)
    print("Output written to outputs/last_run_summary.json")

if __name__ == "__main__":
    main()
