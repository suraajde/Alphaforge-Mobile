"""Unit tests for Holding Quality Engine Service (Sprint 13.8.1)."""
import pytest

from services.holding_quality_service import (
    HoldingQuality,
    HoldingQualityResult,
    HoldingQualityService,
    _empty_result,
    _safe_float,
    _safe_int,
)


class DummyPosition:
    def __init__(self, symbol, name, asset_type, expense_ratio=None, category=None, performance=None):
        self.symbol = symbol
        self.name = name
        self.asset_type = asset_type
        if expense_ratio is not None:
            self.expense_ratio = expense_ratio
        if category is not None:
            self.category = category
        if performance is not None:
            self.performance = performance


class DummyRebalancingState:
    def __init__(self, positions):
        class Portfolio:
            def __init__(self, pos):
                self.positions = pos
        self.portfolio = Portfolio(positions)


class DummyRebalancingService:
    def __init__(self, state):
        self._state = state

    def get_state(self):
        return self._state


def test_dataclasses():
    hq = HoldingQuality(
        symbol="NIFTY50",
        name="Nifty 50 Index Fund",
        asset_type="MUTUAL_FUND",
        quality_score=85.0,
        quality_grade="A",
        assessment_status="ASSESSED",
        rationale="Low expense ratio",
        evidence=["Low expense ratio"],
    )
    assert hq.symbol == "NIFTY50"
    assert hq.quality_score == 85.0
    assert hq.quality_grade == "A"
    assert hq.assessment_status == "ASSESSED"

    res = HoldingQualityResult(
        total_holdings=1,
        assessed_holdings=1,
        unassessed_holdings=0,
        average_quality_score=85.0,
        highest_quality_score=85.0,
        lowest_quality_score=85.0,
        holdings=[hq],
    )
    assert res.total_holdings == 1
    assert res.average_quality_score == 85.0


def test_safe_helpers():
    assert _safe_float("12.34") == 12.34
    assert _safe_float(None, 5.0) == 5.0
    assert _safe_float("abc", 2.0) == 2.0

    assert _safe_int("10") == 10
    assert _safe_int(None, 3) == 3
    assert _safe_int("xyz", 1) == 1

    er = _empty_result()
    assert er.total_holdings == 0
    assert er.holdings == []


def test_service_instantiation():
    svc = HoldingQualityService()
    assert svc._rebalancing_service is None
    assert svc._portfolio_service is None


def test_assess_fund_holding_with_metadata():
    svc = HoldingQualityService()
    fund = {
        "symbol": "HDFCNIFTY",
        "name": "HDFC Nifty 50 Index Fund",
        "asset_type": "MUTUAL_FUND",
        "expense_ratio": 0.20,
        "category": "Large Cap Index",
        "performance": "12.5% CAGR",
    }
    hq = svc.assess_fund_holding(fund)
    assert hq.symbol == "HDFCNIFTY"
    assert hq.assessment_status == "ASSESSED"
    assert hq.quality_score == 100.0
    assert hq.quality_grade == "A"
    assert "Low expense ratio" in hq.rationale


def test_assess_fund_holding_missing_metadata():
    svc = HoldingQualityService()
    fund = {
        "symbol": "SOMEFUND",
        "name": "Some Mutual Fund",
        "asset_type": "MUTUAL_FUND",
    }
    hq = svc.assess_fund_holding(fund)
    assert hq.symbol == "SOMEFUND"
    assert hq.assessment_status == "UNAVAILABLE"
    assert hq.quality_score == 0.0
    assert hq.quality_grade == "N/A"


def test_assess_etf_holding_with_metadata():
    svc = HoldingQualityService()
    etf = DummyPosition(
        symbol="GOLDBEES",
        name="Nippon India ETF Gold BeES",
        asset_type="ETF",
        expense_ratio=0.40,
        category="Commodity ETF",
    )
    hq = svc.assess_etf_holding(etf)
    assert hq.symbol == "GOLDBEES"
    assert hq.assessment_status == "ASSESSED"
    assert hq.quality_score == 55.0  # 25 (moderate er) + 30 (category)
    assert hq.quality_grade == "D"
    assert "Moderate ETF expense ratio" in hq.rationale


