from manim import Square, VGroup, AnimationGroup
from cosmicanimator.adapters.transitions import reveal, shine


def test_fade_in_group_returns_animationgroup():
    g = VGroup(Square(), Square())
    anim = reveal(g.submobjects, run_time=0.2)
    assert isinstance(anim, AnimationGroup)
    assert len(anim.animations) >= 2


def test_slide_in_returns_animationgroup():
    g = VGroup(Square(), Square())
    anim = shine(g.submobjects)
    assert isinstance(anim, AnimationGroup)
    assert len(anim.animations) >= 2
