from conftest import load_json


def test_plugin_json_fields(repo_root):
    p = load_json(repo_root / ".claude-plugin/plugin.json")
    assert p["name"] == "lean-builder-skill"
    assert p["version"] == "0.1.0"
    assert p["license"] == "MIT"
    assert p["repository"] == "https://github.com/LilProff/lean-builder-skill"


def test_marketplace_points_to_root(repo_root):
    m = load_json(repo_root / ".claude-plugin/marketplace.json")
    assert m["plugins"][0]["name"] == "lean-builder-skill"
    assert m["plugins"][0]["source"] == "./"


def test_gitignore_blocks_secrets(repo_root):
    lines = (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()
    for needed in (".env", ".env.*", "!.env.example", "node_modules/", "__pycache__/"):
        assert needed in lines
