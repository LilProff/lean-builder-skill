from datetime import date

import pytest

from conftest import REPO_ROOT, SHARED, load_json
from pick_stack import pick

EXAMPLES = REPO_ROOT / "examples"
EXAMPLES_DATE = date(2026, 11, 23)  # stated in examples/README.md
NAMES = ["website-personal", "saas-startup", "internal-client", "agent-personal"]


def front_matter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    meta = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("["):
            meta[key.strip()] = [v.strip() for v in value.strip("[]").split(",") if v.strip()]
        else:
            meta[key.strip()] = value
    return meta


@pytest.mark.parametrize("name", NAMES)
def test_example_matches_picker(name):
    meta = front_matter(EXAMPLES / name / "brief.md")
    stacks = load_json(SHARED / "stacks.json")
    tiers = load_json(SHARED / "free-tiers.json")
    result = pick(meta["type"], meta["context"], meta["commercial"] == "yes", set(meta["accounts"]),
                  stacks, tiers, EXAMPLES_DATE)
    assert result == load_json(EXAMPLES / name / "expected.json")


def test_readme_states_the_date():
    assert EXAMPLES_DATE.isoformat() in (EXAMPLES / "README.md").read_text(encoding="utf-8")
