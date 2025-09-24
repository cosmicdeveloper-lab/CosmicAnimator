# src/cosmicanimator/application/actions/boxes.py

"""
Action: lay out labeled shapes ("boxes") with optional connectors.

Registers
---------
- `layout_boxes` : arrange boxes in rows, columns, or grids, with optional:
    * Labels (outside or inside)
    * Connectors (arrow, line, curved arrow)
    * Appearance animations (fade, slide, or none)

Notes
-----
- Shapes are normalized via `make_unit_shape` + `style_shape`.
- Labels are attached with `apply_label` (styled text).
- IDs are auto-sanitized from labels (fallback: box1, box2, ...).
- Connectors are labeled separately (connector1, connector2, ...).
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union
from manim import DOWN, ORIGIN, RIGHT, Mobject, VGroup
from cosmicanimator.core.theme import current_theme as t
from cosmicanimator.adapters.style import (
    curved_arrow,
    dotted_line,
    glow_arrow,
    style_shape,
)
from cosmicanimator.adapters.transitions import fade_in_group, slide_in, Timing
from .action_utils import (
    SHAPE_REGISTRY,
    apply_label,
    make_unit_shape
)
from .base import ActionContext, ActionResult, register

ShapeKind = Union[str, Callable[[], Mobject]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deepest_geometry(node: Mobject) -> Mobject:
    """
    Return the deepest geometry node for stable connector anchoring.

    Implementation detail:
    - Traverses submobjects by repeatedly taking the *last* child until a leaf.
    - Ensures connector arrows attach to the visible "core" of a shape.
    """
    current = node
    while getattr(current, "submobjects", None):
        subs = current.submobjects
        if not subs:
            break
        current = subs[-1]
    return current


# ---------------------------------------------------------------------------
# Main action
# ---------------------------------------------------------------------------

@register("layout_boxes")
def layout_boxes(
    ctx: ActionContext,
    *,
    shape: ShapeKind = "square",
    size: float = 1.0,
    count: int = 4,
    # layout
    direction: str = "row",  # "row" | "column" | "grid"
    spacing: float = 1.2,
    rows: Optional[int] = None,
    cols: Optional[int] = None,
    # styling
    color: str = "primary",
    filled: bool = False,
    fill_color: Optional[str] = None,
    labels: Optional[Sequence[str]] = None,
    label_color: Optional[str] = None,
    label_colors: Optional[Sequence[Optional[str]]] = None,
    # connections
    connection_type: Optional[str] = None,  # "arrow" | "line" | "curved_arrow"
    arrow_color: str = "muted",
    connection_labels: Optional[Sequence[str]] = None,
    connection_label_color: Optional[str] = "muted",
    # placement
    label_position: str = "down",
    center_at: Tuple[float, float, float] = ORIGIN,
    # appearance animation (items)
    timing: str = "simultaneous",
    appear: str = "fade",            # "fade" | "slide" | "none"
    appear_direction: str = "left",  # for slide
    appear_run_time: float = 0.6,
    # appearance animation (connectors)
    connection_appear: str = "fade",  # "fade" | "slide" | "none"
) -> ActionResult:
    """
    Lay out boxes with labels, optional connectors, and appearance animation.

    Parameters
    ----------
    ctx : ActionContext
        Provides scene, store, and theme.
    shape : str | Callable, default="square"
        Shape kind (from SHAPE_REGISTRY) or a custom callable returning a Mobject.
    size: float = 1.0
        size of the shape in scale
    count : int, default=4
        Number of shapes to create (≥1).

    direction : {"row", "column", "grid"}, default="row"
        Layout orientation.
    spacing : float, default=1.2
        Buffer spacing between shapes.
    rows, cols : int, optional
        Row/column count for grid layouts. Auto-computed if not given.

    color : str, default="primary"
        Base stroke/glow color (theme role or hex).
    filled : bool, default=True
        Whether to fill shapes.
    fill_color : str, optional
        Fill color override. Defaults to `color` if not given.
    labels : list[str], optional
        Per-shape text labels. Shorter lists are padded.
    label_color : str, optional
        Default label color if no per-item list is given.
    label_colors : list[str|None], optional
        Per-shape label colors. Shorter lists are padded.

    connection_type : {"arrow", "line", "curved_arrow"}, optional
        If given, connect adjacent shapes with connectors.
    arrow_color : str, default="muted"
        Stroke/glow color for connectors.
    connection_labels : list[str], optional
        Optional labels for connectors.
    connection_label_color : str, default="muted"
        Color for connector labels.

    label_position : str, default=down
        If down, labels placed below; if up top of the shapes, if inside, inside the shape
    center_at : tuple[float, float, float], default=ORIGIN
        Center of the overall group.

    appear : {"fade", "slide", "none"}, default="fade"
        How shapes appear.
    appear_direction : {"left", "right", "up", "down"}, default="left"
        Slide direction for appear="slide".
    appear_run_time : float, default=0.6
        Duration of appearance animations.
    timing : {"simultaneous","sequential","stagger"}, default="simultaneous"
        Scheduling of item appearances.

    connection_appear : {"fade", "slide", "none"}, default="fade"
        How connectors appear.

    Returns
    -------
    ActionResult
        - group : VGroup (boxes + connectors)
        - ids : dict of {id -> mobject}
        - animations : list of appearance animations
    """
    # --- Normalize inputs ---
    n = max(1, int(count))

    labels = list(labels) if labels is not None else ["" for _ in range(n)]
    if len(labels) < n:
        labels += [""] * (n - len(labels))

    # Per-item label colors
    fallback_label_color = label_color or color
    if label_colors is None:
        per_item_label_colors = [fallback_label_color] * n
    else:
        tmp = list(label_colors) + [None] * max(0, n - len(label_colors))
        per_item_label_colors = [
            (c if c is not None else fallback_label_color) for c in tmp[:n]
        ]

    # --- Build items ---
    items: List[VGroup] = []
    for i in range(n):
        raw = make_unit_shape(shape, size)
        base = style_shape(raw, color=color, glow=True)

        # Optional fill (tolerant if unsupported)
        if filled:
            try:
                geom = base.submobjects[-1] if base.submobjects else base
                geom.set_fill(t.get_color(fill_color or color), opacity=1)
            except Exception:
                pass

        labeled = apply_label(
            base,
            labels[i],
            position=label_position,
            label_color=per_item_label_colors[i],
        )
        items.append(labeled)

    group = VGroup(*items)

    # --- Arrange items ---
    if direction == "column":
        group.arrange(DOWN, buff=spacing)
        layout_for_connect = "column"

    elif direction == "grid":
        from math import ceil, sqrt

        if rows is None and cols is None:
            cols = max(1, int(round(sqrt(n))))
            rows = int(ceil(n / cols))
        elif rows is None:
            rows = (n + int(cols) - 1) // int(cols)
        elif cols is None:
            cols = (n + int(rows) - 1) // int(rows)

        r, c = int(rows), int(cols)
        grid_rows: List[VGroup] = []
        idx = 0
        for _ in range(r):
            row_items = [items[idx + j] for j in range(min(c, n - idx))]
            row_group = VGroup(*row_items).arrange(RIGHT, buff=spacing)
            grid_rows.append(row_group)
            idx += len(row_items)
            if idx >= n:
                break
        group = VGroup(*grid_rows).arrange(DOWN, buff=spacing)
        layout_for_connect = "row"

    else:  # "row"
        group.arrange(RIGHT, buff=spacing)
        layout_for_connect = "row"

    group.move_to(center_at)

    # --- Appearance animations (items) ---
    animations = []
    if appear == "slide":
        animations.append(
            slide_in(
                group.submobjects,
                direction=appear_direction,
                run_time=appear_run_time,
                timing=Timing(mode=timing)
            )
        )
    elif appear == "fade":
        animations.append(
            fade_in_group(
                group.submobjects,
                run_time=appear_run_time,
                timing=Timing(mode=timing)
            )
        )

    # --- Optional connectors ---
    connectors = VGroup()

    if connection_type in ("arrow", "line", "curved_arrow"):
        if direction == "grid":
            sequences: List[Sequence[VGroup]] = [
                list(row.submobjects) for row in group.submobjects
            ]
        else:
            sequences = [items]

        connector_idx = 0
        for seq in sequences:
            if layout_for_connect == "column":
                start_edge, end_edge = "get_bottom", "get_top"
                curved_start_edge, curved_end_edge = "get_right", "get_right"
            else:
                start_edge, end_edge = "get_right", "get_left"
                curved_start_edge, curved_end_edge = "get_top", "get_top"

            for prev, nxt in zip(seq, seq[1:]):
                prev_geom = _deepest_geometry(prev.submobjects[0] if prev.submobjects else prev)
                next_geom = _deepest_geometry(nxt.submobjects[0] if nxt.submobjects else nxt)

                start_pt = getattr(prev_geom, start_edge)()
                end_pt = getattr(next_geom, end_edge)()
                curved_start_pt = getattr(prev_geom, curved_start_edge)()
                curved_end_pt = getattr(next_geom, curved_end_edge)()

                if connection_type == "arrow":
                    conn = glow_arrow(start=start_pt, end=end_pt, color=arrow_color)
                elif connection_type == "curved_arrow":
                    conn = curved_arrow(start=curved_start_pt, end=curved_end_pt, color=arrow_color)
                else:
                    conn = dotted_line(start=start_pt, end=end_pt, color=arrow_color)

                if connection_labels and connector_idx < len(connection_labels):
                    conn = apply_label(
                        conn,
                        connection_labels[connector_idx],
                        position=False,
                        label_color=connection_label_color,
                    )
                connectors.add(conn)
                connector_idx += 1

        # Connector appearance
        if connection_appear == "slide":
            animations.append(
                slide_in(
                    connectors.submobjects,
                    direction=appear_direction,
                    run_time=appear_run_time,
                    timing=Timing(mode=timing)
                )
            )
        elif connection_appear == "fade":
            animations.append(
                fade_in_group(
                    connectors.submobjects,
                    run_time=appear_run_time,
                    timing=Timing(mode=timing)
                )
            )

    # --- Finalize result ---
    ids: Dict[str, Mobject] = {
        f"box{i + 1}": g for i, g in enumerate(items)
    }
    ids.update({
        f"connector{i + 1}": conn
        for i, conn in enumerate(connectors)
    })

    group_all = VGroup(group, connectors)
    group_all.move_to(center_at)
    ctx.store.update(ids)

    return ActionResult(group=group_all, ids=ids, animations=animations)
