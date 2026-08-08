"""Allocation Analysis Engine Service (Sprint 13.7.1)



Provides descriptive asset, fund, and ETF allocation analysis from existing

Rebalancing Foundation portfolio data.

"""

from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Optional





@dataclass

class AllocationCategory:

    """Represents a grouped allocation category within a portfolio breakdown."""



    name: str

    current_value: float

    current_weight: float

    position_count: int





@dataclass

class AllocationAnalysisResult:

    """Complete allocation analysis container with asset, fund, and ETF breakdowns."""



    total_value: float

    asset_allocations: list[AllocationCategory] = field(default_factory=list)

    fund_allocations: list[AllocationCategory] = field(default_factory=list)

    etf_allocations: list[AllocationCategory] = field(default_factory=list)





def _empty_result() -> AllocationAnalysisResult:

    """Return a safe empty AllocationAnalysisResult."""

    return AllocationAnalysisResult(

        total_value=0.0,

        asset_allocations=[],

        fund_allocations=[],

        etf_allocations=[],

    )





def _is_valid_position(pos: Any) -> bool:

    """Safely check if an object is a valid position record."""

    if pos is None:

        return False

    if isinstance(pos, (str, int, float, bool, list, tuple, set)):

        return False

    return True





def _safe_float(val: Any, default: float = 0.0) -> float:

    """Safely convert value to float."""

    try:

        if val is None:

            return default

        return float(val)

    except (TypeError, ValueError):

        return default





class AllocationAnalysisService:

    """Service for analyzing asset, fund, and ETF portfolio allocations.



    Operates purely as a descriptive analysis engine on existing RebalancingState data.

    Does NOT calculate drift, recommend changes, or generate trade candidates.

    """



    # Asset type classification helpers

    FUND_TYPES = {"FUND", "MUTUAL_FUND", "MUTUAL FUND", "INDEX_FUND"}

    ETF_TYPES = {"ETF", "EXCHANGE_TRADED_FUND", "EXCHANGE TRADED FUND"}



    def __init__(self, rebalancing_service: Optional[Any] = None) -> None:

        """Initialize AllocationAnalysisService with an optional RebalancingService dependency."""

        self._rebalancing_service = rebalancing_service



    def _get_rebalancing_service(self) -> Optional[Any]:

        """Safely retrieve the RebalancingService dependency if explicitly provided."""

        return self._rebalancing_service



    def analyze(self, rebalancing_state: Optional[Any] = None) -> AllocationAnalysisResult:

        """Perform descriptive allocation analysis on the given RebalancingState."""

        try:

            if rebalancing_state is None:

                return _empty_result()



            portfolio = getattr(rebalancing_state, "portfolio", None)

            positions = getattr(portfolio, "positions", []) if portfolio is not None else []

            if not isinstance(positions, list) or not positions:

                return _empty_result()



            valid_positions = [p for p in positions if _is_valid_position(p)]

            if not valid_positions:

                return _empty_result()



            # Determine total portfolio value

            explicit_total = _safe_float(getattr(portfolio, "total_value", None) or getattr(rebalancing_state, "total_value", None), 0.0)

            parsed_positions: list[tuple[str, str, float]] = []



            for p in valid_positions:

                try:

                    sym = str(getattr(p, "symbol", "") or "").strip()

                    atype = str(getattr(p, "asset_type", "") or "EQUITY").strip().upper()

                    val = max(0.0, _safe_float(getattr(p, "current_value", None), 0.0))

                    if not atype:

                        atype = "EQUITY"

                    parsed_positions.append((sym, atype, val))

                except Exception:

                    continue



            if not parsed_positions:

                return _empty_result()



            sum_value = sum(item[2] for item in parsed_positions)

            total_val = explicit_total if (explicit_total > 0) else sum_value



            # 1. Asset Allocation Analysis (Group by asset_type)

            asset_groups: dict[str, list[float]] = {}

            for sym, atype, val in parsed_positions:

                if atype not in asset_groups:

                    asset_groups[atype] = []

                asset_groups[atype].append(val)



            asset_allocations: list[AllocationCategory] = []

            for atype in sorted(asset_groups.keys()):

                vals = asset_groups[atype]

                cat_val = sum(vals)

                weight = (cat_val / total_val * 100.0) if total_val > 0 else 0.0

                asset_allocations.append(

                    AllocationCategory(

                        name=atype,

                        current_value=round(cat_val, 2),

                        current_weight=round(weight, 2),

                        position_count=len(vals),

                    )

                )



            # 2. Fund Allocation Analysis

            fund_groups: dict[str, list[float]] = {}

            for sym, atype, val in parsed_positions:

                if atype in self.FUND_TYPES or "FUND" in atype:

                    if atype not in fund_groups:

                        fund_groups[atype] = []

                    fund_groups[atype].append(val)



            fund_allocations: list[AllocationCategory] = []

            for ftype in sorted(fund_groups.keys()):

                vals = fund_groups[ftype]

                cat_val = sum(vals)

                weight = (cat_val / total_val * 100.0) if total_val > 0 else 0.0

                fund_allocations.append(

                    AllocationCategory(

                        name=ftype,

                        current_value=round(cat_val, 2),

                        current_weight=round(weight, 2),

                        position_count=len(vals),

                    )

                )



            # 3. ETF Allocation Analysis

            etf_groups: dict[str, list[float]] = {}

            for sym, atype, val in parsed_positions:

                if atype in self.ETF_TYPES or "ETF" in atype:

                    if atype not in etf_groups:

                        etf_groups[atype] = []

                    etf_groups[atype].append(val)



            etf_allocations: list[AllocationCategory] = []

            for etype in sorted(etf_groups.keys()):

                vals = etf_groups[etype]

                cat_val = sum(vals)

                weight = (cat_val / total_val * 100.0) if total_val > 0 else 0.0

                etf_allocations.append(

                    AllocationCategory(

                        name=etype,

                        current_value=round(cat_val, 2),

                        current_weight=round(weight, 2),

                        position_count=len(vals),

                    )

                )



            return AllocationAnalysisResult(

                total_value=round(total_val, 2),

                asset_allocations=asset_allocations,

                fund_allocations=fund_allocations,

                etf_allocations=etf_allocations,

            )

        except Exception:

            return _empty_result()



    def get_analysis(self) -> AllocationAnalysisResult:

        """Fetch RebalancingState and compute allocation analysis safely."""

        try:

            svc = self._get_rebalancing_service()

            if svc is not None and hasattr(svc, "get_state"):

                state = svc.get_state()

                return self.analyze(state)

            return _empty_result()

        except Exception:

            return _empty_result()
