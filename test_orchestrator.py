"""Test script for the D-Flare orchestrator system."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from orchestrator.context import StartupContext
from orchestrator.errors import StartupError, ErrorSeverity
from orchestrator.preflight import preflight_check


def test_startup_context():
    """Test StartupContext creation and serialization."""
    print("🧪 Testing StartupContext...")
    
    # Test default creation
    context = StartupContext.create_default()
    print(f"  ✅ Default context created: {context.brand}, {context.mode}, port {context.port}")
    
    # Test custom creation
    custom_context = StartupContext.create_default(
        brand="fortinet", 
        mode="fortinet-only", 
        port=8502
    )
    print(f"  ✅ Custom context: {custom_context.brand}, {custom_context.mode}, port {custom_context.port}")
    
    # Test JSON serialization
    json_data = custom_context.to_json()
    print(f"  ✅ JSON serialization working, keys: {list(json_data.keys())}")
    
    # Test environment variables
    env_vars = custom_context.get_environment_variables()
    print(f"  ✅ Environment variables: {len(env_vars)} vars generated")
    for key, value in list(env_vars.items())[:3]:  # Show first 3
        print(f"    {key}={value}")
    
    print()


def test_error_handling():
    """Test error creation and formatting."""
    print("🧪 Testing Error Handling...")
    
    # Test different error types
    errors = [
        StartupError.dependency_missing("test-trace", "streamlit", "pip install streamlit"),
        StartupError.port_occupied("test-trace", 8501),
        StartupError.connection_failed("test-trace", "Redis", "localhost:6379", "Connection refused")
    ]
    
    for error in errors:
        print(f"  ✅ {error.code}: {error.message}")
    
    # Test JSON formatting
    json_output = json.loads(StartupError.dependency_missing("test", "typer", "pip install typer").to_json())
    print(f"  ✅ Error JSON format working, severity: {json_output['severity']}")
    
    print()


def test_preflight_checks():
    """Test preflight check system."""
    print("🧪 Testing Preflight Checks...")
    
    context = StartupContext.create_default(port=8501)
    
    try:
        errors = preflight_check(context)
        print(f"  ✅ Preflight checks completed, found {len(errors)} issues")
        
        for error in errors:
            severity_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "💥"}
            icon = severity_icon.get(error.severity.value, "❓")
            print(f"    {icon} {error.severity.value.upper()}: {error.message}")
            if error.hint:
                print(f"      Hint: {error.hint}")
        
        if not errors:
            print("  🎉 No issues found!")
            
    except Exception as e:
        print(f"  ❌ Preflight check failed: {e}")
    
    print()


def test_cli_availability():
    """Test CLI system availability."""
    print("🧪 Testing CLI System...")
    
    try:
        from orchestrator.cli import app, TYPER_AVAILABLE
        
        if TYPER_AVAILABLE:
            print("  ✅ Typer-based CLI available")
            print("  📋 Available commands: launch, check")
        else:
            print("  ⚠️ Typer not available, using fallback CLI")
        
    except ImportError as e:
        print(f"  ❌ CLI import failed: {e}")
    
    print()


def test_streamlit_runner():
    """Test Streamlit runner system."""
    print("🧪 Testing Streamlit Runner...")
    
    try:
        from orchestrator.streamlit_runner import validate_app_structure, STREAMLIT_AVAILABLE
        
        if STREAMLIT_AVAILABLE:
            print("  ✅ Streamlit is available")
        else:
            print("  ⚠️ Streamlit not available")
        
        # Test app structure validation
        app_path = project_root / "unified_ui" / "app.py"
        if app_path.exists():
            validation_errors = validate_app_structure(app_path)
            if not validation_errors:
                print(f"  ✅ App structure valid: {app_path}")
            else:
                print(f"  ⚠️ App validation issues: {len(validation_errors)}")
                for error in validation_errors:
                    print(f"    {error.message}")
        else:
            print(f"  ⚠️ App file not found: {app_path}")
        
    except ImportError as e:
        print(f"  ❌ Streamlit runner import failed: {e}")
    
    print()


def main():
    """Run all orchestrator tests."""
    print("🚀 D-Flare Orchestrator System Test")
    print("=" * 50)
    
    test_startup_context()
    test_error_handling()
    test_preflight_checks()
    test_cli_availability()
    test_streamlit_runner()
    
    print("🏁 Test completed!")
    
    # Test CLI help if available
    try:
        from orchestrator.cli import TYPER_AVAILABLE
        if TYPER_AVAILABLE:
            print("\n📚 For CLI usage, run:")
            print("  python -m orchestrator.cli --help")
            print("  python -m orchestrator.cli launch --help")
            print("  python -m orchestrator.cli check --help")
    except ImportError:
        pass


if __name__ == "__main__":
    main()