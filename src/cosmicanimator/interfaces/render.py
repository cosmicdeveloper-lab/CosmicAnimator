# src/cosmicanimator/interfaces/render.py

"""
Render interface for CosmicAnimator.

Provides
--------
- `render` : convenience wrapper for invoking `manim` from Python.

Notes
-----
- Calls `os.system` with a constructed CLI string.
- Default resolution is portrait 1080×1920 (short-form / vertical video).
- Raises FileNotFoundError if the scene file does not exist.
"""

import os
from pathlib import Path


def render(
    scene_file: str = "work/generated_scene.py",
    scene_class: str = "Generated",
    quality: str = "-ql",
    resolution: str = "1080,1920",
) -> None:
    """
    Render a generated scene using Manim.

    Parameters
    ----------
    scene_file : str, default="work/generated_scene.py"
        Path to the generated Python scene file.
    scene_class : str, default="Generated"
        Scene class name inside the file to render.
    quality : str, default="-ql"
        Manim quality flag: `-ql` (low), `-qm` (medium), `-qh` (high).
    resolution : str, default="1080,1920"
        Resolution as `"width,height"` (e.g., 1920,1080 for landscape).

    Raises
    ------
    FileNotFoundError
        If the `scene_file` does not exist.

    Side Effects
    ------------
    Executes `manim` CLI via `os.system`.

    Example
    -------
    >>> from cosmicanimator.interfaces.render import render
    >>> render("work/generated_scene.py", "Generated", "-qm", "1920,1080")
    ▶ Running: manim -qm -r 1920,1080 work/generated_scene.py Generated
    """
    scene_path = Path(scene_file)
    if not scene_path.exists():
        raise FileNotFoundError(f"Scene file not found: {scene_path}")

    cmd = (
        f"manim {quality} --disable_caching "
        f"-r {resolution} {scene_path} {scene_class}"
    )
    print(f"▶ Running: {cmd}")
    os.system(cmd)
