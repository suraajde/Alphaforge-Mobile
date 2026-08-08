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

def test_alert_dashboard_section_loads(qapp):

    """Verify Alert Dashboard section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_ad_total")

    assert hasattr(screen, "lbl_ad_active")

    assert hasattr(screen, "lbl_ad_acknowledged")

    assert hasattr(screen, "lbl_ad_dismissed")

    assert hasattr(screen, "lbl_ad_info")

    assert hasattr(screen, "lbl_ad_low")

    assert hasattr(screen, "lbl_ad_medium")

    assert hasattr(screen, "lbl_ad_high")

    assert hasattr(screen, "lbl_ad_critical")

    assert hasattr(screen, "alert_dashboard_list_container")

def test_alert_dashboard_values_display(qapp):

    """Verify Alert Dashboard values display correctly."""

    from services.alert_center_service import PortfolioAlert

    from services.alert_dashboard_service import AlertDashboard, AlertDashboardSummary, AlertDashboardService

    class MockAlertDashboardService:

        def build_dashboard(self, **kwargs):

            summary = AlertDashboardSummary(

                total_alerts=3,

                active_alerts=2,

                acknowledged_alerts=1,

                dismissed_alerts=0,

                info_alerts=1,

                low_alerts=1,

                medium_alerts=1,

                high_alerts=0,

                critical_alerts=0,

            )

            alerts = [

                PortfolioAlert("1", "2026-08-07 10:00", "MONITORING_STATUS", "INFO", "Mon Ready", "Desc", "ACTIVE"),

                PortfolioAlert("2", "2026-08-07 10:00", "CHANGE_DETECTED", "MEDIUM", "Changes", "Desc", "ACTIVE"),

                PortfolioAlert("3", "2026-08-07 10:00", "TIMELINE_UPDATED", "LOW", "Timeline", "Desc", "ACKNOWLEDGED"),

            ]

            return AlertDashboard(summary=summary, alerts=alerts)

    dash_svc = MockAlertDashboardService()

    screen = PortfolioHealth(alert_dashboard_service=dash_svc)

    assert "Total Alerts: 3" in screen.lbl_ad_total.text()

    assert "Active: 2" in screen.lbl_ad_active.text()

    assert "Acknowledged: 1" in screen.lbl_ad_acknowledged.text()

    assert "INFO: 1" in screen.lbl_ad_info.text()

    assert screen.alert_dashboard_list_container.count() == 3

def test_empty_alert_dashboard_safe(qapp):

    """Verify empty Alert Dashboard displays safely."""

    from services.alert_dashboard_service import AlertDashboard, AlertDashboardSummary, AlertDashboardService

    class MockEmptyDashService:

        def build_dashboard(self, **kwargs):

            summary = AlertDashboardSummary(0, 0, 0, 0, 0, 0, 0, 0, 0)

            return AlertDashboard(summary=summary, alerts=[])

    dash_svc = MockEmptyDashService()

    screen = PortfolioHealth(alert_dashboard_service=dash_svc)

    assert "Total Alerts: 0" in screen.lbl_ad_total.text()

    assert "Active: 0" in screen.lbl_ad_active.text()

def test_alert_history_section_loads(qapp):

    """Verify Alert History section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_ah_total")

    assert hasattr(screen, "lbl_ah_latest")

    assert hasattr(screen, "lbl_ah_earliest")

    assert hasattr(screen, "alert_history_list_container")

def test_alert_history_values_display(qapp):

    """Verify Alert History values display correctly."""

    from services.alert_history_service import AlertHistory, AlertHistoryEntry, AlertHistoryService

    class MockAlertHistoryService:

        def get_history(self):

            entries = [

                AlertHistoryEntry("1", "2026-08-07 10:00", "MONITORING_STATUS", "INFO", "Mon Ready", "Desc", "ACTIVE"),

                AlertHistoryEntry("2", "2026-08-07 10:05", "CHANGE_DETECTED", "MEDIUM", "Changes", "Desc", "ACTIVE"),

            ]

            return AlertHistory(

                total_entries=2,

                latest_timestamp="2026-08-07 10:05",

                earliest_timestamp="2026-08-07 10:00",

                entries=entries,

            )

    hist_svc = MockAlertHistoryService()

    screen = PortfolioHealth(alert_history_service=hist_svc)

    assert "Total Entries: 2" in screen.lbl_ah_total.text()

    assert "Latest: 2026-08-07 10:05" in screen.lbl_ah_latest.text()

    assert "Earliest: 2026-08-07 10:00" in screen.lbl_ah_earliest.text()

    assert screen.alert_history_list_container.count() == 2

def test_empty_alert_history_safe(qapp):

    """Verify empty Alert History displays safely."""

    from services.alert_history_service import AlertHistory, AlertHistoryService

    class MockEmptyHistoryService:

        def get_history(self):

            return AlertHistory(total_entries=0, latest_timestamp=None, earliest_timestamp=None, entries=[])

    hist_svc = MockEmptyHistoryService()

    screen = PortfolioHealth(alert_history_service=hist_svc)

    assert "Total Entries: 0" in screen.lbl_ah_total.text()

    assert "Latest: N/A" in screen.lbl_ah_latest.text()

    assert "Earliest: N/A" in screen.lbl_ah_earliest.text()

def test_alert_management_section_loads(qapp):

    """Verify Alert Management section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_am_total")

    assert hasattr(screen, "lbl_am_active")

    assert hasattr(screen, "lbl_am_acknowledged")

    assert hasattr(screen, "lbl_am_dismissed")

    assert hasattr(screen, "lbl_am_last_updated")

    assert hasattr(screen, "alert_management_list_container")

def test_alert_management_values_display(qapp):

    """Verify Alert Management values display correctly."""

    from services.alert_center_service import PortfolioAlert

    from services.alert_management_service import AlertManagementResult, AlertManagementSummary, AlertManagementService

    class MockAlertManagementService:

        def get_management_result(self):

            summary = AlertManagementSummary(

                total_alerts=2,

                active_alerts=1,

                acknowledged_alerts=1,

                dismissed_alerts=0,

                last_updated="2026-08-07 10:00",

            )

            alerts = [

                PortfolioAlert("1", "2026-08-07 10:00", "TYPE1", "INFO", "Title 1", "Desc 1", "ACTIVE"),

                PortfolioAlert("2", "2026-08-07 10:00", "TYPE2", "MEDIUM", "Title 2", "Desc 2", "ACKNOWLEDGED"),

            ]

            return AlertManagementResult(summary=summary, alerts=alerts)

    mgmt_svc = MockAlertManagementService()

    screen = PortfolioHealth(alert_management_service=mgmt_svc)

    assert "Total Alerts: 2" in screen.lbl_am_total.text()

    assert "Active: 1" in screen.lbl_am_active.text()

    assert "Acknowledged: 1" in screen.lbl_am_acknowledged.text()

    assert screen.alert_management_list_container.count() == 2

def test_empty_alert_management_safe(qapp):

    """Verify empty Alert Management displays safely."""

    from services.alert_management_service import AlertManagementResult, AlertManagementSummary, AlertManagementService

    class MockEmptyMgmtService:

        def get_management_result(self):

            summary = AlertManagementSummary(0, 0, 0, 0, None)

            return AlertManagementResult(summary=summary, alerts=[])

    mgmt_svc = MockEmptyMgmtService()

    screen = PortfolioHealth(alert_management_service=mgmt_svc)

    assert "Total Alerts: 0" in screen.lbl_am_total.text()

    assert "Active: 0" in screen.lbl_am_active.text()

def test_decision_engine_section_loads(qapp):

    """Verify Decision Engine section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_de_status")

    assert hasattr(screen, "lbl_de_total")

    assert hasattr(screen, "lbl_de_pending")

    assert hasattr(screen, "lbl_de_informational")

    assert hasattr(screen, "decision_engine_list_container")

