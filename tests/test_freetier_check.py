import json
from datetime import date

import pytest

from freetier_check import evaluate_triggers, main, stale_entries


def test_threshold_fires():
    assert evaluate_triggers(["neon:storage_gb>0.8"], {"neon:storage_gb": 0.9}) == ["neon:storage_gb>0.8"]


def test_threshold_quiet_below():
    assert evaluate_triggers(["neon:storage_gb>0.8"], {"neon:storage_gb": 0.3}) == []


def test_condition_fires_on_true():
    trig = "vercel-hobby:commercial_use"
    assert evaluate_triggers([trig], {trig: True}) == [trig]


def test_condition_quiet_on_false():
    trig = "vercel-hobby:commercial_use"
    assert evaluate_triggers([trig], {trig: False}) == []


def test_missing_usage_never_fires():
    assert evaluate_triggers(["supabase:idle_pause"], {}) == []


def test_malformed_trigger_raises():
    with pytest.raises(ValueError, match="neon>>1"):
        evaluate_triggers(["neon>>1"], {})


def test_stale_entries():
    tiers = {"old": {"checked_on": "2026-01-01"}, "new": {"checked_on": "2026-04-01"}}
    assert stale_entries(tiers, date(2026, 4, 11)) == ["old"]


def _plan(tmp_path, triggers):
    p = tmp_path / "stack.json"
    p.write_text(json.dumps({"upgrade_triggers": triggers}), encoding="utf-8")
    return p


def test_strict_exit_code(tmp_path):
    plan = _plan(tmp_path, ["neon:storage_gb>0.8"])
    usage = tmp_path / "usage.json"
    usage.write_text(json.dumps({"neon:storage_gb": 0.95}), encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    (data / "free-tiers.json").write_text(json.dumps({"neon": {"checked_on": date.today().isoformat()}}),
                                          encoding="utf-8")
    args = ["--plan-json", str(plan), "--usage", str(usage), "--data-dir", str(data)]
    assert main(args + ["--strict"]) == 1
    assert main(args) == 0


# v0.1.1 (deferred minor): bad input exits 2 with a message instead of a traceback.
def test_main_malformed_trigger_returns_2(tmp_path, capsys):
    from freetier_check import main
    plan = tmp_path / "stack.json"
    plan.write_text('{"upgrade_triggers": ["not a trigger"]}', encoding="utf-8")
    assert main(["--plan-json", str(plan)]) == 2
    assert "Malformed trigger" in capsys.readouterr().err


def test_main_missing_plan_returns_2(tmp_path, capsys):
    from freetier_check import main
    assert main(["--plan-json", str(tmp_path / "nope.json")]) == 2
    assert "nope.json" in capsys.readouterr().err
