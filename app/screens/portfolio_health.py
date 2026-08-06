from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QScrollArea,
)

from services.portfolio_health_history_service import PortfolioHealthHistoryService
from services.portfolio_health_service import (
    PortfolioHealthResult,
    PortfolioHealthService,
    PortfolioHealthSnapshot,
)


class PortfolioHealth(QWidget):

    def __init__(
        self,
        service: Optional[PortfolioHealthService] = None,
        history_service: Optional[PortfolioHealthHistoryService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.history_service = history_service if history_service is not None else PortfolioHealthHistoryService()
        self.service = service if service is not None else PortfolioHealthService(history_service=self.history_service)
        self._build_ui()
        self.refresh_data()

    def refresh_data(self) -> None:
        """Fetch and bind live portfolio health snapshot, evaluation, and history data."""
        if self.service is not None:
            snapshot = None
            if hasattr(self.service, "build_snapshot"):
                try:
                    snapshot = self.service.build_snapshot()
                    self.load_snapshot(snapshot)
                except Exception:
                    pass

            if hasattr(self.service, "evaluate"):
                try:
                    result = self.service.evaluate(snapshot)
                    self.load_result(result)
                except Exception:
                    pass

        self.load_history()

    def load_history(self) -> None:
        """Bind live portfolio health history metrics to UI."""
        if getattr(self, "history_service", None) is None:
            return
        try:
            history = self.history_service.get_history()
            count = len(history) if history else 0
            latest = history[-1] if history else None

            if hasattr(self, "lbl_history_entries"):
                self.lbl_history_entries.setText(f"History Entries: {count}")
            if hasattr(self, "lbl_history_latest_score"):
                score_str = str(latest.score) if latest else "N/A"
                self.lbl_history_latest_score.setText(f"Latest Score: {score_str}")
            if hasattr(self, "lbl_history_latest_grade"):
                grade_str = str(latest.grade) if latest else "N/A"
                self.lbl_history_latest_grade.setText(f"Latest Grade: {grade_str}")
        except Exception:
            pass

    def load_snapshot(self, snapshot: Optional[PortfolioHealthSnapshot] = None) -> None:
        """Bind live snapshot metrics to the metric cards."""
        if snapshot is None:
            return

        if "Position Count" in self.cards:
            self.cards["Position Count"].setText(str(snapshot.position_count))

        if "Cash Allocation" in self.cards:
            val = snapshot.cash_allocation_pct
            val_str = f"{val:.1f}%" if (val % 1 != 0) else f"{int(val)}%"
            self.cards["Cash Allocation"].setText(val_str)

        if "Largest Position" in self.cards:
            self.cards["Largest Position"].setText(str(snapshot.largest_position))

    def load_result(self, result: Optional[PortfolioHealthResult] = None) -> None:
        """Bind live PortfolioHealthResult metrics to score, diversification, concentration, and analytics sections."""
        if result is None:
            return

        if "Overall Health Score" in self.cards:
            grade_suffix = f" ({result.grade})" if getattr(result, "grade", None) else ""
            self.cards["Overall Health Score"].setText(f"{result.score} / 100{grade_suffix}")

        if "Diversification" in self.cards:
            self.cards["Diversification"].setText(str(result.diversification_rating))

        if "Concentration" in self.cards:
            self.cards["Concentration"].setText(str(result.concentration_rating))

        analytics = getattr(result, "analytics", None)
        if analytics is not None:
            if hasattr(self, "lbl_breakdown_div"):
                self.lbl_breakdown_div.setText(f"Diversification: {analytics.diversification_score} / 40")
            if hasattr(self, "lbl_breakdown_conc"):
                self.lbl_breakdown_conc.setText(f"Concentration: {analytics.concentration_score} / 40")
            if hasattr(self, "lbl_breakdown_cash"):
                self.lbl_breakdown_cash.setText(f"Cash Allocation: {analytics.cash_score} / 20")

            if hasattr(self, "strengths_container"):
                self._clear_layout(self.strengths_container)
                if analytics.strengths:
                    for item in analytics.strengths:
                        lbl = QLabel(f"• {item}")
                        lbl.setStyleSheet("font-size: 14px; color: #16a34a; font-weight: 500;")
                        self.strengths_container.addWidget(lbl)
                else:
                    lbl = QLabel("None identified")
                    lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                    self.strengths_container.addWidget(lbl)

            if hasattr(self, "weaknesses_container"):
                self._clear_layout(self.weaknesses_container)
                if analytics.weaknesses:
                    for item in analytics.weaknesses:
                        lbl = QLabel(f"• {item}")
                        lbl.setStyleSheet("font-size: 14px; color: #dc2626; font-weight: 500;")
                        self.weaknesses_container.addWidget(lbl)
                else:
                    lbl = QLabel("None identified")
                    lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                    self.weaknesses_container.addWidget(lbl)

        trend = getattr(result, "trend", None)
        if trend is not None:
            if hasattr(self, "lbl_trend_current"):
                self.lbl_trend_current.setText(f"Current Score: {trend.current_score}")
            if hasattr(self, "lbl_trend_previous"):
                self.lbl_trend_previous.setText(f"Previous Score: {trend.previous_score}")
            if hasattr(self, "lbl_trend_change"):
                change_str = f"+{trend.score_change}" if trend.score_change > 0 else str(trend.score_change)
                self.lbl_trend_change.setText(f"Score Change: {change_str}")
            if hasattr(self, "lbl_trend_direction"):
                self.lbl_trend_direction.setText(f"Trend: {trend.trend_direction}")

        hist_analytics = getattr(result, "historical_analytics", None)
        if hist_analytics is not None:
            if hasattr(self, "lbl_hist_entries"):
                self.lbl_hist_entries.setText(f"History Entries: {hist_analytics.history_count}")
            if hasattr(self, "lbl_hist_best"):
                self.lbl_hist_best.setText(f"Best Score: {hist_analytics.best_score}")
            if hasattr(self, "lbl_hist_worst"):
                self.lbl_hist_worst.setText(f"Worst Score: {hist_analytics.worst_score}")
            if hasattr(self, "lbl_hist_avg"):
                self.lbl_hist_avg.setText(f"Average Score: {hist_analytics.average_score}")
            if hasattr(self, "lbl_hist_curr"):
                self.lbl_hist_curr.setText(f"Current Score: {hist_analytics.current_score}")
            if hasattr(self, "lbl_hist_trend"):
                self.lbl_hist_trend.setText(f"Overall Trend: {hist_analytics.overall_trend}")

        summary = getattr(result, "dashboard_summary", None)
        if summary is not None:
            if hasattr(self, "lbl_dash_curr_score"):
                self.lbl_dash_curr_score.setText(f"Current Score: {summary.current_score}")
            if hasattr(self, "lbl_dash_curr_grade"):
                self.lbl_dash_curr_grade.setText(f"Current Grade: {summary.current_grade}")
            if hasattr(self, "lbl_dash_best_score"):
                self.lbl_dash_best_score.setText(f"Best Historical Score: {summary.best_score}")
            if hasattr(self, "lbl_dash_best_grade"):
                self.lbl_dash_best_grade.setText(f"Best Historical Grade: {summary.best_grade}")
            if hasattr(self, "lbl_dash_worst_score"):
                self.lbl_dash_worst_score.setText(f"Worst Historical Score: {summary.worst_score}")
            if hasattr(self, "lbl_dash_worst_grade"):
                self.lbl_dash_worst_grade.setText(f"Worst Historical Grade: {summary.worst_grade}")
            if hasattr(self, "lbl_dash_avg_score"):
                self.lbl_dash_avg_score.setText(f"Average Historical Score: {summary.average_score}")
            if hasattr(self, "lbl_dash_total_snapshots"):
                self.lbl_dash_total_snapshots.setText(f"Total Snapshots: {summary.total_snapshots}")

            if hasattr(self, "lbl_highlight_highest"):
                self.lbl_highlight_highest.setText(f"Highest Score Achieved: {summary.best_score}")
            if hasattr(self, "lbl_highlight_lowest"):
                self.lbl_highlight_lowest.setText(f"Lowest Score Achieved: {summary.worst_score}")
            if hasattr(self, "lbl_highlight_vs_avg"):
                diff = round(summary.current_score - summary.average_score, 1)
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                self.lbl_highlight_vs_avg.setText(f"Current Score vs Average: {diff_str}")

        metrics = getattr(result, "historical_metrics", None)
        if metrics is not None:
            if hasattr(self, "lbl_metrics_range"):
                self.lbl_metrics_range.setText(f"Score Range: {metrics.score_range}")
            if hasattr(self, "lbl_metrics_volatility"):
                self.lbl_metrics_volatility.setText(f"Volatility Score: {metrics.volatility_score}")
            if hasattr(self, "lbl_metrics_improving"):
                self.lbl_metrics_improving.setText(f"Improving Periods: {metrics.improving_periods}")
            if hasattr(self, "lbl_metrics_deteriorating"):
                self.lbl_metrics_deteriorating.setText(f"Deteriorating Periods: {metrics.deteriorating_periods}")
            if hasattr(self, "lbl_metrics_stability"):
                self.lbl_metrics_stability.setText(f"Stability Rating: {metrics.stability_rating}")

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fb;
                color: #1f2937;
                font-family: Segoe UI;
            }

            QLabel#pageTitle {
                font-size: 28px;
                font-weight: 700;
                color: #173b67;
            }

            QLabel#pageSubtitle {
                font-size: 14px;
                color: #64748b;
            }

            QFrame#metricCard {
                background-color: white;
                border: 1px solid #dce3ed;
                border-radius: 10px;
            }

            QLabel#cardTitle {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
            }

            QLabel#cardValue {
                font-size: 22px;
                font-weight: 700;
                color: #173b67;
            }

            QLabel#sectionHeader {
                font-size: 16px;
                font-weight: 700;
                color: #173b67;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content_widget = QWidget()
        root_layout = QVBoxLayout(content_widget)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(20)

        # Header Title
        title_box = QVBoxLayout()
        header_title = QLabel("Portfolio Health")
        header_title.setObjectName("pageTitle")

        header_subtitle = QLabel("Overview of key health and risk metrics for your portfolio")
        header_subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(header_title)
        title_box.addWidget(header_subtitle)
        root_layout.addLayout(title_box)

        # Metric Cards Grid Layout
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        cards_spec = [
            ("Overall Health Score", "85 / 100", 0, 0),
            ("Diversification", "GOOD", 0, 1),
            ("Concentration", "MODERATE", 0, 2),
            ("Position Count", "12", 1, 0),
            ("Cash Allocation", "5%", 1, 1),
            ("Largest Position", "KPITTECH", 1, 2),
        ]

        self.cards = {}
        for title, value, row, col in cards_spec:
            card_frame, val_lbl = self._create_metric_card(title, value)
            cards_grid.addWidget(card_frame, row, col)
            self.cards[title] = val_lbl

        root_layout.addLayout(cards_grid)

        # Analytics Sections: Health Score Breakdown
        breakdown_card = QFrame()
        breakdown_card.setObjectName("metricCard")
        breakdown_layout = QVBoxLayout(breakdown_card)
        breakdown_layout.setContentsMargins(16, 14, 16, 14)
        breakdown_layout.setSpacing(8)

        lbl_breakdown_header = QLabel("Health Score Breakdown")
        lbl_breakdown_header.setObjectName("sectionHeader")
        breakdown_layout.addWidget(lbl_breakdown_header)

        self.lbl_breakdown_div = QLabel("Diversification: - / 40")
        self.lbl_breakdown_div.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_breakdown_conc = QLabel("Concentration: - / 40")
        self.lbl_breakdown_conc.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_breakdown_cash = QLabel("Cash Allocation: - / 20")
        self.lbl_breakdown_cash.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        breakdown_layout.addWidget(self.lbl_breakdown_div)
        breakdown_layout.addWidget(self.lbl_breakdown_conc)
        breakdown_layout.addWidget(self.lbl_breakdown_cash)

        root_layout.addWidget(breakdown_card)

        # Strengths Section
        strengths_card = QFrame()
        strengths_card.setObjectName("metricCard")
        strengths_layout = QVBoxLayout(strengths_card)
        strengths_layout.setContentsMargins(16, 14, 16, 14)
        strengths_layout.setSpacing(8)

        lbl_strengths_header = QLabel("Strengths")
        lbl_strengths_header.setObjectName("sectionHeader")
        strengths_layout.addWidget(lbl_strengths_header)

        self.strengths_container = QVBoxLayout()
        strengths_layout.addLayout(self.strengths_container)

        root_layout.addWidget(strengths_card)

        # Weaknesses Section
        weaknesses_card = QFrame()
        weaknesses_card.setObjectName("metricCard")
        weaknesses_layout = QVBoxLayout(weaknesses_card)
        weaknesses_layout.setContentsMargins(16, 14, 16, 14)
        weaknesses_layout.setSpacing(8)

        lbl_weaknesses_header = QLabel("Weaknesses")
        lbl_weaknesses_header.setObjectName("sectionHeader")
        weaknesses_layout.addWidget(lbl_weaknesses_header)

        self.weaknesses_container = QVBoxLayout()
        weaknesses_layout.addLayout(self.weaknesses_container)

        root_layout.addWidget(weaknesses_card)

        # Portfolio Health Trend Section
        trend_card = QFrame()
        trend_card.setObjectName("metricCard")
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(16, 14, 16, 14)
        trend_layout.setSpacing(8)

        lbl_trend_header = QLabel("Portfolio Health Trend")
        lbl_trend_header.setObjectName("sectionHeader")
        trend_layout.addWidget(lbl_trend_header)

        self.lbl_trend_current = QLabel("Current Score: -")
        self.lbl_trend_current.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_trend_previous = QLabel("Previous Score: -")
        self.lbl_trend_previous.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_trend_change = QLabel("Score Change: -")
        self.lbl_trend_change.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_trend_direction = QLabel("Trend: -")
        self.lbl_trend_direction.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        trend_layout.addWidget(self.lbl_trend_current)
        trend_layout.addWidget(self.lbl_trend_previous)
        trend_layout.addWidget(self.lbl_trend_change)
        trend_layout.addWidget(self.lbl_trend_direction)

        root_layout.addWidget(trend_card)

        # Portfolio Health History Section
        history_card = QFrame()
        history_card.setObjectName("metricCard")
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(16, 14, 16, 14)
        history_layout.setSpacing(8)

        lbl_history_header = QLabel("Portfolio Health History")
        lbl_history_header.setObjectName("sectionHeader")
        history_layout.addWidget(lbl_history_header)

        self.lbl_history_entries = QLabel("History Entries: 0")
        self.lbl_history_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_history_latest_score = QLabel("Latest Score: N/A")
        self.lbl_history_latest_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_history_latest_grade = QLabel("Latest Grade: N/A")
        self.lbl_history_latest_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        history_layout.addWidget(self.lbl_history_entries)
        history_layout.addWidget(self.lbl_history_latest_score)
        history_layout.addWidget(self.lbl_history_latest_grade)

        root_layout.addWidget(history_card)

        # Portfolio Health Historical Analytics Section
        hist_card = QFrame()
        hist_card.setObjectName("metricCard")
        hist_layout = QVBoxLayout(hist_card)
        hist_layout.setContentsMargins(16, 14, 16, 14)
        hist_layout.setSpacing(8)

        lbl_hist_header = QLabel("Portfolio Health Historical Analytics")
        lbl_hist_header.setObjectName("sectionHeader")
        hist_layout.addWidget(lbl_hist_header)

        self.lbl_hist_entries = QLabel("History Entries: 0")
        self.lbl_hist_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_best = QLabel("Best Score: 0")
        self.lbl_hist_best.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_worst = QLabel("Worst Score: 0")
        self.lbl_hist_worst.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_avg = QLabel("Average Score: 0.0")
        self.lbl_hist_avg.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_curr = QLabel("Current Score: 0")
        self.lbl_hist_curr.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_trend = QLabel("Overall Trend: STABLE")
        self.lbl_hist_trend.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        hist_layout.addWidget(self.lbl_hist_entries)
        hist_layout.addWidget(self.lbl_hist_best)
        hist_layout.addWidget(self.lbl_hist_worst)
        hist_layout.addWidget(self.lbl_hist_avg)
        hist_layout.addWidget(self.lbl_hist_curr)
        hist_layout.addWidget(self.lbl_hist_trend)

        root_layout.addWidget(hist_card)

        # Portfolio Health Dashboard Summary Section
        dash_card = QFrame()
        dash_card.setObjectName("metricCard")
        dash_layout = QVBoxLayout(dash_card)
        dash_layout.setContentsMargins(16, 14, 16, 14)
        dash_layout.setSpacing(8)

        lbl_dash_header = QLabel("Portfolio Health Dashboard Summary")
        lbl_dash_header.setObjectName("sectionHeader")
        dash_layout.addWidget(lbl_dash_header)

        self.lbl_dash_curr_score = QLabel("Current Score: 0")
        self.lbl_dash_curr_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_curr_grade = QLabel("Current Grade: -")
        self.lbl_dash_curr_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_best_score = QLabel("Best Historical Score: 0")
        self.lbl_dash_best_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_best_grade = QLabel("Best Historical Grade: -")
        self.lbl_dash_best_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_worst_score = QLabel("Worst Historical Score: 0")
        self.lbl_dash_worst_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_worst_grade = QLabel("Worst Historical Grade: -")
        self.lbl_dash_worst_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_avg_score = QLabel("Average Historical Score: 0.0")
        self.lbl_dash_avg_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_total_snapshots = QLabel("Total Snapshots: 0")
        self.lbl_dash_total_snapshots.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dash_layout.addWidget(self.lbl_dash_curr_score)
        dash_layout.addWidget(self.lbl_dash_curr_grade)
        dash_layout.addWidget(self.lbl_dash_best_score)
        dash_layout.addWidget(self.lbl_dash_best_grade)
        dash_layout.addWidget(self.lbl_dash_worst_score)
        dash_layout.addWidget(self.lbl_dash_worst_grade)
        dash_layout.addWidget(self.lbl_dash_avg_score)
        dash_layout.addWidget(self.lbl_dash_total_snapshots)

        # Historical Highlights Subsection
        lbl_highlights_header = QLabel("Historical Highlights")
        lbl_highlights_header.setObjectName("sectionHeader")
        lbl_highlights_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #173b67; margin-top: 6px;")
        dash_layout.addWidget(lbl_highlights_header)

        self.lbl_highlight_highest = QLabel("Highest Score Achieved: 0")
        self.lbl_highlight_highest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_highlight_lowest = QLabel("Lowest Score Achieved: 0")
        self.lbl_highlight_lowest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_highlight_vs_avg = QLabel("Current Score vs Average: 0.0")
        self.lbl_highlight_vs_avg.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dash_layout.addWidget(self.lbl_highlight_highest)
        dash_layout.addWidget(self.lbl_highlight_lowest)
        dash_layout.addWidget(self.lbl_highlight_vs_avg)

        root_layout.addWidget(dash_card)

        # Portfolio Health Historical Metrics Section
        metrics_card = QFrame()
        metrics_card.setObjectName("metricCard")
        metrics_layout = QVBoxLayout(metrics_card)
        metrics_layout.setContentsMargins(16, 14, 16, 14)
        metrics_layout.setSpacing(8)

        lbl_metrics_header = QLabel("Portfolio Health Historical Metrics")
        lbl_metrics_header.setObjectName("sectionHeader")
        metrics_layout.addWidget(lbl_metrics_header)

        self.lbl_metrics_range = QLabel("Score Range: 0")
        self.lbl_metrics_range.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_volatility = QLabel("Volatility Score: 0.0")
        self.lbl_metrics_volatility.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_improving = QLabel("Improving Periods: 0")
        self.lbl_metrics_improving.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_deteriorating = QLabel("Deteriorating Periods: 0")
        self.lbl_metrics_deteriorating.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_stability = QLabel("Stability Rating: VERY_STABLE")
        self.lbl_metrics_stability.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        metrics_layout.addWidget(self.lbl_metrics_range)
        metrics_layout.addWidget(self.lbl_metrics_volatility)
        metrics_layout.addWidget(self.lbl_metrics_improving)
        metrics_layout.addWidget(self.lbl_metrics_deteriorating)
        metrics_layout.addWidget(self.lbl_metrics_stability)

        root_layout.addWidget(metrics_card)

        root_layout.addStretch()

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def _create_metric_card(self, title: str, value: str):
        card = QFrame()
        card.setObjectName("metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        t_lbl = QLabel(title.upper())
        t_lbl.setObjectName("cardTitle")

        val_lbl = QLabel(value)
        val_lbl.setObjectName("cardValue")

        layout.addWidget(t_lbl)
        layout.addWidget(val_lbl)
        return card, val_lbl
