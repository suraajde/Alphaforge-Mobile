"""Portfolio Health Service Foundation (Sprint 13.3.0B.1)

Provides a single source of truth service layer for calculating basic Portfolio Health metrics
and returning a PortfolioHealthSnapshot.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)


@dataclass
class PortfolioHealth:
    overall_score: int
    overall_grade: str
    diversification_score: int
    concentration_score: int
    position_sizing_score: int
    weight_balance_score: int
    portfolio_structure_score: int
    recommendation: str


@dataclass
class PortfolioHealthSnapshot:
    position_count: int
    portfolio_value: float
    invested_value: float
    cash_allocation_pct: float
    largest_position: str
    largest_position_weight_pct: float


class PortfolioHealthService:
    """Service layer for computing portfolio health metrics and snapshots safely."""

    def __init__(self, portfolio_app_service: Optional[Any] = None) -> None:
        """Initialize PortfolioHealthService.

        Args:
            portfolio_app_service: Optional instance or provider of PortfolioApplicationService
                or similar portfolio data service.
        """
        self._portfolio_app_service = portfolio_app_service

    def build_snapshot(self) -> PortfolioHealthSnapshot:
        """Build and return a portfolio health snapshot safely without exceptions.

        Returns:
            PortfolioHealthSnapshot containing calculated portfolio metrics.
        """
        try:
            return self._calculate_snapshot()
        except Exception:
            # Defensive fallback ensuring no uncaught exceptions
            return PortfolioHealthSnapshot(
                position_count=0,
                portfolio_value=0.0,
                invested_value=0.0,
                cash_allocation_pct=0.0,
                largest_position="N/A",
                largest_position_weight_pct=0.0,
            )

    def _calculate_snapshot(self) -> PortfolioHealthSnapshot:
        app_service = self._get_app_service()
        if app_service is None:
            return PortfolioHealthSnapshot(
                position_count=0,
                portfolio_value=0.0,
                invested_value=0.0,
                cash_allocation_pct=0.0,
                largest_position="N/A",
                largest_position_weight_pct=0.0,
            )

        status_res = getattr(app_service, "get_status", lambda: {})()
        if not isinstance(status_res, dict) or status_res.get("status") != "OK":
            return PortfolioHealthSnapshot(
                position_count=0,
                portfolio_value=0.0,
                invested_value=0.0,
                cash_allocation_pct=0.0,
                largest_position="N/A",
                largest_position_weight_pct=0.0,
            )

        state = status_res.get("state")
        if not isinstance(state, dict):
            pos_count = self._safe_int(status_res.get("position_count"), 0)
            port_val = self._safe_float(status_res.get("portfolio_value"), 0.0)
            inv_val = self._safe_float(status_res.get("invested_market_value"), 0.0)
            cash_bal = self._safe_float(status_res.get("cash_balance"), 0.0)

            cash_pct = (cash_bal / port_val * 100.0) if port_val > 0 else 0.0
            return PortfolioHealthSnapshot(
                position_count=pos_count,
                portfolio_value=round(port_val, 2),
                invested_value=round(inv_val, 2),
                cash_allocation_pct=round(cash_pct, 2),
                largest_position="N/A",
                largest_position_weight_pct=0.0,
            )

        positions = state.get("positions", {})
        if not isinstance(positions, dict):
            positions = {}

        cash_balance = self._safe_float(state.get("cash_balance"), 0.0)

        active_positions = []
        total_invested_value = 0.0
        total_current_market_value = 0.0

        for symbol_key, pos_data in positions.items():
            if not isinstance(pos_data, dict):
                continue

            symbol = str(pos_data.get("symbol", symbol_key)).strip().upper()
            if not symbol:
                continue

            qty = self._safe_float(pos_data.get("quantity"), 0.0)
            price = self._safe_float(pos_data.get("current_price"), 0.0)
            invested_cost = self._safe_float(pos_data.get("invested_cost"), 0.0)
            current_val = self._safe_float(pos_data.get("current_value"), 0.0)

            if current_val <= 0 and price > 0 and qty > 0:
                current_val = qty * price

            val = current_val if current_val > 0 else invested_cost

            total_invested_value += invested_cost
            total_current_market_value += current_val

            if qty > 0 or val > 0:
                active_positions.append({
                    "symbol": symbol,
                    "quantity": qty,
                    "value": val,
                    "actual_weight": self._safe_float(pos_data.get("actual_weight"), 0.0),
                })

        total_portfolio_value = self._safe_float(
            state.get("total_portfolio_value", state.get("portfolio_value")),
            total_current_market_value + cash_balance,
        )

        if total_portfolio_value <= 0:
            total_portfolio_value = total_invested_value + cash_balance

        position_count = len(active_positions)

        if total_portfolio_value > 0:
            cash_pct = (cash_balance / total_portfolio_value) * 100.0
        else:
            cash_pct = 0.0

        largest_position = "N/A"
        largest_weight_pct = 0.0

        if active_positions:
            active_positions.sort(key=lambda p: p["value"], reverse=True)
            top = active_positions[0]
            largest_position = top["symbol"]

            if total_portfolio_value > 0:
                largest_weight_pct = (top["value"] / total_portfolio_value) * 100.0
            elif top["actual_weight"] > 0:
                largest_weight_pct = top["actual_weight"]

        return PortfolioHealthSnapshot(
            position_count=position_count,
            portfolio_value=round(total_portfolio_value, 2),
            invested_value=round(total_invested_value, 2),
            cash_allocation_pct=round(cash_pct, 2),
            largest_position=largest_position,
            largest_position_weight_pct=round(largest_weight_pct, 2),
        )

    def evaluate(
        self,
        analytics: PortfolioAnalytics,
    ) -> PortfolioHealth:
        """Converts PortfolioAnalytics into a portfolio health assessment."""
        diversification_score = 20
        concentration_score = 20
        position_sizing_score = 20
        weight_balance_score = 20
        portfolio_structure_score = 20

        if analytics.diversification_grade == "B":
            diversification_score = 18
        elif analytics.diversification_grade == "C":
            diversification_score = 15
        elif analytics.diversification_grade == "D":
            diversification_score = 10

        if analytics.concentration_risk == "Moderate":
            concentration_score = 18
        elif analytics.concentration_risk == "High":
            concentration_score = 15
        elif analytics.concentration_risk == "Very High":
            concentration_score = 10

        if analytics.largest_weight > 20:
            position_sizing_score -= 2

        if analytics.largest_weight > 25:
            position_sizing_score -= 3

        if analytics.largest_weight > 30:
            position_sizing_score -= 5

        if analytics.weight_range > 15:
            weight_balance_score -= 2

        if analytics.weight_range > 20:
            weight_balance_score -= 3

        if analytics.weight_range > 30:
            weight_balance_score -= 5

        if analytics.holding_count < 10:
            portfolio_structure_score = 17

        if analytics.holding_count < 8:
            portfolio_structure_score = 15

        if analytics.holding_count < 6:
            portfolio_structure_score = 12

        overall_score = (
            diversification_score
            + concentration_score
            + position_sizing_score
            + weight_balance_score
            + portfolio_structure_score
        )

        if overall_score >= 90:
            overall_grade = "A"
            recommendation = (
                "Healthy portfolio. "
                "No immediate rebalance required."
            )
        elif overall_score >= 80:
            overall_grade = "B"
            recommendation = (
                "Good portfolio. "
                "Minor optimisation recommended."
            )
        elif overall_score >= 70:
            overall_grade = "C"
            recommendation = (
                "Portfolio should be reviewed."
            )
        else:
            overall_grade = "D"
            recommendation = (
                "Portfolio requires rebalancing."
            )

        return PortfolioHealth(
            overall_score=overall_score,
            overall_grade=overall_grade,
            diversification_score=diversification_score,
            concentration_score=concentration_score,
            position_sizing_score=position_sizing_score,
            weight_balance_score=weight_balance_score,
            portfolio_structure_score=portfolio_structure_score,
            recommendation=recommendation,
        )

    def _get_app_service(self) -> Optional[Any]:
        if self._portfolio_app_service is not None:
            return self._portfolio_app_service

        try:
            from services.portfolio_application_service import (
                create_portfolio_application_service,
            )
            return create_portfolio_application_service()
        except Exception:
            try:
                from services.portfolio_application_service import (
                    PortfolioApplicationService,
                )
                return PortfolioApplicationService()
            except Exception:
                return None

    @staticmethod
    def _safe_float(val: Any, default: float = 0.0) -> float:
        try:
            if val is None:
                return default
            return float(val)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(val: Any, default: int = 0) -> int:
        try:
            if val is None:
                return default
            return int(val)
        except (TypeError, ValueError):
            return default