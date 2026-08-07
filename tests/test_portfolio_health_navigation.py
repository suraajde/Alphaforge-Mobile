import pytest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.screens.portfolio_health import PortfolioHealth


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_portfolio_health_screen_instantiation(qapp):
    # Verify PortfolioHealth screen instantiates without exception
    screen = PortfolioHealth()
    assert screen is not None


def test_main_window_instantiation(qapp):
    # Verify MainWindow instantiates without exception
    win = MainWindow()
    assert win is not None


def test_portfolio_health_page_exists(qapp):
    # Verify PortfolioHealth page exists on MainWindow stacked widget
    win = MainWindow()
    assert hasattr(win, "portfolio_health")
    assert isinstance(win.portfolio_health, PortfolioHealth)
    assert win.pages.indexOf(win.portfolio_health) != -1


def test_health_btn_exists(qapp):
    # Verify health_btn exists on Sidebar
    win = MainWindow()
    assert hasattr(win.sidebar, "health_btn")


def test_navigation_wiring(qapp):
    # Verify navigation wiring: clicking health_btn sets current widget to portfolio_health
    win = MainWindow()
    win.sidebar.health_btn.click()
    assert win.pages.currentWidget() == win.portfolio_health


def test_no_exceptions_during_screen_creation(qapp):
    # Verify no exceptions during screen creation and card structure presence
    try:
        screen = PortfolioHealth()
        assert screen is not None
        assert "Overall Health Score" in screen.cards
        assert "Diversification" in screen.cards
        assert "Concentration" in screen.cards
        assert "Position Count" in screen.cards
        assert "Cash Allocation" in screen.cards
        assert "Largest Position" in screen.cards
    except Exception as e:
        pytest.fail(f"PortfolioHealth screen creation raised an exception: {e}")


def test_live_data_binding(qapp):
    from services.portfolio_health_service import PortfolioHealthSnapshot

    class DummyHealthService:
        def build_snapshot(self):
            return PortfolioHealthSnapshot(
                position_count=15,
                portfolio_value=200000.0,
                invested_value=180000.0,
                cash_allocation_pct=10.0,
                largest_position="TCS",
                largest_position_weight_pct=12.5,
            )

    screen = PortfolioHealth(service=DummyHealthService())
    assert screen.cards["Position Count"].text() == "15"
    assert screen.cards["Cash Allocation"].text() == "10%"
    assert screen.cards["Largest Position"].text() == "TCS"


def test_evaluate_result_bound_to_cards(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthResult,
        PortfolioHealthSnapshot,
    )

    class MockHealthService:
        def build_snapshot(self):
            return PortfolioHealthSnapshot(
                position_count=12,
                portfolio_value=100000.0,
                invested_value=95000.0,
                cash_allocation_pct=5.0,
                largest_position="RELIANCE",
                largest_position_weight_pct=15.0,
            )

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=85,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
            )

    screen = PortfolioHealth(service=MockHealthService())
    assert "85 / 100" in screen.cards["Overall Health Score"].text()
    assert screen.cards["Diversification"].text() == "GOOD"
    assert screen.cards["Concentration"].text() == "MODERATE"


def test_empty_portfolio_ui_safety(qapp):
    class EmptyHealthService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            from services.portfolio_health_service import PortfolioHealthResult
            return PortfolioHealthResult(
                score=70,
                grade="C",
                diversification_rating="POOR",
                concentration_rating="LOW",
                position_count=0,
                largest_position_weight_pct=0.0,
                cash_allocation_pct=0.0,
            )

    screen = PortfolioHealth(service=EmptyHealthService())
    assert "70 / 100" in screen.cards["Overall Health Score"].text()
    assert screen.cards["Diversification"].text() == "POOR"
    assert screen.cards["Concentration"].text() == "LOW"


def test_analytics_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_breakdown_div")
    assert hasattr(screen, "lbl_breakdown_conc")
    assert hasattr(screen, "lbl_breakdown_cash")
    assert hasattr(screen, "strengths_container")
    assert hasattr(screen, "weaknesses_container")


