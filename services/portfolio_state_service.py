from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

from config.path_config import get_data_path


class PortfolioStateService:
    """
    AlphaForge Portfolio State & Monthly Accumulation Engine.
    ...
    """

    STATE_VERSION = "1.0"

    DEFAULT_STATE_PATH = get_data_path("portfolio/portfolio_state.json")

    @classmethod
    def get_default_state_path(cls) -> Path:
        return get_data_path("portfolio/portfolio_state.json")

    @staticmethod
    def _normalize_symbol(value):

        if value is None:
            return ""

        return str(
            value
        ).strip().upper()

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return float(
                default
            )

        return result

    @staticmethod
    def _timestamp():

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    def create_state(
        self,
        portfolio,
        cash_balance=0.0,
    ):

        if not isinstance(
            portfolio,
            list,
        ):

            raise TypeError(
                "portfolio must be a list"
            )

        cash_balance = (
            self._safe_float(
                cash_balance,
                0.0,
            )
        )

        if cash_balance < 0:

            raise ValueError(
                "cash_balance cannot be negative"
            )

        positions = {}

        order = []

        for source in portfolio:

            if not isinstance(
                source,
                dict,
            ):

                continue

            symbol = (
                self._normalize_symbol(
                    source.get(
                        "symbol"
                    )
                )
            )

            if not symbol:

                continue

            if symbol in positions:

                raise ValueError(
                    f"Duplicate portfolio symbol: {symbol}"
                )

            target_weight = (
                self._safe_float(
                    source.get(
                        "target_weight",
                        0.0,
                    ),
                    0.0,
                )
            )

            row = {

                "symbol":
                    symbol,

                "company_name":
                    source.get(
                        "company_name",
                        source.get(
                            "universe_company",
                            "",
                        ),
                    ),

                "sector":
                    source.get(
                        "sector",
                        "UNKNOWN",
                    ),

                "category":
                    source.get(
                        "category",
                        "UNKNOWN",
                    ),

                "alpha12_rank":
                    source.get(
                        "alpha12_rank",
                        source.get(
                            "rank"
                        ),
                    ),

                "radar_rank":
                    source.get(
                        "radar_rank",
                        source.get(
                            "rank"
                        ),
                    ),

                "target_weight":
                    round(
                        target_weight,
                        4,
                    ),

                "quantity":
                    0,

                "average_cost":
                    0.0,

                "invested_cost":
                    0.0,

                "current_price":
                    0.0,

                "current_value":
                    0.0,

                "actual_weight":
                    0.0,

                "drift_pct":
                    round(
                        -target_weight,
                        4,
                    ),

                "last_transaction_at":
                    None,

            }

            positions[
                symbol
            ] = row

            order.append(
                symbol
            )

        now = self._timestamp()

        return {

            "state_version":
                self.STATE_VERSION,

            "created_at":
                now,

            "updated_at":
                now,

            "cash_balance":
                round(
                    cash_balance,
                    2,
                ),

            "positions":
                positions,

            "position_order":
                order,

            "transaction_count":
                0,

            "transactions":
                [],

            "snapshots":
                [],

        }

    def apply_confirmed_buys(
        self,
        state,
        buys,
        cash_spent=None,
        transaction_date=None,
        source="MANUAL_CONFIRMATION",
    ):

        if not isinstance(
            state,
            dict,
        ):

            raise TypeError(
                "state must be a dictionary"
            )

        if not isinstance(
            buys,
            list,
        ):

            raise TypeError(
                "buys must be a list"
            )

        updated = deepcopy(
            state
        )

        positions = updated.get(
            "positions",
            {},
        )

        if not isinstance(
            positions,
            dict,
        ):

            raise ValueError(
                "Invalid portfolio state positions"
            )

        timestamp = (
            transaction_date
            or self._timestamp()
        )

        total_spent = 0.0

        transactions = []

        for buy in buys:

            if not isinstance(
                buy,
                dict,
            ):

                continue

            symbol = (
                self._normalize_symbol(
                    buy.get(
                        "symbol"
                    )
                )
            )

            if not symbol:

                continue

            if symbol not in positions:

                raise ValueError(
                    f"Confirmed buy symbol is not "
                    f"in portfolio state: {symbol}"
                )

            quantity = int(
                self._safe_float(
                    buy.get(
                        "quantity",
                        buy.get(
                            "sip_quantity",
                            0,
                        ),
                    ),
                    0.0,
                )
            )

            price = (
                self._safe_float(
                    buy.get(
                        "price",
                        0.0,
                    ),
                    0.0,
                )
            )

            if quantity < 0:

                raise ValueError(
                    f"Negative buy quantity for {symbol}"
                )

            if quantity == 0:

                continue

            if price <= 0:

                raise ValueError(
                    f"Invalid confirmed buy price for {symbol}"
                )

            amount = (
                quantity
                * price
            )

            position = positions[
                symbol
            ]

            old_quantity = int(
                self._safe_float(
                    position.get(
                        "quantity",
                        0,
                    ),
                    0.0,
                )
            )

            old_cost = (
                self._safe_float(
                    position.get(
                        "invested_cost",
                        0.0,
                    ),
                    0.0,
                )
            )

            new_quantity = (
                old_quantity
                + quantity
            )

            new_cost = (
                old_cost
                + amount
            )

            average_cost = (

                new_cost
                / new_quantity

                if new_quantity > 0

                else 0.0

            )

            position[
                "quantity"
            ] = new_quantity

            position[
                "invested_cost"
            ] = round(
                new_cost,
                2,
            )

            position[
                "average_cost"
            ] = round(
                average_cost,
                4,
            )

            position[
                "last_transaction_at"
            ] = timestamp

            total_spent += (
                amount
            )

            transactions.append({

                "type":
                    "BUY",

                "symbol":
                    symbol,

                "quantity":
                    quantity,

                "price":
                    round(
                        price,
                        2,
                    ),

                "amount":
                    round(
                        amount,
                        2,
                    ),

                "source":
                    source,

                "timestamp":
                    timestamp,

            })

        if cash_spent is None:

            cash_spent = (
                total_spent
            )

        else:

            cash_spent = (
                self._safe_float(
                    cash_spent,
                    0.0,
                )
            )

        if cash_spent < 0:

            raise ValueError(
                "cash_spent cannot be negative"
            )

        cash_balance = (
            self._safe_float(
                updated.get(
                    "cash_balance",
                    0.0,
                ),
                0.0,
            )
        )

        if cash_spent > (
            cash_balance
            + 0.01
        ):

            raise ValueError(
                "Confirmed cash spent exceeds "
                "available portfolio cash"
            )

        updated[
            "cash_balance"
        ] = round(

            cash_balance
            - cash_spent,

            2,

        )

        updated.setdefault(
            "transactions",
            [],
        ).extend(
            transactions
        )

        updated[
            "transaction_count"
        ] = len(
            updated[
                "transactions"
            ]
        )

        # ==================================================
        # POST-BUY MARKET VALUATION
        #
        # A confirmed execution price is the best available
        # market mark at the instant the BUY is confirmed.
        #
        # Preserve existing valid marks for positions that
        # were not purchased in this operation, and replace
        # marks only for symbols with confirmed BUYs.
        #
        # mark_to_market() remains the single authoritative
        # implementation for current value, portfolio value,
        # actual weights and drift.
        # ==================================================

        valuation_price_map = {}

        for (
            position_symbol,
            position,
        ) in positions.items():

            if not isinstance(
                position,
                dict,
            ):

                continue

            existing_price = (
                self._safe_float(
                    position.get(
                        "current_price",
                        0.0,
                    ),
                    0.0,
                )
            )

            if existing_price > 0:

                valuation_price_map[
                    position_symbol
                ] = existing_price

        for transaction in transactions:

            if not isinstance(
                transaction,
                dict,
            ):

                continue

            transaction_symbol = (
                self._normalize_symbol(
                    transaction.get(
                        "symbol"
                    )
                )
            )

            transaction_price = (
                self._safe_float(
                    transaction.get(
                        "price",
                        0.0,
                    ),
                    0.0,
                )
            )

            if (
                transaction_symbol
                and transaction_price > 0
            ):

                valuation_price_map[
                    transaction_symbol
                ] = transaction_price

        updated = self.mark_to_market(

            state=
                updated,

            price_map=
                valuation_price_map,

        )

        updated[
            "updated_at"
        ] = self._timestamp()

        return updated

    # ======================================================
    # CORRECT CONFIRMED BUY
    #
    # Controlled accounting correction for an already
    # confirmed BUY transaction.
    #
    # This is NOT a new investment transaction and is NOT
    # a rebalance action.
    #
    # The selected BUY is corrected in place so transaction
    # history reflects economic truth. A separate CORRECTION
    # audit entry preserves the previous and corrected values.
    #
    # Position quantity / cost are rebuilt from all BUY
    # transactions for the symbol so this remains safe when
    # later SIP purchases exist.
    # ======================================================

    def correct_confirmed_buy(
        self,
        state,
        transaction_index,
        quantity,
        price,
        correction_date=None,
        reason="DATA_ENTRY_CORRECTION",
    ):

        if not isinstance(
            state,
            dict,
        ):

            raise TypeError(
                "state must be a dictionary"
            )

        updated = deepcopy(
            state
        )

        transactions = updated.get(
            "transactions",
            [],
        )

        if not isinstance(
            transactions,
            list,
        ):

            raise TypeError(
                "state transactions must be a list"
            )

        try:

            transaction_index = int(
                transaction_index
            )

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                "transaction_index must be an integer"
            )

        if (
            transaction_index < 0
            or transaction_index >= len(
                transactions
            )
        ):

            raise ValueError(
                "transaction_index is out of range"
            )

        original = transactions[
            transaction_index
        ]

        if not isinstance(
            original,
            dict,
        ):

            raise ValueError(
                "Selected transaction is invalid"
            )

        if str(
            original.get(
                "type",
                "",
            )
        ).strip().upper() != "BUY":

            raise ValueError(
                "Only BUY transactions can be corrected"
            )

        symbol = self._normalize_symbol(
            original.get(
                "symbol"
            )
        )

        if not symbol:

            raise ValueError(
                "Selected BUY has no valid symbol"
            )

        positions = updated.get(
            "positions",
            {},
        )

        if (
            not isinstance(
                positions,
                dict,
            )
            or symbol not in positions
        ):

            raise ValueError(
                f"Portfolio position not found: {symbol}"
            )

        quantity = int(
            self._safe_float(
                quantity,
                -1.0,
            )
        )

        price = self._safe_float(
            price,
            -1.0,
        )

        if quantity < 0:

            raise ValueError(
                "Corrected quantity cannot be negative"
            )

        if (
            quantity > 0
            and price <= 0
        ):

            raise ValueError(
                "Corrected BUY price must be positive"
            )

        if (
            quantity == 0
            and price < 0
        ):

            raise ValueError(
                "Corrected BUY price cannot be negative"
            )

        old_quantity = int(
            self._safe_float(
                original.get(
                    "quantity",
                    0,
                ),
                0.0,
            )
        )

        old_price = self._safe_float(
            original.get(
                "price",
                0.0,
            ),
            0.0,
        )

        old_amount = self._safe_float(
            original.get(
                "amount",
                (
                    old_quantity
                    * old_price
                ),
            ),
            0.0,
        )

        new_amount = (
            quantity
            * price
        )

        cash_delta = (
            old_amount
            - new_amount
        )

        current_cash = self._safe_float(
            updated.get(
                "cash_balance",
                0.0,
            ),
            0.0,
        )

        new_cash = (
            current_cash
            + cash_delta
        )

        if new_cash < -0.01:

            raise ValueError(
                "Correction requires more cash than "
                "the portfolio currently holds"
            )

        timestamp = (
            correction_date
            or self._timestamp()
        )

        before = {

            "quantity":
                old_quantity,

            "price":
                round(
                    old_price,
                    2,
                ),

            "amount":
                round(
                    old_amount,
                    2,
                ),

        }

        after = {

            "quantity":
                quantity,

            "price":
                round(
                    price,
                    2,
                ),

            "amount":
                round(
                    new_amount,
                    2,
                ),

        }

        original[
            "quantity"
        ] = quantity

        original[
            "price"
        ] = round(
            price,
            2,
        )

        original[
            "amount"
        ] = round(
            new_amount,
            2,
        )

        original[
            "corrected_at"
        ] = timestamp

        # --------------------------------------------------
        # REBUILD AUTHORITATIVE POSITION COST FROM ALL BUYS
        # --------------------------------------------------

        rebuilt_quantity = 0
        rebuilt_cost = 0.0
        last_transaction_at = None

        for transaction in transactions:

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

            transaction_quantity = int(
                self._safe_float(
                    transaction.get(
                        "quantity",
                        0,
                    ),
                    0.0,
                )
            )

            transaction_price = (
                self._safe_float(
                    transaction.get(
                        "price",
                        0.0,
                    ),
                    0.0,
                )
            )

            if (
                transaction_quantity < 0
                or (
                    transaction_quantity > 0
                    and transaction_price <= 0
                )
            ):

                raise ValueError(
                    f"Invalid BUY history for {symbol}"
                )

            rebuilt_quantity += (
                transaction_quantity
            )

            rebuilt_cost += (
                transaction_quantity
                * transaction_price
            )

            transaction_timestamp = (
                transaction.get(
                    "timestamp"
                )
            )

            if transaction_timestamp:

                last_transaction_at = (
                    transaction_timestamp
                )

        position = positions[
            symbol
        ]

        existing_market_price = (
            self._safe_float(
                position.get(
                    "current_price",
                    0.0,
                ),
                0.0,
            )
        )

        position[
            "quantity"
        ] = rebuilt_quantity

        position[
            "invested_cost"
        ] = round(
            rebuilt_cost,
            2,
        )

        position[
            "average_cost"
        ] = round(

            (
                rebuilt_cost
                / rebuilt_quantity
            )

            if rebuilt_quantity > 0

            else 0.0,

            4,

        )

        position[
            "last_transaction_at"
        ] = last_transaction_at

        updated[
            "cash_balance"
        ] = round(
            max(
                new_cash,
                0.0,
            ),
            2,
        )

        audit_entry = {

            "type":
                "CORRECTION",

            "symbol":
                symbol,

            "source":
                "PURCHASE_ENTRY_CORRECTION",

            "reason":
                str(
                    reason
                    or "DATA_ENTRY_CORRECTION"
                ),

            "corrected_transaction_index":
                transaction_index,

            "before":
                before,

            "after":
                after,

            "cash_delta":
                round(
                    cash_delta,
                    2,
                ),

            "timestamp":
                timestamp,

        }

        transactions.append(
            audit_entry
        )

        updated[
            "transaction_count"
        ] = len(
            transactions
        )

        updated[
            "updated_at"
        ] = self._timestamp()

        # Preserve market valuation independently from
        # corrected purchase economics.

        valuation_price_map = {}

        for (
            position_symbol,
            position_row,
        ) in positions.items():

            if not isinstance(
                position_row,
                dict,
            ):

                continue

            market_price = (
                self._safe_float(
                    position_row.get(
                        "current_price",
                        0.0,
                    ),
                    0.0,
                )
            )

            if market_price > 0:

                valuation_price_map[
                    position_symbol
                ] = market_price

        if (
            existing_market_price > 0
        ):

            valuation_price_map[
                symbol
            ] = existing_market_price

        updated = self.mark_to_market(

            state=
                updated,

            price_map=
                valuation_price_map,

        )

        return updated


    def add_cash(
        self,
        state,
        amount,
        source="SIP",
        transaction_date=None,
    ):

        amount = (
            self._safe_float(
                amount,
                0.0,
            )
        )

        if amount < 0:

            raise ValueError(
                "Cash addition cannot be negative"
            )

        updated = deepcopy(
            state
        )

        timestamp = (
            transaction_date
            or self._timestamp()
        )

        current_cash = (
            self._safe_float(
                updated.get(
                    "cash_balance",
                    0.0,
                ),
                0.0,
            )
        )

        updated[
            "cash_balance"
        ] = round(

            current_cash
            + amount,

            2,

        )

        if amount > 0:

            updated.setdefault(
                "transactions",
                [],
            ).append({

                "type":
                    "CASH_IN",

                "amount":
                    round(
                        amount,
                        2,
                    ),

                "source":
                    source,

                "timestamp":
                    timestamp,

            })

        updated[
            "transaction_count"
        ] = len(
            updated.get(
                "transactions",
                [],
            )
        )

        updated[
            "updated_at"
        ] = self._timestamp()

        return updated

    def mark_to_market(
        self,
        state,
        price_map,
    ):

        if not isinstance(
            price_map,
            dict,
        ):

            raise TypeError(
                "price_map must be a dictionary"
            )

        updated = deepcopy(
            state
        )

        normalized_prices = {

            self._normalize_symbol(
                symbol
            ):
                self._safe_float(
                    price,
                    0.0,
                )

            for (
                symbol,
                price,
            )
            in price_map.items()

        }

        positions = updated.get(
            "positions",
            {},
        )

        invested_market_value = 0.0

        for symbol, position in (
            positions.items()
        ):

            price = (
                normalized_prices.get(
                    symbol,
                    self._safe_float(
                        position.get(
                            "current_price",
                            0.0,
                        ),
                        0.0,
                    ),
                )
            )

            if price < 0:

                raise ValueError(
                    f"Negative market price for {symbol}"
                )

            quantity = (
                self._safe_float(
                    position.get(
                        "quantity",
                        0,
                    ),
                    0.0,
                )
            )

            current_value = (
                quantity
                * price
            )

            position[
                "current_price"
            ] = round(
                price,
                2,
            )

            position[
                "current_value"
            ] = round(
                current_value,
                2,
            )

            invested_market_value += (
                current_value
            )

        cash_balance = (
            self._safe_float(
                updated.get(
                    "cash_balance",
                    0.0,
                ),
                0.0,
            )
        )

        total_portfolio_value = (

            invested_market_value
            + cash_balance

        )

        for position in (
            positions.values()
        ):

            current_value = (
                self._safe_float(
                    position.get(
                        "current_value",
                        0.0,
                    ),
                    0.0,
                )
            )

            target_weight = (
                self._safe_float(
                    position.get(
                        "target_weight",
                        0.0,
                    ),
                    0.0,
                )
            )

            actual_weight = (

                current_value
                / total_portfolio_value
                * 100.0

                if total_portfolio_value > 0

                else 0.0

            )

            position[
                "actual_weight"
            ] = round(
                actual_weight,
                4,
            )

            position[
                "drift_pct"
            ] = round(

                actual_weight
                - target_weight,

                4,

            )

            position[
                "allocation_state"
            ] = self._allocation_state(
                target_weight,
                actual_weight,
            )

        updated[
            "invested_market_value"
        ] = round(
            invested_market_value,
            2,
        )

        updated[
            "total_portfolio_value"
        ] = round(
            total_portfolio_value,
            2,
        )

        updated[
            "updated_at"
        ] = self._timestamp()

        return updated

    def _allocation_state(
        self,
        target_weight,
        actual_weight,
        tolerance_pct=1.0,
    ):
        """
        Classify allocation drift without creating a trade decision.

        IMPORTANT:
        - UNDER_TARGET may inform fresh-capital / Smart SIP allocation.
        - NEAR_TARGET means no meaningful allocation drift.
        - ABOVE_TARGET is informational only.
        - ABOVE_TARGET must never, by itself, mean SELL or TRIM.

        Alpha 12 is a low-churn investment portfolio. Strong holdings
        are allowed to run above strategic target weight through market
        appreciation unless a separate investment or concentration-risk
        decision explicitly justifies action.
        """

        target = self._safe_float(
            target_weight,
            0.0,
        )

        actual = self._safe_float(
            actual_weight,
            0.0,
        )

        tolerance = max(
            0.0,
            self._safe_float(
                tolerance_pct,
                1.0,
            ),
        )

        drift = (
            actual
            - target
        )

        if drift < -tolerance:
            return "UNDER_TARGET"

        if drift > tolerance:
            return "ABOVE_TARGET"

        return "NEAR_TARGET"

    def create_snapshot(
        self,
        state,
        label=None,
    ):

        snapshot_time = (
            self._timestamp()
        )

        positions = (
            state.get(
                "positions",
                {},
            )
        )

        snapshot = {

            "timestamp":
                snapshot_time,

            "label":
                label,

            "cash_balance":
                round(
                    self._safe_float(
                        state.get(
                            "cash_balance",
                            0.0,
                        ),
                        0.0,
                    ),
                    2,
                ),

            "invested_market_value":
                round(
                    self._safe_float(
                        state.get(
                            "invested_market_value",
                            0.0,
                        ),
                        0.0,
                    ),
                    2,
                ),

            "total_portfolio_value":
                round(
                    self._safe_float(
                        state.get(
                            "total_portfolio_value",
                            0.0,
                        ),
                        0.0,
                    ),
                    2,
                ),

            "positions": {

                symbol: {

                    "quantity":
                        item.get(
                            "quantity",
                            0,
                        ),

                    "average_cost":
                        item.get(
                            "average_cost",
                            0.0,
                        ),

                    "invested_cost":
                        item.get(
                            "invested_cost",
                            0.0,
                        ),

                    "current_price":
                        item.get(
                            "current_price",
                            0.0,
                        ),

                    "current_value":
                        item.get(
                            "current_value",
                            0.0,
                        ),

                    "target_weight":
                        item.get(
                            "target_weight",
                            0.0,
                        ),

                    "actual_weight":
                        item.get(
                            "actual_weight",
                            0.0,
                        ),

                    "drift_pct":
                        item.get(
                            "drift_pct",
                            0.0,
                        ),

                }

                for (
                    symbol,
                    item,
                )
                in positions.items()

            },

        }

        updated = deepcopy(
            state
        )

        updated.setdefault(
            "snapshots",
            [],
        ).append(
            snapshot
        )

        updated[
            "updated_at"
        ] = snapshot_time

        return {

            "state":
                updated,

            "snapshot":
                snapshot,

        }

    def holdings_for_smart_sip(
        self,
        state,
    ):

        positions = state.get(
            "positions",
            {},
        )

        return {

            symbol:
                int(
                    self._safe_float(
                        item.get(
                            "quantity",
                            0,
                        ),
                        0.0,
                    )
                )

            for (
                symbol,
                item,
            )
            in positions.items()

        }


    # ======================================================
    # PERSISTENCE
    # ======================================================

    def save_state(
        self,
        state,
        path=None,
    ):

        if not isinstance(
            state,
            dict,
        ):

            raise TypeError(
                "state must be a dictionary"
            )

        target = (

            Path(path)

            if path is not None

            else self.get_default_state_path()

        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Write to a temporary file first so an interrupted
        # write does not destroy the last valid portfolio state.

        temp_path = target.with_suffix(
            target.suffix + ".tmp"
        )

        payload = deepcopy(
            state
        )

        payload[
            "state_version"
        ] = self.STATE_VERSION

        temp_path.write_text(

            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),

            encoding="utf-8",

        )

        temp_path.replace(
            target
        )

        return {

            "status":
                "OK",

            "path":
                str(
                    target
                ),

            "state_version":
                self.STATE_VERSION,

        }

    def load_state(
        self,
        path=None,
    ):

        target = (

            Path(path)

            if path is not None

            else self.get_default_state_path()

        )

        if not target.exists():

            return {

                "status":
                    "NOT_FOUND",

                "path":
                    str(
                        target
                    ),

                "state":
                    None,

            }

        try:

            payload = json.loads(

                target.read_text(
                    encoding="utf-8"
                )

            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:

            return {

                "status":
                    "ERROR",

                "path":
                    str(
                        target
                    ),

                "state":
                    None,

                "error":
                    str(
                        exc
                    ),

            }

        if not isinstance(
            payload,
            dict,
        ):

            return {

                "status":
                    "ERROR",

                "path":
                    str(
                        target
                    ),

                "state":
                    None,

                "error":
                    "Portfolio state root must be a dictionary",

            }

        positions = payload.get(
            "positions"
        )

        if not isinstance(
            positions,
            dict,
        ):

            return {

                "status":
                    "ERROR",

                "path":
                    str(
                        target
                    ),

                "state":
                    None,

                "error":
                    "Portfolio state has invalid positions",

            }

        return {

            "status":
                "OK",

            "path":
                str(
                    target
                ),

            "state_version":
                payload.get(
                    "state_version"
                ),

            "state":
                payload,

        }


def create_portfolio_state(
    portfolio,
    cash_balance=0.0,
):

    return (
        PortfolioStateService()
        .create_state(
            portfolio=
                portfolio,

            cash_balance=
                cash_balance,
        )
    )
