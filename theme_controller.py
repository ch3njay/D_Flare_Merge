"""Global theme controller for the unified D-FLARE UI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import streamlit as st


@dataclass(frozen=True)
class ThemePalette:
    """Simple representation of a sidebar/button palette."""

    label: str
    start: str
    end: str
    text: str
    shadow: str
    sidebar_bg: str
    sidebar_text: str
    sidebar_border: str
    hover: str


THEMES: Dict[str, ThemePalette] = {
    "gradient-blue": ThemePalette(
        label="Gradient Blue",
        start="#38bdf8",
        end="#6366f1",
        text="#ffffff",
        shadow="0 22px 40px -22px rgba(99, 102, 241, 0.55)",
        sidebar_bg="#0f172a",
        sidebar_text="#e2e8f0",
        sidebar_border="rgba(148, 163, 184, 0.25)",
        hover="rgba(37, 99, 235, 0.15)",
    ),
    "gradient-red": ThemePalette(
        label="Gradient Red",
        start="#fb7185",
        end="#f97316",
        text="#ffffff",
        shadow="0 22px 40px -22px rgba(249, 115, 22, 0.55)",
        sidebar_bg="#1f0f17",
        sidebar_text="#f1f5f9",
        sidebar_border="rgba(248, 113, 113, 0.25)",
        hover="rgba(249, 115, 22, 0.18)",
    ),
    "glow-green": ThemePalette(
        label="Glow Green",
        start="#2dd4bf",
        end="#16a34a",
        text="#042f2e",
        shadow="0 22px 40px -22px rgba(34, 197, 94, 0.45)",
        sidebar_bg="#052e16",
        sidebar_text="#ecfdf5",
        sidebar_border="rgba(16, 185, 129, 0.28)",
        hover="rgba(16, 185, 129, 0.22)",
    ),
}

_DEFAULT_THEME = "gradient-blue"


def available_themes() -> Dict[str, str]:
    """Return mapping of theme key to display label."""

    return {key: palette.label for key, palette in THEMES.items()}


def apply_theme(theme: str | None = None) -> None:
    """Persist the chosen theme in session state and inject base styling."""

    theme_key = theme or st.session_state.get("active_theme", _DEFAULT_THEME)
    if theme_key not in THEMES:
        theme_key = _DEFAULT_THEME

    st.session_state["active_theme"] = theme_key
    palette = THEMES[theme_key]

    st.markdown(
        f"""
        <style>
        :root {{
            --df-sidebar-bg: {palette.sidebar_bg};
            --df-sidebar-text: {palette.sidebar_text};
            --df-sidebar-border: {palette.sidebar_border};
            --df-sidebar-hover: {palette.hover};
            --df-button-start: {palette.start};
            --df-button-end: {palette.end};
            --df-button-text: {palette.text};
            --df-button-shadow: {palette.shadow};
        }}
        div[data-testid="stSidebar"] {{
            background: var(--df-sidebar-bg);
            color: var(--df-sidebar-text);
        }}
        div[data-testid="stSidebar"] .sidebar-feature__title {{
            color: var(--df-sidebar-text);
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        div[data-testid="stSidebar"] hr {{
            border-color: var(--df-sidebar-border) !important;
        }}
        div[data-testid="stSidebar"] .sidebar-feature__actions {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
            gap: 0.35rem;
            margin-bottom: 0.75rem;
        }}
        div[data-testid="stSidebar"] .sidebar-feature__actions div.stButton > button,
        div[data-testid="stSidebar"] div.stButton > button {{
            background: linear-gradient(135deg, var(--df-button-start), var(--df-button-end));
            color: var(--df-button-text) !important;
            border: none;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            box-shadow: var(--df-button-shadow);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            padding: 0.45rem 0.6rem;
        }}
        div[data-testid="stSidebar"] .sidebar-feature__actions div.stButton > button:hover,
        div[data-testid="stSidebar"] div.stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 18px 30px -18px var(--df-button-start, rgba(15, 118, 110, 0.45));
        }}
        div[data-testid="stSidebar"] .sidebar-feature__note {{
            color: color-mix(in srgb, var(--df-sidebar-text), #94a3b8 45%);
            font-size: 0.78rem;
            margin-bottom: 0.75rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_button_style() -> str:
    """Return CSS snippet ensuring sidebar buttons use the active palette."""

    palette = THEMES[st.session_state.get("active_theme", _DEFAULT_THEME)]
    return (
        "<style>"
        "div[data-testid=\"stSidebar\"] div.stButton > button {"
        f"background: linear-gradient(135deg, {palette.start}, {palette.end});"
        f"color: {palette.text} !important;"
        "}"
        "</style>"
    )
