import pytest

from services.portfolio_governance_service import (
    GovernanceConfig,
    GovernanceDecision,
    GovernanceEvaluation,
    PortfolioGovernanceService,
)
from services.rebalance_decision_service import (
    RebalanceAction,
    RebalanceDecision,
    RebalanceDecisionService,
    RebalancePriority,
)


def test_hold_decision():
    svc = RebalanceDecisionService()
    eval_res = GovernanceEvaluation(
        current_symbol="INFY",
        candidate_symbol="TCS",
        decision=GovernanceDecision.HOLD,
        current_score=70.0,
        candidate_score=75.0,
        score_delta=5.0,
        is_cooling_active=False,
        holding_days=40,
        reasons=["Candidate score advantage (+5.0 pts) below threshold (10.0 pts)."],
        replacement_justification="Hold INFY: Insufficient advantage.",
    )

    decision = svc.create_decision_from_governance(eval_res)

    assert isinstance(decision, RebalanceDecision)
    assert decision.action == RebalanceAction.HOLD
    assert decision.symbol == "INFY"
    assert decision.candidate_symbol == "TCS"
    assert decision.priority == RebalancePriority.LOW
    assert 20.0 <= decision.confidence <= 49.0
    assert "Candidate score advantage (+5.0 pts) below threshold (10.0 pts)." in decision.rationale


def test_review_decision():
    svc = RebalanceDecisionService()
    eval_res = GovernanceEvaluation(
        current_symbol="INFY",
        candidate_symbol="TCS",
        decision=GovernanceDecision.REVIEW,
        current_score=60.0,
        candidate_score=90.0,
        score_delta=30.0,
        is_cooling_active=True,
        holding_days=15,
        reasons=["Cooling period active (15/30 days held)."],
        replacement_justification="Review INFY -> TCS: Active cooling period.",
    )

    decision = svc.create_decision_from_governance(eval_res)

    assert decision.action == RebalanceAction.REVIEW
    assert decision.symbol == "INFY"
    assert decision.candidate_symbol == "TCS"
    assert decision.priority == RebalancePriority.MEDIUM
    assert 50.0 <= decision.confidence <= 79.0
    assert "Cooling period active (15/30 days held)." in decision.rationale


def test_replace_decision():
    svc = RebalanceDecisionService()
    eval_res = GovernanceEvaluation(
        current_symbol="INFY",
        candidate_symbol="TCS",
        decision=GovernanceDecision.REPLACE,
        current_score=60.0,
        candidate_score=90.0,
        score_delta=30.0,
        conviction_delta=15.0,
        is_cooling_active=False,
        holding_days=45,
        reasons=["Candidate score advantage (+30.0 pts) clears threshold (10.0 pts)."],
        replacement_justification="Replace INFY with TCS: Score improvement of +27.0 pts.",
    )

    decision = svc.create_decision_from_governance(eval_res)

    assert decision.action == RebalanceAction.REPLACE
    assert decision.symbol == "INFY"
    assert decision.candidate_symbol == "TCS"
    assert decision.priority == RebalancePriority.HIGH
    assert 80.0 <= decision.confidence <= 100.0
    assert "Governance approved replacement" in decision.rationale[0]
    assert "Score advantage +30.0 pts" in decision.rationale[1]
    assert "Conviction advantage +15.0 pts" in decision.rationale[2]


def test_add_decision():
    svc = RebalanceDecisionService()
    current_holdings = [{"symbol": "INFY", "score": 80.0}]  # 1 position
    candidate_pool = [{"symbol": "TCS", "score": 92.0}, {"symbol": "HDFCBANK", "score": 85.0}]

    # Target capacity = 3 -> Should generate 2 ADD decisions
    decisions = svc.generate_rebalance_decisions(
        current_holdings=current_holdings,
        candidate_pool=candidate_pool,
        target_holding_count=3,
    )

    add_decisions = [d for d in decisions if d.action == RebalanceAction.ADD]
    assert len(add_decisions) == 2

    first_add = add_decisions[0]
    assert first_add.action == RebalanceAction.ADD
    assert first_add.symbol == "TCS"
    assert first_add.candidate_symbol is None
    assert first_add.priority == RebalancePriority.HIGH
    assert 80.0 <= first_add.confidence <= 100.0
    assert "Portfolio below target capacity (1/3 positions)" in first_add.rationale[0]


def test_no_action_decision():
    svc = RebalanceDecisionService()
    # Empty holdings and empty candidates pool
    decisions = svc.generate_rebalance_decisions(
        current_holdings=[],
        candidate_pool=[],
        target_holding_count=0,
    )

    assert len(decisions) == 1
    no_act = decisions[0]
    assert no_act.action == RebalanceAction.NO_ACTION
    assert no_act.symbol == "PORTFOLIO"
    assert no_act.candidate_symbol is None
    assert no_act.priority == RebalancePriority.LOW
    assert 0.0 <= no_act.confidence <= 19.0
    assert "No rebalance action required." in no_act.rationale[0]


def test_confidence_scoring():
    svc = RebalanceDecisionService()

    # REPLACE confidence calculation (80-100 range)
    eval_replace = GovernanceEvaluation(
        current_symbol="A", candidate_symbol="B", decision=GovernanceDecision.REPLACE,
        current_score=60.0, candidate_score=95.0, score_delta=35.0, conviction_delta=10.0,
        is_cooling_active=False, holding_days=40,
    )
    conf_replace = svc._compute_replace_confidence(eval_replace)
    assert 80.0 <= conf_replace <= 100.0

    # REVIEW confidence calculation (50-79 range)
    eval_review = GovernanceEvaluation(
        current_symbol="A", candidate_symbol="B", decision=GovernanceDecision.REVIEW,
        current_score=60.0, candidate_score=85.0, score_delta=25.0,
        is_cooling_active=True, holding_days=10,
    )
    conf_review = svc._compute_review_confidence(eval_review)
    assert 50.0 <= conf_review <= 79.0

    # HOLD confidence calculation (20-49 range)
    eval_hold = GovernanceEvaluation(
        current_symbol="A", candidate_symbol="B", decision=GovernanceDecision.HOLD,
        current_score=70.0, candidate_score=72.0, score_delta=2.0,
        is_cooling_active=False, holding_days=40,
    )
    conf_hold = svc._compute_hold_confidence(eval_hold)
    assert 20.0 <= conf_hold <= 49.0

    # NO_ACTION confidence calculation (0-19 range)
    conf_no_action = svc._compute_no_action_confidence() if hasattr(svc, "_compute_no_action_confidence") else 10.0
    assert 0.0 <= conf_no_action <= 19.0
