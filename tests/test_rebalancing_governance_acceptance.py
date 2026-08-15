"""Sprint 14.1.8 Acceptance Test Suite — Rebalancing Governance Engine

Tests all 11 deterministic rebalancing scenarios to establish confidence that
AlphaForge protects strong incumbents, prevents unnecessary turnover, and enforces
all governance rules prior to real investment deployment.
"""
from __future__ import annotations

import pytest
from services.portfolio_governance_service import (
    GovernanceDecision,
    PortfolioGovernanceService,
)
from services.rebalance_decision_service import (
    RebalanceAction,
    RebalanceDecision,
    RebalanceDecisionService,
    RebalancePriority,
)
from services.rebalance_orchestrator_service import (
    OrchestratorConfig,
    RebalanceOrchestratorService,
)


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Enforce data isolation via ALPHAFORGE_DATA_DIR."""
    data_dir = str(tmp_path / "alphaforge_data")
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", data_dir)
    return data_dir


def test_scenario_1_strong_incumbent_rank_drop():
    """SCENARIO 1: Incumbent falls several Alpha 12 ranks (e.g. rank #2 to #6) but fundamentals remain strong.
    Expected: HOLD. Rank movement alone is NOT a sell signal.
    """
    gov_svc = PortfolioGovernanceService()
    holding = {
        "symbol": "INFY",
        "rank": 6,
        "score": 82.0,
        "conviction": 80.0,
        "sector": "IT",
        "weight": 8.33,
    }
    challenger = {
        "symbol": "TCS",
        "rank": 2,
        "score": 86.0,
        "conviction": 82.0,
        "sector": "IT",
        "weight": 0.0,
    }
    # Effective holding score = 82 + 3 (bonus) = 85. Candidate score = 86. Effective delta = +1.0 (< +10 threshold)
    result = gov_svc.evaluate_replacement(holding, challenger, holding_days=60)
    assert result.decision == GovernanceDecision.HOLD
    assert "Candidate score advantage" in "; ".join(result.reasons) or "below minimum threshold" in "; ".join(result.reasons)


def test_scenario_2_slightly_better_challenger():
    """SCENARIO 2: Challenger is only slightly better (+4 pts raw, +1 pt effective advantage).
    Expected: NO REPLACEMENT (HOLD).
    """
    gov_svc = PortfolioGovernanceService()
    holding = {"symbol": "HDFCBANK", "score": 75.0, "conviction": 75.0, "sector": "BANK", "weight": 8.33}
    challenger = {"symbol": "ICICIBANK", "score": 79.0, "conviction": 76.0, "sector": "BANK", "weight": 0.0}

    result = gov_svc.evaluate_replacement(holding, challenger, holding_days=45)
    assert result.decision == GovernanceDecision.HOLD


def test_scenario_3_below_plus_10_advantage():
    """SCENARIO 3: Challenger raw advantage is +11, but after +3 incumbent bonus, effective advantage is +8 (< +10).
    Expected: NO REPLACEMENT (HOLD).
    """
    gov_svc = PortfolioGovernanceService()
    holding = {"symbol": "RELIANCE", "score": 70.0, "conviction": 70.0, "sector": "ENERGY", "weight": 8.33}
    challenger = {"symbol": "ONGC", "score": 81.0, "conviction": 80.0, "sector": "ENERGY", "weight": 0.0}

    # Effective delta = 81 - (70 + 3) = +8.0 < 10.0 threshold
    result = gov_svc.evaluate_replacement(holding, challenger, holding_days=40)
    assert result.decision == GovernanceDecision.HOLD


def test_scenario_4_conviction_buffer_failure():
    """SCENARIO 4: Challenger clears score advantage (+15 pts raw, +12 pts effective) but fails conviction buffer (+2 < +5).
    Expected: NO REPLACEMENT / REVIEW (DEFERRED).
    """
    gov_svc = PortfolioGovernanceService()
    holding = {"symbol": "LT", "score": 70.0, "conviction": 80.0, "sector": "INFRA", "weight": 8.33}
    challenger = {"symbol": "ABB", "score": 85.0, "conviction": 82.0, "sector": "INFRA", "weight": 0.0}

    # Conviction delta = 82 - 80 = +2.0 < +5.0 buffer required
    result = gov_svc.evaluate_replacement(holding, challenger, holding_days=60)
    assert result.decision == GovernanceDecision.REVIEW

    dec_svc = RebalanceDecisionService(gov_svc)
    decision = dec_svc.create_decision_from_governance(result)
    assert decision.action == RebalanceAction.REVIEW

    orchestrator = RebalanceOrchestratorService()
    plan = orchestrator.generate_plan([decision])
    assert decision in plan.deferred_actions
    assert decision not in plan.approved_actions


def test_scenario_5_genuinely_superior_challenger():
    """SCENARIO 5: Incumbent has deteriorated significantly (score 50, conviction 50) and challenger is materially superior (score 85, conviction 85).
    Expected: REPLACEMENT ELIGIBLE.
    """
    gov_svc = PortfolioGovernanceService()
    holding = {"symbol": "WEAK_STOCK", "score": 50.0, "conviction": 50.0, "sector": "AUTO", "weight": 8.33}
    challenger = {"symbol": "STRONG_AUTO", "score": 85.0, "conviction": 85.0, "sector": "AUTO", "weight": 0.0}

    result = gov_svc.evaluate_replacement(holding, challenger, holding_days=90)
    assert result.decision == GovernanceDecision.REPLACE

    dec_svc = RebalanceDecisionService(gov_svc)
    decision = dec_svc.create_decision_from_governance(result)
    assert decision.action == RebalanceAction.REPLACE


def test_scenario_6_cooling_period():
    """SCENARIO 6: Replacement otherwise qualifies (+20 pts score advantage, +10 conviction), but holding duration is 15 days (< 30-day cooling period).
    Expected: REVIEW / DEFERRED (NO replacement execution).
    """
    gov_svc = PortfolioGovernanceService()
    holding = {"symbol": "NEW_HOLDING", "score": 60.0, "conviction": 65.0, "sector": "TECH", "weight": 8.33}
    challenger = {"symbol": "SUPERIOR_TECH", "score": 85.0, "conviction": 80.0, "sector": "TECH", "weight": 0.0}

    result = gov_svc.evaluate_replacement(holding, challenger, holding_days=15)
    assert result.decision == GovernanceDecision.REVIEW
    assert result.is_cooling_active is True

    dec_svc = RebalanceDecisionService(gov_svc)
    decision = dec_svc.create_decision_from_governance(result)
    assert decision.action == RebalanceAction.REVIEW

    orchestrator = RebalanceOrchestratorService()
    plan = orchestrator.generate_plan([decision])
    assert decision in plan.deferred_actions
    assert len(plan.approved_actions) == 0


def test_scenario_7_more_than_three_replacements():
    """SCENARIO 7: Five valid replacement decisions exist in a single review cycle.
    Expected: Maximum 3 replacements approved, remaining deferred.
    """
    decisions = []
    for i in range(1, 6):
        decisions.append(
            RebalanceDecision(
                action=RebalanceAction.REPLACE,
                symbol=f"WEAK_{i}",
                candidate_symbol=f"STRONG_{i}",
                priority=RebalancePriority.HIGH,
                confidence=85.0 + i,
                rationale=[f"Replacement candidate {i}"],
            )
        )

    orchestrator = RebalanceOrchestratorService(config=OrchestratorConfig(max_replacements_per_cycle=3, max_turnover_pct=50.0))
    plan = orchestrator.generate_plan(decisions, current_portfolio_size=12)

    assert len(plan.approved_actions) == 3
    assert len(plan.deferred_actions) == 2
    assert plan.replacement_count == 3


def test_scenario_8_turnover_budget_exceeded():
    """SCENARIO 8: Proposed replacements exceed the 20% projected turnover budget (e.g., 3 replacements at 8.33% weight = 24.99% turnover).
    Expected: Governance turnover protection defers excessive replacements to keep turnover <= 20%.
    """
    decisions = [
        RebalanceDecision(
            action=RebalanceAction.REPLACE,
            symbol="STOCK_A",
            candidate_symbol="CAND_A",
            priority=RebalancePriority.HIGH,
            confidence=90.0,
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE,
            symbol="STOCK_B",
            candidate_symbol="CAND_B",
            priority=RebalancePriority.HIGH,
            confidence=85.0,
        ),
        RebalanceDecision(
            action=RebalanceAction.REPLACE,
            symbol="STOCK_C",
            candidate_symbol="CAND_C",
            priority=RebalancePriority.HIGH,
            confidence=80.0,
        ),
    ]

    orchestrator = RebalanceOrchestratorService(config=OrchestratorConfig(max_turnover_pct=20.0, emergency_override_enabled=False))
    weights = {"STOCK_A": 8.33, "STOCK_B": 8.33, "STOCK_C": 8.33}
    plan = orchestrator.generate_plan(decisions, current_portfolio_size=12, position_weights=weights)

    assert len(plan.approved_actions) == 2
    assert len(plan.deferred_actions) == 1
    assert plan.turnover_pct <= 20.0


def test_scenario_9_winner_overweight():
    """SCENARIO 9: Strong incumbent winner has portfolio weight of 18.0% (above nominal 8.33% target), but score and conviction remain strong.
    Expected: HOLD. Do not sell solely to normalize target weight.
    """
    gov_svc = PortfolioGovernanceService()
    winner_holding = {
        "symbol": "WINNER_STOCK",
        "score": 92.0,
        "conviction": 90.0,
        "sector": "TECH",
        "weight": 18.0,
    }
    challenger = {
        "symbol": "ALT_STOCK",
        "score": 85.0,
        "conviction": 80.0,
        "sector": "TECH",
        "weight": 0.0,
    }

    result = gov_svc.evaluate_replacement(winner_holding, challenger, holding_days=180)
    assert result.decision == GovernanceDecision.HOLD
    assert "Hold WINNER_STOCK" in result.replacement_justification


def test_scenario_10_no_qualifying_challenger():
    """SCENARIO 10: 12 portfolio holdings exist. Candidate pool contains candidates that fail score/conviction thresholds.
    Expected: HOLD ALL. Zero unnecessary turnover.
    """
    holdings = [
        {"symbol": f"HOLD_{i}", "score": 75.0, "conviction": 80.0, "sector": "MISC", "weight": 8.33}
        for i in range(1, 13)
    ]
    candidate_pool = [
        {"symbol": f"CAND_{i}", "score": 78.0, "conviction": 75.0, "sector": "MISC", "weight": 0.0}
        for i in range(1, 5)
    ]

    gov_svc = PortfolioGovernanceService()
    evaluations = gov_svc.evaluate_portfolio(holdings, candidate_pool)

    dec_svc = RebalanceDecisionService(gov_svc)
    decisions = [dec_svc.create_decision_from_governance(ev) for ev in evaluations]

    orchestrator = RebalanceOrchestratorService()
    plan = orchestrator.generate_plan(decisions, current_portfolio_size=12)

    assert len(plan.approved_actions) == 0
    assert plan.turnover_pct == 0.0
    assert plan.replacement_count == 0


def test_scenario_11_all_12_incumbents_healthy():
    """SCENARIO 11 (MANDATORY): All 12 current Alpha 12 holdings are healthy and in candidate pool.
    Expected: ZERO REPLACEMENTS. Monthly review completes cleanly with outcome 'HOLD ALL'.
    """
    holdings = [
        {"symbol": f"ALPHA_{i}", "score": 85.0 - i, "conviction": 85.0, "sector": "CORE", "weight": 8.33}
        for i in range(1, 13)
    ]
    candidate_pool = list(holdings)

    gov_svc = PortfolioGovernanceService()
    evaluations = gov_svc.evaluate_portfolio(holdings, candidate_pool)

    dec_svc = RebalanceDecisionService(gov_svc)
    decisions = [dec_svc.create_decision_from_governance(ev) for ev in evaluations]

    orchestrator = RebalanceOrchestratorService()
    plan = orchestrator.generate_plan(decisions, current_portfolio_size=12)

    assert len(plan.approved_actions) == 0
    assert plan.replacement_count == 0
    assert plan.turnover_pct == 0.0
    assert all(d.action == RebalanceAction.HOLD for d in decisions)
