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
from typing import Optional, Dict, Any
from manim import VGroup, UP, DOWN, Mobject
from .base import ActionContext, ActionResult, register
from cosmicanimator.adapters.style import style_text
from cosmicanimator.adapters.transitions.fade import fade_in_group


@register("render_title")
def render_title(
    ctx: ActionContext,
    *,
    text: str,
    color: str = "primary",
    font_size: Optional[float] = None,
    variant: Optional[str] = "title",
    style_kwargs: Optional[Dict[str, Any]] = None,
    margin: float = 0.3,
    center: bool = True,
    id: str = "title",
) -> ActionResult:
    """
    Render a styled title (HUD overlay).

    Parameters
    ----------
    ctx : ActionContext
        Provides scene, theme, and store.
    text : str
        Title string (short, display-oriented).
    color : str, default="primary"
        Theme role or hex code for text color.
    font_size : float, optional
        Explicit font size override.
    variant : str, default="title"
        Text style variant (e.g., "title", "subtitle").
    style_kwargs : dict, optional
        Extra keyword arguments forwarded to `style_text`.
    margin : float, default=0.3
        Vertical offset down from the top edge.
    center : bool, default=True
        If True, center horizontally; otherwise preserve alignment.
    id : str, default="title"
        Store ID for later reference (e.g., for fade-out).

    Returns
    -------
    ActionResult
        - group : VGroup containing the styled title
        - ids : {id -> title object}
        - animations : [fade-in Animation]
    """
    lbl = style_text(
        text,
        color=color,
        font_size=font_size,
        variant=variant,
        **(style_kwargs or {}),
    )
    grp = lbl if isinstance(lbl, VGroup) else VGroup(lbl)

    # Position top-of-frame with margin
    grp.to_edge(UP)
    if margin:
        grp.shift(DOWN * margin)
    if center:
        grp.move_to([0, grp.get_y(), 0])

    # Fade-in animation
    anims = [fade_in_group([grp], run_time=0.6)]

    # Store in context
    ids: Dict[str, Mobject] = {id: grp}
    ctx.store.update(ids)

    return ActionResult(group=grp, ids=ids, animations=anims)