def test_breakdown_section_displays(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthAnalytics,
        PortfolioHealthResult,
    )

    class MockService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=85,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
                analytics=PortfolioHealthAnalytics(
                    diversification_score=40,
                    concentration_score=30,
                    cash_score=15,
                    strengths=["Good diversification"],
                    weaknesses=["Elevated concentration"],
                ),
            )

    screen = PortfolioHealth(service=MockService())
    assert "Diversification: 40 / 40" in screen.lbl_breakdown_div.text()
    assert "Concentration: 30 / 40" in screen.lbl_breakdown_conc.text()
    assert "Cash Allocation: 15 / 20" in screen.lbl_breakdown_cash.text()


def test_strengths_section_displays(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthAnalytics,
        PortfolioHealthResult,
    )

    class MockService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=100,
                grade="A",
                diversification_rating="GOOD",
                concentration_rating="LOW",
                position_count=12,
                largest_position_weight_pct=8.0,
                cash_allocation_pct=5.0,
                analytics=PortfolioHealthAnalytics(
                    diversification_score=40,
                    concentration_score=40,
                    cash_score=20,
                    strengths=["Good diversification", "Low concentration risk"],
                    weaknesses=[],
                ),
            )

    screen = PortfolioHealth(service=MockService())
    assert screen.strengths_container.count() == 2


def test_weaknesses_section_displays(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthAnalytics,
        PortfolioHealthResult,
    )

    class MockService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=60,
                grade="D",
                diversification_rating="POOR",
                concentration_rating="HIGH",
                position_count=3,
                largest_position_weight_pct=35.0,
                cash_allocation_pct=25.0,
                analytics=PortfolioHealthAnalytics(
                    diversification_score=10,
                    concentration_score=10,
                    cash_score=5,
                    strengths=[],
                    weaknesses=[
                        "Portfolio may be under-diversified",
                        "High concentration risk",
                    ],
                ),
            )

    screen = PortfolioHealth(service=MockService())
    assert screen.weaknesses_container.count() == 2


def test_trend_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_trend_current")
    assert hasattr(screen, "lbl_trend_previous")
    assert hasattr(screen, "lbl_trend_change")
    assert hasattr(screen, "lbl_trend_direction")


def test_trend_section_displays_values(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthResult,
        PortfolioHealthTrend,
    )

    class MockTrendService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=84,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
                trend=PortfolioHealthTrend(
                    current_score=84,
                    previous_score=80,
                    score_change=4,
                    current_grade="B",
                    previous_grade="B",
                    trend_direction="IMPROVING",
                ),
            )

    screen = PortfolioHealth(service=MockTrendService())
    assert "Current Score: 84" in screen.lbl_trend_current.text()
    assert "Previous Score: 80" in screen.lbl_trend_previous.text()
    assert "Score Change: +4" in screen.lbl_trend_change.text()
    assert "Trend: IMPROVING" in screen.lbl_trend_direction.text()


def test_history_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_history_entries")
    assert hasattr(screen, "lbl_history_latest_score")
    assert hasattr(screen, "lbl_history_latest_grade")


def test_history_values_display(qapp):
    from services.portfolio_health_history_service import PortfolioHealthHistoryEntry

    class MockHistoryService:
        def get_history(self):
            return [
                PortfolioHealthHistoryEntry(
                    timestamp="2026-08-06T12:00:00Z",
                    score=84,
                    grade="B",
                    diversification_rating="GOOD",
                    concentration_rating="MODERATE",
                    position_count=12,
                    largest_position_weight_pct=15.0,
                    cash_allocation_pct=5.0,
                )
            ]

    history_svc = MockHistoryService()
    screen = PortfolioHealth(history_service=history_svc)
    assert "History Entries: 1" in screen.lbl_history_entries.text()
    assert "Latest Score: 84" in screen.lbl_history_latest_score.text()
    assert "Latest Grade: B" in screen.lbl_history_latest_grade.text()


def test_empty_history_ui_safety(qapp):
    class EmptyHistoryService:
        def get_history(self):
            return []

    history_svc = EmptyHistoryService()
    screen = PortfolioHealth(history_service=history_svc)
    assert "History Entries: 0" in screen.lbl_history_entries.text()
    assert "Latest Score: N/A" in screen.lbl_history_latest_score.text()
    assert "Latest Grade: N/A" in screen.lbl_history_latest_grade.text()


