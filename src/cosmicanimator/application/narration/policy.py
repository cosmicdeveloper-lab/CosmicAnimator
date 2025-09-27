# src/cosmicanimator/application/narration/policy.py

"""
Subtitle timing and chunking policy.

This module defines `SubtitlePolicy`, which handles:
- Splitting text into balanced, readable chunks.
- Estimating or fitting per-chunk durations.
- Enforcing minimum/maximum timing constraints for readability.
"""

from __future__ import annotations
from typing import List, Tuple
import re


class SubtitlePolicy:
    """
    Policy for splitting text and computing subtitle durations.

    Responsibilities
    ----------------
    - Split narration into balanced chunks that fit display constraints.
    - Respect sentence boundaries when possible.
    - Handle oversize sentences with recursive balanced splitting.
    - Merge tiny tail fragments when possible.
    - Assign per-chunk durations, either estimated from text length or
      fitted to a known total duration.

    Parameters
    ----------
    wrap_chars : int, default=38
        Approximate maximum line width in characters.
    max_lines : int, default=2
        Maximum number of lines per subtitle chunk.
    chars_per_sec : float, default=16.0
        Approximate reading speed for duration estimation.
    min_duration : float, default=1.2
        Minimum allowed chunk duration (seconds).
    max_duration : float, default=3.8
        Maximum allowed chunk duration (seconds).
    """

    def __init__(
        self,
        *,
        wrap_chars: int = 38,
        max_lines: int = 2,
        chars_per_sec: float = 16.0,
        min_duration: float = 1.2,
        max_duration: float = 3.8,
    ):
        self.wrap_chars = int(max(1, wrap_chars))
        self.max_lines = int(max(1, max_lines))
        self.chars_per_sec = float(max(1e-6, chars_per_sec))
        self.min_duration = float(max(0.0, min_duration))
        self.max_duration = float(max(self.min_duration, max_duration))

    # ---------- Chunking ----------

    def chunk(self, text: str) -> List[str]:
        """
        Split input text into balanced, consistent chunks.

        Steps
        -----
        1. Normalize spaces.
        2. Split on sentence-like boundaries (`.`, `!`, `?`).
        3. For sentences exceeding the line budget, recursively split near
           target midpoints using punctuation or spaces as breakpoints.
        4. Merge a tiny tail with the previous chunk if it fits.

        Parameters
        ----------
        text : str
            Input narration text.

        Returns
        -------
        list[str]
            List of subtitle chunks.
        """
        text = " ".join((text or "").split())
        if not text:
            return []

        width = self.wrap_chars
        max_lines = self.max_lines

        # Split into sentence-like parts
        parts = [p for p in re.split(r'(?<=[.!?])\s+', text) if p]

        chunks: List[str] = []
        for p in parts:
            if self._wrapped_line_count(p, width) <= max_lines:
                chunks.append(p)
            else:
                chunks.extend(self._autosplit_chunk(p, max_lines=max_lines, width=width))

        return self._merge_tiny_tail(chunks, width, max_lines)

    def _autosplit_chunk(self, text: str, *, max_lines: int, width: int) -> List[str]:
        """
        Recursively split oversize text into balanced chunks.
        """
        text = " ".join(text.split())
        if not text or self._wrapped_line_count(text, width) <= max_lines:
            return [text] if text else []

        left, right = self._balanced_break(text, target=len(text) // 2)
        return (
            self._autosplit_chunk(left, max_lines=max_lines, width=width)
            + self._autosplit_chunk(right, max_lines=max_lines, width=width)
        )

    @staticmethod
    def _wrapped_line_count(s: str, width: int) -> int:
        """
        Estimate how many wrapped lines are needed for string `s`.
        """
        if width <= 0:
            return 1 if s else 0
        words = s.split()
        if not words:
            return 0

        lines, cur = 1, words[0]
        for w in words[1:]:
            if len(cur) + 1 + len(w) <= width:
                cur += " " + w
            else:
                lines += 1
                cur = w
        return lines

    @staticmethod
    def _balanced_break(s: str, target: int) -> Tuple[str, str]:
        """
        Find a balanced break point near `target` for splitting text.

        Prefers punctuation, then spaces, and finally falls back to a hard cut.
        """
        s = s.strip()
        n = len(s)
        if n <= 1:
            return s, ""

        # Candidate window around target
        window = max(12, n // 6)
        lo, hi = max(1, target - window), min(n - 1, target + window)

        punct = [
            i for i in range(lo, hi)
            if s[i] in ".!?;:,"
            and i + 1 < n and s[i + 1] == " "
        ]
        spaces = [i for i in range(lo, hi) if s[i] == " "]

        pick = lambda arr: (min(arr, key=lambda i: abs(i - target)) if arr else None)

        idx = pick(punct) or pick(spaces)
        if idx is None:
            all_spaces = [i for i, ch in enumerate(s) if ch == " "]
            idx = pick(all_spaces) or target

        left = s[: idx + 1].rstrip()
        right = s[idx + 1 :].lstrip()
        return left, right

    def _merge_tiny_tail(self, chunks: List[str], width: int, max_lines: int) -> List[str]:
        """
        Merge a tiny tail chunk with the previous chunk if it fits.

        Parameters
        ----------
        chunks : list[str]
            The current list of chunks.
        width : int
            Wrap width in characters.
        max_lines : int
            Maximum lines per chunk.

        Returns
        -------
        list[str]
            Possibly modified chunks.
        """
        if len(chunks) < 2:
            return chunks

        tail = chunks[-1]
        if len(tail) <= max(6, width // 2):
            merged = (chunks[-2] + " " + tail).strip()
            if self._wrapped_line_count(merged, width) <= max_lines:
                return chunks[:-2] + [merged]

        return chunks

    # ---------- Durations ----------

    def durations(self, chunks: List[str], total_duration: float) -> List[float]:
        """
        Compute per-chunk durations.

        Parameters
        ----------
        chunks : list[str]
            Subtitle chunks.
        total_duration : float
            Total narration duration (seconds). If <= 0, estimate durations
            using characters per second.

        Returns
        -------
        list[float]
            List of per-chunk durations.
        """
        if not chunks:
            return []

        lengths = [max(1, len(c.replace("\n", " "))) for c in chunks]

        # Case 1: use real total_duration if provided
        if total_duration and total_duration > 0:
            weights = [L / float(sum(lengths)) for L in lengths]
            d = [total_duration * w for w in weights]
        else:
            # Case 2: estimate from cps
            d = [L / self.chars_per_sec for L in lengths]

        # Apply upper cap
        d = [min(self.max_duration, x) for x in d]

        if total_duration and total_duration > 0:
            # Soft readability floor
            min_readable = min(0.6, self.min_duration)
            d = [max(min_readable, x) for x in d]

            # Normalize to match exact total
            s = sum(d)
            if s > 1e-6:
                scale = total_duration / s
                d = [x * scale for x in d]
            else:
                per = total_duration / len(d)
                d = [per for _ in d]

            # Re-apply upper cap
            d = [min(self.max_duration, x) for x in d]

            # Final normalization to match exact total
            s = sum(d)
            if s > 1e-6 and abs(s - total_duration) > 1e-3:
                k = total_duration / s
                d = [x * k for x in d]
        else:
            # No total provided → clamp
            d = [max(self.min_duration, min(self.max_duration, x)) for x in d]

        return d
