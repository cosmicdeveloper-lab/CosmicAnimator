# src/cosmicanimator/application/subtitle.py

"""
Subtitle overlay system for timed captions in CosmicAnimator.

- `SubtitleOverlay`: schedules caption chunks and renders them as styled
  text at the bottom of the screen, synced to scene time.

Notes
-----
- Captions are styled via `style_text` (theme-aware) unless explicitly
  disabled (`use_style_text=False`).
- Chunks are swapped automatically as the scene time advances.
- Designed to be composable: overlay is just a `VGroup` you add to the scene.
"""

from __future__ import annotations
from manim import VGroup, Text, always_redraw, DOWN
from dataclasses import dataclass
from typing import List, Optional, Sequence, Dict, Any
from cosmicanimator.adapters.style import style_text


# ---------------------------------------------------------------------------
# Internal schedule container
# ---------------------------------------------------------------------------

@dataclass
class _Schedule:
    """Internal: stores a scheduled subtitle sequence."""
    chunks: Sequence[str]
    cum: Sequence[float]   # cumulative times for each chunk
    start_time: float      # absolute scene time offset


# ---------------------------------------------------------------------------
# Subtitle overlay
# ---------------------------------------------------------------------------

class SubtitleOverlay(VGroup):
    """
    On-screen subtitle overlay for Manim.

    Usage
    -----
    >>> overlay = SubtitleOverlay(scene, wrap_chars=34, style_variant="subtitle")
    >>> overlay.schedule_chunks(chunks, durations, start_time=scene.time)

    Parameters
    ----------
    scene : Scene
        Parent scene (must have `time` attribute).
    wrap_chars : int, optional
        Soft-wrap width (approximate characters per line).
    use_style_text : bool, default=True
        If True, build captions via `style_text`. If False, raw `Text`.
    style_variant : str, optional
        Named style variant to use (e.g., "subtitle").
    style_kwargs : dict, optional
        Extra style parameters for `style_text`.
    **style :
        Legacy kwargs forwarded to `Text` if `use_style_text=False`.
    """

    def __init__(
        self,
        scene,
        *,
        wrap_chars: Optional[int] = None,
        use_style_text: bool = True,
        style_variant: Optional[str] = "subtitle",
        style_kwargs: Optional[Dict[str, Any]] = None,
        **style,
    ):
        super().__init__()
        self.scene = scene

        # --- style config ---
        self.wrap_chars = wrap_chars
        self.use_style_text = use_style_text
        self.style_variant = style_variant
        self.style_kwargs = style_kwargs or {}
        self.style = style  # only used if use_style_text=False

        # --- runtime state ---
        self._current_idx: int = -1
        self._schedule: Optional[_Schedule] = None
        self._has_updater: bool = False

        # Root container for the active caption node
        self._root = VGroup()
        self.add(self._root)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def schedule_chunks(
        self,
        chunks: Sequence[str],
        durations: Sequence[float],
        *,
        start_time: float,
        offset: float = 0.0,
    ) -> None:
        """
        Schedule a sequence of caption chunks.

        Parameters
        ----------
        chunks : list[str]
            Subtitle strings to display.
        durations : list[float]
            Durations (seconds) for each chunk.
        start_time : float
            Scene time (seconds) to begin.
        offset : float, default=0.0
            Additional offset delay before first caption.

        Raises
        ------
        ValueError
            If lengths mismatch or any duration is negative.
        """
        if not chunks:
            self.clear_schedule()
            return
        if len(chunks) != len(durations):
            raise ValueError(
                f"chunks ({len(chunks)}) and durations ({len(durations)}) must match"
            )
        if any(d < 0 for d in durations):
            raise ValueError("durations must be non-negative")

        # Compute cumulative times (end boundaries)
        cum: List[float] = [0.0]
        for d in durations:
            cum.append(cum[-1] + float(d))

        self._schedule = _Schedule(
            chunks=list(chunks),
            cum=cum,
            start_time=float(start_time) + float(offset),
        )

        # Ensure overlay is in scene and updating
        if self not in self.scene.mobjects:
            self.scene.add(self)
        if not self._has_updater:
            self.add_updater(self._update)
            self._has_updater = True

    def stop(self) -> None:
        """Stop updating and clear any visible caption."""
        self.clear_schedule()
        if self._has_updater:
            self.remove_updater(self._update)
            self._has_updater = False

    def clear_schedule(self) -> None:
        """Clear subtitle schedule and remove current caption mobject."""
        self._schedule = None
        self._current_idx = -1
        self._root.submobjects.clear()

    # -----------------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------------

    def _wrap(self, s: str) -> str:
        """Greedy soft-wrap text into lines of ~wrap_chars length."""
        if not self.wrap_chars or self.wrap_chars <= 0:
            return s
        words = s.split()
        if not words:
            return s
        lines: List[str] = []
        cur: List[str] = []
        n = 0
        for w in words:
            add = (1 if cur else 0) + len(w)
            if n + add > self.wrap_chars:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
                n = len(w)
            else:
                cur.append(w)
                n += add
        if cur:
            lines.append(" ".join(cur))
        return "\n".join(lines)

    def _make_group(self, s: str) -> VGroup:
        """Create a styled caption group for one chunk of text."""
        s = self._wrap(s)
        if self.use_style_text:
            node = style_text(
                s,
                **({"variant": self.style_variant} if self.style_variant else {}),
                **self.style_kwargs,
            )
            return node if isinstance(node, VGroup) else VGroup(node)
        return VGroup(Text(s, **{k: v for k, v in self.style.items() if v is not None}))

    def _update(self, _mobj) -> None:
        """Updater: swaps active caption according to current scene time."""
        sch = self._schedule
        if not sch:
            return

        now = float(getattr(self.scene, "time", 0.0))
        t = now - sch.start_time

        # End of schedule → stop
        if t >= sch.cum[-1]:
            self.stop()
            return

        # Find active chunk index
        idx = -1
        for i in range(len(sch.chunks)):
            if sch.cum[i] <= t < sch.cum[i + 1]:
                idx = i
                break

        # Update overlay if index changed
        if idx != self._current_idx:
            self._current_idx = idx
            self._root.submobjects.clear()
            if 0 <= idx < len(sch.chunks):
                grp = self._make_group(sch.chunks[idx])
                # Position: bottom of frame, shifted further down for safety
                caption = always_redraw(lambda: grp.copy().to_edge(DOWN).shift(DOWN * 4))
                self._root.add(caption)