def test_historical_analytics_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_hist_entries")
    assert hasattr(screen, "lbl_hist_best")
    assert hasattr(screen, "lbl_hist_worst")
    assert hasattr(screen, "lbl_hist_avg")
    assert hasattr(screen, "lbl_hist_curr")
    assert hasattr(screen, "lbl_hist_trend")


def test_historical_analytics_values_display(qapp):
    from services.portfolio_health_history_service import PortfolioHealthHistoricalAnalytics
    from services.portfolio_health_service import PortfolioHealthResult

    class MockHistService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=84,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
                historical_analytics=PortfolioHealthHistoricalAnalytics(
                    history_count=12,
                    best_score=92,
                    worst_score=71,
                    average_score=83.4,
                    current_score=84,
                    overall_trend="IMPROVING",
                ),
            )

    screen = PortfolioHealth(service=MockHistService())
    assert "History Entries: 12" in screen.lbl_hist_entries.text()
    assert "Best Score: 92" in screen.lbl_hist_best.text()
    assert "Worst Score: 71" in screen.lbl_hist_worst.text()
    assert "Average Score: 83.4" in screen.lbl_hist_avg.text()
    assert "Current Score: 84" in screen.lbl_hist_curr.text()
    assert "Overall Trend: IMPROVING" in screen.lbl_hist_trend.text()


def test_dashboard_summary_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_dash_curr_score")
    assert hasattr(screen, "lbl_dash_curr_grade")
    assert hasattr(screen, "lbl_dash_best_score")
    assert hasattr(screen, "lbl_dash_best_grade")
    assert hasattr(screen, "lbl_dash_worst_score")
    assert hasattr(screen, "lbl_dash_worst_grade")
    assert hasattr(screen, "lbl_dash_avg_score")
    assert hasattr(screen, "lbl_dash_total_snapshots")
    assert hasattr(screen, "lbl_highlight_highest")
    assert hasattr(screen, "lbl_highlight_lowest")
    assert hasattr(screen, "lbl_highlight_vs_avg")


def test_dashboard_summary_values_display(qapp):
    from services.portfolio_health_history_service import PortfolioHealthDashboardSummary
    from services.portfolio_health_service import PortfolioHealthResult

    class MockDashService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=84,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
                dashboard_summary=PortfolioHealthDashboardSummary(
                    total_snapshots=12,
                    current_score=84,
                    current_grade="B",
                    best_score=92,
                    best_grade="A",
                    worst_score=71,
                    worst_grade="C",
                    average_score=83.4,
                ),
            )

    screen = PortfolioHealth(service=MockDashService())
    assert "Current Score: 84" in screen.lbl_dash_curr_score.text()
    assert "Current Grade: B" in screen.lbl_dash_curr_grade.text()
    assert "Best Historical Score: 92" in screen.lbl_dash_best_score.text()
    assert "Best Historical Grade: A" in screen.lbl_dash_best_grade.text()
    assert "Worst Historical Score: 71" in screen.lbl_dash_worst_score.text()
    assert "Worst Historical Grade: C" in screen.lbl_dash_worst_grade.text()
    assert "Average Historical Score: 83.4" in screen.lbl_dash_avg_score.text()
    assert "Total Snapshots: 12" in screen.lbl_dash_total_snapshots.text()

    assert "Highest Score Achieved: 92" in screen.lbl_highlight_highest.text()
    assert "Lowest Score Achieved: 71" in screen.lbl_highlight_lowest.text()
    assert "Current Score vs Average: +0.6" in screen.lbl_highlight_vs_avg.text()


def test_historical_metrics_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_metrics_range")
    assert hasattr(screen, "lbl_metrics_volatility")
    assert hasattr(screen, "lbl_metrics_improving")
    assert hasattr(screen, "lbl_metrics_deteriorating")
    assert hasattr(screen, "lbl_metrics_stability")


