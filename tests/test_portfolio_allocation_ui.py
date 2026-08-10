"""Regression coverage for executable whole-share investment allocations."""

import pytest
from PySide6.QtWidgets import QApplication

from app.screens.portfolio import Portfolio
from services.investment_allocation_service import InvestmentAllocationService


def _price_provider(symbol):
    """Deterministic reference prices for allocation and UI data-flow tests."""
    return {"price": 500.0 + (len(symbol) * 25.0)}


def _empty_portfolio_state():
    return {"positions": {}, "total_portfolio_value": 0.0}


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(["-platform", "offscreen"])


def test_monthly_allocation_exposes_whole_share_quantity_and_separate_amount():
    service = InvestmentAllocationService(price_provider=_price_provider)
    result = service.allocate_monthly_investment(30000.0, _empty_portfolio_state())

    assert result.allocation_type == "MONTHLY"
    assert result.total_allocated_amount == 30000.0
    assert sum(item.suggested_amount for item in result.allocations) == 30000.0
    assert result.allocations

    for item in result.allocations:
        assert item.reference_price > 0
        assert isinstance(item.quantity, int)
        assert item.quantity == item.suggested_amount // item.reference_price
        assert item.quantity != item.suggested_amount


def test_lump_sum_allocation_exposes_whole_share_quantity_and_separate_amount():
    service = InvestmentAllocationService(price_provider=_price_provider)
    result = service.allocate_lump_sum_investment(100000.0, _empty_portfolio_state())

    assert result.allocation_type == "LUMP_SUM"
    assert result.total_allocated_amount == 100000.0
    assert sum(item.suggested_amount for item in result.allocations) == 100000.0
    assert result.allocations

    for item in result.allocations:
        assert item.reference_price > 0
        assert isinstance(item.quantity, int)
        assert item.quantity == item.suggested_amount // item.reference_price
        assert item.quantity != item.suggested_amount


def test_reference_price_and_quantity_do_not_change_alpha12_ranking_or_weighting():
    unpriced_service = InvestmentAllocationService()
    priced_service = InvestmentAllocationService(price_provider=_price_provider)
    state = _empty_portfolio_state()

    unpriced = unpriced_service.allocate_monthly_investment(30000.0, state)
    priced = priced_service.allocate_monthly_investment(30000.0, state)

    assert [item.symbol for item in priced.allocations] == [item.symbol for item in unpriced.allocations]
    assert [item.alpha12_rank for item in priced.allocations] == [item.alpha12_rank for item in unpriced.allocations]
    assert [item.target_weight_pct for item in priced.allocations] == [item.target_weight_pct for item in unpriced.allocations]
    assert [item.suggested_amount for item in priced.allocations] == [item.suggested_amount for item in unpriced.allocations]


def test_monthly_ui_renders_sip_shares_before_sip_amount(qapp):
    result = InvestmentAllocationService(price_provider=_price_provider).allocate_monthly_investment(
        30000.0,
        _empty_portfolio_state(),
    )
    screen = Portfolio()

    screen._render_allocation_results(result)

    headers = [screen.alloc_table.horizontalHeaderItem(index).text() for index in range(screen.alloc_table.columnCount())]
    first = result.allocations[0]
    assert headers[7:10] == ["Price", "SIP Shares", "SIP Amount"]
    assert screen.alloc_table.item(0, 8).text() == str(first.quantity)
    assert screen.alloc_table.item(0, 9).text() == f"₹{first.suggested_amount:,.2f}"
    assert screen.alloc_table.item(0, 8).text() != f"{first.suggested_amount:,.2f}"


def test_lump_sum_ui_renders_shares_to_buy_before_investment(qapp):
    result = InvestmentAllocationService(price_provider=_price_provider).allocate_lump_sum_investment(
        100000.0,
        _empty_portfolio_state(),
    )
    screen = Portfolio()

    screen._render_allocation_results(result)

    headers = [screen.alloc_table.horizontalHeaderItem(index).text() for index in range(screen.alloc_table.columnCount())]
    first = result.allocations[0]
    assert headers[7:10] == ["Price", "Shares to Buy", "Investment"]
    assert screen.alloc_table.item(0, 8).text() == str(first.quantity)
    assert screen.alloc_table.item(0, 9).text() == f"₹{first.suggested_amount:,.2f}"
    assert screen.alloc_table.item(0, 8).text() != f"{first.suggested_amount:,.2f}"


