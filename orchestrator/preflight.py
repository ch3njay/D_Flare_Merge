"""Preflight checks for D-Flare orchestrator startup."""
from __future__ import annotations

import socket
from typing import List

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import streamlit
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from .context import StartupContext
from .errors import StartupError, ErrorSeverity


def preflight_check(context: StartupContext) -> List[StartupError]:
    """Perform comprehensive preflight checks before starting the dashboard.
    
    Args:
        context: The startup context containing configuration
        
    Returns:
        List of StartupError objects. Empty list means all checks passed.
    """
    errors: List[StartupError] = []
    
    # Check required dependencies
    errors.extend(_check_dependencies(context))
    
    # Check port availability
    errors.extend(_check_port_availability(context))
    
    # Check Redis connectivity (if available)
    if REDIS_AVAILABLE:
        errors.extend(_check_redis_connection(context))
    
    # Check Brand Adapter APIs (if requests available)
    if REQUESTS_AVAILABLE:
        errors.extend(_check_brand_adapters(context))
    
    return errors


def _check_dependencies(context: StartupContext) -> List[StartupError]:
    """Check if required dependencies are installed."""
    errors: List[StartupError] = []
    
    if not STREAMLIT_AVAILABLE:
        errors.append(StartupError.dependency_missing(
            trace_id=context.trace_id,
            dependency="streamlit",
            install_cmd="pip install streamlit"
        ))
    
    if not REQUESTS_AVAILABLE:
        errors.append(StartupError(
            code="DEPENDENCY_MISSING",
            severity=ErrorSeverity.WARNING,
            message="requests library not available",
            hint="Install with: pip install requests (optional for API health checks)",
            trace_id=context.trace_id,
            details={"dependency": "requests", "optional": True}
        ))
    
    if not REDIS_AVAILABLE:
        errors.append(StartupError(
            code="DEPENDENCY_MISSING", 
            severity=ErrorSeverity.WARNING,
            message="redis library not available",
            hint="Install with: pip install redis (optional for cache health checks)",
            trace_id=context.trace_id,
            details={"dependency": "redis", "optional": True}
        ))
    
    return errors


def _check_port_availability(context: StartupContext) -> List[StartupError]:
    """Check if the specified port is available."""
    errors: List[StartupError] = []
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('localhost', context.port))
    except OSError:
        errors.append(StartupError.port_occupied(context.trace_id, context.port))
    
    return errors


def _check_redis_connection(context: StartupContext) -> List[StartupError]:
    """Check Redis connectivity."""
    errors: List[StartupError] = []
    
    try:
        client = redis.Redis(host='localhost', port=6379, socket_timeout=2)
        client.ping()
    except Exception as e:
        errors.append(StartupError.connection_failed(
            trace_id=context.trace_id,
            service="Redis",
            endpoint="localhost:6379", 
            error_details=str(e)
        ))
    
    return errors


def _check_brand_adapters(context: StartupContext) -> List[StartupError]:
    """Check Brand Adapter API health."""
    errors: List[StartupError] = []
    
    # Skip brand adapter checks in standalone mode
    if context.mode == "unified" and context.config_source == "cli":
        # In standalone/development mode, brand adapters are optional
        return errors
    
    supported_brands = context.pipeline_metadata.get("supported_brands", [])
    base_url = "http://localhost:8000"
    
    for brand in supported_brands:
        try:
            response = requests.get(f"{base_url}/health/{brand}", timeout=3)
            if response.status_code != 200:
                errors.append(StartupError(
                    code="BRAND_ADAPTER_UNHEALTHY",
                    severity=ErrorSeverity.WARNING,
                    message=f"Brand adapter '{brand}' returned status {response.status_code}",
                    hint=f"Check if the {brand} adapter service is running properly",
                    trace_id=context.trace_id,
                    details={"brand": brand, "status_code": response.status_code}
                ))
        except Exception as e:
            # Downgrade connection failures to warnings in standalone mode
            errors.append(StartupError(
                code="BRAND_ADAPTER_UNAVAILABLE",
                severity=ErrorSeverity.WARNING,
                message=f"Brand adapter '{brand}' is not available",
                hint=f"This is normal in standalone mode. Brand adapter at {base_url}/health/{brand} will be used when available.",
                trace_id=context.trace_id,
                details={"brand": brand, "endpoint": f"{base_url}/health/{brand}", "error": str(e)}
            ))
    
    return errors


def _check_streamlit_version(context: StartupContext) -> List[StartupError]:
    """Check Streamlit version compatibility."""
    errors: List[StartupError] = []
    
    if not STREAMLIT_AVAILABLE:
        return errors
    
    try:
        import streamlit as st
        current_version = st.__version__
        required_version = "1.28.0"
        
        # Simple version comparison (could be enhanced with proper semver)
        if current_version < required_version:
            errors.append(StartupError.version_incompatible(
                trace_id=context.trace_id,
                component="streamlit",
                current=current_version,
                required=required_version
            ))
    except Exception as e:
        errors.append(StartupError(
            code="VERSION_CHECK_FAILED",
            severity=ErrorSeverity.WARNING,
            message=f"Could not check Streamlit version: {e}",
            hint="Version check failed, but startup may still work",
            trace_id=context.trace_id
        ))
    
    return errors
