"""Utility helpers for global styling and branding assets."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import streamlit as st

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli as tomllib  # type: ignore[no-redef]

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_ASSET_ROOT = Path(__file__).resolve().parent / "assets"
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _PROJECT_ROOT / ".streamlit" / "config.toml"

_KEY_OVERRIDES = {
    "bodyFont": "font-body",
    "headingFont": "font-heading",
    "codeFont": "font-code",
    "baseFontSize": "base-font-size",
    "headingFontWeight": "heading-font-weight",
    "bodyFontWeight": "body-font-weight",
}


def _camel_to_kebab(name: str) -> str:
    buffer: list[str] = []
    for idx, ch in enumerate(name):
        if ch.isupper() and idx > 0 and not name[idx - 1].isupper():
            buffer.append("-")
        buffer.append(ch.lower())
    return "".join(buffer)


def _to_css_var(name: str) -> str:
    token = _KEY_OVERRIDES.get(name, _camel_to_kebab(name))
    token = token.strip("-")
    return f"--df-{token}"


@lru_cache(maxsize=1)
def _load_theme_variables() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Parse custom theme tokens from config.toml."""

    if not _CONFIG_PATH.exists():
        return {}, {}

    try:
        data = tomllib.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):  # pragma: no cover - invalid config
        return {}, {}

    theme = data.get("theme", {}) or {}

    base_vars: Dict[str, str] = {}
    dark_vars: Dict[str, str] = {}

    for section in ("typography", "tokens"):
        payload = theme.get(section) or {}
        for key, value in payload.items():
            base_vars[_to_css_var(key)] = value

    light_section = theme.get("light") or {}
    for section in ("tokens", "gradients"):
        payload = light_section.get(section) or {}
        for key, value in payload.items():
            base_vars[_to_css_var(key)] = value

    dark_section = theme.get("dark") or {}
    for section in ("tokens", "gradients"):
        payload = dark_section.get(section) or {}
        for key, value in payload.items():
            dark_vars[_to_css_var(key)] = value

    return base_vars, dark_vars


def _build_theme_css() -> str:
    base_vars, dark_vars = _load_theme_variables()

    chunks: list[str] = []
    if base_vars:
        body = ";".join(f"{key}: {value}" for key, value in base_vars.items())
        chunks.append(f":root{{{body};}}")
        chunks.append(f"html[data-theme='light'], body[data-theme='light']{{{body};}}")

    if dark_vars:
        body = ";".join(f"{key}: {value}" for key, value in dark_vars.items())
        chunks.append(f"html[data-theme='dark'], body[data-theme='dark']{{{body};}}")

    return "".join(chunks)


@lru_cache(maxsize=1)
def _load_global_css() -> str:
    """Return the contents of the global CSS override file if present."""

    css_path = _STATIC_DIR / "global.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def inject_global_styles() -> None:
    """Inject the shared CSS overrides exactly once per session."""

    if st.session_state.get("_unified_global_css"):
        return

    if not st.session_state.get("_unified_bootstrap_icons"):
        st.markdown(
            "<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css\">",
            unsafe_allow_html=True,
        )
        st.session_state["_unified_bootstrap_icons"] = True

    theme_css = _build_theme_css()
    if theme_css:
        st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)

    css = _load_global_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.session_state["_unified_global_css"] = True


@lru_cache(maxsize=1)
def get_logo_data_uri() -> str:
    """Load the dashboard logo from the unified_ui assets directory."""

    search_roots = (_ASSET_ROOT, Path(__file__).resolve().parent)
    for root in search_roots:
        for name in ("logo.png", "LOGO.png"):
            logo_path = root / name
            if logo_path.exists():
                encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
                return f"data:image/png;base64,{encoded}"
    return ""


__all__ = ["inject_global_styles", "get_logo_data_uri"]
