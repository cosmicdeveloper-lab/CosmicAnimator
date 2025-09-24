# src/cosmicanimator/application/actions/__init__.py

"""
Action registry for CosmicAnimator.

This package collects all action modules:

- base       : core types (`ActionContext`, `ActionResult`, registry helpers)
- boxes      : row/column/grid box layouts with labels and connectors
- diagrams   : branch-style diagrams (root → children)
- loop       : looping curved arrows (orbiting arcs)
- title      : HUD titles
- effects    : visual transitions (fade, slide, highlight, etc.)

Notes
-----
- All actions are registered globally via `@register`.
- Use `get_action(name)` to retrieve one by name.
"""

from .base import *
from .boxes import *
from .diagrams import *
from .loop import *
from .title import *
from .effects import *

__all__ = [
    "ActionContext",
    "ActionResult",
    "get_action",
]
