import importlib.util
import json
from pathlib import Path
from cosmicanimator.application.generator import write_scene_from_json


def _import_module_from_path(module_path: Path):
    spec = importlib.util.spec_from_file_location("generated_scene", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_generate_scene_file_importable(tmp_path):
    scen = {"script": [{"actions": [{"name": "layout_branch", "args": {"child_count": 2}}]}]}
    scen_path = tmp_path / "scenario.json"
    out_path = tmp_path / "scene_generated.py"
    scen_path.write_text(json.dumps(scen), encoding="utf-8")

    write_scene_from_json(str(scen_path), str(out_path), scene_class_name="Gen")
    assert out_path.exists()
    mod = _import_module_from_path(out_path)
    assert hasattr(mod, "Gen")
