"""Portfolio Health Timeline Service (Sprint 13.4.2)

Provides a chronological timeline engine summarizing the evolution of Portfolio Health over time.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from services.portfolio_health_change_detection_service import (
    PortfolioHealthChangeDetectionService,
)
from services.portfolio_health_history_service import PortfolioHealthHistoryService


@dataclass
class PortfolioHealthTimelineEntry:
    sequence: int
    timestamp: str
    score: int
    grade: str
    trend_direction: str
    change_count: int


@dataclass
class PortfolioHealthTimeline:
    total_entries: int
    latest_timestamp: Optional[str]
    earliest_timestamp: Optional[str]
    entries: list[PortfolioHealthTimelineEntry]


class PortfolioHealthTimelineService:
    """Service for building chronological portfolio health timeline evolutions."""

    def __init__(
        self,
        history_service: Optional[PortfolioHealthHistoryService] = None,
        change_detection_service: Optional[PortfolioHealthChangeDetectionService] = None,
    ) -> None:
        self.history_service = history_service if history_service is not None else PortfolioHealthHistoryService()
        self.change_detection_service = (
            change_detection_service
            if change_detection_service is not None
            else PortfolioHealthChangeDetectionService(history_service=self.history_service)
        )

    def build_timeline(self, history: Optional[list[Any]] = None) -> PortfolioHealthTimeline:
        """Builds and returns a chronological PortfolioHealthTimeline safely without raising exceptions."""
        default_timeline = PortfolioHealthTimeline(
            total_entries=0,
            latest_timestamp=None,
            earliest_timestamp=None,
            entries=[],
        )

        try:
            if history is None:
                if self.history_service is None:
                    return default_timeline
                try:
                    history = self.history_service.get_history()
                except Exception:
                    return default_timeline

            if not isinstance(history, list) or len(history) == 0:
                return default_timeline

            # Sort entries chronologically from Oldest to Newest
            sorted_history = sorted(
                history,
                key=lambda e: getattr(e, "timestamp", "") or "",
            )

            total_entries = len(sorted_history)
            earliest_timestamp = getattr(sorted_history[0], "timestamp", None)
            latest_timestamp = getattr(sorted_history[-1], "timestamp", None)

            entries: list[PortfolioHealthTimelineEntry] = []

            for idx, entry in enumerate(sorted_history):
                sequence = idx + 1
                timestamp = str(getattr(entry, "timestamp", ""))
                score = int(getattr(entry, "score", 0))
                grade = str(getattr(entry, "grade", "-"))

                if idx == 0:
                    trend_direction = "STABLE"
                    change_count = 0
                else:
                    prev_entry = sorted_history[idx - 1]
                    prev_score = int(getattr(prev_entry, "score", 0))
                    diff = score - prev_score

                    if diff >= 3:
                        trend_direction = "IMPROVING"
                    elif diff <= -3:
                        trend_direction = "DETERIORATING"
                    else:
                        trend_direction = "STABLE"

                    try:
                        report = self.change_detection_service.detect_changes(
                            history=[prev_entry, entry]
                        )
                        change_count = getattr(report, "total_changes", 0)
                    except Exception:
                        change_count = 0

                entries.append(
                    PortfolioHealthTimelineEntry(
                        sequence=sequence,
                        timestamp=timestamp,
                        score=score,
                        grade=grade,
                        trend_direction=trend_direction,
                        change_count=change_count,
                    )
                )

            return PortfolioHealthTimeline(
                total_entries=total_entries,
                latest_timestamp=latest_timestamp,
                earliest_timestamp=earliest_timestamp,
                entries=entries,
            )
        except Exception:
            return default_timeline
