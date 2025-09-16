from manim import VGroup
from cosmicanimator.application.actions.diagrams import layout_branch


class _Ctx:
    def __init__(self):
        self.store = {}


def test_layout_branch_ids_and_counts_defaults():
    # No labels → defaults become 'root', 'child1..n', 'arrow1..n'
    ctx = _Ctx()
    res = layout_branch(
        ctx,
        root_label="",          # ensure 'root'
        child_count=3,          # ensure 'child1..child3'
        child_labels=None,      # ensure 'child*' instead of label-based IDs
        direction="down",
        appear="none",
    )
    assert isinstance(res.group, VGroup)
    for key in ("root", "child1", "child2", "child3", "arrow1", "arrow2", "arrow3"):
        assert key in res.ids, f"Missing id: {key}"
        assert key in ctx.store, f"Context store missing id: {key}"

    root = res.ids["root"]
    c1, c2, c3 = (res.ids["child1"], res.ids["child2"], res.ids["child3"])
    assert c1.get_center()[1] < root.get_center()[1]
    assert c2.get_center()[1] < root.get_center()[1]
    assert c3.get_center()[1] < root.get_center()[1]


def test_layout_branch_direction_up_positions_defaults():
    # Also keep defaults so id 'root' exists
    ctx = _Ctx()
    res = layout_branch(
        ctx,
        root_label="",
        child_count=2,
        child_labels=None,
        direction="up",
        appear="none",
    )
    root = res.ids["root"]
    x = res.ids["child1"]
    y = res.ids["child2"]
    assert x.get_center()[1] > root.get_center()[1]
    assert y.get_center()[1] > root.get_center()[1]
