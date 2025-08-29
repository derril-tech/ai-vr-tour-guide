"""
Telemetry Worker

Collects and analyzes user behavior data including dwell time, comfort events,
quiz scores, and generates aggregate reports for tour optimization.
"""

from .main import app
from .processor import TelemetryProcessor
from .analytics_engine import AnalyticsEngine
from .report_generator import ReportGenerator
from .comfort_monitor import ComfortMonitor

__all__ = [
    "app",
    "TelemetryProcessor",
    "AnalyticsEngine",
    "ReportGenerator",
    "ComfortMonitor",
]
