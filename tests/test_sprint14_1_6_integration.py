"""Integration tests for Sprint 14.1.6/14.1.7 Portfolio Intelligence & Allocation Reconciliation."""
import math
import pytest
from services.investment_allocation_service import InvestmentAllocationService
from services.holding_quality_service import HoldingQualityService, HoldingQuality
from services.alpha12_mapping_service import Alpha12MappingService
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService


def test_investment_allocation_whole_share_reconciliation():
    """Verify whole-share reconciliation in monthly and lump-sum investment allocation."""
    mock_price_provider = lambda sym: {"price": 450.0}
    svc = InvestmentAllocationService(price_provider=mock_price_provider)

    # Monthly allocation test
    user_input_monthly = 6000.0
    res_monthly = svc.allocate_monthly_investment(user_input_monthly)

    assert res_monthly.total_input_amount == user_input_monthly
    assert res_monthly.total_allocated_amount <= user_input_monthly
    assert res_monthly.total_allocated_amount > 0.0

    for item in res_monthly.allocations:
        assert isinstance(item.quantity, int)
        assert item.quantity >= 0
        expected_amt = round(item.quantity * item.reference_price, 2)
        assert item.executable_amount == expected_amt

    residual_cash_monthly = round(user_input_monthly - res_monthly.total_allocated_amount, 2)
    assert residual_cash_monthly >= 0.0

    # Lump-sum allocation test
    user_input_lump = 50000.0
    res_lump = svc.allocate_lump_sum_investment(user_input_lump)

    assert res_lump.total_input_amount == user_input_lump
    assert res_lump.total_allocated_amount <= user_input_lump
    assert res_lump.total_allocated_amount > 0.0

    for item in res_lump.allocations:
        assert isinstance(item.quantity, int)
        assert item.quantity >= 0
        expected_amt = round(item.quantity * item.reference_price, 2)
        assert item.executable_amount == expected_amt

    residual_cash_lump = round(user_input_lump - res_lump.total_allocated_amount, 2)
    assert residual_cash_lump >= 0.0


def test_holding_quality_service_equity_recognition():
    """Verify equity holdings are assessed using equity path and never marked UNSUPPORTED."""
    svc = HoldingQualityService()

    # Equity holding with fundamental score
    eq_with_score = {
        "symbol": "TRAVELFOOD",
        "company_name": "Travel Food Services",
        "asset_type": "EQUITY",
        "score": 88.5,
    }
    res_scored = svc.assess_single_holding(eq_with_score)
    assert res_scored.asset_type == "EQUITY"
    assert res_scored.assessment_status == "ASSESSED"
    assert res_scored.quality_score == 88.5
    assert res_scored.quality_grade == "A"

    # Equity holding without fundamental metrics
    eq_bare = {
        "symbol": "CASTROLIND",
        "company_name": "Castrol India",
        "asset_type": "EQUITY",
    }
    res_bare = svc.assess_single_holding(eq_bare)
    assert res_bare.asset_type == "EQUITY"
    assert res_bare.assessment_status == "UNAVAILABLE"
    assert res_bare.quality_grade == "N/A"
    assert res_bare.assessment_status != "UNSUPPORTED"

    # ETF holding preserves ETF assessment path
    etf_holding = {
        "symbol": "NIFTYBEES",
        "name": "Nippon India Nifty 50 ETF",
        "asset_type": "ETF",
        "expense_ratio": 0.05,
        "tracking_error": 0.02,
        "aum_cr": 5000.0,
    }
    res_etf = svc.assess_single_holding(etf_holding)
    assert res_etf.asset_type == "ETF"
    assert res_etf.assessment_status == "ASSESSED"


def test_alpha12_mapping_service_provider_resolution():
    """Verify Alpha12MappingService resolves Alpha 12 provider correctly."""
    sample_alpha12 = [
        {"symbol": "TRAVELFOOD", "name": "Travel Food", "alpha12_rank": 1, "alpha12_weight": 8.33},
        {"symbol": "CASTROLIND", "name": "Castrol India", "alpha12_rank": 2, "alpha12_weight": 8.33},
    ]
    provider = lambda: sample_alpha12
    svc = Alpha12MappingService(alpha12_provider=provider)

    res = svc.get_mapping()
    assert res.analysis_status == "ANALYZED"
    assert res.portfolio.total_alpha12_holdings == 2


def test_watchtower_monitoring_state_baseline():
    """Verify Watchtower monitor service handles baseline state safely."""
    svc = PortfolioHealthMonitorService()
    state = svc.get_monitoring_state()
    assert state.monitoring_status in ("READY", "WAITING", "UNAVAILABLE")
