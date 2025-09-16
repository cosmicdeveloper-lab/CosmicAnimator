# src/cosmicanimator/adapters/style/__init__.py

"""
Public API for CosmicAnimator's style helpers.

This package bundles:
- Text styling (`style_text`)
- Shape styling (`style_shape`)
- Arrow/line helpers (`glow_arrow`, `curved_arrow`, `dotted_line`)
- Low-level utilities (`is_hex_color`, `resolve_role_or_hex`, `add_glow_layers`)

All functions are theme-aware and designed to be composable with Manim objects.
"""

from .text import *
from .shapes import *
from .arrows import *
from .style_helpers import *

__all__ = [
    # High-level styling
    "style_text",
    "style_shape",
    # Arrow helpers
    "glow_arrow", "curved_arrow", "dotted_line",
    # Utilities
    "is_hex_color", "resolve_role_or_hex", "add_glow_layers",
]
