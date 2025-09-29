"""Launch the unified Streamlit dashboard with a single Python command."""
from __future__ import annotations

import sys
from pathlib import Path


def _prepare_sys_path(project_root: Path) -> None:
    """Ensure the project root is available on ``sys.path`` for imports."""
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def main() -> int:
    """Start the Streamlit UI without requiring manual CLI commands."""
    project_root = Path(__file__).resolve().parent
    app_path = project_root / "unified_ui" / "app.py"

    if not app_path.is_file():
        raise FileNotFoundError(f"Cannot locate Streamlit app at {app_path}")

    _prepare_sys_path(project_root)

    try:
        from streamlit.web import cli as stcli
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency missing
        raise ModuleNotFoundError(
            "Streamlit is required to launch the dashboard. "
            "Install it with 'pip install streamlit'."
        ) from exc

    # Mimic ``streamlit run unified_ui/app.py``
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
    ]

    try:
        return stcli.main()
    except SystemExit as exc:  # pragma: no cover - Streamlit exits via SystemExit
        return int(exc.code or 0)


if __name__ == "__main__":
    sys.exit(main())
