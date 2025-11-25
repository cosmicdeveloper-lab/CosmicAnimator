# src/cosmicanimator/adapters/transitions/reveal.py

"""
Sequential reveal transition for Manim objects.

This module defines:
- `reveal`: sequentially transforms one object into the next
  (chain-like reveal) using `TransformFromCopy` animations.
"""

from __future__ import annotations
from typing import Iterable
from manim import (
    VGroup, VMobject, AnimationGroup, TransformFromCopy,
    smooth, PI
)


def reveal(
    targets: Iterable[VMobject | VGroup],
    *,
    run_time: float = 0.6,
    path_arc: float = PI / 2,
    rate_func=smooth,
) -> AnimationGroup:
    """
    Sequentially transform each object into the next, creating a reveal chain.

    Parameters
    ----------
    targets
        Iterable of objects to reveal sequentially.
    run_time
        Duration of each `TransformFromCopy`.
    path_arc
        Arc angle followed by the transformation.
    rate_func
        Easing function applied to each step.

    Returns
    -------
    AnimationGroup
        Combined animation of sequential reveals.
    """

    anims = [t.animate for t in targets]
    steps = [
        TransformFromCopy(
            targets[i],
            targets[i + 1],
            path_arc=path_arc,
            rate_func=rate_func,
            run_time=run_time,
        )
        for i in range(len(targets) - 1)
    ]

    return AnimationGroup(*anims, *steps)
