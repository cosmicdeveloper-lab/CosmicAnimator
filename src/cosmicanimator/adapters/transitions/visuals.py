# src/cosmicanimator/adapters/transitions/visuals.py

"""
Visual effects utilities for Manim.

Includes:
- `shine`: pulsing glow transformation.
- `spin`: continuous rotation with automatic stop timer.
"""

from __future__ import annotations
import numpy as np
from manim import (
    VMobject, VGroup, ValueTracker, Animation, AnimationGroup,
    Transform, UP
)
from cosmicanimator.adapters.style import add_glow_layers


def shine(targets: list[VMobject | VGroup]) -> AnimationGroup:
    """
    Create a pulsing glow effect by alternating between target and its glow layers.

    Parameters
    ----------
    targets
        Iterable of Manim objects to apply the shine effect to.

    Returns
    -------
    AnimationGroup
        Combined pulse animation for all targets.
    """
    animations = []
    for target in targets:
        glow = add_glow_layers(
            target,
            bands=[
                (1.0, 0.15),
                (1.8, 0.06),
                (3.2, 0.025),
                (6.0, 0.010),
                (9.0, 0.005),
            ],
            count=5,
            spread=2.0,
            max_opacity=0.20,
        )
        animations.append(Transform(target, glow))
        animations.append(Transform(glow, target))

    return AnimationGroup(*animations)


def spin(
    targets: list[VMobject | VGroup],
    *,
    angular_speed_deg_per_sec: float = 220.0,
    axis=UP,
    run_time: float = 3.0,
) -> Animation:
    """
    Apply continuous rotation updaters to targets for a set duration.

    Parameters
    ----------
    targets
        Manim objects to spin.
    angular_speed_deg_per_sec
        Rotation speed in degrees per second.
    axis
        Axis to rotate around (default: UP).
    run_time
        Duration before automatically stopping rotation.

    Returns
    -------
    Animation
        Wait-like animation that keeps updaters active for `run_time`.
    """

    def _flatten(obj):
        if isinstance(obj, (list, tuple, VGroup)):
            out = []
            for x in obj:
                out.extend(_flatten(x))
            return out
        return [obj]

    items = _flatten(targets)
    omega = np.deg2rad(angular_speed_deg_per_sec)

    for t in items:
        t.add_updater(lambda m, dt, ax=axis: m.rotate(omega * dt, axis=ax))

    timer = ValueTracker(0)

    def advance_timer(m, dt):
        m.increment_value(dt)
        if m.get_value() >= run_time:
            for t in items:
                t.clear_updaters()
            m.clear_updaters()

    timer.add_updater(advance_timer)
    return Animation(timer, run_time=run_time)
