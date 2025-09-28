"""Configuration-driven theme and design helpers for the unified UI."""
from __future__ import annotations

import base64
import codecs
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # Python < 3.11 fallback
    try:
        import tomli as tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - toml parsing unavailable
        tomllib = None  # type: ignore[assignment]

_CONFIG_PATH = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"
_DEFAULT_LOGO = "unified_ui/static/logo.png"


def _read_config() -> Dict[str, Any]:
    """Read and parse the Streamlit configuration file."""

    try:
        data = _CONFIG_PATH.read_bytes()
    except FileNotFoundError:
        return {}

    if data.startswith(codecs.BOM_UTF8):
        data = data[len(codecs.BOM_UTF8) :]

    if tomllib is None:
        return {}

    try:
        return tomllib.loads(data.decode("utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _get_app_config() -> Dict[str, Any]:
    """Return the cached configuration dictionary."""

    return _read_config()


def _get_nested(mapping: Mapping[str, Any], *keys: str, default: Any | None = None) -> Any:
    """Safely retrieve a nested configuration value."""

    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return default
        current = current[key]
    return current


def get_theme_presets() -> Dict[str, Dict[str, Any]]:
    """Return the configured light/dark palette presets."""

    presets = _get_nested(_get_app_config(), "unified_ui", "design", "theme_presets", default={})
    return {name: dict(values) for name, values in (presets or {}).items()}


def get_default_theme() -> str:
    """Return the default theme key defined in the config."""

    return _get_nested(_get_app_config(), "unified_ui", "design", "default_theme", default="dark")


def get_feature_variants() -> Dict[str, Dict[str, Any]]:
    """Return feature card styling variants from the config."""

    variants = _get_nested(
        _get_app_config(), "unified_ui", "design", "feature_variants", default={}
    )
    return {name: dict(values) for name, values in (variants or {}).items()}


def get_brand_hero(brand: str) -> Dict[str, Any]:
    """Return hero styling for a brand, inheriting from the default definition."""

    design = _get_nested(_get_app_config(), "unified_ui", "design", default={})
    hero_defaults = dict(_get_nested(design, "hero", "default", default={}) or {})
    brand_override = _get_nested(design, "hero", brand, default={}) or {}
    hero_defaults.update(brand_override)
    return hero_defaults


def get_sidebar_config() -> Dict[str, Any]:
    """Return sidebar metadata such as options and headings."""

    sidebar = _get_nested(_get_app_config(), "unified_ui", "sidebar", default={}) or {}
    return dict(sidebar)


def iter_sidebar_options() -> Iterable[tuple[str, Dict[str, Any]]]:
    """Iterate sidebar option definitions preserving the configured order."""

    sidebar = get_sidebar_config()
    options = sidebar.get("options", {}) or {}
    order = sidebar.get("order")
    if isinstance(order, list):
        for key in order:
            if key in options:
                yield key, dict(options[key])
        for key, value in options.items():
            if key not in order:
                yield key, dict(value)
    else:
        for key, value in options.items():
            yield key, dict(value)


@lru_cache(maxsize=1)
def get_logo_data_uri() -> str:
    """Return the base64 data URI for the configured logo asset."""

    assets = _get_nested(_get_app_config(), "unified_ui", "assets", default={}) or {}
    logo_path = assets.get("logo_path", _DEFAULT_LOGO)
    base_dir = Path(__file__).resolve().parent.parent
    potential_paths = []
    if isinstance(logo_path, str) and logo_path:
        potential_paths.append(base_dir / logo_path)
    potential_paths.append(base_dir / _DEFAULT_LOGO)

    for path in potential_paths:
        try:
            data = path.read_bytes()
            encoded = base64.b64encode(data).decode("ascii")
            return f"data:image/png;base64,{encoded}"
        except FileNotFoundError:
            continue
    return ""


__all__ = [
    "get_app_config",
    "get_brand_hero",
    "get_default_theme",
    "get_feature_variants",
    "get_logo_data_uri",
    "get_sidebar_config",
    "get_theme_presets",
    "iter_sidebar_options",
]


def get_app_config() -> Dict[str, Any]:
    """Expose the parsed configuration for other modules."""

    return dict(_get_app_config())
