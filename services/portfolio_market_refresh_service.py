"""
Portfolio Market Refresh Service

Service responsible for extracting holding symbols from portfolio state/positions,
fetching live market prices via stock_service, and constructing a price map for
portfolio mark-to-market updates.
"""

from typing import Any, Dict, List, Union
from services.stock_service import get_stock_data


class PortfolioMarketRefreshService:
    """
    Service for generating live price maps for portfolio market refreshes.
    """

    def fetch_live_prices(
        self,
        portfolio_input: Union[Dict[str, Any], List[Any]]
    ) -> Dict[str, Any]:
        """
        Extracts symbols from portfolio state or positions list, fetches live prices
        using stock_service.get_stock_data, and returns the price_map alongside
        updated and failed symbol lists.

        :param portfolio_input: Portfolio state dict or list/dict of positions.
        :return: Dict with keys 'price_map', 'updated_symbols', 'failed_symbols'.
        """
        symbols = self.extract_symbols(portfolio_input)

        price_map: Dict[str, float] = {}
        updated_symbols: List[str] = []
        failed_symbols: List[str] = []

        for symbol in symbols:
            try:
                data = get_stock_data(symbol)
                if isinstance(data, dict) and "error" not in data:
                    raw_price = data.get("price")
                    if raw_price is not None and raw_price != "N/A":
                        price = float(raw_price)
                        if price > 0:
                            price_map[symbol] = round(price, 2)
                            updated_symbols.append(symbol)
                            continue
                failed_symbols.append(symbol)
            except Exception:
                failed_symbols.append(symbol)

        return {
            "price_map": price_map,
            "updated_symbols": updated_symbols,
            "failed_symbols": failed_symbols,
        }

    # Aliases for flexibility
    create_price_map = fetch_live_prices
    get_live_price_map = fetch_live_prices

    def extract_symbols(
        self,
        portfolio_input: Union[Dict[str, Any], List[Any]]
    ) -> List[str]:
        """
        Extracts unique, normalized stock symbols from various portfolio state/position input structures.
        """
        symbols = set()

        if isinstance(portfolio_input, dict):
            # Case 1: Full portfolio state dict containing a "positions" key
            positions = portfolio_input.get("positions")
            if positions is not None:
                if isinstance(positions, dict):
                    for k, v in positions.items():
                        sym = self._normalize_symbol(k)
                        if sym:
                            symbols.add(sym)
                        if isinstance(v, dict):
                            item_sym = self._normalize_symbol(v.get("symbol") or v.get("ticker"))
                            if item_sym:
                                symbols.add(item_sym)
                elif isinstance(positions, list):
                    for item in positions:
                        sym = self._extract_single_symbol(item)
                        if sym:
                            symbols.add(sym)
            else:
                # Case 2: Dict of position objects keyed by symbol
                for k, v in portfolio_input.items():
                    if k in (
                        "status",
                        "updated_at",
                        "cash_balance",
                        "invested_market_value",
                        "portfolio_value",
                        "position_count",
                        "transaction_count",
                        "snapshot_count",
                    ):
                        continue
                    sym = self._normalize_symbol(k)
                    if sym:
                        symbols.add(sym)
                    if isinstance(v, dict):
                        item_sym = self._normalize_symbol(v.get("symbol") or v.get("ticker"))
                        if item_sym:
                            symbols.add(item_sym)

        elif isinstance(portfolio_input, list):
            for item in portfolio_input:
                sym = self._extract_single_symbol(item)
                if sym:
                    symbols.add(sym)

        return sorted(list(symbols))

    def _extract_single_symbol(self, item: Any) -> str:
        if isinstance(item, str):
            return self._normalize_symbol(item)
        elif isinstance(item, dict):
            raw = item.get("symbol") or item.get("ticker")
            return self._normalize_symbol(raw)
        return ""

    @staticmethod
    def _normalize_symbol(symbol: Any) -> str:
        if not symbol:
            return ""
        return str(symbol).strip().upper()
