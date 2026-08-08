"""Unit tests for SIP Optimization Engine Service (Sprint 13.8.2)."""
import pytest
from services.sip_optimization_service import (
    SIPOptimizationService,
    SIPOptimizationResult,
    SIPHoldingAnalysis,
    SIPDistributionMetrics,
    SIPEfficiencyMetrics,
)


def test_service_init_defaults():
    """Verify service initializes cleanly with None arguments."""
    service = SIPOptimizationService()
    assert service is not None
    assert service._portfolio_state_service is None
    assert service._rebalancing_service is None


def test_empty_state_returns_unavailable():
    """Verify empty/missing state returns UNAVAILABLE status safely."""
    class EmptyStateService:
        def load_state(self):
            return None

    service = SIPOptimizationService(portfolio_state_service=EmptyStateService())
    result = service.analyze_sip()
    assert isinstance(result, SIPOptimizationResult)
    assert result.analysis_status == "UNAVAILABLE"
    assert result.total_positions == 0
    assert result.total_sip_invested == 0.0
    assert "No valid portfolio state" in result.rationale


def test_state_with_no_positions():
    """Verify state with empty positions dict returns NO_DATA status."""
    service = SIPOptimizationService()
    state = {"positions": {}, "transactions": []}
    result = service.analyze_sip(state)
    assert result.analysis_status == "NO_DATA"
    assert result.total_positions == 0


def test_state_with_no_sip_transactions():
    """Verify state with positions but no source='SIP' transactions returns NO_DATA."""
    service = SIPOptimizationService()
    state = {
        "positions": {
            "RELIANCE": {
                "company_name": "Reliance Industries",
                "target_weight": 50.0,
                "actual_weight": 48.0,
                "drift_pct": -2.0,
                "invested_cost": 10000.0,
                "current_value": 9600.0,
            },
            "TCS": {
                "company_name": "Tata Consultancy Services",
                "target_weight": 50.0,
                "actual_weight": 52.0,
                "drift_pct": 2.0,
                "invested_cost": 10000.0,
                "current_value": 10400.0,
            },
        },
        "transactions": [
            {
                "type": "BUY",
                "symbol": "RELIANCE",
                "amount": 10000.0,
                "source": "MANUAL_CONFIRMATION",
            }
        ],
    }
    result = service.analyze_sip(state)
    assert result.analysis_status == "NO_DATA"
    assert result.total_positions == 2
    assert result.total_sip_transactions == 0
    assert result.total_sip_invested == 0.0
    assert result.distribution.positions_with_sip == 0
    assert result.distribution.sip_coverage_pct == 0.0


def test_state_with_sip_transactions():
    """Verify state with valid source='SIP' transactions returns ANALYZED metrics."""
    service = SIPOptimizationService()
    state = {
        "positions": {
            "INFY": {
                "company_name": "Infosys Ltd",
                "target_weight": 40.0,
                "actual_weight": 45.0,
                "drift_pct": 5.0,
                "invested_cost": 20000.0,
                "current_value": 22500.0,
            },
            "HDFCBANK": {
                "company_name": "HDFC Bank Ltd",
                "target_weight": 60.0,
                "actual_weight": 55.0,
                "drift_pct": -5.0,
                "invested_cost": 30000.0,
                "current_value": 27500.0,
            },
        },
        "transactions": [
            {
                "type": "BUY",
                "symbol": "INFY",
                "amount": 5000.0,
                "source": "SIP",
            },
            {
                "type": "BUY",
                "symbol": "INFY",
                "amount": 5000.0,
                "source": "SIP",
            },
            {
                "type": "BUY",
                "symbol": "HDFCBANK",
                "amount": 10000.0,
                "source": "SIP",
            },
            {
                "type": "BUY",
                "symbol": "HDFCBANK",
                "amount": 2000.0,
                "source": "MANUAL_CONFIRMATION",
            },
        ],
    }
    result = service.analyze_sip(state)
    assert result.analysis_status == "ANALYZED"
    assert result.total_positions == 2
    assert result.total_sip_transactions == 3
    assert result.total_sip_invested == 20000.0

    # Distribution checks
    assert result.distribution is not None
    assert result.distribution.positions_with_sip == 2
    assert result.distribution.sip_coverage_pct == 100.0
    assert result.distribution.sip_concentration_top_pct == 50.0  # 10k max out of 20k total SIP

    # Efficiency checks
    assert result.efficiency is not None
    assert result.efficiency.average_sip_per_transaction == round(20000.0 / 3, 2)
    assert result.efficiency.weight_misaligned_positions == 2  #Both INFY (+5%) and HDFCBANK (-5%) exceed 2% tolerance


