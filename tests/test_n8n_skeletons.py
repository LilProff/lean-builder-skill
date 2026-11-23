import json

import pytest

from conftest import SHARED

N8N_DIR = SHARED / "overlays" / "n8n-skeletons" / "files" / "n8n"
FILES = ["sheet-sync.json", "lead-capture.json", "daily-report.json"]


@pytest.mark.parametrize("name", FILES)
def test_n8n_skeletons_shape(name):
    flow = json.loads((N8N_DIR / name).read_text(encoding="utf-8"))
    assert flow["name"]
    assert isinstance(flow["nodes"], list) and flow["nodes"]
    assert isinstance(flow["connections"], dict)
    first = flow["nodes"][0]["type"].lower()
    assert "trigger" in first or "webhook" in first
    names = {n["name"] for n in flow["nodes"]}
    for source, outputs in flow["connections"].items():
        assert source in names
        for branch in outputs["main"]:
            for link in branch:
                assert link["node"] in names


@pytest.mark.parametrize("name", FILES)
def test_n8n_skeletons_store_no_credentials(name):
    flow = json.loads((N8N_DIR / name).read_text(encoding="utf-8"))
    for node in flow["nodes"]:
        assert "credentials" not in node, node["name"]
