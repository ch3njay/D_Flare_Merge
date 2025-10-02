"""Streamlit runner for D-Flare orchestrator."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import streamlit.web.cli as st_cli
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from .context import StartupContext
from .errors import StartupError


def run_streamlit(context: StartupContext, app_path: Optional[str] = None) -> None:
    """Run Streamlit with the given context configuration.
    
    Args:
        context: The startup context containing all configuration
        app_path: Optional custom app path. If None, uses unified_ui/app.py
    
    Raises:
        StartupError: If Streamlit is not available or app file not found
    """
    if not STREAMLIT_AVAILABLE:
        raise StartupError(
            code="STREAMLIT_NOT_AVAILABLE",
            severity="critical",
            message="Streamlit is not installed",
            hint="Install with: pip install streamlit",
            trace_id=context.trace_id
        )
    
    # Determine app path
    if app_path is None:
        workspace_root = Path(__file__).parent.parent
        # Always use the main unified_ui app, not the test app
        app_path = workspace_root / "unified_ui" / "app.py"
        
        # Only fallback to test app if main app doesn't exist
        if not app_path.exists():
            test_app = workspace_root / "test_launch" / "app.py"
            if test_app.exists():
                print("⚠️  Main app not found, using test app...")
                app_path = test_app
    
    app_path_obj = Path(app_path)
    if not app_path_obj.exists():
        raise StartupError.file_not_found(context.trace_id, str(app_path_obj))
    
    # Set environment variables for the Streamlit process
    env_vars = context.get_environment_variables()
    for key, value in env_vars.items():
        os.environ[key] = value
    
    # Update sys.argv for Streamlit
    original_argv = sys.argv.copy()
    try:
        sys.argv = context.get_streamlit_argv(str(app_path_obj))
        
        # Additional Streamlit configuration through environment
        os.environ["STREAMLIT_SERVER_PORT"] = str(context.port)
        # Set headless to false to allow browser auto-open
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "false"
        os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        
        # Print startup information
        print(f"🚀 D-Flare Dashboard starting on port {context.port}")
        print(f"🌐 URL: http://localhost:{context.port}")
        print("   (Browser should open automatically)")
        if context.brand != "unified":
            print(f"🏷️  Brand: {context.brand}, Mode: {context.mode}")
        
        # Disable TOML config loading to avoid parse errors
        os.environ["STREAMLIT_CONFIG_OPTION_VALIDATION_ENABLED"] = "false"
        
        # Launch Streamlit
        # This will not return unless there's an error or shutdown
        st_cli.main()
        
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


def _prepare_sys_path() -> None:
    """Prepare sys.path for module imports (legacy compatibility)."""
    workspace_root = Path(__file__).parent.parent
    
    # Add workspace root to Python path
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))
    
    # Add specific UI module directories
    ui_paths = [
        workspace_root / "Cisco_ui",
        workspace_root / "Forti_ui_app_bundle", 
        workspace_root / "unified_ui",
        workspace_root / "ui_shared"
    ]
    
    for ui_path in ui_paths:
        if ui_path.exists() and str(ui_path) not in sys.path:
            sys.path.insert(0, str(ui_path))


def validate_app_structure(app_path: Path) -> list[StartupError]:
    """Validate that the Streamlit app structure is correct.
    
    Args:
        app_path: Path to the main Streamlit app file
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check if main app file exists
    if not app_path.exists():
        errors.append(StartupError(
            code="APP_FILE_MISSING",
            severity="error",
            message=f"Main app file not found: {app_path}",
            hint="Check if the unified_ui/app.py file exists",
            trace_id="validation",
            details={"app_path": str(app_path)}
        ))
        return errors
    
    # Check if app file has basic Streamlit structure
    try:
        content = app_path.read_text(encoding='utf-8')
        if "streamlit" not in content.lower():
            errors.append(StartupError(
                code="APP_STRUCTURE_INVALID", 
                severity="warning",
                message="App file may not be a valid Streamlit app",
                hint="Ensure the app file imports and uses Streamlit",
                trace_id="validation",
                details={"app_path": str(app_path)}
            ))
    except Exception as e:
        errors.append(StartupError(
            code="APP_READ_ERROR",
            severity="error",
            message=f"Could not read app file: {e}",
            hint="Check file permissions and encoding",
            trace_id="validation",
            details={"app_path": str(app_path), "error": str(e)}
        ))
    
    return errors
