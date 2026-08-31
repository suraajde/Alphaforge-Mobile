"""Tests for Let Winners Run (30% Trim Ceiling) and Emergency Eject & Reserve 8 Promotion."""
import pytest
from copy import deepcopy

from services.drift_detection_service import DriftDetectionService, DriftMetric
from services.rebalancing_candidate_service import (
    RebalancingCandidate,
    RebalancingCandidateResult,
    RebalancingCandidateService,
)
from services.rebalancing_recommendation_service import RebalancingRecommendationService
from services.rebalancing_service import (
    RebalancingPortfolio,
    RebalancingPosition,
    RebalancingState,
)
from services.portfolio_state_service import PortfolioStateService
from services.portfolio_orchestration_service import PortfolioOrchestrationService
from services.portfolio_application_service import PortfolioApplicationService
from services.alpha12_mapping_service import Alpha12MappingService


# ===========================================================================
# 1. LET WINNERS RUN (30% TRIM CEILING) TESTS
# ===========================================================================

def test_drift_detection_let_winners_run_under_30():
    """Positive drift under 30% current weight outputs HOLD action in drift detection."""
    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 2500.0, 25.0, target_weight=10.0)
    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)

    service = DriftDetectionService()
    result = service.detect_drift(state)

    assert len(result.metrics) == 1
    m = result.metrics[0]
    assert m.direction == "OVERWEIGHT"
    assert m.current_weight == 25.0
    assert m.target_weight == 10.0
    assert m.drift == 15.0
    assert m.action == "HOLD"


def test_drift_detection_trim_at_or_above_30():
    """Positive drift at or above 30.0% current weight triggers REDUCE action."""
    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 3000.0, 30.0, target_weight=10.0)
    pos2 = RebalancingPosition("NVDA", "Nvidia", "EQUITY", 4500.0, 45.0, target_weight=10.0)
    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)

    service = DriftDetectionService()
    result = service.detect_drift(state)

    assert len(result.metrics) == 2
    assert result.metrics[0].action == "REDUCE"
    assert result.metrics[1].action == "REDUCE"


def test_rebalancing_candidate_let_winners_run_under_30():
    """RebalancingCandidate under 30% weight outputs action=HOLD and impact_value=0.0."""
    pos = RebalancingPosition("TATAMOTORS", "Tata Motors", "EQUITY", 2800.0, 28.0, target_weight=8.33)
    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)

    service = RebalancingCandidateService()
    result = service.identify_candidates(state)

    assert result.total_candidates == 1
    c = result.candidates[0]
    assert c.direction == "OVERWEIGHT"
    assert c.action == "HOLD"
    assert c.impact_value == 0.0


def test_rebalancing_candidate_partial_trim_at_30_percent_ceiling():
    """RebalancingCandidate at >= 30% triggers REDUCE and calculates partial trim to baseline target weight."""
    # 35% weight on a $100,000 portfolio with target 10.0%
    # Trim amount = (35.0 - 10.0)% * 100,000 = $25,000 (NOT full liquidation of $35,000)
    pos = RebalancingPosition("TITAN", "Titan Company", "EQUITY", 35000.0, 35.0, target_weight=10.0)
    state = RebalancingState("READY", RebalancingPortfolio(100000.0, [pos]), 1, 100000.0)

    service = RebalancingCandidateService()
    result = service.identify_candidates(state)

    assert result.total_candidates == 1
    c = result.candidates[0]
    assert c.direction == "OVERWEIGHT"
    assert c.action == "REDUCE"
    assert c.impact_value == 25000.0
    assert c.target_weight == 10.0
    assert c.current_weight == 35.0


def test_rebalancing_recommendation_let_winners_run():
    """Recommendation engine suppresses DECREASE and outputs MAINTAIN for winner under 30% ceiling."""
    pos = RebalancingPosition("BEL", "Bharat Electronics", "EQUITY", 2200.0, 22.0, target_weight=8.33)
    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)

    cand_svc = RebalancingCandidateService()
    cand_res = cand_svc.identify_candidates(state)

    rec_svc = RebalancingRecommendationService()
    rec_res = rec_svc.generate_recommendations(candidates=cand_res)

    assert rec_res.total_recommendations == 1
    r = rec_res.recommendations[0]
    assert r.recommended_action == "MAINTAIN"
    assert "winner is allowed to run" in r.rationale.lower()


def test_rebalancing_recommendation_trim_above_30():
    """Recommendation engine triggers DECREASE/REDUCE for winner at or above 30% ceiling."""
    pos = RebalancingPosition("BEL", "Bharat Electronics", "EQUITY", 3200.0, 32.0, target_weight=10.0)
    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)

    cand_svc = RebalancingCandidateService()
    cand_res = cand_svc.identify_candidates(state)

    rec_svc = RebalancingRecommendationService()
    rec_res = rec_svc.generate_recommendations(candidates=cand_res)

    assert rec_res.total_recommendations == 1
    r = rec_res.recommendations[0]
    assert r.recommended_action == "DECREASE"
    assert "trim" in r.rationale.lower()


# ===========================================================================
# 2. EMERGENCY EJECT & RESERVE 8 PROMOTION TESTS
# ===========================================================================

