from cosmicanimator.adapters.style.style_helpers import is_hex_color, resolve_role_or_hex


def test_is_hex_color():
    assert is_hex_color("#fff")
    assert is_hex_color("#FFFFFF")
    assert not is_hex_color("fff")
    assert not is_hex_color("#FFFF")
    assert not is_hex_color(123)  # type: ignore


def test_resolve_role_or_hex_primary_role():
    d = resolve_role_or_hex("primary")
    assert "color" in d and "stroke" in d and "glow" in d
    for k in ("color", "stroke", "glow"):
        assert isinstance(d[k], str) and d[k].startswith("#")


def test_resolve_role_or_hex_hex_passthrough():
    d = resolve_role_or_hex("#112233")
    assert d["color"] == "#112233"
    assert d["stroke"] == "#112233"
    assert d["glow"] == "#112233"
