"""Startup context management for D-Flare orchestrator."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StartupContext:
    """Encapsulates all startup configuration and state for the D-Flare dashboard."""
    
    brand: str
    mode: str                          # "unified" / "fortinet-only" / "cisco-only"
    port: int
    theme: Dict[str, Any]
    feature_flags: Dict[str, bool]
    pipeline_metadata: Dict[str, Any]
    trace_id: str
    config_source: str                 # "ui-config-service" / "local-yaml" / "cli"
    argv: Optional[List[str]] = field(default=None)
    extra: Optional[Dict[str, Any]] = field(default=None)
    
    @classmethod
    def create_default(cls, brand: str = "unified", mode: str = "unified", port: int = 8501) -> StartupContext:
        """Create a default startup context with sensible defaults."""
        return cls(
            brand=brand,
            mode=mode,
            port=port,
            theme={
                "primaryColor": "#FF4B4B",
                "backgroundColor": "#FFFFFF",
                "secondaryBackgroundColor": "#F0F2F6",
                "textColor": "#262730"
            },
            feature_flags={
                "enable_discord_notifications": True,
                "enable_line_notifications": True,
                "enable_gpu_processing": False,
                "enable_model_caching": True
            },
            pipeline_metadata={
                "supported_brands": ["fortinet", "cisco"],
                "model_versions": {"fortinet": "v1.2.0", "cisco": "v1.1.0"},
                "feature_count": {"fortinet": 128, "cisco": 96}
            },
            trace_id=str(uuid.uuid4()),
            config_source="cli",
            argv=None,
            extra={}
        )
    
    def to_json(self) -> Dict[str, Any]:
        """Serialize the startup context to a JSON-compatible dictionary."""
        return {
            "brand": self.brand,
            "mode": self.mode,
            "port": self.port,
            "theme": self.theme,
            "feature_flags": self.feature_flags,
            "pipeline_metadata": self.pipeline_metadata,
            "trace_id": self.trace_id,
            "config_source": self.config_source,
            "argv": self.argv,
            "extra": self.extra
        }
    
    def to_json_string(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_json(), indent=2, ensure_ascii=False)
    
    def get_streamlit_argv(self, app_path: str) -> List[str]:
        """Generate sys.argv for Streamlit execution."""
        if self.argv:
            return self.argv
        
        return [
            "streamlit",
            "run", 
            app_path,
            "--server.port", str(self.port),
            # Allow browser auto-open by removing headless mode
            # "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Generate environment variables for the Streamlit process."""
        return {
            "DFLARE_BRAND": self.brand,
            "DFLARE_MODE": self.mode,
            "DFLARE_PORT": str(self.port),
            "DFLARE_FEATURE_FLAGS": json.dumps(self.feature_flags),
            "DFLARE_TRACE_ID": self.trace_id,
            "DFLARE_CONFIG_SOURCE": self.config_source,
            "DFLARE_PIPELINE_METADATA": json.dumps(self.pipeline_metadata)
        }
