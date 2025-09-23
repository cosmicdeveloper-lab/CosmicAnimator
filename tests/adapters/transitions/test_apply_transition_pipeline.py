from manim import Square, VGroup, AnimationGroup
from cosmicanimator.adapters.transitions import fade_in_group, slide_in, Timing


def test_fade_in_group_returns_animationgroup():
    g = VGroup(Square(), Square())
    anim = fade_in_group(g.submobjects, run_time=0.2, timing=Timing(mode="simultaneous"))
    assert isinstance(anim, AnimationGroup)
    assert len(anim.animations) >= 2


def test_slide_in_returns_animationgroup():
    g = VGroup(Square(), Square())
    anim = slide_in(g.submobjects, direction="left", run_time=0.2, timing=Timing(mode="sequential"))
    assert isinstance(anim, AnimationGroup)
    assert len(anim.animations) >= 2