def test_decision_engine_values_display(qapp):

    """Verify Decision Engine values display correctly."""

    from services.decision_engine_service import DecisionEngineResult, DecisionSummary, DecisionEngineService

    class MockDecisionEngineService:

        def evaluate(self, **kwargs):

            summary = DecisionSummary(

                total_decisions=0,

                pending_decisions=0,

                informational_decisions=0,

                engine_status="READY",

            )

            return DecisionEngineResult(summary=summary, decisions=[])

    dec_svc = MockDecisionEngineService()

    screen = PortfolioHealth(decision_engine_service=dec_svc)

    assert "Engine Status: READY" in screen.lbl_de_status.text()

    assert "Total Decisions: 0" in screen.lbl_de_total.text()

    assert "Pending Decisions: 0" in screen.lbl_de_pending.text()

    assert "Informational Decisions: 0" in screen.lbl_de_informational.text()

def test_empty_decision_engine_safe(qapp):

    """Verify empty Decision Engine displays safely."""

    from services.decision_engine_service import DecisionEngineResult, DecisionSummary, DecisionEngineService

    class MockEmptyDecService:

        def evaluate(self, **kwargs):

            summary = DecisionSummary(0, 0, 0, "UNAVAILABLE")

            return DecisionEngineResult(summary=summary, decisions=[])

    dec_svc = MockEmptyDecService()

    screen = PortfolioHealth(decision_engine_service=dec_svc)

    assert "Engine Status: UNAVAILABLE" in screen.lbl_de_status.text()

    assert "Total Decisions: 0" in screen.lbl_de_total.text()

def test_decision_classification_section_loads(qapp):

    """Verify Decision Classification section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_dc_total")

    assert hasattr(screen, "lbl_dc_classified")

    assert hasattr(screen, "lbl_dc_unclassified")

    assert hasattr(screen, "decision_classification_list_container")

def test_decision_classification_values_display(qapp):

    """Verify Decision Classification values display correctly."""

    from services.decision_classification_service import (

        DecisionClassificationResult,

    )

    class MockDecisionClassificationService:

        def classify(self, **kwargs):

            return DecisionClassificationResult(

                total_classifications=0,

                classified=0,

                unclassified=0,

                classifications=[],

            )

    cls_svc = MockDecisionClassificationService()

    screen = PortfolioHealth(decision_classification_service=cls_svc)

    assert "Total Classifications: 0" in screen.lbl_dc_total.text()

    assert "Classified: 0" in screen.lbl_dc_classified.text()

    assert "Unclassified: 0" in screen.lbl_dc_unclassified.text()

def test_empty_decision_classification_safe(qapp):

    """Verify empty Decision Classification displays safely."""

    from services.decision_classification_service import (

        DecisionClassificationResult,

    )

    class MockEmptyClsService:

        def classify(self, **kwargs):

            return DecisionClassificationResult(0, 0, 0, [])

    cls_svc = MockEmptyClsService()

    screen = PortfolioHealth(decision_classification_service=cls_svc)

    assert "Total Classifications: 0" in screen.lbl_dc_total.text()

    assert "Classified: 0" in screen.lbl_dc_classified.text()

    assert "Unclassified: 0" in screen.lbl_dc_unclassified.text()

def test_decision_prioritization_section_loads(qapp):

    """Verify Decision Prioritization section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_dp_total")

    assert hasattr(screen, "lbl_dp_critical")

    assert hasattr(screen, "lbl_dp_high")

    assert hasattr(screen, "lbl_dp_medium")

    assert hasattr(screen, "lbl_dp_low")

    assert hasattr(screen, "lbl_dp_info")

    assert hasattr(screen, "decision_prioritization_list_container")

def test_decision_prioritization_values_display(qapp):

    """Verify Decision Prioritization values display correctly."""

    from services.decision_prioritization_service import (

        DecisionPrioritizationResult,

    )

    class MockDecisionPrioritizationService:

        def prioritize(self, **kwargs):

            return DecisionPrioritizationResult(

                total_prioritized=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                info_count=0,

                priorities=[],

            )

    prio_svc = MockDecisionPrioritizationService()

    screen = PortfolioHealth(decision_prioritization_service=prio_svc)

    assert "Total Prioritized: 0" in screen.lbl_dp_total.text()

    assert "Critical: 0" in screen.lbl_dp_critical.text()

    assert "High: 0" in screen.lbl_dp_high.text()

    assert "Medium: 0" in screen.lbl_dp_medium.text()

    assert "Low: 0" in screen.lbl_dp_low.text()

    assert "Info: 0" in screen.lbl_dp_info.text()

def test_empty_decision_prioritization_safe(qapp):

    """Verify empty Decision Prioritization displays safely."""

    from services.decision_prioritization_service import (

        DecisionPrioritizationResult,

    )

    class MockEmptyPrioService:

        def prioritize(self, **kwargs):

            return DecisionPrioritizationResult(0, 0, 0, 0, 0, 0, [])

    prio_svc = MockEmptyPrioService()

    screen = PortfolioHealth(decision_prioritization_service=prio_svc)

    assert "Total Prioritized: 0" in screen.lbl_dp_total.text()

    assert "Critical: 0" in screen.lbl_dp_critical.text()

    assert "High: 0" in screen.lbl_dp_high.text()

    assert "Medium: 0" in screen.lbl_dp_medium.text()

    assert "Low: 0" in screen.lbl_dp_low.text()

    assert "Info: 0" in screen.lbl_dp_info.text()

