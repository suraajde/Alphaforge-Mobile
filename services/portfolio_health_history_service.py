import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class PortfolioHealthHistoryEntry:
    timestamp: str
    score: int
    grade: str
    diversification_rating: str
    concentration_rating: str
    position_count: int
    largest_position_weight_pct: float
    cash_allocation_pct: float


@dataclass
class PortfolioHealthHistoricalAnalytics:
    history_count: int
    best_score: int
    worst_score: int
    average_score: float
    current_score: int
    overall_trend: str


@dataclass
class PortfolioHealthDashboardSummary:
    total_snapshots: int
    current_score: int
    current_grade: str
    best_score: int
    best_grade: str
    worst_score: int
    worst_grade: str
    average_score: float


@dataclass
class PortfolioHealthHistoricalMetrics:
    score_range: int
    best_score: int
    worst_score: int
    volatility_score: float
    improving_periods: int
    deteriorating_periods: int
    stability_rating: str


@dataclass
class PortfolioHealthHistoricalInsights:
    improvement_percentage: float
    deterioration_percentage: float
    neutral_percentage: float
    consistency_score: float
    quality_rating: str
    direction_rating: str


class PortfolioHealthHistoryService:
    """Service layer for persisting and retrieving portfolio health history entries."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        if storage_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            storage_path = os.path.join(base_dir, "data", "portfolio_health", "portfolio_health_history.json")
        self.storage_path = storage_path

    def _ensure_directory(self) -> None:
        dir_name = os.path.dirname(self.storage_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    def save_snapshot(self, result: Any) -> Optional[PortfolioHealthHistoryEntry]:
        """Saves a PortfolioHealthResult as a historical entry safely.

        Args:
            result: PortfolioHealthResult or object with score, grade, ratings, etc.
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            score = int(getattr(result, "score", 0))
            grade = str(getattr(result, "grade", "N/A"))
            div_rating = str(getattr(result, "diversification_rating", "N/A"))
            conc_rating = str(getattr(result, "concentration_rating", "N/A"))
            pos_count = int(getattr(result, "position_count", 0))
            largest_weight = float(getattr(result, "largest_position_weight_pct", 0.0))
            cash_pct = float(getattr(result, "cash_allocation_pct", 0.0))

            entry = PortfolioHealthHistoryEntry(
                timestamp=timestamp,
                score=score,
                grade=grade,
                diversification_rating=div_rating,
                concentration_rating=conc_rating,
                position_count=pos_count,
                largest_position_weight_pct=largest_weight,
                cash_allocation_pct=cash_pct,
            )

            history = self.get_history()
            history.append(entry)

            self._ensure_directory()
            data = [asdict(e) for e in history]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return entry
        except Exception:
            return None

    def get_history(self) -> list[PortfolioHealthHistoryEntry]:
        """Loads and returns historical portfolio health entries safely without raising exceptions."""
        try:
            if not os.path.exists(self.storage_path):
                return []
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []

            entries = []
            for item in data:
                if isinstance(item, dict):
                    entries.append(
                        PortfolioHealthHistoryEntry(
                            timestamp=str(item.get("timestamp", "")),
                            score=int(item.get("score", 0)),
                            grade=str(item.get("grade", "N/A")),
                            diversification_rating=str(item.get("diversification_rating", "N/A")),
                            concentration_rating=str(item.get("concentration_rating", "N/A")),
                            position_count=int(item.get("position_count", 0)),
                            largest_position_weight_pct=float(item.get("largest_position_weight_pct", 0.0)),
                            cash_allocation_pct=float(item.get("cash_allocation_pct", 0.0)),
                        )
                    )
            return entries
        except Exception:
            return []

    def get_latest(self) -> Optional[PortfolioHealthHistoryEntry]:
        """Returns the most recent history entry, or None if empty."""
        history = self.get_history()
        return history[-1] if history else None

    def get_previous(self) -> Optional[PortfolioHealthHistoryEntry]:
        """Returns the second most recent history entry, or None if unavailable."""
        history = self.get_history()
        return history[-2] if len(history) >= 2 else None

    def get_historical_analytics(self) -> PortfolioHealthHistoricalAnalytics:
        """Calculates multi-period historical analytics from stored health history."""
        try:
            history = self.get_history()
            if not history:
                return PortfolioHealthHistoricalAnalytics(
                    history_count=0,
                    best_score=0,
                    worst_score=0,
                    average_score=0.0,
                    current_score=0,
                    overall_trend="STABLE",
                )

            scores = [e.score for e in history]
            history_count = len(scores)
            best_score = max(scores)
            worst_score = min(scores)
            average_score = round(sum(scores) / len(scores), 1)
            current_score = scores[-1]

            if current_score > average_score + 3:
                overall_trend = "IMPROVING"
            elif current_score < average_score - 3:
                overall_trend = "DETERIORATING"
            else:
                overall_trend = "STABLE"

            return PortfolioHealthHistoricalAnalytics(
                history_count=history_count,
                best_score=best_score,
                worst_score=worst_score,
                average_score=average_score,
                current_score=current_score,
                overall_trend=overall_trend,
            )
        except Exception:
            return PortfolioHealthHistoricalAnalytics(
                history_count=0,
                best_score=0,
                worst_score=0,
                average_score=0.0,
                current_score=0,
                overall_trend="STABLE",
            )

    def get_dashboard_summary(self) -> PortfolioHealthDashboardSummary:
        """Calculates consolidated dashboard summary from stored health history."""
        try:
            history = self.get_history()
            if not history:
                return PortfolioHealthDashboardSummary(
                    total_snapshots=0,
                    current_score=0,
                    current_grade="-",
                    best_score=0,
                    best_grade="-",
                    worst_score=0,
                    worst_grade="-",
                    average_score=0.0,
                )

            total_snapshots = len(history)
            current_entry = history[-1]
            current_score = current_entry.score
            current_grade = current_entry.grade

            best_entry = max(history, key=lambda e: e.score)
            best_score = best_entry.score
            best_grade = best_entry.grade

            worst_entry = min(history, key=lambda e: e.score)
            worst_score = worst_entry.score
            worst_grade = worst_entry.grade

            average_score = round(sum(e.score for e in history) / total_snapshots, 1)

            return PortfolioHealthDashboardSummary(
                total_snapshots=total_snapshots,
                current_score=current_score,
                current_grade=current_grade,
                best_score=best_score,
                best_grade=best_grade,
                worst_score=worst_score,
                worst_grade=worst_grade,
                average_score=average_score,
            )
        except Exception:
            return PortfolioHealthDashboardSummary(
                total_snapshots=0,
                current_score=0,
                current_grade="-",
                best_score=0,
                best_grade="-",
                worst_score=0,
                worst_grade="-",
                average_score=0.0,
            )

    def get_historical_metrics(self) -> PortfolioHealthHistoricalMetrics:
        """Calculates advanced quantitative historical metrics from stored health history."""
        try:
            history = self.get_history()
            if not history:
                return PortfolioHealthHistoricalMetrics(
                    score_range=0,
                    best_score=0,
                    worst_score=0,
                    volatility_score=0.0,
                    improving_periods=0,
                    deteriorating_periods=0,
                    stability_rating="VERY_STABLE",
                )

            scores = [e.score for e in history]
            best_score = max(scores)
            worst_score = min(scores)
            score_range = best_score - worst_score

            if len(scores) < 2:
                volatility_score = 0.0
                improving_periods = 0
                deteriorating_periods = 0
            else:
                diffs = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
                abs_diffs = [abs(d) for d in diffs]
                volatility_score = round(sum(abs_diffs) / len(abs_diffs), 1)
                improving_periods = sum(1 for d in diffs if d > 0)
                deteriorating_periods = sum(1 for d in diffs if d < 0)

            if volatility_score <= 2.0:
                stability_rating = "VERY_STABLE"
            elif volatility_score <= 5.0:
                stability_rating = "STABLE"
            elif volatility_score <= 8.0:
                stability_rating = "MODERATE"
            else:
                stability_rating = "VOLATILE"

            return PortfolioHealthHistoricalMetrics(
                score_range=score_range,
                best_score=best_score,
                worst_score=worst_score,
                volatility_score=volatility_score,
                improving_periods=improving_periods,
                deteriorating_periods=deteriorating_periods,
                stability_rating=stability_rating,
            )
        except Exception:
            return PortfolioHealthHistoricalMetrics(
                score_range=0,
                best_score=0,
                worst_score=0,
                volatility_score=0.0,
                improving_periods=0,
                deteriorating_periods=0,
                stability_rating="VERY_STABLE",
            )

    def get_historical_insights(self) -> PortfolioHealthHistoricalInsights:
        """Calculates high-level insight statistics derived from historical behavior."""
        try:
            history = self.get_history()
            if not history or len(history) < 2:
                return PortfolioHealthHistoricalInsights(
                    improvement_percentage=0.0,
                    deterioration_percentage=0.0,
                    neutral_percentage=0.0,
                    consistency_score=0.0,
                    quality_rating="MIXED",
                    direction_rating="STABLE",
                )

            scores = [e.score for e in history]
            total_transitions = len(scores) - 1
            diffs = [scores[i] - scores[i - 1] for i in range(1, len(scores))]

            improving_count = sum(1 for d in diffs if d > 0)
            deteriorating_count = sum(1 for d in diffs if d < 0)
            neutral_count = sum(1 for d in diffs if d == 0)

            improvement_percentage = round((improving_count / total_transitions) * 100.0, 1)
            deterioration_percentage = round((deteriorating_count / total_transitions) * 100.0, 1)
            neutral_percentage = round((neutral_count / total_transitions) * 100.0, 1)

            consistency_score = round(improvement_percentage - deterioration_percentage, 1)

            if consistency_score >= 75.0:
                quality_rating = "EXCELLENT"
            elif consistency_score >= 40.0:
                quality_rating = "GOOD"
            elif consistency_score >= 10.0:
                quality_rating = "FAIR"
            elif consistency_score >= -9.9:
                quality_rating = "MIXED"
            else:
                quality_rating = "WEAK"

            if consistency_score > 10.0:
                direction_rating = "IMPROVING"
            elif consistency_score < -10.0:
                direction_rating = "DETERIORATING"
            else:
                direction_rating = "STABLE"

            return PortfolioHealthHistoricalInsights(
                improvement_percentage=improvement_percentage,
                deterioration_percentage=deterioration_percentage,
                neutral_percentage=neutral_percentage,
                consistency_score=consistency_score,
                quality_rating=quality_rating,
                direction_rating=direction_rating,
            )
        except Exception:
            return PortfolioHealthHistoricalInsights(
                improvement_percentage=0.0,
                deterioration_percentage=0.0,
                neutral_percentage=0.0,
                consistency_score=0.0,
                quality_rating="MIXED",
                direction_rating="STABLE",
            )
