# src/cosmicanimator/adapters/transitions/stars.py

"""
Star and pulsar-related effects for Manim.

Includes:
- `shooting_star`: animates a star streaking across the scene.
- `pulsar`: creates dynamic DNA-like glowing strands around a target.
"""

import math
import random
import numpy as np
from manim import (
    ThreeDScene, VMobject, VGroup, ValueTracker, Line, Dot, Text, MarkupText,
    MathTex, FadeOut, AnimationGroup, Succession, Wait, smooth, DOWN, UP, PI,
    ORIGIN, LEFT, RIGHT, WHITE
)
from cosmicanimator.adapters.style import add_glow_layers
from cosmicanimator.core.theme import current_theme as t


def shooting_star(
    scene: ThreeDScene,
    start=(7.2, 3.8, -1.2),
    end=(-7.2, -3.8, -1.2),
    color=WHITE,
    run_time=1.8,
    delay=0.0,
) -> Succession:
    """
    Add a shooting star animation across the scene.

    Parameters
    ----------
    scene : ThreeDScene
        The active scene.
    start, end : tuple
        3D coordinates defining the star’s trajectory.
    color : ManimColor
        Star color.
    run_time : float
        Duration of travel.
    delay : float
        Delay before starting motion.
    """
    star = Dot(radius=0.03, color=color).set_opacity(0.9).move_to(start)
    trail = VMobject().set_stroke(color, width=2.5, opacity=0.3)

    def _update_trail(mob):
        mob.become(
            Line(star.get_center(), start, color=color, stroke_opacity=0.3, stroke_width=2.5)
        )

    trail.add_updater(_update_trail)
    scene.add(trail, star)

    if delay:
        scene.wait(delay)

    anim = AnimationGroup(
        star.animate.move_to(end),
        rate_func=lambda t: smooth(t) * 0.8,
        run_time=run_time,
    )

    remove = AnimationGroup(FadeOut(trail), FadeOut(star), run_time=2.0)
    return Succession(anim, remove)


def _dna_strand(
    *,
    start=DOWN * 3,
    end=UP * 3,
    segments=220,
    amp=0.7,
    period=1.5,
    phase=0.0,
    jitter=0.0,
) -> VMobject:
    """
    Generate a smooth sinusoidal (DNA-like) strand between two points.
    """
    start = np.array(start)
    end = np.array(end)
    direction = end - start
    height = np.linalg.norm(direction)
    unit_dir = direction / height if height != 0 else np.array([0, 1, 0])

    ys = np.linspace(0, height, segments + 1)
    w = 2 * PI / period

    pts = []
    for y in ys:
        j = random.uniform(-jitter, jitter) if jitter else 0.0
        x = amp * math.sin(w * y + phase) + j
        pts.append(start + unit_dir * y + np.array([x, 0, 0]))

    m = VMobject().set_fill(opacity=0).set_stroke(width=0)
    m.set_points_smoothly(np.array(pts))
    return m


def _make_glow_follow(strand: VMobject, *, core_color, glow_color) -> VGroup:
    """Create a dynamic glowing version of a strand that updates each frame."""
    core = VMobject()
    core.add_updater(
        lambda m: m.become(strand.copy().set_stroke(core_color, width=3.0, opacity=1.0))
    )

    glows = VGroup()

    def _rebuild(_):
        glows.become(
            add_glow_layers(
                strand.copy(),
                glow_color=glow_color,
                count=6,
                spread=2.2,
                max_opacity=0.22,
            )
        )

    glows.add_updater(_rebuild)
    glows.set_z_index(2)
    core.set_z_index(3)
    return VGroup(glows, core)


def _hide_all_text(vgroup: VGroup) -> None:
    """Recursively set opacity=0 for all text elements."""
    for sub in vgroup.submobjects:
        if isinstance(sub, (Text, MarkupText, MathTex)):
            sub.set_opacity(0)
        elif isinstance(sub, VGroup):
            _hide_all_text(sub)


