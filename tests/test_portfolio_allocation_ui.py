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
