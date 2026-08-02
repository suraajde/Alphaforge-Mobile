"""Portfolio Performance Service

Provides core portfolio performance measurement logic including absolute return,
benchmark return, alpha, growth multiple, and an XIRR placeholder API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class PortfolioPerformanceSnapshot:
    """Dataclass capturing a point-in-time portfolio performance measurement."""

    initial_value: float
    current_value: float
    absolute_return: float
    absolute_return_pct: float
    initial_benchmark: float
    current_benchmark: float
    benchmark_return_pct: float
    alpha_pct: float
    growth_multiple: float
    xirr_pct: Optional[float] = None
    warnings: List[str] = field(default_factory=list)


class PortfolioPerformanceService:
    """Service that computes portfolio performance metrics relative to initial capital

    and benchmark performance.
    """

    def calculate_performance(
        self,
        initial_value: float,
        current_value: float,
        initial_benchmark: float = 0.0,
        current_benchmark: float = 0.0,
        cash_flows: Optional[List[Any]] = None,
    ) -> PortfolioPerformanceSnapshot:
        """Calculate performance metrics for a portfolio over a measurement period.

        Args:
            initial_value: Starting portfolio value in currency units.
            current_value: Current portfolio value in currency units.
            initial_benchmark: Starting benchmark index/value (optional).
            current_benchmark: Current benchmark index/value (optional).
            cash_flows: Optional list of cash flow transactions for XIRR calculation.

        Returns:
            PortfolioPerformanceSnapshot instance with calculated metrics.
        """
        warnings: List[str] = []

        # 1. Absolute Return & Return %
        absolute_return = current_value - initial_value
        if initial_value > 0:
            absolute_return_pct = (absolute_return / initial_value) * 100.0
            growth_multiple = current_value / initial_value
        else:
            absolute_return_pct = 0.0
            growth_multiple = 0.0
            warnings.append("Initial portfolio value must be greater than 0 to compute return percentage.")

        # 2. Benchmark Return %
        if initial_benchmark > 0:
            benchmark_return = current_benchmark - initial_benchmark
            benchmark_return_pct = (benchmark_return / initial_benchmark) * 100.0
        else:
            benchmark_return_pct = 0.0
            if initial_benchmark < 0:
                warnings.append("Initial benchmark value must be positive.")

        # 3. Alpha %
        alpha_pct = absolute_return_pct - benchmark_return_pct

        # 4. XIRR Placeholder API
        xirr_pct = self.calculate_xirr(cash_flows)

        return PortfolioPerformanceSnapshot(
            initial_value=initial_value,
            current_value=current_value,
            absolute_return=absolute_return,
            absolute_return_pct=absolute_return_pct,
            initial_benchmark=initial_benchmark,
            current_benchmark=current_benchmark,
            benchmark_return_pct=benchmark_return_pct,
            alpha_pct=alpha_pct,
            growth_multiple=growth_multiple,
            xirr_pct=xirr_pct,
            warnings=warnings,
        )

    def calculate_xirr(
        self,
        cash_flows: Optional[List[Any]] = None,
    ) -> Optional[float]:
        """Placeholder API for Extended Internal Rate of Return (XIRR) calculation.

        Future enhancement will calculate money-weighted rate of return based on
        dated cash flow transactions.

        Args:
            cash_flows: Optional list of cash flow events (e.g. (date, amount) tuples).

        Returns:
            None (placeholder API).
        """
        if not cash_flows:
            return None
        # Placeholder for future XIRR calculation engine implementation
        return None
