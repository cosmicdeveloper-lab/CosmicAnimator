# src/cosmicanimator/application/actions/boxes.py

"""
Action: layout_boxes

Creates one or more styled shapes ("boxes") arranged in a row, column, or grid,
optionally with connecting lines or arrows between them.

Features
--------
- Supports several shape kinds (from SHAPE_REGISTRY).
- Optional glow and fill styling.
- Automatic label placement.
- Connectors between adjacent boxes (arrow, line, curved arrow).
- Returns a combined VGroup and reveal animation.

Usage
-----
Registered as `"layout_boxes"` and callable from the action pipeline.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union
from math import ceil, sqrt
from manim import DOWN, ORIGIN, RIGHT, UP, Mobject, VGroup, LEFT, Write, rush_from
from cosmicanimator.core.theme import current_theme as t
from cosmicanimator.adapters.style import (
    curved_arrow,
    dotted_line,
    glow_arrow,
    style_shape,
    style_text
)
from cosmicanimator.adapters.transitions.reveal import reveal
from .action_utils import SHAPE_REGISTRY, apply_label, make_unit_shape
from .base import ActionContext, ActionResult, register


ShapeKind = Union[str, Callable[[], Mobject]]


@register("layout_boxes")
def layout_boxes(
    ctx: ActionContext,
    *,
    shape: ShapeKind = "square",
    size: float = None,
    count: int = 3,
    # layout
    direction: str = "row",  # "row" | "column" | "grid"
    spacing: float = 1.2,
    runtime: float = 0.6,
    # styling
    color: str = "primary",
    filled: bool = False,
    labels: Optional[Sequence[str]] = None,
    label_color: Optional[str] = None,
    # connections
    connection_type: Optional[str] = None,  # "arrow" | "line" | "curved_arrow"
    arrow_color: str = "muted",
    connection_labels: Optional[Sequence[str]] = None,
    # placement
    label_position: str = "down",
    center_at: Tuple[float, float, float] = ORIGIN,
) -> ActionResult:
    """
    Layout a sequence of styled shapes and optionally connect them with lines or arrows.
    Labels are handled separately (not grouped into shapes), similar to `layout_branch`.
    """
    # --- Normalize inputs ---------------------------------------------------
    n = max(1, int(count))
    labels = list(labels) if labels is not None else ["" for _ in range(n)]
    if len(labels) < n:
        labels += [""] * (n - len(labels))

    # --- Build shapes (without labels) --------------------------------------
    items = []
    for i in range(n):
        raw = make_unit_shape(shape, size)
        base = style_shape(raw, color=color, glow=True)

        if filled:
            try:
                geom = base.submobjects[-1] if base.submobjects else base
                geom.set_fill(t.get_color(color), opacity=1)
            except Exception:
                pass

        items.append(base)

    shapes = VGroup(*items)

    # --- Arrange items ------------------------------------------------------
    if direction == "row":
        shapes.arrange(RIGHT, buff=spacing)
        layout_for_connect = "row"

    elif direction == "column":
        shapes.arrange(DOWN, buff=spacing)
        layout_for_connect = "column"

    else:  # "grid"
        cols = max(1, int(round(sqrt(n))))
        rows = int(ceil(n / cols))
        grid_rows: List[VGroup] = []
        idx = 0
        for _ in range(rows):
            row_items = [items[idx + j] for j in range(min(cols, n - idx))]
            row_group = VGroup(*row_items).arrange(RIGHT, buff=spacing)
            grid_rows.append(row_group)
            idx += len(row_items)
            if idx >= n:
                break
        shapes = VGroup(*grid_rows).arrange(DOWN, buff=spacing)
        layout_for_connect = "row"

    shapes.move_to(center_at)

    # --- Labels (created separately after layout) ----------------------------
    label_mobs = []
    for i, shape in enumerate(items):
        txt = labels[i]
        if not txt:
            label_mobs.append(None)
            continue
        lbl = style_text(txt, variant="label", color=label_color or color)

        if label_position == "up":
            lbl.next_to(shape, UP, buff=0.3)
        elif label_position == "left":
            lbl.next_to(shape, LEFT, buff=0.3)
        elif label_position == "right":
            lbl.next_to(shape, RIGHT, buff=0.3)
        else:
            lbl.next_to(shape, DOWN, buff=0.3)

        label_mobs.append(lbl)

    labels_group = VGroup(*[m for m in label_mobs if m is not None])

    # --- Connectors ----------------------------------------------------------
    connectors = VGroup()
    if connection_type in ("arrow", "line", "curved_arrow"):
        if direction == "grid":
            sequences: List[Sequence[VGroup]] = [
                list(row.submobjects) for row in shapes.submobjects
            ]
        else:
            sequences = [items]

        connector_idx = 0
        for seq in sequences:
            if layout_for_connect == "row":
                start_edge, end_edge = "get_right", "get_left"
                curved_start_edge, curved_end_edge = "get_top", "get_top"
                buffer = UP * 0.3
            else:  # column
                start_edge, end_edge = "get_bottom", "get_top"
                curved_start_edge, curved_end_edge = "get_right", "get_right"
                buffer = RIGHT * 0.2

            for prev, nxt in zip(seq, seq[1:]):
                start_pt = getattr(prev, start_edge)()
                end_pt = getattr(nxt, end_edge)()
                curved_start_pt = getattr(prev, curved_start_edge)() + buffer
                curved_end_pt = getattr(nxt, curved_end_edge)() + buffer

                if connection_type == "arrow":
                    conn = glow_arrow(start=start_pt, end=end_pt, color=arrow_color)
                elif connection_type == "curved_arrow":
                    conn = curved_arrow(start=curved_start_pt, end=curved_end_pt, color=arrow_color)
                else:
                    conn = dotted_line(start=start_pt, end=end_pt, color=arrow_color)

                if connection_labels and connector_idx < len(connection_labels):
                    conn_lbl = style_text(connection_labels[connector_idx], variant="label", color=arrow_color)
                    conn_lbl.next_to(conn, UP, buff=0.2)
                    connectors.add(VGroup(conn, conn_lbl))
                else:
                    connectors.add(conn)
                connector_idx += 1

    # --- Combine -------------------------------------------------------------
    group = VGroup(shapes, connectors, labels_group).move_to(center_at)

    # --- Appearance animation ------------------------------------------------
    animations = [reveal(shapes, run_time=runtime)]
    if connection_type:
        animations.append(reveal(connectors, run_time=runtime))
    animations += [Write(m, rate_func=rush_from) for m in label_mobs if m is not None]

    # --- Finalize result -----------------------------------------------------
    ids: Dict[str, Mobject] = {f"shape{i + 1}": g for i, g in enumerate(items)}
    ids.update({f"connector{i + 1}": conn for i, conn in enumerate(connectors)})
    ids.update({f"label{i + 1}": lbl for i, lbl in enumerate(label_mobs) if lbl is not None})

    ctx.store.update(ids)
    return ActionResult(group=group, ids=ids, animations=animations)
