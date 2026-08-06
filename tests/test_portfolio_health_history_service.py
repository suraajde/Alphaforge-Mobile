import json
import tempfile
import pytest
from pathlib import Path

from services.portfolio_health_history_service import (
    PortfolioHealthDashboardSummary,
    PortfolioHealthHistoricalAnalytics,
    PortfolioHealthHistoricalMetrics,
    PortfolioHealthHistoryEntry,
    PortfolioHealthHistoryService,
)
from services.portfolio_health_service import PortfolioHealthResult


@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "portfolio_health_history.json")
        yield path


def test_history_service_instantiation(temp_storage):
    """TEST 1: Verify service instantiation."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    assert service is not None
    assert service.storage_path == temp_storage


def test_save_snapshot(temp_storage):
    """TEST 2: Verify saving snapshot persists entry."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    result = PortfolioHealthResult(
        score=84,
        grade="B",
        diversification_rating="GOOD",
        concentration_rating="MODERATE",
        position_count=12,
        largest_position_weight_pct=15.0,
        cash_allocation_pct=5.0,
    )
    entry = service.save_snapshot(result)

    assert entry is not None
    assert isinstance(entry, PortfolioHealthHistoryEntry)
    assert entry.score == 84
    assert entry.grade == "B"
    assert entry.diversification_rating == "GOOD"
    assert entry.position_count == 12


def test_load_history(temp_storage):
    """TEST 3: Verify load_history returns persisted entries."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    res1 = PortfolioHealthResult(80, "B", "GOOD", "LOW", 10, 10.0, 5.0)
    res2 = PortfolioHealthResult(85, "B", "GOOD", "LOW", 12, 8.0, 5.0)

    service.save_snapshot(res1)
    service.save_snapshot(res2)

    history = service.get_history()
    assert len(history) == 2
    assert history[0].score == 80
    assert history[1].score == 85


def test_get_latest_entry(temp_storage):
    """TEST 4: Verify get_latest returns the most recent entry."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    res1 = PortfolioHealthResult(75, "C", "MODERATE", "MODERATE", 6, 18.0, 12.0)
    res2 = PortfolioHealthResult(90, "A", "GOOD", "LOW", 14, 7.0, 4.0)

    service.save_snapshot(res1)
    service.save_snapshot(res2)

    latest = service.get_latest()
    assert latest is not None
    assert latest.score == 90
    assert latest.grade == "A"


def test_get_previous_entry(temp_storage):
    """TEST 5: Verify get_previous returns second newest entry."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    res1 = PortfolioHealthResult(70, "C", "POOR", "MODERATE", 4, 19.0, 15.0)
    res2 = PortfolioHealthResult(80, "B", "MODERATE", "LOW", 8, 12.0, 8.0)
    res3 = PortfolioHealthResult(90, "A", "GOOD", "LOW", 12, 8.0, 5.0)

    service.save_snapshot(res1)
    service.save_snapshot(res2)
    service.save_snapshot(res3)

    previous = service.get_previous()
    assert previous is not None
    assert previous.score == 80
    assert previous.grade == "B"


def test_missing_file_safety(temp_storage):
    """TEST 6: Verify missing storage file returns empty history safely."""
    missing_path = temp_storage + ".nonexistent"
    service = PortfolioHealthHistoryService(storage_path=missing_path)

    history = service.get_history()
    assert history == []
    assert service.get_latest() is None
    assert service.get_previous() is None


def test_corrupt_file_safety(temp_storage):
    """TEST 7: Verify corrupt storage file returns empty history safely without throwing exceptions."""
    with open(temp_storage, "w", encoding="utf-8") as f:
        f.write("{ INVALID JSON CORRUPTED DATA }")

    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    history = service.get_history()
    assert history == []
    assert service.get_latest() is None
    assert service.get_previous() is None


def test_historical_analytics_object_exists(temp_storage):
    """TEST 1: Verify historical analytics object exists."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    analytics = service.get_historical_analytics()
    assert analytics is not None
    assert isinstance(analytics, PortfolioHealthHistoricalAnalytics)


def test_best_score_calculated_correctly(temp_storage):
    """TEST 2: Verify best score calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 95, 70, 85]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    analytics = service.get_historical_analytics()
    assert analytics.best_score == 95


def test_worst_score_calculated_correctly(temp_storage):
    """TEST 3: Verify worst score calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 95, 65, 85]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    analytics = service.get_historical_analytics()
    assert analytics.worst_score == 65


