"""Tests for RebalancingService (Sprint 13.7.0)."""



import pytest



from services.rebalancing_service import (

    RebalancingPortfolio,

    RebalancingPosition,

    RebalancingService,

    RebalancingState,

)





class _FakePosition:

    """Mimics a position object for testing."""



    def __init__(self, symbol="AAPL", name="Apple Inc.", asset_type="EQUITY", current_value=1000.0):

        self.symbol = symbol

        self.name = name

        self.asset_type = asset_type

        self.current_value = current_value





class _FakePortfolioService:

    """Mimics application portfolio service."""



    def __init__(self, positions=None, portfolio_value=None):

        self._positions = positions or []

        self._portfolio_value = portfolio_value



    def get_status(self):

        val = self._portfolio_value if self._portfolio_value is not None else sum(p.current_value for p in self._positions if hasattr(p, "current_value"))

        return {

            "status": "OK",

            "portfolio_value": val,

            "position_count": len(self._positions),

            "state": {"positions": self._positions},

        }





# ---------------------------------------------------------------------------

# Tests

# ---------------------------------------------------------------------------





def test_service_instantiation():

    """Verify RebalancingService instantiates without exception."""

    service = RebalancingService()

    assert service is not None





def test_empty_portfolio():

    """Verify empty input produces empty portfolio."""

    service = RebalancingService()

    portfolio = service.load_portfolio()



    assert isinstance(portfolio, RebalancingPortfolio)

    assert portfolio.total_value == 0.0

    assert portfolio.positions == []





def test_empty_state():

    """Verify empty input produces EMPTY status RebalancingState."""

    service = RebalancingService()

    state = service.get_state()



    assert isinstance(state, RebalancingState)

    assert state.status == "UNAVAILABLE" or state.status == "EMPTY"

    assert state.total_positions == 0

    assert state.total_value == 0.0





def test_position_creation():

    """Verify RebalancingPosition attributes are populated correctly."""

    pos = RebalancingPosition(

        symbol="AAPL",

        name="Apple Inc.",

        asset_type="EQUITY",

        current_value=1500.0,

        current_weight=15.0,

        target_weight=None,

    )

    assert pos.symbol == "AAPL"

    assert pos.name == "Apple Inc."

    assert pos.asset_type == "EQUITY"

    assert pos.current_value == 1500.0

    assert pos.current_weight == 15.0

    assert pos.target_weight is None





def test_portfolio_creation():

    """Verify RebalancingPortfolio stores total_value and positions list."""

    pos = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 2000.0, 100.0)

    portfolio = RebalancingPortfolio(total_value=2000.0, positions=[pos])



    assert portfolio.total_value == 2000.0

    assert len(portfolio.positions) == 1

    assert portfolio.positions[0].symbol == "MSFT"





def test_current_weight_calculation():

    """Verify current_weight = position.current_value / total_value * 100."""

    positions = [

        _FakePosition("AAPL", "Apple Inc.", "EQUITY", 3000.0),

        _FakePosition("MSFT", "Microsoft", "EQUITY", 7000.0),

    ]

    mock_svc = _FakePortfolioService(positions=positions, portfolio_value=10000.0)

    service = RebalancingService(portfolio_service=mock_svc)

    portfolio = service.load_portfolio()



    assert portfolio.total_value == 10000.0

    assert len(portfolio.positions) == 2

    assert portfolio.positions[0].current_weight == 30.0

    assert portfolio.positions[1].current_weight == 70.0





def test_zero_value_weight_safety():

    """Verify zero total portfolio value safely assigns 0.0 current_weight."""

    positions = [_FakePosition("AAPL", "Apple Inc.", "EQUITY", 0.0)]

    mock_svc = _FakePortfolioService(positions=positions, portfolio_value=0.0)

    service = RebalancingService(portfolio_service=mock_svc)

    portfolio = service.load_portfolio()



    assert portfolio.total_value == 0.0

    assert len(portfolio.positions) == 1

    assert portfolio.positions[0].current_weight == 0.0





def test_multiple_positions():

    """Verify multiple positions are normalized correctly."""

    positions = [

        _FakePosition("AAPL", "Apple Inc.", "EQUITY", 1000.0),

        _FakePosition("GOOGL", "Alphabet", "EQUITY", 2000.0),

        _FakePosition("BND", "Total Bond ETF", "FIXED_INCOME", 2000.0),

    ]

    mock_svc = _FakePortfolioService(positions=positions, portfolio_value=5000.0)

    service = RebalancingService(portfolio_service=mock_svc)

    portfolio = service.load_portfolio()



    assert portfolio.total_value == 5000.0

    assert len(portfolio.positions) == 3

    symbols = [p.symbol for p in portfolio.positions]

    assert symbols == ["AAPL", "GOOGL", "BND"]





def test_missing_portfolio_service():

    """Verify get_state returns fallback state when portfolio service is None."""

    service = RebalancingService(portfolio_service=None)

    state = service.get_state()



    assert isinstance(state, RebalancingState)

    assert state.total_positions == 0





def test_missing_fields_safety():

    """Verify position dictionary or object with missing attributes is handled safely."""



    class PartialPosition:

        def __init__(self):

            self.symbol = "NVDA"

            # Missing: name, asset_type, current_value



    mock_svc = _FakePortfolioService(positions=[PartialPosition()])

    service = RebalancingService(portfolio_service=mock_svc)

    portfolio = service.load_portfolio()



    assert len(portfolio.positions) == 1

    assert portfolio.positions[0].symbol == "NVDA"

    assert portfolio.positions[0].name == "NVDA"  # Fallback to symbol

    assert portfolio.positions[0].current_value == 0.0





def test_malformed_position_safety():

    """Verify non-record malformed items in position list are safely ignored."""

    positions = [None, "invalid_string", 456, _FakePosition("AMZN", "Amazon", "EQUITY", 1000.0)]

    mock_svc = _FakePortfolioService(positions=positions, portfolio_value=1000.0)

    service = RebalancingService(portfolio_service=mock_svc)

    portfolio = service.load_portfolio()



    assert len(portfolio.positions) == 1

    assert portfolio.positions[0].symbol == "AMZN"





def test_none_input_safety():

    """Verify service methods handle None portfolio gracefully."""

    service = RebalancingService(portfolio_service=None)

    portfolio = service.load_portfolio()

    assert isinstance(portfolio, RebalancingPortfolio)

    assert portfolio.positions == []





def test_defensive_exception_handling():

    """Verify service methods never propagate exceptions."""



    class FaultyPortfolioService:

        def get_status(self):

            raise RuntimeError("Database connection failure")



    service = RebalancingService(portfolio_service=FaultyPortfolioService())

    state = service.get_state()

    assert isinstance(state, RebalancingState)

    assert state.total_positions == 0





def test_state_summary():

    """Verify get_state populates READY status and total values for valid portfolios."""

    positions = [_FakePosition("SPY", "SPDR S&P 500 ETF", "ETF", 5000.0)]

    mock_svc = _FakePortfolioService(positions=positions, portfolio_value=5000.0)

    service = RebalancingService(portfolio_service=mock_svc)

    state = service.get_state()



    assert state.status == "READY"

    assert state.total_positions == 1

    assert state.total_value == 5000.0