def test_holding_analysis_unavailable_fields():
    """Verify schedule fields (amount per schedule, frequency, next date) are strictly UNAVAILABLE."""
    service = SIPOptimizationService()
    state = {
        "positions": {
            "TATAMOTORS": {
                "company_name": "Tata Motors Ltd",
                "target_weight": 100.0,
                "actual_weight": 100.0,
                "drift_pct": 0.0,
                "invested_cost": 5000.0,
                "current_value": 5000.0,
            }
        },
        "transactions": [
            {
                "type": "BUY",
                "symbol": "TATAMOTORS",
                "amount": 5000.0,
                "source": "SIP",
            }
        ],
    }
    result = service.analyze_sip(state)
    assert len(result.holdings) == 1
    holding = result.holdings[0]
    assert holding.sip_amount_per_schedule == "UNAVAILABLE"
    assert holding.sip_frequency == "UNAVAILABLE"
    assert holding.sip_next_date == "UNAVAILABLE"


def test_efficiency_observation_no_recommendations():
    """Verify observation summary contains factual counts and no recommendation words."""
    service = SIPOptimizationService()
    state = {
        "positions": {
            "SBIN": {
                "company_name": "State Bank of India",
                "target_weight": 50.0,
                "actual_weight": 50.5,
                "drift_pct": 0.5,
                "invested_cost": 10000.0,
                "current_value": 10100.0,
            },
            "ITC": {
                "company_name": "ITC Ltd",
                "target_weight": 50.0,
                "actual_weight": 40.0,
                "drift_pct": -10.0,
                "invested_cost": 10000.0,
                "current_value": 8000.0,
            },
        },
        "transactions": [
            {
                "type": "BUY",
                "symbol": "SBIN",
                "amount": 2000.0,
                "source": "SIP",
            }
        ],
    }
    result = service.analyze_sip(state)
    obs = result.efficiency.observation_summary
    assert "1 positions aligned" in obs
    assert "1 positions materially misaligned" in obs

    # Strict audit: verify no recommendation terms present in observation
    forbidden_terms = ["buy", "sell", "increase", "decrease", "recommend", "should", "action"]
    for term in forbidden_terms:
        assert term not in obs.lower(), f"Forbidden recommendation term '{term}' found in observation summary"


def test_alias_method():
    """Verify get_sip_analysis delegates to analyze_sip."""
    class EmptyStateService:
        def load_state(self):
            return None

    service = SIPOptimizationService(portfolio_state_service=EmptyStateService())
    res1 = service.analyze_sip()
    res2 = service.get_sip_analysis()
    assert res1.analysis_status == res2.analysis_status == "UNAVAILABLE"


def test_malformed_state_safe():
    """Verify malformed state structures handle safely without throwing exceptions."""
    service = SIPOptimizationService()
    malformed_states = [
        "not a dict",
        {"positions": "invalid positions type"},
        {"positions": {"XYZ": "not a dict position"}},
        {"positions": {"XYZ": None}},
    ]
    for st in malformed_states:
        result = service.analyze_sip(st)
        assert isinstance(result, SIPOptimizationResult)
        assert result.analysis_status in ("UNAVAILABLE", "NO_DATA", "ERROR")


def test_exception_resilience():
    """Verify internal exception during analysis returns safe ERROR result."""
    class BrokenStateService:
        def load_state(self):
            raise RuntimeError("Database connection failure")

    service = SIPOptimizationService(portfolio_state_service=BrokenStateService())
    result = service.analyze_sip()
    assert isinstance(result, SIPOptimizationResult)
    assert result.analysis_status in ("UNAVAILABLE", "ERROR")
