"""Rebalancing Foundation Service (Sprint 13.7.0)



Provides foundational Rebalancing data model, portfolio normalization,

and current portfolio weight calculation for AlphaForge.

"""

from __future__ import annotations



from dataclasses import dataclass

from typing import Any, Optional





@dataclass

class RebalancingPosition:

    """Represents a single position in the rebalancing portfolio."""



    symbol: str

    name: str

    asset_type: str

    current_value: float

    current_weight: float

    target_weight: Optional[float] = None





@dataclass

class RebalancingPortfolio:

    """Represents a collection of normalized rebalancing positions."""



    total_value: float

    positions: list[RebalancingPosition]





@dataclass

class RebalancingState:

    """Overall rebalancing engine state container."""



    status: str

    portfolio: RebalancingPortfolio

    total_positions: int

    total_value: float





def _empty_portfolio() -> RebalancingPortfolio:

    """Return a safe empty RebalancingPortfolio."""

    return RebalancingPortfolio(

        total_value=0.0,

        positions=[],

    )





def _empty_state(status: str = "EMPTY") -> RebalancingState:

    """Return a safe fallback RebalancingState."""

    return RebalancingState(

        status=status,

        portfolio=_empty_portfolio(),

        total_positions=0,

        total_value=0.0,

    )





def _safe_float(val: Any, default: float = 0.0) -> float:

    """Safely convert value to float."""

    try:

        if val is None:

            return default

        return float(val)

    except (TypeError, ValueError):

        return default





class RebalancingService:

    """Foundational service for loading portfolio structure and calculating current weights.



    Does NOT perform drift detection, target allocation analysis, or candidate ranking.

    """



    def __init__(self, portfolio_service: Optional[Any] = None) -> None:

        """Initialize RebalancingService with an optional portfolio service dependency."""

        self._portfolio_service = portfolio_service



    def _get_portfolio_service(self) -> Optional[Any]:

        """Safely retrieve or instantiate the application portfolio service."""

        if self._portfolio_service is not None:

            return self._portfolio_service

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



    def load_portfolio(self) -> RebalancingPortfolio:

        """Load, normalize, and return current rebalancing portfolio positions."""

        try:

            svc = self._get_portfolio_service()

            if svc is None:

                return _empty_portfolio()



            raw_positions: list[Any] = []

            explicit_total_value: Optional[float] = None



            # Attempt to extract status dict or position data from service

            if hasattr(svc, "get_status"):

                status_res = svc.get_status()

                if isinstance(status_res, dict) and status_res.get("status") == "OK":

                    explicit_total_value = _safe_float(status_res.get("portfolio_value"), 0.0)

                    state = status_res.get("state")

                    if isinstance(state, dict):

                        pos_dict = state.get("positions", {})

                        if isinstance(pos_dict, dict):

                            raw_positions = list(pos_dict.values())

                        elif isinstance(pos_dict, list):

                            raw_positions = pos_dict

                    elif isinstance(status_res.get("positions"), list):

                        raw_positions = status_res.get("positions", [])

            elif hasattr(svc, "get_positions"):

                res = svc.get_positions()

                if isinstance(res, list):

                    raw_positions = res

                elif isinstance(res, dict):

                    raw_positions = list(res.values())

            elif hasattr(svc, "positions"):

                pos_attr = getattr(svc, "positions")

                if isinstance(pos_attr, list):

                    raw_positions = pos_attr

                elif isinstance(pos_attr, dict):

                    raw_positions = list(pos_attr.values())

            elif isinstance(svc, list):

                raw_positions = svc

            elif isinstance(svc, dict):

                raw_positions = list(svc.values())



            if not raw_positions:

                return _empty_portfolio()



            # First pass: parse raw position objects/dicts

            parsed_items: list[tuple[str, str, str, float]] = []

            for item in raw_positions:

                if item is None or isinstance(item, (int, float, str, bool)):

                    continue

                try:

                    if isinstance(item, dict):

                        sym = str(item.get("symbol") or item.get("ticker") or "").strip()

                        nm = str(item.get("name") or sym).strip()

                        atype = str(item.get("asset_type") or item.get("type") or "EQUITY").strip()

                        val = _safe_float(item.get("current_value") or item.get("market_value") or item.get("value"), 0.0)

                    else:

                        sym = str(getattr(item, "symbol", "") or getattr(item, "ticker", "") or "").strip()

                        nm = str(getattr(item, "name", "") or sym).strip()

                        atype = str(getattr(item, "asset_type", "") or getattr(item, "type", "") or "EQUITY").strip()

                        val = _safe_float(getattr(item, "current_value", None) or getattr(item, "market_value", None) or getattr(item, "value", None), 0.0)



                    if not sym and not nm:

                        continue



                    parsed_items.append((sym, nm, atype, max(0.0, val)))

                except Exception:

                    continue



            if not parsed_items:

                return _empty_portfolio()



            # Compute portfolio total value

            sum_value = sum(item[3] for item in parsed_items)

            total_val = explicit_total_value if (explicit_total_value is not None and explicit_total_value > 0) else sum_value



            positions: list[RebalancingPosition] = []

            for sym, nm, atype, val in parsed_items:

                weight = (val / total_val * 100.0) if total_val > 0 else 0.0

                positions.append(

                    RebalancingPosition(

                        symbol=sym,

                        name=nm,

                        asset_type=atype,

                        current_value=round(val, 2),

                        current_weight=round(weight, 2),

                        target_weight=None,

                    )

                )



            return RebalancingPortfolio(

                total_value=round(total_val, 2),

                positions=positions,

            )

        except Exception:

            return _empty_portfolio()



    def get_state(self) -> RebalancingState:

        """Fetch and return overall RebalancingState safely."""

        try:

            svc = self._get_portfolio_service()

            if svc is None:

                return _empty_state("UNAVAILABLE")



            portfolio = self.load_portfolio()

            total_pos = len(portfolio.positions)



            if total_pos > 0 and portfolio.total_value > 0:

                status = "READY"

            elif total_pos == 0:

                status = "EMPTY"

            else:

                status = "READY" if total_pos > 0 else "EMPTY"



            return RebalancingState(

                status=status,

                portfolio=portfolio,

                total_positions=total_pos,

                total_value=portfolio.total_value,

            )

        except Exception:

            return _empty_state("EMPTY")
