# src/cosmicanimator/core/theme.py

"""
A thin, future-proof wrapper around constants.py that:
Exposes clear getters (get_role, get_glow, get_stroke, default_role, arrow_style, etc.)
Adds robust fallbacks for unknown keys
Supports overrides so you can compose custom themes without touching constants.py
Keeps helpers for timing/layout/typography in one place
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Mapping
from cosmicanimator.core import constants as c


def _merge_dicts(base: Mapping[str, Any], override: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """
    Shallow-merge two dictionaries.
    - Keys in override replace keys in base.
    - If override is None, return a copy of base.
    This keeps merging predictable and cheap. For nested structures, pass
    the exact sub-dicts you want to override.
    """
    out = dict(base)
    if override:
        out.update(override)
    return out


class Theme:
    """
    Theme provides a stable API to query style presets (roles, glow bands,
    strokes, text variants, arrow styles) and layout/timing helpers.

    You can create a Theme with optional overrides to experiment without
    editing `constants.py`. For example:

        custom = Theme(
            role_triplets={"highlight": {"fill": "#FFD166", "stroke": "#CCAA33", "glow": "#8C6D1F"}},
            text_variants={"title": {"font_size": "title", "color": "secondary", "weight": "HEAVY", "uppercase": True}},
            arrow_styles={"default": _merge_dicts(c.ARROW_STYLES["default"], {"stroke_width": 9.0})},
        )

    All getters apply robust fallbacks:
    - Unknown role         → "primary"
    - Unknown glow preset  → c.GLOW_DEFAULT["bands_key"]
    - Unknown stroke name  → "normal"
    - Unknown text variant → "label"
    - Unknown arrow style  → "default"
    """

    # ---- Construction -----------------------------------------------------

    def __init__(
        self,
        *,
        # allow named palette theme override (light/dark or custom keys added in constants.PALETTES)
        theme_name: Optional[str] = None,
        # optional shallow overrides per-family:
        palette: Optional[Mapping[str, str]] = None,
        role_triplets: Optional[Mapping[str, Dict[str, str]]] = None,
        stroke_widths: Optional[Mapping[str, float]] = None,
        glow_bands: Optional[Mapping[str, List[Tuple[float, float]]]] = None,
        text_variants: Optional[Mapping[str, Dict[str, Any]]] = None,
        arrow_styles: Optional[Mapping[str, Dict[str, Any]]] = None,
        defaults: Optional[Mapping[str, Any]] = None,
        profiles: Optional[Mapping[str, Dict[str, Any]]] = None,
        canvas: Optional[Mapping[str, Dict[str, Any]]] = None,
        video_profile: Optional[str] = None,
        speaker: Optional[str] = None,
        tts_model: Optional[str] = None,
    ) -> None:
        # capture selected profile name (falls back to constants.VIDEO_PROFILE)
        self._video_profile: str = video_profile or getattr(c, "VIDEO_PROFILE", "short")

        # Palette resolution: start from active palette for chosen theme_name (or c.ACTIVE_THEME)
        base_theme_name = theme_name or getattr(c, "ACTIVE_THEME", "light")
        base_palette = c.PALETTES.get(base_theme_name, c.PALETTES.get("light", {}))
        self._palette: Dict[str, str] = _merge_dicts(base_palette, palette)

        # Primary stores (shallow copies with optional overrides)
        self._role_triplets: Dict[str, Dict[str, str]] = _merge_dicts(getattr(c, "ROLE_TRIPLETS", {}), role_triplets)
        self._stroke_widths: Dict[str, float] = _merge_dicts(getattr(c, "STROKE_WIDTHS", {}), stroke_widths)
        self._glow_bands: Dict[str, List[Tuple[float, float]]] = _merge_dicts(getattr(c, "GLOW_BANDS", {}), glow_bands)
        self._text_variants: Dict[str, Dict[str, Any]] = _merge_dicts(getattr(c, "TEXT_VARIANTS", {}), text_variants)
        self._arrow_styles: Dict[str, Dict[str, Any]] = _merge_dicts(getattr(c, "ARROW_STYLES", {}), arrow_styles)
        self._defaults: Dict[str, Any] = _merge_dicts(getattr(c, "DEFAULTS", {}), defaults)

        # Profiles/canvas (so your layout/time helpers remain consistent)
        self._profiles: Dict[str, Dict[str, Any]] = _merge_dicts(getattr(c, "PROFILES", {}), profiles)
        self._canvas: Dict[str, Dict[str, Any]] = _merge_dicts(getattr(c, "CANVAS", {}), canvas)
        self._speaker: str = speaker or getattr(c, "SPEAKER", "p364")
        self._tts_model: str = tts_model or getattr(c, "TTS_MODEL", "tts_models/en/vctk/vits")

        # Handy cached fallbacks
        self._fallback_role = "primary"
        self._fallback_stroke = "normal"
        self._fallback_text = "label"
        self._fallback_arrow = "default"
        self._fallback_glow_key = getattr(c, "GLOW_DEFAULT", {}).get("bands_key", "neon")

    # ---- Factories --------------------------------------------------------

    def with_overrides(
        self,
        **kwargs: Any,
    ) -> "Theme":
        """
        Return a new Theme that reuses this theme as base and applies additional overrides.
        Example:
            neon = current_theme.with_overrides(arrow_styles={"default": {"glow_layers": 4}})
        """
        return Theme(
            theme_name=kwargs.get("theme_name"),
            palette=_merge_dicts(self._palette, kwargs.get("palette")),
            role_triplets=_merge_dicts(self._role_triplets, kwargs.get("role_triplets")),
            stroke_widths=_merge_dicts(self._stroke_widths, kwargs.get("stroke_widths")),
            glow_bands=_merge_dicts(self._glow_bands, kwargs.get("glow_bands")),
            text_variants=_merge_dicts(self._text_variants, kwargs.get("text_variants")),
            arrow_styles=_merge_dicts(self._arrow_styles, kwargs.get("arrow_styles")),
            defaults=_merge_dicts(self._defaults, kwargs.get("defaults")),
            profiles=_merge_dicts(self._profiles, kwargs.get("profiles")),
            canvas=_merge_dicts(self._canvas, kwargs.get("canvas")),
            video_profile=kwargs.get("video_profile", self._video_profile),
            speaker=kwargs.get("speaker", self._speaker),
            tts_model=kwargs.get("tts_model", self._tts_model),
        )

    # ---- Palette/Color ----------------------------------------------------

    def get_color(self, name: str) -> str:
        """
        Resolve a color name from the active palette (or raw hex if already hex-like).
        Fallback: constants.DEFAULT_TEXT_COLOR.
        """
        if isinstance(name, str) and name.startswith("#") and len(name) in (4, 7):
            return name
        return self._palette.get(name, getattr(c, "DEFAULT_TEXT_COLOR", "#FFFFFF"))

    @property
    def background_color(self) -> str:
        """Active background color."""
        key = getattr(c, "BACKGROUND_COLOR", None)
        return key if isinstance(key, str) and key.startswith("#") else self.get_color("bg")

    # ---- Roles / Strokes / Glow / Text / Arrows ---------------------------

    def get_role(self, role: Optional[str]) -> Dict[str, str]:
        """
        Return {'fill','stroke','glow'} for a semantic role.
        Fallback: 'primary'.
        """
        key = (role or self._fallback_role).strip().lower()
        return self._role_triplets.get(key, self._role_triplets[self._fallback_role])

    def get_stroke(self, kind: Optional[str]) -> float:
        """
        Return a stroke width by name ('thin'|'normal'|'thick'|'extra_thick').
        Fallback: 'normal'.
        """
        key = (kind or self._fallback_stroke).strip().lower()
        return self._stroke_widths.get(key, self._stroke_widths[self._fallback_stroke])

    def get_glow(self, preset: Optional[str]) -> List[Tuple[float, float]]:
        """
        Return glow bands preset list of (width_multiplier, opacity).
        Fallback: GLOW_DEFAULT['bands_key'] from constants.
        """
        key = (preset or "").strip().lower()
        if key in self._glow_bands:
            return self._glow_bands[key]
        return self._glow_bands.get(self._fallback_glow_key, next(iter(self._glow_bands.values()), []))

    def get_text_variant(self, name: Optional[str]) -> Dict[str, Any]:
        key = (name or self._fallback_text)
        variant = self._text_variants.get(key, self._text_variants[self._fallback_text])
        return variant

    def arrow_style(self, name: Optional[str]) -> Dict[str, Any]:
        """
        Return an arrow style config. Fallback: 'default'.
        """
        key = (name or self._fallback_arrow)
        return self._arrow_styles.get(key, self._arrow_styles[self._fallback_arrow])

    # ---- Defaults ---------------------------------------------------------

    def default_role(self) -> str:
        """Semantic default role name."""
        return self._defaults.get("color", self._fallback_role)

    def default_arrow_style_key(self) -> str:
        """Arrow style key string (not the dict)."""
        return self._defaults.get("arrow_style", self._fallback_arrow)

    # ---- Timing / Layout / Typography ------------------------------------

    @property
    def video_profile(self) -> str:
        """Active video profile name (e.g. 'short'|'long'|'square')."""
        return self._video_profile

    def get_speaker(self) -> str:
        """Speaker id (e.g. 'p365'|'p225'|...)."""
        return self._speaker

    def get_tts_model(self) -> str:
        """TTS model id/path (e.g. 'tts_models/en/vctk/vits')."""
        return self._tts_model

    def _p(self, section: str, key: str) -> Any:
        return self._profiles.get(self._video_profile, {}).get(section, {}).get(key)

    def timing(self, name: str) -> float:
        """Get a timing value by key (e.g. 'fade', 'zoom')."""
        val = self._p("timing", name)
        if val is None:
            # fall back to constants helper if present
            try:
                return float(c.timing(name))
            except Exception:
                return 0.5
        return float(val)

    def spacing(self) -> float:
        """Base spacing for layout."""
        val = self._p("layout", "spacing")
        if val is None:
            try:
                return float(c.spacing())
            except Exception:
                return 1.5
        return float(val)

    def base_scale(self) -> float:
        """Base scale multiplier for glyphs/shapes."""
        val = self._p("layout", "scale")
        if val is None:
            try:
                return float(c.base_scale())
            except Exception:
                return 1.0
        return float(val)

    def font_px(self, size_key: str) -> int:
        """
        Resolve a named text size to an integer pixel size using the active profile.
        """
        sizes = self._profiles.get(self._video_profile, {}).get("type", {})
        if size_key in sizes:
            return int(sizes[size_key])
        # fallback to constants helper
        try:
            return int(c.font_size(size_key))
        except Exception:
            return int(sizes.get("label", 24) if sizes else 24)

    # ---- Canvas helpers ---------------------------------------------------

    @property
    def canvas_aspect(self) -> str:
        return self._canvas.get(self._video_profile, {}).get("aspect", getattr(c, "ASPECT", "vertical"))

    @property
    def canvas_resolution(self) -> Tuple[int, int]:
        return tuple(self._canvas.get(self._video_profile, {}).get("resolution", getattr(c, "RESOLUTION", (1080, 1920))))  # type: ignore

    @property
    def canvas_safe(self) -> Dict[str, float]:
        return dict(self._canvas.get(self._video_profile, {}).get("safe", getattr(c, "SAFE", {})))

    # ---- Interop (constants-style helpers) --------------------------------

    def get_color_hex(self, name: str) -> str:
        """Alias to match constants.get_color for easier swapping."""
        try:
            return c.get_color(name)  # type: ignore[attr-defined]
        except Exception:
            return self.get_color(name)

    # ---- Debug/Introspection ----------------------------------------------

    def describe(self) -> Dict[str, Any]:
        """Return a snapshot of key style families for quick inspection/logging."""
        return {
            "video_profile": self._video_profile,
            "palette_keys": sorted(self._palette.keys()),
            "roles": sorted(self._role_triplets.keys()),
            "strokes": sorted(self._stroke_widths.keys()),
            "glow_presets": sorted(self._glow_bands.keys()),
            "text_variants": sorted(self._text_variants.keys()),
            "arrow_styles": sorted(self._arrow_styles.keys()),
            "defaults": dict(self._defaults),
        }


# A ready-to-use theme that follows constants.py exactly.
current_theme = Theme()
