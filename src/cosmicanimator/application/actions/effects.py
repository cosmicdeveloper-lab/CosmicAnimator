# src/cosmicanimator/application/actions/effects.py

"""
Action: apply visual transitions in a uniform, scene-bound way.

Design
------
- At registry-build time, the current `scene` is injected into camera transitions.
- All transitions share the same call signature:
    fn(targets: list[VMobject], **kwargs) -> Animation

Types
-----
- Group transitions: operate on all targets together.
- Single transitions: operate on the first target only.
- Camera transitions: require the scene; may use the first target.

This design allows a consistent transition pipeline interface.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Iterable, Callable
from manim import VGroup, VMobject, Animation, Succession
from cosmicanimator.application.actions.base import ActionContext, ActionResult, register
from cosmicanimator.adapters.transitions import (
    blackhole,
    pulsar,
    hawking_radiation,
    shooting_star,
    spin,
    shine,
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
    1. All ctx.store values (sorted by key).
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


def make_transitions(ctx: ActionContext) -> Dict[str, Callable]:
    """
    Build scene-bound transition callables with uniform signatures.

    Returns
    -------
    dict[str, Callable]
        Mapping of transition names to callables with shape:
            fn(targets: list[VMobject], **kwargs) -> Animation
    """

    def as_group(fn_group):
        return lambda targets, **kw: fn_group(targets, **kw)

    def as_single(fn_single):
        return lambda targets, **kw: fn_single(_require_first(targets), **kw)

    def cam_with_target(fn_cam):
        return lambda targets, **kw: fn_cam(ctx.scene, _require_first(targets), **kw)

    def cam_with_targets(fn_cam):
        return lambda targets, **kw: fn_cam(ctx.scene, targets, **kw)

    def cam_no_target(fn_cam):
        return lambda targets, **kw: fn_cam(ctx.scene, **kw)

    return {
        "blackhole": cam_with_targets(blackhole),
        "pulsar": cam_with_target(pulsar),
        "hawking_radiation": as_group(hawking_radiation),
        "shooting_star": cam_no_target(shooting_star),
        "spin": as_group(spin),
        "shine": as_group(shine),
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
    target_id: Optional[str] = None,                  # single target shortcut
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
        Shortcut for a single target.

    Returns
    -------
    ActionResult
        Result containing:
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

    # Pipeline mode
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
