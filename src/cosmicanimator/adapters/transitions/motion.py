# src/cosmicanimator/adapters/transitions/motion.py

"""
Motion transition helpers for CosmicAnimator.

Provides animated movements for scene elements:

- `slide_in`: slide objects from off-screen into place
- `slide_out`: slide objects off-screen (optionally removing them)
- `orbit_around`: orbit an object around a point or another object
- `shake`: shake an object with optional alert color flash

All helpers:
- Use theme-driven sizing (via `Timing`) where appropriate.
- Work with both `VMobject` and `VGroup`.
- Return Manim `Animation` objects ready to be played.
"""

from __future__ import annotations
import numpy as np
from typing import Iterable, Literal
from manim import (
    VGroup,
    VMobject,
    AnimationGroup,
    smooth,
    linear,
    Succession,
    FadeOut,
    TAU,
    UpdateFromAlphaFunc,
    RED,
    config,
    Wait,
)
from .timing import Timing, schedule_items

# Allowed slide directions
Direction = Literal["left", "right", "up", "down"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def offscreen_center_for(mobj: VMobject | VGroup, direction: Direction, margin: float = 0.5):
    """
    Compute an off-screen position for an object so it clears the frame.

    Parameters
    ----------
    mobj : VMobject | VGroup
        Object to move.
    direction : {"left", "right", "up", "down"}
        Off-screen direction.
    margin : float, default=0.5
        Extra spacing beyond the frame edge.

    Returns
    -------
    tuple[float, float, float]
        Target position outside the visible frame.
    """
    fw, fh = config.frame_width, config.frame_height
    x, y, _ = mobj.get_center()
    half_w, half_h = mobj.width / 2, mobj.height / 2

    if direction == "left":
        return (-(fw / 2) - half_w - margin, y, 0)
    if direction == "right":
        return ((fw / 2) + half_w + margin, y, 0)
    if direction == "up":
        return (x, (fh / 2) + half_h + margin, 0)
    return (x, -(fh / 2) - half_h - margin, 0)  # "down"


# ---------------------------------------------------------------------------
# Slide in/out
# ---------------------------------------------------------------------------

def slide_in(
    targets: Iterable[VMobject | VGroup],
    *,
    direction: Direction = "left",
    run_time: float = 0.6,
    rate_func=smooth,
    margin: float = 0.5,
    timing: Timing = Timing(mode="stagger", interval=0.05, order="forward"),
) -> AnimationGroup:
    """
    Slide objects from off-screen into their current positions.

    Parameters
    ----------
    targets : iterable of VMobject | VGroup
        Objects to animate.
    direction : {"left", "right", "up", "down"}, default="left"
        Entry direction.
    run_time : float, default=0.6
        Duration of each slide.
    rate_func : callable, default=smooth
        Easing function.
    margin : float, default=0.5
        Extra spacing beyond frame edge before entry.
    timing : Timing, default=staggered forward
        Controls staggered start times.

    Returns
    -------
    AnimationGroup
        Grouped slide-in animations.
    """
    groups: list[tuple[VGroup, np.ndarray]] = []
    for t in targets:
        g = t if isinstance(t, VGroup) else VGroup(t)
        final_center = g.get_center()
        g.move_to(offscreen_center_for(g, direction, margin))
        groups.append((g, final_center))

    scheduled = schedule_items(groups, timing)

    seqs = [
        Succession(
            Wait(start),
            g.animate(run_time=run_time, rate_func=rate_func).move_to(final_center),
        )
        for (g, final_center), start in scheduled
    ]
    return AnimationGroup(*seqs, lag_ratio=0.0, rate_func=linear)


def slide_out(
    targets: Iterable[VMobject | VGroup],
    *,
    direction: Direction = "right",
    run_time: float = 0.6,
    rate_func=smooth,
    margin: float = 0.5,
    remove: bool = True,
    timing: Timing = Timing(mode="stagger", interval=0.05, order="forward"),
) -> AnimationGroup:
    """
    Slide objects out of frame.

    Parameters
    ----------
    targets : iterable of VMobject | VGroup
        Objects to animate.
    direction : {"left", "right", "up", "down"}, default="right"
        Exit direction.
    run_time : float, default=0.6
        Duration of each slide.
    rate_func : callable, default=smooth
        Easing function.
    margin : float, default=0.5
        Extra spacing beyond frame edge after exit.
    remove : bool, default=True
        If True, remove objects from the scene after exit.
    timing : Timing, default=staggered forward
        Controls staggered start times.

    Returns
    -------
    AnimationGroup
        Grouped slide-out animations.
    """
    groups: list[VGroup] = [t if isinstance(t, VGroup) else VGroup(t) for t in targets]
    scheduled = schedule_items(groups, timing)

    seqs = []
    for g, start in scheduled:
        exit_center = offscreen_center_for(g, direction, margin)
        move = g.animate(run_time=run_time, rate_func=rate_func).move_to(exit_center)
        if remove:
            seqs.append(Succession(Wait(start), move, FadeOut(g, run_time=0.001)))
        else:
            seqs.append(Succession(Wait(start), move))
    return AnimationGroup(*seqs, lag_ratio=0.0, rate_func=linear)


# ---------------------------------------------------------------------------
# Orbit
# ---------------------------------------------------------------------------

def orbit_around(
    target: VMobject | VGroup,
    *,
    center: np.ndarray | None = None,
    around: VMobject | None = None,
    radius: float | None = None,
    start_angle: float | None = None,
    rotations: float = 1.0,
    clockwise: bool = False,
    run_time: float = 2.0,
    rate_func=linear,
    rotate_self: bool = False,
) -> UpdateFromAlphaFunc:
    """
    Orbit an object around a point or another object.

    Parameters
    ----------
    target : VMobject | VGroup
        Object to orbit.
    center : np.ndarray, optional
        Explicit orbit center.
    around : VMobject, optional
        Orbit around another object’s center.
    radius : float, optional
        Radius of orbit. Defaults to current offset.
    start_angle : float, optional
        Starting angle (rad). Defaults to current placement.
    rotations : float, default=1.0
        Number of full rotations.
    clockwise : bool, default=False
        Orbit clockwise if True.
    run_time : float, default=2.0
        Duration of orbit.
    rate_func : callable, default=linear
        Speed profile.
    rotate_self : bool, default=False
        Rotate object about its own center while orbiting.

    Returns
    -------
    UpdateFromAlphaFunc
        Orbit animation.
    """
    # Determine center
    if around is not None:
        c = np.array(around.get_center())
    elif center is not None:
        c = np.array(center)
    else:
        c = np.array([0.0, 0.0, 0.0])

    # Initial offset and radius
    p0 = target.get_center()
    v0 = p0 - c
    r = float(radius) if radius is not None else float(np.linalg.norm(v0[:2]))
    if r == 0:
        raise ValueError("orbit_around(): radius is zero; target at center.")

    # Default start angle
    if start_angle is None:
        start_angle = float(np.arctan2(v0[1], v0[0]))

    direction = -1.0 if clockwise else 1.0
    total_angle = direction * rotations * TAU
    last_alpha = 0.0

    def _update(m: VMobject, alpha: float):
        nonlocal last_alpha
        if rotate_self:
            # Rotate relative to previous frame
            dtheta = (alpha - last_alpha) * total_angle
            if abs(dtheta) > 1e-12:
                m.rotate(dtheta, about_point=c)
            last_alpha = alpha
        else:
            # Compute new position on circle
            ang = start_angle + total_angle * alpha
            new_xy = c[:2] + np.array([np.cos(ang) * r, np.sin(ang) * r])
            new_pos = np.array([new_xy[0], new_xy[1], c[2] if len(c) == 3 else 0.0])
            m.move_to(new_pos)

    return UpdateFromAlphaFunc(target, _update, run_time=run_time, rate_func=rate_func)


# ---------------------------------------------------------------------------
# Shake
# ---------------------------------------------------------------------------

def shake(
    target: VMobject | VGroup,
    *,
    amplitude: float = 0.3,
    shakes: int = 2,
    run_time: float = 0.6,
    rate_func=smooth,
    axis: Literal["horizontal", "vertical"] = "horizontal",
    color_change: bool = True,
    color=RED,
) -> UpdateFromAlphaFunc:
    """
    Shake an object with optional color flash.

    Parameters
    ----------
    target : VMobject | VGroup
        Object to shake.
    amplitude : float, default=0.3
        Maximum displacement.
    shakes : int, default=2
        Number of oscillations.
    run_time : float, default=0.6
        Duration of shake.
    rate_func : callable, default=smooth
        Easing function.
    axis : {"horizontal", "vertical"}, default="horizontal"
        Shake direction.
    color_change : bool, default=True
        If True, recolor during shake.
    color : Manim color, default=RED
        Color used when flashing.

    Returns
    -------
    UpdateFromAlphaFunc
        Shake animation.
    """
    start_center = target.get_center()
    orig_color = target.get_color()

    def _update(m: VMobject, alpha: float):
        # Oscillation around center
        offset = amplitude * np.sin(alpha * shakes * TAU)
        shift = np.array([offset, 0, 0]) if axis == "horizontal" else np.array([0, offset, 0])
        m.move_to(start_center + shift)

        # Handle temporary color change
        if color_change:
            if alpha <= 1e-6:
                m.set_color(color)
            elif alpha >= 1 - 1e-6:
                m.set_color(orig_color)
            else:
                m.set_color(color)
        else:
            if alpha >= 1 - 1e-6:
                m.set_color(orig_color)

    return UpdateFromAlphaFunc(target, _update, run_time=run_time, rate_func=rate_func)