def test_historical_metrics_values_display(qapp):
    from services.portfolio_health_history_service import PortfolioHealthHistoricalMetrics
    from services.portfolio_health_service import PortfolioHealthResult

    class MockMetricsService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=84,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
                historical_metrics=PortfolioHealthHistoricalMetrics(
                    score_range=21,
                    best_score=92,
                    worst_score=71,
                    volatility_score=4.7,
                    improving_periods=2,
                    deteriorating_periods=1,
                    stability_rating="STABLE",
                ),
            )

    screen = PortfolioHealth(service=MockMetricsService())
    assert "Score Range: 21" in screen.lbl_metrics_range.text()
    assert "Volatility Score: 4.7" in screen.lbl_metrics_volatility.text()
    assert "Improving Periods: 2" in screen.lbl_metrics_improving.text()
    assert "Deteriorating Periods: 1" in screen.lbl_metrics_deteriorating.text()
    assert "Stability Rating: STABLE" in screen.lbl_metrics_stability.text()


def test_historical_insights_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_insights_improvement")
    assert hasattr(screen, "lbl_insights_deterioration")
    assert hasattr(screen, "lbl_insights_neutral")
    assert hasattr(screen, "lbl_insights_consistency")
    assert hasattr(screen, "lbl_insights_quality")
    assert hasattr(screen, "lbl_insights_direction")


def test_historical_insights_values_display(qapp):
    from services.portfolio_health_history_service import PortfolioHealthHistoricalInsights
    from services.portfolio_health_service import PortfolioHealthResult

    class MockInsightsService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=84,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
                historical_insights=PortfolioHealthHistoricalInsights(
                    improvement_percentage=66.7,
                    deterioration_percentage=33.3,
                    neutral_percentage=0.0,
                    consistency_score=33.4,
                    quality_rating="FAIR",
                    direction_rating="IMPROVING",
                ),
            )

    screen = PortfolioHealth(service=MockInsightsService())
    assert "Improvement Percentage: 66.7%" in screen.lbl_insights_improvement.text()
    assert "Deterioration Percentage: 33.3%" in screen.lbl_insights_deterioration.text()
    assert "Neutral Percentage: 0.0%" in screen.lbl_insights_neutral.text()
    assert "Consistency Score: 33.4" in screen.lbl_insights_consistency.text()
    assert "Quality Rating: FAIR" in screen.lbl_insights_quality.text()
    assert "Direction Rating: IMPROVING" in screen.lbl_insights_direction.text()


def test_monitoring_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_mon_enabled")
    assert hasattr(screen, "lbl_mon_status")
    assert hasattr(screen, "lbl_mon_snapshots")
    assert hasattr(screen, "lbl_mon_latest_snapshot")
    assert hasattr(screen, "lbl_mon_latest_score")
    assert hasattr(screen, "lbl_mon_latest_grade")


def test_monitoring_values_display(qapp):
    from services.portfolio_health_monitor_service import PortfolioHealthMonitoringState

    class MockMonitorService:
        def get_monitoring_state(self):
            return PortfolioHealthMonitoringState(
                monitoring_enabled=True,
                monitoring_status="READY",
                snapshot_count=18,
                latest_snapshot_time="2026-08-07 09:15",
                latest_score=91,
                latest_grade="A",
            )

    mon_svc = MockMonitorService()
    screen = PortfolioHealth(monitor_service=mon_svc)
    assert "Monitoring Enabled: YES" in screen.lbl_mon_enabled.text()
    assert "Monitoring Status: READY" in screen.lbl_mon_status.text()
    assert "Snapshots Available: 18" in screen.lbl_mon_snapshots.text()
    assert "Latest Snapshot: 2026-08-07 09:15" in screen.lbl_mon_latest_snapshot.text()
    assert "Latest Score: 91" in screen.lbl_mon_latest_score.text()
    assert "Latest Grade: A" in screen.lbl_mon_latest_grade.text()


