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
