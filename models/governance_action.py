"""Governance Action Model (Sprint 13.0.0 Phase 1)

Defines data model for actionable governance items generated from portfolio observations.
"""
from dataclasses import dataclass

from models.governance_severity import GovernanceSeverity


@dataclass
class GovernanceAction:
    """Dataclass representing a governance action item."""
    title: str
    description: str
    severity: GovernanceSeverity
    recommendation: str
