import pytest

from services.rebalance_decision_service import (
    RebalanceAction,
    RebalanceDecision,
    RebalancePriority,
)
from services.rebalance_orchestrator_service import (
    OrchestratorConfig,
    RebalanceOrchestratorService,
    RebalancePlan,
)


def test_priority_ranking():
    svc = RebalanceOrchestratorService(OrchestratorConfig(max_replacements_per_cycle=1))
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.HOLD, symbol="HOLD_LOW", candidate_symbol=None,
            priority=RebalancePriority.LOW, confidence=45.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="INFY", candidate_symbol="TCS",
            priority=RebalancePriority.HIGH, confidence=88.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="WIPRO", candidate_symbol="LTIM",
            priority=RebalancePriority.HIGH, confidence=95.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REVIEW, symbol="HDFCBANK", candidate_symbol="ICICIBANK",
            priority=RebalancePriority.MEDIUM, confidence=74.0, rationale=[]
        ),
    ]

    plan = svc.generate_plan(decisions, current_portfolio_size=12)

    assert len(plan.approved_actions) == 1
    assert plan.approved_actions[0].symbol == "WIPRO"
    assert plan.approved_actions[0].candidate_symbol == "LTIM"


def test_three_replacements_allowed():
    # Policy limit: max 3 replacements per monthly review cycle
    svc = RebalanceOrchestratorService(OrchestratorConfig(max_replacements_per_cycle=3, max_turnover_pct=30.0))
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="REP_1", candidate_symbol="CAND_1",
            priority=RebalancePriority.HIGH, confidence=95.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="REP_2", candidate_symbol="CAND_2",
            priority=RebalancePriority.HIGH, confidence=92.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="REP_3", candidate_symbol="CAND_3",
            priority=RebalancePriority.HIGH, confidence=90.0, rationale=[]
        ),
    ]
    position_weights = {"REP_1": 8.0, "REP_2": 8.0, "REP_3": 8.0}

    plan = svc.generate_plan(decisions, current_portfolio_size=12, position_weights=position_weights)

    assert plan.replacement_count == 3
    assert len(plan.approved_actions) == 3
    approved_symbols = [d.symbol for d in plan.approved_actions]
    assert approved_symbols == ["REP_1", "REP_2", "REP_3"]
    assert len(plan.deferred_actions) == 0


def test_fourth_replacement_deferred():
    # Policy limit: max 3 replacements per monthly review cycle -> 4th replacement deferred
    svc = RebalanceOrchestratorService(OrchestratorConfig(max_replacements_per_cycle=3, max_turnover_pct=40.0))
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="REP_1", candidate_symbol="CAND_1",
            priority=RebalancePriority.HIGH, confidence=95.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="REP_2", candidate_symbol="CAND_2",
            priority=RebalancePriority.HIGH, confidence=92.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="REP_3", candidate_symbol="CAND_3",
            priority=RebalancePriority.HIGH, confidence=90.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="REP_4", candidate_symbol="CAND_4",
            priority=RebalancePriority.HIGH, confidence=85.0, rationale=[]
        ),
    ]
    position_weights = {"REP_1": 5.0, "REP_2": 5.0, "REP_3": 5.0, "REP_4": 5.0}

    plan = svc.generate_plan(decisions, current_portfolio_size=12, position_weights=position_weights)

    assert plan.replacement_count == 3
    assert len(plan.approved_actions) == 3
    assert len(plan.deferred_actions) == 1
    assert plan.deferred_actions[0].symbol == "REP_4"
    assert any("Maximum replacement limit reached (3/monthly review cycle)" in r for r in plan.rationale)


