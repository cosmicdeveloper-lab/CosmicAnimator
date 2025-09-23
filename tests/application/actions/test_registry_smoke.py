from cosmicanimator.application.actions.base import get_action
# Importing actions registers them via decorators
from cosmicanimator.application.actions import render_title, boxes, diagrams, effects  # noqa: F401


def test_action_registered_render_title():
    fn = get_action("render_title")
    assert callable(fn)


def test_action_registered_layout_boxes():
    fn = get_action("layout_boxes")
    assert callable(fn)
