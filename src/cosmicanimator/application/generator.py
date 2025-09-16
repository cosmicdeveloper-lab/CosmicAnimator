# src/cosmicanimator/application/generator.py
"""
CosmicAnimator — application/generator
Supports generating a self-contained Manim scene file from either:
  1) a JSON scenario file, or
  2) a Scenario entity (or any Python object) via a mapper → steps

"steps" format (unchanged from your original):
  - list of steps:
      { "line": "...", "action": "fade_in", "args": {...} }
    or
      { "line": "...", "actions": [ {"name": "...", "args": {...}}, ... ] }
  - OR an object: { "script": [ ... ] }

Public API:
  write_scene_from_json(json_path, out_py_path, scene_class_name="Generated")
  write_scene_from_entities(scenario, out_py_path, scene_class_name="Generated", mapper=None)
  write_scene(scenario_or_path, out_py_path, scene_class_name="Generated", mapper=None)
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List, Optional


# --------------------------- internal helpers ---------------------------

def _escape_string(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
         .replace("\"", "\\\"")
         .replace("\n", "\\n")
         .replace("\r", "")
    )


def _normalize_steps(data: Any) -> List[Dict[str, Any]]:
    """Accepts:
       - list[step]
       - dict with 'script': list[step]
    Returns a list[dict].
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("script"), list):
        return data["script"]
    raise ValueError("Scenario must be a list of steps or an object with a 'script' list.")


def _alloc_helper_code() -> str:
    # injected into generated scene
    return """
def _alloc(total, parts):
    parts = max(1, parts)
    raw = max(0.12, total/parts)   # clamp so nothing is too tiny
    scale = total / (raw*parts) if raw*parts > 0 else 1.0
    return [raw*scale]*parts
"""


def _fade_helper_code() -> str:
    return """
def _safe_fade_clear(scene, run_time=0.15, targets=None):
    mobs = list(targets) if targets is not None else list(scene.mobjects)
    if not mobs:
        return
    anims = []
    for m in mobs:
        try:
            # VMobject: fade both fill and stroke (important when filled=False)
            if isinstance(m, VMobject):
                anims.append(m.animate.set_fill(opacity=0).set_stroke(opacity=0))
            # Image/other mobjects that support set_opacity
            elif hasattr(m, "set_opacity"):
                anims.append(m.animate.set_opacity(0))
            else:
                # last resort: tiny scale so it visually disappears
                anims.append(m.animate.scale(0.01))
        except Exception as e:
            pass
    if anims:
        scene.play(*anims, run_time=run_time)
    # ensure nothing keeps running / holding refs
    for m in mobs:
        try:
            m.clear_updaters()
        except Exception:
            pass
    scene.remove(*mobs)
"""


def _gen_common_prelude(lines: List[str], scenario_json_basename: Optional[str]) -> None:
    lines.append("# AUTO-GENERATED FILE — do not edit by hand")
    if scenario_json_basename:
        lines.append(f"# Generated from: {scenario_json_basename}")
    lines.append("")
    lines.append("from manim import *")
    # ✅ use our centralized narration wrapper (Orchestra via ensure_orchestra)
    lines.append("from cosmicanimator.application.narration import VoiceScene, ensure_orchestra")
    lines.append("from cosmicanimator.application.actions import ActionContext, get_action")

    lines.append("")
    lines.append("# Map JSON/entity effect names to actual callables")
    lines.append(_alloc_helper_code())
    lines.append(_fade_helper_code())
    lines.append(
        """
def _resolve_targets_from_ids(ctx: ActionContext, id_list):
    if not id_list:
        return []
    out = []
    for _id in id_list:
        m = ctx.store.get(_id)
        if m is None:
            print(f"[warn] target id '{_id}' not found in ctx.store")
        else:
            out.append(m)
    return out

def _apply_effect_animations(self, ctx: ActionContext, res, effect_specs):
    \"\"\"Return a list[Animation] from effect_specs.
    Each spec: {'name': str, 'args': {...}, 'targets': [ids]? }
    - If 'targets' omitted -> use [res.group] if present.
    - Camera effects ('zoom_to','pan_to','zoom_out') receive 'self' scene.
    \"\"\"
    if not effect_specs:
        return []

    anims = []
    for spec in effect_specs:
        name = spec.get('name')
        args = spec.get('args') or {}
        targets_ids = spec.get('targets')
        targets = _resolve_targets_from_ids(ctx, targets_ids) if targets_ids else ([res.group] if getattr(res, 'group', None) is not None else [])

        if name in ('zoom_to', 'pan_to', 'zoom_out'):
            if name == 'zoom_out':
                anims.append(TRANSITION_REGISTRY[name](self, **args))
            else:
                for t in (targets or []):
                    anims.append(TRANSITION_REGISTRY[name](self, t, **args))
            continue

        fx = TRANSITION_REGISTRY.get(name)
        if fx is None:
            print(f"[warn] effect '{name}' not found")
            continue

        if targets:
            try:
                anim = fx(targets, **args)  # group-style functions
                anims.append(anim)
            except Exception:
                for t in targets:
                    try:
                        anims.append(fx(t, **args))  # single-target fallback
                    except Exception as e:
                        print(f"[warn] effect '{name}' failed for target: {e}")
        else:
            try:
                anims.append(fx(**args))
            except Exception:
                print(f"[warn] effect '{name}' needs targets but none were provided")
    return anims
"""
    )


