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
            --df-title-color: var(--text-h1, var(--textColor));
            --df-heading2-color: var(--text-h2, var(--textColor));
            --df-heading3-color: var(--text-h3, var(--textColor));
            --df-body-color: var(--text-body, var(--textColor));
            --df-caption-color: var(--text-on-dark, var(--df-body-color));
            --df-label-color: var(--text-label, var(--textColor));
            --df-font-h1: var(--font-h1, 26px);
            --df-font-h2: var(--font-h2, 22px);
            --df-font-h3: var(--font-h3, 18px);
            --df-font-label: var(--font-label, 16px);
            --df-font-body: var(--font-body, 15.5px);
            --df-font-caption: var(--font-caption, 13.5px);
            --df-button-gradient-start: var(--primary, var(--primaryColor));
            --df-button-gradient-end: var(--primary-hover, color-mix(in srgb, var(--primaryColor) 70%, var(--textColor) 30%));
            --df-button-shadow: var(--hover-glow, 0 32px 64px -34px color-mix(in srgb, var(--primaryColor) 55%, transparent));
            --df-upload-background: var(--upload-background, color-mix(in srgb, var(--secondaryBackgroundColor) 84%, var(--backgroundColor) 16%));
            --df-upload-border: var(--upload-border, color-mix(in srgb, var(--primaryColor) 35%, transparent));
            --df-upload-text: var(--text-on-dark, var(--df-body-color));
            --df-warning-color: var(--warning, color-mix(in srgb, var(--primaryColor) 45%, var(--textColor) 55%));
            --df-error-color: color-mix(in srgb, var(--primaryColor) 30%, var(--textColor) 70%);
        }
        div[data-testid="stAppViewContainer"] .main .block-container {
            color: var(--df-body-color) !important;
            font-size: var(--df-font-body);
            line-height: 1.65;
        }
        div[data-testid="stAppViewContainer"] .main .block-container h1,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h1 {
            color: var(--df-title-color) !important;
            font-size: var(--df-font-h1);
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 0.75rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container h2,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h2 {
            color: var(--df-heading2-color) !important;
            font-size: var(--df-font-h2);
            font-weight: 600;
            margin-top: 2.1rem;
            margin-bottom: 0.7rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container h3,
        div[data-testid="stAppViewContainer"] .main .block-container h4,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h3,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h4 {
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
            color: var(--text-on-primary);
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
            color: var(--text-on-primary);
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
            background: var(--app-surface-muted, color-mix(in srgb, var(--secondaryBackgroundColor) 82%, var(--backgroundColor) 18%));
            border: 1px solid var(--muted-border, color-mix(in srgb, var(--textColor) 14%, var(--backgroundColor) 86%));
            border-radius: 12px;
            color: var(--df-body-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] .uploadedFile span,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] .uploadedFile small {
            color: var(--df-body-color) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert {
            border-radius: 16px;
            background: var(--app-surface-muted, color-mix(in srgb, var(--secondaryBackgroundColor) 82%, var(--backgroundColor) 18%));
            border: 1px solid var(--muted-border, color-mix(in srgb, var(--textColor) 14%, var(--backgroundColor) 86%));
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
            background: var(--code-background, color-mix(in srgb, var(--secondaryBackgroundColor) 78%, var(--backgroundColor) 22%));
            border-radius: 12px;
            padding: 0.25rem 0.5rem;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] input,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] textarea {
            background: var(--input-background, color-mix(in srgb, var(--secondaryBackgroundColor) 82%, var(--backgroundColor) 18%)) !important;
            color: var(--df-title-color) !important;
            border: 1px solid var(--input-border, color-mix(in srgb, var(--textColor) 16%, var(--backgroundColor) 84%)) !important;
            border-radius: 12px;
            font-size: var(--df-font-body) !important;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stTextArea"] label {
            color: var(--df-label-color) !important;
            font-size: var(--df-font-label);
            font-weight: 600;
        }
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stTextArea"] textarea {
            background: var(--code-background, color-mix(in srgb, var(--secondaryBackgroundColor) 78%, var(--backgroundColor) 22%)) !important;
            color: var(--df-body-color) !important;
            border: 1px solid var(--input-border, color-mix(in srgb, var(--textColor) 16%, var(--backgroundColor) 84%)) !important;
            border-radius: 14px !important;
            font-size: var(--df-font-body) !important;
        }
    /* [NEW] Token-based overrides to ensure gray/secondary text follows theme tokens */
    /* # [NEW] */
        /* File uploader inner texts (drag zone prompt, size limit, helper) -> secondary */
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] strong {
            color: var(--text-secondary) !important;
        }

        /* Uploader label above control -> primary (more prominent) */
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] > label {
            color: var(--text-primary) !important;
        }

        /* Input labels (text/number) -> primary */
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stTextInput"] label,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stNumberInput"] label,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] label {
            color: var(--text-primary) !important;
        }

        /* Captions / help / small helper text -> secondary */
        div[data-testid="stAppViewContainer"] .main .block-container small,
        div[data-testid="stAppViewContainer"] .main .block-container .stCaption,
        div[data-testid="stAppViewContainer"] .main .block-container .caption {
            color: var(--text-secondary) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
