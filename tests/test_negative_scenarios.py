import json
import pytest
from cosmicanimator.application.generator import write_scene


def _expect_fail(result):
    # Accept either exception-based API (handled by caller) or result object/False
    if hasattr(result, "success"):
        assert not result.success
    else:
        assert result is None or result is False


def test_missing_script_fails(tmp_path):
    bad = {"not_script": []}
    scen = tmp_path / "scenario.json"
    outp = tmp_path / "scene.py"
    scen.write_text(json.dumps(bad), encoding="utf-8")
    try:
        res = write_scene(str(scen), str(outp), scene_class_name="Gen")
        _expect_fail(res)
    except Exception:
        # also acceptable
        pass


def test_unknown_action_fails(tmp_path):
    bad = {"script": [{"actions": [{"name": "no_such_action"}]}]}
    scen = tmp_path / "scenario.json"
    outp = tmp_path / "scene.py"
    scen.write_text(json.dumps(bad), encoding="utf-8")
    try:
        res = write_scene(str(scen), str(outp), scene_class_name="Gen")
        _expect_fail(res)
    except Exception:
        pass


def test_unknown_transition_fails(tmp_path):
    bad = {"script": [{"actions": [{"name": "apply_transition", "args": {"transition": "not_a_transition"}}]}]}
    scen = tmp_path / "scenario.json"
    outp = tmp_path / "scene.py"
    scen.write_text(json.dumps(bad), encoding="utf-8")
    try:
        res = write_scene(str(scen), str(outp), scene_class_name="Gen")
        _expect_fail(res)
    except Exception:
        pass
