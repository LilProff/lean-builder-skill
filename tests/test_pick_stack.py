import io
import json
import sys
from datetime import date, timedelta

import pytest

import pick_stack
from conftest import SHARED, load_json
from pick_stack import NoMatchError, main, pick, render_md

ALL = {"vercel", "neon", "resend", "cloudflare", "paystack", "supabase", "github", "render", "gcp",
       "openrouter", "n8n-selfhosted", "meta", "telegram", "grey"}


@pytest.fixture
def real():
    return load_json(SHARED / "stacks.json"), load_json(SHARED / "free-tiers.json"), date(2026, 11, 23)


@pytest.fixture
def fx():
    tiers = {
        "appx": {"name": "AppX", "account": None, "limits": [], "source_url": "https://a", "checked_on": "2026-01-01"},
        "hosty": {"name": "Hosty", "account": "hostco", "limits": [{"metric": "m", "value": 1, "period": "p"}],
                  "source_url": "https://h", "checked_on": "2026-01-01"},
    }
    stacks = {"version": 1, "rows": [{
        "id": "x", "type": "website", "context": "personal", "commercial": "any", "accounts_owner": "builder",
        "stack": {"app": "appx", "host": "hosty"}, "fallbacks": {}, "why": {"app": "a", "host": "h"},
        "overlays": ["claude-md-lean"], "upgrade_triggers": [],
    }]}
    return stacks, tiers


def test_saas_personal_free_picks_vercel_hobby(real):
    r = pick("saas", "personal", False, {"vercel", "neon", "resend", "cloudflare", "paystack"}, *real)
    assert r["components"]["host"]["provider"] == "vercel-hobby"
    assert r["row_id"] == "saas-personal-free"


def test_saas_personal_commercial_moves_off_hobby(real):
    r = pick("saas", "personal", True, ALL, *real)
    assert r["components"]["host"]["provider"] == "cloudflare-workers"


def test_missing_account_uses_fallback(real):
    r = pick("saas", "personal", False, ALL - {"vercel"}, *real)
    assert r["components"]["host"]["provider"] == "cloudflare-workers"
    assert "No vercel account" in r["components"]["host"]["note"]


def test_no_fallback_marks_account_needed(fx):
    stacks, tiers = fx
    r = pick("website", "personal", False, set(), stacks, tiers, date(2026, 2, 1))
    host = r["components"]["host"]
    assert host["account_needed"] is True
    assert host["note"].startswith("Needs a new")


def test_client_rows_skip_account_checks(real):
    r = pick("saas", "client", True, set(), *real)
    assert r["accounts_owner"] == "client"
    assert all(not c["account_needed"] and c["note"] is None for c in r["components"].values())


def test_no_profile_keeps_defaults_with_note(real):
    r = pick("saas", "personal", False, None, *real)
    assert r["components"]["host"]["provider"] == "vercel-hobby"
    assert r["notes"][0].startswith("No profile found")


def test_unknown_type_raises(real):
    with pytest.raises(NoMatchError):
        pick("mobile", "personal", False, ALL, *real)


def test_stale_limits_flagged(fx):
    stacks, tiers = fx
    today = date(2026, 1, 1) + timedelta(days=91)
    r = pick("website", "personal", False, {"hostco"}, stacks, tiers, today)
    assert r["components"]["host"]["stale"] is True
    assert "re-check" in r["components"]["host"]["note"]


def test_fresh_limits_not_stale(fx):
    stacks, tiers = fx
    r = pick("website", "personal", False, {"hostco"}, stacks, tiers, date(2026, 2, 1))
    assert r["components"]["host"]["stale"] is False


def test_headers_overlay_resolved(real):
    free = pick("saas", "personal", False, ALL, *real)
    paid = pick("saas", "personal", True, ALL, *real)
    assert "security-headers-vercel" in free["overlays"] and "security-headers" not in free["overlays"]
    assert "security-headers-cloudflare" in paid["overlays"]