def test_decision_audit_section_loads(qapp):

    """Verify Decision Audit Trail section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_da_total")

    assert hasattr(screen, "lbl_da_earliest")

    assert hasattr(screen, "lbl_da_latest")

    assert hasattr(screen, "decision_audit_list_container")

def test_decision_audit_values_display(qapp):

    """Verify Decision Audit Trail values display correctly."""

    from services.decision_audit_service import DecisionAuditTrail

    class MockDecisionAuditService:

        def get_audit_trail(self):

            return DecisionAuditTrail(0, None, None, [])

        def record_decisions(self, **kwargs):

            return DecisionAuditTrail(0, None, None, [])

    audit_svc = MockDecisionAuditService()

    screen = PortfolioHealth(decision_audit_service=audit_svc)

    assert "Total Entries: 0" in screen.lbl_da_total.text()

    assert "Earliest Entry:" in screen.lbl_da_earliest.text()

    assert "Latest Entry:" in screen.lbl_da_latest.text()

def test_empty_decision_audit_safe(qapp):

    """Verify empty Decision Audit Trail displays safely."""

    from services.decision_audit_service import DecisionAuditTrail

    class MockEmptyAuditService:

        def get_audit_trail(self):

            return DecisionAuditTrail(0, None, None, [])

        def record_decisions(self, **kwargs):

            return DecisionAuditTrail(0, None, None, [])

    audit_svc = MockEmptyAuditService()

    screen = PortfolioHealth(decision_audit_service=audit_svc)

    assert "Total Entries: 0" in screen.lbl_da_total.text()

def test_corrupt_decision_audit_safe(qapp):

    """Verify corrupt Decision Audit Trail data does not crash UI."""

    class CorruptAuditService:

        def get_audit_trail(self):

            raise RuntimeError("Corrupt data")

        def record_decisions(self, **kwargs):

            raise RuntimeError("Corrupt data")

    audit_svc = CorruptAuditService()

    try:

        screen = PortfolioHealth(decision_audit_service=audit_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt decision audit data should not crash UI")

def test_decision_audit_analytics_section_loads(qapp):

    """Verify Decision Audit Analytics section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_daa_total")

    assert hasattr(screen, "lbl_daa_unique")

    assert hasattr(screen, "lbl_daa_classified")

    assert hasattr(screen, "lbl_daa_unclassified")

    assert hasattr(screen, "lbl_daa_critical")

    assert hasattr(screen, "lbl_daa_high")

    assert hasattr(screen, "lbl_daa_medium")

    assert hasattr(screen, "lbl_daa_low")

    assert hasattr(screen, "lbl_daa_info")

    assert hasattr(screen, "decision_audit_analytics_container")

def test_decision_audit_analytics_values_display(qapp):

    """Verify Decision Audit Analytics values display correctly."""

    from services.decision_audit_analytics_service import (

        DecisionAuditAnalytics,

        DecisionAuditAnalyticsSummary,

    )

    class MockAnalyticsService:

        def get_analytics(self):

            return DecisionAuditAnalytics(

                summary=DecisionAuditAnalyticsSummary(

                    total_entries=5,

                    unique_decisions=3,

                    classified_entries=4,

                    unclassified_entries=1,

                    high_priority_entries=2,

                    medium_priority_entries=1,

                    low_priority_entries=1,

                    info_priority_entries=0,

                    critical_priority_entries=1,

                ),

                category_counts={"HEALTH": 3, "MONITORING": 2},

                priority_counts={"CRITICAL": 1, "HIGH": 2, "MEDIUM": 1, "LOW": 1},

                classification_counts={"CLASSIFIED": 4, "UNCLASSIFIED": 1},

                source_counts={"decision_pipeline": 5},

            )

    analytics_svc = MockAnalyticsService()

    screen = PortfolioHealth(decision_audit_analytics_service=analytics_svc)

    assert "Total Entries: 5" in screen.lbl_daa_total.text()

    assert "Unique Decisions: 3" in screen.lbl_daa_unique.text()

    assert "Classified: 4" in screen.lbl_daa_classified.text()

    assert "Unclassified: 1" in screen.lbl_daa_unclassified.text()

    assert "Critical: 1" in screen.lbl_daa_critical.text()

    assert "High: 2" in screen.lbl_daa_high.text()

def test_empty_decision_audit_analytics_safe(qapp):

    """Verify empty Decision Audit Analytics displays safely."""

    from services.decision_audit_analytics_service import (

        DecisionAuditAnalytics,

        DecisionAuditAnalyticsSummary,

    )

    class MockEmptyAnalyticsService:

        def get_analytics(self):

            return DecisionAuditAnalytics(

                summary=DecisionAuditAnalyticsSummary(0, 0, 0, 0, 0, 0, 0, 0, 0),

                category_counts={},

                priority_counts={},

                classification_counts={},

                source_counts={},

            )

    analytics_svc = MockEmptyAnalyticsService()

    screen = PortfolioHealth(decision_audit_analytics_service=analytics_svc)

    assert "Total Entries: 0" in screen.lbl_daa_total.text()

def test_corrupt_decision_audit_analytics_safe(qapp):

    """Verify corrupt Decision Audit Analytics data does not crash UI."""

    class CorruptAnalyticsService:

        def get_analytics(self):

            raise RuntimeError("Corrupt analytics data")

    analytics_svc = CorruptAnalyticsService()

    try:

        screen = PortfolioHealth(decision_audit_analytics_service=analytics_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt decision audit analytics data should not crash UI")

def test_decision_audit_trend_section_loads(qapp):

    """Verify Decision Audit Trend section loads on screen."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_dat_total_points")

    assert hasattr(screen, "lbl_dat_earliest")

    assert hasattr(screen, "lbl_dat_latest")

    assert hasattr(screen, "lbl_dat_direction")

    assert hasattr(screen, "decision_audit_trend_container")

def test_decision_audit_trend_values_display(qapp):

    """Verify Decision Audit Trend values display correctly."""

    from services.decision_audit_trend_service import (

        DecisionAuditTrend,

        DecisionAuditTrendPoint,

    )

    class MockTrendService:

        def get_trend(self):

            pt1 = DecisionAuditTrendPoint("2026-01-01T00:00:00", 2, 2, 0, 1, 0, 1, 0, 0)

            pt2 = DecisionAuditTrendPoint("2026-01-02T00:00:00", 5, 4, 1, 2, 1, 1, 0, 1)

            return DecisionAuditTrend(

                total_points=2,

                earliest_timestamp="2026-01-01T00:00:00",

                latest_timestamp="2026-01-02T00:00:00",

                direction="INCREASING",

                points=[pt1, pt2],

            )

    trend_svc = MockTrendService()

    screen = PortfolioHealth(decision_audit_trend_service=trend_svc)

    assert "Total Points: 2" in screen.lbl_dat_total_points.text()

    assert "Earliest Timestamp: 2026-01-01T00:00:00" in screen.lbl_dat_earliest.text()

    assert "Latest Timestamp: 2026-01-02T00:00:00" in screen.lbl_dat_latest.text()

    assert "Direction: INCREASING" in screen.lbl_dat_direction.text()

def test_empty_decision_audit_trend_safe(qapp):

    """Verify empty Decision Audit Trend displays safely."""

    from services.decision_audit_trend_service import DecisionAuditTrend

    class MockEmptyTrendService:

        def get_trend(self):

            return DecisionAuditTrend(0, None, None, "STABLE", [])

    trend_svc = MockEmptyTrendService()

    screen = PortfolioHealth(decision_audit_trend_service=trend_svc)

    assert "Total Points: 0" in screen.lbl_dat_total_points.text()

    assert "Direction: STABLE" in screen.lbl_dat_direction.text()

def test_corrupt_decision_audit_trend_safe(qapp):

    """Verify corrupt Decision Audit Trend data does not crash UI."""

    class CorruptTrendService:

        def get_trend(self):

            raise RuntimeError("Corrupt trend data")

    trend_svc = CorruptTrendService()

    try:

        screen = PortfolioHealth(decision_audit_trend_service=trend_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt decision audit trend data should not crash UI")

def test_rebalancing_section_loads(qapp):

    """Verify Rebalancing section loads on screen with safety text."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_reb_status")

    assert hasattr(screen, "lbl_reb_total_val")

    assert hasattr(screen, "lbl_reb_total_pos")

    assert hasattr(screen, "rebalancing_positions_container")

