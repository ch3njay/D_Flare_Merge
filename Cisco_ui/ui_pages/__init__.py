"""Cisco UI 頁面模組集合與樣式工具。"""
from __future__ import annotations

import streamlit as st

from .data_cleaning import app as data_cleaning_app
from .log_monitor import app as log_monitor_app
from .model_inference import app as model_inference_app
from .notifications import app as notifications_app
from .visualization import app as visualization_app

__all__ = [
    "apply_dark_theme",
    "data_cleaning_app",
    "log_monitor_app",
    "model_inference_app",
    "notifications_app",
    "visualization_app",
]


def apply_dark_theme() -> None:
    """Inject consistent typography and contrast-aware component styling."""

    if st.session_state.get("_cisco_dark_theme_applied"):
        return

    st.session_state["_cisco_dark_theme_applied"] = True
    st.markdown(
        """
        <style>
        :root {
            --cisco-title-color: var(--text-h1, #ffffff);
            --cisco-heading2-color: var(--text-h2, #ffffff);
            --cisco-heading3-color: var(--text-h3, #ffffff);
            --cisco-body-color: var(--text-body, #ffffff);
            --cisco-caption-color: var(--text-caption, #e2e8f0);
            --cisco-label-color: var(--text-label, #ffffff);
            --cisco-font-h1: var(--font-h1, 26px);
            --cisco-font-h2: var(--font-h2, 22px);
            --cisco-font-h3: var(--font-h3, 18px);
            --cisco-font-label: var(--font-label, 16px);
            --cisco-font-body: var(--font-body, 15.5px);
            --cisco-font-caption: var(--font-caption, 13.5px);
            --cisco-button-gradient-start: var(--primary, #2563eb);
            --cisco-button-gradient-end: var(--primary-hover, #38bdf8);
            --cisco-button-shadow: var(--hover-glow, 0 32px 64px -34px rgba(37, 99, 235, 0.55));
            --cisco-upload-background: var(--upload-background, #101a2d);
            --cisco-upload-border: var(--upload-border, rgba(37, 99, 235, 0.35));
            --cisco-upload-text: var(--upload-text, #f8fafc);
        }

        div[data-testid="stAppViewContainer"] .main .block-container {
            color: var(--cisco-body-color) !important;
            font-size: var(--cisco-font-body);
            line-height: 1.65;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h1,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h1 {
            color: var(--cisco-title-color) !important;
            font-size: var(--cisco-font-h1);
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 0.75rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h2,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h2 {
            color: var(--cisco-heading2-color) !important;
            font-size: var(--cisco-font-h2);
            font-weight: 600;
            margin-top: 2.1rem;
            margin-bottom: 0.7rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h3,
        div[data-testid="stAppViewContainer"] .main .block-container h4,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h3,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h4 {
            color: var(--cisco-heading3-color) !important;
            font-size: var(--cisco-font-h3);
            font-weight: 600;
            margin-top: 1.7rem;
            margin-bottom: 0.6rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h5,
        div[data-testid="stAppViewContainer"] .main .block-container h6,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h5,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h6 {
            color: var(--cisco-label-color) !important;
            font-size: calc(var(--cisco-font-label) - 1px);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1.5rem;
            margin-bottom: 0.45rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container p,
        div[data-testid="stAppViewContainer"] .main .block-container span,
        div[data-testid="stAppViewContainer"] .main .block-container li,
        div[data-testid="stAppViewContainer"] .main .block-container label,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown p,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown li {
            color: var(--cisco-body-color) !important;
            font-size: var(--cisco-font-body);
        }

        div[data-testid="stAppViewContainer"] ::placeholder {
            color: var(--cisco-caption-color) !important;
            opacity: 0.85;
        }

        div[data-testid="stAppViewContainer"] .main .block-container label {
            color: var(--cisco-label-color) !important;
            font-size: var(--cisco-font-label);
            font-weight: 500;
        }

        div[data-testid="stAppViewContainer"] .main .block-container small,
        div[data-testid="stAppViewContainer"] .main .block-container .stCaption,
        div[data-testid="stAppViewContainer"] .main .block-container .caption {
            color: var(--cisco-caption-color) !important;
            font-size: var(--cisco-font-caption);
            line-height: 1.55;
        }

        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] input,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-baseweb="input"] textarea,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
            background: var(--input-background, #0a121f) !important;
            color: var(--cisco-title-color) !important;
            border-color: var(--input-border, #3b4f6d) !important;
        }

        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stSelectbox"] label,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stRadio"] label,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stCheckbox"] label {
            color: var(--cisco-label-color) !important;
        }

        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] > label {
            color: var(--cisco-label-color) !important;
            font-weight: 600;
            font-size: var(--cisco-font-label);
            margin-bottom: 0.6rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
            background: var(--cisco-upload-background);
            border: 1.5px dashed var(--cisco-upload-border);
            border-radius: 18px;
            color: var(--cisco-upload-text) !important;
            padding: 1.35rem 1.1rem;
            transition: border-color 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
        }

        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small {
            color: var(--cisco-upload-text) !important;
        }

        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] button {
            background: linear-gradient(135deg, var(--cisco-button-gradient-start), var(--cisco-button-gradient-end));
            color: #ffffff;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.55rem 1.2rem;
            box-shadow: var(--cisco-button-shadow);
        }

        div[data-testid="stAppViewContainer"] .main .block-container div[data-testid="stFileUploader"] .uploadedFile,
        div[data-testid="stAppViewContainer"] .main .block-container .stAlert {
            background: var(--app-surface-muted, #101a30);
            border: 1px solid var(--muted-border, #3b4f6d);
            color: var(--cisco-body-color) !important;
        }

        div[data-testid="stAppViewContainer"] .main .block-container .stButton > button,
        div[data-testid="stAppViewContainer"] .main .block-container .stFormSubmitButton > button,
        div[data-testid="stAppViewContainer"] .main .block-container .stDownloadButton > button {
            background: linear-gradient(135deg, var(--cisco-button-gradient-start), var(--cisco-button-gradient-end));
            color: #ffffff;
            border: none;
            border-radius: 14px;
            font-size: var(--cisco-font-label);
            font-weight: 600;
            padding: 0.75rem 1.45rem;
            box-shadow: var(--cisco-button-shadow);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
