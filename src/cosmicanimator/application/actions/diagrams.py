# src/cosmicanimator/application/actions/diagrams.py

"""
Action: layout_branch

Creates a simple branch diagram connecting a root node to one or more child nodes.

Features
--------
- Supports multiple layout directions ("up", "down", "left", "right").
- The root node and children can have independent shapes, colors, and fill styles.
- Connects nodes with either glowing arrows or dotted lines.
- Automatically applies labels and glow styles.

Usage
-----
Registered as `"layout_branch"` and callable from the action pipeline.
"""

from __future__ import annotations
from typing import Optional, Sequence, Dict, Union, Callable
from manim import VGroup, ORIGIN, RIGHT, DOWN, UP, LEFT, Mobject, FadeIn, GrowFromCenter, Write, rush_from

from cosmicanimator.adapters.style import style_shape, glow_arrow, dotted_line, style_text
from cosmicanimator.adapters.transitions import reveal
from cosmicanimator.core.theme import current_theme as t
from .base import ActionContext, ActionResult, register
from .action_utils import make_unit_shape

ShapeKind = Union[str, Callable[[], Mobject]]


@register("layout_branch")
def layout_branch(
    ctx: ActionContext,
    *,
    root_shape: ShapeKind = "circle",
    child_shape: ShapeKind = "square",
    child_count: int = 3,
    direction: str = "down",  # "down" | "up" | "left" | "right"
    spacing: float = 1.5,
    level_gap: float = 1.7,
    root_size: float | None = None,
    child_size: float | None = None,
    root_label: str = "",
    child_labels: Optional[Sequence[str]] = None,
    child_label_position: Union[str, Sequence[str]] = "down",  # per-child supported
    root_label_position: str = "up",
    root_color: str = "primary",
    child_color: str = "secondary",
    arrow_color: str = "muted",
    connection_type: str = "arrow",  # "arrow" | "line"
    root_filled: bool = False,
    child_filled: bool = False,
    center_at=ORIGIN,
) -> ActionResult:
    """
    Branch diagram: root -> children with connectors and labels.
    Nodes (shapes) and labels are handled in **separate lists**.
    """

    n = max(1, int(child_count))

    # --- Normalize labels (per-child) ---------------------------------------
    labels = list(child_labels) if child_labels is not None else []
    if len(labels) < n:
        labels += [""] * (n - len(labels))
    labels = labels[:n]

    # Normalize per-child label positions
    if isinstance(child_label_position, str):
        positions = [child_label_position] * n
    else:
        positions = list(child_label_position) if child_label_position is not None else []
        if len(positions) < n:
            positions += ["down"] * (n - len(positions))
        positions = positions[:n]

    # Direction helpers
    dir_map = {"up": UP, "down": DOWN, "left": LEFT, "right": RIGHT}

    # Edge pickers for connectors (root_edge(child_edge))
    def _edges_for_direction(dir_name: str):
        if dir_name == "down":
            return (Mobject.get_bottom, Mobject.get_top)
        if dir_name == "up":
            return (Mobject.get_top, Mobject.get_bottom)
        if dir_name == "right":
            return (Mobject.get_right, Mobject.get_left)
        # left
        return (Mobject.get_left, Mobject.get_right)

    root_edge_fn, child_edge_fn = _edges_for_direction(direction)

    # --- Root node ----------------------------------------------------------
    root_raw = make_unit_shape(root_shape, root_size)
    root_node = style_shape(root_raw, color=root_color, glow=True)
    root_node.set_fill(t.get_color(root_color), opacity=1 if root_filled else 0)

    root_grp: VGroup = VGroup(root_node).shift(UP * 3)

    # Root label (kept separate)
    root_label_mob = None
    if root_label:
        root_label_mob = style_text(root_label, variant="label", color=root_color)

    # --- Child nodes (shapes only) ------------------------------------------
    child_nodes: list[Mobject] = []
    for _ in range(n):
        ch_raw = make_unit_shape(child_shape, child_size)
        ch_node = style_shape(ch_raw, color=child_color, glow=True)
        ch_node.set_fill(t.get_color(child_color), opacity=1 if child_filled else 0)
        child_nodes.append(ch_node)

    children = VGroup(*[VGroup(node) for node in child_nodes])

    # --- Layout children relative to root -----------------------------------
    if direction in ("down", "up"):
        children.arrange(RIGHT, buff=spacing)
        if direction == "down":
            children.next_to(root_grp, DOWN, buff=level_gap)
        else:
            children.next_to(root_grp, UP, buff=level_gap)
    else:
        children.arrange(DOWN, buff=spacing)
        if direction == "right":
            children.next_to(root_grp, RIGHT, buff=level_gap)
        else:
            children.next_to(root_grp, LEFT, buff=level_gap)

    # Place root label after root is positioned
    if root_label_mob:
        root_label_mob.next_to(root_grp, dir_map.get(root_label_position, UP), buff=0.30)

    # --- Child labels (separate list; placed after layout) -------------------
    child_label_mobs: list[Optional[Mobject]] = []
    for i, node in enumerate(child_nodes):
        txt = labels[i]
        if not txt:
            child_label_mobs.append(None)
            continue
        lbl = style_text(txt, variant="label", color=child_color)
        vec = dir_map.get(positions[i], DOWN)
        lbl.next_to(node, vec, buff=0.30)
        child_label_mobs.append(lbl)

    # --- Connectors (from shape edges only) ---------------------------------
    arrows = VGroup()
    for ch_node in child_nodes:
        start_pt = root_edge_fn(root_node)
        end_pt = child_edge_fn(ch_node)
        conn = (
            glow_arrow(start=start_pt, end=end_pt, color=arrow_color)
            if connection_type == "arrow"
            else dotted_line(start=start_pt, end=end_pt, color=arrow_color)
        )
        arrows.add(conn)

    # --- Combine group (labels remain separate but included in scene) -------
    labels_group = VGroup(
        *([root_label_mob] if root_label_mob else []),
        *[m for m in child_label_mobs if m is not None],
    )
    group = VGroup(root_grp, arrows, child_nodes, labels_group).move_to(center_at)

    # --- Animations ----------------------------------------------------------
    # If there’s only one child, just fade that in; otherwise reveal sequence.
    if n == 1:
        shape_anims = FadeIn(root_grp, children, arrows)
    else:
        shape_anims = [
            GrowFromCenter(root_grp, run_time=0.5),
            reveal(VGroup(arrows, children))
        ]

    label_anims = []
    if root_label_mob:
        label_anims.append(Write(root_label_mob, rate_func=rush_from))
    label_anims += [Write(m, rate_func=rush_from) for m in child_label_mobs if m is not None]

    animations = shape_anims + label_anims

    # --- IDs for external targeting -----------------------------------------
    ids: Dict[str, Mobject] = {
        "root": root_grp,
        "root_label": root_label_mob if root_label_mob else VGroup(),
        **{f"child{i+1}": ch for i, ch in enumerate(child_nodes)},
        **{f"child_label{i+1}": (m if m is not None else VGroup()) for i, m in enumerate(child_label_mobs)},
        **{f"connector{i+1}": arr for i, arr in enumerate(arrows)},
    }

    ctx.store.update(ids)
    return ActionResult(group=group, ids=ids, animations=animations)
