# src/cosmicanimator/application/narration/orchestra.py

"""
Orchestra: synchronization layer for voice and subtitles.

This module defines `Orchestra`, a conductor that:
- Runs TTS narration via the scene's voiceover.
- Captures start time and actual duration from the tracker.
- Delegates subtitle scheduling/retiming to `SubtitleScheduler`.
"""

from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, Dict, Any
from .contracts import NarrationResult
from .scheduler import SubtitleScheduler


class Orchestra:
    """
    Conductor for voice ↔ scene time synchronization.

    Responsibilities
    ----------------
    - Runs TTS via `scene.voiceover`.
    - Captures start_time and duration of narrations.
    - Optionally schedules subtitles via `SubtitleScheduler`.

    Parameters
    ----------
    scene : manim.Scene
        Parent scene containing `voiceover`.
    overlay_kwargs : dict, optional
        Extra arguments passed to `SubtitleScheduler` → `SubtitleOverlay`.
    """

    def __init__(self, scene, *, overlay_kwargs: Optional[Dict[str, Any]] = None):
        self.scene = scene
        self.scheduler = SubtitleScheduler(scene, overlay_kwargs=overlay_kwargs or {})
        self._subs_enabled: bool = True

    # ---------------- Configuration ----------------

    def enable_subtitles(self, flag: bool = True):
        """
        Enable or disable subtitles globally.

        Parameters
        ----------
        flag : bool, default=True
            If True, subtitles are rendered. If False, disabled.
        """
        self._subs_enabled = bool(flag)

    def configure_voice(self, **voice_kwargs: Any) -> None:
        """
        Configure the scene's voice (if supported).

        Parameters
        ----------
        **voice_kwargs : dict
            Forwarded to `scene.configure_voice`.

        Notes
        -----
        If the scene does not implement `configure_voice`, a warning is printed.
        """
        if hasattr(self.scene, "configure_voice"):
            self.scene.configure_voice(**voice_kwargs)
        else:
            print("[orchestra] scene does not support configure_voice; ignored")

    # ---------------- Narration ----------------

    @contextmanager
    def narrate(
        self,
        text: str,
        *,
        add_subtitle: Optional[bool] = None,
        voice_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Context-managed narration block.

        Parameters
        ----------
        text : str
            Narration text.
        add_subtitle : bool, optional
            Whether to add subtitles. If None, uses global setting.
        voice_kwargs : dict, optional
            Extra arguments forwarded to `configure_voice`.

        Yields
        ------
        tracker : manim_voiceover.tracker.VoiceoverTracker
            Tracker for synchronizing animations with narration.

        Notes
        -----
        - Subtitles are provisionally scheduled with `duration=0.0`.
        - After TTS completes, subtitles are retimed with the true duration.
        """
        if voice_kwargs:
            self.configure_voice(**voice_kwargs)

        start_time = float(getattr(self.scene, "time", 0.0))
        want_subs = self._subs_enabled if add_subtitle is None else bool(add_subtitle)

        # Schedule provisionally (duration=0.0 → policy fallback)
        if want_subs:
            provisional = NarrationResult(text=text, start_time=start_time, duration=0.0)
            self.scheduler.schedule(provisional)

        # Run TTS
        with self.scene.voiceover(text=text) as tracker:
            yield tracker

        # Retime subtitles after actual duration is known
        if want_subs:
            actual = NarrationResult(
                text=text,
                start_time=start_time,
                duration=float(getattr(tracker, "duration", 0.0)),
            )
            self.scheduler.retime(actual)

    def say(
        self,
        text: str,
        *,
        wait: bool = True,
        add_subtitle: Optional[bool] = None,
        voice_kwargs: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        One-shot narration.

        Parameters
        ----------
        text : str
            Narration text.
        wait : bool, default=True
            If True, call `scene.wait(duration)` after narration finishes.
        add_subtitle : bool, optional
            Whether to add subtitles (default = global setting).
        voice_kwargs : dict, optional
            Forwarded to `configure_voice`.

        Returns
        -------
        float
            Duration of narration in seconds.
        """
        vkw = dict(voice_kwargs or {})
        with self.narrate(text, add_subtitle=add_subtitle, voice_kwargs=vkw) as trk:
            dur = float(getattr(trk, "duration", 0.0))
            if wait and dur > 0:
                self.scene.wait(dur)
            return dur


def ensure_orchestra(scene, *, overlay_kwargs: Optional[Dict[str, Any]] = None) -> Orchestra:
    """
    Ensure that a scene has an `Orchestra` instance attached.

    Parameters
    ----------
    scene : manim.Scene
        Target scene.
    overlay_kwargs : dict, optional
        Extra arguments passed to `Orchestra`.

    Returns
    -------
    Orchestra
        Reuses an existing Orchestra if present; otherwise creates one.
    """
    orch = getattr(scene, "_orch", None)
    if isinstance(orch, Orchestra):
        return orch
    orch = Orchestra(scene, overlay_kwargs=overlay_kwargs)
    setattr(scene, "_orch", orch)
    return orch
