import pytest

from profile_io import ProfileError, load_profile, write_profile
from secret_patterns import looks_like_secret


def write(tmp_path, text):
    p = tmp_path / "profile.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_missing_returns_none(tmp_path):
    assert load_profile(tmp_path / "nope.md") is None


def test_load_parses_lists_and_scalars(tmp_path):
    p = write(tmp_path, "---\naccounts: [cloudflare, neon]\ncurrency: NGN\n---\nnotes here\n")
    prof = load_profile(p)
    assert prof["accounts"] == {"cloudflare", "neon"}
    assert prof["currency"] == "NGN"
    assert prof["notes"] == "notes here"


def test_missing_keys_get_defaults(tmp_path):
    prof = load_profile(write(tmp_path, "---\ncurrency: NGN\n---\n"))
    assert prof["accounts"] == set()
    assert prof["secret_names"] == []


def test_malformed_line_names_line(tmp_path):
    p = write(tmp_path, "---\naccounts [cloudflare]\n---\n")
    with pytest.raises(ProfileError, match="line 2"):
        load_profile(p)


def test_missing_front_matter_is_an_error(tmp_path):
    with pytest.raises(ProfileError, match="line 1"):
        load_profile(write(tmp_path, "accounts: [neon]\n"))


def test_write_refuses_secret_values(tmp_path):
    with pytest.raises(ValueError, match="paystack"):
        write_profile(tmp_path / "p.md", {"accounts": ["paystack"], "secret_names": ["sk_live_" + "a" * 24]})
    assert not (tmp_path / "p.md").exists()


def test_roundtrip(tmp_path):
    path = tmp_path / "deep" / "profile.md"
    write_profile(path, {"accounts": ["neon", "cloudflare"], "currency": "NGN",
                         "secret_names": ["PAYSTACK_SECRET_KEY"], "notes": "likes Astro"})
    prof = load_profile(path)
    assert prof["accounts"] == {"neon", "cloudflare"}
    assert prof["secret_names"] == ["PAYSTACK_SECRET_KEY"]
    assert prof["notes"] == "likes Astro"


def test_patterns_detect_fakes():
    assert looks_like_secret("sk-or-v1-" + "ab" * 20) == "openrouter"
    assert looks_like_secret("sk_test_" + "x" * 24) == "paystack"
    assert looks_like_secret("-----BEGIN RSA " + "PRIVATE KEY-----") == "private-key"


def test_patterns_ignore_names():
    assert looks_like_secret("PAYSTACK_SECRET_KEY") is None
    assert looks_like_secret("OPENROUTER_API_KEY") is None


# Final review fixes (Important 1 and 6)
def test_unknown_key_names_line(tmp_path):
    with pytest.raises(ProfileError, match="line 2"):
        load_profile(write(tmp_path, "---\nacounts: [neon]\n---\n"))


def test_unclosed_list_names_line(tmp_path):
    with pytest.raises(ProfileError, match="line 2"):
        load_profile(write(tmp_path, "---\naccounts: [cloudflare, neon\n---\n"))


def test_unknown_account_id_names_line(tmp_path):
    with pytest.raises(ProfileError, match="line 2.*Cloudflare"):
        load_profile(write(tmp_path, "---\naccounts: [Cloudflare]\n---\n"))


def test_bom_is_ignored(tmp_path):
    prof = load_profile(write(tmp_path, "﻿---\naccounts: [neon]\n---\n"))
    assert prof["accounts"] == {"neon"}


def test_known_accounts_match_catalogue():
    from conftest import SHARED, load_json
    from profile_io import KNOWN_ACCOUNTS
    tiers = load_json(SHARED / "free-tiers.json")
    assert KNOWN_ACCOUNTS == {e["account"] for e in tiers.values() if e["account"]}


def test_identifiers_are_not_secrets():
    assert looks_like_secret("def store_user_session_in_database():") is None
    assert looks_like_secret("ignore_whitespace_in_comparisons = True") is None
    assert looks_like_secret("/blog/ask-anything-about-your-documents-here") is None
    assert looks_like_secret("key = 'sk_live_" + "a" * 24 + "'") == "paystack"
