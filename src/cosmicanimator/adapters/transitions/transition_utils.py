# src/cosmicanimator/adapters/transitions/transition_utils.py

"""
Utility functions used by transition modules in CosmicAnimator.

Provides helpers for:
- Resolving theme-aware colors (`fill_for`, `glow_for`, `visible_color_of`)
- Building glow overlays for shapes (`build_glow_overlay`)
- Extracting geometry targets safely (`extract_targets`)
- Collecting representative colors from targets (`collect_target_colors`)
"""

from __future__ import annotations
from typing import Optional, Iterable, List, Sequence
from manim import VMobject, Text, MarkupText, MathTex, Paragraph, VGroup
from manim.utils.color import ManimColor
from collections import Counter
from cosmicanimator.core.theme import current_theme as t
from cosmicanimator.adapters.style import is_hex_color, add_glow_layers


# ---------------------------------------------------------------------------
# Color resolvers
# ---------------------------------------------------------------------------

def _fill_for(role_or_hex: Optional[str]) -> str:
    """
    Resolve a role or hex to a concrete **fill** color (hex).

    Parameters
    ----------
    role_or_hex : str | None
        - None → "primary"
        - Hex string → return as-is
        - Role name → resolve via theme

    Returns
    -------
    str
        Hex color string.
    """
    if not role_or_hex:
        role_or_hex = "primary"
    if is_hex_color(role_or_hex):
        return t.get_color(role_or_hex)
    role = t.get_role(str(role_or_hex))
    return role.get("fill", t.get_color("white"))


def _glow_for(role_or_hex: Optional[str]) -> str:
    """
    Resolve a role or hex to a concrete **glow** color (hex).

    Order of preference:
    1. Role glow color
    2. Role stroke color
    3. Role fill color
    4. White fallback
    """
    if not role_or_hex:
        role_or_hex = "primary"
    if is_hex_color(role_or_hex):
        return t.get_color(role_or_hex)
    role = t.get_role(str(role_or_hex))
    return role.get("glow", role.get("stroke", role.get("fill", t.get_color("white"))))


def _to_hex(c) -> str:
    """Convert a Manim color-like to hex, with fallback to theme white."""
    try:
        return ManimColor(c).to_hex()
    except Exception:
        return t.get_color("white")


def _visible_color_of(
    m: VMobject,
    *,
    fallback: str = "primary",
    use_raw_when_transparent: bool = True,
) -> str:
    """
    Pick a "representative" visible color from a VMobject.

    Order of preference
    -------------------
    1. Stroke (if width > 0 and opacity > 0)
    2. Fill (if opacity > 0)
    3. Raw stroke color (even if transparent) if `use_raw_when_transparent=True`
    4. Raw fill color (same rule as above)
    5. Fallback theme color

    Returns
    -------
    str
        Hex color string.
    """
    try:
        if getattr(m, "stroke_width", 0) and m.get_stroke_opacity() > 0:
            return _to_hex(m.get_stroke_color())
        if m.get_fill_opacity() > 0:
            return _to_hex(m.get_fill_color())

        if use_raw_when_transparent:
            try:
                return _to_hex(m.get_stroke_color())
            except Exception:
                pass
            try:
                return _to_hex(m.get_fill_color())
            except Exception:
                pass
    except Exception:
        pass

    return t.get_color(fallback)


# ---------------------------------------------------------------------------
# Glow overlays
# ---------------------------------------------------------------------------

def _shape_width() -> float:
    """Base stroke width for shapes per theme (fallback: 'normal')."""
    return float(t.get_stroke("normal"))


def build_glow_overlay(
    shape: VMobject,
    color: str,
    bands: Sequence[tuple[float, float]] | None = None,
) -> VGroup:
    """
    Build a glow-only overlay for a shape.

    Behavior
    --------
    - Duplicates the shape.
    - Clears fill (opacity=0).
    - Applies base stroke.
    - Adds halo layers via `add_glow_layers`.

    Parameters
    ----------
    shape : VMobject
        Shape to duplicate.
    color : str
        Role or hex to resolve glow color.
    bands : list of (width_mul, opacity), optional
        Explicit glow band spec.

    Returns
    -------
    VGroup
        (glow_layers, base_shape).
    """
    base = shape.copy()
    base.set_fill(opacity=0.0)
    base.set_stroke(_fill_for(color), width=max(_shape_width(), 6.0), opacity=1.0)
    glows = add_glow_layers(base, glow_color=_glow_for(color), bands=bands)
    return VGroup(glows, base)


# ---------------------------------------------------------------------------
# Target extraction
# ---------------------------------------------------------------------------

def _is_text(obj: VMobject) -> bool:
    """Return True if obj is text-like (Text, MarkupText, MathTex, Paragraph)."""
    return isinstance(obj, (Text, MarkupText, MathTex, Paragraph))


def extract_targets(
    target,
    *,
    include_text: bool = False,
    strategy: str = "leaves",  # "leaves" | "parents_with_points"
):
    """
    Extract VMobjects from a target for styling/transition purposes.

    Parameters
    ----------
    target : VMobject | VGroup
        The input object.
    include_text : bool, default=False
        If False, skip text mobjects.
    strategy : {"leaves", "parents_with_points"}
        - "leaves": walk submobjects to leaf geometry
        - "parents_with_points": keep parent objects with points, deduping children

    Returns
    -------
    list[VMobject]
        List of geometry/text objects.
    """
    def _is_text_safe(m):
        try:
            return _is_text(m)
        except NameError:
            return False

    if strategy == "leaves":
        results: list[VMobject] = []

        def walk(m):
            if not include_text and _is_text_safe(m):
                return
            subs = getattr(m, "submobjects", None) or []
            if subs:
                for s in subs:
                    walk(s)
            else:
                results.append(m)

        walk(target)
        return results

    if strategy == "parents_with_points":
        fam = target.family_members_with_points() if hasattr(target, "family_members_with_points") else [target]
        if not include_text:
            fam = [m for m in fam if not _is_text_safe(m)]

        def fam_with_points(m):
            return set(m.family_members_with_points()) if hasattr(m, "family_members_with_points") else {m}

        descendants = {m: fam_with_points(m) for m in fam}
        keep = [m for m in fam if not any((m in descendants[n]) and (n is not m) for n in fam)]

        out, seen = [], set()
        for m in keep:
            if id(m) not in seen:
                seen.add(id(m))
                out.append(m)
        return out

    raise ValueError(f"Unknown strategy: {strategy}")


# ---------------------------------------------------------------------------
# Collect colors
# ---------------------------------------------------------------------------

def collect_target_colors(
    targets: Iterable[VMobject | VGroup],
    *,
    include_text: bool = False,
    fallback: str = "primary",
    per_part: bool = False,
) -> List[str] | List[List[str]]:
    """
    Collect representative colors from targets.

    Parameters
    ----------
    targets : iterable of VMobject | VGroup
    include_text : bool, default=False
        Include text if True.
    fallback : str, default="primary"
        Role fallback if no color is found.
    per_part : bool, default=False
        - False → return one "majority" color per target.
        - True → return list of colors (one per part).

    Returns
    -------
    list[str] | list[list[str]]
        Colors in hex form.
    """
    results: List[str] | List[List[str]] = []
    for target in targets:
        parts = extract_targets(target, include_text=include_text)

        if not parts:
            if per_part:
                results.append([t.get_color(fallback)])
            else:
                results.append(t.get_color(fallback))
            continue

        part_colors = [_visible_color_of(p, fallback=fallback) for p in parts]

        if per_part:
            results.append(part_colors)
        else:
            results.append(Counter(part_colors).most_common(1)[0][0])
    return results