def test_monitoring_empty_history_safe(qapp):
    import shutil
    import tempfile
    from pathlib import Path
    from services.portfolio_health_history_service import PortfolioHealthHistoryService
    from services.portfolio_health_monitor_service import PortfolioHealthMonitorService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        empty_file = Path(temp_dir) / "empty.json"
        empty_file.write_text("[]", encoding="utf-8")

        hist_svc = PortfolioHealthHistoryService(storage_path=str(empty_file))
        mon_svc = PortfolioHealthMonitorService(history_service=hist_svc)
        screen = PortfolioHealth(monitor_service=mon_svc, history_service=hist_svc)

        assert "Monitoring Enabled: YES" in screen.lbl_mon_enabled.text()
        assert "Monitoring Status: WAITING" in screen.lbl_mon_status.text()
        assert "Snapshots Available: 0" in screen.lbl_mon_snapshots.text()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_monitoring_corrupt_history_safe(qapp):
    import shutil
    import tempfile
    from pathlib import Path
    from services.portfolio_health_history_service import PortfolioHealthHistoryService
    from services.portfolio_health_monitor_service import PortfolioHealthMonitorService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        corrupt_file = Path(temp_dir) / "corrupt.json"
        corrupt_file.write_text("INVALID{", encoding="utf-8")

        hist_svc = PortfolioHealthHistoryService(storage_path=str(corrupt_file))
        mon_svc = PortfolioHealthMonitorService(history_service=hist_svc)
        screen = PortfolioHealth(monitor_service=mon_svc, history_service=hist_svc)

        assert "Monitoring Enabled: NO" in screen.lbl_mon_enabled.text()
        assert "Monitoring Status: UNAVAILABLE" in screen.lbl_mon_status.text()
        assert "Snapshots Available: 0" in screen.lbl_mon_snapshots.text()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_change_detection_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_cd_snapshots_compared")
    assert hasattr(screen, "lbl_cd_changes_detected")
    assert hasattr(screen, "lbl_cd_total_changes")
    assert hasattr(screen, "changes_list_container")


def test_change_detection_values_display(qapp):
    from services.portfolio_health_change_detection_service import (
        PortfolioHealthChange,
        PortfolioHealthChangeReport,
    )

    class MockChangeDetectionService:
        def detect_changes(self):
            return PortfolioHealthChangeReport(
                snapshot_count=2,
                total_changes=3,
                has_changes=True,
                changes=[
                    PortfolioHealthChange("Health Score", "84", "91", "INCREASED"),
                    PortfolioHealthChange("Grade", "B", "A", "CHANGED"),
                    PortfolioHealthChange("Cash Allocation", "8%", "5%", "DECREASED"),
                ],
            )

    cd_svc = MockChangeDetectionService()
    screen = PortfolioHealth(change_detection_service=cd_svc)

    assert "Snapshots Compared: 2" in screen.lbl_cd_snapshots_compared.text()
    assert "Changes Detected: YES" in screen.lbl_cd_changes_detected.text()
    assert "Total Changes: 3" in screen.lbl_cd_total_changes.text()
    assert screen.changes_list_container.count() == 3


def test_change_detection_no_history_safe(qapp):
    import shutil
    import tempfile
    from pathlib import Path
    from services.portfolio_health_change_detection_service import PortfolioHealthChangeDetectionService
    from services.portfolio_health_history_service import PortfolioHealthHistoryService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        missing_file = Path(temp_dir) / "missing.json"
        hist_svc = PortfolioHealthHistoryService(storage_path=str(missing_file))
        cd_svc = PortfolioHealthChangeDetectionService(history_service=hist_svc)
        screen = PortfolioHealth(change_detection_service=cd_svc, history_service=hist_svc)

        assert "Snapshots Compared: 0" in screen.lbl_cd_snapshots_compared.text()
        assert "Changes Detected: NO" in screen.lbl_cd_changes_detected.text()
        assert "Total Changes: 0" in screen.lbl_cd_total_changes.text()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_change_detection_single_snapshot_safe(qapp):
    import json
    import shutil
    import tempfile
    from pathlib import Path
    from services.portfolio_health_change_detection_service import PortfolioHealthChangeDetectionService
    from services.portfolio_health_history_service import PortfolioHealthHistoryService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        single_file = Path(temp_dir) / "single.json"
        single_file.write_text(json.dumps([{"score": 85, "grade": "B"}]), encoding="utf-8")

        hist_svc = PortfolioHealthHistoryService(storage_path=str(single_file))
        cd_svc = PortfolioHealthChangeDetectionService(history_service=hist_svc)
        screen = PortfolioHealth(change_detection_service=cd_svc, history_service=hist_svc)

        assert "Snapshots Compared: 1" in screen.lbl_cd_snapshots_compared.text()
        assert "Changes Detected: NO" in screen.lbl_cd_changes_detected.text()
        assert "Total Changes: 0" in screen.lbl_cd_total_changes.text()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_timeline_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_tl_entries")
    assert hasattr(screen, "lbl_tl_earliest")
    assert hasattr(screen, "lbl_tl_latest")
    assert hasattr(screen, "timeline_list_container")


