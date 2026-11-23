from datetime import date

import jsonschema

from conftest import load_json

FRAMEWORKS = {"astro", "nextjs", "hono", "fastapi", "better-auth", "keystatic"}
SERVICES = {
    "cloudflare-pages", "cloudflare-workers", "cloudflare-d1", "cloudflare-r2", "cloudflare-cron",
    "github-pages", "vercel-hobby", "vercel-pro", "render", "gcp-cloud-run", "supabase", "neon",
    "resend", "openrouter", "paystack", "grey", "n8n-selfhosted", "whatsapp-cloud-api", "telegram-bot",
}
EXPECTED_IDS = FRAMEWORKS | SERVICES


def _tiers(shared_dir):
    return load_json(shared_dir / "free-tiers.json")


def test_schema_valid(shared_dir):
    jsonschema.validate(_tiers(shared_dir), load_json(shared_dir / "free-tiers.schema.json"))


def test_exact_provider_ids(shared_dir):
    assert set(_tiers(shared_dir)) == EXPECTED_IDS


def test_frameworks_have_no_account(shared_dir):
    tiers = _tiers(shared_dir)
    assert all(tiers[f]["account"] is None for f in FRAMEWORKS)
    assert all(tiers[s]["account"] for s in SERVICES)


def test_services_have_limits_or_a_note(shared_dir):
    for pid, e in _tiers(shared_dir).items():
        if e["account"]:
            assert e["limits"] or e.get("notes"), pid


def test_checked_on_not_future(shared_dir):
    assert all(date.fromisoformat(e["checked_on"]) <= date.today() for e in _tiers(shared_dir).values())


def test_vercel_hobby_never_marked_commercial(shared_dir):
    assert _tiers(shared_dir)["vercel-hobby"]["commercial_use"] is not True


def test_github_pages_not_for_business(shared_dir):
    assert _tiers(shared_dir)["github-pages"]["commercial_use"] is False


def test_n8n_is_conditional(shared_dir):
    assert _tiers(shared_dir)["n8n-selfhosted"]["commercial_use"] == "conditional"
