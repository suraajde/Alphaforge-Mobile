"""Tests for AllocationAnalysisService (Sprint 13.7.1)."""



import pytest



from services.allocation_analysis_service import (

    AllocationAnalysisResult,

    AllocationAnalysisService,

    AllocationCategory,

)

from services.rebalancing_service import (

    RebalancingPortfolio,

    RebalancingPosition,

    RebalancingState,

)





class _FakeRebalancingService:

    """Mimics RebalancingService for testing."""



    def __init__(self, state=None):

        self._state = state



    def get_state(self):

        if self._state is not None:

            return self._state

        return RebalancingState("EMPTY", RebalancingPortfolio(0.0, []), 0, 0.0)





# ---------------------------------------------------------------------------

# Tests

# ---------------------------------------------------------------------------





def test_service_instantiation():

    """Verify AllocationAnalysisService instantiates without exception."""

    service = AllocationAnalysisService()

    assert service is not None





def test_empty_analysis():

    """Verify empty input returns empty AllocationAnalysisResult."""

    service = AllocationAnalysisService()

    result = service.analyze()



    assert isinstance(result, AllocationAnalysisResult)

    assert result.total_value == 0.0

    assert result.asset_allocations == []

    assert result.fund_allocations == []

    assert result.etf_allocations == []





def test_asset_allocation_analysis():

    """Verify asset allocation groups positions by asset_type."""

    pos1 = RebalancingPosition("AAPL", "Apple Inc.", "EQUITY", 6000.0, 60.0)

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 4000.0, 40.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert result.total_value == 10000.0

    assert len(result.asset_allocations) == 1

    assert result.asset_allocations[0].name == "EQUITY"

    assert result.asset_allocations[0].current_value == 10000.0

    assert result.asset_allocations[0].current_weight == 100.0

    assert result.asset_allocations[0].position_count == 2





