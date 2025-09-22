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
    """Inject consistent typography and element styling for darker surfaces."""

    if st.session_state.get("_df_dark_theme_applied"):  # [ADDED]
        return  # [ADDED]

    st.session_state["_df_dark_theme_applied"] = True  # [ADDED]
    st.markdown(  # [ADDED]
        """
        <style>
        :root {
            --df-title-color: var(--text-primary, #f9fafb);
            --df-body-color: var(--text-secondary, #d1d5db);
            --df-muted-color: var(--text-secondary, #9ca3af);
            --df-button-gradient-start: var(--primary, #FF6B2C);
            --df-button-gradient-end: var(--primary-hover, #FF834D);
            --df-button-shadow: var(--hover-glow, 0 26px 48px -30px rgba(255, 107, 44, 0.4));
            --df-warning-color: var(--warning, #FFC107);
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
        div[data-testid="stAppViewContainer"] .main .block-container .stButton > button,
        div[data-testid="stAppViewContainer"] .main .block-container .stDownloadButton > button,
        div[data-testid="stAppViewContainer"] .main .block-container .stFormSubmitButton > button {
            background: linear-gradient(135deg, var(--df-button-gradient-start), var(--df-button-gradient-end));
            color: #ffffff;
            border: none;
            border-radius: 14px;
            box-shadow: var(--df-button-shadow);
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stButton > button:hover,
        div[data-testid="stAppViewContainer"] .main .block-container .stDownloadButton > button:hover,
        div[data-testid="stAppViewContainer"] .main .block-container .stFormSubmitButton > button:hover {
            transform: translateY(-1px) scale(1.02);
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert {
            border-radius: 14px;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="warning"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-warning-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="error"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-error-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container pre,
        div[data-testid="stAppViewContainer"] .main .block-container code {
            color: var(--df-title-color);
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] input,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] textarea {
            background: var(--input-background, #0f172a) !important;
            color: var(--df-title-color) !important;
            border: 1px solid var(--input-border, #334155) !important;
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
