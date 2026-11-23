import re

import pytest

from conftest import REPO_ROOT, SHARED

SKILLS_DIR = REPO_ROOT / "skills"
OVERLAY_IDS = {
    "claude-md-lean", "status-md", "env-example", "gitignore-secrets", "security-headers-cloudflare",
    "security-headers-vercel", "contact-form-worker", "paystack-webhook", "whatsapp-webhook-worker",
    "telegram-webhook-worker", "openrouter-client", "n8n-skeletons", "audit-log-table", "rls-policies",
    "cloud-run-fastapi",
}
OVERLAY_SUFFIXES = ("-worker", "-webhook", "-skeletons", "-table", "-policies", "-fastapi")
CORE = {"profile", "kit", "lean-claude"}
BUILD = {"build-website", "build-saas", "build-internal", "build-agent"}
SUPPORT = {"pay", "deploy", "cost-guard", "handoff"}


def skill_dirs():
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.exists() else []


def front_matter(text: str) -> dict:
    lines = text.splitlines()
    assert lines and lines[0] == "---", "SKILL.md must start with front matter"
    end = lines.index("---", 1)
    data = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip()
    return data


@pytest.mark.parametrize("skill_dir", skill_dirs(), ids=lambda p: p.name)
def test_frontmatter(skill_dir):
    meta = front_matter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    assert meta["name"] == skill_dir.name
    assert 50 <= len(meta["description"]) <= 1024


@pytest.mark.parametrize("skill_dir", skill_dirs(), ids=lambda p: p.name)
def test_referenced_tools_exist(skill_dir):
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    for tool in re.findall(r"tools/([a-z_]+\.py)", text):
        assert (SHARED / "tools" / tool).exists(), tool


@pytest.mark.parametrize("skill_dir", skill_dirs(), ids=lambda p: p.name)
def test_referenced_overlays_exist(skill_dir):
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    for token in re.findall(r"`([a-z0-9-]+)`", text):
        if token in OVERLAY_IDS:
            assert (SHARED / "overlays" / token / "overlay.json").exists(), token
        elif token.endswith(OVERLAY_SUFFIXES):
            pytest.fail(f"{skill_dir.name} names unknown overlay `{token}`")


@pytest.mark.parametrize("skill_dir", skill_dirs(), ids=lambda p: p.name)
def test_no_dashes(skill_dir):
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "—" not in text and "–" not in text


def names():
    return {p.name for p in skill_dirs()}


def test_core_skills_present():
    assert CORE <= names()


def test_build_skills_present():
    assert BUILD <= names()


def test_exactly_eleven_skills():
    assert names() == CORE | BUILD | SUPPORT


# Final review fixes (Important 3, 4, 7, 9): instructions match how the tools behave.
def skill_text(name):
    return (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")


def test_build_agent_forces_worker_overlay():
    assert "--force" in skill_text("build-agent")


@pytest.mark.parametrize("name", sorted(BUILD))
def test_build_skills_handle_non_empty_folder(name):
    assert "_starter" in skill_text(name)


def test_hobby_warning_before_live_keys():
    assert "--commercial yes" in skill_text("build-saas")
    assert "--commercial yes" in skill_text("pay")


def test_deploy_names_agent_host_role():
    assert "webhooks" in skill_text("deploy")
