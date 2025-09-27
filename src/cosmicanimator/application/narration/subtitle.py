# src/cosmicanimator/application/narration/subtitle.py

"""
Subtitle overlay rendering for Manim scenes.

This module provides a pure rendering layer for subtitles synchronized
with narration. It handles:
- Splitting text into chunks with timings.
- Wrapping and styling text for display.
- Updating captions in sync with scene time.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence, Dict, Any
from manim import VGroup, Text, DOWN
from cosmicanimator.adapters.style import style_text


@dataclass
class _Schedule:
    """
    Internal data structure representing a subtitle schedule.
    """
    chunks: Sequence[str]
    cum: Sequence[float]
    start_time: float


class SubtitleOverlay(VGroup):
    """
    Subtitle rendering overlay for Manim scenes.

    Responsibilities
    ----------------
    - Receives pre-chunked text with durations.
    - Normalizes and clamps timing for consistent pacing.
    - Displays subtitles at the bottom of the frame, styled via
      `style_text` or raw Manim `Text`.

    Notes
    -----
    This class only handles *rendering*. Chunking and timing policies
    should be managed upstream.
    """

    def __init__(
        self,
        scene,
        *,
        wrap_chars: Optional[int] = None,
        use_style_text: bool = True,
        style_variant: Optional[str] = "subtitle",
        style_kwargs: Optional[Dict[str, Any]] = None,
        max_lines: int = 2,
        chars_per_sec: float = 16.0,
        min_duration: float = 1.2,
        max_duration: float = 3.8,
        safe_width: float = 0.86,
        **style,
    ):
        """
        Initialize the subtitle overlay.

        Parameters
        ----------
        scene : manim.Scene
            The parent scene.
        wrap_chars : int, optional
            Wrap width in characters. Defaults to 38.
        use_style_text : bool, default=True
            Whether to use `style_text` for rendering.
        style_variant : str, optional
            Style variant name (passed to `style_text`).
        style_kwargs : dict, optional
            Extra keyword arguments for `style_text`.
        max_lines : int, default=2
            Maximum number of subtitle lines.
        chars_per_sec : float, default=16.0
            Approximate reading speed for auto-timing.
        min_duration : float, default=1.2
            Minimum duration per chunk in seconds.
        max_duration : float, default=3.8
            Maximum duration per chunk in seconds.
        safe_width : float, default=0.86
            Maximum fraction of frame width allowed for subtitles.
        **style :
            Extra kwargs forwarded to `manim.Text` when `use_style_text=False`.
        """
        super().__init__()
        self.scene = scene

        # Styling options
        self.wrap_chars = wrap_chars
        self.use_style_text = use_style_text
        self.style_variant = style_variant
        self.style_kwargs = style_kwargs or {}
        self.style = style

        # Timing policy (render-guards only)
        self.max_lines = int(max(1, max_lines))
        self.chars_per_sec = float(max(1e-6, chars_per_sec))
        self.min_duration = float(max(0.0, min_duration))
        self.max_duration = float(max(self.min_duration, max_duration))
        self._default_wrap = 38
        self.safe_width = float(max(0.5, min(0.98, safe_width)))

        # Runtime state
        self._current_idx: int = -1
        self._schedule: Optional[_Schedule] = None
        self._has_updater: bool = False

        # Persistent slot for captions (always pinned to bottom)
        self._caption_node = VGroup()
        self._caption_node.add_updater(lambda m: m)
        self.add(self._caption_node)

    # ---------------- Public API ----------------

    def schedule_chunks(
        self,
        chunks: Sequence[str],
        durations: Sequence[float],
        *,
        start_time: float,
        offset: float = 0.0,
        pace: float = 0.92,
        lead: float = 0.14,
    ) -> None:
        """
        Schedule subtitle chunks with associated durations.

        Parameters
        ----------
        chunks : list[str]
            List of subtitle strings.
        durations : list[float]
            Durations for each subtitle chunk (seconds).
        start_time : float
            Start time of the first chunk (scene-relative).
        offset : float, default=0.0
            Global timing offset applied to all chunks.
        pace : float, default=0.92
            Scaling factor applied to durations.
        lead : float, default=0.14
            Time subtracted from the start for early lead-in.
        """
        if not chunks:
            self.clear_schedule()
            return
        if len(chunks) != len(durations):
            raise ValueError("chunks and durations must have the same length")
        if any(d < 0 for d in durations):
            raise ValueError("durations must be non-negative")

        # Normalize durations and clamp
        durations = [max(d, 1e-3) * pace for d in durations]
        start_time = float(start_time) - lead

        norm_chunks: List[str] = []
        norm_durations: List[float] = []
        for text, dur in zip(chunks, durations):
            text = " ".join((text or "").split())
            if not text:
                continue
            nd = self._clamped_duration(
                dur if dur > 0 else len(text) / self.chars_per_sec
            )
            norm_chunks.append(text)
            norm_durations.append(nd)

        # Build cumulative schedule
        cum: List[float] = [0.0]
        for d in norm_durations:
            cum.append(cum[-1] + float(d))

        self._schedule = _Schedule(
            chunks=norm_chunks, cum=cum, start_time=float(start_time) + float(offset)
        )

        if self not in self.scene.mobjects:
            self.scene.add(self)
        if not self._has_updater:
            self.add_updater(self._update)
            self._has_updater = True

    def stop(self) -> None:
        """
        Stop subtitle rendering and remove the updater.
        """
        self.clear_schedule()
        if self._has_updater:
            self.remove_updater(self._update)
            self._has_updater = False

    def clear_schedule(self) -> None:
        """
        Clear the current subtitle schedule and reset state.
        """
        self._schedule = None
        self._current_idx = -1
        self._caption_node.become(VGroup())

    # ---------------- Internal helpers ----------------

    def _clamped_duration(self, seconds: float) -> float:
        """Clamp duration to [min_duration, max_duration]."""
        s = float(seconds)
        return max(self.min_duration, min(self.max_duration, s))

    def _wrap(self, s: str) -> str:
        """Word-wrap a string into multiple lines."""
        width = int(self.wrap_chars or 0)
        if width <= 0:
            return s
        words = s.split()
        if not words:
            return s
        lines: List[str] = []
        cur: List[str] = []
        n = 0
        for w in words:
            need = (1 if cur else 0) + len(w)
            if n + need > width:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
                n = len(w)
            else:
                cur.append(w)
                n += need
        if cur:
            lines.append(" ".join(cur))
        return "\n".join(lines)

    def _make_group(self, s: str) -> VGroup:
        """Create a styled group for a subtitle string."""
        s = self._wrap(s)
        if self.use_style_text:
            node = style_text(
                s,
                **({"variant": self.style_variant} if self.style_variant else {}),
                **self.style_kwargs,
            )
            from manim import Mobject
            grp = (
                node
                if isinstance(node, VGroup)
                else (VGroup(node) if isinstance(node, Mobject) else VGroup(Text(s)))
            )
        else:
            grp = VGroup(Text(s, **{k: v for k, v in self.style.items() if v is not None}))

        # Keep a constant visual width (avoid large/small jumps)
        max_w = self.scene.camera.frame_width * self.safe_width
        if grp.width > max_w:
            grp.scale_to_fit_width(max_w)
        return grp

    def _show_text(self, s: str) -> None:
        """Render a subtitle string at the bottom of the frame."""
        grp = self._make_group(s)
        self._caption_node.become(grp).to_edge(DOWN).shift(DOWN * 4)

    def _update(self, _mobj) -> None:
        """Frame updater: show current chunk if within schedule window."""
        sch = self._schedule
        if not sch:
            return
        now = float(getattr(self.scene, "time", 0.0))
        t = now - sch.start_time
        if t < 0:
            return  # not time yet
        if t >= sch.cum[-1]:
            self.stop()
            return
        idx = -1
        for i in range(len(sch.chunks)):
            if sch.cum[i] <= t < sch.cum[i + 1]:
                idx = i
                break
        if idx != self._current_idx:
            self._current_idx = idx
            if 0 <= idx < len(sch.chunks):
                self._show_text(sch.chunks[idx])