def _emit_scene_body(lines: List[str], steps: List[Dict[str, Any]], scene_class_name: str) -> None:
    FADE_OUT_TIME = 0.10  # quick clear between narrated lines
    lines.append(f"class {scene_class_name}(MovingCameraScene, VoiceScene):")
    lines.append("    def construct(self):")
    # Configure narrator defaults (your VoiceScene can wire to Coqui, etc.)
    lines.append("        self.configure_voice()")
    lines.append("        ctx = ActionContext(scene=self, store={}, theme={})")
    lines.append("")

    for idx, step in enumerate(steps):
        # Normalize step -> actions list
        line_text = (step.get("line") or "").strip()
        actions_list = step.get("actions")
        if actions_list is None:
            action = step.get("action")
            if action is None:
                actions_list = []
            else:
                aargs = step.get("args") or {}
                actions_list = [{"name": action, "args": aargs}]

        # At generation time, detect whether this step contains an explicit 'narrate' action
        has_narrate = any((isinstance(a, dict) and a.get("name") == "narrate") for a in actions_list)

        # Emit per-step prologue
        lines.append(f"        # --- Step {idx + 1} ---")
        lines.append("        if self.mobjects:")
        lines.append(f"            _safe_fade_clear(self, run_time={FADE_OUT_TIME})")

        esc_line = _escape_string(line_text)

        if (line_text and not has_narrate):
            # Implicit narration: start audio+subs, then play actions concurrently inside the block
            lines.append("        _orch = ensure_orchestra(self)")
            lines.append(f"        with _orch.narrate(\"{esc_line}\") as _trk:")
            lines.append("            _dur = float(getattr(_trk, 'duration', 0.0))")

            if not actions_list:
                lines.append("            if _dur > 0:")
                lines.append("                self.wait(_dur)")
                lines.append("            ")  # blank line
                lines.append("            # (no actions in this step)")
                continue

            lines.append(f"            _durations = _alloc(_dur, {len(actions_list)})")
            # ↓↓↓ emit your action calls here, INDENTED to live inside the with-block ↓↓↓
            for i, a in enumerate(actions_list):
                lines.append("            _args = " + repr((a.get('args') or {})))
                lines.append("            _effects = _args.pop('effects', None)")
                lines.append(f"            _act = get_action({a.get('name')!r})")
                lines.append("            _res = _act(ctx, **_args)")
                lines.append(
                    "            _anims_main = list(_res.animations) if getattr(_res, 'animations', None) else []")
                lines.append("            _anims_fx = _apply_effect_animations(self, ctx, _res, _effects)")
                lines.append(f"            _t = _durations[{i}]")
                lines.append("            if _anims_main and _anims_fx:")
                lines.append("                self.play(*_anims_main, run_time=_t*0.6)")
                lines.append("                self.play(*_anims_fx, run_time=_t*0.4)")
                lines.append("            elif _anims_main:")
                lines.append("                self.play(*_anims_main, run_time=_t)")
                lines.append("            elif _anims_fx:")
                lines.append("                self.play(*_anims_fx, run_time=_t)")
                lines.append("            if getattr(_res, 'postwait', 0.0):")
                lines.append("                self.wait(_res.postwait)")

        else:
            # No implicit narration (either no line, or explicit 'narrate' action will handle audio)
            lines.append("        _dur = 0.0")
            if not actions_list:
                lines.append("        # (no actions and no implicit narration)")
                lines.append("        pass")
                lines.append("")
                # no continue here; nothing else to emit
            else:
                lines.append(f"        _durations = _alloc(_dur, {len(actions_list)})")
                # ↓↓↓ emit your action calls here (normal indentation, outside any with-block) ↓↓↓
                for i, a in enumerate(actions_list):
                    lines.append("        _args = " + repr((a.get('args') or {})))
                    lines.append("        _effects = _args.pop('effects', None)")
                    lines.append(f"        _act = get_action({a.get('name')!r})")
                    lines.append("        _res = _act(ctx, **_args)")
                    lines.append(
                        "        _anims_main = list(_res.animations) if getattr(_res, 'animations', None) else []")
                    lines.append("        _anims_fx = _apply_effect_animations(self, ctx, _res, _effects)")
                    lines.append(f"        _t = _durations[{i}]")
                    lines.append("        if _anims_main and _anims_fx:")
                    lines.append("            self.play(*_anims_main, run_time=_t*0.6)")
                    lines.append("            self.play(*_anims_fx, run_time=_t*0.4)")
                    lines.append("        elif _anims_main:")
                    lines.append("            self.play(*_anims_main, run_time=_t)")
                    lines.append("        elif _anims_fx:")
                    lines.append("            self.play(*_anims_fx, run_time=_t)")
                    lines.append("        if getattr(_res, 'postwait', 0.0):")
                    lines.append("            self.wait(_res.postwait)")

        lines.append("")


