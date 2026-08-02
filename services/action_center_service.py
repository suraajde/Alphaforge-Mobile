"""Action Center Service (Sprint 12.9.0 Portfolio Action Center Foundation)

Transforms RebalancePlan outputs from RebalanceOrchestratorService into clean, user-facing
UI View Models for presentation in the Portfolio Action Center screen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.rebalance_orchestrator_service import RebalancePlan


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


class ActionCenterService:
    """Service that transforms raw RebalancePlan data into UI View Models."""

    def build_view_model(
        self,
        plan: Optional[RebalancePlan] = None,
        review_date: Optional[str] = None,
    ) -> ActionCenterViewModel:
        """Build a complete ActionCenterViewModel from a RebalancePlan.

        Args:
            plan: RebalancePlan instance, or None for empty state.
            review_date: Optional formatted date string (defaults to current YYYY-MM-DD date).

        Returns:
            ActionCenterViewModel instance.
        """
        date_str = review_date or datetime.now().strftime("%Y-%m-%d")

        if plan is None:
            summary = ReviewSummaryViewModel(
                review_date=date_str,
                portfolio_status="NO ACTION REQUIRED",
                approved_action_count=0,
                deferred_action_count=0,
                estimated_turnover=0.0,
            )
            return ActionCenterViewModel(
                summary=summary,
                approved_actions=[],
                deferred_actions=[],
                rationale=["Monthly review completed. No actions generated."],
                governance_snapshot=GovernanceSnapshotViewModel(),
            )

        # 1. Summary
        approved_count = len(plan.approved_actions)
        deferred_count = len(plan.deferred_actions)
        status = "REBALANCE APPROVED" if approved_count > 0 else "NO ACTION REQUIRED"

        summary = ReviewSummaryViewModel(
            review_date=date_str,
            portfolio_status=status,
            approved_action_count=approved_count,
            deferred_action_count=deferred_count,
            estimated_turnover=float(plan.turnover_pct),
        )

        # 2. Approved Actions
        approved_vms: List[ApprovedActionViewModel] = []
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

        # 3. Deferred Actions
        deferred_vms: List[DeferredActionViewModel] = []
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

        # 4. Rationale
        rationale_list = list(plan.rationale) if plan.rationale else ["Governance policy satisfied."]

        # 5. Governance Snapshot
        snapshot = GovernanceSnapshotViewModel()

        return ActionCenterViewModel(
            summary=summary,
            approved_actions=approved_vms,
            deferred_actions=deferred_vms,
            rationale=rationale_list,
            governance_snapshot=snapshot,
        )
