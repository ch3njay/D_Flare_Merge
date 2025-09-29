"""Theme controller for the unified dashboard UI.

This module provides theme management functionality, including built-in light/dark
themes and custom themes. It handles theme switching and style application while
maintaining compatibility with Streamlit's native theme system.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, Optional

import streamlit as st

# Theme configuration constants
THEME_LIGHT = "light" #這是淺色主題
THEME_DARK = "dark" #這是深色主題
THEME_CUSTOM = "custom" #這是自訂主題

ThemeType = Literal["light", "dark", "custom"]


_PREVIOUS_FONT_SCALE = 1.5
_FONT_SCALE = _PREVIOUS_FONT_SCALE * 0.8
_BASE_FONT_SIZES = {
    "h1": 26.0,  #這是標題的字體大小
    "h2": 22.0,  #這是次標題的字體大小
    "h3": 18.0,  #這是三級標題的字體大小
    "label": 16.0, #這是表單標籤的字體大小
    "body": 15.5,  #這是一般正文的字體大小
    "caption": 13.5,  #這是輔助說明文字的字體大小
}


def _scaled_font(value: float, scale: float = _FONT_SCALE) -> str:
    """Return the scaled font size string in px."""

    return f"{value * scale:.2f}px"


def _load_config_sample() -> str:  ##這是載入官方的config範本
    """Load the official Streamlit config sample shipped with the project."""

    sample_path = (
        Path(__file__).resolve().parent.parent / ".streamlit" / "config sample.toml"
    )
    try:
        return sample_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


@lru_cache(maxsize=1)  #這是用來快取logo的base64編碼
def _get_logo_data_uri() -> str: 
    """Return the base64 data URI for the dashboard logo if available."""

    potential_names = ("logo.png", "LOGO.png")
    base_dir = Path(__file__).resolve().parent.parent
    for name in potential_names:
        logo_path = base_dir / name
        if logo_path.exists():
            encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    return ""


def get_logo_data_uri() -> str:
    """Public accessor for the cached logo data URI used by other modules."""

    return _get_logo_data_uri()

st.markdown(  #這是引入外部的icon字型 確保icon可以正常顯示
    """
    <link rel="stylesheet" 
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <link rel="stylesheet" 
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    """,
    unsafe_allow_html=True
)

# Theme configurations mapping – enhanced with palette metadata so the UI feels richer.
THEME_CONFIGS: Dict[str, Dict[str, Any]] = {
    THEME_LIGHT: {
        "base": "light",
        "font_scale": _FONT_SCALE,
        "icon": '<i class="fa-solid fa-sun"></i>',
        "tagline": "柔和日光",
        "description": "亮色系搭配暖色重點，適合展示報表與簡報場景。",
        "palette": ["#FF6B2C", "#1ABC9C", "#38bdf8"],
        "hero_gradient": ("#f97316", "#ef4444"),
        "css_variables": {
            "surface-border": "#d9e2f1",
            "surface-shadow": "0 24px 54px -34px rgba(15, 23, 42, 0.22)",
            "card-background": "#ffffff",
            "card-border": "#d9e2f1",
            "card-hover-shadow": "0 28px 60px -32px rgba(255, 107, 44, 0.35)",
            "primary-gradient-start": "#FF6B2C",
            "primary-gradient-end": "#FF834D",
            "button-shadow": "0 18px 36px -20px rgba(255, 107, 44, 0.46)",
            "sidebar-background": "#f1f5f9",
            "sidebar-text": "#0f172a",
            "sidebar-muted": "#64748b",
        },
    },
    THEME_DARK: {
        "base": "dark",
        "font_scale": _FONT_SCALE,
        "icon": '<i class="fa-solid fa-moon"></i>',
        "tagline": "夜幕量測",
        "description": "高對比與霓虹重點，適合控制台與監控儀表板。",
        "palette": ["#1ABC9C", "#6366f1", "#facc15"],
        "hero_gradient": ("#1a2a6c", "#b21f1f"),
        "css_variables": {
            "surface-border": "rgba(120, 144, 180, 0.34)",
            "surface-shadow": "0 42px 88px -48px rgba(4, 8, 20, 0.9)",
            "card-background": "rgba(9, 16, 32, 0.88)",
            "card-border": "rgba(120, 144, 180, 0.34)",
            "card-hover-shadow": "0 36px 72px -42px rgba(5, 10, 22, 0.92)",
            "primary-gradient-start": "#1ABC9C",
            "primary-gradient-end": "#6366f1",
            "button-shadow": "0 20px 44px -28px rgba(99, 102, 241, 0.55)",
            "sidebar-background": "#060f1f",
            "sidebar-text": "#f8fafc",
            "sidebar-muted": "#94a3b8",
        },
    },
    THEME_CUSTOM: {
        "base": "dark",
        "font_scale": _FONT_SCALE,
        "icon": '<i class="fa-solid fa-palette"></i>',
        "tagline": "自訂調色盤",
        "description": "依照 config 設定調整品牌色彩，適合客製化展示。",
        "palette": ["#f97316", "#38bdf8", "#9b59b6"],
        "hero_gradient": ("#38bdf8", "#9b59b6"),
        "css_variables": {
            "surface-border": "rgba(120, 144, 180, 0.28)",
            "surface-shadow": "0 32px 70px -40px rgba(8, 15, 35, 0.85)",
            "card-background": "rgba(10, 18, 40, 0.88)",
            "card-border": "rgba(120, 144, 180, 0.28)",
            "card-hover-shadow": "0 28px 64px -38px rgba(59, 130, 246, 0.48)",
            "primary-gradient-start": "#38bdf8",
            "primary-gradient-end": "#9b59b6",
            "button-shadow": "0 20px 48px -30px rgba(59, 130, 246, 0.65)",
            "sidebar-background": "rgba(8, 15, 35, 0.94)",
            "sidebar-text": "#ffffff",
            "sidebar-muted": "#cbd5f5",
        },
    },
}

def _init_theme_state() -> None:
    """Initialize theme-related session state if not already present."""
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = THEME_DARK
    if "theme_initialized" not in st.session_state:
        st.session_state.theme_initialized = False

def _generate_css_variables(theme_config: Dict[str, Any]) -> Iterable[str]:
    """Generate CSS custom property declarations for the theme."""

    variables = theme_config.get("css_variables", {})
    for key, value in variables.items():
        yield f"--theme-customTheme-{key}: {value};"

    font_scale = float(theme_config.get("font_scale", _FONT_SCALE))
    for name, size in _BASE_FONT_SIZES.items():
        yield f"--font-{name}: {_scaled_font(size, font_scale)};"


def _apply_theme_styles(theme_config: Dict[str, Any]) -> None:
    """Apply theme-specific styles using custom CSS."""

    css_variables = "\n            ".join(_generate_css_variables(theme_config))
    font_scale = float(theme_config.get("font_scale", _FONT_SCALE))

    st.markdown(
        f"""
        <style>
        :root {{
            color-scheme: {theme_config['base']};
            --theme-font-scale: {font_scale};
            {css_variables}
        }}

        html {{
            font-size: {font_scale * 100:.0f}%;
        }}

        body, [class^="st-"], [class*=" st-"], div[data-testid="stMarkdown"], section[data-testid="stSidebar"], .stButton > button {{
            font-size: var(--font-body) !important;
            line-height: 1.6 !important;
        }}

        h1 {{ font-size: var(--font-h1) !important; }}
        h2 {{ font-size: var(--font-h2) !important; }}
        h3 {{ font-size: var(--font-h3) !important; }}
        label {{ font-size: var(--font-label) !important; }}
        small, .stCaption, .stMarkdown small {{ font-size: var(--font-caption) !important; }}

        section[data-testid="stSidebar"] {{
            background: var(--theme-customTheme-sidebar-background);
            color: var(--theme-customTheme-sidebar-text);
        }}

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color: var(--theme-customTheme-sidebar-muted);
        }}

        .theme-switcher__brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.85rem;
        }}

        .theme-switcher__logo {{
            width: 42px;
            height: 42px;
            object-fit: contain;
            flex-shrink: 0;
        }}

        .theme-switcher__brand-text {{
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }}

        .theme-switcher__brand-title {{
            font-size: calc(var(--font-h1) * 1.4);
            font-weight: 800;
            line-height: 1.1;
            color: var(--theme-customTheme-sidebar-text);
        }}

        .theme-switcher__brand-subtitle {{
            font-size: calc(var(--font-label) * 0.95);
            color: var(--theme-customTheme-sidebar-muted);
            letter-spacing: 0.04em;
        }}

        .theme-switcher__header {{
            padding: 0.75rem 0 0.35rem 0;
        }}

        .theme-switcher__subtitle {{
            font-size: calc(var(--font-body) - 0.4px);
            opacity: 0.82;
            margin-bottom: 0.65rem;
        }}

        .theme-switcher div[data-testid="stRadio"] > div[role="radiogroup"] {{
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }}

        .theme-switcher div[data-testid="stRadio"] > div[role="radiogroup"] > div {{
            margin: 0 !important;
        }}

        .theme-switcher div[data-testid="stRadio"] label {{
            border-radius: 1rem;
            border: 1px solid var(--muted-border);
            padding: 0.75rem 0.95rem;
            background: var(--app-surface);
            display: flex;
            align-items: center;
            gap: 0.65rem;
            font-weight: 600;
            font-size: var(--font-label);
            color: var(--sidebar-text);
            cursor: pointer;
            transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, color 0.2s ease;
        }}

        .theme-switcher div[data-testid="stRadio"] label:hover {{
            border-color: var(--primary);
            box-shadow: var(--hover-glow);
        }}

        .theme-switcher div[data-testid="stRadio"] label > div:first-child {{
            display: none;
        }}

        .theme-switcher div[data-testid="stRadio"] input[type="radio"] {{
            display: none;
        }}

        .theme-switcher div[data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]) {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #ffffff;
            border-color: transparent;
            box-shadow: var(--hover-glow);
        }}

        .theme-preview {{
            border-radius: 1.25rem;
            padding: 1.2rem 1.4rem;
            margin-top: 0.9rem;
            color: rgba(255, 255, 255, 0.95);
        }}

        .theme-preview__eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: calc(var(--font-caption) + 1px);
            opacity: 0.82;
        }}

        .theme-preview__title {{
            font-size: calc(var(--font-h2) + 2px);
            font-weight: 700;
            margin: 0.2rem 0;
        }}

        .theme-preview__description {{
            font-size: calc(var(--font-body));
            margin-bottom: 0.85rem;
            opacity: 0.92;
        }}

        .theme-preview__palette {{
            display: flex;
            gap: 0.6rem;
        }}

        .theme-preview__swatch {{
            width: 38px;
            height: 38px;
            border-radius: 0.75rem;
            border: 2px solid rgba(255, 255, 255, 0.5);
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
        }}

        .feature-card {{
            background: var(--theme-customTheme-card-background);
            border: 1px solid var(--theme-customTheme-card-border);
            border-radius: 1.1rem;
            padding: 1.5rem;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
            box-shadow: var(--theme-customTheme-surface-shadow);
        }}

        .feature-card:hover {{
            transform: translateY(-3px);
            box-shadow: var(--theme-customTheme-card-hover-shadow);
        }}

        .stButton > button {{
            background: linear-gradient(
                135deg,
                var(--theme-customTheme-primary-gradient-start),
                var(--theme-customTheme-primary-gradient-end)
            ) !important;
            border: 1px solid transparent !important;
            border-radius: 0.75rem !important;
            color: white !important;
            font-weight: 700 !important;
            padding: 0.85rem 1.5rem !important;
            box-shadow: var(--theme-customTheme-button-shadow) !important;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: var(--theme-customTheme-card-hover-shadow) !important;
        }}

        .theme-config-tip {{
            font-size: calc(var(--font-caption) + 1px);
            color: var(--theme-customTheme-sidebar-muted);
            margin-top: 0.5rem;
        }}

        .theme-config-tip a {{
            color: inherit;
            text-decoration: underline;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Theme name constants
THEME_DISPLAY_NAMES = {
    THEME_DARK: "深色",
    THEME_LIGHT: "淺色",
    THEME_CUSTOM: "自訂"
}

# Theme name to theme key mapping
THEME_NAME_MAP = {v: k for k, v in THEME_DISPLAY_NAMES.items()}


def switch_theme(theme: ThemeType) -> None:
    """Switch to the specified theme and apply its styles.
    
    Args:
        theme: The theme to switch to ("light", "dark", or "custom").
    """
    _init_theme_state()
    
    # Update theme only if changed
    should_apply = st.session_state.current_theme != theme or not st.session_state.get(
        "theme_initialized", False
    )

    if should_apply:
        st.session_state.current_theme = theme
        config = THEME_CONFIGS[theme]
        _apply_theme_styles(config)
        st.session_state.theme_initialized = True


def _render_theme_palette(colors: Iterable[str]) -> str:
    """Render palette swatches for the current theme."""

    return "".join(
        f"<span class='theme-preview__swatch' title='{color}' style='background:{color};'></span>"
        for color in colors
    )


def render_theme_switcher() -> None:
    """在側邊欄應用全域樣式，並提供更直覺的主題切換介面。"""

    with st.sidebar:
        _init_theme_state()

        current_theme = get_current_theme()
        # Apply CSS once we know the current theme
        switch_theme(current_theme)

        logo_src = _get_logo_data_uri()
        brand_markup = """
            <div class="theme-switcher__brand">
                <div class="theme-switcher__brand-text">
                    <div class="theme-switcher__brand-title">D-FLARE Unified</div>
                    <div class="theme-switcher__brand-subtitle">介面主題中心</div>
                </div>
            </div>
        """
        if logo_src:
            brand_markup = (
                """
                <div class="theme-switcher__brand">
                    <img src="{logo}" alt="D-FLARE logo" class="theme-switcher__logo" />
                    <div class="theme-switcher__brand-text">
                        <div class="theme-switcher__brand-title">D-FLARE Unified</div>
                        <div class="theme-switcher__brand-subtitle">介面主題中心</div>
                    </div>
                </div>
                """.format(logo=logo_src)
            )

        st.markdown('<div class="theme-switcher">', unsafe_allow_html=True)
        st.markdown(brand_markup, unsafe_allow_html=True)

        if "theme_switcher" not in st.session_state:
            st.session_state.theme_switcher = current_theme

        with st.expander("🎨 介面主題", expanded=False):
            st.markdown(
                """
                <div class="theme-switcher__header">
                    <div class="theme-switcher__subtitle">選擇符合情境的色彩與層次，或參考官方 config 延伸客製。</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            theme_options = list(THEME_DISPLAY_NAMES.keys())

            selection = st.radio(
                "選擇主題",
                theme_options,
                format_func=lambda key: f"{THEME_CONFIGS[key]['icon']} {THEME_DISPLAY_NAMES[key]}",
                horizontal=False,
                key="theme_switcher",
                label_visibility="collapsed",
            )

            st.markdown(
                """
                <style>
                .theme-switcher div[role="radiogroup"] label span {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .theme-switcher div[role="radiogroup"] label span i {
                    font-size: 1rem;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            switch_theme(selection)

            preview_config = THEME_CONFIGS[selection]
            gradient_start, gradient_end = preview_config.get("hero_gradient", ("#6366f1", "#8b5cf6"))
            palette_html = _render_theme_palette(preview_config.get("palette", []))

            st.markdown(
                f"""
                <div class="theme-preview" style="background: linear-gradient(135deg, {gradient_start}, {gradient_end});">
                    <div class="theme-preview__eyebrow">{preview_config.get('tagline', '')}</div>
                    <div class="theme-preview__title">{preview_config.get('icon', '')} {THEME_DISPLAY_NAMES[selection]}</div>
                    <p class="theme-preview__description">{preview_config.get('description', '')}</p>
                    <div class="theme-preview__palette">{palette_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        sample = _load_config_sample()
        if sample:
            with st.expander("想要更多自訂？查看官方 config 樣板"):
                st.markdown(
                    "利用 `.streamlit/config.toml` 可與下方範例同步調整 Streamlit 的原生主題設定。",
                    unsafe_allow_html=False,
                )
                st.code(sample, language="toml")

        st.markdown("</div>", unsafe_allow_html=True)


def get_current_theme() -> str:
    """Get the name of the currently active theme.
    
    Returns:
        The current theme name ("light", "dark", or "custom").
    """
    _init_theme_state()
    return st.session_state.current_theme


def get_theme_config(theme: Optional[ThemeType] = None) -> Dict[str, Any]:
    """Get the configuration for the specified theme.
    
    Args:
        theme: Optional theme name. If None, returns current theme's config.
    
    Returns:
        Dictionary containing theme configuration parameters.
    """
    if theme is None:
        theme = get_current_theme()
    return THEME_CONFIGS[theme].copy()


def add_custom_theme(
    name: str,
    config: Dict[str, Any],
) -> None:
    """Add a new custom theme configuration.
    
    Args:
        name: Unique name for the custom theme.
        config: Theme configuration dictionary.
    
    Raises:
        ValueError: If name conflicts with built-in themes.
    """
    if name in {THEME_LIGHT, THEME_DARK}:
        raise ValueError(f"Cannot override built-in theme: {name}")
    THEME_CONFIGS[name] = config.copy()
