# src/cosmicanimator/application/actions/narration_actions.py

"""
Narration-related actions for CosmicAnimator.

Provides
--------
- `voice_config` : configure TTS model/voice for the current scene.
- `narrate` : speak a line with optional on-screen subtitles.

Notes
-----
- Both actions wrap `Orchestra` (see `application/narration/orchestra.py`).
- They return empty `ActionResult` groups, since narration does not
  generate visible geometry. Timing is handled via `postwait`.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from manim import VGroup
from cosmicanimator.application.actions.base import register, ActionResult, ActionContext
from cosmicanimator.application.narration import ensure_orchestra


# ---------------------------------------------------------------------------
# Voice configuration
# ---------------------------------------------------------------------------

@register("voice_config")
def voice_config(ctx: ActionContext, **voice_kwargs: Any) -> ActionResult:
    """
    Configure the current TTS voice for this scene.

    Parameters
    ----------
    ctx : ActionContext
        Action context (provides `scene`).
    **voice_kwargs : Any
        Keyword args forwarded to `Orchestra.configure_voice`.
        Examples: `model="tts_models/en/vctk/vits"`, `speaker_idx=305`.

    Returns
    -------
    ActionResult
        Empty group/ids/animations; postwait=0.0.
    """
    orch = ensure_orchestra(ctx.scene)
    orch.configure_voice(**voice_kwargs)
    return ActionResult(group=VGroup(), ids={}, animations=[], postwait=0.0)


# ---------------------------------------------------------------------------
# Narrate
# ---------------------------------------------------------------------------

@register("narrate")
def narrate(
    ctx: ActionContext,
    *,
    text: str,
    wait: bool = True,
    add_subtitle: Optional[bool] = None,
    speaker_idx: Optional[int] = "P230",
    overlay_kwargs: Optional[Dict[str, Any]] = None,
    **voice_kwargs: Any,
) -> ActionResult:
    """
    Speak a line (TTS) and optionally show on-video subtitles.

    Parameters
    ----------
    ctx : ActionContext
        Action context (provides `scene`).
    text : str
        Line of narration to speak.
    wait : bool, default=True
        If True, block with `scene.wait(duration)`.
        If False, narration runs asynchronously and `postwait`
        carries the duration for pacing.
    add_subtitle : bool, optional
        Override Orchestra subtitle toggle.
        If None, use Orchestra’s global setting.
    speaker_idx : int, optional
        Temporary speaker index override.
    overlay_kwargs : dict, optional
        Arguments for first-time creation of Orchestra/overlay.
        Subsequent calls reuse the same instance.
    **voice_kwargs : Any
        Temporary TTS overrides (model, style, etc.).

    Returns
    -------
    ActionResult
        - group : empty VGroup (no geometry)
        - ids : {}
        - animations : []
        - postwait : narration duration if wait=False, else 0.0
    """
    orch = ensure_orchestra(ctx.scene, overlay_kwargs=overlay_kwargs)
    dur = orch.say(
        text,
        wait=wait,
        add_subtitle=add_subtitle,
        speaker_idx=speaker_idx,
        voice_kwargs=(voice_kwargs or None),
    )
    return ActionResult(
        group=VGroup(),
        ids={},
        animations=[],
        postwait=(0.0 if wait else float(dur)),
    )
