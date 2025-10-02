"""Error handling for D-Flare orchestrator startup."""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorSeverity(Enum):
    """Severity levels for startup errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class StartupError:
    """Represents a startup error with structured information."""
    
    code: str
    severity: ErrorSeverity
    message: str
    hint: str
    trace_id: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "hint": self.hint,
            "trace_id": self.trace_id,
            "details": self.details or {}
        }
    
    def to_json(self) -> str:
        """Convert error to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def dependency_missing(cls, trace_id: str, dependency: str, install_cmd: str) -> StartupError:
        """Create error for missing dependency."""
        return cls(
            code="DEPENDENCY_MISSING",
            severity=ErrorSeverity.ERROR,
            message=f"Required dependency '{dependency}' is not installed",
            hint=f"Install with: {install_cmd}",
            trace_id=trace_id,
            details={"dependency": dependency, "install_command": install_cmd}
        )
    
    @classmethod
    def connection_failed(cls, trace_id: str, service: str, endpoint: str, error_details: str) -> StartupError:
        """Create error for connection failures."""
        return cls(
            code="CONNECTION_FAILED",
            severity=ErrorSeverity.ERROR,
            message=f"Failed to connect to {service}",
            hint=f"Check if {service} is running and accessible at {endpoint}",
            trace_id=trace_id,
            details={"service": service, "endpoint": endpoint, "error": error_details}
        )
    
    @classmethod
    def port_occupied(cls, trace_id: str, port: int) -> StartupError:
        """Create error for port occupation."""
        return cls(
            code="PORT_OCCUPIED",
            severity=ErrorSeverity.ERROR,
            message=f"Port {port} is already in use",
            hint=f"Use a different port with --port option or stop the process using port {port}",
            trace_id=trace_id,
            details={"port": port}
        )
    
    @classmethod
    def file_not_found(cls, trace_id: str, file_path: str) -> StartupError:
        """Create error for missing files."""
        return cls(
            code="FILE_NOT_FOUND",
            severity=ErrorSeverity.ERROR,
            message=f"Required file not found: {file_path}",
            hint="Check if the file exists and the path is correct",
            trace_id=trace_id,
            details={"file_path": file_path}
        )
    
    @classmethod
    def version_incompatible(cls, trace_id: str, component: str, current: str, required: str) -> StartupError:
        """Create error for version incompatibility."""
        return cls(
            code="VERSION_INCOMPATIBLE",
            severity=ErrorSeverity.WARNING,
            message=f"{component} version {current} may be incompatible (required: {required})",
            hint=f"Consider upgrading {component} to version {required} or newer",
            trace_id=trace_id,
            details={"component": component, "current_version": current, "required_version": required}
        )


def format_errors_json(errors: List[StartupError]) -> str:
    """Format a list of errors as JSON string."""
    if not errors:
        return json.dumps({"status": "ok", "errors": []}, indent=2)
    
    return json.dumps({
        "status": "error",
        "error_count": len(errors),
        "errors": [error.to_dict() for error in errors]
    }, indent=2, ensure_ascii=False)
