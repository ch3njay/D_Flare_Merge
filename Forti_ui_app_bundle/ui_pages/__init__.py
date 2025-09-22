"""UI subpackage utilities and dependency fallbacks.

This package provides thin stub implementations for optional third-party
libraries so the UI can operate in environments where those packages are
unavailable.  When the real dependency is installed it will be imported
normally; otherwise a lightweight stub from this package is used instead.
"""
import importlib
import sys

import streamlit as st  # [ADDED]

_DEF_STUBS = {
    "numpy": "numpy_stub",
    "pandas": "pandas_stub",
    "psutil": "psutil_stub",
    "cupy": "cupy_stub",
}


def _ensure_module(name: str, stub: str) -> None:
    """Import *name* if possible, otherwise register *stub* as its fallback."""
    try:
        importlib.import_module(name)
    except Exception:  # pragma: no cover - best effort fallback
        module = importlib.import_module(f".{stub}", __name__)
        sys.modules[name] = module


for _pkg, _stub in _DEF_STUBS.items():
    _ensure_module(_pkg, _stub)

__all__ = [
    "_ensure_module",
    "apply_dark_theme",  # [ADDED]
]


def apply_dark_theme() -> None:  # [ADDED]
    """Inject typography colors optimized for dark surfaces."""

    if st.session_state.get("_df_dark_theme_applied"):  # [ADDED]
        return  # [ADDED]

    st.session_state["_df_dark_theme_applied"] = True  # [ADDED]
    st.markdown(  # [ADDED]
        """
        <style>
        :root {
            --df-title-color: #f9fafb;
            --df-subtitle-color: #e5e7eb;
            --df-body-color: #d1d5db;
            --df-muted-color: #9ca3af;
            --df-button-bg: #1f2937;
            --df-button-border: #4b5563;
            --df-button-hover: #374151;
            --df-warning-color: #fb923c;
            --df-error-color: #f87171;
        }
        div[data-testid="stAppViewContainer"] .main .block-container {
            color: var(--df-body-color);
        }
        div[data-testid="stAppViewContainer"] .main .block-container h1,
        div[data-testid="stAppViewContainer"] .main .block-container h2,
        div[data-testid="stAppViewContainer"] .main .block-container h3,
        div[data-testid="stAppViewContainer"] .main .block-container h4,
        div[data-testid="stAppViewContainer"] .main .block-container h5,
        div[data-testid="stAppViewContainer"] .main .block-container h6 {
            color: var(--df-title-color);
        }
        div[data-testid="stAppViewContainer"] .main .block-container p,
        div[data-testid="stAppViewContainer"] .main .block-container span,
        div[data-testid="stAppViewContainer"] .main .block-container label,
        div[data-testid="stAppViewContainer"] .main .block-container li {
            color: var(--df-body-color);
        }
        div[data-testid="stAppViewContainer"] .main .block-container small,
        div[data-testid="stAppViewContainer"] .main .block-container .stCaption,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown small {
            color: var(--df-muted-color);
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stButton > button {
            color: var(--df-title-color);
            background-color: var(--df-button-bg);
            border: 1px solid var(--df-button-border);
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stButton > button:hover {
            background-color: var(--df-button-hover);
            border-color: var(--df-title-color);
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert {
            border-radius: 12px;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="warning"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-warning-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="error"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-error-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="info"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-subtitle-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="success"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-title-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container pre,
        div[data-testid="stAppViewContainer"] .main .block-container code {
            color: var(--df-title-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
