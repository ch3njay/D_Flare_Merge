"""Cisco UI 訓練（推論）流程套件初始化。"""
from .config import PipelineConfig
from .trainer import execute_pipeline

__all__ = ["PipelineConfig", "execute_pipeline"]
