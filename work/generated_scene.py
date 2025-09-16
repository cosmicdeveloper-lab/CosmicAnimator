# AUTO-GENERATED FILE — do not edit by hand
# Generated from: scenario.json

from manim import *
from cosmicanimator.application.narration import VoiceScene, ensure_orchestra
from cosmicanimator.application.actions import ActionContext, get_action

# Map JSON/entity effect names to actual callables

def _alloc(total, parts):
    parts = max(1, parts)
    raw = max(0.12, total/parts)   # clamp so nothing is too tiny
    scale = total / (raw*parts) if raw*parts > 0 else 1.0
    return [raw*scale]*parts


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
    """Return a list[Animation] from effect_specs.
    Each spec: {'name': str, 'args': {...}, 'targets': [ids]? }
    - If 'targets' omitted -> use [res.group] if present.
    - Camera effects ('zoom_to','pan_to','zoom_out') receive 'self' scene.
    """
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

class Generated(MovingCameraScene, VoiceScene):
    def construct(self):
        self.configure_voice()
        ctx = ActionContext(scene=self, store={}, theme={})

        # --- Step 1 ---
        if self.mobjects:
            _safe_fade_clear(self, run_time=0.1)
        _orch = ensure_orchestra(self)
        with _orch.narrate("Welcome to CosmicAnimator!") as _trk:
            _dur = float(getattr(_trk, 'duration', 0.0))
            _durations = _alloc(_dur, 1)
            _args = {'text': 'CosmicAnimator', 'color': 'accent'}
            _effects = _args.pop('effects', None)
            _act = get_action('render_title')
            _res = _act(ctx, **_args)
            _anims_main = list(_res.animations) if getattr(_res, 'animations', None) else []
            _anims_fx = _apply_effect_animations(self, ctx, _res, _effects)
            _t = _durations[0]
            if _anims_main and _anims_fx:
                self.play(*_anims_main, run_time=_t*0.6)
                self.play(*_anims_fx, run_time=_t*0.4)
            elif _anims_main:
                self.play(*_anims_main, run_time=_t)
            elif _anims_fx:
                self.play(*_anims_fx, run_time=_t)
            if getattr(_res, 'postwait', 0.0):
                self.wait(_res.postwait)

        # --- Step 2 ---
        if self.mobjects:
            _safe_fade_clear(self, run_time=0.1)
        _orch = ensure_orchestra(self)
        with _orch.narrate("Here are three processes Highlight the middle process.") as _trk:
            _dur = float(getattr(_trk, 'duration', 0.0))
            _durations = _alloc(_dur, 2)
            _args = {'count': 3, 'labels': ['Process A', 'Process B', 'Process C'], 'direction': 'row'}
            _effects = _args.pop('effects', None)
            _act = get_action('layout_boxes')
            _res = _act(ctx, **_args)
            _anims_main = list(_res.animations) if getattr(_res, 'animations', None) else []
            _anims_fx = _apply_effect_animations(self, ctx, _res, _effects)
            _t = _durations[0]
            if _anims_main and _anims_fx:
                self.play(*_anims_main, run_time=_t*0.6)
                self.play(*_anims_fx, run_time=_t*0.4)
            elif _anims_main:
                self.play(*_anims_main, run_time=_t)
            elif _anims_fx:
                self.play(*_anims_fx, run_time=_t)
            if getattr(_res, 'postwait', 0.0):
                self.wait(_res.postwait)
            _args = {'pipeline': [{'name': 'highlight_shapes'}], 'target_ids': ['process_b']}
            _effects = _args.pop('effects', None)
            _act = get_action('apply_transition')
            _res = _act(ctx, **_args)
            _anims_main = list(_res.animations) if getattr(_res, 'animations', None) else []
            _anims_fx = _apply_effect_animations(self, ctx, _res, _effects)
            _t = _durations[1]
            if _anims_main and _anims_fx:
                self.play(*_anims_main, run_time=_t*0.6)
                self.play(*_anims_fx, run_time=_t*0.4)
            elif _anims_main:
                self.play(*_anims_main, run_time=_t)
            elif _anims_fx:
                self.play(*_anims_fx, run_time=_t)
            if getattr(_res, 'postwait', 0.0):
                self.wait(_res.postwait)
