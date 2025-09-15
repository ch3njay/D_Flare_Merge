"""Cisco UI 頁面模組集合。"""
from .data_cleaning import app as data_cleaning_app
from .log_monitor import app as log_monitor_app
from .model_inference import app as model_inference_app
from .notifications import app as notifications_app
from .visualization import app as visualization_app

__all__ = [
    "data_cleaning_app",
    "log_monitor_app",
    "model_inference_app",
    "notifications_app",
    "visualization_app",
]
