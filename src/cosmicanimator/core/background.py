# src/cosmicanimator/core/background.py

from manim import *
import random
import numpy as np


# ============================================================
# 🌠 STARFIELD (static + parallax layers)
# ============================================================

def create_starfield(layer_defs=None, seed=None):
    """
    Create multiple parallax starfield layers.

    Args:
        layer_defs: list of tuples (count, radius, z_range, color, opacity)
        seed: random seed for reproducibility
    Returns:
        list of VGroups (e.g. [stars_far, stars_mid])
    """
    if seed is not None:
        random.seed(seed)

    if layer_defs is None:
        layer_defs = [
            (320, 0.05, (-3.0, -2.0), GRAY_D, 0.30),
            (220, 0.06, (-1.4, -0.8), GRAY_C, 0.40),
        ]

    layers = []
    for count, radius, (zmin, zmax), color, opacity in layer_defs:
        vg = VGroup(*[
            Dot(radius=radius, color=color).set_opacity(opacity).move_to([
                random.uniform(-15, 15),
                random.uniform(-20, 20),
                random.uniform(zmin, zmax)
            ])
            for _ in range(count)
        ])
        vg.set_z_index(-10)
        layers.append(vg)
    return layers


def add_parallax_motion(scene: ThreeDScene, layers, speeds=(0.10, 0.13)):
    """Attach continuous parallax motion to star layers."""
    for vg, speed in zip(layers, speeds):
        vg.add_updater(lambda m, dt, s=speed: m.shift(s * LEFT * dt))
        scene.add(vg)
