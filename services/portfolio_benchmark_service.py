"""
Portfolio Benchmark Intelligence Service

Calculates portfolio 1-year returns, benchmark (Nifty 50: ^NSEI) 1-year returns,
alpha return, and overall benchmark comparison status.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import yfinance as yf

from services.stock_service import get_stock_data


class PortfolioBenchmarkService:
    """
    Service responsible for benchmark tracking, 1-year returns calculation,
    and alpha performance summary against ^NSEI.
    """

    BENCHMARK_SYMBOL: str = "^NSEI"

    def __init__(self, stock_service: Any = None, state_service: Any = None):
        self.stock_service = stock_service
        self.state_service = state_service

    def get_nifty_return_1y(self) -> Optional[float]:
        """
        Calculates 1-year percentage return of the Nifty 50 benchmark (^NSEI).
        """
        return self._fetch_symbol_1y_return(self.BENCHMARK_SYMBOL)

    def get_portfolio_return_1y(self, portfolio_input: Any = None) -> Optional[float]:
        """
        Calculates weighted 1-year percentage return of portfolio holdings.
        """
        positions, symbols = self._extract_positions_and_symbols(portfolio_input)
        if not positions or not symbols:
            return None

        weighted_returns: List[Tuple[float, float]] = []
        total_weight = 0.0

        for symbol, pos in positions.items():
            sym_return = self._fetch_symbol_1y_return(symbol)
            if sym_return is None:
                continue

            weight = pos.get("weight", 0.0)
            weighted_returns.append((weight, sym_return))
            total_weight += weight

        if not weighted_returns:
            return None

        if total_weight <= 0:
            # Fallback to equal weighting if total weight is <= 0
            equal_w = 1.0 / len(weighted_returns)
            port_return = sum(equal_w * r for _, r in weighted_returns)
        else:
            port_return = sum((w / total_weight) * r for w, r in weighted_returns)

        return round(float(port_return), 2)

    def get_alpha_return_1y(self, portfolio_input: Any = None) -> Optional[float]:
        """
        Calculates 1-year alpha return (portfolio return - benchmark return).
        """
        port_return = self.get_portfolio_return_1y(portfolio_input)
        nifty_return = self.get_nifty_return_1y()

        if port_return is None or nifty_return is None:
            return None

        return round(port_return - nifty_return, 2)

    def get_benchmark_summary(self, portfolio_input: Any = None) -> Dict[str, Any]:
        """
        Generates benchmark intelligence summary.
        """
        positions, symbols = self._extract_positions_and_symbols(portfolio_input)
        portfolio_symbol_count = len(symbols)

        port_return = self.get_portfolio_return_1y(portfolio_input)
        nifty_return = self.get_nifty_return_1y()

        if port_return is None or nifty_return is None or portfolio_symbol_count == 0:
            return {
                "portfolio_return_1y": float(port_return) if port_return is not None else 0.0,
                "benchmark_return_1y": float(nifty_return) if nifty_return is not None else 0.0,
                "alpha_return_1y": round((port_return or 0.0) - (nifty_return or 0.0), 2)
                if (port_return is not None and nifty_return is not None)
                else 0.0,
                "status": "UNKNOWN",
                "portfolio_symbol_count": portfolio_symbol_count,
                "benchmark_symbol": self.BENCHMARK_SYMBOL,
            }

        alpha_return = round(port_return - nifty_return, 2)
        status = "BEATING_BENCHMARK" if alpha_return >= 0.0 else "LAGGING_BENCHMARK"

        return {
            "portfolio_return_1y": float(port_return),
            "benchmark_return_1y": float(nifty_return),
            "alpha_return_1y": alpha_return,
            "status": status,
            "portfolio_symbol_count": portfolio_symbol_count,
            "benchmark_symbol": self.BENCHMARK_SYMBOL,
        }

    def _fetch_symbol_1y_return(self, symbol: str) -> Optional[float]:
        """
        Fetches 1-year return for a given stock symbol or index.
        Uses stock_service if practical, or yfinance fallback.
        """
        if not symbol or not isinstance(symbol, str):
            return None

        normalized_sym = symbol.strip().upper()
        if not normalized_sym:
            return None

        if self.stock_service is not None and hasattr(self.stock_service, "get_1y_return"):
            try:
                res = self.stock_service.get_1y_return(normalized_sym)
                if res is not None:
                    return float(res)
            except Exception:
                pass

        if not normalized_sym.startswith("^") and not normalized_sym.endswith(".NS"):
            normalized_sym += ".NS"

        try:
            ticker = yf.Ticker(normalized_sym)
            hist = ticker.history(period="1y")
            if hist is None or hist.empty or "Close" not in hist.columns:
                return None

            close = hist["Close"].dropna()
            if len(close) < 2:
                return None

            start_price = float(close.iloc[0])
            end_price = float(close.iloc[-1])

            if start_price <= 0:
                return None

            ret = ((end_price - start_price) / start_price) * 100.0
            return round(ret, 2)
        except Exception:
            return None

    def _extract_positions_and_symbols(
        self, portfolio_input: Any
    ) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        """
        Extracts position dict map and list of symbols defensively from portfolio input.
        """
        positions_map: Dict[str, Dict[str, Any]] = {}

        if portfolio_input is None and self.state_service is not None:
            try:
                state = self.state_service.load_state()
                if isinstance(state, dict):
                    portfolio_input = state
            except Exception:
                pass

        if isinstance(portfolio_input, dict):
            raw_pos = portfolio_input.get("positions")
            if isinstance(raw_pos, dict):
                for k, v in raw_pos.items():
                    sym = self._normalize_symbol(k or (v.get("symbol") if isinstance(v, dict) else None))
                    if sym:
                        weight = 0.0
                        if isinstance(v, dict):
                            weight = float(
                                v.get("weight")
                                or v.get("actual_weight")
                                or v.get("target_weight")
                                or v.get("current_value")
                                or 0.0
                            )
                        positions_map[sym] = {"weight": max(0.0, weight)}
            elif isinstance(raw_pos, list):
                for item in raw_pos:
                    if isinstance(item, dict):
                        sym = self._normalize_symbol(item.get("symbol") or item.get("ticker"))
                        if sym:
                            weight = max(
                                0.0,
                                float(
                                    item.get("weight")
                                    or item.get("actual_weight")
                                    or item.get("target_weight")
                                    or item.get("current_value")
                                    or 0.0
                                ),
                            )
                            positions_map[sym] = {"weight": weight}
            else:
                for k, v in portfolio_input.items():
                    if k in (
                        "status",
                        "updated_at",
                        "cash_balance",
                        "invested_market_value",
                        "portfolio_value",
                        "snapshots",
                        "transactions",
                    ):
                        continue
                    sym = self._normalize_symbol(k)
                    if sym:
                        weight = 0.0
                        if isinstance(v, dict):
                            weight = max(
                                0.0,
                                float(
                                    v.get("weight")
                                    or v.get("actual_weight")
                                    or v.get("target_weight")
                                    or v.get("current_value")
                                    or 0.0
                                ),
                            )
                        positions_map[sym] = {"weight": weight}

        elif isinstance(portfolio_input, list):
            for item in portfolio_input:
                if isinstance(item, dict):
                    sym = self._normalize_symbol(item.get("symbol") or item.get("ticker"))
                    if sym:
                        weight = max(
                            0.0,
                            float(
                                item.get("weight")
                                or item.get("actual_weight")
                                or item.get("target_weight")
                                or item.get("current_value")
                                or 0.0
                            ),
                        )
                        positions_map[sym] = {"weight": weight}
                elif isinstance(item, str):
                    sym = self._normalize_symbol(item)
                    if sym:
                        positions_map[sym] = {"weight": 0.0}

        symbols = sorted(list(positions_map.keys()))
        return positions_map, symbols

    @staticmethod
    def _normalize_symbol(symbol: Any) -> str:
        if not symbol or not isinstance(symbol, (str, int)):
            return ""
        return str(symbol).strip().upper()
