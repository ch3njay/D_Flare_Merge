"""Launch the unified D-Flare dashboard using the orchestrator system."""
from __future__ import annotations

import sys


def main() -> int:
    """Start the D-Flare unified dashboard using the orchestrator."""
    try:
        # Check if orchestrator and dependencies are available
        from orchestrator.cli import TYPER_AVAILABLE
        
        if not TYPER_AVAILABLE:
            print("⚠️  Typer not available, using legacy launcher...")
            return _legacy_main()
        
        # Try to use the new orchestrator CLI
        from orchestrator.cli import app
        
        # If no command line arguments provided, default to launch with lenient checks
        if len(sys.argv) == 1:
            # Allow warnings but block on errors/critical issues only
            sys.argv = ["dflare", "launch", "--lenient-checks"]
        
        app()
        return 0
        
    except ImportError:
        # Fallback to legacy launcher if orchestrator is not available
        print("⚠️  Orchestrator not available, using legacy launcher...")
        return _legacy_main()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def _legacy_main() -> int:
    """Legacy launcher for backward compatibility."""
    from pathlib import Path
    
    project_root = Path(__file__).resolve().parent
    app_path = project_root / "unified_ui" / "app.py"

    if not app_path.is_file():
        raise FileNotFoundError(f"Cannot locate Streamlit app at {app_path}")

    # Add project root to sys.path
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    try:
        from streamlit.web import cli as stcli
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Streamlit is required to launch the dashboard. "
            "Install it with 'pip install streamlit'."
        ) from exc

    # Mimic ``streamlit run unified_ui/app.py`` with browser auto-open
    original_argv = sys.argv.copy()
    try:
        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--server.port", "8501",
            # Remove headless mode to allow browser auto-open
            # "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        # Print startup message with URL
        print("🚀 Starting D-Flare Unified Dashboard...")
        print(f"📂 App path: {app_path}")
        print("🌐 Opening browser at: http://localhost:8501")
        print("   (If browser doesn't open automatically, click the URL above)")
        
        return stcli.main()
    except SystemExit as exc:
        return int(exc.code or 0)
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    sys.exit(main())