def test_average_score_calculated_correctly(temp_storage):
    """TEST 4: Verify average score calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 84, 82, 90]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    analytics = service.get_historical_analytics()
    assert analytics.history_count == 4
    assert analytics.average_score == 84.0


def test_improving_trend_detected(temp_storage):
    """TEST 5: Verify improving trend detected when current > average + 3."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [70, 75, 75, 90]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    analytics = service.get_historical_analytics()
    assert analytics.current_score == 90
    assert analytics.overall_trend == "IMPROVING"


def test_deteriorating_trend_detected(temp_storage):
    """TEST 6: Verify deteriorating trend detected when current < average - 3."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [90, 85, 85, 65]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    analytics = service.get_historical_analytics()
    assert analytics.current_score == 65
    assert analytics.overall_trend == "DETERIORATING"


def test_stable_trend_detected(temp_storage):
    """TEST 7: Verify stable trend detected when current is within average +/- 3."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 82, 84, 83]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    analytics = service.get_historical_analytics()
    assert analytics.overall_trend == "STABLE"


def test_empty_history_analytics_safety(temp_storage):
    """TEST 8: Verify empty history safety returns default historical analytics."""
    missing_path = temp_storage + ".empty"
    service = PortfolioHealthHistoryService(storage_path=missing_path)
    analytics = service.get_historical_analytics()
    assert analytics.history_count == 0
    assert analytics.best_score == 0
    assert analytics.worst_score == 0
    assert analytics.average_score == 0.0
    assert analytics.current_score == 0
    assert analytics.overall_trend == "STABLE"


def test_corrupt_history_analytics_safety(temp_storage):
    """TEST 9: Verify corrupt history safety returns default historical analytics."""
    with open(temp_storage, "w", encoding="utf-8") as f:
        f.write("{ CORRUPT JSON }")
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    analytics = service.get_historical_analytics()
    assert analytics.history_count == 0
    assert analytics.overall_trend == "STABLE"


def test_dashboard_summary_object_exists(temp_storage):
    """TEST 1: Dashboard summary object exists."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    summary = service.get_dashboard_summary()
    assert summary is not None
    assert isinstance(summary, PortfolioHealthDashboardSummary)


def test_dashboard_current_score_calculated_correctly(temp_storage):
    """TEST 2: Current score calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s, g in [(80, "B"), (84, "B"), (92, "A"), (71, "C")]:
        service.save_snapshot(PortfolioHealthResult(s, g, "GOOD", "LOW", 10, 10.0, 5.0))
    summary = service.get_dashboard_summary()
    assert summary.current_score == 71
    assert summary.current_grade == "C"


def test_dashboard_best_score_calculated_correctly(temp_storage):
    """TEST 3: Best score calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s, g in [(80, "B"), (84, "B"), (92, "A"), (71, "C")]:
        service.save_snapshot(PortfolioHealthResult(s, g, "GOOD", "LOW", 10, 10.0, 5.0))
    summary = service.get_dashboard_summary()
    assert summary.best_score == 92


def test_dashboard_worst_score_calculated_correctly(temp_storage):
    """TEST 4: Worst score calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s, g in [(80, "B"), (84, "B"), (92, "A"), (71, "C")]:
        service.save_snapshot(PortfolioHealthResult(s, g, "GOOD", "LOW", 10, 10.0, 5.0))
    summary = service.get_dashboard_summary()
    assert summary.worst_score == 71


def test_dashboard_average_score_calculated_correctly(temp_storage):
    """TEST 5: Average score calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s, g in [(80, "B"), (84, "B"), (92, "A"), (71, "C")]:
        service.save_snapshot(PortfolioHealthResult(s, g, "GOOD", "LOW", 10, 10.0, 5.0))
    summary = service.get_dashboard_summary()
    assert summary.total_snapshots == 4
    assert summary.average_score == 81.8


def test_dashboard_best_grade_calculated_correctly(temp_storage):
    """TEST 6: Best grade calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s, g in [(80, "B"), (84, "B"), (92, "A"), (71, "C")]:
        service.save_snapshot(PortfolioHealthResult(s, g, "GOOD", "LOW", 10, 10.0, 5.0))
    summary = service.get_dashboard_summary()
    assert summary.best_grade == "A"


