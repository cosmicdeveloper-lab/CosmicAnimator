# src/cosmicanimator/adapters/transitions/camera.py

"""
Camera transition helpers (zoom and pan).

These helpers animate the camera frame in a MovingCameraScene:
- `zoom_to`: zoom in on a target, hold, then optionally restore
- `zoom_out`: zoom out from current view, hold, then optionally restore
- `pan_to`: move the camera center smoothly to a target
"""

from __future__ import annotations
from manim import (
    VMobject, VGroup, Succession,
    Wait, smooth, Transform,
    RIGHT, LEFT, UP, DOWN
)


def zoom_to(
    scene,
    target: VMobject | VGroup,
    *,
    zoom: float = 1.8,         # >1 zooms in
    in_time: float = 0.9,
    hold_time: float = 0.5,
    out_time: float = 0.8,     # set to 0 to stay zoomed
    rate_func=smooth,
) -> Succession:
    """
    Zoom camera frame to `target`, hold, then optionally restore.

    Parameters
    ----------
    scene:
        Must be a MovingCameraScene (requires `scene.camera.frame`).
    target:
        VMobject or VGroup to center the zoom on.
    zoom:
        Zoom factor (>1 means zoom in).
    in_time:
        Duration of zoom-in animation.
    hold_time:
        Time to pause after zooming.
    out_time:
        Duration of restoring to original frame (0 = stay zoomed).
    rate_func:
        Rate function for smoothness (default: `smooth`).

    Returns
    -------
    Succession
        Sequence of animations: zoom-in, hold, and optional restore.
    """
    cam_frame = getattr(scene.camera, "frame", None)
    if cam_frame is None:
        raise TypeError("zoom_to() requires a MovingCameraScene.")

    # Prevent conflicts: updaters will override animations
    if cam_frame.updaters:
        raise RuntimeError("camera.frame has updaters; clear them before zooming.")

    # Snapshot original frame for exact restore
    original = cam_frame.copy()
    focus_center = target.get_center()

    zoom_in = (
        cam_frame.animate(run_time=in_time, rate_func=rate_func)
        .scale(1 / zoom)
        .move_to(focus_center)
    )

    steps = [zoom_in]
    if hold_time and hold_time > 0:
        steps.append(Wait(hold_time))

    if out_time and out_time > 0:
        steps.append(
            Transform(cam_frame, original, run_time=out_time, rate_func=rate_func)
        )

    return Succession(*steps)


def zoom_out(
    scene,
    *,
    zoom: float = 1.8,        # >1 means zoom OUT by that factor
    in_time: float = 0.9,
    hold_time: float = 0.5,
    out_time: float = 0.8,
    rate_func=smooth,
) -> Succession:
    """
    Smoothly zoom the camera out, hold, then optionally restore.

    Parameters
    ----------
    scene:
        Must be a MovingCameraScene.
    zoom:
        Outward zoom factor (>1 enlarges the frame).
    in_time:
        Duration of zoom-out animation.
    hold_time:
        Time to pause after zooming out.
    out_time:
        Duration of restoring to original frame (0 = stay zoomed out).
    rate_func:
        Rate function for smoothness.

    Returns
    -------
    Succession
        Sequence of animations: zoom-out, hold, and optional restore.
    """
    cam_frame = getattr(scene.camera, "frame", None)
    if cam_frame is None:
        raise TypeError("zoom_out() requires a MovingCameraScene.")

    # Snapshot original state for restore
    original = cam_frame.copy()

    zoom_out_anim = cam_frame.animate(run_time=in_time, rate_func=rate_func).scale(zoom)

    steps = [zoom_out_anim]
    if hold_time and hold_time > 0:
        steps.append(Wait(hold_time))

    if out_time and out_time > 0:
        steps.append(
            Transform(cam_frame, original, run_time=out_time, rate_func=rate_func)
        )

    return Succession(*steps)


def pan_to(
    scene,
    target: VMobject | VGroup,
    *,
    run_time: float = 1.0,
    rate_func=smooth,
    direction_step: float = 2.0,
    direction: str = "left",
):
    """
    Pan camera toward a target with optional directional offset.

    Parameters
    ----------
    scene:
        Must be a MovingCameraScene.
    target:
        VMobject or VGroup to move the frame center near.
    run_time:
        Duration of the pan.
    rate_func:
        Rate function for smoothness.
    direction_step:
        How far to offset (in Manim units).
    direction:
        One of {"left", "right", "up", "down"}.

    Returns
    -------
    Animation
        The camera movement animation.
    """
    cam_frame = getattr(scene.camera, "frame", None)
    if cam_frame is None:
        raise TypeError("pan_to() requires a MovingCameraScene.")

    # Direction vectors
    offsets = {
        "left":  LEFT,
        "right": RIGHT,
        "up":    UP,
        "down":  DOWN,
    }

    offset = offsets.get(direction, RIGHT) * direction_step
    target_point = target.get_center() + offset

    return cam_frame.animate(run_time=run_time, rate_func=rate_func).move_to(target_point)