def test_timeline_entries_display(qapp):
    from services.portfolio_health_timeline_service import (
        PortfolioHealthTimeline,
        PortfolioHealthTimelineEntry,
    )

    class MockTimelineService:
        def build_timeline(self):
            return PortfolioHealthTimeline(
                total_entries=3,
                latest_timestamp="2026-08-08",
                earliest_timestamp="2026-07-01",
                entries=[
                    PortfolioHealthTimelineEntry(1, "2026-07-01", 80, "B", "STABLE", 0),
                    PortfolioHealthTimelineEntry(2, "2026-07-15", 84, "B", "IMPROVING", 2),
                    PortfolioHealthTimelineEntry(3, "2026-08-08", 91, "A", "IMPROVING", 3),
                ],
            )

    tl_svc = MockTimelineService()
    screen = PortfolioHealth(timeline_service=tl_svc)

    assert "Entries: 3" in screen.lbl_tl_entries.text()
    assert "Earliest: 2026-07-01" in screen.lbl_tl_earliest.text()
    assert "Latest: 2026-08-08" in screen.lbl_tl_latest.text()
    assert screen.timeline_list_container.count() == 3


def test_timeline_empty_timeline_safe(qapp):
    import shutil
    import tempfile
    from pathlib import Path
    from services.portfolio_health_history_service import PortfolioHealthHistoryService
    from services.portfolio_health_timeline_service import PortfolioHealthTimelineService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        empty_file = Path(temp_dir) / "empty.json"
        empty_file.write_text("[]", encoding="utf-8")

        hist_svc = PortfolioHealthHistoryService(storage_path=str(empty_file))
        tl_svc = PortfolioHealthTimelineService(history_service=hist_svc)
        screen = PortfolioHealth(timeline_service=tl_svc, history_service=hist_svc)

        assert "Entries: 0" in screen.lbl_tl_entries.text()
        assert "Earliest: N/A" in screen.lbl_tl_earliest.text()
        assert "Latest: N/A" in screen.lbl_tl_latest.text()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_timeline_single_snapshot_safe(qapp):
    import json
    import shutil
    import tempfile
    from pathlib import Path
    from services.portfolio_health_history_service import PortfolioHealthHistoryService
    from services.portfolio_health_timeline_service import PortfolioHealthTimelineService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        single_file = Path(temp_dir) / "single.json"
        single_file.write_text(json.dumps([{"timestamp": "2026-08-01", "score": 85, "grade": "B"}]), encoding="utf-8")

        hist_svc = PortfolioHealthHistoryService(storage_path=str(single_file))
        tl_svc = PortfolioHealthTimelineService(history_service=hist_svc)
        screen = PortfolioHealth(timeline_service=tl_svc, history_service=hist_svc)

        assert "Entries: 1" in screen.lbl_tl_entries.text()
        assert "Earliest: 2026-08-01" in screen.lbl_tl_earliest.text()
        assert "Latest: 2026-08-01" in screen.lbl_tl_latest.text()
        assert screen.timeline_list_container.count() == 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_monitoring_dashboard_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_mon_dash_status")
    assert hasattr(screen, "lbl_mon_dash_enabled")
    assert hasattr(screen, "lbl_mon_dash_latest_score")
    assert hasattr(screen, "lbl_mon_dash_latest_grade")
    assert hasattr(screen, "lbl_mon_dash_latest_snapshot")
    assert hasattr(screen, "lbl_mon_dash_total_snapshots")
    assert hasattr(screen, "lbl_mon_dash_timeline_entries")
    assert hasattr(screen, "lbl_mon_dash_latest_change_count")
    assert hasattr(screen, "lbl_mon_dash_total_detected_changes")


