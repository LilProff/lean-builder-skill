"""Patterns that look like real secret values. Used by profile_io and secret_scan.

Order matters: more specific patterns come first so a key is named by its real provider.
Each prefix must start a token (B = "not glued to a longer word"), so names such as
store_user_session or ask-anything-about-... are not flagged.
"""
import re

B = r"(?<![A-Za-z0-9_-])"

PATTERNS: dict[str, re.Pattern] = {
    "paystack": re.compile(B + r"sk_(?:live|test)_[A-Za-z0-9]{20,}"),
    "openrouter": re.compile(B + r"sk-or-v1-[A-Fa-f0-9]{32,}"),
    "anthropic": re.compile(B + r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai": re.compile(B + r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    "resend": re.compile(B + r"re_[A-Za-z0-9_]{20,}"),
    "github": re.compile(B + r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "aws": re.compile(B + r"AKIA[0-9A-Z]{16}"),
    "google": re.compile(B + r"AIza[0-9A-Za-z_-]{35}"),
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def looks_like_secret(text: str) -> str | None:
    """Return the name of the first pattern found in text, or None."""
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            return name
    return None
