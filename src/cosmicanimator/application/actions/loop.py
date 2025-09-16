# src/cosmicanimator/application/actions/loop.py

"""
Action: render a looping curved arrow orbiting around a target.

Registers
---------
- `render_loop` : draws a curved arrow arc around a target object,
  then animates it orbiting the target.

Notes
-----
- Arc span/orientation are controlled via `span_degrees` and `base_angle`.
- Orbit uses `orbit_around` transition, with optional clockwise motion.
"""

from __future__ import annotations
from typing import Optional, Dict
import numpy as np
from manim import Mobject
from manim import rate_functions as rf

from .base import ActionContext, ActionResult, register
from cosmicanimator.adapters.style import curved_arrow
from cosmicanimator.adapters.transitions.motion import orbit_around


@register("render_loop")
def render_loop(
    ctx: ActionContext,
    *,
    target: Mobject | None = None,      # direct object reference
    target_id: str | None = None,       # JSON-friendly lookup from ctx.store
    padding: float = 0.30,
    span_degrees: float = 300.0,
    base_angle: float = -np.pi / 2,
    curvature: float = -0.8,
    color: Optional[str] = "muted",
    stroke_width: Optional[float] = None,
    revolutions: float = 1.0,
    run_time: float = 2.0,
    clockwise: bool = True,
    rate_func=rf.linear,
    id: str | None = None,              # optional ID for storing the loop arrow
) -> ActionResult:
    """
    Render a curved arrow loop around a target and animate its orbit.

    Parameters
    ----------
    ctx : ActionContext
        Provides scene, theme, and store.
    target : Mobject, optional
        Direct target object (overrides `target_id`).
    target_id : str, optional
        ID to resolve target from `ctx.store`.
    padding : float, default=0.30
        Extra distance beyond target radius to place the loop.
    span_degrees : float, default=300.0
        Angular span of arc (degrees). 360° = full circle.
    base_angle : float, default=-π/2
        Central orientation of arc (radians).
        -π/2 points downward.
    curvature : float, default=-0.8
        Curvature passed to `curved_arrow`.
    color : str, default="muted"
        Arrow stroke/glow color (theme role or hex).
    stroke_width : float, optional
        Arrow stroke width override.
    revolutions : float, default=1.0
        Number of orbits to complete.
    run_time : float, default=2.0
        Duration of orbit animation (seconds).
    clockwise : bool, default=True
        If True, orbit clockwise; else counter-clockwise.
    rate_func : Callable, default=rf.linear
        Easing function for orbit animation.
    id : str, optional
        ID to store the loop arrow in ctx.store.

    Returns
    -------
    ActionResult
        - group : loop arrow group
        - ids : dict mapping id → arrow (if provided)
        - animations : orbit animation list
    """
    # Resolve target
    tgt = target or (ctx.store.get(target_id) if target_id else None)
    if tgt is None:
        raise ValueError("render_loop: provide `target` or `target_id` (must exist in ctx.store)")

    # Compute radius and arc endpoints
    radius = 0.5 * max(tgt.width, tgt.height) + padding
    C = tgt.get_center()
    half_span = np.deg2rad(span_degrees) / 2.0
    theta_start = base_angle - half_span
    theta_end = base_angle + half_span

    def _pt(r, th):
        return C + np.array([r * np.cos(th), r * np.sin(th), 0.0])

    start_pt, end_pt = _pt(radius, theta_start), _pt(radius, theta_end)

    # Build curved arrow
    loop_group = curved_arrow(
        start=start_pt,
        end=end_pt,
        angle=curvature,
        color=color,
        stroke_width=stroke_width,
    )

    # Animate orbit
    anim = orbit_around(
        loop_group,
        around=tgt,
        rotations=revolutions,
        run_time=run_time,
        clockwise=clockwise,
        rate_func=rate_func,
        rotate_self=True,
    )

    ids: Dict[str, Mobject] = {}
    if id:
        ids[id] = loop_group

    return ActionResult(group=loop_group, ids=ids, animations=[anim])
