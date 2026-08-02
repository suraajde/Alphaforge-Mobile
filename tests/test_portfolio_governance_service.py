import pytest

from services.portfolio_governance_service import (
    GovernanceConfig,
    GovernanceDecision,
    GovernanceEvaluation,
    PortfolioGovernanceService,
)


def test_incumbent_protection_scoring():
    # Incumbent bonus is 3.0, min_score_advantage is 10.0
    # Candidate raw score 82.0 vs Current raw score 70.0 -> Raw delta +12.0
    # Effective current score = 70.0 + 3.0 = 73.0 -> Effective delta +9.0 < 10.0 -> HOLD
    svc = PortfolioGovernanceService()
    curr = {"symbol": "INFY", "score": 70.0, "conviction": 80.0}
    cand = {"symbol": "TCS", "score": 82.0, "conviction": 90.0}

    eval_res = svc.evaluate_replacement(curr, cand, holding_days=40)

    assert eval_res.decision == GovernanceDecision.HOLD
    assert eval_res.incumbent_bonus_applied == 3.0
    assert eval_res.score_delta == 12.0
    assert "Hold INFY" in eval_res.replacement_justification
    assert len(eval_res.audit_trail) >= 2
    assert "Incumbent Protection" in eval_res.audit_trail[0]


def test_conviction_buffer_unmet_triggers_review():
    # Raw delta +25.0 clears score advantage, but candidate conviction 82 vs holding conviction 80
    # Conviction delta = 2.0 < 5.0 conviction_buffer -> REVIEW
    svc = PortfolioGovernanceService()
    curr = {"symbol": "INFY", "score": 60.0, "conviction": 80.0}
    cand = {"symbol": "TCS", "score": 88.0, "conviction": 82.0}

    eval_res = svc.evaluate_replacement(curr, cand, holding_days=40)

    assert eval_res.decision == GovernanceDecision.REVIEW
    assert eval_res.conviction_delta == 2.0
    assert "does not clear conviction buffer" in eval_res.reasons[0]
    assert "Conviction Buffer" in eval_res.audit_trail[2]


def test_sector_diversification_guardrail_breached():
    svc = PortfolioGovernanceService(GovernanceConfig(max_sector_exposure_pct=30.0))
    curr = {"symbol": "INFY", "score": 60.0, "conviction": 70.0, "sector": "IT"}
    cand = {"symbol": "TCS", "score": 90.0, "conviction": 90.0, "sector": "IT", "weight": 10.0}

    context = {"sector_weights": {"IT": 35.0}}  # Already 35% exposure

    eval_res = svc.evaluate_replacement(curr, cand, holding_days=40, portfolio_context=context)

    assert eval_res.decision == GovernanceDecision.REVIEW
    assert eval_res.sector_guardrail_breached
    assert "Sector diversification guardrail triggered" in eval_res.reasons[0]


def test_position_concentration_guardrail_breached():
    svc = PortfolioGovernanceService(GovernanceConfig(max_position_weight_pct=25.0))
    curr = {"symbol": "INFY", "score": 60.0, "conviction": 70.0}
    cand = {"symbol": "TCS", "score": 90.0, "conviction": 90.0, "weight": 30.0}  # 30% > 25% max position weight

    eval_res = svc.evaluate_replacement(curr, cand, holding_days=40)

    assert eval_res.decision == GovernanceDecision.REVIEW
    assert eval_res.concentration_guardrail_breached
    assert "Position concentration guardrail triggered" in eval_res.reasons[0]


def test_audit_trail_and_full_replace_flow():
    svc = PortfolioGovernanceService()
    curr = {"symbol": "INFY", "score": 60.0, "conviction": 70.0, "sector": "IT"}
    cand = {"symbol": "TCS", "score": 90.0, "conviction": 85.0, "sector": "IT", "weight": 15.0}

    context = {"sector_weights": {"IT": 20.0}}

    eval_res = svc.evaluate_replacement(curr, cand, holding_days=45, portfolio_context=context)

    assert eval_res.decision == GovernanceDecision.REPLACE
    assert not eval_res.is_cooling_active
    assert not eval_res.sector_guardrail_breached
    assert not eval_res.concentration_guardrail_breached
    assert eval_res.incumbent_bonus_applied == 3.0
    assert eval_res.conviction_delta == 15.0

    # Audit trail verification
    assert len(eval_res.audit_trail) >= 5
    assert "Step 1 [Incumbent Protection]" in eval_res.audit_trail[0]
    assert "Step 2 [Score Advantage Check]: PASSED" in eval_res.audit_trail[1]
    assert "Step 3 [Conviction Buffer]" in eval_res.audit_trail[2]
    assert "Step 4 [Cooling Period]: SATISFIED" in eval_res.audit_trail[3]
    assert "Step 5 [Sector Guardrail]: PASSED" in eval_res.audit_trail[4]
    assert "Replace INFY with TCS" in eval_res.replacement_justification


def test_evaluate_portfolio_batch_with_context():
    svc = PortfolioGovernanceService()
    holdings = [
        {"symbol": "INFY", "score": 60.0, "conviction": 70.0, "sector": "IT"},
        {"symbol": "RELIANCE", "score": 75.0, "conviction": 80.0, "sector": "Energy"},
    ]
    candidates = [
        {"symbol": "TCS", "score": 90.0, "conviction": 88.0, "sector": "IT", "weight": 10.0},
        {"symbol": "ONGC", "score": 80.0, "conviction": 75.0, "sector": "Energy", "weight": 10.0},
    ]
    durations = {"INFY": 45, "RELIANCE": 10}
    context = {"sector_weights": {"IT": 15.0, "Energy": 20.0}}

    evaluations = svc.evaluate_portfolio(holdings, candidates, durations, portfolio_context=context)

    assert len(evaluations) == 2
    # INFY vs TCS: REPLACE
    assert evaluations[0].current_symbol == "INFY"
    assert evaluations[0].decision == GovernanceDecision.REPLACE

    # RELIANCE vs TCS: RELIANCE raw score 75 + bonus 3 = 78 vs TCS 90. Delta 12 >= 10, but 10 days held < 30 -> REVIEW
    assert evaluations[1].current_symbol == "RELIANCE"
    assert evaluations[1].decision == GovernanceDecision.REVIEW
