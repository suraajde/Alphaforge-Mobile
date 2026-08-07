"""Portfolio Health Change Detection Service (Sprint 13.4.1)

Compares consecutive Portfolio Health snapshots and detects factual changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from services.portfolio_health_history_service import PortfolioHealthHistoryService


@dataclass
class PortfolioHealthChange:
    field_name: str
    previous_value: str
    current_value: str
    change_type: str


@dataclass
class PortfolioHealthChangeReport:
    snapshot_count: int
    total_changes: int
    has_changes: bool
    changes: list[PortfolioHealthChange]


class PortfolioHealthChangeDetectionService:
    """Service for comparing portfolio health snapshots and generating change detection reports."""

    def __init__(self, history_service: Optional[PortfolioHealthHistoryService] = None) -> None:
        self.history_service = history_service if history_service is not None else PortfolioHealthHistoryService()

    def detect_changes(self, history: Optional[list[Any]] = None) -> PortfolioHealthChangeReport:
        """Detects changes between the latest and previous portfolio health snapshots safely."""
        default_report = PortfolioHealthChangeReport(
            snapshot_count=0,
            total_changes=0,
            has_changes=False,
            changes=[],
        )

        try:
            if history is None:
                if self.history_service is None:
                    return default_report
                try:
                    history = self.history_service.get_history()
                except Exception:
                    return default_report

            if not isinstance(history, list) or len(history) < 2:
                snapshot_cnt = len(history) if isinstance(history, list) else 0
                return PortfolioHealthChangeReport(
                    snapshot_count=snapshot_cnt,
                    total_changes=0,
                    has_changes=False,
                    changes=[],
                )

            prev_entry = history[-2]
            curr_entry = history[-1]

            changes: list[PortfolioHealthChange] = []

            # 1. Health Score (Numeric)
            prev_score = int(getattr(prev_entry, "score", 0))
            curr_score = int(getattr(curr_entry, "score", 0))
            changes.append(
                self._compare_numeric("Health Score", prev_score, curr_score)
            )

            # 2. Grade (Text)
            prev_grade = str(getattr(prev_entry, "grade", "-"))
            curr_grade = str(getattr(curr_entry, "grade", "-"))
            changes.append(
                self._compare_text("Grade", prev_grade, curr_grade)
            )

            # 3. Diversification Rating (Text)
            prev_div = str(getattr(prev_entry, "diversification_rating", "N/A"))
            curr_div = str(getattr(curr_entry, "diversification_rating", "N/A"))
            changes.append(
                self._compare_text("Diversification Rating", prev_div, curr_div)
            )

            # 4. Concentration Rating (Text)
            prev_conc = str(getattr(prev_entry, "concentration_rating", "N/A"))
            curr_conc = str(getattr(curr_entry, "concentration_rating", "N/A"))
            changes.append(
                self._compare_text("Concentration Rating", prev_conc, curr_conc)
            )

            # 5. Cash Allocation (Numeric)
            prev_cash = float(getattr(prev_entry, "cash_allocation_pct", 0.0))
            curr_cash = float(getattr(curr_entry, "cash_allocation_pct", 0.0))
            changes.append(
                self._compare_numeric_pct("Cash Allocation", prev_cash, curr_cash)
            )

            # 6. Position Count (Numeric)
            prev_pos = int(getattr(prev_entry, "position_count", 0))
            curr_pos = int(getattr(curr_entry, "position_count", 0))
            changes.append(
                self._compare_numeric("Position Count", prev_pos, curr_pos)
            )

            # 7. Largest Position (Text)
            prev_lpos = str(getattr(prev_entry, "largest_position", "N/A"))
            curr_lpos = str(getattr(curr_entry, "largest_position", "N/A"))
            changes.append(
                self._compare_text("Largest Position", prev_lpos, curr_lpos)
            )

            # 8. Largest Position Weight (Numeric)
            prev_lweight = float(getattr(prev_entry, "largest_position_weight_pct", 0.0))
            curr_lweight = float(getattr(curr_entry, "largest_position_weight_pct", 0.0))
            changes.append(
                self._compare_numeric_pct("Largest Position Weight", prev_lweight, curr_lweight)
            )

            total_changes = sum(1 for c in changes if c.change_type != "UNCHANGED")
            has_changes = total_changes > 0

            return PortfolioHealthChangeReport(
                snapshot_count=2,
                total_changes=total_changes,
                has_changes=has_changes,
                changes=changes,
            )
        except Exception:
            return default_report

    @staticmethod
    def _compare_numeric(field_name: str, prev_val: int | float, curr_val: int | float) -> PortfolioHealthChange:
        if curr_val > prev_val:
            change_type = "INCREASED"
        elif curr_val < prev_val:
            change_type = "DECREASED"
        else:
            change_type = "UNCHANGED"

        return PortfolioHealthChange(
            field_name=field_name,
            previous_value=str(prev_val),
            current_value=str(curr_val),
            change_type=change_type,
        )

    @staticmethod
    def _compare_numeric_pct(field_name: str, prev_val: float, curr_val: float) -> PortfolioHealthChange:
        if curr_val > prev_val:
            change_type = "INCREASED"
        elif curr_val < prev_val:
            change_type = "DECREASED"
        else:
            change_type = "UNCHANGED"

        prev_str = f"{int(prev_val)}%" if (prev_val % 1 == 0) else f"{prev_val:.1f}%"
        curr_str = f"{int(curr_val)}%" if (curr_val % 1 == 0) else f"{curr_val:.1f}%"

        return PortfolioHealthChange(
            field_name=field_name,
            previous_value=prev_str,
            current_value=curr_str,
            change_type=change_type,
        )

    @staticmethod
    def _compare_text(field_name: str, prev_val: str, curr_val: str) -> PortfolioHealthChange:
        if curr_val != prev_val:
            change_type = "CHANGED"
        else:
            change_type = "UNCHANGED"

        return PortfolioHealthChange(
            field_name=field_name,
            previous_value=prev_val,
            current_value=curr_val,
            change_type=change_type,
        )
