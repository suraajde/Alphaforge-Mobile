import pytest
from services.portfolio_health_service import (
    PortfolioHealthService,
    PortfolioHealthSnapshot,
)


def test_service_instantiation():
    """TEST 1: Verify service instantiation."""
    service = PortfolioHealthService()
    assert service is not None


def test_build_snapshot_return_type():
    """TEST 2: Verify returned object is PortfolioHealthSnapshot."""
    service = PortfolioHealthService()
    snapshot = service.build_snapshot()
    assert isinstance(snapshot, PortfolioHealthSnapshot)


def test_snapshot_contains_required_fields():
    """TEST 3: Verify snapshot contains all required fields."""
    service = PortfolioHealthService()
    snapshot = service.build_snapshot()

    assert hasattr(snapshot, "position_count")
    assert hasattr(snapshot, "portfolio_value")
    assert hasattr(snapshot, "invested_value")
    assert hasattr(snapshot, "cash_allocation_pct")
    assert hasattr(snapshot, "largest_position")
    assert hasattr(snapshot, "largest_position_weight_pct")

    assert isinstance(snapshot.position_count, int)
    assert isinstance(snapshot.portfolio_value, float)
    assert isinstance(snapshot.invested_value, float)
    assert isinstance(snapshot.cash_allocation_pct, float)
    assert isinstance(snapshot.largest_position, str)
    assert isinstance(snapshot.largest_position_weight_pct, float)


def test_build_snapshot_defensive_empty_unavailable():
    """TEST 4: Verify service does not throw exceptions when portfolio data is empty or unavailable."""
    # Case 1: None app service with missing file/data
    service_none = PortfolioHealthService(portfolio_app_service=None)
    snapshot = service_none.build_snapshot()
    assert isinstance(snapshot, PortfolioHealthSnapshot)

    # Case 2: App service raising exception
    class FaultyAppService:
        def get_status(self):
            raise RuntimeError("Data pipeline failure")

    service_faulty = PortfolioHealthService(portfolio_app_service=FaultyAppService())
    snapshot_faulty = service_faulty.build_snapshot()
    assert isinstance(snapshot_faulty, PortfolioHealthSnapshot)
    assert snapshot_faulty.position_count == 0
    assert snapshot_faulty.largest_position == "N/A"

    # Case 3: Empty state dictionary
    class EmptyAppService:
        def get_status(self):
            return {"status": "OK", "state": {}}

    service_empty = PortfolioHealthService(portfolio_app_service=EmptyAppService())
    snapshot_empty = service_empty.build_snapshot()
    assert isinstance(snapshot_empty, PortfolioHealthSnapshot)
    assert snapshot_empty.position_count == 0


def test_build_snapshot_with_mock_portfolio():
    """Verify snapshot calculation accuracy with mock portfolio data."""
    class MockAppService:
        def get_status(self):
            return {
                "status": "OK",
                "state": {
                    "cash_balance": 5000.0,
                    "total_portfolio_value": 100000.0,
                    "positions": {
                        "KPITTECH": {
                            "symbol": "KPITTECH",
                            "quantity": 10,
                            "invested_cost": 40000.0,
                            "current_value": 60000.0,
                        },
                        "INFY": {
                            "symbol": "INFY",
                            "quantity": 20,
                            "invested_cost": 30000.0,
                            "current_value": 35000.0,
                        },
                    },
                },
            }

    service = PortfolioHealthService(portfolio_app_service=MockAppService())
    snapshot = service.build_snapshot()

    assert snapshot.position_count == 2
    assert snapshot.portfolio_value == 100000.0
    assert snapshot.invested_value == 70000.0
    assert snapshot.cash_allocation_pct == 5.0
    assert snapshot.largest_position == "KPITTECH"
    assert snapshot.largest_position_weight_pct == 60.0