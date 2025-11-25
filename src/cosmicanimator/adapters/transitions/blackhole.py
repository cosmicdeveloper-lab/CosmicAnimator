# src/cosmicanimator/adapters/transitions/blackhole.py

"""
Black hole and space-themed transition utilities for Manim.

This module provides:
- `_gaussian_haze`: builds a rotating, multi-arc haze VGroup.
- `blackhole`: composes a background horizon + haze and animates
   targets collapsing into a beam of light with gentle haze squeezing.
- `hawking_radiation`: transforms a target into a cloud of outward
   moving dots (stylized Hawking radiation).
"""

import random
import numpy as np
from manim import (
    Scene, VGroup, VMobject, Mobject, Circle, Arc, Line, Dot,
    FadeOut, FadeToColor, FadeTransform, AnimationGroup, Succession,
    Transform, Rotate, interpolate_color, ORIGIN, OUT, IN, UP, LEFT,
    RIGHT, TAU, PI, DEGREES, WHITE, ORANGE, BLUE_E, BLACK, linear
)


def _gaussian_haze(
    *,
    center_radius: float = 2.05,
    r_min: float = 1.00,
    r_max: float = 2.6,
    n_lines: int = 420,
    base_color=WHITE,
    warm_tint=ORANGE,
    cool_tint=BLUE_E,
    width_range: tuple[float, float] = (0.6, 1.8),
    opacity_range: tuple[float, float] = (0.06, 0.32),
    angle_len_range: tuple[float, float] = (0.55 * PI, 1.75 * PI),
    seed: int = 7,
    spin: bool = True,
    spin_speed: float = 0.2,  # radians per second
) -> VGroup:
    """
    Create a hazy ring made of many faint arcs with optional slow spin.
    """
    random.seed(seed)
    group = VGroup()

    for _ in range(n_lines):
        r = random.gauss(center_radius, 0.28)
        r = max(r_min, min(r_max, r))
        r += random.uniform(-0.01, 0.01)

        theta0 = random.uniform(0, TAU)
        dtheta = random.uniform(*angle_len_range) * random.choice([1, -1])

        t = (r - r_min) / (r_max - r_min + 1e-9)
        mid_color = interpolate_color(base_color, warm_tint, 0.25)
        tint_in = interpolate_color(base_color, mid_color, 0.55)
        tint_out = interpolate_color(base_color, cool_tint, 0.35)
        color = interpolate_color(tint_in, tint_out, t)

        width = random.uniform(*width_range)
        opac = random.uniform(*opacity_range) * (
            0.8 + 0.6 * (1 - abs(r - center_radius) / (r_max - center_radius + 1e-9))
        )

        arc = (
            Arc(start_angle=theta0, angle=dtheta, radius=r)
            .set_stroke(color, width=width, opacity=opac)
            .set_fill(opacity=0)
        )

        arc.scale(1.0 + random.uniform(-0.004, 0.004), about_point=ORIGIN)
        group.add(arc)

    if spin:
        group.add_updater(lambda m, dt: m.rotate(spin_speed * dt, axis=OUT))

    return group


def blackhole(scene: Scene, targets) -> AnimationGroup:
    """
    Build a black hole background and return an animation that collapses
    each object in `target` into a streak of light while the haze spins.
    """
    horizon = (
        Circle(radius=1.94)
        .set_fill(BLACK, 1)
        .set_stroke(BLACK, 0)
        .shift(UP * 2)
    )
    horizon.set_z(-4, OUT).set_z_index(-2)

    haze = _gaussian_haze()
    haze.set_z_index(-1)
    haze.shift(IN * 0.2)

    scene.add(horizon, haze)

    light = (
        Line(start=LEFT * 4, end=RIGHT * 4, color=WHITE, stroke_width=6)
        .set_opacity(0.0)
        .move_to(ORIGIN)
    )
    light.rotate(-50 * DEGREES, axis=UP).rotate(10 * DEGREES, axis=RIGHT)

    anims = []
    for target in targets:
        for t in target:
            collapse = Transform(t, light)
            appear = light.animate.set_opacity(0.9).scale(0.15).shift(IN * 0.6)
            push = light.animate.shift(IN * 2.0).scale(0.25)
            fade = FadeOut(light, shift=IN * 0.8)

            anims.append(
                Succession(
                    AnimationGroup(collapse, appear, run_time=2.0),
                    push,
                    fade,
                )
            )

    anim = AnimationGroup(*anims, lag_ratio=0.1)

    spin_speed = 0.75
    spin_rt = 12.0
    spin = Rotate(
        haze,
        angle=spin_speed * spin_rt,
        axis=OUT,
        rate_func=linear,
        run_time=spin_rt,
    )

    return AnimationGroup(anim, spin, lag_ratio=0.0)


def hawking_radiation(
    targets: Mobject | VGroup,
    n_particles: int = 40,
    radius: float = 0.03,
    spread: float = 1.4,
) -> AnimationGroup:
    """
    Transform the target into a cloud of outward-moving dots (stylized radiation).
    """
    dots = VGroup()
    transform = []
    fade = []

    for target in targets:
        for t in target.submobjects if isinstance(target, VGroup) else [target]:
            center = t.get_center()
            half_w = t.get_width() / 2
            half_h = t.get_height() / 2
            max_dim = max(half_w, half_h)

            for _ in range(n_particles):
                direction = np.array([random.uniform(-1, 1), random.uniform(-1, 1), 0.0])
                direction /= np.linalg.norm(direction) + 1e-9
                offset = direction * random.uniform(max_dim * 1.0, max_dim * spread)

                p = Dot(radius=radius, color=t.get_color()).set_opacity(0.8)
                p.move_to(center + offset)
                dots.add(p)

        transform.append(FadeTransform(target, dots))
        fade.append(FadeToColor(dots, BLACK))

    return AnimationGroup(transform, fade)