def test_no_action_month():
    svc = RebalanceOrchestratorService()
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.HOLD, symbol="INFY", candidate_symbol="TCS",
            priority=RebalancePriority.LOW, confidence=35.0, rationale=["Score advantage below threshold"]
        ),
        RebalanceDecision(
            action=RebalanceAction.HOLD, symbol="RELIANCE", candidate_symbol="ONGC",
            priority=RebalancePriority.LOW, confidence=30.0, rationale=["Score advantage below threshold"]
        ),
    ]

    plan = svc.generate_plan(decisions, current_portfolio_size=12)

    assert len(plan.approved_actions) == 0
    assert len(plan.deferred_actions) == 2
    assert plan.replacement_count == 0
    assert plan.add_count == 0
    assert plan.turnover_pct == 0.0


def test_emergency_override_enabled():
    # max_replacements_per_cycle = 1, but 2nd replacement is CRITICAL (thesis broken) -> Emergency Override
    svc = RebalanceOrchestratorService(
        OrchestratorConfig(max_replacements_per_cycle=1, max_turnover_pct=30.0, emergency_override_enabled=True)
    )
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="NORMAL_REP", candidate_symbol="CAND_1",
            priority=RebalancePriority.HIGH, confidence=90.0, rationale=["Normal replacement"]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="BROKEN_THESIS", candidate_symbol="CAND_2",
            priority=RebalancePriority.CRITICAL, confidence=99.0, rationale=["Accounting irregularity detected"]
        ),
    ]

    plan = svc.generate_plan(decisions, current_portfolio_size=12)

    assert plan.replacement_count == 2
    assert len(plan.approved_actions) == 2
    # CRITICAL decision comes first due to priority ranking
    assert plan.approved_actions[0].symbol == "BROKEN_THESIS"
    assert plan.approved_actions[1].symbol == "NORMAL_REP"
    assert any("EMERGENCY OVERRIDE APPROVED" in r for r in plan.rationale)


def test_turnover_limit():
    svc = RebalanceOrchestratorService(
        OrchestratorConfig(max_replacements_per_cycle=3, max_turnover_pct=10.0)
    )
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="INFY", candidate_symbol="TCS",
            priority=RebalancePriority.HIGH, confidence=92.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE, symbol="WIPRO", candidate_symbol="LTIM",
            priority=RebalancePriority.HIGH, confidence=88.0, rationale=[]
        ),
    ]
    position_weights = {"INFY": 8.0, "WIPRO": 5.0}

    plan = svc.generate_plan(decisions, current_portfolio_size=12, position_weights=position_weights)

    assert plan.replacement_count == 1
    assert plan.turnover_pct == 8.0
    assert len(plan.approved_actions) == 1
    assert plan.approved_actions[0].symbol == "INFY"
    assert len(plan.deferred_actions) == 1
    assert plan.deferred_actions[0].symbol == "WIPRO"


def test_add_capacity_management():
    svc = RebalanceOrchestratorService(OrchestratorConfig(target_portfolio_size=12))
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.ADD, symbol="CDSL", candidate_symbol=None,
            priority=RebalancePriority.HIGH, confidence=96.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.ADD, symbol="BSE", candidate_symbol=None,
            priority=RebalancePriority.HIGH, confidence=94.0, rationale=[]
        ),
        RebalanceDecision(
            action=RebalanceAction.ADD, symbol="MCX", candidate_symbol=None,
            priority=RebalancePriority.HIGH, confidence=90.0, rationale=[]
        ),
    ]

    plan = svc.generate_plan(decisions, current_portfolio_size=10)

    assert plan.add_count == 2
    assert len(plan.approved_actions) == 2
    approved_symbols = [d.symbol for d in plan.approved_actions]
    assert approved_symbols == ["CDSL", "BSE"]


def test_review_deferred():
    svc = RebalanceOrchestratorService()
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.REVIEW, symbol="HDFCBANK", candidate_symbol="ICICIBANK",
            priority=RebalancePriority.MEDIUM, confidence=74.0, rationale=["Cooling period active"]
        ),
    ]

    plan = svc.generate_plan(decisions, current_portfolio_size=12)

    assert len(plan.approved_actions) == 0
    assert len(plan.deferred_actions) == 1
    assert plan.deferred_actions[0].symbol == "HDFCBANK"
