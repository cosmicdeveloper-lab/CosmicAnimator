# src/cosmicanimator/application/actions/base.py

"""
Base action definitions and global registry for CosmicAnimator.

Defines
-------
- `ActionContext` : shared context object passed into every action.
- `ActionResult` : standardized return bundle from an action.
- `register` : decorator to add a function to the global registry.
- `get_action` : retrieve a registered action by name.

Notes
-----
- Actions are pure builders: they should *not* call `scene.play` directly.
- Instead, return animations in `ActionResult.animations` for the caller to run.
"""

from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional
from manim import Scene, Mobject, Animation, VGroup


# ---------------------------------------------------------------------------
# Context and result containers
# ---------------------------------------------------------------------------

@dataclass
class ActionContext:
    """
    Shared context provided to all actions.

    Attributes
    ----------
    scene : Scene
        The active Manim scene the action should target.
    store : dict[str, Mobject]
        Store of reusable mobjects (`id -> mobject`) that actions can
        reference or update across steps.
    theme : dict[str, Any]
        Theme parameters (colors, fonts, sizes, spacing presets).
    """
    scene: Scene
    store: Dict[str, Mobject]
    theme: Dict[str, Any]


@dataclass
class ActionResult:
    """
    Standardized return bundle from an action.

    Attributes
    ----------
    group : Mobject
        Main object created (often a VGroup grouping multiple sub-shapes).
    ids : dict[str, Mobject]
        Named handles for later steps (`id -> mobject`).
    animations : list[Animation]
        Animations to be played by the caller.
    postwait : float, default=0.0
        Optional pacing hint (seconds to wait after this action).
    """
    group: Mobject
    ids: Dict[str, Mobject]
    animations: List[Animation]
    postwait: float = 0.0


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, Callable[..., ActionResult]] = {}


def register(name: str):
    """
    Decorator to register a function as an action.

    Parameters
    ----------
    name : str
        Registry key to bind the action under.

    Returns
    -------
    Callable
        The original function (unchanged).

    Example
    -------
    >>> @register("box")
    ... def build_box(ctx: ActionContext, **kwargs) -> ActionResult:
    ...     return ActionResult(group=..., ids={"box": ...}, animations=[...])
    """
    def deco(fn: Callable[..., ActionResult]):
        _REGISTRY[name] = fn
        return fn
    return deco


def get_action(name: str) -> Callable[..., ActionResult]:
    """
    Retrieve an action function by name.

    Parameters
    ----------
    name : str
        Registry key used during registration.

    Returns
    -------
    Callable[..., ActionResult]
        The registered action function.

    Raises
    ------
    KeyError
        If no action has been registered under `name`.
    """
    return _REGISTRY[name]