def test_monitoring_dashboard_values_display(qapp):
    from services.portfolio_health_monitor_dashboard_service import (
        PortfolioHealthMonitoringDashboard,
    )

    class MockDashboardService:
        def build_dashboard(self):
            return PortfolioHealthMonitoringDashboard(
                monitoring_status="READY",
                monitoring_enabled=True,
                latest_score=91,
                latest_grade="A",
                latest_snapshot_time="2026-08-08 09:15",
                total_snapshots=18,
                total_detected_changes=27,
                latest_change_count=3,
                timeline_entries=18,
            )

    dash_svc = MockDashboardService()
    screen = PortfolioHealth(monitoring_dashboard_service=dash_svc)

    assert "Monitoring Status: READY" in screen.lbl_mon_dash_status.text()
    assert "Monitoring Enabled: YES" in screen.lbl_mon_dash_enabled.text()
    assert "Latest Score: 91" in screen.lbl_mon_dash_latest_score.text()
    assert "Latest Grade: A" in screen.lbl_mon_dash_latest_grade.text()
    assert "Latest Snapshot: 2026-08-08 09:15" in screen.lbl_mon_dash_latest_snapshot.text()
    assert "Total Snapshots: 18" in screen.lbl_mon_dash_total_snapshots.text()
    assert "Timeline Entries: 18" in screen.lbl_mon_dash_timeline_entries.text()
    assert "Latest Change Count: 3" in screen.lbl_mon_dash_latest_change_count.text()
    assert "Total Detected Changes: 27" in screen.lbl_mon_dash_total_detected_changes.text()


def test_monitoring_dashboard_empty_dashboard_safe(qapp):
    import shutil
    import tempfile
    from pathlib import Path
    from services.portfolio_health_history_service import PortfolioHealthHistoryService
    from services.portfolio_health_monitor_dashboard_service import PortfolioHealthMonitoringDashboardService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        empty_file = Path(temp_dir) / "empty.json"
        empty_file.write_text("[]", encoding="utf-8")

        hist_svc = PortfolioHealthHistoryService(storage_path=str(empty_file))
        dash_svc = PortfolioHealthMonitoringDashboardService(history_service=hist_svc)
        screen = PortfolioHealth(monitoring_dashboard_service=dash_svc, history_service=hist_svc)

        assert "Monitoring Status: WAITING" in screen.lbl_mon_dash_status.text()
        assert "Monitoring Enabled: YES" in screen.lbl_mon_dash_enabled.text()
        assert "Total Snapshots: 0" in screen.lbl_mon_dash_total_snapshots.text()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_alert_center_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_ac_total")
    assert hasattr(screen, "lbl_ac_active")
    assert hasattr(screen, "lbl_ac_acknowledged")
    assert hasattr(screen, "lbl_ac_dismissed")
    assert hasattr(screen, "alerts_list_container")


def test_alert_values_display(qapp):
    from services.alert_center_service import AlertCenterState, PortfolioAlert

    class MockAlertCenterService:
        def get_state(self):
            return AlertCenterState(
                total_alerts=4,
                active_alerts=2,
                acknowledged_alerts=1,
                dismissed_alerts=1,
                alerts=[
                    PortfolioAlert("1", "2026-08-08", "CONCENTRATION", "HIGH", "Portfolio concentration increased", "Desc 1", "ACTIVE"),
                    PortfolioAlert("2", "2026-08-06", "CASH", "LOW", "Cash allocation changed", "Desc 2", "ACKNOWLEDGED"),
                ],
            )

    ac_svc = MockAlertCenterService()
    screen = PortfolioHealth(alert_center_service=ac_svc)

    assert "Total Alerts: 4" in screen.lbl_ac_total.text()
    assert "Active: 2" in screen.lbl_ac_active.text()
    assert "Acknowledged: 1" in screen.lbl_ac_acknowledged.text()
    assert "Dismissed: 1" in screen.lbl_ac_dismissed.text()
    assert screen.alerts_list_container.count() == 2


