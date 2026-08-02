"""Portfolio Governance Service (Sprint 12.7.1 Enhancement Layer)

Strengthens Alpha 12 anti-churn portfolio governance with:
- Incumbent protection scoring (trading/friction penalty for existing positions)
- Minimum score advantage thresholds
- Conviction buffer validation
- Cooling period enforcement
- Sector diversification guardrails
- Position concentration guardrails
- Extended step-by-step audit trail
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class GovernanceDecision:
    """Governance decision outcomes."""
    HOLD = "HOLD"        # Retain existing holding; candidate fails score advantage, conviction buffer, or guardrails
    REVIEW = "REVIEW"    # Flag for manual review (active cooling period, conviction buffer marginal, or guardrail warning)
    REPLACE = "REPLACE"  # Candidate clears all churn buffers, conviction thresholds, cooling period, and guardrails


@dataclass
class GovernanceConfig:
    """Configurable governance thresholds and guardrails to control churn."""
    min_score_advantage: float = 10.0      # Candidate score must exceed effective holding score by >= 10 pts
    conviction_buffer: float = 5.0          # Minimum conviction advantage required (candidate - holding)
    cooling_period_days: int = 30           # Holding duration in days before replacement is allowed
    incumbent_bonus_score: float = 3.0      # Friction protection bonus added to incumbent holding score
    max_sector_exposure_pct: float = 30.0   # Maximum allowed sector exposure percentage
    max_position_weight_pct: float = 25.0    # Maximum allowed single position weight percentage


@dataclass
class GovernanceEvaluation:
    """Detailed evaluation result comparing a current holding against a potential candidate."""
    current_symbol: str
    candidate_symbol: str
    decision: str
    current_score: float
    candidate_score: float
    score_delta: float
    is_cooling_active: bool
    holding_days: int
    conviction_delta: float = 0.0
    incumbent_bonus_applied: float = 0.0
    sector_guardrail_breached: bool = False
    concentration_guardrail_breached: bool = False
    reasons: List[str] = field(default_factory=list)
    audit_trail: List[str] = field(default_factory=list)
    replacement_justification: str = ""


class PortfolioGovernanceService:
    """Governance engine evaluating candidate stock replacements against existing portfolio holdings."""

    def __init__(self, config: Optional[GovernanceConfig] = None) -> None:
        self.config = config or GovernanceConfig()

    def evaluate_replacement(
        self,
        current_holding: Dict[str, Any],
        candidate: Dict[str, Any],
        holding_days: int = 0,
        portfolio_context: Optional[Dict[str, Any]] = None,
    ) -> GovernanceEvaluation:
        """Evaluate whether a candidate stock should replace an existing holding.

        Args:
            current_holding: Dict containing symbol, score/composite_score, conviction, sector, weight.
            candidate: Dict containing symbol, score/composite_score, conviction, sector, weight.
            holding_days: Number of days current_holding has been held in portfolio.
            portfolio_context: Optional dict with portfolio-wide sector_weights and position_weights.

        Returns:
            GovernanceEvaluation object containing decision, metrics, audit trail, and justification.
        """
        curr_symbol = str(current_holding.get("symbol", "UNKNOWN")).upper()
        cand_symbol = str(candidate.get("symbol", "UNKNOWN")).upper()

        curr_score = float(current_holding.get("score", current_holding.get("composite_score", 0.0)))
        cand_score = float(candidate.get("score", candidate.get("composite_score", 0.0)))

        curr_conviction = float(current_holding.get("conviction_score", current_holding.get("conviction", 0.0)))
        cand_conviction = float(candidate.get("conviction_score", candidate.get("conviction", 0.0)))

        curr_sector = str(current_holding.get("sector", current_holding.get("industry", "Unassigned")))
        cand_sector = str(candidate.get("sector", candidate.get("industry", "Unassigned")))

        cand_weight = float(candidate.get("weight", candidate.get("target_weight", candidate.get("actual_weight", 0.0))))

        # 1. Incumbent Protection Bonus
        incumbent_bonus = self.config.incumbent_bonus_score
        effective_curr_score = curr_score + incumbent_bonus
        raw_score_delta = cand_score - curr_score
        effective_score_delta = cand_score - effective_curr_score

        conviction_delta = cand_conviction - curr_conviction
        is_cooling_active = holding_days < self.config.cooling_period_days

        audit_trail: List[str] = []
        reasons: List[str] = []

        audit_trail.append(
            f"Step 1 [Incumbent Protection]: Raw Scores: {curr_symbol}={curr_score:.1f}, {cand_symbol}={cand_score:.1f}. "
            f"Incumbent Bonus: +{incumbent_bonus:.1f} pts -> Effective {curr_symbol} Score: {effective_curr_score:.1f} pts. "
            f"Effective Score Delta: {effective_score_delta:+.1f} pts."
        )

        decision = GovernanceDecision.REPLACE

        # 2. Minimum Score Advantage Check
        if effective_score_delta < self.config.min_score_advantage:
            decision = GovernanceDecision.HOLD
            msg = (
                f"Candidate score advantage ({effective_score_delta:+.1f} pts vs effective holding score) "
                f"is below minimum threshold ({self.config.min_score_advantage:.1f} pts)."
            )
            reasons.append(msg)
            audit_trail.append(f"Step 2 [Score Advantage Check]: FAILED. {msg}")
        else:
            audit_trail.append(
                f"Step 2 [Score Advantage Check]: PASSED. Candidate effective advantage ({effective_score_delta:+.1f} pts) "
                f">= Threshold ({self.config.min_score_advantage:.1f} pts)."
            )

        # 3. Conviction Buffer Check
        audit_trail.append(
            f"Step 3 [Conviction Buffer]: Holding Conviction={curr_conviction:.1f}, Candidate Conviction={cand_conviction:.1f}. "
            f"Conviction Delta: {conviction_delta:+.1f} pts (Buffer required: +{self.config.conviction_buffer:.1f} pts)."
        )

        if conviction_delta < self.config.conviction_buffer:
            msg = (
                f"Candidate conviction advantage ({conviction_delta:+.1f} pts) "
                f"does not clear conviction buffer (+{self.config.conviction_buffer:.1f} pts)."
            )
            reasons.append(msg)
            audit_trail.append(f"Step 3 [Conviction Buffer]: UNMET. {msg}")

            if decision != GovernanceDecision.HOLD:
                decision = GovernanceDecision.REVIEW

        # 4. Cooling Period Check
        if is_cooling_active:
            msg = f"Cooling period active ({holding_days}/{self.config.cooling_period_days} days held)."
            reasons.append(msg)
            audit_trail.append(f"Step 4 [Cooling Period]: ACTIVE. {msg}")

            if decision != GovernanceDecision.HOLD:
                decision = GovernanceDecision.REVIEW
        else:
            audit_trail.append(
                f"Step 4 [Cooling Period]: SATISFIED. Holding duration ({holding_days} days) >= Cooling Period ({self.config.cooling_period_days} days)."
            )

        # 5. Guardrail Checks (Sector & Concentration)
        sector_breached = False
        concentration_breached = False

        # Context-based or direct candidate weight concentration check
        if cand_weight > self.config.max_position_weight_pct:
            concentration_breached = True
            msg = (
                f"Position concentration guardrail triggered: Proposed weight ({cand_weight:.1f}%) "
                f"exceeds maximum allowed limit ({self.config.max_position_weight_pct:.1f}%)."
            )
            reasons.append(msg)
            audit_trail.append(f"Step 5 [Concentration Guardrail]: BREACHED. {msg}")

            if decision != GovernanceDecision.HOLD:
                decision = GovernanceDecision.REVIEW

        if portfolio_context and isinstance(portfolio_context, dict):
            sector_weights = portfolio_context.get("sector_weights", {})
            cand_sector_exposure = float(sector_weights.get(cand_sector, 0.0))

            # Adjust for swap if current holding is in same or different sector
            if curr_sector != cand_sector:
                projected_sector_weight = cand_sector_exposure + cand_weight
            else:
                projected_sector_weight = cand_sector_exposure

            if projected_sector_weight > self.config.max_sector_exposure_pct:
                sector_breached = True
                msg = (
                    f"Sector diversification guardrail triggered: Projected sector '{cand_sector}' exposure ({projected_sector_weight:.1f}%) "
                    f"exceeds maximum sector limit ({self.config.max_sector_exposure_pct:.1f}%)."
                )
                reasons.append(msg)
                audit_trail.append(f"Step 5 [Sector Guardrail]: BREACHED. {msg}")

                if decision != GovernanceDecision.HOLD:
                    decision = GovernanceDecision.REVIEW
            else:
                audit_trail.append(
                    f"Step 5 [Sector Guardrail]: PASSED. Projected sector '{cand_sector}' exposure ({projected_sector_weight:.1f}%) "
                    f"<= Limit ({self.config.max_sector_exposure_pct:.1f}%)."
                )

        # 6. Final Justification Construction
        if decision == GovernanceDecision.HOLD:
            justification = (
                f"Hold {curr_symbol}: Candidate {cand_symbol} (raw score {cand_score:.1f}, effective score delta {effective_score_delta:+.1f} pts) "
                f"does not overcome the churn threshold and incumbent protection bonus (+{incumbent_bonus:.1f} pts)."
            )
        elif decision == GovernanceDecision.REVIEW:
            justification = (
                f"Review {curr_symbol} -> {cand_symbol}: Candidate offers score improvement ({cand_score:.1f} vs {curr_score:.1f}), "
                f"but flagged for manual review ({'; '.join(reasons)})."
            )
        else:
            justification = (
                f"Replace {curr_symbol} with {cand_symbol}: Score improvement of {effective_score_delta:+.1f} pts over effective holding score "
                f"({curr_score:.1f} + {incumbent_bonus:.1f} bonus -> {cand_score:.1f}) after {holding_days} days holding."
            )

        return GovernanceEvaluation(
            current_symbol=curr_symbol,
            candidate_symbol=cand_symbol,
            decision=decision,
            current_score=curr_score,
            candidate_score=cand_score,
            score_delta=raw_score_delta,
            is_cooling_active=is_cooling_active,
            holding_days=holding_days,
            conviction_delta=conviction_delta,
            incumbent_bonus_applied=incumbent_bonus,
            sector_guardrail_breached=sector_breached,
            concentration_guardrail_breached=concentration_breached,
            reasons=reasons,
            audit_trail=audit_trail,
            replacement_justification=justification,
        )

    def evaluate_portfolio(
        self,
        current_holdings: List[Dict[str, Any]],
        candidate_pool: List[Dict[str, Any]],
        holding_durations: Optional[Dict[str, int]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None,
    ) -> List[GovernanceEvaluation]:
        """Evaluate candidate replacements across a list of portfolio holdings.

        Args:
            current_holdings: List of current position dicts.
            candidate_pool: List of candidate stock dicts sorted by score desc.
            holding_durations: Mapping of symbol -> days held.
            portfolio_context: Optional portfolio-wide context (e.g. sector_weights).

        Returns:
            List of GovernanceEvaluation objects for each candidate/holding pair.
        """
        durations = holding_durations or {}
        evaluations: List[GovernanceEvaluation] = []

        for curr in current_holdings:
            symbol = str(curr.get("symbol", "")).upper()
            days_held = durations.get(symbol, 0)

            # Find best candidate not already in holdings
            matching_candidates = [
                cand for cand in candidate_pool
                if str(cand.get("symbol", "")).upper() != symbol
            ]

            if not matching_candidates:
                continue

            best_candidate = matching_candidates[0]
            eval_result = self.evaluate_replacement(
                current_holding=curr,
                candidate=best_candidate,
                holding_days=days_held,
                portfolio_context=portfolio_context,
            )
            evaluations.append(eval_result)

        return evaluations
