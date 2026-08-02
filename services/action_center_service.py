"""Action Center Service (Sprint 13.0.0 Phase 2 Governance Pipeline Integration)

Transforms RebalancePlan outputs and GovernancePipelineService actions into clean, user-facing
UI View Models for presentation in the Portfolio Action Center screen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from models.governance_action import GovernanceAction
from services.governance_pipeline_service import GovernancePipelineService
from services.rebalance_orchestrator_service import RebalancePlan


DEFAULT_SAMPLE_OBSERVATIONS: List[Dict[str, Any]] = [
    {
        "type": "sector_concentration",
        "sector": "Technology",
        "allocation_percent": 38.2,
        "exposure_pct": 38.2,
        "threshold": 30.0,
        "limit_pct": 30.0,
        "severity": "WARNING",
    }
]


@dataclass
class ReviewSummaryViewModel:
    """View model for monthly review summary metadata."""
    review_date: str
    portfolio_status: str
    approved_action_count: int
    deferred_action_count: int
    estimated_turnover: float


@dataclass
class ApprovedActionViewModel:
    """View model for an approved rebalance action."""
    action: str
    current_holding: str
    candidate_holding: str
    priority: str
    confidence: float


@dataclass
class DeferredActionViewModel:
    """View model for a deferred rebalance action."""
    action: str
    current_holding: str
    candidate_holding: str
    reason: str
    confidence: float


@dataclass
class GovernanceSnapshotViewModel:
    """View model for governance policy parameters."""
    review_frequency: str = "Monthly Review"
    rebalance_mode: str = "Conditional Rebalance"
    max_replacements: str = "Max Replacements: 3"
    turnover_budget: str = "Turnover Budget: 20%"
    emergency_override: str = "Emergency Override: Enabled"


@dataclass
class ActionCenterViewModel:
    """Complete aggregated view model for Portfolio Action Center UI."""
    summary: ReviewSummaryViewModel
    approved_actions: List[ApprovedActionViewModel]
    deferred_actions: List[DeferredActionViewModel]
    rationale: List[str]
    governance_snapshot: GovernanceSnapshotViewModel
    governance_pipeline_actions: List[GovernanceAction] = field(default_factory=list)


class ActionCenterService:
    """Service that integrates GovernancePipelineService outputs and RebalancePlan data into UI View Models."""

    def __init__(self, governance_pipeline: Optional[GovernancePipelineService] = None) -> None:
        self.governance_pipeline = governance_pipeline or GovernancePipelineService()

    def build_view_model(
        self,
        plan: Optional[RebalancePlan] = None,
        observations: Optional[List[Dict[str, Any]]] = None,
        review_date: Optional[str] = None,
    ) -> ActionCenterViewModel:
        """Build a complete ActionCenterViewModel integrating GovernancePipelineService actions and RebalancePlan.

        Args:
            plan: Optional RebalancePlan instance.
            observations: Optional list of observation dicts (defaults to internal sample observations).
            review_date: Optional formatted date string (defaults to current YYYY-MM-DD date).

        Returns:
            ActionCenterViewModel instance.
        """
        date_str = review_date or datetime.now().strftime("%Y-%m-%d")

        # 1. Process Governance Pipeline Observations
        effective_obs = observations if observations is not None else DEFAULT_SAMPLE_OBSERVATIONS

        gov_actions: List[GovernanceAction] = self.governance_pipeline.generate_actions(effective_obs)

        approved_vms: List[ApprovedActionViewModel] = []
        deferred_vms: List[DeferredActionViewModel] = []
        rationale_list: List[str] = []

        # Convert GovernanceAction items into DeferredActionViewModel and Rationale entries
        for g_act in gov_actions:
            sev_str = g_act.severity.value if hasattr(g_act.severity, "value") else str(g_act.severity)
            rationale_list.append(f"Governance Alert [{sev_str}]: {g_act.title} - {g_act.description}")

            reason_str = f"{g_act.description} Recommendation: {g_act.recommendation}"
            conf_val = 85.0 if sev_str in ("WARNING", "CRITICAL") else 70.0

            deferred_vms.append(
                DeferredActionViewModel(
                    action=sev_str,
                    current_holding=g_act.title,
                    candidate_holding="-",
                    reason=reason_str,
                    confidence=conf_val,
                )
            )

        # 2. Process RebalancePlan data if provided
        turnover = 0.0
        if plan is not None:
            turnover = float(plan.turnover_pct)

            for d in plan.approved_actions:
                curr = str(d.symbol) if d.symbol else "-"
                cand = str(d.candidate_symbol) if d.candidate_symbol else "-"
                approved_vms.append(
                    ApprovedActionViewModel(
                        action=str(d.action),
                        current_holding=curr,
                        candidate_holding=cand,
                        priority=str(d.priority),
                        confidence=float(d.confidence),
                    )
                )

            for d in plan.deferred_actions:
                curr = str(d.symbol) if d.symbol else "-"
                cand = str(d.candidate_symbol) if d.candidate_symbol else "-"
                reason_text = "; ".join(d.rationale) if d.rationale else "Deferred by orchestrator rule."
                deferred_vms.append(
                    DeferredActionViewModel(
                        action=str(d.action),
                        current_holding=curr,
                        candidate_holding=cand,
                        reason=reason_text,
                        confidence=float(d.confidence),
                    )
                )

            if plan.rationale:
                for r in plan.rationale:
                    if r not in rationale_list:
                        rationale_list.append(r)

        if not rationale_list:
            rationale_list.append("Monthly review completed. Governance policy satisfied.")

        # 3. Summary Construction
        approved_count = len(approved_vms)
        deferred_count = len(deferred_vms)
        status = "REBALANCE APPROVED" if approved_count > 0 else "NO ACTION REQUIRED"

        summary = ReviewSummaryViewModel(
            review_date=date_str,
            portfolio_status=status,
            approved_action_count=approved_count,
            deferred_action_count=deferred_count,
            estimated_turnover=turnover,
        )

        snapshot = GovernanceSnapshotViewModel()

        return ActionCenterViewModel(
            summary=summary,
            approved_actions=approved_vms,
            deferred_actions=deferred_vms,
            rationale=rationale_list,
            governance_snapshot=snapshot,
            governance_pipeline_actions=gov_actions,
        )
