"""SIP Optimization Engine Service (Sprint 13.8.2)

Provides a structured, factual, deterministic, analytical layer for evaluating the user's existing SIP configuration.
Analyzes actual SIP-sourced transactions from portfolio state history and evaluates SIP coverage, distribution, and alignment metrics.

IMPORTANT SCOPE BOUNDARY & ANALYTICAL BOUNDARY:
- Real data source: Only transactions where source == "SIP" are treated as SIP evidence.
- No inferred recurring schedules: SIP amount per schedule, frequency, and next date are strictly UNAVAILABLE.
- Purely analytical: Provides factual observations (e.g. weight alignment counts).
- NO RECOMMENDATIONS: Does NOT instruct the user to change, start, stop, increase, decrease, or modify any SIP.
- NO EXECUTION / BROKER INTEGRATION.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SIPHoldingAnalysis:
    """Factual SIP analysis metrics for a single portfolio position."""

    symbol: str
    name: str
    target_weight: float = 0.0
    actual_weight: float = 0.0
    drift_pct: float = 0.0
    invested_cost: float = 0.0
    current_value: float = 0.0
    sip_transaction_count: int = 0
    sip_invested_amount: float = 0.0
    sip_analysis_status: str = "UNAVAILABLE"  # "ANALYZED", "NO_SIP_DATA", "UNAVAILABLE"
    sip_amount_per_schedule: str = "UNAVAILABLE"  # Explicitly UNAVAILABLE (no schedule inferred)
    sip_frequency: str = "UNAVAILABLE"  # Explicitly UNAVAILABLE (no schedule inferred)
    sip_next_date: str = "UNAVAILABLE"  # Explicitly UNAVAILABLE (no schedule inferred)


@dataclass
class SIPDistributionMetrics:
    """Summary of SIP distribution across portfolio holdings."""

    total_positions: int = 0
    positions_with_sip: int = 0
    positions_without_sip: int = 0
    sip_coverage_pct: float = 0.0
    sip_concentration_top_pct: float = 0.0
    distribution_status: str = "UNAVAILABLE"  # "ANALYZED", "NO_DATA", "UNAVAILABLE"


@dataclass
class SIPEfficiencyMetrics:
    """Analytical efficiency metrics comparing SIP capital with portfolio state."""

    total_sip_invested: float = 0.0
    total_sip_transactions: int = 0
    average_sip_per_transaction: float = 0.0
    sip_to_portfolio_ratio: float = 0.0
    weight_aligned_positions: int = 0
    weight_misaligned_positions: int = 0
    efficiency_status: str = "UNAVAILABLE"  # "ANALYZED", "NO_DATA", "UNAVAILABLE"
    observation_summary: str = ""  # Strictly factual observations only, no recommendations


@dataclass
class SIPOptimizationResult:
    """Complete container for SIP optimization analysis results."""

    analysis_status: str = "UNAVAILABLE"  # "ANALYZED", "NO_DATA", "UNAVAILABLE", "ERROR"
    total_positions: int = 0
    total_sip_invested: float = 0.0
    total_sip_transactions: int = 0
    holdings: list[SIPHoldingAnalysis] = field(default_factory=list)
    distribution: Optional[SIPDistributionMetrics] = None
    efficiency: Optional[SIPEfficiencyMetrics] = None
    rationale: str = ""


def _empty_result(status: str = "UNAVAILABLE", rationale: str = "") -> SIPOptimizationResult:
    """Return a safe empty SIPOptimizationResult."""
    return SIPOptimizationResult(
        analysis_status=status,
        total_positions=0,
        total_sip_invested=0.0,
        total_sip_transactions=0,
        holdings=[],
        distribution=SIPDistributionMetrics(distribution_status=status),
        efficiency=SIPEfficiencyMetrics(efficiency_status=status),
        rationale=rationale,
    )


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


class SIPOptimizationService:
    """Service layer for computing factual SIP optimization analysis."""

    def __init__(
        self,
        portfolio_state_service: Optional[Any] = None,
        rebalancing_service: Optional[Any] = None,
    ) -> None:
        """Initialize SIPOptimizationService with optional dependencies (Pattern A)."""
        self._portfolio_state_service = portfolio_state_service
        self._rebalancing_service = rebalancing_service

    def _get_portfolio_state_service(self) -> Optional[Any]:
        """Safely retrieve or instantiate PortfolioStateService."""
        if self._portfolio_state_service is not None:
            return self._portfolio_state_service
        try:
            from services.portfolio_state_service import PortfolioStateService
            return PortfolioStateService()
        except Exception:
            return None

    def _get_rebalancing_service(self) -> Optional[Any]:
        """Safely retrieve or instantiate RebalancingService."""
        if self._rebalancing_service is not None:
            return self._rebalancing_service
        try:
            from services.rebalancing_service import RebalancingService
            return RebalancingService()
        except Exception:
            return None

    def _extract_sip_transactions(self, state: dict) -> list[dict]:
        """Extract transactions from portfolio state where source == 'SIP'."""
        if not isinstance(state, dict):
            return []
        raw_txns = state.get("transactions", [])
        if not isinstance(raw_txns, list):
            return []

        sip_txns = []
        for txn in raw_txns:
            if isinstance(txn, dict) and str(txn.get("source", "")).strip().upper() == "SIP":
                sip_txns.append(txn)
        return sip_txns

    def _analyze_holding(
        self,
        symbol: str,
        pos_data: dict,
        sip_txns: list[dict],
    ) -> SIPHoldingAnalysis:
        """Perform factual analysis of SIP history for a single position."""
        name = str(pos_data.get("company_name", pos_data.get("name", symbol))).strip()
        target_weight = _safe_float(pos_data.get("target_weight"), 0.0)
        actual_weight = _safe_float(pos_data.get("actual_weight", pos_data.get("current_weight")), 0.0)
        drift_pct = _safe_float(pos_data.get("drift_pct"), 0.0)
        invested_cost = _safe_float(pos_data.get("invested_cost"), 0.0)
        current_value = _safe_float(pos_data.get("current_value"), 0.0)

        # Filter SIP transactions for this symbol
        symbol_sip_txns = [
            t for t in sip_txns
            if str(t.get("symbol", "")).strip().upper() == symbol.upper()
        ]
        tx_count = len(symbol_sip_txns)
        tx_amount = sum(_safe_float(t.get("amount"), 0.0) for t in symbol_sip_txns)

        status = "ANALYZED" if tx_count > 0 else "NO_SIP_DATA"

        return SIPHoldingAnalysis(
            symbol=symbol,
            name=name,
            target_weight=round(target_weight, 4),
            actual_weight=round(actual_weight, 4),
            drift_pct=round(drift_pct, 4),
            invested_cost=round(invested_cost, 2),
            current_value=round(current_value, 2),
            sip_transaction_count=tx_count,
            sip_invested_amount=round(tx_amount, 2),
            sip_analysis_status=status,
            sip_amount_per_schedule="UNAVAILABLE",
            sip_frequency="UNAVAILABLE",
            sip_next_date="UNAVAILABLE",
        )

    def _compute_distribution(
        self,
        holdings: list[SIPHoldingAnalysis],
    ) -> SIPDistributionMetrics:
        """Compute SIP coverage and concentration across positions."""
        total = len(holdings)
        if total == 0:
            return SIPDistributionMetrics(distribution_status="NO_DATA")

        with_sip = sum(1 for h in holdings if h.sip_transaction_count > 0)
        without_sip = total - with_sip
        coverage_pct = (with_sip / total * 100.0) if total > 0 else 0.0

        total_sip_amount = sum(h.sip_invested_amount for h in holdings)
        top_sip_amount = max((h.sip_invested_amount for h in holdings), default=0.0)
        concentration_pct = (top_sip_amount / total_sip_amount * 100.0) if total_sip_amount > 0 else 0.0

        status = "ANALYZED" if with_sip > 0 else "NO_DATA"

        return SIPDistributionMetrics(
            total_positions=total,
            positions_with_sip=with_sip,
            positions_without_sip=without_sip,
            sip_coverage_pct=round(coverage_pct, 2),
            sip_concentration_top_pct=round(concentration_pct, 2),
            distribution_status=status,
        )

    def _compute_efficiency(
        self,
        holdings: list[SIPHoldingAnalysis],
        portfolio_invested_cost: float,
    ) -> SIPEfficiencyMetrics:
        """Compute SIP efficiency metrics relative to portfolio state."""
        total_sip_invested = sum(h.sip_invested_amount for h in holdings)
        total_sip_txns = sum(h.sip_transaction_count for h in holdings)

        avg_per_tx = (total_sip_invested / total_sip_txns) if total_sip_txns > 0 else 0.0
        ratio = (total_sip_invested / portfolio_invested_cost * 100.0) if portfolio_invested_cost > 0 else 0.0

        # Alignment threshold: drift within +/- 2.0% is considered weight-aligned
        aligned_count = 0
        misaligned_count = 0
        for h in holdings:
            if abs(h.drift_pct) <= 2.0:
                aligned_count += 1
            else:
                misaligned_count += 1

        status = "ANALYZED" if total_sip_txns > 0 else "NO_DATA"

        # Factual analytical observation summary — strictly NO recommendations
        if total_sip_txns > 0:
            obs = f"{aligned_count} positions aligned with target weights; {misaligned_count} positions materially misaligned."
        else:
            obs = "No SIP transactions recorded in portfolio history."

        return SIPEfficiencyMetrics(
            total_sip_invested=round(total_sip_invested, 2),
            total_sip_transactions=total_sip_txns,
            average_sip_per_transaction=round(avg_per_tx, 2),
            sip_to_portfolio_ratio=round(ratio, 2),
            weight_aligned_positions=aligned_count,
            weight_misaligned_positions=misaligned_count,
            efficiency_status=status,
            observation_summary=obs,
        )

    def analyze_sip(self, state_input: Optional[Any] = None) -> SIPOptimizationResult:
        """Main entry point to perform SIP optimization analysis defensively."""
        try:
            state = None
            if isinstance(state_input, dict):
                state = state_input
            elif state_input is not None and hasattr(state_input, "get") and callable(state_input.get):
                state = state_input
            else:
                # Load from PortfolioStateService
                state_svc = self._get_portfolio_state_service()
                if state_svc is not None and hasattr(state_svc, "load_state"):
                    try:
                        state = state_svc.load_state()
                    except Exception:
                        state = None

            if not isinstance(state, dict) or not state:
                return _empty_result(
                    status="UNAVAILABLE",
                    rationale="No valid portfolio state available for SIP optimization analysis.",
                )

            # Unwrap nested state payload if state was loaded via load_state() wrapper dict
            if "state" in state and isinstance(state["state"], dict):
                state = state["state"]

            positions_dict = state.get("positions", {})
            if not isinstance(positions_dict, dict) or not positions_dict:
                return _empty_result(
                    status="NO_DATA",
                    rationale="Portfolio contains no positions to analyze.",
                )

            sip_txns = self._extract_sip_transactions(state)

            holdings: list[SIPHoldingAnalysis] = []
            for symbol, pos_data in positions_dict.items():
                if isinstance(pos_data, dict):
                    holdings.append(self._analyze_holding(symbol, pos_data, sip_txns))

            dist_metrics = self._compute_distribution(holdings)

            portfolio_invested_cost = sum(_safe_float(p.get("invested_cost")) for p in positions_dict.values() if isinstance(p, dict))
            eff_metrics = self._compute_efficiency(holdings, portfolio_invested_cost)

            total_sip_invested = sum(h.sip_invested_amount for h in holdings)
            total_sip_txns = sum(h.sip_transaction_count for h in holdings)

            status = "ANALYZED" if total_sip_txns > 0 else "NO_DATA"
            rat = (
                f"Analyzed {len(holdings)} positions; {len(sip_txns)} SIP transactions found."
                if total_sip_txns > 0
                else "No historical SIP configuration recorded."
            )

            return SIPOptimizationResult(
                analysis_status=status,
                total_positions=len(holdings),
                total_sip_invested=round(total_sip_invested, 2),
                total_sip_transactions=total_sip_txns,
                holdings=holdings,
                distribution=dist_metrics,
                efficiency=eff_metrics,
                rationale=rat,
            )

        except Exception as exc:
            return _empty_result(
                status="ERROR",
                rationale=f"Error analyzing SIP configuration: {str(exc)}",
            )

    def get_sip_analysis(self, state_input: Optional[Any] = None) -> SIPOptimizationResult:
        """Alias interface for fetching SIP optimization analysis."""
        return self.analyze_sip(state_input=state_input)