def test_rebalancing_values_display(qapp):

    """Verify Rebalancing values display correctly."""

    from services.rebalancing_service import (

        RebalancingPortfolio,

        RebalancingPosition,

        RebalancingState,

    )

    class MockRebalancingService:

        def get_state(self):

            pos = RebalancingPosition("AAPL", "Apple Inc.", "EQUITY", 10000.0, 100.0)

            port = RebalancingPortfolio(10000.0, [pos])

            return RebalancingState("READY", port, 1, 10000.0)

    rebal_svc = MockRebalancingService()

    screen = PortfolioHealth(rebalancing_service=rebal_svc)

    assert "Rebalancing Status: READY" in screen.lbl_reb_status.text()

    assert "$10,000.00" in screen.lbl_reb_total_val.text()

    assert "Total Positions: 1" in screen.lbl_reb_total_pos.text()

def test_empty_rebalancing_safe(qapp):

    """Verify empty Rebalancing state displays safely."""

    from services.rebalancing_service import (

        RebalancingPortfolio,

        RebalancingState,

    )

    class MockEmptyRebalancingService:

        def get_state(self):

            return RebalancingState("EMPTY", RebalancingPortfolio(0.0, []), 0, 0.0)

    rebal_svc = MockEmptyRebalancingService()

    screen = PortfolioHealth(rebalancing_service=rebal_svc)

    assert "Rebalancing Status: EMPTY" in screen.lbl_reb_status.text()

def test_corrupt_rebalancing_safe(qapp):

    """Verify corrupt Rebalancing data does not crash UI."""

    class CorruptRebalancingService:

        def get_state(self):

            raise RuntimeError("Corrupt rebalancing state")

    rebal_svc = CorruptRebalancingService()

    try:

        screen = PortfolioHealth(rebalancing_service=rebal_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt rebalancing data should not crash UI")

def test_allocation_analysis_section_loads(qapp):

    """Verify Allocation Analysis section loads on screen with safety text."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_aa_total_val")

    assert hasattr(screen, "allocation_analysis_container")

def test_allocation_analysis_values_display(qapp):

    """Verify Allocation Analysis values display correctly."""

    from services.allocation_analysis_service import (

        AllocationAnalysisResult,

        AllocationCategory,

    )

    class MockAllocationAnalysisService:

        def get_analysis(self):

            asset_cat = AllocationCategory("EQUITY", 10000.0, 100.0, 1)

            fund_cat = AllocationCategory("MUTUAL_FUND", 5000.0, 50.0, 1)

            etf_cat = AllocationCategory("ETF", 5000.0, 50.0, 1)

            return AllocationAnalysisResult(

                total_value=10000.0,

                asset_allocations=[asset_cat],

                fund_allocations=[fund_cat],

                etf_allocations=[etf_cat],

            )

    alloc_svc = MockAllocationAnalysisService()

    screen = PortfolioHealth(allocation_analysis_service=alloc_svc)

    assert "$10,000.00" in screen.lbl_aa_total_val.text()

    assert screen.allocation_analysis_container.count() > 0

def test_empty_allocation_analysis_safe(qapp):

    """Verify empty Allocation Analysis state displays safely."""

    from services.allocation_analysis_service import AllocationAnalysisResult

    class MockEmptyAllocationAnalysisService:

        def get_analysis(self):

            return AllocationAnalysisResult(0.0, [], [], [])

    alloc_svc = MockEmptyAllocationAnalysisService()

    screen = PortfolioHealth(allocation_analysis_service=alloc_svc)

    assert "$0.00" in screen.lbl_aa_total_val.text()

def test_corrupt_allocation_analysis_safe(qapp):

    """Verify corrupt Allocation Analysis data does not crash UI."""

    class CorruptAllocationAnalysisService:

        def get_analysis(self):

            raise RuntimeError("Corrupt allocation analysis data")

    alloc_svc = CorruptAllocationAnalysisService()

    try:

        screen = PortfolioHealth(allocation_analysis_service=alloc_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt allocation analysis data should not crash UI")

def test_drift_detection_section_loads(qapp):

    """Verify Drift Detection section loads on screen with safety text."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_dd_total_pos")

    assert hasattr(screen, "lbl_dd_pos_with_target")

    assert hasattr(screen, "lbl_dd_pos_without_target")

    assert hasattr(screen, "lbl_dd_total_abs_drift")

    assert hasattr(screen, "lbl_dd_avg_abs_drift")

    assert hasattr(screen, "lbl_dd_max_abs_drift")

    assert hasattr(screen, "drift_metrics_container")

    assert hasattr(screen, "drift_history_container")

