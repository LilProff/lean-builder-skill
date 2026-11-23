import json

import pytest

from apply_overlays import apply
from conftest import SHARED, load_json

OVERLAYS = SHARED / "overlays"
VALUES = {"PROJECT_NAME": "Demo", "STACK_SUMMARY": "Astro on Cloudflare Pages", "CONTEXT": "personal",
          "ENV_VARS": "RESEND_API_KEY=", "SHARED_DIR": "/plugins/lean-builder-skill/shared",
          "HOST": "cloudflare-pages", "INSTALL_CMD": "npm install", "BUILD_CMD": "npm run build"}
BASE = ["claude-md-lean", "status-md", "env-example", "gitignore-secrets"]


def manifests():
    return sorted(p for p in OVERLAYS.glob("*/overlay.json"))


def test_every_overlay_manifest_valid():
    assert manifests(), "no overlays found"
    for path in manifests():
        m = load_json(path)
        assert m["id"] == path.parent.name
        assert m["description"]
        for f in m["files"]:
            assert f["mode"] in ("copy", "append")
            assert (path.parent / "files" / f["src"]).is_file(), (m["id"], f["src"])


def test_stack_overlay_ids_exist():
    stacks = load_json(SHARED / "stacks.json")
    needed = set()
    for row in stacks["rows"]:
        for overlay in row["overlays"]:
            if overlay == "security-headers":
                needed |= {"security-headers-cloudflare", "security-headers-vercel"}
            else:
                needed.add(overlay)
    missing = sorted(o for o in needed if not (OVERLAYS / o / "overlay.json").exists())
    assert missing == []


def test_apply_creates_files(tmp_path):
    report = apply(BASE, tmp_path, OVERLAYS, VALUES)
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "STATUS.md").exists()
    assert "RESEND_API_KEY=" in (tmp_path / ".env.example").read_text(encoding="utf-8")
    assert "Demo" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "{{" not in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in report.created


def test_apply_skips_existing_without_force(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("mine", encoding="utf-8")
    report = apply(["claude-md-lean"], tmp_path, OVERLAYS, VALUES)
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "mine"
    assert "CLAUDE.md" in report.skipped


def test_force_overwrites(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("mine", encoding="utf-8")
    apply(["claude-md-lean"], tmp_path, OVERLAYS, VALUES, force=True)
    assert "Demo" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


def test_append_adds_missing_lines_once(tmp_path):
    (tmp_path / ".gitignore").write_text("node_modules/\n.env\n", encoding="utf-8")
    first = apply(["gitignore-secrets"], tmp_path, OVERLAYS, VALUES)
    second = apply(["gitignore-secrets"], tmp_path, OVERLAYS, VALUES)
    lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines.count(".env") == 1
    assert lines.count("!.env.example") == 1
    assert lines[0] == "node_modules/"
    assert ".gitignore" in first.appended
    assert ".gitignore" in second.skipped


def test_missing_value_raises_before_writing(tmp_path):
    with pytest.raises(KeyError, match="PROJECT_NAME"):
        apply(["status-md", "claude-md-lean"], tmp_path, OVERLAYS, {})
    assert list(tmp_path.iterdir()) == []


def test_unknown_overlay_raises(tmp_path):
    with pytest.raises(KeyError, match="no-such-overlay"):
        apply(["no-such-overlay"], tmp_path, OVERLAYS, VALUES)


def test_headers_variants(tmp_path):
    apply(["security-headers-cloudflare"], tmp_path, OVERLAYS, VALUES)
    assert "X-Content-Type-Options" in (tmp_path / "public" / "_headers").read_text(encoding="utf-8")
    other = tmp_path / "v"
    other.mkdir()
    apply(["security-headers-vercel"], other, OVERLAYS, VALUES)
    assert "headers" in json.loads((other / "vercel.json").read_text(encoding="utf-8"))


def test_claude_md_template_max_60_lines():
    text = (OVERLAYS / "claude-md-lean" / "files" / "CLAUDE.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 60


# v0.1.1 (dogfood item 2, 3, 6): CLAUDE.md has real paths and commands, no unfilled <...> placeholders.
def test_claude_md_is_fully_filled(tmp_path):
    apply(["claude-md-lean"], tmp_path, OVERLAYS, VALUES)
    text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "<lean-builder>" not in text and "<host>" not in text
    # quoted, because real plugin paths contain spaces (found while dogfooding on Windows)
    assert 'python "/plugins/lean-builder-skill/shared/tools/secret_scan.py" .' in text
    assert 'python "/plugins/lean-builder-skill/shared/tools/preflight.py" --project .' in text
    assert "--host cloudflare-pages" in text and '--build-cmd "npm run build"' in text
    assert "Install: `npm install`" in text
    assert "AGENTS.md" in text


def test_claude_md_requires_host(tmp_path):
    values = {k: v for k, v in VALUES.items() if k != "HOST"}
    with pytest.raises(KeyError, match="HOST"):
        apply(["claude-md-lean"], tmp_path, OVERLAYS, values)


# v0.1.1 (dogfood item 4): role-specific overlays say which stack role they serve.
EXPECTED_ROLES = {
    "contact-form-worker": ["forms"], "paystack-webhook": ["payments"],
    "telegram-webhook-worker": ["messaging"], "whatsapp-webhook-worker": ["messaging"],
    "openrouter-client": ["ai"], "n8n-skeletons": ["glue", "sync"], "cloud-run-fastapi": ["backend", "api"],
}


def test_role_overlays_declare_roles():
    declared = {p.parent.name: load_json(p).get("roles") for p in OVERLAYS.glob("*/overlay.json")}
    assert {k: v for k, v in declared.items() if v} == EXPECTED_ROLES
    stack_roles = {role for row in load_json(SHARED / "stacks.json")["rows"] for role in row["stack"]}
    assert set().union(*EXPECTED_ROLES.values()) <= stack_roles


def test_paystack_route_says_check_amount_and_currency():
    route = (OVERLAYS / "paystack-webhook" / "files" / "src" / "app" / "api" / "paystack" / "webhook" / "route.ts")
    text = route.read_text(encoding="utf-8")
    assert "amount" in text and "currency" in text
