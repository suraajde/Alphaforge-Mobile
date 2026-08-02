"""Governance Severity Model (Sprint 13.0.0 Phase 1)

Defines severity levels for governance actions and alerts.
"""
from enum import Enum


class GovernanceSeverity(str, Enum):
    """Enum representing governance action severity levels."""
    INFO = "INFO"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
