"""Cisco 介面在統一平台中的轉接層。"""
from __future__ import annotations

from cisco_ui import app as cisco_app


def render() -> None:
    cisco_app.render()