def test_deterministic(real):
    assert pick("agent", "startup", True, ALL, *real) == pick("agent", "startup", True, ALL, *real)


def test_render_md_has_table_and_naira_safe(real):
    md = render_md(pick("website", "personal", False, ALL, *real))
    assert "| Role | Choice |" in md
    assert "Cloudflare Pages" in md


def test_main_bad_type_returns_2(capsys):
    assert main(["--type", "mobile", "--context", "personal", "--commercial", "no"]) == 2
    assert "website, saas, internal, agent" in capsys.readouterr().err


def test_main_bad_profile_returns_2(tmp_path, capsys):
    bad = tmp_path / "profile.md"
    bad.write_text("---\naccounts [x]\n---\n", encoding="utf-8")
    code = main(["--type", "website", "--context", "personal", "--commercial", "no", "--profile", str(bad)])
    assert code == 2
    assert "line 2" in capsys.readouterr().err


def test_md_output_on_cp1252_stdout(monkeypatch, tmp_path):
    buf = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", buf)
    code = main(["--type", "saas", "--context", "personal", "--commercial", "no", "--md",
                 "--profile", str(tmp_path / "none.md")])
    assert code == 0


def test_out_writes_json(tmp_path):
    out = tmp_path / "kit" / "stack.json"
    code = main(["--type", "website", "--context", "client", "--commercial", "yes",
                 "--profile", str(tmp_path / "none.md"), "--out", str(out)])
    assert code == 0
    assert json.loads(out.read_text(encoding="utf-8"))["row_id"] == "website-client"


# Final review fix (kit uses each component's reason)
def test_components_carry_why(real):
    r = pick("website", "personal", False, ALL, *real)
    assert "Cloudflare Pages" in r["components"]["host"]["why"]


# v0.1.1 (dogfood item 4): a plan can leave roles out of v1.
@pytest.fixture
def overlay_roles():
    return pick_stack.load_overlay_roles(SHARED / "overlays")


def test_skip_roles_drops_components_overlays_and_triggers(real, overlay_roles):
    r = pick("website", "personal", False, ALL, *real, skip_roles={"forms", "email"}, overlay_roles=overlay_roles)
    assert set(r["components"]) == {"app", "host"}
    assert "contact-form-worker" not in r["overlays"]
    assert r["upgrade_triggers"] == []
    assert any("Not in v1: email, forms" in n for n in r["notes"])


def test_skip_keeps_triggers_of_providers_still_used(real, overlay_roles):
    r = pick("agent", "personal", False, ALL, *real, skip_roles={"glue"}, overlay_roles=overlay_roles)
    assert "glue" not in r["components"] and "n8n-skeletons" not in r["overlays"]
    assert r["upgrade_triggers"] == ["cloudflare-workers:requests_per_day>80000", "openrouter:free_requests_per_day>40"]


@pytest.mark.parametrize("role", ["host", "app", "webhooks"])
def test_required_roles_cannot_be_skipped(real, overlay_roles, role):
    btype = "agent" if role == "webhooks" else "website"
    with pytest.raises(ValueError, match=role):
        pick(btype, "personal", False, ALL, *real, skip_roles={role}, overlay_roles=overlay_roles)


def test_unknown_skip_role_rejected(real, overlay_roles):
    with pytest.raises(ValueError, match="payments"):
        pick("website", "personal", False, ALL, *real, skip_roles={"payments"}, overlay_roles=overlay_roles)


def test_main_skip_roles(tmp_path, capsys):
    out = tmp_path / "kit" / "stack.json"
    code = main(["--type", "website", "--context", "personal", "--commercial", "no", "--skip-roles", "forms,email",
                 "--profile", str(tmp_path / "none.md"), "--out", str(out)])
    assert code == 0
    assert "forms" not in json.loads(out.read_text(encoding="utf-8"))["components"]
    assert main(["--type", "website", "--context", "personal", "--commercial", "no", "--skip-roles", "host",
                 "--profile", str(tmp_path / "none.md")]) == 2
