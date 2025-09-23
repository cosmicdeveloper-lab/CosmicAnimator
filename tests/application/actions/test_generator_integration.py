import json
from pathlib import Path
from cosmicanimator.application.generator import write_scene_from_json


def test_write_scene_from_json(tmp_path):
    scen = {"script": [{"actions": [{"name": "layout_branch", "args": {"child_count": 1}}]}]}
    scen_path = tmp_path / "scenario.json"
    out_path = tmp_path / "generated_scene.py"
    scen_path.write_text(json.dumps(scen), encoding="utf-8")

    # file-writing API returns None, but should create the file
    write_scene_from_json(str(scen_path), str(out_path), scene_class_name="Auto")
    assert out_path.exists()
