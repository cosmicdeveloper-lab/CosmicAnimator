# src/cosmicanimator/adapters/transitions/__init__.py

"""
Public API for CosmicAnimator's transition helpers.

This package bundles:
- Highlighting (`highlight_shapes`, `focus_on_shape`)
- Fade transitions (`fade_out_group`, `fade_in_group`, `ghost_shapes`)
- Motion transitions (`slide_in`, `slide_out`, `orbit_around`, `shake`)
- Camera transitions (`zoom_to`, `pan_to`, `zoom_out`)
- Visual overlays (`ripple_effect`)
- Timing utilities (`Timing`)

All helpers are theme-aware and designed to compose cleanly with Manim scenes.
"""

from .highlighting import *
from .fade import *
from .motion import *
from .camera import *
from .visuals import *
from .timing import *

__all__ = [
    # Highlighting
    "highlight_shapes", "focus_on_shape",
    # Fade
    "fade_out_group", "fade_in_group", "ghost_shapes",
    # Motion
    "slide_in", "slide_out", "orbit_around", "shake",
    # Camera
    "zoom_to", "pan_to", "zoom_out",
    # Visuals
    "ripple_effect",
    # Timing
    "Timing",
]
