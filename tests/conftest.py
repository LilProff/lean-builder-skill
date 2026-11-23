import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED = REPO_ROOT / "shared"
sys.path.insert(0, str(SHARED / "tools"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def shared_dir() -> Path:
    return SHARED
