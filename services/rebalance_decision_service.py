"""Rebalance Decision Service (Sprint 12.8.0 Rebalance Decision Engine Foundation)

Bridges Portfolio Governance evaluations and Portfolio Action Center outputs by mapping
governance results (HOLD, REVIEW, REPLACE) and target portfolio capacity into actionable
RebalanceDecision items (ADD, HOLD, REVIEW, REPLACE, NO_ACTION) with deterministic confidence scoring.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.portfolio_governance_service import (
    GovernanceDecision,
    GovernanceEvaluation,
    PortfolioGovernanceService,
)


class RebalanceAction:
    """Action categories for rebalancing decisions."""
    ADD = "ADD"
    HOLD = "HOLD"
    REVIEW = "REVIEW"
    REPLACE = "REPLACE"
    NO_ACTION = "NO_ACTION"


class RebalancePriority:
    """Priority levels for rebalance actions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RebalanceDecision:
    """Actionable rebalance decision data model."""
    action: str
    symbol: str
    candidate_symbol: Optional[str]
    priority: str
    confidence: float
    rationale: List[str] = field(default_factory=list)


class RebalanceDecisionService:
    """Engine that translates governance evaluations into structured rebalance decisions."""

    def __init__(self, governance_service: Optional[PortfolioGovernanceService] = None) -> None:
        self.governance_service = governance_service or PortfolioGovernanceService()

    def create_decision_from_governance(
        self,
        evaluation: GovernanceEvaluation,
    ) -> RebalanceDecision:
        """Convert a single GovernanceEvaluation object into a RebalanceDecision.

        Args:
            evaluation: GovernanceEvaluation output from PortfolioGovernanceService.

        Returns:
            RebalanceDecision with mapped action, priority, confidence, and rationale.
        """
        gov_decision = evaluation.decision.upper()

        if gov_decision == GovernanceDecision.REPLACE:
            action = RebalanceAction.REPLACE
            priority = RebalancePriority.HIGH
            confidence = self._compute_replace_confidence(evaluation)
            rationale = [
                "Governance approved replacement",
                f"Score advantage {evaluation.score_delta:+.1f} pts",
                f"Conviction advantage {evaluation.conviction_delta:+.1f} pts",
                "Cooling period satisfied",
            ]
            if evaluation.replacement_justification:
                rationale.append(evaluation.replacement_justification)

        elif gov_decision == GovernanceDecision.REVIEW:
            action = RebalanceAction.REVIEW
            priority = RebalancePriority.MEDIUM
            confidence = self._compute_review_confidence(evaluation)
            rationale = list(evaluation.reasons)
            if evaluation.replacement_justification:
                rationale.append(evaluation.replacement_justification)

        elif gov_decision == GovernanceDecision.HOLD:
            action = RebalanceAction.HOLD
            priority = RebalancePriority.LOW
            confidence = self._compute_hold_confidence(evaluation)
            rationale = list(evaluation.reasons)
            if evaluation.replacement_justification:
                rationale.append(evaluation.replacement_justification)

        else:
            action = RebalanceAction.NO_ACTION
            priority = RebalancePriority.LOW
            confidence = 10.0
            rationale = ["Governance evaluation complete; no action required."]

        return RebalanceDecision(
            action=action,
            symbol=evaluation.current_symbol,
            candidate_symbol=evaluation.candidate_symbol,
            priority=priority,
            confidence=round(confidence, 1),
            rationale=rationale,
        )

    def generate_rebalance_decisions(
        self,
        current_holdings: List[Dict[str, Any]],
        candidate_pool: List[Dict[str, Any]],
        target_holding_count: int = 10,
        holding_durations: Optional[Dict[str, int]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None,
    ) -> List[RebalanceDecision]:
        """Generate full suite of rebalance decisions for portfolio holdings and target capacity.

        Args:
            current_holdings: List of current position dicts.
            candidate_pool: List of candidate stock dicts.
            target_holding_count: Desired total portfolio size.
            holding_durations: Mapping of symbol -> days held.
            portfolio_context: Optional portfolio-wide metadata.

        Returns:
            List of RebalanceDecision objects.
        """
        decisions: List[RebalanceDecision] = []
        owned_symbols = {str(h.get("symbol", "")).upper() for h in current_holdings}

        # 1. Capacity Expansion Check (Portfolio Under Target Size)
        current_count = len(current_holdings)
        if current_count < target_holding_count:
            slots_to_fill = target_holding_count - current_count
            qualifying_additions = [
                cand for cand in candidate_pool
                if str(cand.get("symbol", "")).upper() not in owned_symbols
            ]

            for cand in qualifying_additions[:slots_to_fill]:
                cand_sym = str(cand.get("symbol", "UNKNOWN")).upper()
                cand_score = float(cand.get("score", cand.get("composite_score", 0.0)))
                confidence = self._compute_add_confidence(cand)

                decisions.append(
                    RebalanceDecision(
                        action=RebalanceAction.ADD,
                        symbol=cand_sym,
                        candidate_symbol=None,
                        priority=RebalancePriority.HIGH,
                        confidence=round(confidence, 1),
                        rationale=[
                            f"Portfolio below target capacity ({current_count}/{target_holding_count} positions)",
                            f"Top candidate {cand_sym} approved for allocation",
                            f"Candidate composite score: {cand_score:.1f} pts",
                        ],
                    )
                )

        # 2. Portfolio Replacements / Governance Checks
        gov_evaluations = self.governance_service.evaluate_portfolio(
            current_holdings=current_holdings,
            candidate_pool=candidate_pool,
            holding_durations=holding_durations,
            portfolio_context=portfolio_context,
        )

        for eval_res in gov_evaluations:
            decisions.append(self.create_decision_from_governance(eval_res))

        # 3. Fallback: NO_ACTION if empty or no decisions
        if not decisions:
            decisions.append(
                RebalanceDecision(
                    action=RebalanceAction.NO_ACTION,
                    symbol="PORTFOLIO",
                    candidate_symbol=None,
                    priority=RebalancePriority.LOW,
                    confidence=10.0,
                    rationale=["No rebalance action required. Portfolio is balanced and governance constraints are satisfied."],
                )
            )

        return decisions

    # ======================================================
    # DETERMINISTIC CONFIDENCE SCORING (FOUNDATION VERSION)
    # ======================================================

    def _compute_replace_confidence(self, evaluation: GovernanceEvaluation) -> float:
        """Compute REPLACE confidence in the 80-100 range."""
        base = 80.0
        min_adv = self.governance_service.config.min_score_advantage
        score_adv_bonus = max(0.0, (evaluation.score_delta - min_adv) * 0.5)
        conviction_bonus = max(0.0, evaluation.conviction_delta * 0.5)

        total = base + score_adv_bonus + conviction_bonus
        return max(80.0, min(100.0, total))

    def _compute_add_confidence(self, candidate: Dict[str, Any]) -> float:
        """Compute ADD confidence in the 80-100 range."""
        base = 85.0
        score = float(candidate.get("score", candidate.get("composite_score", 0.0)))
        score_bonus = max(0.0, (score - 70.0) * 0.5)

        total = base + score_bonus
        return max(80.0, min(100.0, total))

    def _compute_review_confidence(self, evaluation: GovernanceEvaluation) -> float:
        """Compute REVIEW confidence in the 50-79 range."""
        base = 50.0
        delta_bonus = max(0.0, evaluation.score_delta * 0.8)

        total = base + delta_bonus
        return max(50.0, min(79.0, total))

    def _compute_hold_confidence(self, evaluation: GovernanceEvaluation) -> float:
        """Compute HOLD confidence in the 20-49 range."""
        base = 20.0
        # Lower raw delta yields higher confidence in holding current position
        delta_penalty = max(0.0, evaluation.score_delta)
        stability_bonus = max(0.0, (20.0 - delta_penalty) * 1.45)

        total = base + stability_bonus
        return max(20.0, min(49.0, total))
