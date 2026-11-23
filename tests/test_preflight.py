import json
from datetime import date

from preflight import main, run_preflight

TODAY = date(2026, 11, 23)
FRESH = {"neon": {"checked_on": "2026-11-23"}}


def status(checks, name):
    return next(c.status for c in checks if c.name == name)


def clean_cloudflare(tmp_path):
    (tmp_path / ".env.example").write_text("RESEND_API_KEY=\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("node_modules/\n.env\n", encoding="utf-8")
    (tmp_path / "public").mkdir()
    (tmp_path / "public" / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n", encoding="utf-8")
    return tmp_path


def test_clean_cloudflare_project_passes(tmp_path):
    checks = run_preflight(clean_cloudflare(tmp_path), "cloudflare-pages", None, FRESH, TODAY)
    assert [c.name for c in checks] == ["build", "secrets", "env-example", "gitignore-env", "headers", "limits"]
    assert all(c.status != "fail" for c in checks)
    assert status(checks, "build") == "warn"


def test_failing_build_fails(tmp_path):
    checks = run_preflight(clean_cloudflare(tmp_path), "cloudflare-pages",
                           'python -c "import sys; sys.exit(1)"', FRESH, TODAY)
    assert status(checks, "build") == "fail"


def test_passing_build_passes(tmp_path):
    checks = run_preflight(clean_cloudflare(tmp_path), "cloudflare-pages", 'python -c "pass"', FRESH, TODAY)
    assert status(checks, "build") == "pass"


def test_missing_env_example_fails(tmp_path):
    clean_cloudflare(tmp_path)
    (tmp_path / ".env.example").unlink()
    assert status(run_preflight(tmp_path, "cloudflare-pages", None, FRESH, TODAY), "env-example") == "fail"


def test_gitignore_without_env_fails(tmp_path):
    clean_cloudflare(tmp_path)
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    assert status(run_preflight(tmp_path, "cloudflare-pages", None, FRESH, TODAY), "gitignore-env") == "fail"


def test_committed_secret_fails(tmp_path):
    clean_cloudflare(tmp_path)
    (tmp_path / "a.ts").write_text("sk_live_" + "y" * 24, encoding="utf-8")
    assert status(run_preflight(tmp_path, "cloudflare-pages", None, FRESH, TODAY), "secrets") == "fail"


def test_vercel_headers_from_vercel_json(tmp_path):
    clean_cloudflare(tmp_path)
    (tmp_path / "vercel.json").write_text(json.dumps({"headers": []}), encoding="utf-8")
    assert status(run_preflight(tmp_path, "vercel-hobby", None, FRESH, TODAY), "headers") == "pass"


def test_vercel_without_headers_fails(tmp_path):
    clean_cloudflare(tmp_path)
    assert status(run_preflight(tmp_path, "vercel-hobby", None, FRESH, TODAY), "headers") == "fail"


def test_render_headers_warn(tmp_path):
    assert status(run_preflight(clean_cloudflare(tmp_path), "render", None, FRESH, TODAY), "headers") == "warn"


def test_stale_limits_warn(tmp_path):
    old = {"neon": {"checked_on": "2026-01-01"}}
    assert status(run_preflight(clean_cloudflare(tmp_path), "cloudflare-pages", None, old, TODAY), "limits") == "warn"


def test_main_exit_code(tmp_path):
    clean_cloudflare(tmp_path)
    assert main(["--project", str(tmp_path), "--host", "cloudflare-pages"]) == 0
    (tmp_path / ".env.example").unlink()
    assert main(["--project", str(tmp_path), "--host", "cloudflare-pages"]) == 1


# Final review fix (Important 3): API-only Workers and Next.js on Workers.
def test_worker_without_public_folder_warns(tmp_path):
    (tmp_path / ".env.example").write_text("A=\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    assert status(run_preflight(tmp_path, "cloudflare-workers", None, FRESH, TODAY), "headers") == "warn"


def test_next_config_headers_pass_on_workers(tmp_path):
    clean_cloudflare(tmp_path)
    (tmp_path / "public" / "_headers").unlink()
    (tmp_path / "next.config.ts").write_text("export default { async headers() { return [] } }", encoding="utf-8")
    assert status(run_preflight(tmp_path, "cloudflare-workers", None, FRESH, TODAY), "headers") == "pass"
