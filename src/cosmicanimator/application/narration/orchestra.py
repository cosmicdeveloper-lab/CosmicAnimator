# src/cosmicanimator/application/orchestra.py

"""
Narration orchestration for CosmicAnimator.

Responsibilities
---------------
- Wraps a `VoiceoverScene` (configured via `tts.py`).
- Manages TTS playback and subtitle overlay scheduling.
- Provides both atomic (`say`) and contextual (`with narrate(...)`) APIs.

Notes
-----
- Subtitles are overlay-only (`SubtitleOverlay`), no file export here.
- If TTS returns ~0 duration (e.g., silent), fallback estimation is applied.
"""

from __future__ import annotations
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Dict, Any

from manim_voiceover import VoiceoverScene
from .subtitle import SubtitleOverlay


# ---------------------------------------------------------------------------
# Text & timing utilities
# ---------------------------------------------------------------------------

def _normalize_ws(text: str) -> str:
    """Collapse whitespace into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def _split_sentences(text: str) -> List[str]:
    """
    Naive sentence splitter on [.?!;:] boundaries.
    Short trailing fragments (<12 chars) are merged into the previous sentence.
    """
    text = _normalize_ws(text)
    if not text:
        return []
    parts: List[str] = []
    start = 0
    for m in re.finditer(r"[\.!\?;:](?=\s|$)", text):
        end = m.end()
        parts.append(text[start:end].strip())
        start = end
    if start < len(text):
        parts.append(text[start:].strip())

    merged: List[str] = []
    for s in parts:
        if merged and len(s) < 12:
            merged[-1] = (merged[-1] + " " + s).strip()
        else:
            merged.append(s)
    return [p for p in merged if p]


def _soft_wrap_line(line: str, max_len: int) -> List[str]:
    """Greedy word wrap for a single line up to `max_len` characters."""
    words = line.split()
    out, cur = [], []
    cur_len = 0
    for w in words:
        extra = 1 if cur else 0
        if cur_len + len(w) + extra <= max_len:
            cur.append(w)
            cur_len += len(w) + extra
        else:
            out.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        out.append(" ".join(cur))
    return out


def _auto_wrap_multiline(text: str, max_len: int) -> str:
    """Word-wrap across multiple sentences/lines."""
    if max_len <= 0:
        return text
    if "\n" in text:
        return "\n".join(
            " ".join(_soft_wrap_line(ln.strip(), max_len)) for ln in text.splitlines()
        )
    parts = _split_sentences(text) or [text]
    wrapped: List[str] = []
    for p in parts:
        wrapped.extend(_soft_wrap_line(p, max_len))
    return "\n".join(wrapped)


def _proportional_durations(tokens_per_part: Sequence[int], total_dur: float) -> List[float]:
    """
    Distribute total duration across parts proportionally by token count.

    Ensures:
    - Each part ≥ 0.01 s.
    - Durations sum back to total_dur.
    """
    total_tokens = max(1, sum(tokens_per_part))
    raw = [total_dur * max(1, n) / total_tokens for n in tokens_per_part]
    min_d = 0.01
    clipped = [max(min_d, d) for d in raw]
    scale = total_dur / max(min_d, sum(clipped))
    return [d * scale for d in clipped]


# ---------------------------------------------------------------------------
# Orchestra
# ---------------------------------------------------------------------------

@dataclass
class Orchestra:
    """
    High-level narrator orchestrating TTS and subtitle overlays.

    Attributes
    ----------
    scene : VoiceoverScene
        The scene to control narration in.
    subtitles : bool, default=True
        Whether to enable subtitle scheduling.
    render_on_video : bool, default=True
        If True, render subtitles as overlay captions.
    max_chars_per_line : int, default=36
        Soft wrap limit for subtitle lines.
    smart_split : bool, default=True
        If True, split text into sentence-based chunks.
    max_sentence_chars : int, default=80
        Max characters per chunk before forced split.
    global_caption_offset : float, default=0.0
        Offset (s) applied to all subtitle start times.
    overlay_kwargs : dict, optional
        Extra arguments for `SubtitleOverlay`.
    estimate_if_silent : bool, default=True
        Estimate duration if TTS returns ~0.
    words_per_sec : float, default=2.5
        Speed used for estimation (words per second).
    min_chunk_dur : float, default=0.6
        Minimum duration per subtitle chunk.
    max_chunk_dur : float, default=6.0
        Maximum duration per subtitle chunk.
    """
    scene: VoiceoverScene
    subtitles: bool = True
    render_on_video: bool = True
    max_chars_per_line: int = 36
    smart_split: bool = True
    max_sentence_chars: int = 80
    global_caption_offset: float = 0.0
    overlay_kwargs: Optional[Dict[str, Any]] = None
    estimate_if_silent: bool = True
    words_per_sec: float = 2.5
    min_chunk_dur: float = 0.6
    max_chunk_dur: float = 6.0

    def __post_init__(self) -> None:
        self._overlay: Optional[SubtitleOverlay] = None
        if self.subtitles and self.render_on_video:
            self._overlay = SubtitleOverlay(self.scene, **(self.overlay_kwargs or {}))

    # -----------------------------------------------------------------------
    # Voice control
    # -----------------------------------------------------------------------

    def configure_voice(self, **kwargs) -> None:
        """
        Forward voice configuration to the scene (see `tts.py`).

        Example
        -------
        >>> orch.configure_voice(model="tts_models/en/vctk/vits", speaker_idx=305)
        """
        if hasattr(self.scene, "configure_voice"):
            self.scene.configure_voice(**kwargs)
        else:
            raise AttributeError("Scene lacks `configure_voice(**kwargs)` (check tts.py).")

    # -----------------------------------------------------------------------
    # Overlay helpers
    # -----------------------------------------------------------------------

    def _now(self) -> float:
        """Return current scene time (renderer clock if available)."""
        if hasattr(self.scene, "renderer") and hasattr(self.scene.renderer, "time"):
            return float(self.scene.renderer.time)
        return float(getattr(self.scene, "time", 0.0))

    def _ensure_overlay(self) -> Optional[SubtitleOverlay]:
        """Lazily create subtitle overlay if needed."""
        if not (self.subtitles and self.render_on_video):
            return None
        if self._overlay is None:
            self._overlay = SubtitleOverlay(self.scene, **(self.overlay_kwargs or {}))
        return self._overlay

    def _estimate_durations(self, chunks: Sequence[str]) -> List[float]:
        """Estimate durations for chunks using words-per-second heuristic."""
        if not chunks:
            return []
        wps = max(0.1, float(self.words_per_sec))
        est: List[float] = []
        for c in chunks:
            words = max(1, len(c.split()))
            d = words / wps
            d = max(self.min_chunk_dur, min(self.max_chunk_dur, d))
            est.append(d)
        return est

    def _chunk_and_wrap(self, text: str) -> Tuple[List[str], List[str], List[int]]:
        """
        Split text → sentence chunks → wrapped lines.

        Returns
        -------
        (raw_chunks, wrapped_chunks, token_counts)
        """
        sentences = _split_sentences(text) or [text]
        chunks: List[str] = []
        for s in sentences:
            if len(s) <= self.max_sentence_chars:
                chunks.append(s)
            else:
                chunks.extend(self._chunk_by_length(s, self.max_sentence_chars))
        wrapped = [_auto_wrap_multiline(c, self.max_chars_per_line) for c in chunks]
        token_counts = [max(1, len(c.split())) for c in chunks]
        return chunks, wrapped, token_counts

    def _schedule_overlay(
        self,
        chunks_wrapped: Sequence[str],
        durations: Sequence[float],
        *,
        start_time: float,
    ) -> None:
        """Schedule overlay captions at a given start_time."""
        ov = self._ensure_overlay()
        if ov and chunks_wrapped and durations:
            ov.schedule_chunks(
                chunks_wrapped,
                list(durations),
                start_time=start_time + self.global_caption_offset,
            )

    # -----------------------------------------------------------------------
    # Speaking (atomic)
    # -----------------------------------------------------------------------

    def say(
        self,
        text: str,
        *,
        wait: bool = True,
        add_subtitle: Optional[bool] = None,
        speaker_idx: Optional[int] = None,
        voice_kwargs: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Speak text with TTS and optionally schedule subtitles.

        Parameters
        ----------
        text : str
            Text to speak.
        wait : bool
            If True, wait scene time for duration.
        add_subtitle : bool | None
            Override subtitle toggle. None = follow self.subtitles.
        speaker_idx, voice_kwargs :
            Temporary voice configuration.

        Returns
        -------
        float
            Duration of spoken text.
        """
        text = _normalize_ws(text)
        if not text:
            return 0.0

        _revert_needed = False
        if speaker_idx is not None or voice_kwargs:
            _revert_needed = True
            vk = dict(voice_kwargs or {})
            if speaker_idx is not None:
                vk["speaker_idx"] = speaker_idx
            self.configure_voice(**vk)

        dur = 0.0
        try:
            start_time = self._now()
            with self.scene.voiceover(text=text) as tracker:
                dur = float(getattr(tracker, "duration", 0.0))

                do_caption = self.subtitles if add_subtitle is None else bool(add_subtitle)
                if do_caption:
                    if self.smart_split:
                        _, wrapped_chunks, token_counts = self._chunk_and_wrap(text)
                        chunk_durs = (
                            _proportional_durations(token_counts, dur)
                            if dur > 0.001
                            else (
                                self._estimate_durations(wrapped_chunks)
                                if self.estimate_if_silent
                                else [0.0] * len(wrapped_chunks)
                            )
                        )
                        self._schedule_overlay(wrapped_chunks, chunk_durs, start_time=start_time)
                    else:
                        wrapped = _auto_wrap_multiline(text, self.max_chars_per_line)
                        total = (
                            dur
                            if dur > 0.001
                            else (
                                self._estimate_durations([wrapped])[0]
                                if self.estimate_if_silent
                                else 0.0
                            )
                        )
                        self._schedule_overlay([wrapped], [total], start_time=start_time)

            if wait and dur > 0:
                self.scene.wait(dur)

        finally:
            if _revert_needed:
                pass

        return float(dur)

    # -----------------------------------------------------------------------
    # Speaking (contextual)
    # -----------------------------------------------------------------------

    @contextmanager
    def narrate(
        self,
        text: str,
        *,
        add_subtitle: Optional[bool] = None,
        speaker_idx: Optional[int] = None,
        voice_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager version of `say`.

        Usage
        -----
        >>> with orch.narrate("Hello!") as t:
        ...     self.play(Transform(...))
        ...     self.wait(t.duration)
        """
        text = _normalize_ws(text)

        class _Stub: duration = 0.0
        if not text:
            yield _Stub()
            return

        _revert_needed = False
        if speaker_idx is not None or voice_kwargs:
            _revert_needed = True
            vk = dict(voice_kwargs or {})
            if speaker_idx is not None:
                vk["speaker_idx"] = speaker_idx
            self.configure_voice(**vk)

        try:
            start_time = self._now()
            with self.scene.voiceover(text=text) as tracker:
                dur = float(getattr(tracker, "duration", 0.0))

                do_caption = self.subtitles if add_subtitle is None else bool(add_subtitle)
                if do_caption:
                    if self.smart_split:
                        _, wrapped_chunks, token_counts = self._chunk_and_wrap(text)
                        chunk_durs = (
                            _proportional_durations(token_counts, dur)
                            if dur > 0.001
                            else (
                                self._estimate_durations(wrapped_chunks)
                                if self.estimate_if_silent
                                else [0.0] * len(wrapped_chunks)
                            )
                        )
                        self._schedule_overlay(wrapped_chunks, chunk_durs, start_time=start_time)
                    else:
                        wrapped = _auto_wrap_multiline(text, self.max_chars_per_line)
                        total = (
                            dur
                            if dur > 0.001
                            else (
                                self._estimate_durations([wrapped])[0]
                                if self.estimate_if_silent
                                else 0.0
                            )
                        )
                        self._schedule_overlay([wrapped], [total], start_time=start_time)

                class _T: pass
                t = _T()
                t.duration = dur
                yield t
        finally:
            if _revert_needed:
                pass

    # -----------------------------------------------------------------------
    # Chunking helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _chunk_by_length(text: str, max_chars: int) -> List[str]:
        """Split text into chunks of ~max_chars, without breaking words."""
        words = text.split()
        out, cur = [], []
        cur_len = 0
        for w in words:
            extra = 1 if cur else 0
            if cur_len + len(w) + extra <= max_chars:
                cur.append(w)
                cur_len += len(w) + extra
            else:
                out.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
        if cur:
            out.append(" ".join(cur))
        return out

    def clear(self) -> None:
        """Clear any active subtitle overlay schedule."""
        if self._overlay:
            self._overlay.clear_schedule()


def ensure_orchestra(scene: Any, **kwargs: Dict[str, Any]) -> Orchestra:
    """
    Get (or lazily create) the `Orchestra` bound to this Manim scene.

    Behavior
    --------
    - Caches a single Orchestra instance on `scene._orch`.
    - `kwargs` (e.g., overlay_kwargs, smart_split) are applied only on first creation.
    - By default, enables on-video subtitles with overlay-only pipeline.

    Parameters
    ----------
    scene : Any
        A Manim scene (ideally subclass of VoiceScene).
    **kwargs :
        Extra arguments forwarded to `Orchestra`.

    Returns
    -------
    Orchestra
        Bound narrator instance for this scene.
    """
    orch: Optional[Orchestra] = getattr(scene, "_orch", None)
    if orch is None:
        base_kwargs = dict(subtitles=True, render_on_video=True)
        base_kwargs.update(kwargs or {})
        orch = Orchestra(scene=scene, **base_kwargs)
        setattr(scene, "_orch", orch)
    return orch
