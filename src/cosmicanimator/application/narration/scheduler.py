# src/cosmicanimator/application/narration/scheduler.py

"""
Subtitle scheduling layer.

This module defines `SubtitleScheduler`, a utility class that bridges:
- Narration results (`NarrationResult` from contracts).
- Subtitle policy (`SubtitlePolicy` for chunking and durations).
- Subtitle overlay (`SubtitleOverlay` for rendering in Manim).
"""

from __future__ import annotations
from typing import Optional, List
from .policy import SubtitlePolicy
from .subtitle import SubtitleOverlay
from .contracts import NarrationResult


class SubtitleScheduler:
    """
    Bridge between narration results and subtitle rendering.

    Responsibilities
    ----------------
    - Split narration text into subtitle chunks via `SubtitlePolicy`.
    - Compute per-chunk durations (either estimated or fitted).
    - Schedule subtitles for rendering with `SubtitleOverlay`.

    Parameters
    ----------
    scene : manim.Scene
        Parent scene for subtitle rendering.
    overlay : SubtitleOverlay, optional
        Custom overlay instance. If not provided, a new one is created.
    overlay_kwargs : dict, optional
        Extra keyword arguments forwarded to `SubtitleOverlay`.
    policy : SubtitlePolicy, optional
        Custom subtitle policy. If not provided, one is created
        based on overlay parameters.
    """

    def __init__(
        self,
        scene,
        *,
        overlay: Optional[SubtitleOverlay] = None,
        overlay_kwargs: Optional[dict] = None,
        policy: Optional[SubtitlePolicy] = None,
    ):
        overlay_kwargs = overlay_kwargs or {}
        self.scene = scene
        self.overlay = overlay or SubtitleOverlay(scene, **overlay_kwargs)
        self.policy = policy or SubtitlePolicy(
            wrap_chars=overlay_kwargs.get("wrap_chars", 38),
            max_lines=overlay_kwargs.get("max_lines", 2),
        )

    # ---------------- Public API ----------------

    def schedule(self, narr: NarrationResult, **kwargs) -> List[str]:
        """
        Schedule a new narration’s subtitles.

        Parameters
        ----------
        narr : NarrationResult
            Narration text and metadata (duration, start time).
        **kwargs :
            Extra arguments forwarded to `SubtitleOverlay.schedule_chunks`
            (e.g., `pace`, `lead`, `offset`).

        Returns
        -------
        list[str]
            The subtitle chunks that were scheduled.
        """
        chunks = self.policy.chunk(narr.text)
        durations = self.policy.durations(chunks, narr.duration)
        self.overlay.schedule_chunks(
            chunks, durations,
            start_time=narr.start_time,
            **kwargs
        )
        return chunks

    def retime(self, narr: NarrationResult, **kwargs) -> None:
        """
        Update timings once the true narration duration is known.

        Parameters
        ----------
        narr : NarrationResult
            Narration text and metadata with final duration.
        **kwargs :
            Extra arguments forwarded to `SubtitleOverlay.schedule_chunks`.

        Notes
        -----
        - If no subtitles are currently scheduled, this is a no-op.
        - Useful when initial scheduling was based on estimated durations.
        """
        if not getattr(self.overlay, "_schedule", None):
            return

        chunks = self.policy.chunk(narr.text)
        durations = self.policy.durations(chunks, narr.duration)
        self.overlay.schedule_chunks(
            chunks, durations,
            start_time=narr.start_time,
            **kwargs
        )