def test_empty_alert_center_safe(qapp):
    import shutil
    import tempfile
    from pathlib import Path
    from services.alert_center_service import AlertCenterService

    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        empty_file = Path(temp_dir) / "empty.json"
        empty_file.write_text("[]", encoding="utf-8")

        ac_svc = AlertCenterService(storage_path=str(empty_file))
        screen = PortfolioHealth(alert_center_service=ac_svc)

        assert "Total Alerts: 0" in screen.lbl_ac_total.text()
        assert "Active: 0" in screen.lbl_ac_active.text()
        assert "Acknowledged: 0" in screen.lbl_ac_acknowledged.text()
        assert "Dismissed: 0" in screen.lbl_ac_dismissed.text()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_generated_alerts_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_gen_alerts_count")
    assert hasattr(screen, "generated_alerts_container")


def test_generated_alerts_display(qapp):
    from services.alert_center_service import PortfolioAlert
    from services.alert_generation_service import AlertGenerationResult

    class MockAlertGenerationService:
        def generate_alerts(self, **kwargs):
            return AlertGenerationResult(
                generated_alerts=2,
                alerts=[
                    PortfolioAlert("1", "2026-08-08 10:00", "MONITORING_STATUS", "INFO", "Monitoring ready", "Desc 1", "ACTIVE"),
                    PortfolioAlert("2", "2026-08-08 10:00", "CHANGE_DETECTED", "MEDIUM", "Portfolio changes detected", "Desc 2", "ACTIVE"),
                ],
            )

    gen_svc = MockAlertGenerationService()
    screen = PortfolioHealth(alert_generation_service=gen_svc)

    assert "Generated Alerts: 2" in screen.lbl_gen_alerts_count.text()
    assert screen.generated_alerts_container.count() == 2


def test_empty_generated_alerts_safe(qapp):
    from services.alert_generation_service import AlertGenerationResult, AlertGenerationService

    class MockEmptyGenService:
        def generate_alerts(self, **kwargs):
            return AlertGenerationResult(generated_alerts=0, alerts=[])

    gen_svc = MockEmptyGenService()
    screen = PortfolioHealth(alert_generation_service=gen_svc)

    assert "Generated Alerts: 0" in screen.lbl_gen_alerts_count.text()


def test_alert_rules_section_loads(qapp):
    """Verify Alert Rules section loads on screen."""
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_alert_rules_total")
    assert hasattr(screen, "lbl_alert_rules_triggered")
    assert hasattr(screen, "alert_rules_list_container")


def test_alert_rules_values_display(qapp):
    """Verify Alert Rules values display correctly."""
    from services.alert_rules_service import AlertRule, AlertRulesResult, AlertRulesService

    class MockAlertRulesService:
        def evaluate_rules(self, **kwargs):
            return AlertRulesResult(
                total_rules=5,
                triggered_rules=2,
                rules=[
                    AlertRule("Monitoring Ready", True, "INFO", "MONITORING_STATUS", True, "Monitoring ready."),
                    AlertRule("Monitoring Unavailable", True, "HIGH", "MONITORING_STATUS", False, "Monitoring unavailable."),
                    AlertRule("Portfolio Changes Detected", True, "MEDIUM", "CHANGE_DETECTED", True, "Changes detected."),
                    AlertRule("Timeline Updated", True, "LOW", "TIMELINE_UPDATED", False, "Timeline updated."),
                    AlertRule("Health Score Changed", True, "MEDIUM", "HEALTH_SCORE_CHANGED", False, "Score changed."),
                ],
            )

    rules_svc = MockAlertRulesService()
    screen = PortfolioHealth(alert_rules_service=rules_svc)

    assert "Total Rules: 5" in screen.lbl_alert_rules_total.text()
    assert "Triggered Rules: 2" in screen.lbl_alert_rules_triggered.text()
    assert screen.alert_rules_list_container.count() == 5


def test_empty_alert_rules_safe(qapp):
    """Verify empty Alert Rules displays safely."""
    from services.alert_rules_service import AlertRulesResult, AlertRulesService

    class MockEmptyRulesService:
        def evaluate_rules(self, **kwargs):
            return AlertRulesResult(total_rules=0, triggered_rules=0, rules=[])

    rules_svc = MockEmptyRulesService()
    screen = PortfolioHealth(alert_rules_service=rules_svc)

    assert "Total Rules: 0" in screen.lbl_alert_rules_total.text()
    assert "Triggered Rules: 0" in screen.lbl_alert_rules_triggered.text()















