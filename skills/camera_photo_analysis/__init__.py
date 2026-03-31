"""
Camera Photo Analysis Skill
拍摄人像照片并使用 qwen3-397b 模型进行分析

技能名称：camera_photo_analysis
版本：1.0
创建时间：2024-03-27
"""

from .camera_capture import capture_photo
from .photo_analyzer import analyze_photo

__version__ = "1.0"
__all__ = ["capture_photo", "analyze_photo"]