def test_multiple_asset_types():

    """Verify multiple asset types are categorized into separate entries."""

    pos1 = RebalancingPosition("AAPL", "Apple Inc.", "EQUITY", 5000.0, 50.0)

    pos2 = RebalancingPosition("BND", "Bond ETF", "FIXED_INCOME", 5000.0, 50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert len(result.asset_allocations) == 2

    names = [cat.name for cat in result.asset_allocations]

    assert "EQUITY" in names

    assert "FIXED_INCOME" in names





def test_asset_allocation_weights():

    """Verify current_weight = category_current_value / total_portfolio_value * 100."""

    pos1 = RebalancingPosition("AAPL", "Apple Inc.", "EQUITY", 3000.0, 30.0)

    pos2 = RebalancingPosition("BND", "Total Bond ETF", "FIXED_INCOME", 7000.0, 70.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    weights = {cat.name: cat.current_weight for cat in result.asset_allocations}

    assert weights["EQUITY"] == 30.0

    assert weights["FIXED_INCOME"] == 70.0





def test_fund_allocation_analysis():

    """Verify fund positions are grouped under fund_allocations."""

    pos1 = RebalancingPosition("VFIAX", "Vanguard 500 Index Fund", "MUTUAL_FUND", 8000.0, 80.0)

    pos2 = RebalancingPosition("AAPL", "Apple Inc.", "EQUITY", 2000.0, 20.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert len(result.fund_allocations) == 1

    assert result.fund_allocations[0].name == "MUTUAL_FUND"

    assert result.fund_allocations[0].current_value == 8000.0

    assert result.fund_allocations[0].current_weight == 80.0

    assert result.fund_allocations[0].position_count == 1





def test_etf_allocation_analysis():

    """Verify ETF positions are grouped under etf_allocations."""

    pos1 = RebalancingPosition("SPY", "SPDR S&P 500 ETF", "ETF", 6000.0, 60.0)

    pos2 = RebalancingPosition("QQQ", "Invesco QQQ ETF", "ETF", 4000.0, 40.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert len(result.etf_allocations) == 1

    assert result.etf_allocations[0].name == "ETF"

    assert result.etf_allocations[0].current_value == 10000.0

    assert result.etf_allocations[0].current_weight == 100.0

    assert result.etf_allocations[0].position_count == 2





def test_multiple_funds():

    """Verify multiple fund positions are tracked correctly."""

    pos1 = RebalancingPosition("VFIAX", "Vanguard 500", "MUTUAL_FUND", 5000.0, 50.0)

    pos2 = RebalancingPosition("VBTLX", "Vanguard Total Bond", "INDEX_FUND", 5000.0, 50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert len(result.fund_allocations) == 2

    fund_names = [cat.name for cat in result.fund_allocations]

    assert "INDEX_FUND" in fund_names

    assert "MUTUAL_FUND" in fund_names





def test_multiple_etfs():

    """Verify multiple ETF categories or positions are tracked correctly."""

    pos1 = RebalancingPosition("SPY", "S&P 500 ETF", "ETF", 4000.0, 40.0)

    pos2 = RebalancingPosition("BND", "Total Bond ETF", "EXCHANGE_TRADED_FUND", 6000.0, 60.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert len(result.etf_allocations) == 2

    etf_names = [cat.name for cat in result.etf_allocations]

    assert "ETF" in etf_names

    assert "EXCHANGE_TRADED_FUND" in etf_names





def test_total_value_preserved():

    """Verify total portfolio value matches rebalancing state total value."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 12345.67, 100.0)

    state = RebalancingState("READY", RebalancingPortfolio(12345.67, [pos]), 1, 12345.67)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert result.total_value == 12345.67





def test_zero_value_safety():

    """Verify zero portfolio value safely computes 0.0 current_weight."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 0.0, 0.0)

    state = RebalancingState("READY", RebalancingPortfolio(0.0, [pos]), 1, 0.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert result.total_value == 0.0

    assert len(result.asset_allocations) == 1

    assert result.asset_allocations[0].current_weight == 0.0





def test_missing_asset_type_safety():

    """Verify position with missing asset_type defaults safely to EQUITY."""



    class PartialPosition:

        def __init__(self):

            self.symbol = "AAPL"

            self.current_value = 5000.0

            # Missing asset_type attribute



    state = RebalancingState("READY", RebalancingPortfolio(5000.0, [PartialPosition()]), 1, 5000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert len(result.asset_allocations) == 1

    assert result.asset_allocations[0].name == "EQUITY"





def test_malformed_position_safety():

    """Verify non-record malformed items in position list are safely skipped."""

    positions = [None, "invalid_string", 123, RebalancingPosition("AAPL", "Apple", "EQUITY", 5000.0, 100.0)]

    state = RebalancingState("READY", RebalancingPortfolio(5000.0, positions), 1, 5000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    assert len(result.asset_allocations) == 1

    assert result.asset_allocations[0].position_count == 1





def test_none_input_safety():

    """Verify passing None to analyze returns empty result."""

    service = AllocationAnalysisService()

    result = service.analyze(None)



    assert isinstance(result, AllocationAnalysisResult)

    assert result.total_value == 0.0





def test_missing_rebalancing_service_safety():

    """Verify get_analysis works safely when RebalancingService is None."""

    service = AllocationAnalysisService(rebalancing_service=None)

    result = service.get_analysis()



    assert isinstance(result, AllocationAnalysisResult)





def test_defensive_exception_handling():

    """Verify service methods never propagate exceptions."""



    class FaultyRebalancingService:

        def get_state(self):

            raise RuntimeError("Database connection lost")



    service = AllocationAnalysisService(rebalancing_service=FaultyRebalancingService())

    result = service.get_analysis()



    assert isinstance(result, AllocationAnalysisResult)

    assert result.total_value == 0.0





def test_allocation_summary_consistency():

    """Verify sum of category values equals portfolio total value for asset allocations."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 4000.0, 40.0)

    pos2 = RebalancingPosition("BND", "Bond ETF", "FIXED_INCOME", 6000.0, 60.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = AllocationAnalysisService()

    result = service.analyze(state)



    sum_cat_values = sum(cat.current_value for cat in result.asset_allocations)

    sum_cat_weights = sum(cat.current_weight for cat in result.asset_allocations)



    assert sum_cat_values == result.total_value == 10000.0

    assert pytest.approx(sum_cat_weights, 0.01) == 100.0
