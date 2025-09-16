# src/cosmicanimator/application/actions/effects.py

"""
Action: apply visual transitions in a uniform, scene-bound way.

Design
------
- At registry-build time, the current `scene` is injected into camera transitions.
- All transitions are exposed through the same call signature:

    fn(targets: list[VMobject], **kwargs) -> Animation

Types
-----
- Group transitions: operate on the entire list of targets.
- Single transitions: operate on the first target only.
- Camera transitions: require the scene; use first target if relevant.

This uniform shape simplifies pipelines of transitions, since every callable
looks the same.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Iterable
from manim import VGroup, VMobject, Animation, Succession
from cosmicanimator.application.actions.base import ActionContext, ActionResult, register
from cosmicanimator.adapters.transitions import (
    # group-style (list[VMobject] -> Animation)
    fade_in_group, fade_out_group, ghost_shapes,
    highlight_shapes, focus_on_shape,
    slide_in, slide_out,
    ripple_effect,

    # single-style (VMobject -> Animation)
    orbit_around, shake,

    # camera-style (scene[, target] -> Animation)
    zoom_to, zoom_out, pan_to,
)


# ---------------------------------------------------------------------------
# Target resolvers
# ---------------------------------------------------------------------------

def _resolve_many(store: Dict[str, VMobject], ids: Iterable[str]) -> List[VMobject]:
    """Resolve multiple IDs from ctx.store → VMobjects."""
    resolved: List[VMobject] = []
    for i in ids:
        if i not in store:
            raise KeyError(f"apply_transition: id '{i}' not found in ctx.store")
        resolved.append(store[i])
    return resolved


def _resolve_one(store: Dict[str, VMobject], i: Optional[str]) -> VMobject:
    """Resolve a single ID from ctx.store (strict)."""
    if not i:
        raise ValueError("apply_transition: 'target_id' is required for this transition")
    if i not in store:
        raise KeyError(f"apply_transition: id '{i}' not found in ctx.store")
    return store[i]


def _all_store_targets(ctx: ActionContext) -> List[VMobject]:
    """
    Deterministic "all shapes" fallback.

    Priority
    --------
    1. All ctx.store values (stable order by key).
    2. If store is empty, all VMobjects currently in scene.
    """
    keys = [k for k, v in ctx.store.items() if isinstance(v, VMobject)]
    keys.sort()
    out = [ctx.store[k] for k in keys]
    if out:
        return out
    return [m for m in ctx.scene.mobjects if isinstance(m, VMobject)]


# ---------------------------------------------------------------------------
# Scene-bound transition registry
# ---------------------------------------------------------------------------

def _require_first(targets: List[VMobject]) -> VMobject:
    """Helper: return first target or raise if empty."""
    if not targets:
        raise ValueError("Transition requires at least one target, but none provided.")
    return targets[0]


def make_transitions(ctx: ActionContext) -> Dict[str, Any]:
    """
    Build scene-bound transition callables with uniform signatures.

    Returns
    -------
    dict[str, Callable]
        Mapping of transition names to functions of shape:
            fn(targets: list[VMobject], **kwargs) -> Animation
    """
    # Adapt signatures to the uniform call shape
    def as_group(fn_group):
        return lambda targets, **kw: fn_group(targets, **kw)

    def as_single(fn_single):
        return lambda targets, **kw: fn_single(_require_first(targets), **kw)

    def cam_with_target(fn_cam):
        return lambda targets, **kw: fn_cam(ctx.scene, _require_first(targets), **kw)

    def cam_no_target(fn_cam):
        return lambda targets, **kw: fn_cam(ctx.scene, **kw)

    return {
        # Group transitions
        "fade_in_group":    as_group(fade_in_group),
        "fade_out_group":   as_group(fade_out_group),
        "ghost_shapes":     as_group(ghost_shapes),
        "highlight_shapes": as_group(highlight_shapes),
        "focus_on_shape":   as_group(focus_on_shape),
        "slide_in":         as_group(slide_in),
        "slide_out":        as_group(slide_out),
        "ripple_effect":    as_group(ripple_effect),

        # Single-target transitions
        "orbit_around":     as_single(orbit_around),
        "shake":            as_single(shake),

        # Camera transitions
        "zoom_to":          cam_with_target(zoom_to),
        "zoom_out":         cam_no_target(zoom_out),
        "pan_to":           cam_with_target(pan_to),
    }


# ---------------------------------------------------------------------------
# Action: apply_transition
# ---------------------------------------------------------------------------

@register("apply_transition")
def apply_transition(
    ctx: ActionContext,
    *,
    transition: Optional[str] = None,                 # one-shot
    args: Optional[Dict[str, Any]] = None,            # kwargs for single transition
    pipeline: Optional[List[Dict[str, Any]]] = None,  # sequence of {name, args}
    target_ids: Optional[List[str]] = None,           # explicit multiple targets
    target_id: Optional[str] = None,                  # convenience single target
) -> ActionResult:
    """
    Apply one or more transition helpers by name.

    Parameters
    ----------
    ctx : ActionContext
        Provides scene and store.
    transition : str, optional
        Transition name for a single call.
    args : dict, optional
        Arguments for the single transition.
    pipeline : list[dict], optional
        List of steps {name, args} to chain sequentially.
    target_ids : list[str], optional
        IDs of targets from ctx.store.
    target_id : str, optional
        Shortcut for single target.

    Returns
    -------
    ActionResult
        - group : VGroup of all targets
        - ids : {}
        - animations : [Animation]
    """
    if not transition and not pipeline:
        raise ValueError("apply_transition: provide either 'transition' or 'pipeline'.")

    registry = make_transitions(ctx)

    # Resolve targets once
    if target_ids:
        targets = _resolve_many(ctx.store, target_ids)
    elif target_id:
        targets = [_resolve_one(ctx.store, target_id)]
    else:
        targets = _all_store_targets(ctx)

    # Pipeline
    if pipeline:
        anims: List[Animation] = []
        for step in pipeline:
            name = step.get("name")
            kargs = step.get("args", {}) or {}
            fn = registry.get(name)
            if not fn:
                raise KeyError(f"apply_transition: unknown transition '{name}'")
            anims.append(fn(targets, **kargs))
        seq = Succession(*anims)
        return ActionResult(group=VGroup(*targets), ids={}, animations=[seq])

    # Single transition
    fn = registry.get(transition)
    if not fn:
        raise KeyError(f"apply_transition: unknown transition '{transition}'")
    anim = fn(targets, **(args or {}))
    return ActionResult(group=VGroup(*targets), ids={}, animations=[anim])
