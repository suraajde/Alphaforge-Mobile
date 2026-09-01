from __future__ import annotations

from copy import deepcopy

from services.portfolio_orchestration_service import (
    PortfolioOrchestrationService,
)
from services.portfolio_market_refresh_service import (
    PortfolioMarketRefreshService,
)



class PortfolioApplicationService:
    """
    AlphaForge Portfolio Application Boundary.

    Provides a stable, UI-friendly interface over the tested
    portfolio orchestration lifecycle.

    Responsibilities:
    - Load persistent portfolio state when required.
    - Expose portfolio availability/status to application screens.
    - Delegate initial-investment preparation and confirmation.
    - Delegate Smart SIP preparation and confirmation.
    - Delegate portfolio mark-to-market refresh.
    - Produce a normalized portfolio summary for presentation.

    This service does NOT:
    - Select Alpha 12 stocks.
    - Calculate target portfolio weights.
    - Allocate whole-share capital directly.
    - Calculate Smart SIP allocation directly.
    - Mutate portfolio holdings outside the orchestration service.
    - Fetch live market prices.
    """

    def __init__(
        self,
        orchestration_service=None,
        state_path=None,
    ):

        self.orchestrator = (
            orchestration_service
            if orchestration_service is not None
            else PortfolioOrchestrationService()
        )

        self.state_path = state_path

    # ======================================================
    # INTERNAL HELPERS
    # ======================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

            if value is None:
                return float(
                    default
                )

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return float(
                default
            )

    @staticmethod
    def _normalize_symbol(
        value,
    ):

        if value is None:
            return ""

        return str(
            value
        ).strip().upper()

    def _load_result(
        self,
    ):

        try:

            result = (
                self.orchestrator
                .load_state(
                    path=self.state_path,
                )
            )

        except Exception as exc:

            return {

                "status":
                    "ERROR",

                "error":
                    str(
                        exc
                    ),

                "state":
                    None,

            }

        if not isinstance(
            result,
            dict,
        ):

            return {

                "status":
                    "ERROR",

                "error":
                    "Invalid portfolio state load result.",

                "state":
                    None,

            }

        return result

    def _require_state(
        self,
    ):

        result = (
            self._load_result()
        )

        status = str(
            result.get(
                "status",
                "",
            )
        ).upper()

        if status == "NOT_FOUND":

            return {

                "status":
                    "NOT_FOUND",

                "error":
                    None,

                "state":
                    None,

            }

        if status != "OK":

            return {

                "status":
                    "ERROR",

                "error":
                    result.get(
                        "error",
                        "Unable to load portfolio state.",
                    ),

                "state":
                    None,

            }

        state = result.get(
            "state"
        )

        if not isinstance(
            state,
            dict,
        ):

            return {

                "status":
                    "ERROR",

                "error":
                    "Loaded portfolio state is invalid.",

                "state":
                    None,

            }

        return {

            "status":
                "OK",

            "error":
                None,

            "state":
                state,

        }

    # ======================================================
    # PORTFOLIO STATUS
    # ======================================================

    def get_status(
        self,
    ):

        loaded = (
            self._require_state()
        )

        if (
            loaded[
                "status"
            ]
            == "NOT_FOUND"
        ):

            return {

                "status":
                    "OK",

                "portfolio_exists":
                    False,

                "position_count":
                    0,

                "cash_balance":
                    0.0,

                "invested_market_value":
                    0.0,

                "portfolio_value":
                    0.0,

                "transaction_count":
                    0,

                "snapshot_count":
                    0,

                "state":
                    None,

            }

        if (
            loaded[
                "status"
            ]
            != "OK"
        ):

            return {

                "status":
                    "ERROR",

                "portfolio_exists":
                    False,

                "error":
                    loaded.get(
                        "error"
                    ),

            }

        state = loaded[
            "state"
        ]

        positions = state.get(
            "positions",
            {},
        )

        if not isinstance(
            positions,
            dict,
        ):

            positions = {}

        transactions = state.get(
            "transactions",
            [],
        )

        if not isinstance(
            transactions,
            list,
        ):

            transactions = []

        snapshots = state.get(
            "snapshots",
            [],
        )

        if not isinstance(
            snapshots,
            list,
        ):

            snapshots = []

        pos_iterable = positions.values() if isinstance(positions, dict) else positions
        total_invested_cost = sum(
            self._safe_float(p.get("invested_cost", 0.0)) for p in pos_iterable if isinstance(p, dict)
        )
        total_current_value = sum(
            self._safe_float(p.get("current_value", p.get("market_value", 0.0))) for p in pos_iterable if isinstance(p, dict)
        )
        running_pnl = total_current_value - total_invested_cost
        running_pnl_pct = (running_pnl / total_invested_cost * 100.0) if total_invested_cost > 0 else 0.0

        return {

            "status":
                "OK",

            "portfolio_exists":
                True,

            "position_count":
                len(
                    positions
                ),

            "cash_balance":
                round(
                    self._safe_float(
                        state.get(
                            "cash_balance",
                            0.0,
                        )
                    ),
                    2,
                ),

            "invested_market_value":
                round(
                    self._safe_float(
                        state.get(
                            "invested_market_value",
                            total_current_value,
                        )
                    ),
                    2,
                ),

            "total_invested_cost":
                round(
                    total_invested_cost,
                    2,
                ),

            "total_cost":
                round(
                    total_invested_cost,
                    2,
                ),

            "total_current_value":
                round(
                    total_current_value,
                    2,
                ),

            "total_running_pnl":
                round(
                    running_pnl,
                    2,
                ),

            "running_pnl":
                round(
                    running_pnl,
                    2,
                ),

            "total_running_pnl_pct":
                round(
                    running_pnl_pct,
                    4,
                ),

            "running_pnl_pct":
                round(
                    running_pnl_pct,
                    4,
                ),

            "portfolio_value":
                round(
                    self._safe_float(
                        state.get(
                            "total_portfolio_value",
                            state.get(
                                "portfolio_value",
                                0.0,
                            ),
                        )
                    ),
                    2,
                ),

            "transaction_count":
                len(
                    transactions
                ),

            "snapshot_count":
                len(
                    snapshots
                ),

            "state":
                deepcopy(
                    state
                ),

        }

    # ======================================================
    # INITIAL INVESTMENT
    # ======================================================

    def prepare_initial_investment(
        self,
        alpha12,
        capital,
        price_map,
    ):

        try:

            result = (
                self.orchestrator
                .prepare_initial_investment(

                    alpha12=
                        alpha12,

                    capital=
                        capital,

                    price_map=
                        price_map,

                )
            )

            if isinstance(
                result,
                dict,
            ):

                result = deepcopy(
                    result
                )

                result[
                    "recommended_invested_amount"
                ] = self._safe_float(
                    result.get(
                        "invested_amount",
                        0.0,
                    )
                )

                result[
                    "recommended_cash_remaining"
                ] = self._safe_float(
                    result.get(
                        "cash_remaining",
                        0.0,
                    )
                )

            return result

        except Exception as exc:

            return {

                "status":
                    "ERROR",

                "mode":
                    "INITIAL_INVESTMENT_RECOMMENDATION",

                "confirmed":
                    False,

                "error":
                    str(
                        exc
                    ),

            }

    def confirm_initial_investment(
        self,
        recommendation,
        confirmed_buys=None,
        transaction_date=None,
    ):

        try:

            return (
                self.orchestrator
                .confirm_initial_investment(

                    recommendation=
                        recommendation,

                    confirmed_buys=
                        confirmed_buys,

                    transaction_date=
                        transaction_date,

                    save=
                        True,

                    path=
                        self.state_path,

                )
            )

        except Exception as exc:

            return {

                "status":
                    "ERROR",

                "mode":
                    "INITIAL_INVESTMENT_CONFIRMATION",

                "confirmed":
                    False,

                "error":
                    str(
                        exc
                    ),

            }

    # ======================================================
    # CORRECT CONFIRMED BUY
    #
    # Public application boundary for controlled correction
    # of one specific confirmed BUY transaction.
    # ======================================================

    def correct_confirmed_buy(
        self,
        transaction_index,
        quantity,
        price,
        correction_date=None,
        reason="DATA_ENTRY_CORRECTION",
    ):

        try:

            return (
                self.orchestrator
                .correct_confirmed_buy(

                    transaction_index=
                        transaction_index,

                    quantity=
                        quantity,

                    price=
                        price,

                    correction_date=
                        correction_date,

                    reason=
                        reason,

                    save=
                        True,

                    path=
                        self.state_path,

                )
            )

        except Exception as exc:

            return {

                "status":
                    "ERROR",

                "mode":
                    "PURCHASE_ENTRY_CORRECTION",

                "corrected":
                    False,

                "error":
                    str(
                        exc
                    ),

            }


    # ======================================================
    # SMART SIP
    # ======================================================

    def prepare_sip(
        self,
        sip_amount,
        price_map,
    ):

        loaded = (
            self._require_state()
        )

        if (
            loaded[
                "status"
            ]
            != "OK"
        ):

            return {

                "status":
                    loaded[
                        "status"
                    ],

                "mode":
                    "SMART_SIP_RECOMMENDATION",

                "confirmed":
                    False,

                "error":
                    loaded.get(
                        "error"
                    ),

            }

        try:

            result = (
                self.orchestrator
                .prepare_sip(

                    state=
                        loaded[
                            "state"
                        ],

                    sip_amount=
                        sip_amount,

                    price_map=
                        price_map,

                )
            )

            if isinstance(
                result,
                dict,
            ):

                result = deepcopy(
                    result
                )

                result[
                    "carry_forward_in"
                ] = self._safe_float(
                    result.get(
                        "carry_forward_cash",
                        0.0,
                    )
                )

                result[
                    "recommended_invested_amount"
                ] = self._safe_float(
                    result.get(
                        "sip_invested",
                        0.0,
                    )
                )

                result[
                    "recommended_cash_remaining"
                ] = self._safe_float(
                    result.get(
                        "cash_remaining",
                        0.0,
                    )
                )

            return result

        except Exception as exc:

            return {

                "status":
                    "ERROR",

                "mode":
                    "SMART_SIP_RECOMMENDATION",

                "confirmed":
                    False,

                "error":
                    str(
                        exc
                    ),

            }

    def confirm_sip(
        self,
        recommendation,
        confirmed_buys=None,
        transaction_date=None,
        snapshot_label=None,
    ):

        loaded = (
            self._require_state()
        )

        if (
            loaded[
                "status"
            ]
            != "OK"
        ):

            return {

                "status":
                    loaded[
                        "status"
                    ],

                "mode":
                    "SMART_SIP_CONFIRMATION",

                "confirmed":
                    False,

                "error":
                    loaded.get(
                        "error"
                    ),

            }

        try:

            return (
                self.orchestrator
                .confirm_sip(

                    state=
                        loaded[
                            "state"
                        ],

                    recommendation=
                        recommendation,

                    confirmed_buys=
                        confirmed_buys,

                    transaction_date=
                        transaction_date,

                    snapshot_label=
                        snapshot_label,

                    save=
                        True,

                    path=
                        self.state_path,

                )
            )

        except Exception as exc:

            return {

                "status":
                    "ERROR",

                "mode":
                    "SMART_SIP_CONFIRMATION",

                "confirmed":
                    False,

                "error":
                    str(
                        exc
                    ),

            }

    # ======================================================
    # PORTFOLIO REFRESH
    # ======================================================

    def refresh_portfolio(
        self,
        price_map=None,
        snapshot_label=None,
        save=True,
    ):

        loaded = (
            self._require_state()
        )

        if (
            loaded[
                "status"
            ]
            != "OK"
        ):

            return {

                "status":
                    loaded[
                        "status"
                    ],

                "error":
                    loaded.get(
                        "error"
                    ),

            }

        if not price_map:
            refresh_service = PortfolioMarketRefreshService()
            refresh_res = refresh_service.fetch_live_prices(
                loaded["state"]
            )
            price_map = refresh_res.get("price_map", {})

        try:

            return (
                self.orchestrator
                .refresh_portfolio(

                    state=
                        loaded[
                            "state"
                        ],

                    price_map=
                        price_map,

                    snapshot_label=
                        snapshot_label,

                    save=
                        save,

                    path=
                        self.state_path,

                )
            )

        except Exception as exc:

            return {

                "status":
                    "ERROR",

                "error":
                    str(
                        exc
                    ),

            }

    # ======================================================
    # PURCHASE TRANSACTIONS
    #
    # READ ONLY
    #
    # Returns genuine BUY transactions for one portfolio
    # symbol together with their authoritative transaction
    # list indexes.
    #
    # CORRECTION audit entries are intentionally excluded.
    # ======================================================

    def get_purchase_transactions(
        self,
        symbol,
    ):

        symbol = self._normalize_symbol(
            symbol
        )

        if not symbol:

            return {

                "status":
                    "ERROR",

                "error":
                    "Invalid portfolio symbol",

                "purchases":
                    [],

            }

        loaded = self._require_state()

        if loaded.get(
            "status"
        ) != "OK":

            return {

                "status":
                    loaded.get(
                        "status",
                        "ERROR",
                    ),

                "error":
                    loaded.get(
                        "error",
                        "Unable to load portfolio state",
                    ),

                "purchases":
                    [],

            }

        state = loaded.get(
            "state",
            {},
        )

        transactions = state.get(
            "transactions",
            [],
        )

        if not isinstance(
            transactions,
            list,
        ):

            transactions = []

        purchases = []

        for (
            transaction_index,
            transaction,
        ) in enumerate(
            transactions
        ):

            if not isinstance(
                transaction,
                dict,
            ):

                continue

            if str(
                transaction.get(
                    "type",
                    "",
                )
            ).strip().upper() != "BUY":

                continue

            transaction_symbol = (
                self._normalize_symbol(
                    transaction.get(
                        "symbol"
                    )
                )
            )

            if transaction_symbol != symbol:

                continue

            row = deepcopy(
                transaction
            )

            row[
                "transaction_index"
            ] = transaction_index

            purchases.append(
                row
            )

        return {

            "status":
                "OK",

            "symbol":
                symbol,

            "purchases":
                purchases,

            "purchase_count":
                len(
                    purchases
                ),

        }


    # ======================================================
    # UI-READY PORTFOLIO SUMMARY
    # ======================================================

    def get_portfolio_summary(
        self,
    ):

        loaded = (
            self._require_state()
        )

        if (
            loaded[
                "status"
            ]
            == "NOT_FOUND"
        ):

            return {

                "status":
                    "OK",

                "portfolio_exists":
                    False,

                "positions":
                    [],

                "position_count":
                    0,

                "cash_balance":
                    0.0,

                "invested_market_value":
                    0.0,

                "portfolio_value":
                    0.0,

                "transaction_count":
                    0,

                "snapshot_count":
                    0,

            }

        if (
            loaded[
                "status"
            ]
            != "OK"
        ):

            return {

                "status":
                    "ERROR",

                "portfolio_exists":
                    False,

                "error":
                    loaded.get(
                        "error"
                    ),

            }

        state = loaded[
            "state"
        ]

        source_positions = state.get(
            "positions",
            {},
        )

        if not isinstance(
            source_positions,
            dict,
        ):

            source_positions = {}

        positions = []

        for (
            symbol,
            source,
        ) in source_positions.items():

            if not isinstance(
                source,
                dict,
            ):

                continue

            row = deepcopy(
                source
            )

            normalized_symbol = (
                self._normalize_symbol(
                    row.get(
                        "symbol",
                        symbol,
                    )
                )
            )

            row[
                "symbol"
            ] = normalized_symbol

            row[
                "market_value"
            ] = round(
                self._safe_float(
                    row.get(
                        "current_value",
                        row.get(
                            "market_value",
                            0.0,
                        ),
                    )
                ),
                2,
            )

            positions.append(
                row
            )

        positions.sort(

            key=lambda row: (

                row.get(
                    "alpha12_rank",
                    row.get(
                        "rank",
                        999,
                    ),
                ),

                row.get(
                    "symbol",
                    "",
                ),

            )

        )

        transactions = state.get(
            "transactions",
            [],
        )

        if not isinstance(
            transactions,
            list,
        ):

            transactions = []

        snapshots = state.get(
            "snapshots",
            [],
        )

        if not isinstance(
            snapshots,
            list,
        ):

            snapshots = []

        total_invested_cost = sum(
            self._safe_float(p.get("invested_cost", 0.0)) for p in positions if isinstance(p, dict)
        )
        total_current_value = sum(
            self._safe_float(p.get("market_value", p.get("current_value", 0.0))) for p in positions if isinstance(p, dict)
        )
        running_pnl = total_current_value - total_invested_cost
        running_pnl_pct = (running_pnl / total_invested_cost * 100.0) if total_invested_cost > 0 else 0.0

        return {

            "status":
                "OK",

            "portfolio_exists":
                True,

            "positions":
                positions,

            "position_count":
                len(
                    positions
                ),

            "cash_balance":
                round(
                    self._safe_float(
                        state.get(
                            "cash_balance",
                            0.0,
                        )
                    ),
                    2,
                ),

            "invested_market_value":
                round(
                    self._safe_float(
                        state.get(
                            "invested_market_value",
                            total_current_value,
                        )
                    ),
                    2,
                ),

            "total_invested_cost":
                round(
                    total_invested_cost,
                    2,
                ),

            "total_cost":
                round(
                    total_invested_cost,
                    2,
                ),

            "total_current_value":
                round(
                    total_current_value,
                    2,
                ),

            "total_running_pnl":
                round(
                    running_pnl,
                    2,
                ),

            "running_pnl":
                round(
                    running_pnl,
                    2,
                ),

            "total_running_pnl_pct":
                round(
                    running_pnl_pct,
                    4,
                ),

            "running_pnl_pct":
                round(
                    running_pnl_pct,
                    4,
                ),

            "portfolio_value":
                round(
                    self._safe_float(
                        state.get(
                            "total_portfolio_value",
                            state.get(
                                "portfolio_value",
                                0.0,
                            ),
                        )
                    ),
                    2,
                ),

            "transaction_count":
                len(
                    transactions
                ),

            "snapshot_count":
                len(
                    snapshots
                ),

            "updated_at":
                state.get(
                    "updated_at"
                ),

        }

    # ======================================================
    # PORTFOLIO INTELLIGENCE
    # ======================================================

    def get_portfolio_intelligence(
        self,
        price_map=None,
    ):
        loaded = self._require_state()

        if loaded["status"] == "NOT_FOUND":
            return {
                "status": "NOT_FOUND",
                "portfolio_exists": False,
                "error": None,
                "state": None,
                "analytics": None,
                "health": None,
                "recommendations": None,
                "decisions": None,
            }

        if loaded["status"] != "OK":
            return {
                "status": "ERROR",
                "portfolio_exists": False,
                "error": loaded.get("error"),
                "state": None,
                "analytics": None,
                "health": None,
                "recommendations": None,
                "decisions": None,
            }

        state = loaded["state"]

        try:
            return self.orchestrator.get_portfolio_intelligence(
                state=state,
                price_map=price_map,
            )
        except Exception as exc:
            return {
                "status": "ERROR",
                "portfolio_exists": True,
                "error": str(exc),
                "state": deepcopy(state),
                "analytics": None,
                "health": None,
                "recommendations": None,
                "decisions": None,
            }

    # ======================================================
    # EMERGENCY EJECT & RESERVE PROMOTION
    # ======================================================

    def emergency_replace_position(
        self,
        symbol_to_remove,
        replacement_stock=None,
        transaction_date=None,
    ):
        """
        AlphaForge Emergency Eject & Reserve 8 Promotion.

        Execution:
        1. Validates and removes symbol_to_remove from active portfolio state['positions'].
        2. Queries the Research Radar universe (top 20 ranked stocks) and identifies
           the highest-ranked stock not currently in the portfolio (Reserve 8 bench).
        3. Injects this Reserve 8 candidate with quantity = 0 and invested_cost = 0.00,
           establishing an UNDER_TARGET (massive UNDERWEIGHT) position for Smart SIP capital routing.
        4. Persists the updated state.
        """
        symbol_to_remove = self._normalize_symbol(symbol_to_remove)
        if not symbol_to_remove:
            return {
                "status": "ERROR",
                "mode": "EMERGENCY_REPLACE_POSITION",
                "confirmed": False,
                "error": "Invalid symbol to remove",
            }

        loaded = self._require_state()
        if loaded.get("status") != "OK":
            return {
                "status": loaded.get("status", "ERROR"),
                "mode": "EMERGENCY_REPLACE_POSITION",
                "confirmed": False,
                "error": loaded.get("error", "Unable to load active portfolio state"),
            }

        state = loaded.get("state", {})
        positions = state.get("positions", {})
        if not isinstance(positions, dict) or symbol_to_remove not in positions:
            return {
                "status": "ERROR",
                "mode": "EMERGENCY_REPLACE_POSITION",
                "confirmed": False,
                "error": f"Symbol '{symbol_to_remove}' is not present in active portfolio holdings",
            }

        # Resolve replacement from Reserve 8 bench if not explicitly provided
        if replacement_stock is None:
            try:
                from services.alpha12_mapping_service import Alpha12MappingService
                mapping_svc = Alpha12MappingService()
                replacement_stock = mapping_svc.get_highest_reserve_candidate(active_symbols=positions)
            except Exception:
                replacement_stock = None

        if not replacement_stock or not isinstance(replacement_stock, dict):
            # Fallback to authoritative top 30 symbols with strict uppercase set matching
            active_symbols = {str(k).strip().upper() for k in positions.keys() if str(k).strip()}
            authoritative_top30 = [
                "CASTROLIND", "GLAND", "AJANTPHARM", "IPCALAB", "HSCL",
                "OBEROIRLTY", "MARICO", "NAVINFLUOR", "SAREGAMA", "SONACOMS",
                "AEGISLOG", "RRKABEL", "APARINDS", "JBCHEPHARM", "KIMS",
                "TRENT", "POLYMED", "ERIS", "PNCINFRA", "CENTURYPLY",
                "GLAXO", "RADICO", "COFORGE", "LALPATHLAB", "ACE",
                "ACUTAAS", "CPPLUS", "AARTIIND", "GLENMARK", "FINCABLES"
            ]
            cand_sym = None
            for s in authoritative_top30:
                clean_s = str(s).strip().upper()
                if clean_s not in active_symbols and clean_s != symbol_to_remove:
                    cand_sym = clean_s
                    break
            if cand_sym:
                replacement_stock = {
                    "symbol": cand_sym,
                    "name": cand_sym,
                    "company_name": cand_sym,
                    "sector": "UNKNOWN",
                    "category": "UNKNOWN",
                    "current_price": 0.0,
                    "rank": 13,
                }
            else:
                return {
                    "status": "ERROR",
                    "mode": "EMERGENCY_REPLACE_POSITION",
                    "confirmed": False,
                    "error": "No eligible Reserve 8 replacement candidate found in Research Radar universe",
                }

        if replacement_stock and isinstance(replacement_stock, dict):
            if not replacement_stock.get("current_price"):
                try:
                    from services.stock_service import get_stock_data
                    sdata = get_stock_data(replacement_stock.get("symbol", ""))
                    if isinstance(sdata, dict) and "price" in sdata:
                        raw_p = sdata.get("price")
                        if raw_p and raw_p != "N/A":
                            replacement_stock["current_price"] = float(raw_p)
                except Exception:
                    pass

        try:
            res = self.orchestrator.emergency_replace_position(
                symbol_to_remove=symbol_to_remove,
                replacement_stock=replacement_stock,
                state=state,
                transaction_date=transaction_date,
                save=True,
                path=self.state_path,
            )
            return res
        except Exception as exc:
            return {
                "status": "ERROR",
                "mode": "EMERGENCY_REPLACE_POSITION",
                "confirmed": False,
                "error": str(exc),
            }


def create_portfolio_application_service(
    state_path=None,
):

    return PortfolioApplicationService(
        state_path=
            state_path
    )
