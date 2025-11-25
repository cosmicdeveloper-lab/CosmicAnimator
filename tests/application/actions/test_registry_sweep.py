import importlib
import types
import pytest


def _load_action_registry():
    base = importlib.import_module("cosmicanimator.application.actions.base")
    # Try common names to stay compatible with your base module
    for attr in ("_REGISTRY", "ACTIONS_REGISTRY"):
        reg = getattr(base, attr, None)
        if isinstance(reg, dict) and reg:
            return base, reg
    # Fallback: use accessor if present
    get_all = getattr(base, "get_all_actions", None)
    if callable(get_all):
        return base, get_all()
    pytest.skip("No public action registry found in actions.base")


def test_all_registered_actions_callable():
    # Importing the package registers actions via decorators
    import cosmicanimator.application.actions  # noqa: F401
    # Also import known modules to ensure their decorators run
    from cosmicanimator.application.actions import render_title, boxes, diagrams, effects  # noqa: F401

    base, registry = _load_action_registry()
    get_action = getattr(base, "get_action", None)
    assert callable(get_action), "actions.base.get_action must be callable"

    assert len(registry) > 0, "No actions registered"
    for name in list(registry.keys())[:64]:  # cap to keep the test speedy
        fn = get_action(name)
        assert callable(fn), f"Action '{name}' is not callable"


def test_transitions_module_importable():
    # A light smoke test that transitions package is importable and exposes helpers
    mod = importlib.import_module("cosmicanimator.adapters.transitions")
    # Accept either module objects or functions hanging off the package
    has_any = any(
        isinstance(getattr(mod, attr, None), (types.FunctionType, types.ModuleType))
        for attr in ("blackhole", "pulsar", "hawking_radiation", "pulsar")
    )
    assert has_any, "No transitions found on adapters.transitions"
