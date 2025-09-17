# src/cosmicanimator/application/actions/diagrams.py

"""
Branch-style diagram action: one root node → multiple children with connectors.

Registers
---------
- `layout_branch`: create a root shape with labeled child shapes,
  connect them with arrows or lines, and animate their appearance.

Notes
-----
- Shapes are styled via `style_shape` (theme-aware, neon+glow).
- Labels use `apply_label` and are sanitized into IDs.
- Connectors default to arrows, but can be dotted lines.
"""

from __future__ import annotations
from typing import Optional, Sequence, Dict, Union, Callable
from manim import VGroup, ORIGIN, RIGHT, DOWN, UP, LEFT, Mobject
from .base import ActionContext, ActionResult, register
from .action_utils import make_unit_shape, apply_label, sanitize_id
from cosmicanimator.adapters.style import style_shape, glow_arrow, dotted_line
from cosmicanimator.adapters.transitions import fade_in_group, slide_in, Timing
from cosmicanimator.core.theme import current_theme as t

ShapeKind = Union[str, Callable[[], Mobject]]


@register("layout_branch")
def layout_branch(
    ctx: ActionContext,
    *,
    root_shape: ShapeKind = "circle",
    child_shape: ShapeKind = "square",
    child_count: int = 3,
    direction: str = "down",           # "down" | "up" | "left" | "right"
    spacing: float = 1.2,
    level_gap: float = 1.5,
    root_label: str = "",
    child_labels: Optional[Sequence[str]] = None,
    label_outside: bool = True,
    root_color: str = "primary",
    child_color: str = "secondary",
    arrow_color: str = "muted",
    connection_type: str = "arrow",    # "arrow" | "line"
    root_filled: bool = False,
    child_filled: bool = False,
    root_fill_color: Optional[str] = None,
    child_fill_color: Optional[str] = None,
    center_at=ORIGIN,
    # appearance animation
    timing: str = "simultaneous",  # "simultaneous" | "sequential" | "stagger"
    appear: str = "fade",          # "fade" | "slide" | "none"
    appear_direction: str = "up",  # for slide
    appear_run_time: float = 0.6,
) -> ActionResult:
    """
    Lay out a root → children branch diagram with connectors.

    Parameters
    ----------
    ctx : ActionContext
        Provides scene, store, theme.
    root_shape : str | Callable, default="circle"
        Shape for the root node.
    child_shape : str | Callable, default="square"
        Shape for each child node.
    child_count : int, default=3
        Number of children (≥1).
    direction : {"down","up","left","right"}, default="down"
        Layout orientation.
    spacing : float, default=1.2
        Distance between siblings.
    level_gap : float, default=1.5
        Distance from root to children.
    root_label : str, default=""
        Text label for root node.
    child_labels : list[str], optional
        Labels for children. Padded if too short.
    label_outside : bool, default=True
        If True, labels placed outside; otherwise inside shapes.
    root_color : str, default="primary"
        Root stroke/glow color.
    child_color : str, default="secondary"
        Child stroke/glow color.
    arrow_color : str, default="muted"
        Connector stroke/glow color.
    connection_type : {"arrow","line"}, default="arrow"
        Connector style.
    root_filled : bool, default=True
        Whether root is filled.
    child_filled : bool, default=True
        Whether children are filled.
    root_fill_color : str, optional
        Override fill color for root.
    child_fill_color : str, optional
        Override fill color for children.
    center_at : tuple, default=ORIGIN
        Center point of diagram.
    timing : {"simultaneous","sequential","stagger"}, default="simultaneous"
        Entry animation scheduling.
    appear : {"fade","slide","none"}, default="fade"
        Entry animation type.
    appear_direction : {"up","down","left","right"}, default="up"
        Slide direction if appear="slide".
    appear_run_time : float, default=0.6
        Duration of entry animation.

    Returns
    -------
    ActionResult
        - group : VGroup (root + children + connectors)
        - ids : dict of ids ("root", "child1", ... "arrow1", ...)
        - animations : list of entry animations
    """
    n = max(1, int(child_count))

    # Normalize child labels to length n
    child_labels = list(child_labels) if child_labels is not None else ["" for _ in range(n)]
    if len(child_labels) < n:
        child_labels += [""] * (n - len(child_labels))

    # --- Root node -----------------------------------------------------------------
    root_raw = make_unit_shape(root_shape)
    root_node = style_shape(root_raw, color=root_color, glow=True)
    if root_filled:
        root_node.set_fill(t.get_color(root_fill_color or root_color), opacity=1)
    else:
        root_node.set_fill(opacity=0)
    root_grp: VGroup = VGroup(root_node)
    if root_label:
        root_grp = apply_label(root_grp, root_label, outside=label_outside, label_color=root_color)

    # --- Child nodes ---------------------------------------------------------------
    children_groups = []
    child_nodes = []
    for i in range(n):
        ch_raw = make_unit_shape(child_shape)
        ch_node = style_shape(ch_raw, color=child_color, glow=True)
        ch_grp = VGroup(ch_node)
        if child_labels[i]:
            ch_grp = apply_label(ch_grp, child_labels[i], outside=label_outside, label_color=child_color)
        if child_filled:
            ch_node.set_fill(t.get_color(child_fill_color or child_color), opacity=1)
        else:
            ch_node.set_fill(opacity=0)
        children_groups.append(ch_grp)
        child_nodes.append(ch_node)

    children = VGroup(*children_groups)

    # --- Position children relative to root ----------------------------------------
    if direction in ("down", "up"):
        children.arrange(RIGHT, buff=spacing)
        if direction == "down":
            children.next_to(root_grp, DOWN, buff=level_gap)
            root_edge, child_edge = Mobject.get_bottom, Mobject.get_top
        else:  # "up"
            children.next_to(root_grp, UP, buff=level_gap)
            root_edge, child_edge = Mobject.get_top, Mobject.get_bottom
    else:  # "left" or "right"
        children.arrange(DOWN, buff=spacing)
        if direction == "right":
            children.next_to(root_grp, RIGHT, buff=level_gap)
            root_edge, child_edge = Mobject.get_right, Mobject.get_left
        else:  # "left"
            children.next_to(root_grp, LEFT, buff=level_gap)
            root_edge, child_edge = Mobject.get_left, Mobject.get_right

    # --- Connectors ----------------------------------------------------------------
    arrows = VGroup()
    root_anchor = root_node
    for ch_node in child_nodes:
        start_pt = root_edge(root_anchor)
        end_pt = child_edge(ch_node)
        arr = glow_arrow(start=start_pt, end=end_pt, color=arrow_color) if connection_type == "arrow" \
            else dotted_line(start=start_pt, end=end_pt, color=arrow_color)
        arrows.add(arr)

    # --- Combine -------------------------------------------------------------------
    group = VGroup(root_grp, children, arrows).move_to(center_at)

    # --- Appearance animation ------------------------------------------------------
    animations = []
    if appear == "slide":
        animations.append(slide_in(group.submobjects, direction=appear_direction,
                                   run_time=appear_run_time, timing=Timing(mode=timing)))
    elif appear == "fade":
        animations.append(fade_in_group(group.submobjects, run_time=appear_run_time,
                                        timing=Timing(mode=timing)))

    # --- IDs -----------------------------------------------------------------------
    ids: Dict[str, Mobject] = {
        sanitize_id(root_label, "root"): root_grp,
        **{
            sanitize_id(lbl, f"child{i + 1}"): ch
            for i, (lbl, ch) in enumerate(zip(child_labels, children))
        },
        **{
            f"arrow{i + 1}": arr
            for i, arr in enumerate(arrows)
        },
    }
    ctx.store.update(ids)

    return ActionResult(group=group, ids=ids, animations=animations)
