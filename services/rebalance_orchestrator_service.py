"""Rebalance Orchestrator Service (Sprint 12.8.2 Alpha 12 Governance Policy Alignment)

Coordinates portfolio-level rebalance constraints for monthly review cycles by ranking decisions,
enforcing replacement caps (max 3/cycle), budgeting turnover limits (max 20.0%), managing capacity additions,
handling emergency overrides, and deferring review items to generate a final executable RebalancePlan for Alpha 12.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.rebalance_decision_service import (
    RebalanceAction,
    RebalanceDecision,
    RebalancePriority,
)


@dataclass
class OrchestratorConfig:
    """Configuration for portfolio-level rebalance orchestration aligned with Alpha 12 policy."""
    max_replacements_per_cycle: int = 3
    max_turnover_pct: float = 20.0
    target_portfolio_size: int = 12
    emergency_override_enabled: bool = True


@dataclass
class RebalancePlan:
    """Final executable rebalance plan output from orchestrator."""
    approved_actions: List[RebalanceDecision] = field(default_factory=list)
    deferred_actions: List[RebalanceDecision] = field(default_factory=list)
    turnover_pct: float = 0.0
    replacement_count: int = 0
    add_count: int = 0
    rationale: List[str] = field(default_factory=list)


class RebalanceOrchestratorService:
    """Orchestrator responsible for applying monthly review cycle constraints to RebalanceDecision items."""

    def __init__(self, config: Optional[OrchestratorConfig] = None) -> None:
        self.config = config or OrchestratorConfig()

    def generate_plan(
        self,
        decisions: List[RebalanceDecision],
        current_portfolio_size: Optional[int] = None,
        position_weights: Optional[Dict[str, float]] = None,
    ) -> RebalancePlan:
        """Process decisions and apply monthly review cycle constraints to produce a final RebalancePlan.

        Args:
            decisions: List of RebalanceDecision objects from RebalanceDecisionService.
            current_portfolio_size: Optional count of current portfolio holdings.
            position_weights: Optional dict of symbol -> weight percentage.

        Returns:
            RebalancePlan object.
        """
        priority_map = {
            RebalancePriority.CRITICAL: 4,
            RebalancePriority.HIGH: 3,
            RebalancePriority.MEDIUM: 2,
            RebalancePriority.LOW: 1,
        }

        # 1. Decision Ranking: Priority (CRITICAL > HIGH > MEDIUM > LOW), then Confidence desc
        sorted_decisions = sorted(
            decisions,
            key=lambda d: (priority_map.get(str(d.priority).upper(), 0), float(d.confidence)),
            reverse=True,
        )

        approved_actions: List[RebalanceDecision] = []
        deferred_actions: List[RebalanceDecision] = []
        plan_rationale: List[str] = []

        normal_replacement_count = 0
        replacement_count = 0
        add_count = 0
        accumulated_turnover = 0.0

        # Estimate default position weight if not provided: 100.0 / target_portfolio_size
        default_weight = (
            100.0 / float(self.config.target_portfolio_size)
            if self.config.target_portfolio_size > 0
            else 8.33
        )

        # Capacity calculation
        curr_size = current_portfolio_size if current_portfolio_size is not None else 10
        capacity_available = max(0, self.config.target_portfolio_size - curr_size)

        for decision in sorted_decisions:
            act = str(decision.action).upper()
            is_emergency = str(decision.priority).upper() == RebalancePriority.CRITICAL or getattr(decision, "is_emergency", False)

            # Rule 5: REVIEW Handling -> Always Defer
            if act == RebalanceAction.REVIEW:
                deferred_actions.append(decision)
                plan_rationale.append(
                    f"Manual review required for REVIEW decision on {decision.symbol} -> {decision.candidate_symbol or 'None'}."
                )
                continue

            # Rule 6 & 7: HOLD and NO_ACTION -> Informational only, do not approve or consume turnover
            if act in (RebalanceAction.HOLD, RebalanceAction.NO_ACTION):
                deferred_actions.append(decision)
                continue

            # Rule 4: ADD Handling -> Capacity Management
            if act == RebalanceAction.ADD:
                if add_count < capacity_available:
                    approved_actions.append(decision)
                    add_count += 1
                    plan_rationale.append(
                        f"Approved ADD for {decision.symbol} (capacity slot {add_count}/{capacity_available})."
                    )
                else:
                    deferred_actions.append(decision)
                    plan_rationale.append(
                        f"Deferred ADD for {decision.symbol}: Target portfolio capacity ({self.config.target_portfolio_size}) reached."
                    )
                continue

            # Rule 2 & 3: REPLACE Handling -> Replacement Cap, Turnover Control & Emergency Override
            if act == RebalanceAction.REPLACE:
                weights = position_weights or {}
                estimated_weight = float(weights.get(decision.symbol, default_weight))

                # Check Emergency Override
                if is_emergency and self.config.emergency_override_enabled:
                    approved_actions.append(decision)
                    replacement_count += 1
                    accumulated_turnover += estimated_weight
                    plan_rationale.append(
                        f"EMERGENCY OVERRIDE APPROVED for {decision.symbol} -> {decision.candidate_symbol}: "
                        f"Investment thesis broken. Bypassed monthly replacement limit."
                    )
                    continue

                # Normal Monthly Review Replacement Cap Check
                if normal_replacement_count >= self.config.max_replacements_per_cycle:
                    deferred_actions.append(decision)
                    plan_rationale.append(
                        f"Deferred REPLACE for {decision.symbol} -> {decision.candidate_symbol}: "
                        f"Maximum replacement limit reached ({self.config.max_replacements_per_cycle}/monthly review cycle)."
                    )
                    continue

                # Normal Monthly Review Turnover Limit Check
                if accumulated_turnover + estimated_weight > self.config.max_turnover_pct + 0.001:
                    deferred_actions.append(decision)
                    plan_rationale.append(
                        f"Deferred REPLACE for {decision.symbol} -> {decision.candidate_symbol}: "
                        f"Exceeds turnover budget ({accumulated_turnover + estimated_weight:.1f}% > {self.config.max_turnover_pct:.1f}%)."
                    )
                    continue

                # Approve REPLACE
                approved_actions.append(decision)
                normal_replacement_count += 1
                replacement_count += 1
                accumulated_turnover += estimated_weight
                plan_rationale.append(
                    f"Approved REPLACE for {decision.symbol} -> {decision.candidate_symbol} "
                    f"(Turnover: {accumulated_turnover:.1f}%)."
                )

        if not approved_actions and not deferred_actions:
            plan_rationale.append("Monthly review completed. Default outcome: NO_ACTION. Portfolio is aligned.")

        return RebalancePlan(
            approved_actions=approved_actions,
            deferred_actions=deferred_actions,
            turnover_pct=round(accumulated_turnover, 2),
            replacement_count=replacement_count,
            add_count=add_count,
            rationale=plan_rationale,
        )