def _get_color(m, fallback="primary") -> str:
    """Return the visible stroke or fill color of a mobject as a hex string."""
    try:
        if getattr(m, "stroke_width", 0) and m.get_stroke_opacity() > 0:
            return m.get_stroke_color().to_hex()
        if m.get_fill_opacity() > 0:
            return m.get_fill_color().to_hex()
        return m.get_stroke_color().to_hex()
    except Exception:
        return t._get_color(fallback)


def _collect_colors(targets, fallback="primary") -> list[str]:
    """Return one representative color per target."""
    colors = []
    for m in targets:
        parts = (
            m.family_members_with_points()
            if hasattr(m, "family_members_with_points")
            else [m]
        )
        visible = [_get_color(p, fallback) for p in parts]
        colors.append(max(set(visible), key=visible.count))
    return colors


def pulsar(scene: ThreeDScene, target: VGroup | VMobject) -> Wait:
    """
    Create a pulsar-like animation of glowing DNA strands around a target.
    """
    _hide_all_text(target)

    amp, period, segments = 0.7, 1.5, 220
    x, z = target.get_center()[0], target.get_center()[2]
    top_pt, bot_pt = target.get_top(), target.get_bottom()
    extend = 10

    strand_t1 = _dna_strand(start=[x, top_pt[1] + extend, z], end=top_pt, amp=amp, period=period)
    strand_t2 = _dna_strand(start=[x, top_pt[1] + extend, z], end=top_pt, amp=amp, period=period, phase=PI)
    strand_b1 = _dna_strand(start=bot_pt, end=[x, bot_pt[1] - extend, z], amp=amp, period=period)
    strand_b2 = _dna_strand(start=bot_pt, end=[x, bot_pt[1] - extend, z], amp=amp, period=period, phase=PI)

    color = _collect_colors(target)
    styled_t1 = _make_glow_follow(strand_t1, core_color=color, glow_color=color)
    styled_t2 = _make_glow_follow(strand_t2, core_color=color, glow_color=color)
    styled_b1 = _make_glow_follow(strand_b1, core_color=color, glow_color=color)
    styled_b2 = _make_glow_follow(strand_b2, core_color=color, glow_color=color)

    scene.add(styled_t1, styled_t2, styled_b1, styled_b2, target)

    phase_top = ValueTracker(0.0)
    phase_bot = ValueTracker(0.0)
    w = 2 * PI / period

    def _retarget_factory(start, end, offset, phase_src):
        start, end = np.array(start), np.array(end)
        direction = end - start
        height = np.linalg.norm(direction)
        unit_dir = direction / height if height != 0 else np.array([0, 1, 0])
        ys_local = np.linspace(0, height, segments + 1)

        def _retarget(m):
            phi = phase_src.get_value()
            pts = [
                start + unit_dir * y + np.array([amp * math.sin(w * y + phi + offset), 0, 0])
                for y in ys_local
            ]
            m.set_points_smoothly(np.array(pts))

        return _retarget

    cb_t1 = _retarget_factory([x, top_pt[1] + extend, z], top_pt, 0.0, phase_top)
    cb_t2 = _retarget_factory([x, top_pt[1] + extend, z], top_pt, PI, phase_top)
    cb_b1 = _retarget_factory(bot_pt, [x, bot_pt[1] - extend, z], 0.0, phase_bot)
    cb_b2 = _retarget_factory(bot_pt, [x, bot_pt[1] - extend, z], PI, phase_bot)

    strand_t1.add_updater(cb_t1)
    strand_t2.add_updater(cb_t2)
    strand_b1.add_updater(cb_b1)
    strand_b2.add_updater(cb_b2)

    for s in (strand_t1, strand_t2, strand_b1, strand_b2):
        s.set_stroke(opacity=0).set_fill(opacity=0)
    scene.add(strand_t1, strand_t2, strand_b1, strand_b2)

    speed = 2 * PI / 3.0
    phase_top.add_updater(lambda p, dt: p.increment_value(+speed * dt))
    phase_bot.add_updater(lambda p, dt: p.increment_value(-speed * dt))
    scene.add(phase_top, phase_bot)

    target.add_updater(lambda m, dt: m.rotate(15 * dt, axis=UP))
    return Wait(6.0)