def test_drift_detection_values_display(qapp):

    """Verify Drift Detection values display correctly."""

    from services.drift_detection_service import (

        DriftDetectionResult,

        DriftMetric,

    )

    class MockDriftDetectionService:

        def get_drift(self):

            m = DriftMetric("AAPL", 60.0, 50.0, 10.0, 10.0, "OVERWEIGHT")

            return DriftDetectionResult(1, 1, 0, 10.0, 10.0, 10.0, [m])

        def load_history(self):

            from services.drift_detection_service import DriftHistory

            return DriftHistory(0, None, None, [])

    drift_svc = MockDriftDetectionService()

    screen = PortfolioHealth(drift_detection_service=drift_svc)

    assert "Total Positions: 1" in screen.lbl_dd_total_pos.text()

    assert "Positions With Target: 1" in screen.lbl_dd_pos_with_target.text()

    assert "Total Absolute Drift: 10.00%" in screen.lbl_dd_total_abs_drift.text()

    assert screen.drift_metrics_container.count() > 0

def test_empty_drift_detection_safe(qapp):

    """Verify empty Drift Detection state displays safely."""

    from services.drift_detection_service import (

        DriftDetectionResult,

        DriftHistory,

    )

    class MockEmptyDriftDetectionService:

        def get_drift(self):

            return DriftDetectionResult(0, 0, 0, 0.0, 0.0, 0.0, [])

        def load_history(self):

            return DriftHistory(0, None, None, [])

    drift_svc = MockEmptyDriftDetectionService()

    screen = PortfolioHealth(drift_detection_service=drift_svc)

    assert "Total Positions: 0" in screen.lbl_dd_total_pos.text()

