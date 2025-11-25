# src/cosmicanimator/application/actions/title.py

"""
Action: render styled title text.

Registers
---------
- `render_title`: create a fixed-position HUD title
  (usually top-of-frame) with fade-in animation.

Notes
-----
- Uses `style_text` (theme-aware) for styling.
- Titles are non-moving HUD elements, intended for short phrases.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from manim import Mobject, UP, Write
from .base import ActionContext, ActionResult, register
from cosmicanimator.adapters.style import style_text


@register("render_title")
def render_title(
    ctx: ActionContext,
    *,
    text: str,
    color: str = None,
    font_size: Optional[float] = None,
    variant: Optional[str] = "title",
    style_kwargs: Optional[Dict[str, Any]] = None,
    margin: float = 4,
    center: bool = False,
) -> ActionResult:
    """
    Render a styled HUD title at the top of the frame and fade it in.

    Parameters
    ----------
    ctx : ActionContext
        Action context with storage and theme access.
    text : str
        Title text content.
    color : str | None, optional
        Text/stroke color override (theme default if None).
    font_size : float | None, optional
        Font size override.
    variant : str | None, optional
        Style variant key for `style_text` (default "title").
    style_kwargs : dict | None, optional
        Extra keyword arguments forwarded to `style_text`.
    margin : float, optional
        Upward offset after docking to top edge.
    center : bool, optional
        If True, horizontally center the title.

    Returns
    -------
    ActionResult
        Result containing the created group, ids, and animations.
    """
    title = style_text(
        text,
        color=color,
        font_size=font_size,
        variant=variant,
        stroke_color=color,
        **(style_kwargs or {}),
    )
    grp = title

    # Position top-of-frame with margin
    grp.to_edge(UP, buff=0)
    if margin:
        grp.shift(UP * margin)
    if center:
        grp.move_to([0, grp.get_y(), 0])

    # Fade-in animation
    anims = [Write(grp, run_time=0.6)]

    # Store in context
    ids: Dict[str, Mobject] = {"title": grp}
    ctx.store.update(ids)

    return ActionResult(group=grp, ids=ids, animations=anims)