def test_dashboard_worst_grade_calculated_correctly(temp_storage):
    """TEST 7: Worst grade calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s, g in [(80, "B"), (84, "B"), (92, "A"), (71, "C")]:
        service.save_snapshot(PortfolioHealthResult(s, g, "GOOD", "LOW", 10, 10.0, 5.0))
    summary = service.get_dashboard_summary()
    assert summary.worst_grade == "C"


def test_dashboard_empty_history_safety(temp_storage):
    """TEST 8: Empty history safety returns default summary."""
    missing_path = temp_storage + ".empty"
    service = PortfolioHealthHistoryService(storage_path=missing_path)
    summary = service.get_dashboard_summary()
    assert summary.total_snapshots == 0
    assert summary.current_score == 0
    assert summary.current_grade == "-"
    assert summary.best_score == 0
    assert summary.best_grade == "-"
    assert summary.worst_score == 0
    assert summary.worst_grade == "-"
    assert summary.average_score == 0.0


def test_dashboard_corrupt_history_safety(temp_storage):
    """TEST 9: Corrupt history safety returns default summary."""
    with open(temp_storage, "w", encoding="utf-8") as f:
        f.write("{ CORRUPT DATA }")
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    summary = service.get_dashboard_summary()
    assert summary.total_snapshots == 0
    assert summary.current_grade == "-"


def test_historical_metrics_object_exists(temp_storage):
    """TEST 1: Historical metrics object exists."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    metrics = service.get_historical_metrics()
    assert metrics is not None
    assert isinstance(metrics, PortfolioHealthHistoricalMetrics)


def test_metrics_score_range_calculated_correctly(temp_storage):
    """TEST 2: Score range calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 84, 92, 71]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert metrics.best_score == 92
    assert metrics.worst_score == 71
    assert metrics.score_range == 21


def test_metrics_volatility_calculated_correctly(temp_storage):
    """TEST 3: Volatility calculated correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 84, 82, 90]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert metrics.volatility_score == 4.7


def test_metrics_improving_periods_counted_correctly(temp_storage):
    """TEST 4: Improving periods counted correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 84, 82, 90]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert metrics.improving_periods == 2


def test_metrics_deteriorating_periods_counted_correctly(temp_storage):
    """TEST 5: Deteriorating periods counted correctly."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 84, 82, 90]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert metrics.deteriorating_periods == 1


def test_metrics_very_stable_classification(temp_storage):
    """TEST 6: VERY_STABLE classification (volatility 0 - 2.0)."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 81, 80, 82]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert metrics.volatility_score <= 2.0
    assert metrics.stability_rating == "VERY_STABLE"


def test_metrics_stable_classification(temp_storage):
    """TEST 7: STABLE classification (volatility 2.1 - 5.0)."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [80, 84, 82, 86]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert 2.1 <= metrics.volatility_score <= 5.0
    assert metrics.stability_rating == "STABLE"


def test_metrics_moderate_classification(temp_storage):
    """TEST 8: MODERATE classification (volatility 5.1 - 8.0)."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [70, 77, 70, 77]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert 5.1 <= metrics.volatility_score <= 8.0
    assert metrics.stability_rating == "MODERATE"


def test_metrics_volatile_classification(temp_storage):
    """TEST 9: VOLATILE classification (volatility 8.1+)."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    for s in [50, 70, 50, 75]:
        service.save_snapshot(PortfolioHealthResult(s, "B", "GOOD", "LOW", 10, 10.0, 5.0))
    metrics = service.get_historical_metrics()
    assert metrics.volatility_score >= 8.1
    assert metrics.stability_rating == "VOLATILE"


def test_metrics_empty_history_safety(temp_storage):
    """TEST 10: Empty history safety returns default metrics."""
    missing_path = temp_storage + ".empty"
    service = PortfolioHealthHistoryService(storage_path=missing_path)
    metrics = service.get_historical_metrics()
    assert metrics.score_range == 0
    assert metrics.volatility_score == 0.0
    assert metrics.improving_periods == 0
    assert metrics.deteriorating_periods == 0
    assert metrics.stability_rating == "VERY_STABLE"


def test_metrics_corrupt_history_safety(temp_storage):
    """TEST 11: Corrupt history safety returns default metrics."""
    with open(temp_storage, "w", encoding="utf-8") as f:
        f.write("{ CORRUPT FILE DATA }")
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    metrics = service.get_historical_metrics()
    assert metrics.score_range == 0
    assert metrics.stability_rating == "VERY_STABLE"



