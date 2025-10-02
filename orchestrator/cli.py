"""Command-line interface for D-Flare orchestrator."""
from __future__ import annotations

import json
import os
import sys
from typing import Optional

try:
    import typer
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

from .context import StartupContext
from .errors import format_errors_json
from .preflight import preflight_check
from .streamlit_runner import run_streamlit

# Fallback CLI if typer is not available
if TYPER_AVAILABLE:
    app = typer.Typer(
        name="dflare",
        help="D-Flare unified dashboard orchestrator",
        add_completion=False
    )
else:
    # Minimal CLI implementation without typer
    class SimpleCLI:
        def __call__(self, *args):
            print("Error: typer not installed. Install with: pip install typer")
            return 1
    
    app = SimpleCLI()


if TYPER_AVAILABLE:
    @app.command("launch")
    def launch(
        brand: str = typer.Option("unified", "--brand", "-b", help="Brand to launch (unified/fortinet/cisco)"),
        mode: str = typer.Option("unified", "--mode", "-m", help="Launch mode (unified/fortinet-only/cisco-only)"),
        port: int = typer.Option(8501, "--port", "-p", help="Port to run Streamlit on"),
        trace_id: Optional[str] = typer.Option(None, "--trace-id", help="Custom trace ID for logging"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format"),
        skip_checks: bool = typer.Option(False, "--skip-checks", help="Skip preflight checks"),
        lenient_checks: bool = typer.Option(False, "--lenient-checks", help="Allow warnings, block only on errors/critical")
    ):
        """Launch the D-Flare unified dashboard."""
        try:
            # Create startup context
            context = StartupContext.create_default(brand=brand, mode=mode, port=port)
            if trace_id:
                context.trace_id = trace_id
            
            # Run preflight checks unless skipped
            if not skip_checks:
                errors = preflight_check(context)
                if errors:
                    if json_output:
                        typer.echo(format_errors_json(errors))
                    else:
                        typer.echo("⚠️  Preflight checks found issues:", err=True)
                        for error in errors:
                            typer.echo(f"  {error.severity.value.upper()}: {error.message}", err=True)
                            typer.echo(f"  Hint: {error.hint}", err=True)
                    
                    # Exit conditions based on check mode
                    has_critical = any(error.severity.value == "critical" for error in errors)
                    has_error = any(error.severity.value == "error" for error in errors)
                    
                    if lenient_checks:
                        # In lenient mode, only block on critical issues
                        if has_critical:
                            typer.echo("❌ Critical issues found, cannot start", err=True)
                            raise typer.Exit(1)
                        elif has_error:
                            typer.echo("⚠️  Errors found but proceeding in lenient mode...", err=True)
                    else:
                        # Default mode: block on errors and critical
                        if has_critical or has_error:
                            raise typer.Exit(1)
            
            # Launch Streamlit
            if json_output:
                typer.echo(json.dumps({
                    "status": "launching",
                    "context": context.to_json(),
                    "message": "Starting D-Flare dashboard..."
                }, indent=2))
            else:
                typer.echo(f"🚀 Starting D-Flare dashboard (brand: {brand}, mode: {mode}, port: {port})")
            
            # This will not return unless there's an error
            run_streamlit(context)
            
        except KeyboardInterrupt:
            if json_output:
                typer.echo(json.dumps({"status": "interrupted", "message": "Shutdown requested"}), err=True)
            else:
                typer.echo("\n👋 Shutdown requested", err=True)
            raise typer.Exit(0)
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2), err=True)
            else:
                typer.echo(f"❌ Error: {e}", err=True)
            raise typer.Exit(1)
    
    @app.command("check")
    def check(
        brand: str = typer.Option("unified", "--brand", "-b", help="Brand to check"),
        mode: str = typer.Option("unified", "--mode", "-m", help="Mode to check"),
        port: int = typer.Option(8501, "--port", "-p", help="Port to check"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format")
    ):
        """Run preflight checks without launching the dashboard."""
        try:
            context = StartupContext.create_default(brand=brand, mode=mode, port=port)
            errors = preflight_check(context)
            
            if json_output:
                typer.echo(format_errors_json(errors))
            else:
                if not errors:
                    typer.echo("✅ All preflight checks passed!")
                else:
                    typer.echo("⚠️  Preflight check results:")
                    for error in errors:
                        icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "💥"}
                        typer.echo(f"  {icon.get(error.severity.value, '❓')} {error.message}")
                        typer.echo(f"    Hint: {error.hint}")
            
            # Exit with error code if there are critical/error issues
            has_critical = any(error.severity.value == "critical" for error in errors)
            has_error = any(error.severity.value == "error" for error in errors)
            if has_critical or has_error:
                raise typer.Exit(1)
            
        except Exception as e:
            if json_output:
                typer.echo(json.dumps({"status": "error", "error": str(e)}, indent=2), err=True)
            else:
                typer.echo(f"❌ Error during checks: {e}", err=True)
            raise typer.Exit(1)


def main():
    """Entry point for the CLI when typer is not available."""
    if not TYPER_AVAILABLE:
        print("Error: typer not installed. Install with: pip install typer")
        sys.exit(1)
    
    app()


if __name__ == "__main__":
    main()
