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
            --df-title-color: var(--text-h1, var(--text-primary, #ffffff));
            --df-heading2-color: var(--text-h2, var(--text-primary, #ffffff));
            --df-heading3-color: var(--text-h3, var(--text-primary, #ffffff));
            --df-body-color: var(--text-body, #ffffff);
            --df-caption-color: var(--text-on-dark, var(--df-body-color));
            --df-label-color: var(--text-label, #ffffff);
            --df-font-h1: var(--font-h1, 26px);
            --df-font-h2: var(--font-h2, 22px);
            --df-font-h3: var(--font-h3, 18px);
            --df-font-label: var(--font-label, 16px);
            --df-font-body: var(--font-body, 15.5px);
            --df-font-caption: var(--font-caption, 13.5px);
            --df-button-gradient-start: var(--primary, #1ABC9C);
            --df-button-gradient-end: var(--primary-hover, #9B59B6);
            --df-button-shadow: var(--hover-glow, 0 32px 64px -34px rgba(26, 188, 156, 0.55));
            --df-upload-background: var(--upload-background, #101a2d);
            --df-upload-border: var(--upload-border, rgba(26, 188, 156, 0.35));
            --df-upload-text: var(--text-on-dark, var(--df-body-color));
            --df-warning-color: var(--warning, #FFC107);
            --df-error-color: #f87171;
        }
        div[data-testid="stAppViewContainer"] .main .block-container {
            color: var(--df-body-color) !important;
            font-size: var(--df-font-body);
            line-height: 1.65;
        }
        div[data-testid="stAppViewContainer"] .main .block-container h1,

        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h1,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stMarkdownContainer"] h1 {

            color: var(--df-title-color) !important;
            font-size: var(--df-font-h1);
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 0.75rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container h2,

        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h2,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stMarkdownContainer"] h2 {
r
            color: var(--df-heading2-color) !important;
            font-size: var(--df-font-h2);
            font-weight: 600;
            margin-top: 2.1rem;
            margin-bottom: 0.7rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container h3,
        div[data-testid="stAppViewContainer"] .main .block-container h4,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h3,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h4,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stMarkdownContainer"] h4 {

            color: var(--df-heading3-color) !important;
            font-size: var(--df-font-h3);
            font-weight: 600;
            margin-top: 1.7rem;
            margin-bottom: 0.6rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container h5,
        div[data-testid="stAppViewContainer"] .main .block-container h6,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h5,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h6 {
            color: var(--df-label-color) !important;
            font-size: calc(var(--df-font-label) - 1px);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1.5rem;
            margin-bottom: 0.45rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container p,
        div[data-testid="stAppViewContainer"] .main .block-container span,
        div[data-testid="stAppViewContainer"] .main .block-container li {
            color: var(--df-body-color) !important;
            font-size: var(--df-font-body);
        }

        div[data-testid="stAppViewContainer"] ::placeholder {
            color: var(--df-body-color) !important;
            opacity: 1;

        }
        div[data-testid="stAppViewContainer"] .main .block-container label {
            color: var(--df-label-color) !important;
            font-size: var(--df-font-label);
            font-weight: 500;
        }
        div[data-testid="stAppViewContainer"] .main .block-container label span,
        div[data-testid="stAppViewContainer"] .main .block-container label p {
            color: var(--df-label-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stMarkdownContainer"] > * {
            color: var(--df-body-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stSelectbox"] label,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stSelectbox"] label span,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stSelectbox"] label p {
            color: var(--df-label-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stSelectbox"] div[data-baseweb="select"] *,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stSelectbox"] div[data-baseweb="select"] input {
            color: var(--df-title-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container small,
        div[data-testid="stAppViewContainer"] .main .block-container .stCaption,
        div[data-testid="stAppViewContainer"] .main .block-container .caption {
            color: var(--df-caption-color) !important;
            font-size: var(--df-font-caption);
            line-height: 1.55;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stCheckbox"] label p,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stCheckbox"] label span,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stRadio"] label p,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stRadio"] label span {
            color: var(--df-body-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stButton > button,
        div[data-testid="stAppViewContainer"] .main .block-container .stDownloadButton > button,
        div[data-testid="stAppViewContainer"] .main .block-container .stFormSubmitButton > button {
            background: linear-gradient(135deg, var(--df-button-gradient-start), var(--df-button-gradient-end));
            color: #ffffff;
            border: none;
            border-radius: 14px;
            box-shadow: var(--df-button-shadow);
            font-size: var(--df-font-label);
            font-weight: 600;
            padding: 0.75rem 1.45rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.45rem;
            letter-spacing: 0.01em;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stButton > button:hover,
        div[data-testid="stAppViewContainer"] .main .block-container .stDownloadButton > button:hover,
        div[data-testid="stAppViewContainer"] .main .block-container .stFormSubmitButton > button:hover {
            transform: translateY(-1px) scale(1.02);
            box-shadow: 0 26px 48px -24px var(--df-button-shadow);
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] > label {
            color: var(--df-label-color) !important;
            font-weight: 600;
            font-size: var(--df-font-label);
            margin-bottom: 0.6rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
            background: var(--df-upload-background);
            border: 1.5px dashed var(--df-upload-border);
            border-radius: 18px;
            color: var(--df-upload-text) !important;
            padding: 1.35rem 1.1rem;
            transition: border-color 0.25s ease, box-shadow 0.25s ease,
                background 0.25s ease;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--df-button-gradient-start);
            box-shadow: var(--df-button-shadow);
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small {
            color: var(--df-upload-text) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button {
            background: linear-gradient(135deg, var(--df-button-gradient-start), var(--df-button-gradient-end));
            color: #ffffff;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.55rem 1.2rem;
            box-shadow: var(--df-button-shadow);
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button:hover {
            filter: brightness(1.05);
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] .uploadedFile {
            background: var(--app-surface-muted, #101a30);
            border: 1px solid var(--muted-border, #3b4f6d);
            border-radius: 12px;
            color: var(--df-body-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] .uploadedFile span,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] .uploadedFile small {
            color: var(--df-body-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert {
            border-radius: 16px;
            background: var(--app-surface-muted, #101a30);
            border: 1px solid var(--muted-border, #3b4f6d);
            box-shadow: var(--df-button-shadow);
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert div[role="alert"] p {
            color: var(--df-body-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="warning"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-warning-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert[data-baseweb="alert"][kind="error"] div[data-testid="stMarkdownContainer"] p {
            color: var(--df-error-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container pre,
        div[data-testid="stAppViewContainer"] .main .block-container code {
            color: var(--df-body-color) !important;
            background: var(--code-background, #0b1220);
            border-radius: 12px;
            padding: 0.25rem 0.5rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] input,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] textarea {
            background: var(--input-background, #0a121f) !important;
            color: var(--df-title-color) !important;
            border: 1px solid var(--input-border, #3b4f6d) !important;
            border-radius: 12px;
            font-size: var(--df-font-body) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stTextArea"] label {
            color: var(--df-label-color) !important;
            font-size: var(--df-font-label);
            font-weight: 600;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stTextArea"] textarea {
            background: var(--code-background, #0b1220) !important;
            color: var(--df-body-color) !important;
            border: 1px solid var(--input-border, #3b4f6d) !important;
            border-radius: 14px !important;
            font-size: var(--df-font-body) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