def _write_file(out_py_path: str, content: str) -> None:
    os.makedirs(os.path.dirname(out_py_path) or ".", exist_ok=True)
    with open(out_py_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Wrote {out_py_path}")


# ------------------------------ Public API ------------------------------

def write_scene_from_json(scenario_json_path: str, out_py_path: str, scene_class_name: str = "Generated") -> None:
    """Original behavior: read JSON → generate a Manim scene file."""
    with open(scenario_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    steps = _normalize_steps(data)

    lines: List[str] = []
    _gen_common_prelude(lines, scenario_json_basename=os.path.basename(scenario_json_path))
    _emit_scene_body(lines, steps, scene_class_name=scene_class_name)
    _write_file(out_py_path, "\n".join(lines))


def write_scene_from_entities(
    scenario: Any,
    out_py_path: str,
    scene_class_name: str = "Generated",
    mapper: Optional[Callable[[Any], List[Dict[str, Any]]]] = None,
) -> None:
    """
    Entity-driven flow: scenario → steps → file.
    - mapper(scenario) MUST return the same 'steps' structure accepted by _normalize_steps.
    - If mapper is None, we try a few common patterns:
        * scenario.script : list[step]
        * scenario.steps  : list[step]
        * dict with 'script'
        * list already in step format
    """
    if mapper is not None:
        steps = mapper(scenario)
    else:
        # heuristic defaults to keep you moving quickly
        if hasattr(scenario, "script"):
            steps = _normalize_steps(getattr(scenario, "script"))
        elif hasattr(scenario, "steps"):
            steps = _normalize_steps(getattr(scenario, "steps"))
        elif isinstance(scenario, (list, dict)):
            steps = _normalize_steps(scenario)
        else:
            raise TypeError(
                "No mapper provided and scenario doesn't expose .script/.steps or list/dict structure."
            )

    lines: List[str] = []
    _gen_common_prelude(lines, scenario_json_basename=None)
    _emit_scene_body(lines, steps, scene_class_name=scene_class_name)
    _write_file(out_py_path, "\n".join(lines))


def write_scene(
    scenario_or_path: Any,
    out_py_path: str,
    scene_class_name: str = "Generated",
    mapper: Optional[Callable[[Any], List[Dict[str, Any]]]] = None,
) -> None:
    """
    Convenience wrapper:
      - If given a string path → treat as JSON.
      - Else → treat as entities and use mapper (or heuristics).
    """
    if isinstance(scenario_or_path, str) and scenario_or_path.lower().endswith((".json", ".JSON")):
        return write_scene_from_json(scenario_or_path, out_py_path, scene_class_name=scene_class_name)
    return write_scene_from_entities(scenario_or_path, out_py_path, scene_class_name=scene_class_name, mapper=mapper)
