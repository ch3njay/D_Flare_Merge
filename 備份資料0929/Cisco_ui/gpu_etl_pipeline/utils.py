"""Cisco GPU ETL Pipeline 工具模組（預留擴充）。"""
from __future__ import annotations


def is_gpu_available() -> bool:
    """檢查是否有 GPU 支援。"""
    try:
        import cupy  # type: ignore  # noqa: F401

        return True
    except Exception:  # pragma: no cover - 無 GPU 環境
        return False