@pytest.fixture
def sample_initial_state(tmp_path):
    """Create a sample 12-position active portfolio state."""
    mapping_svc = Alpha12MappingService()
    top20 = mapping_svc.get_top20_universe()
    alpha12 = top20[:12]

    positions = [
        {
            "symbol": p["symbol"],
            "company_name": p.get("name", p["symbol"]),
            "target_weight": 8.3333,
            "sector": p.get("sector", "UNKNOWN"),
            "category": p.get("category", "UNKNOWN"),
            "rank": idx + 1
        }
        for idx, p in enumerate(alpha12)
    ]
    state_svc = PortfolioStateService()
    state = state_svc.create_state(portfolio=positions, cash_balance=120000.0)

    # Apply mock buys: 10 shares at 1000 INR = 10,000 INR per position
    buys = [
        {"symbol": p["symbol"], "quantity": 10, "price": 1000.0}
        for p in positions
    ]
    state = state_svc.apply_confirmed_buys(state=state, buys=buys)

    state_file = str(tmp_path / "portfolio_state.json")
    state_svc.save_state(state, path=state_file)
    return state, state_file, alpha12[0]["symbol"]


def test_alpha12_mapping_service_highest_reserve():
    """Alpha12MappingService correctly finds the top unheld Reserve 8 candidate."""
    mapping_svc = Alpha12MappingService()
    top20 = mapping_svc.get_top20_universe()
    alpha12_symbols = [p["symbol"] for p in top20[:12]]
    expected_top_reserve = top20[12]["symbol"]

    reserve_cand = mapping_svc.get_highest_reserve_candidate(active_symbols=alpha12_symbols)
    assert reserve_cand is not None
    assert reserve_cand["symbol"] == expected_top_reserve


def test_emergency_replace_position_1_to_1_capital_transfer(sample_initial_state):
    """emergency_replace_position injects replacement stock with 1:1 capital transfer."""
    initial_state, state_file, symbol_to_remove = sample_initial_state

    app_svc = PortfolioApplicationService(state_path=state_file)
    res = app_svc.emergency_replace_position(symbol_to_remove)

    assert res["status"] == "OK"
    assert res["confirmed"] is True
    assert res["removed_symbol"] == symbol_to_remove
    replacement_symbol = res["replacement_symbol"]
    assert replacement_symbol != symbol_to_remove

    # Reload state from disk to confirm persistence
    state_svc = PortfolioStateService()
    loaded = state_svc.load_state(path=state_file)["state"]

    positions = loaded["positions"]
    assert symbol_to_remove not in positions
    assert replacement_symbol in positions

    injected = positions[replacement_symbol]
    # Direct 1:1 capital transfer: exited position had 10,000.0 invested/market value
    assert injected["invested_cost"] == 10000.0
    assert injected["current_value"] == 10000.0
    assert injected["target_weight"] == 8.3333
    assert loaded["cash_balance"] == 0.0

    # Check transaction audit trail
    txs = loaded["transactions"]
    eject_tx = [t for t in txs if t.get("type") == "EMERGENCY_REPLACE"]
    assert len(eject_tx) == 1
    assert eject_tx[0]["symbol_removed"] == symbol_to_remove
    assert eject_tx[0]["symbol_injected"] == replacement_symbol
    assert eject_tx[0]["capital_transferred"] == 10000.0


def test_emergency_replace_position_priced_placeholder_quantity(sample_initial_state):
    """emergency_replace_position calculates estimated placeholder quantity as round(exited_value / rep_price, 2)."""
    initial_state, state_file, symbol_to_remove = sample_initial_state

    state_svc = PortfolioStateService()
    current_state = state_svc.load_state(path=state_file)["state"]

    # Replacement stock priced at Rs. 3,000 against Rs. 10,000 exited value:
    # quantity = round(10000 / 3000, 2) = 3.33
    # invested_cost = 10000.0
    # current_value = 10000.0
    # cash_balance remains 0.0 (no routing to cash balance)
    replacement_stock = {
        "symbol": "TRENT",
        "name": "Trent Ltd",
        "company_name": "Trent Ltd",
        "sector": "CONSUMER",
        "category": "GROWTH",
        "current_price": 3000.0,
        "rank": 14,
    }

    updated = state_svc.emergency_replace_position(
        state=current_state,
        symbol_to_remove=symbol_to_remove,
        replacement_stock=replacement_stock,
    )

    positions = updated["positions"]
    assert symbol_to_remove not in positions
    assert "TRENT" in positions

    injected = positions["TRENT"]
    assert injected["quantity"] == 3.33
    assert injected["invested_cost"] == 10000.0
    assert injected["current_value"] == 10000.0
    assert injected["current_price"] == 3000.0
    assert injected["average_cost"] == 3000.0
    assert updated["cash_balance"] == 0.0

    # Total portfolio value should remain exactly balanced at Rs. 120,000.00
    total_val = sum(p["current_value"] for p in positions.values()) + updated["cash_balance"]
    assert total_val == 120000.0


def test_emergency_replace_position_nonexistent_symbol(sample_initial_state):
    """emergency_replace_position returns ERROR when target symbol is not in active portfolio."""
    _, state_file, _ = sample_initial_state
    app_svc = PortfolioApplicationService(state_path=state_file)

    res = app_svc.emergency_replace_position("NONEXISTENT_SYM")
    assert res["status"] == "ERROR"
    assert "not present" in res["error"].lower()


def test_smart_sip_with_swapped_portfolio(sample_initial_state):
    """Smart SIP operates smoothly after emergency capital transfer."""
    _, state_file, symbol_to_remove = sample_initial_state
    app_svc = PortfolioApplicationService(state_path=state_file)

    res = app_svc.emergency_replace_position(symbol_to_remove)
    rep_sym = res["replacement_symbol"]

    state = app_svc._require_state()["state"]
    price_map = {
        sym: 1000.0 for sym in state["positions"].keys()
    }
    sip_prep = app_svc.prepare_sip(sip_amount=50000.0, price_map=price_map)

    assert sip_prep["status"] == "OK"
    allocations = sip_prep.get("allocations", [])
    assert len(allocations) > 0