def test_investment_allocation_uses_authoritative_alpha12_provider():
    """Verify InvestmentAllocationService consumes authoritative Alpha 12 provider candidates."""
    authoritative_candidates = [
        {"symbol": "TRAVELFOOD", "name": "Travel Food Services", "rank": 1, "conviction": 95.0},
        {"symbol": "CASTROLIND", "name": "Castrol India", "rank": 2, "conviction": 92.5},
        {"symbol": "CAPLIPOINT", "name": "Caplin Point Lab", "rank": 3, "conviction": 90.0},
        {"symbol": "AIAENG", "name": "AIA Engineering", "rank": 4, "conviction": 87.5},
        {"symbol": "CPPLUS", "name": "CP PLUS Ltd", "rank": 5, "conviction": 85.0},
        {"symbol": "GLAND", "name": "Gland Pharma", "rank": 6, "conviction": 82.5},
        {"symbol": "LLOYDSME", "name": "Lloyds Metals", "rank": 7, "conviction": 80.0},
        {"symbol": "HONASA", "name": "Honasa Consumer", "rank": 8, "conviction": 77.5},
        {"symbol": "VIJAYA", "name": "Vijaya Diagnostic", "rank": 9, "conviction": 75.0},
        {"symbol": "HSCL", "name": "Himadri Speciality", "rank": 10, "conviction": 72.5},
        {"symbol": "SAREGAMA", "name": "Saregama India", "rank": 11, "conviction": 70.0},
        {"symbol": "MARICO", "name": "Marico Ltd", "rank": 12, "conviction": 67.5},
    ]

    def _auth_provider():
        return authoritative_candidates

    service = InvestmentAllocationService(
        price_provider=_price_provider,
        alpha12_provider=_auth_provider,
    )

    state = _empty_portfolio_state()
    monthly_res = service.allocate_monthly_investment(30000.0, state)
    lump_res = service.allocate_lump_sum_investment(100000.0, state)

    monthly_symbols = [item.symbol for item in monthly_res.allocations]
    lump_symbols = [item.symbol for item in lump_res.allocations]
    expected_symbols = [cand["symbol"] for cand in authoritative_candidates]

    # A. Monthly allocation uses authoritative candidates
    assert monthly_symbols == expected_symbols

    # B. Lump-sum allocation uses authoritative candidates
    assert lump_symbols == expected_symbols

    # C. Monthly and lump-sum candidate symbol sets are identical
    assert monthly_symbols == lump_symbols

    # D. Candidate ordering and ranks match authoritative source
    assert [item.alpha12_rank for item in monthly_res.allocations] == list(range(1, 13))
    assert [item.alpha12_rank for item in lump_res.allocations] == list(range(1, 13))

    # E. No stale universe fallback symbols appear (e.g., AWL, ABBOTINDIA, ATGL)
    stale_symbols = {"AWL", "ABBOTINDIA", "ABBOTTINDIA", "ATGL", "ABCAPITAL"}
    assert not (set(monthly_symbols) & stale_symbols)
    assert not (set(lump_symbols) & stale_symbols)

    # F. Mathematics check: amounts sum to input total
    assert sum(item.suggested_amount for item in monthly_res.allocations) == 30000.0
    assert sum(item.suggested_amount for item in lump_res.allocations) == 100000.0


def test_investment_allocation_supports_explicit_alpha12_candidates_override():
    """Verify explicit alpha12_candidates parameter overrides fallback and takes precedence."""
    explicit_candidates = [
        {"symbol": "STOCK_A", "company_name": "Company A", "rank": 1},
        {"symbol": "STOCK_B", "company_name": "Company B", "rank": 2},
    ]

    service = InvestmentAllocationService(price_provider=_price_provider)
    state = _empty_portfolio_state()

    monthly_res = service.allocate_monthly_investment(10000.0, state, alpha12_candidates=explicit_candidates)
    lump_res = service.allocate_lump_sum_investment(50000.0, state, alpha12_candidates=explicit_candidates)

    assert [item.symbol for item in monthly_res.allocations] == ["STOCK_A", "STOCK_B"]
    assert [item.symbol for item in lump_res.allocations] == ["STOCK_A", "STOCK_B"]
