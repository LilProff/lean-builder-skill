"""Check free-tier data age and whether any upgrade trigger has fired.

Usage:
  python freetier_check.py --plan-json kit/stack.json [--usage usage.json] [--strict]

Trigger grammar: "provider:metric>number" fires when usage["provider:metric"] > number;
"provider:condition" fires when usage["provider:condition"] is True. Missing usage never fires.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent
TRIGGER = re.compile(r"^(?P<key>[a-z0-9-]+:[a-z0-9_]+)(?:>(?P<limit>[0-9]+(?:\.[0-9]+)?))?$")


def stale_entries(tiers: dict, today: date, max_age_days: int = 90) -> list[str]:
    return sorted(
        pid for pid, entry in tiers.items()
        if (today - date.fromisoformat(entry["checked_on"])).days > max_age_days
    )


def evaluate_triggers(triggers: list[str], usage: dict) -> list[str]:
    fired = []
    for trigger in triggers:
        match = TRIGGER.match(trigger)
        if not match:
            raise ValueError(f"Malformed trigger: {trigger}")
        key, limit = match["key"], match["limit"]
        if key not in usage:
            continue
        value = usage[key]
        if limit is None:
            if value is True:
                fired.append(trigger)
        elif isinstance(value, (int, float)) and not isinstance(value, bool) and value > float(limit):
            fired.append(trigger)
    return fired


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Check free-tier data age and upgrade triggers.")
    parser.add_argument("--plan-json", type=Path, required=True)
    parser.add_argument("--usage", type=Path)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    try:
        plan = json.loads(args.plan_json.read_text(encoding="utf-8"))
        tiers = json.loads((args.data_dir / "free-tiers.json").read_text(encoding="utf-8"))
        usage = json.loads(args.usage.read_text(encoding="utf-8")) if args.usage else {}

        stale = stale_entries(tiers, date.today())
        fired = evaluate_triggers(plan.get("upgrade_triggers", []), usage)
    except (OSError, ValueError) as err:
        print(f"freetier_check: {err}", file=sys.stderr)
        return 2
    print("Stale limit data (re-check the source page): " + (", ".join(stale) if stale else "none"))
    print("Upgrade triggers fired: " + (", ".join(fired) if fired else "none"))
    if not usage:
        print("No usage file given: triggers were not checked against real numbers.")
    return 1 if args.strict and (stale or fired) else 0


if __name__ == "__main__":
    sys.exit(main())
