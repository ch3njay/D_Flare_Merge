"""Shared CSS helpers for keeping brand styling consistent across apps."""

from __future__ import annotations

from collections import OrderedDict
from textwrap import dedent
from typing import Iterable, Mapping

# Central color alias definitions map higher-level semantic variables to
# brand/theme specific primitives.  ``render_color_aliases`` exposes them for
# inline CSS templates while still allowing per-call overrides.
_COLOR_ALIAS_DEFAULTS = OrderedDict[
    tuple[str, str]
]([
    (
        "--primary-color",
        "var(--theme-customTheme-primary-color, var(--primary, var(--primaryColor)))",
    ),
    (
        "--secondary-color",
        "var(--theme-customTheme-secondary-color, var(--secondary-start, var(--primaryColor)))",
    ),
    (
        "--button-box-shadow",
        "var(--theme-customTheme-button-shadow, 0 18px 36px -22px color-mix(in srgb, var(--primaryColor) 55%, transparent))",
    ),
    (
        "--button-box-shadow-hover",
        "var(--theme-customTheme-button-shadow-hover, 0 0 10px color-mix(in srgb, var(--primaryColor) 60%, transparent))",
    ),
])


def render_color_aliases(
    *, indent: int = 12, overrides: Mapping[str, str] | None = None
) -> str:
    """Return formatted CSS custom property declarations for shared aliases."""

    values = dict(_COLOR_ALIAS_DEFAULTS)
    if overrides:
        values.update(overrides)
    pad = " " * indent
    return "\n".join(f"{pad}{name}: {value};" for name, value in values.items())


def gradient_button_css(
    selectors: Iterable[str] | None = None, *, indent: int = 8
) -> str:
    """Return a gradient button CSS block shared by the unified dashboards."""

    targets = tuple(selectors or (".stButton > button",))
    base_selectors = ",\n".join(f"{' ' * indent}{selector}" for selector in targets)
    hover_selectors = ",\n".join(
        f"{' ' * indent}{selector}:hover" for selector in targets
    )
    focus_selectors = ",\n".join(
        f"{' ' * indent}{selector}:focus-visible" for selector in targets
    )
    return dedent(
        f"""
        {base_selectors} {{
            background-color: var(--primary-color);
            background-image: linear-gradient(
                135deg,
                var(--primary-color),
                var(--secondary-color)
            );
            color: #fff !important;
            border: none !important;
            border-radius: 0.5rem !important;
            padding: 0.4rem 1rem !important;
            font-weight: 600 !important;
            box-shadow: var(--button-box-shadow) !important;
            transition: all 0.3s ease-in-out !important;
        }}

        {hover_selectors} {{
            box-shadow: var(--button-box-shadow-hover) !important;
            transform: translateY(-1px) !important;
        }}

        {focus_selectors} {{
            outline: 2px solid color-mix(in srgb, var(--secondary-color) 55%, transparent);
            outline-offset: 2px;
        }}
        """
    ).strip()


def color_mix_fallback_css(*, indent: int = 8) -> str:
    """Provide graceful fallbacks when ``color-mix`` is unavailable."""

    pad = " " * indent
    return dedent(
        f"""
        @supports not (color: color-mix(in srgb, red 50%, white 50%)) {{
        {pad}:root {{
        {pad}    --secondary-color: var(--theme-customTheme-secondary-color, var(--primary-color));
        {pad}    --button-box-shadow: var(--theme-customTheme-button-shadow, 0 18px 36px -22px rgba(0, 0, 0, 0.25));
        {pad}    --button-box-shadow-hover: var(--theme-customTheme-button-shadow-hover, 0 0 10px rgba(0, 0, 0, 0.35));
        {pad}}}
        }}
        """
    ).strip()


def sidebar_icon_visibility_css(*, indent: int = 8) -> str:
    """Return CSS ensuring sidebar icons remain visible after theme swaps."""

    pad = " " * indent

    comment_pad = " " * max(indent - 4, 0)
    return dedent(
        f"""
        {comment_pad}/* Sidebar 功能目錄 icon 強制顯示 */

        {pad}section[data-testid="stSidebar"] svg,
        {pad}section[data-testid="stSidebar"] i {{
        {pad}    display: inline-block !important;
        {pad}    opacity: 1 !important;
        {pad}    visibility: visible !important;
        {pad}    margin-right: 0.5rem;
        {pad}}}
        """
    ).strip()


__all__ = [
    "color_mix_fallback_css",
    "gradient_button_css",
    "render_color_aliases",
    "sidebar_icon_visibility_css",
]
