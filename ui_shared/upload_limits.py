"""Utilities for presenting consistent upload size guidance across apps."""

from __future__ import annotations

# Streamlit's ``maxUploadSize`` configuration is set to 2 GiB (2048 MB).
# Expose both the raw byte size and a display-friendly label so help copy can be
# updated from a single location whenever the backend limit changes.
UPLOAD_LIMIT_BYTES: int = 2 * 1024 * 1024 * 1024
UPLOAD_LIMIT_LABEL: str = "2GB"


def insert_upload_limit(text: str) -> str:

    """Embed the shared upload limit label into *text* if the placeholder exists."""

    if "{limit}" not in text:
        raise ValueError("upload limit placeholder '{limit}' missing from template")


    return text.format(limit=UPLOAD_LIMIT_LABEL)


__all__ = [
    "UPLOAD_LIMIT_BYTES",
    "UPLOAD_LIMIT_LABEL",
    "insert_upload_limit",
]
