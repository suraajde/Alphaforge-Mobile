import pytest
from services.portfolio_health_service import (
    PortfolioHealthAnalytics,
    PortfolioHealthResult,
    PortfolioHealthService,
    PortfolioHealthSnapshot,
    PortfolioHealthTrend,
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


def test_evaluate_healthy_portfolio():
    """Verify evaluation of a healthy portfolio."""
    service = PortfolioHealthService()
    snapshot = PortfolioHealthSnapshot(
        position_count=12,
        portfolio_value=100000.0,
        invested_value=95000.0,
        cash_allocation_pct=5.0,
        largest_position="RELIANCE",
        largest_position_weight_pct=9.5,
    )
    result = service.evaluate(snapshot)
    assert isinstance(result, PortfolioHealthResult)
    assert result.score > 80
    assert result.grade in ["A", "B"]


def test_evaluate_high_concentration():
    """Verify evaluation of high concentration risk."""
    service = PortfolioHealthService()
    snapshot = PortfolioHealthSnapshot(
        position_count=10,
        portfolio_value=100000.0,
        invested_value=95000.0,
        cash_allocation_pct=5.0,
        largest_position="RELIANCE",
        largest_position_weight_pct=25.0,
    )
    result = service.evaluate(snapshot)
    assert result.largest_position_weight_pct > 20
    assert result.concentration_rating == "HIGH"


def test_evaluate_poor_diversification():
    """Verify evaluation of poor diversification."""
    service = PortfolioHealthService()
    snapshot = PortfolioHealthSnapshot(
        position_count=3,
        portfolio_value=100000.0,
        invested_value=95000.0,
        cash_allocation_pct=5.0,
        largest_position="RELIANCE",
        largest_position_weight_pct=10.0,
    )
    result = service.evaluate(snapshot)
    assert result.position_count < 6
    assert result.diversification_rating == "POOR"


def test_evaluate_grade_mapping():
    """Verify grade mapping rules (A, B, C, D)."""
    service = PortfolioHealthService()

    # Score = 40 (pos) + 40 (conc) + 20 (cash) = 100 -> Grade A
    snap_a = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    res_a = service.evaluate(snap_a)
    assert res_a.score >= 90
    assert res_a.grade == "A"

    # Score = 30 (pos 7) + 30 (conc 12%) + 20 (cash 5%) = 80 -> Grade B
    snap_b = PortfolioHealthSnapshot(7, 100000.0, 95000.0, 5.0, "SYM", 12.0)
    res_b = service.evaluate(snap_b)
    assert 80 <= res_b.score <= 89
    assert res_b.grade == "B"

    # Score = 20 (pos 4) + 30 (conc 14%) + 20 (cash 5%) = 70 -> Grade C
    snap_c = PortfolioHealthSnapshot(4, 100000.0, 95000.0, 5.0, "SYM", 14.0)
    res_c = service.evaluate(snap_c)
    assert 70 <= res_c.score <= 79
    assert res_c.grade == "C"

    # Score = 10 (pos 2) + 10 (conc 25%) + 20 (cash 5%) = 40 -> Grade D
    snap_d = PortfolioHealthSnapshot(2, 100000.0, 95000.0, 5.0, "SYM", 25.0)
    res_d = service.evaluate(snap_d)
    assert res_d.score < 70
    assert res_d.grade == "D"


def test_evaluate_empty_portfolio_safety():
    """Verify evaluate() handles empty portfolio safely without exceptions."""
    class EmptyAppService:
        def get_status(self):
            return {"status": "OK", "state": {}}

    service = PortfolioHealthService(portfolio_app_service=EmptyAppService())
    result = service.evaluate()
    assert isinstance(result, PortfolioHealthResult)
    assert result.position_count == 0
    assert result.diversification_rating == "POOR"
    assert result.concentration_rating == "LOW"


def test_analytics_object_exists():
    """TEST 1: Verify analytics object exists on result."""
    service = PortfolioHealthService()
    result = service.evaluate()
    assert result.analytics is not None
    assert isinstance(result.analytics, PortfolioHealthAnalytics)


def test_breakdown_sums_correctly():
    """TEST 2: Verify breakdown scores sum to total score."""
    service = PortfolioHealthService()
    snapshot = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    result = service.evaluate(snapshot)
    analytics = result.analytics
    assert analytics is not None
    assert (
        analytics.diversification_score
        + analytics.concentration_score
        + analytics.cash_score
        == result.score
    )


def test_healthy_portfolio_produces_strengths():
    """TEST 3: Verify healthy portfolio produces strengths."""
    service = PortfolioHealthService()
    snapshot = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    result = service.evaluate(snapshot)
    assert result.analytics is not None
    assert len(result.analytics.strengths) > 0
    assert "Good diversification" in result.analytics.strengths
    assert "Low concentration risk" in result.analytics.strengths
    assert "Healthy cash allocation" in result.analytics.strengths


def test_weak_portfolio_produces_weaknesses():
    """TEST 4: Verify weak portfolio produces weaknesses."""
    service = PortfolioHealthService()
    snapshot = PortfolioHealthSnapshot(2, 100000.0, 70000.0, 30.0, "SYM", 35.0)
    result = service.evaluate(snapshot)
    assert result.analytics is not None
    assert len(result.analytics.weaknesses) > 0
    assert "Portfolio may be under-diversified" in result.analytics.weaknesses
    assert "High concentration risk" in result.analytics.weaknesses
    assert "Elevated cash allocation" in result.analytics.weaknesses


def test_empty_portfolio_safety_analytics():
    """TEST 5: Verify evaluate() handles empty portfolio safely and returns valid analytics."""
    class EmptyAppService:
        def get_status(self):
            return {"status": "OK", "state": {}}

    service = PortfolioHealthService(portfolio_app_service=EmptyAppService())
    result = service.evaluate()
    assert result.analytics is not None
    assert isinstance(result.analytics, PortfolioHealthAnalytics)
    assert result.analytics.diversification_score == 10
    assert result.analytics.concentration_score == 40
    assert result.analytics.cash_score == 20


def test_trend_object_exists():
    """TEST 1: Verify trend object exists on result."""
    service = PortfolioHealthService()
    result = service.evaluate()
    assert result.trend is not None
    assert isinstance(result.trend, PortfolioHealthTrend)


def test_improving_trend():
    """TEST 2: Verify improving trend direction when score increases by >= 3."""
    service = PortfolioHealthService()
    curr_snap = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    prev_snap = PortfolioHealthSnapshot(7, 100000.0, 95000.0, 5.0, "SYM", 12.0)
    prev_res = service.evaluate(prev_snap)
    curr_res = service.evaluate(curr_snap, previous=prev_res)

    assert curr_res.trend is not None
    assert curr_res.trend.score_change > 0
    assert curr_res.trend.trend_direction == "IMPROVING"


def test_deteriorating_trend():
    """TEST 3: Verify deteriorating trend direction when score decreases by >= 3."""
    service = PortfolioHealthService()
    curr_snap = PortfolioHealthSnapshot(3, 100000.0, 70000.0, 30.0, "SYM", 25.0)
    prev_snap = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    prev_res = service.evaluate(prev_snap)
    curr_res = service.evaluate(curr_snap, previous=prev_res)

    assert curr_res.trend is not None
    assert curr_res.trend.score_change < 0
    assert curr_res.trend.trend_direction == "DETERIORATING"


def test_stable_trend():
    """TEST 4: Verify stable trend direction when score change is within (-3, 3)."""
    service = PortfolioHealthService()
    curr_snap = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    prev_snap = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    prev_res = service.evaluate(prev_snap)
    curr_res = service.evaluate(curr_snap, previous=prev_res)

    assert curr_res.trend is not None
    assert curr_res.trend.score_change == 0
    assert curr_res.trend.trend_direction == "STABLE"


def test_no_previous_result_trend_safety():
    """TEST 5: Verify trend object is created safely when no previous result is provided."""
    service = PortfolioHealthService()
    result = service.evaluate(previous=None)
    assert result.trend is not None
    assert isinstance(result.trend, PortfolioHealthTrend)
    assert result.trend.score_change == 0
    assert result.trend.trend_direction == "STABLE"


def test_trend_uses_history_service_safely():
    """Verify trend evaluation uses history_service get_latest() safely when previous is None."""
    class MockHistoryService:
        def get_latest(self):
            return PortfolioHealthResult(
                score=80,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=10,
                largest_position_weight_pct=12.0,
                cash_allocation_pct=5.0,
            )

    history_svc = MockHistoryService()
    service = PortfolioHealthService(history_service=history_svc)

    curr_snap = PortfolioHealthSnapshot(12, 100000.0, 95000.0, 5.0, "SYM", 8.0)
    result = service.evaluate(curr_snap, previous=None)

    assert result.trend is not None
    assert result.trend.previous_score == 80
    assert result.trend.current_score == 100
    assert result.trend.score_change == 20
    assert result.trend.trend_direction == "IMPROVING"