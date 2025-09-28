"""Utility helpers for global styling and branding assets."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_ASSET_ROOT = Path(__file__).resolve().parent


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

    css = _load_global_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.session_state["_unified_global_css"] = True


@lru_cache(maxsize=1)
def get_logo_data_uri() -> str:
    """Load the dashboard logo from the unified_ui assets directory."""

    for name in ("logo.png", "LOGO.png"):
        logo_path = _ASSET_ROOT / name
        if logo_path.exists():
            encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    return ""


__all__ = ["inject_global_styles", "get_logo_data_uri"]