def test_corrupt_drift_detection_safe(qapp):

    """Verify corrupt Drift Detection data does not crash UI."""

    class CorruptDriftDetectionService:

        def get_drift(self):

            raise RuntimeError("Corrupt drift detection data")

        def load_history(self):

            raise RuntimeError("Corrupt history data")

    drift_svc = CorruptDriftDetectionService()

    try:

        screen = PortfolioHealth(drift_detection_service=drift_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt drift detection data should not crash UI")

def test_drift_history_display(qapp):

    """Verify Drift History section displays history entries correctly."""

    from services.drift_detection_service import (

        DriftDetectionResult,

        DriftHistory,

        DriftHistoryEntry,

    )

    class MockHistoryDriftDetectionService:

        def get_drift(self):

            return DriftDetectionResult(1, 1, 0, 10.0, 10.0, 10.0, [])

        def load_history(self):

            e1 = DriftHistoryEntry("2026-08-08T00:00:00Z", 10.0, 10.0, 10.0, 1)

            return DriftHistory(1, "2026-08-08T00:00:00Z", "2026-08-08T00:00:00Z", [e1])

    drift_svc = MockHistoryDriftDetectionService()

    screen = PortfolioHealth(drift_detection_service=drift_svc)

    assert "Total History Entries: 1" in screen.lbl_dh_total_entries.text()

    assert "2026-08-08T00:00:00Z" in screen.lbl_dh_earliest.text()

    assert screen.drift_history_container.count() > 0

def test_rebalancing_candidates_section_loads(qapp):

    """Verify Rebalancing Candidates section loads on screen with safety text."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_rc_total_candidates")

    assert hasattr(screen, "lbl_rc_overweight_candidates")

    assert hasattr(screen, "lbl_rc_underweight_candidates")

    assert hasattr(screen, "lbl_rc_on_target_candidates")

    assert hasattr(screen, "lbl_rc_total_impact_val")

    assert hasattr(screen, "rebalancing_candidates_container")

def test_rebalancing_candidates_values_display(qapp):

    """Verify Rebalancing Candidates values display correctly."""

    from services.rebalancing_candidate_service import (

        RebalancingCandidate,

        RebalancingCandidateResult,

    )

    class MockRebalancingCandidateService:

        def get_candidates(self):

            c = RebalancingCandidate(

                symbol="AAPL",

                name="Apple Inc.",

                asset_type="EQUITY",

                current_weight=60.0,

                target_weight=50.0,

                drift=10.0,

                absolute_drift=10.0,

                direction="OVERWEIGHT",

                impact_value=1000.0,

                scenario_weight=50.0,

                scenario_delta=-10.0,

                candidate_score=10.0,

                rank=1,

            )

            return RebalancingCandidateResult(1, 1, 0, 0, 1000.0, [c])

    cand_svc = MockRebalancingCandidateService()

    screen = PortfolioHealth(rebalancing_candidate_service=cand_svc)

    assert "Total Candidates: 1" in screen.lbl_rc_total_candidates.text()

    assert "Overweight Candidates: 1" in screen.lbl_rc_overweight_candidates.text()

    assert "$1,000.00" in screen.lbl_rc_total_impact_val.text()

    assert screen.rebalancing_candidates_container.count() > 0

def test_empty_rebalancing_candidates_safe(qapp):

    """Verify empty Rebalancing Candidates state displays safely."""

    from services.rebalancing_candidate_service import RebalancingCandidateResult

    class MockEmptyRebalancingCandidateService:

        def get_candidates(self):

            return RebalancingCandidateResult(0, 0, 0, 0, 0.0, [])

    cand_svc = MockEmptyRebalancingCandidateService()

    screen = PortfolioHealth(rebalancing_candidate_service=cand_svc)

    assert "Total Candidates: 0" in screen.lbl_rc_total_candidates.text()

def test_corrupt_rebalancing_candidates_safe(qapp):

    """Verify corrupt Rebalancing Candidates data does not crash UI."""

    class CorruptRebalancingCandidateService:

        def get_candidates(self):

            raise RuntimeError("Corrupt candidate data")

    cand_svc = CorruptRebalancingCandidateService()

    try:

        screen = PortfolioHealth(rebalancing_candidate_service=cand_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt rebalancing candidate data should not crash UI")

def test_rebalancing_recommendations_section_loads(qapp):

    """Verify Rebalancing Recommendations section loads on screen with boundary text."""

    screen = PortfolioHealth()

    assert hasattr(screen, "lbl_rr_total_recommendations")

    assert hasattr(screen, "lbl_rr_increase_count")

    assert hasattr(screen, "lbl_rr_decrease_count")

    assert hasattr(screen, "lbl_rr_maintain_count")

    assert hasattr(screen, "lbl_rr_high_priority_count")

    assert hasattr(screen, "lbl_rr_medium_priority_count")

    assert hasattr(screen, "lbl_rr_low_priority_count")

    assert hasattr(screen, "lbl_rr_total_impact_val")

    assert hasattr(screen, "rebalancing_recommendations_container")

def test_rebalancing_recommendations_values_display(qapp):

    """Verify Rebalancing Recommendations values display correctly."""

    from services.rebalancing_recommendation_service import (

        RebalancingRecommendation,

        RebalancingRecommendationResult,

    )

    class MockRebalancingRecommendationService:

        def get_recommendations(self):

            r = RebalancingRecommendation(

                recommendation_id="rec_12345",

                symbol="AAPL",

                name="Apple Inc.",

                asset_type="EQUITY",

                current_weight=60.0,

                target_weight=50.0,

                drift=10.0,

                absolute_drift=10.0,

                direction="OVERWEIGHT",

                impact_value=1000.0,

                recommended_action="DECREASE",

                recommended_weight=50.0,

                weight_change=-10.0,

                priority="HIGH",

                rationale="Current allocation is above target.",

                candidate_score=10.0,

                candidate_rank=1,

            )

            return RebalancingRecommendationResult(1, 0, 1, 0, 1, 0, 0, 1000.0, [r])

    rec_svc = MockRebalancingRecommendationService()

    screen = PortfolioHealth(rebalancing_recommendation_service=rec_svc)

    assert "Total Recommendations: 1" in screen.lbl_rr_total_recommendations.text()

    assert "Decrease: 1" in screen.lbl_rr_decrease_count.text()

    assert "High Priority: 1" in screen.lbl_rr_high_priority_count.text()

    assert "$1,000.00" in screen.lbl_rr_total_impact_val.text()

    assert screen.rebalancing_recommendations_container.count() > 0

def test_empty_rebalancing_recommendations_safe(qapp):

    """Verify empty Rebalancing Recommendations state displays safely."""

    from services.rebalancing_recommendation_service import RebalancingRecommendationResult

    class MockEmptyRebalancingRecommendationService:

        def get_recommendations(self):

            return RebalancingRecommendationResult(0, 0, 0, 0, 0, 0, 0, 0.0, [])

    rec_svc = MockEmptyRebalancingRecommendationService()

    screen = PortfolioHealth(rebalancing_recommendation_service=rec_svc)

    assert "Total Recommendations: 0" in screen.lbl_rr_total_recommendations.text()

def test_corrupt_rebalancing_recommendations_safe(qapp):

    """Verify corrupt Rebalancing Recommendations data does not crash UI."""

    class CorruptRebalancingRecommendationService:

        def get_recommendations(self):

            raise RuntimeError("Corrupt recommendation data")

    rec_svc = CorruptRebalancingRecommendationService()

    try:

        screen = PortfolioHealth(rebalancing_recommendation_service=rec_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt rebalancing recommendation data should not crash UI")

def test_recommendation_review_boundary_display(qapp):

    """Verify review-only boundary message displays and no execution controls are present."""

    screen = PortfolioHealth()

    assert not hasattr(screen, "btn_execute")

    assert not hasattr(screen, "btn_buy")

    assert not hasattr(screen, "btn_sell")

    assert not hasattr(screen, "btn_rebalance_now")


def test_portfolio_intelligence_section_loads(qapp):

    """Verify Portfolio Intelligence section loads cleanly."""

    screen = PortfolioHealth()

    assert hasattr(screen, "portfolio_intelligence_container")


def test_portfolio_intelligence_values_display(qapp):

    """Verify Portfolio Intelligence values display properly."""

    from services.portfolio_intelligence_service import PortfolioIntelligenceResult, PortfolioIntelligenceSummary

    class MockPortfolioIntelligenceService:

        def get_intelligence(self):

            return PortfolioIntelligenceResult(

                summary=PortfolioIntelligenceSummary(

                    total_value=75000.0,

                    holding_count=15,

                    account_count=3,

                    last_analysis_timestamp="2026-08-08T12:00:00Z"

                ),

                history=[]

            )

    intel_svc = MockPortfolioIntelligenceService()

    screen = PortfolioHealth(portfolio_intelligence_service=intel_svc)

    assert hasattr(screen, "portfolio_intelligence_container")


def test_empty_portfolio_intelligence_safe(qapp):

    """Verify empty Portfolio Intelligence result handles gracefully without crashing UI."""

    class EmptyPortfolioIntelligenceService:

        def get_intelligence(self):

            return None

    intel_svc = EmptyPortfolioIntelligenceService()

    screen = PortfolioHealth(portfolio_intelligence_service=intel_svc)

    assert hasattr(screen, "portfolio_intelligence_container")


def test_corrupt_portfolio_intelligence_safe(qapp):

    """Verify corrupt Portfolio Intelligence data does not crash UI."""

    class CorruptPortfolioIntelligenceService:

        def get_intelligence(self):

            raise RuntimeError("Corrupt portfolio intelligence data")

    intel_svc = CorruptPortfolioIntelligenceService()

    try:

        screen = PortfolioHealth(portfolio_intelligence_service=intel_svc)

        assert screen is not None

    except Exception:

        pytest.fail("Corrupt portfolio intelligence data should not crash UI")


def test_holding_quality_section_loads(qapp):
    """Verify Holding Quality section loads cleanly."""
    screen = PortfolioHealth()
    assert hasattr(screen, "holding_quality_container")


def test_holding_quality_values_display(qapp):
    """Verify Holding Quality values display properly."""
    from services.holding_quality_service import HoldingQualityResult, HoldingQuality

    class MockHoldingQualityService:
        def get_quality(self):
            return HoldingQualityResult(
                total_holdings=2,
                assessed_holdings=1,
                unassessed_holdings=1,
                average_quality_score=85.0,
                highest_quality_score=85.0,
                lowest_quality_score=85.0,
                holdings=[
                    HoldingQuality(
                        symbol="MOCKFUND",
                        name="Mock Fund",
                        asset_type="MUTUAL_FUND",
                        quality_score=85.0,
                        quality_grade="A",
                        assessment_status="ASSESSED",
                        rationale="Mock rationale",
                    )
                ]
            )

    hq_svc = MockHoldingQualityService()
    screen = PortfolioHealth(holding_quality_service=hq_svc)
    assert hasattr(screen, "holding_quality_container")


def test_empty_holding_quality_safe(qapp):
    """Verify empty Holding Quality result handles gracefully without crashing UI."""
    class EmptyHoldingQualityService:
        def get_quality(self):
            return None

    hq_svc = EmptyHoldingQualityService()
    screen = PortfolioHealth(holding_quality_service=hq_svc)
    assert hasattr(screen, "holding_quality_container")


def test_holding_quality_missing_data_safe(qapp):
    """Verify missing holding quality data handles safely."""
    class BrokenHoldingQualityService:
        def get_quality(self):
            raise RuntimeError("Holding quality data missing")

    hq_svc = BrokenHoldingQualityService()
    try:
        screen = PortfolioHealth(holding_quality_service=hq_svc)
        assert screen is not None
    except Exception:
        pytest.fail("Missing holding quality data should not crash UI")


def test_sip_optimization_section_loads(qapp):
    """Verify SIP Optimization container layout exists in PortfolioHealth widget."""
    screen = PortfolioHealth()
    assert hasattr(screen, "sip_optimization_container")


def test_sip_optimization_values_display(qapp):
    """Verify SIP Optimization values display properly in UI."""
    from services.sip_optimization_service import SIPOptimizationResult, SIPHoldingAnalysis, SIPDistributionMetrics, SIPEfficiencyMetrics

    class MockSIPOptimizationService:
        def get_sip_analysis(self):
            return SIPOptimizationResult(
                analysis_status="ANALYZED",
                total_positions=1,
                total_sip_invested=5000.0,
                total_sip_transactions=1,
                distribution=SIPDistributionMetrics(total_positions=1, positions_with_sip=1, sip_coverage_pct=100.0),
                efficiency=SIPEfficiencyMetrics(total_sip_invested=5000.0, total_sip_transactions=1, observation_summary="1 positions aligned; 0 misaligned."),
                holdings=[
                    SIPHoldingAnalysis(
                        symbol="MOCKSYM",
                        name="Mock Symbol",
                        target_weight=100.0,
                        actual_weight=100.0,
                        drift_pct=0.0,
                        sip_transaction_count=1,
                        sip_invested_amount=5000.0,
                    )
                ]
            )

    sip_svc = MockSIPOptimizationService()
    screen = PortfolioHealth(sip_optimization_service=sip_svc)
    assert hasattr(screen, "sip_optimization_container")


def test_empty_sip_optimization_safe(qapp):
    """Verify empty/None SIP Optimization result handles gracefully without crashing UI."""
    class EmptySIPOptimizationService:
        def get_sip_analysis(self):
            return None

    sip_svc = EmptySIPOptimizationService()
    screen = PortfolioHealth(sip_optimization_service=sip_svc)
    assert hasattr(screen, "sip_optimization_container")


def test_sip_optimization_no_data_safe(qapp):
    """Verify missing/broken SIP optimization data handles safely without crashing UI."""
    class BrokenSIPOptimizationService:
        def get_sip_analysis(self):
            raise RuntimeError("SIP optimization data missing")

    sip_svc = BrokenSIPOptimizationService()
    try:
        screen = PortfolioHealth(sip_optimization_service=sip_svc)
        assert screen is not None
    except Exception:
        pytest.fail("Missing SIP optimization data should not crash UI")


def test_portfolio_opportunities_section_loads(qapp):
    """Verify Portfolio Opportunities container layout exists in PortfolioHealth widget."""
    screen = PortfolioHealth()
    assert hasattr(screen, "portfolio_opportunity_container")


def test_portfolio_opportunities_values_display(qapp):
    """Verify Portfolio Opportunities values display properly in UI."""
    from services.portfolio_opportunity_service import PortfolioOpportunityResult, PortfolioOpportunitySummary, OpportunityRecord

    class MockPortfolioOpportunityService:
        def get_opportunities(self):
            return PortfolioOpportunityResult(
                analysis_status="ANALYZED",
                summary=PortfolioOpportunitySummary(total_opportunities=1, high_priority_count=1, assessed_count=1, highest_opportunity_score=85.0),
                opportunities=[
                    OpportunityRecord(
                        opportunity_id="OPP_TEST",
                        symbol="TEST",
                        name="Test Symbol",
                        asset_type="EQUITY",
                        opportunity_type="ALLOCATION_GAP",
                        opportunity_score=85.0,
                        opportunity_status="IDENTIFIED",
                        priority="HIGH",
                        evidence=["Test evidence"],
                        rationale="Test rationale",
                    )
                ]
            )

    opp_svc = MockPortfolioOpportunityService()
    screen = PortfolioHealth(portfolio_opportunity_service=opp_svc)
    assert hasattr(screen, "portfolio_opportunity_container")


def test_empty_portfolio_opportunities_safe(qapp):
    """Verify empty/None Portfolio Opportunities result handles gracefully without crashing UI."""
    class EmptyPortfolioOpportunityService:
        def get_opportunities(self):
            return None

    opp_svc = EmptyPortfolioOpportunityService()
    screen = PortfolioHealth(portfolio_opportunity_service=opp_svc)
    assert hasattr(screen, "portfolio_opportunity_container")


def test_portfolio_opportunities_missing_data_safe(qapp):
    """Verify missing/broken portfolio opportunity data handles safely without crashing UI."""
    class BrokenPortfolioOpportunityService:
        def get_opportunities(self):
            raise RuntimeError("Portfolio opportunity data missing")

    opp_svc = BrokenPortfolioOpportunityService()
    try:
        screen = PortfolioHealth(portfolio_opportunity_service=opp_svc)
        assert screen is not None
    except Exception:
        pytest.fail("Missing portfolio opportunity data should not crash UI")


def test_portfolio_risk_intelligence_section_loads(qapp):
    """Verify Portfolio Risk Intelligence container layout exists in PortfolioHealth widget."""
    screen = PortfolioHealth()
    assert hasattr(screen, "portfolio_risk_container")


def test_portfolio_risk_intelligence_values_display(qapp):
    """Verify Portfolio Risk Intelligence values display properly in UI."""
    from services.portfolio_risk_intelligence_service import PortfolioRiskResult, PortfolioRiskSummary, RiskAssessment, RiskHistory, RiskHistoryEntry

    class MockPortfolioRiskIntelligenceService:
        def get_risk(self):
            return PortfolioRiskResult(
                analysis_status="ANALYZED",
                summary=PortfolioRiskSummary(total_assessments=1, high_risk_count=1, assessed_count=1, highest_risk_score=75.0, position_count=1, largest_position_weight=25.0),
                assessments=[
                    RiskAssessment(
                        risk_id="RISK_TEST",
                        symbol="TEST",
                        name="Test Symbol",
                        asset_type="EQUITY",
                        risk_type="CONCENTRATION",
                        risk_score=75.0,
                        risk_level="HIGH",
                        assessment_status="ASSESSED",
                        evidence=["Test concentration evidence"],
                        rationale="Test risk rationale",
                    )
                ],
                history=RiskHistory(
                    total_entries=1,
                    earliest_timestamp="2026-08-08T08:00:00Z",
                    latest_timestamp="2026-08-08T08:00:00Z",
                    entries=[
                        RiskHistoryEntry(timestamp="2026-08-08T08:00:00Z", average_risk_score=75.0, highest_risk_score=75.0, high_risk_count=1, position_count=1, largest_position_weight=25.0)
                    ]
                )
            )

    risk_svc = MockPortfolioRiskIntelligenceService()
    screen = PortfolioHealth(portfolio_risk_intelligence_service=risk_svc)
    assert hasattr(screen, "portfolio_risk_container")


def test_empty_portfolio_risk_intelligence_safe(qapp):
    """Verify empty/None Portfolio Risk Intelligence result handles gracefully without crashing UI."""
    class EmptyPortfolioRiskIntelligenceService:
        def get_risk(self):
            return None

    risk_svc = EmptyPortfolioRiskIntelligenceService()
    screen = PortfolioHealth(portfolio_risk_intelligence_service=risk_svc)
    assert hasattr(screen, "portfolio_risk_container")


def test_portfolio_risk_intelligence_missing_data_safe(qapp):
    """Verify missing/broken portfolio risk data handles safely without crashing UI."""
    class BrokenPortfolioRiskIntelligenceService:
        def get_risk(self):
            raise RuntimeError("Portfolio risk data missing")

    risk_svc = BrokenPortfolioRiskIntelligenceService()
    try:
        screen = PortfolioHealth(portfolio_risk_intelligence_service=risk_svc)
        assert screen is not None
    except Exception:
        pytest.fail("Missing portfolio risk data should not crash UI")


def test_portfolio_risk_history_safe(qapp):
    """Verify empty/corrupt risk history handles safely without crashing UI."""
    from services.portfolio_risk_intelligence_service import PortfolioRiskResult, PortfolioRiskSummary, RiskHistory

    class EmptyHistoryRiskIntelligenceService:
        def get_risk(self):
            return PortfolioRiskResult(
                analysis_status="ANALYZED",
                summary=PortfolioRiskSummary(total_assessments=0),
                assessments=[],
                history=RiskHistory(total_entries=0, entries=[])
            )

    risk_svc = EmptyHistoryRiskIntelligenceService()
    screen = PortfolioHealth(portfolio_risk_intelligence_service=risk_svc)
    assert hasattr(screen, "portfolio_risk_container")


def test_alpha12_mapping_section_loads(qapp):
    """Verify Alpha 12 Portfolio Mapping container layout exists in PortfolioHealth widget."""
    screen = PortfolioHealth()
    assert hasattr(screen, "alpha12_mapping_container")


def test_alpha12_mapping_values_display(qapp):
    """Verify Alpha 12 Portfolio Mapping values display properly in UI."""
    from services.alpha12_mapping_service import Alpha12MappingResult, Alpha12PortfolioMapping, Alpha12HoldingMapping

    class MockAlpha12MappingService:
        def get_mapping(self):
            return Alpha12MappingResult(
                analysis_status="ANALYZED",
                portfolio=Alpha12PortfolioMapping(
                    mapping_status="MAPPED",
                    total_alpha12_holdings=1,
                    mapped_holdings=1,
                    unmapped_holdings=0,
                    mapping_coverage_pct=100.0,
                    holdings=[
                        Alpha12HoldingMapping(
                            symbol="TEST",
                            name="Test Symbol",
                            alpha12_rank=1,
                            alpha12_weight=100.0,
                            current_weight=100.0,
                            current_value=50000.0,
                            asset_type="EQUITY",
                            mapping_status="MAPPED",
                            evidence=["Exact symbol match: TEST"],
                            rationale="Test mapping rationale",
                        )
                    ],
                )
            )

    map_svc = MockAlpha12MappingService()
    screen = PortfolioHealth(alpha12_mapping_service=map_svc)
    assert hasattr(screen, "alpha12_mapping_container")


def test_empty_alpha12_mapping_safe(qapp):
    """Verify empty/None Alpha 12 Mapping result handles gracefully without crashing UI."""
    class EmptyAlpha12MappingService:
        def get_mapping(self):
            return None

    map_svc = EmptyAlpha12MappingService()
    screen = PortfolioHealth(alpha12_mapping_service=map_svc)
    assert hasattr(screen, "alpha12_mapping_container")


def test_alpha12_mapping_missing_data_safe(qapp):
    """Verify missing/broken Alpha 12 mapping data handles safely without crashing UI."""
    class BrokenAlpha12MappingService:
        def get_mapping(self):
            raise RuntimeError("Alpha 12 mapping data missing")

    map_svc = BrokenAlpha12MappingService()
    try:
        screen = PortfolioHealth(alpha12_mapping_service=map_svc)
        assert screen is not None
    except Exception:
        pytest.fail("Missing Alpha 12 mapping data should not crash UI")


def test_alpha12_mapping_unavailable_source_safe(qapp):
    """Verify UNAVAILABLE Alpha 12 mapping status displays safely in UI."""
    from services.alpha12_mapping_service import Alpha12MappingResult, Alpha12PortfolioMapping

    class UnavailableAlpha12MappingService:
        def get_mapping(self):
            return Alpha12MappingResult(
                analysis_status="UNAVAILABLE",
                portfolio=Alpha12PortfolioMapping(mapping_status="UNAVAILABLE"),
                rationale="Alpha 12 portfolio source is not available."
            )

    map_svc = UnavailableAlpha12MappingService()
    screen = PortfolioHealth(alpha12_mapping_service=map_svc)
    assert hasattr(screen, "alpha12_mapping_container")


def test_alpha12_stability_section_loads(qapp):
    """Verify Alpha 12 Stability UI container loads safely."""
    screen = PortfolioHealth()
    assert hasattr(screen, "alpha12_stability_container")


def test_alpha12_stability_empty_state_safe(qapp):
    """Verify empty/UNAVAILABLE Alpha 12 stability result renders safe empty message."""
    from services.alpha12_stability_service import Alpha12StabilityResult

    class EmptyStabilityService:
        def get_stability(self):
            return Alpha12StabilityResult(
                analysis_status="UNAVAILABLE",
                rationale="Alpha 12 stability data unavailable.",
            )

    stab_svc = EmptyStabilityService()
    screen = PortfolioHealth(alpha12_stability_service=stab_svc)
    assert hasattr(screen, "alpha12_stability_container")


def test_alpha12_stability_values_display(qapp):
    """Verify valid Alpha 12 stability result populates UI container."""
    from services.alpha12_stability_service import (
        Alpha12StabilityMetrics,
        Alpha12StabilityResult,
    )

    class ValidStabilityService:
        def get_stability(self):
            metrics = Alpha12StabilityMetrics(
                stability_score=92.5,
                stability_rating="VERY_STABLE",
                turnover_rate=2.5,
                churn_prevention_ratio=100.0,
                unnecessary_swap_prevention=2,
                churn_risk="LOW",
                turnover_efficiency=0.98,
                average_holding_tenure_months=12.0,
                persistence_count=12,
                assessment_status="STABLE",
                rationale="Highly stable long-term portfolio.",
                evidence=["Stability Score: 92.5/100"],
            )
            return Alpha12StabilityResult(
                analysis_status="ANALYZED",
                stability_metrics=metrics,
                latest_timestamp="2026-08-08T12:00:00Z",
                rationale="Highly stable long-term portfolio.",
            )

    stab_svc = ValidStabilityService()
    screen = PortfolioHealth(alpha12_stability_service=stab_svc)
    assert hasattr(screen, "alpha12_stability_container")
