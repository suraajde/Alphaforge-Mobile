"""Investment Allocation Service (Sprint 14.1.1)

Provides dynamic, new-money allocation calculations for Monthly Investment Allocation
and Lump-Sum Investment Allocation across the Alpha 12 portfolio framework.

Scope Boundary:
- Purely analytical allocation proposals.
- NO automatic selling or rebalancing.
- NO order/broker execution.
- Sum of proposed stock allocations MUST equal EXACTLY the user's input amount.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from services.universe_service import UniverseService
from services.portfolio_state_service import PortfolioStateService


@dataclass
class AllocationItem:
    """Analytical allocation proposal for a single stock."""
    symbol: str
    company_name: str
    alpha12_rank: int
    conviction: float
    current_weight_pct: float
    target_weight_pct: float = 8.33
    expected_weight_pct: float = 8.33
    suggested_amount: float = 0.0
    suggested_pct: float = 0.0
    reference_price: float = 0.0
    quantity: int = 0
    reason: str = ""


@dataclass
class InvestmentAllocationResult:
    """Container for complete Monthly or Lump-Sum Investment Allocation proposal."""
    allocation_type: str  # "MONTHLY" or "LUMP_SUM"
    total_input_amount: float
    total_allocated_amount: float
    allocations: List[AllocationItem] = field(default_factory=list)
    summary_rationale: str = ""


class InvestmentAllocationService:
    """Service providing dynamic investment allocation proposals across Alpha 12 stocks."""

    def __init__(
        self,
        universe_service: Optional[UniverseService] = None,
        state_service: Optional[PortfolioStateService] = None,
        price_provider: Optional[Callable[[str], Dict[str, Any]]] = None,
    ) -> None:
        self.universe_service = universe_service or UniverseService()
        self.state_service = state_service or PortfolioStateService()
        self.price_provider = price_provider

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _resolve_reference_price(
        self,
        symbol: str,
        positions: Dict[str, Any],
    ) -> float:
        """Prefer the portfolio price, then use the UI-supplied market-price provider."""
        pos_info = positions.get(symbol, {}) if isinstance(positions, dict) else {}
        if isinstance(pos_info, dict):
            for field_name in ("current_price", "price", "ltp"):
                price = self._safe_float(pos_info.get(field_name), 0.0)
                if price > 0:
                    return round(price, 2)

        if not callable(self.price_provider):
            return 0.0

        try:
            market_data = self.price_provider(symbol)
        except Exception:
            return 0.0

        if not isinstance(market_data, dict) or market_data.get("error"):
            return 0.0

        price = self._safe_float(market_data.get("price"), 0.0)
        return round(price, 2) if price > 0 else 0.0

    def _apply_reference_prices_and_quantities(
        self,
        allocations: List[AllocationItem],
        positions: Dict[str, Any],
    ) -> None:
        """Attach executable whole-share quantities without changing monetary allocations."""
        for item in allocations:
            item.reference_price = self._resolve_reference_price(item.symbol, positions)
            item.quantity = (
                math.floor(item.suggested_amount / item.reference_price)
                if item.reference_price > 0
                else 0
            )

    def _get_alpha12_candidates(self) -> List[Dict[str, Any]]:
        """Retrieve top 12 production candidates from stock universe."""
        res = self.universe_service.get_enabled_stocks()
        stocks = res.get("stocks", [])
        if not stocks:
            return []

        # Sort by conviction score if available, else rank/symbol
        candidates = stocks[:12]
        formatted = []
        for i, s in enumerate(candidates, start=1):
            symbol = str(s.get("symbol", f"STOCK_{i}")).strip().upper()
            company = str(s.get("company", s.get("company_name", symbol))).strip()
            category = str(s.get("category", "MIDCAP")).strip().upper()

            # Base conviction calculation based on rank
            conviction = max(60.0, round(95.0 - (i - 1) * 2.5, 1))

            formatted.append({
                "symbol": symbol,
                "company_name": company,
                "rank": i,
                "category": category,
                "conviction": conviction,
                "target_weight": round(100.0 / 12.0, 2),
            })
        return formatted

    def allocate_monthly_investment(
        self,
        total_amount: float,
        portfolio_state: Optional[Dict[str, Any]] = None,
    ) -> InvestmentAllocationResult:
        """Calculate dynamic Monthly Investment new-money allocation across Alpha 12 stocks.

        New-money principle:
        - Does NOT sell incumbents.
        - Overrepresented incumbents receive reduced or zero new money allocation.
        - Underrepresented or high-conviction candidates receive higher new money allocation.
        - Sum of allocations equals EXACTLY total_amount.
        """
        if total_amount <= 0:
            return InvestmentAllocationResult(
                allocation_type="MONTHLY",
                total_input_amount=0.0,
                total_allocated_amount=0.0,
                allocations=[],
                summary_rationale="Please enter a valid monthly investment amount greater than ₹0.",
            )

        if portfolio_state is None:
            state_res = self.state_service.load_state()
            portfolio_state = state_res.get("state", {}) if isinstance(state_res, dict) and state_res.get("state") else {}

        if not isinstance(portfolio_state, dict):
            portfolio_state = {}

        positions = portfolio_state.get("positions", {}) if isinstance(portfolio_state, dict) else {}
        total_val = float(portfolio_state.get("total_portfolio_value", 0.0))

        candidates = self._get_alpha12_candidates()
        if not candidates:
            return InvestmentAllocationResult(
                allocation_type="MONTHLY",
                total_input_amount=total_amount,
                total_allocated_amount=0.0,
                allocations=[],
                summary_rationale="No stock universe candidates available for allocation.",
            )

        # 1. Compute raw allocation weights based on conviction & underrepresentation
        raw_scores = []
        for cand in candidates:
            sym = cand["symbol"]
            rank = cand["rank"]
            conv = cand["conviction"]

            # Current weight in existing portfolio
            pos_info = positions.get(sym, {}) if isinstance(positions, dict) else {}
            curr_weight = float(pos_info.get("actual_weight", pos_info.get("current_weight", 0.0)))

            target_weight = 100.0 / len(candidates)
            underrep_bonus = max(0.0, target_weight - curr_weight)

            # Raw score = base conviction weight + underrepresentation bonus
            score = max(1.0, (13 - rank) * 10.0 + conv * 0.5 + underrep_bonus * 3.0)
            raw_scores.append((cand, curr_weight, score))

        total_score = sum(s[2] for s in raw_scores)

        # 2. Allocate integer rupees, ensuring total equals EXACTLY total_amount
        allocations: List[AllocationItem] = []
        allocated_so_far = 0.0

        for idx, (cand, curr_weight, score) in enumerate(raw_scores):
            is_last = (idx == len(raw_scores) - 1)
            if is_last:
                item_amt = max(0.0, round(total_amount - allocated_so_far, 2))
            else:
                pct_share = score / total_score if total_score > 0 else (1.0 / len(candidates))
                item_amt = round((total_amount * pct_share) / 100.0) * 100.0  # Round to nearest ₹100
                item_amt = min(item_amt, max(0.0, total_amount - allocated_so_far))

            allocated_so_far += item_amt
            item_pct = (item_amt / total_amount * 100.0) if total_amount > 0 else 0.0

            # Calculate expected resulting weight
            curr_pos_val = float(pos_info.get("market_value", pos_info.get("invested_cost", 0.0)))
            new_pos_val = curr_pos_val + item_amt
            new_total_val = total_val + total_amount
            expected_wt = (new_pos_val / new_total_val * 100.0) if new_total_val > 0 else item_pct

            # Generate factual reason
            rank = cand["rank"]
            conv = cand["conviction"]
            if curr_weight == 0.0:
                reason = f"Alpha 12 Rank #{rank} (Conviction: {conv:.1f}%). New position allocation."
            elif curr_weight < target_weight:
                reason = f"Alpha 12 Rank #{rank} (Conviction: {conv:.1f}%). Currently underrepresented ({curr_weight:.1f}% weight vs target {target_weight:.1f}%)."
            else:
                reason = f"Alpha 12 Rank #{rank} (Conviction: {conv:.1f}%). Core incumbent position ({curr_weight:.1f}% weight)."

            allocations.append(
                AllocationItem(
                    symbol=cand["symbol"],
                    company_name=cand["company_name"],
                    alpha12_rank=rank,
                    conviction=conv,
                    current_weight_pct=round(curr_weight, 2),
                    target_weight_pct=round(target_weight, 2),
                    expected_weight_pct=round(expected_wt, 2),
                    suggested_amount=item_amt,
                    suggested_pct=round(item_pct, 1),
                    reason=reason,
                )
            )

        # Exact adjustments if rounding created a tiny mismatch
        diff = total_amount - sum(a.suggested_amount for a in allocations)
        if abs(diff) > 0.001 and allocations:
            allocations[0].suggested_amount += diff
            allocations[0].suggested_pct = round(allocations[0].suggested_amount / total_amount * 100.0, 1)

        self._apply_reference_prices_and_quantities(allocations, positions)

        total_alloc = sum(a.suggested_amount for a in allocations)

        return InvestmentAllocationResult(
            allocation_type="MONTHLY",
            total_input_amount=total_amount,
            total_allocated_amount=round(total_alloc, 2),
            allocations=allocations,
            summary_rationale=f"NEW MONEY DEPLOYMENT: Monthly investment of ₹{total_amount:,.2f} dynamically allocated across Alpha 12 candidates without selling incumbents.",
        )

    def allocate_lump_sum_investment(
        self,
        total_amount: float,
        portfolio_state: Optional[Dict[str, Any]] = None,
    ) -> InvestmentAllocationResult:
        """Calculate dynamic Lump-Sum Investment allocation across Alpha 12 stocks.

        Sum of allocations equals EXACTLY total_amount.
        """
        if total_amount <= 0:
            return InvestmentAllocationResult(
                allocation_type="LUMP_SUM",
                total_input_amount=0.0,
                total_allocated_amount=0.0,
                allocations=[],
                summary_rationale="Please enter a valid lump-sum investment amount greater than ₹0.",
            )

        if portfolio_state is None:
            state_res = self.state_service.load_state()
            portfolio_state = state_res.get("state", {}) if isinstance(state_res, dict) and state_res.get("state") else {}

        if not isinstance(portfolio_state, dict):
            portfolio_state = {}

        positions = portfolio_state.get("positions", {}) if isinstance(portfolio_state, dict) else {}

        candidates = self._get_alpha12_candidates()
        if not candidates:
            return InvestmentAllocationResult(
                allocation_type="LUMP_SUM",
                total_input_amount=total_amount,
                total_allocated_amount=0.0,
                allocations=[],
                summary_rationale="No stock universe candidates available for allocation.",
            )

        raw_scores = []
        for cand in candidates:
            sym = cand["symbol"]
            rank = cand["rank"]
            conv = cand["conviction"]

            pos_info = positions.get(sym, {}) if isinstance(positions, dict) else {}
            curr_weight = float(pos_info.get("actual_weight", pos_info.get("current_weight", 0.0)))

            # Higher rank stocks get higher lump-sum allocation
            score = (13 - rank) * 15.0 + conv
            raw_scores.append((cand, curr_weight, score))

        total_score = sum(s[2] for s in raw_scores)

        allocations: List[AllocationItem] = []
        allocated_so_far = 0.0

        for idx, (cand, curr_weight, score) in enumerate(raw_scores):
            is_last = (idx == len(raw_scores) - 1)
            if is_last:
                item_amt = max(0.0, round(total_amount - allocated_so_far, 2))
            else:
                pct_share = score / total_score if total_score > 0 else (1.0 / len(candidates))
                item_amt = round((total_amount * pct_share) / 500.0) * 500.0  # Round to nearest ₹500
                item_amt = min(item_amt, max(0.0, total_amount - allocated_so_far))

            allocated_so_far += item_amt
            item_pct = (item_amt / total_amount * 100.0) if total_amount > 0 else 0.0

            target_weight = 100.0 / len(candidates)
            total_val = float(portfolio_state.get("total_portfolio_value", 0.0))
            pos_info = positions.get(cand["symbol"], {}) if isinstance(positions, dict) else {}
            curr_pos_val = float(pos_info.get("market_value", pos_info.get("invested_cost", 0.0)))
            new_pos_val = curr_pos_val + item_amt
            new_total_val = total_val + total_amount
            expected_wt = (new_pos_val / new_total_val * 100.0) if new_total_val > 0 else item_pct

            rank = cand["rank"]
            conv = cand["conviction"]
            reason = f"Alpha 12 Rank #{rank} (Conviction: {conv:.1f}%). Lump-sum strategic allocation."

            allocations.append(
                AllocationItem(
                    symbol=cand["symbol"],
                    company_name=cand["company_name"],
                    alpha12_rank=rank,
                    conviction=conv,
                    current_weight_pct=round(curr_weight, 2),
                    target_weight_pct=round(target_weight, 2),
                    expected_weight_pct=round(expected_wt, 2),
                    suggested_amount=item_amt,
                    suggested_pct=round(item_pct, 1),
                    reason=reason,
                )
            )

        diff = total_amount - sum(a.suggested_amount for a in allocations)
        if abs(diff) > 0.001 and allocations:
            allocations[0].suggested_amount += diff
            allocations[0].suggested_pct = round(allocations[0].suggested_amount / total_amount * 100.0, 1)

        self._apply_reference_prices_and_quantities(allocations, positions)

        total_alloc = sum(a.suggested_amount for a in allocations)

        return InvestmentAllocationResult(
            allocation_type="LUMP_SUM",
            total_input_amount=total_amount,
            total_allocated_amount=round(total_alloc, 2),
            allocations=allocations,
            summary_rationale=f"NEW MONEY DEPLOYMENT: Lump-sum investment of ₹{total_amount:,.2f} dynamically allocated across Alpha 12 candidates.",
        )
