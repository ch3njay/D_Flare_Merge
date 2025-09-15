"""UI subpackage utilities and dependency fallbacks.

This package provides thin stub implementations for optional third-party
libraries so the UI can operate in environments where those packages are
unavailable.  When the real dependency is installed it will be imported
normally; otherwise a lightweight stub from this package is used instead.
"""
import importlib
import sys

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
]
