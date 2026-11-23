"""Read and write the private lean-builder profile (a Markdown file with simple front matter).

The profile holds account ids and the NAMES of secrets, never secret values.
"""
from pathlib import Path

from secret_patterns import looks_like_secret

DEFAULT_PATH = Path.home() / ".claude" / "lean-builder" / "profile.md"
LIST_KEYS = ("accounts", "secret_names")
SCALAR_DEFAULTS = {"currency": "", "region": "", "default_context": "", "client_rule": ""}
ALLOWED_KEYS = set(LIST_KEYS) | set(SCALAR_DEFAULTS)
# Must equal the "account" values in shared/free-tiers.json (a test checks this).
KNOWN_ACCOUNTS = {
    "vercel", "cloudflare", "github", "gcp", "render", "supabase", "neon", "resend",
    "openrouter", "paystack", "grey", "n8n-selfhosted", "meta", "telegram",
}


class ProfileError(ValueError):
    """The profile file exists but cannot be read."""


def _parse_value(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [item.strip() for item in raw[1:-1].split(",") if item.strip()]
    return raw


def load_profile(path: Path) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ProfileError(f"{path}: line 1 must be '---' (start of the profile settings).")
    data: dict = {}
    end = None
    for number, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            end = number
            break
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep or not key.strip() or " " in key.strip():
            raise ProfileError(f"{path}: line {number} should look like 'key: value' or 'key: [a, b]'.")
        key = key.strip()
        if key not in ALLOWED_KEYS:
            raise ProfileError(
                f"{path}: line {number}: unknown setting '{key}'. Allowed: {', '.join(sorted(ALLOWED_KEYS))}."
            )
        if value.strip().startswith("[") and not value.strip().endswith("]"):
            raise ProfileError(f"{path}: line {number}: the list is not closed with ']'.")
        data[key] = _parse_value(value)
        if key == "accounts":
            listed = data[key] if isinstance(data[key], list) else [data[key]]
            unknown = [a for a in listed if a and a not in KNOWN_ACCOUNTS]
            if unknown:
                raise ProfileError(
                    f"{path}: line {number}: unknown account id(s) {', '.join(unknown)}. "
                    f"Use lower-case ids from: {', '.join(sorted(KNOWN_ACCOUNTS))}."
                )
    if end is None:
        raise ProfileError(f"{path}: line {len(lines) + 1}: the settings block is never closed with '---'.")
    profile = dict(SCALAR_DEFAULTS)
    profile.update({k: v for k, v in data.items() if k not in LIST_KEYS})
    accounts = data.get("accounts", [])
    profile["accounts"] = set(accounts if isinstance(accounts, list) else [accounts])
    names = data.get("secret_names", [])
    profile["secret_names"] = names if isinstance(names, list) else [names]
    profile["notes"] = "\n".join(lines[end:]).strip()
    return profile


def _values(data: dict):
    for value in data.values():
        if isinstance(value, (list, set, tuple)):
            yield from (str(v) for v in value)
        else:
            yield str(value)


def write_profile(path: Path, data: dict) -> None:
    for value in _values(data):
        kind = looks_like_secret(value)
        if kind:
            raise ValueError(
                f"Refusing to save: a value looks like a real {kind} secret. "
                "Store only the NAME of the key (for example PAYSTACK_SECRET_KEY), never the key itself."
            )
    out = ["---"]
    for key, value in data.items():
        if key == "notes":
            continue
        if isinstance(value, (list, set, tuple)):
            items = sorted(value) if isinstance(value, set) else list(value)
            out.append(f"{key}: [{', '.join(items)}]")
        else:
            out.append(f"{key}: {value}")
    out.append("---")
    if data.get("notes"):
        out.append(str(data["notes"]))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
