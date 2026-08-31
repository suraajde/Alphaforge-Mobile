"""Sprint 14.1.8 Acceptance Test Suite — SIP & Lump-Sum Investment Allocation Engine

Verifies dynamic whole-share allocation, continuous SIP money deployment,
intelligent residual cash minimization, and strict execution bounds (executable_amount <= input_amount).
"""
from __future__ import annotations

import pytest
from services.investment_allocation_service import InvestmentAllocationService


@pytest.fixture
def mock_price_provider():
    """Realistic mixed stock prices for Alpha 12 candidates."""
    prices = {
        "RELIANCE": 2900.0,
        "TCS": 3800.0,
        "HDFCBANK": 1600.0,
        "INFY": 1800.0,
        "ICICIBANK": 1200.0,
        "BHARTIARTL": 1400.0,
        "ITC": 480.0,
        "SBIN": 820.0,
        "LTIM": 5200.0,
        "LT": 3600.0,
        "AXISBANK": 1150.0,
        "KOTAKBANK": 1750.0,
    }
    return lambda sym: {"symbol": sym, "price": prices.get(sym, 1000.0)}


def test_sip_6000_continuous_deployment(mock_price_provider):
    """Test Rs. 6,000 monthly SIP deployment.
    Verifies:
    - Executable total <= Rs. 6,000.
    - Continuous deployment: Executable total > Rs. 5,000 (residual cash intelligently minimized).
    - Unallocated residual cash < Rs. 1,000 (NOT Rs. 4,967).
    - Whole shares strictly enforced.
    - No selling required.
    """
    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_monthly_investment(6000.0)

    assert result.total_input_amount == 6000.0
    assert result.total_allocated_amount <= 6000.0
    assert result.total_allocated_amount >= 5000.0, f"Expected deployment > 5000, got {result.total_allocated_amount}"

    residual_cash = round(6000.0 - result.total_allocated_amount, 2)
    assert residual_cash < 1000.0, f"Expected residual cash < 1000, got {residual_cash}"

    for alloc in result.allocations:
        assert isinstance(alloc.quantity, int)
        if alloc.reference_price > 0:
            assert alloc.executable_amount == round(alloc.quantity * alloc.reference_price, 2)
        assert alloc.executable_amount <= 6000.0


def test_sip_10000_deployment(mock_price_provider):
    """Test Rs. 10,000 monthly SIP deployment."""
    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_monthly_investment(10000.0)

    assert result.total_input_amount == 10000.0
    assert result.total_allocated_amount <= 10000.0
    assert result.total_allocated_amount >= 8500.0

    residual = round(10000.0 - result.total_allocated_amount, 2)
    assert residual < 1500.0


def test_sip_30000_deployment(mock_price_provider):
    """Test Rs. 30,000 monthly SIP deployment."""
    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_monthly_investment(30000.0)

    assert result.total_input_amount == 30000.0
    assert result.total_allocated_amount <= 30000.0
    assert result.total_allocated_amount >= 28000.0

    residual = round(30000.0 - result.total_allocated_amount, 2)
    assert residual < 2000.0


def test_small_sip_amount(mock_price_provider):
    """Test small Rs. 2,000 monthly SIP deployment with high stock prices."""
    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_monthly_investment(2000.0)

    assert result.total_input_amount == 2000.0
    assert result.total_allocated_amount <= 2000.0
    # For Rs. 2,000, stocks priced <= Rs. 2,000 (e.g. HDFCBANK Rs. 1600, INFY Rs. 1800, ICICIBANK Rs. 1200, ITC Rs. 480) will absorb funds
    assert result.total_allocated_amount > 0.0


def test_high_priced_candidates_sip():
    """Test SIP when all candidate prices are high (e.g. Rs. 2,500, Rs. 3,500, Rs. 4,500)."""
    high_prices = {
        "STOCK_A": 2500.0,
        "STOCK_B": 3500.0,
        "STOCK_C": 4500.0,
    }
    price_provider = lambda sym: {"symbol": sym, "price": high_prices.get(sym, 3000.0)}

    explicit_candidates = [
        {"symbol": "STOCK_A", "company_name": "Stock A", "rank": 1, "conviction": 90.0},
        {"symbol": "STOCK_B", "company_name": "Stock B", "rank": 2, "conviction": 85.0},
        {"symbol": "STOCK_C", "company_name": "Stock C", "rank": 3, "conviction": 80.0},
    ]

    service = InvestmentAllocationService(price_provider=price_provider)
    result = service.allocate_monthly_investment(6000.0, alpha12_candidates=explicit_candidates)

    assert result.total_input_amount == 6000.0
    assert result.total_allocated_amount <= 6000.0
    # 6000 / prices: Stock A (2500) + Stock B (3500) = 6000 exactly!
    assert result.total_allocated_amount == 6000.0
    assert round(6000.0 - result.total_allocated_amount, 2) == 0.0


def test_existing_holdings_underrepresentation_bonus(mock_price_provider):
    """Test monthly SIP when portfolio has existing holdings with underrepresented positions."""
    portfolio_state = {
        "total_portfolio_value": 100000.0,
        "positions": {
            "RELIANCE": {"actual_weight": 20.0, "current_price": 2900.0},  # Overrepresented (20% vs target 8.33%)
            "INFY": {"actual_weight": 2.0, "current_price": 1800.0},       # Underrepresented (2% vs target 8.33%)
        },
    }
    candidates = [
        {"symbol": "RELIANCE", "company_name": "Reliance", "rank": 1, "conviction": 85.0},
        {"symbol": "INFY", "company_name": "Infosys", "rank": 2, "conviction": 85.0},
        {"symbol": "TCS", "company_name": "TCS", "rank": 3, "conviction": 80.0},
    ]

    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_monthly_investment(10000.0, portfolio_state=portfolio_state, alpha12_candidates=candidates)

    infy_alloc = next((a for a in result.allocations if a.symbol == "INFY"), None)
    reliance_alloc = next((a for a in result.allocations if a.symbol == "RELIANCE"), None)

    assert infy_alloc is not None
    assert reliance_alloc is not None
    # Underrepresented INFY should receive higher suggested allocation percentage than overrepresented RELIANCE
    assert infy_alloc.suggested_amount >= reliance_alloc.suggested_amount


def test_lump_sum_10k_allocation(mock_price_provider):
    """Test Rs. 10,000 lump-sum investment allocation."""
    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_lump_sum_investment(10000.0)

    assert result.allocation_type == "LUMP_SUM"
    assert result.total_input_amount == 10000.0
    assert result.total_allocated_amount <= 10000.0
    assert result.total_allocated_amount >= 8000.0


def test_lump_sum_50k_allocation(mock_price_provider):
    """Test Rs. 50,000 lump-sum investment allocation."""
    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_lump_sum_investment(50000.0)

    assert result.total_input_amount == 50000.0
    assert result.total_allocated_amount <= 50000.0
    assert result.total_allocated_amount >= 48000.0


def test_lump_sum_100k_allocation(mock_price_provider):
    """Test Rs. 1,00,000 lump-sum investment allocation."""
    service = InvestmentAllocationService(price_provider=mock_price_provider)
    result = service.allocate_lump_sum_investment(100000.0)

    assert result.total_input_amount == 100000.0
    assert result.total_allocated_amount <= 100000.0
    assert result.total_allocated_amount >= 98000.0