def test_assess_etf_holding_missing_metadata():
    svc = HoldingQualityService()
    etf = {
        "symbol": "NIFTYBEES",
        "name": "Nippon India ETF Nifty BeES",
        "asset_type": "ETF",
    }
    hq = svc.assess_etf_holding(etf)
    assert hq.symbol == "NIFTYBEES"
    assert hq.assessment_status == "UNAVAILABLE"
    assert hq.quality_score == 0.0
    assert hq.quality_grade == "N/A"


def test_unsupported_asset_type():
    svc = HoldingQualityService()
    stock = {
        "symbol": "CRYPTO_TOKEN",
        "name": "Crypto Token",
        "asset_type": "CRYPTO",
    }
    hq = svc.assess_single_holding(stock)
    assert hq.symbol == "CRYPTO_TOKEN"
    assert hq.assessment_status == "UNSUPPORTED"
    assert hq.quality_score == 0.0
    assert hq.quality_grade == "N/A"
    assert "unsupported" in hq.rationale.lower()


def test_deterministic_scoring_reproducibility():
    svc = HoldingQualityService()
    item = {
        "symbol": "INDEX1",
        "name": "Index Fund 1",
        "asset_type": "INDEX_FUND",
        "expense_ratio": 0.10,
        "category": "Equity Index",
    }
    hq1 = svc.assess_fund_holding(item)
    hq2 = svc.assess_fund_holding(item)
    assert hq1.quality_score == hq2.quality_score == 70.0
    assert hq1.quality_grade == hq2.quality_grade == "B"


def test_assess_holdings_multiple_items():
    svc = HoldingQualityService()
    holdings_list = [
        {
            "symbol": "FUND1",
            "name": "Fund One",
            "asset_type": "MUTUAL_FUND",
            "expense_ratio": 0.15,
            "category": "Flexi Cap",
            "performance": "15%",
        },
        {
            "symbol": "ETF1",
            "name": "ETF One",
            "asset_type": "ETF",
            "expense_ratio": 0.10,
            "category": "Large Cap ETF",
            "performance": "10%",
        },
        {
            "symbol": "STOCK1",
            "name": "Stock One",
            "asset_type": "EQUITY",
        },
        {
            "symbol": "NO_META_FUND",
            "name": "Fund Without Meta",
            "asset_type": "MUTUAL_FUND",
        },
    ]
    res = svc.assess_holdings(holdings_list)
    assert res.total_holdings == 4
    assert res.assessed_holdings == 2
    assert res.unassessed_holdings == 2
    assert res.highest_quality_score == 100.0
    assert res.lowest_quality_score == 100.0
    assert res.average_quality_score == 100.0


def test_assess_holdings_with_injected_rebalancing_service():
    pos1 = DummyPosition("FUND_INJ", "Injected Fund", "MUTUAL_FUND", expense_ratio=0.3, category="Large Cap")
    st = DummyRebalancingState([pos1])
    r_svc = DummyRebalancingService(st)
    svc = HoldingQualityService(rebalancing_service=r_svc)

    res = svc.assess_holdings()
    assert res.total_holdings == 1
    assert res.assessed_holdings == 1
    assert res.holdings[0].symbol == "FUND_INJ"


def test_none_and_malformed_input():
    svc = HoldingQualityService()
    res_none = svc.assess_holdings(None)
    assert isinstance(res_none, HoldingQualityResult)

    res_malformed = svc.assess_holdings("invalid string input")
    assert isinstance(res_malformed, HoldingQualityResult)

    single_malformed = svc.assess_single_holding(12345)
    assert single_malformed.assessment_status == "UNAVAILABLE"


def test_defensive_exception_handling():
    class BrokenObject:
        @property
        def symbol(self):
            raise RuntimeError("Corrupt property access")

    svc = HoldingQualityService()
    hq = svc.assess_single_holding(BrokenObject())
    assert hq.assessment_status == "UNAVAILABLE"
