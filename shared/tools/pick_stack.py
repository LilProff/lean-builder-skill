"""Pick the cheapest stack for a build. Deterministic: same inputs, same output. No network, no model calls.

Usage:
  python pick_stack.py --type saas --context personal --commercial no [--md] [--out kit/stack.json]
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from profile_io import DEFAULT_PATH, ProfileError, load_profile

TYPES = ("website", "saas", "internal", "agent")
CONTEXTS = ("personal", "client", "startup")
STALE_DAYS = 90
DATA_DIR = Path(__file__).resolve().parent.parent


class NoMatchError(ValueError):
    """No decision-table row fits the request."""


class AmbiguousMatchError(ValueError):
    """More than one decision-table row fits the request."""


def _select_row(build_type, context, commercial, stacks):
    rows = [
        r for r in stacks["rows"]
        if r["type"] == build_type and r["context"] == context and r["commercial"] in ("any", commercial)
    ]
    if not rows:
        raise NoMatchError(
            f"No stack for type '{build_type}', context '{context}'. "
            f"Valid types: {', '.join(TYPES)}. Valid contexts: {', '.join(CONTEXTS)}."
        )
    if len(rows) > 1:
        raise AmbiguousMatchError(f"More than one stack matches: {', '.join(r['id'] for r in rows)}.")
    return rows[0]


def _usable(provider, accounts, tiers):
    account = tiers[provider].get("account")
    return account is None or account in accounts


def _component(provider, tiers, today):
    entry = tiers[provider]
    checked = date.fromisoformat(entry["checked_on"])
    stale = (today - checked).days > STALE_DAYS
    return {
        "provider": provider,
        "name": entry["name"],
        "account": entry.get("account"),
        "limits": entry.get("limits", []),
        "source_url": entry["source_url"],
        "checked_on": entry["checked_on"],
        "stale": stale,
        "account_needed": False,
        "note": None,
    }


def _add_note(component, text):
    component["note"] = text if not component["note"] else f"{component['note']} {text}"


def _resolve_headers(overlays, host, tiers, notes):
    out = []
    for overlay in overlays:
        if overlay != "security-headers":
            out.append(overlay)
        elif host and host.startswith("vercel-"):
            out.append("security-headers-vercel")
        elif host and (host.startswith("cloudflare-") or host == "github-pages"):
            out.append("security-headers-cloudflare")
        else:
            name = tiers[host]["name"] if host in tiers else "this host"
            notes.append(f"Set security headers in the app for {name}.")
    return out


def pick(build_type: str, context: str, commercial: bool, accounts: set[str] | None,
         stacks: dict, tiers: dict, today: date) -> dict:
    row = _select_row(build_type, context, commercial, stacks)
    notes: list[str] = []
    if accounts is None:
        notes.append("No profile found: using default choices. Run the profile skill to personalise.")
    check_accounts = accounts is not None and row["accounts_owner"] != "client"

    components = {}
    for role, provider in row["stack"].items():
        chosen = provider
        swap_note = None
        needed = False
        if check_accounts and not _usable(provider, accounts, tiers):
            account = tiers[provider]["account"]
            for option in row["fallbacks"].get(role, []):
                if _usable(option, accounts, tiers):
                    chosen = option
                    swap_note = f"No {account} account in your profile: using {tiers[option]['name']} instead."
                    break
            else:
                needed = True
                swap_note = f"Needs a new {account} account."
        comp = _component(chosen, tiers, today)
        comp["account_needed"] = needed
        comp["why"] = row.get("why", {}).get(role, "")
        if swap_note:
            _add_note(comp, swap_note)
        if comp["stale"]:
            _add_note(comp, f"Limits last checked {comp['checked_on']}: re-check before relying on them.")
        components[role] = comp

    host = components.get("host", {}).get("provider")
    overlays = _resolve_headers(row["overlays"], host, tiers, notes)
    return {
        "row_id": row["id"],
        "type": build_type,
        "context": context,
        "commercial": commercial,
        "accounts_owner": row["accounts_owner"],
        "components": components,
        "overlays": overlays,
        "upgrade_triggers": list(row["upgrade_triggers"]),
        "notes": notes,
    }


def _limits_text(limits):
    if not limits:
        return "none listed"
    parts = []
    for item in limits:
        unit = f" {item['unit']}" if item.get("unit") else ""
        parts.append(f"{item['metric']}: {item['value']}{unit} {item['period']}")
    return "; ".join(parts)


def render_md(result: dict) -> str:
    owner = "the client's accounts" if result["accounts_owner"] == "client" else "your accounts"
    lines = [
        f"Stack `{result['row_id']}` ({result['type']}, {result['context']}, "
        f"{'earns money' if result['commercial'] else 'not earning'}), on {owner}.",
        "",
        "| Role | Choice | Free-tier limits | Checked on | Note |",
        "|---|---|---|---|---|",
    ]
    for role, comp in result["components"].items():
        lines.append(
            f"| {role} | {comp['name']} | {_limits_text(comp['limits'])} | "
            f"[{comp['checked_on']}]({comp['source_url']}) | {comp['note'] or ''} |"
        )
    if result["upgrade_triggers"]:
        lines += ["", "Upgrade triggers: " + ", ".join(f"`{t}`" for t in result["upgrade_triggers"])]
    if result["notes"]:
        lines.append("")
    for note in result["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Pick the cheapest stack for a build.")
    parser.add_argument("--type", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--commercial", required=True, choices=("yes", "no"))
    parser.add_argument("--profile", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--md", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    try:
        profile = load_profile(args.profile)
        stacks = json.loads((args.data_dir / "stacks.json").read_text(encoding="utf-8"))
        tiers = json.loads((args.data_dir / "free-tiers.json").read_text(encoding="utf-8"))
        accounts = profile["accounts"] if profile else None
        result = pick(args.type, args.context, args.commercial == "yes", accounts, stacks, tiers, date.today())
    except (NoMatchError, AmbiguousMatchError, ProfileError) as err:
        print(str(err), file=sys.stderr)
        return 2

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(render_md(result) if args.md else json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
