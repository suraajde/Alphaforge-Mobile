from __future__ import annotations


class CapitalDeploymentService:
    """
    AlphaForge Capital Deployment Engine.

    Converts portfolio target weights into executable whole-share
    allocations for a supplied investment amount and price map.

    Responsibilities:
    - Preserve upstream target portfolio weights.
    - Convert target percentages into target rupee allocations.
    - Buy only whole shares.
    - Redistribute usable residual cash toward underweight positions.
    - Avoid unnecessary target overshoot.
    - Report actual allocation and portfolio drift.

    This service does NOT:
    - Select Alpha 12 stocks.
    - Recalculate target weights.
    - Fetch live market prices.
    """

    def __init__(
        self,
        overshoot_tolerance_pct=0.75,
    ):

        self.overshoot_tolerance_pct = max(
            0.0,
            float(
                overshoot_tolerance_pct
            ),
        )

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

        return str(
            value
            or ""
        ).strip().upper()

    def _validate_portfolio(
        self,
        portfolio,
    ):

        if not isinstance(
            portfolio,
            list,
        ):

            raise TypeError(
                "portfolio must be a list"
            )

        clean = []

        seen = set()

        for item in portfolio:

            if not isinstance(
                item,
                dict,
            ):
                continue

            symbol = (
                self._normalize_symbol(
                    item.get(
                        "symbol"
                    )
                )
            )

            if not symbol:
                continue

            if symbol in seen:

                raise ValueError(
                    f"Duplicate portfolio symbol: {symbol}"
                )

            target_weight = (
                self._safe_float(
                    item.get(
                        "target_weight"
                    ),
                    0.0,
                )
            )

            if target_weight < 0:

                raise ValueError(
                    f"Negative target weight for {symbol}"
                )

            row = dict(
                item
            )

            row[
                "symbol"
            ] = symbol

            row[
                "target_weight"
            ] = target_weight

            clean.append(
                row
            )

            seen.add(
                symbol
            )

        if not clean:

            return []

        total_weight = sum(

            item[
                "target_weight"
            ]

            for item in clean

        )

        if total_weight <= 0:

            raise ValueError(
                "Portfolio target weights must total above zero"
            )

        return clean

    def _prepare_prices(
        self,
        portfolio,
        price_map,
    ):

        if not isinstance(
            price_map,
            dict,
        ):

            raise TypeError(
                "price_map must be a dictionary"
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

        missing = []

        invalid = []

        prices = {}

        for item in portfolio:

            symbol = item[
                "symbol"
            ]

            if symbol not in normalized_prices:

                missing.append(
                    symbol
                )

                continue

            price = normalized_prices[
                symbol
            ]

            if price <= 0:

                invalid.append(
                    symbol
                )

                continue

            prices[
                symbol
            ] = price

        if missing or invalid:

            parts = []

            if missing:

                parts.append(

                    "Missing prices: "
                    + ", ".join(
                        missing
                    )

                )

            if invalid:

                parts.append(

                    "Invalid prices: "
                    + ", ".join(
                        invalid
                    )

                )

            raise ValueError(
                " | ".join(
                    parts
                )
            )

        return prices

    @staticmethod
    def _allocation_metrics(
        rows,
        capital,
    ):

        invested = sum(

            row[
                "actual_amount"
            ]

            for row in rows

        )

        cash_remaining = max(
            0.0,
            capital
            - invested,
        )

        for row in rows:

            actual_weight = (

                row[
                    "actual_amount"
                ]
                / capital
                * 100.0

                if capital > 0

                else 0.0

            )

            row[
                "actual_weight"
            ] = actual_weight

            row[
                "drift_pct"
            ] = (

                actual_weight
                - row[
                    "target_weight"
                ]

            )

            row[
                "target_gap_amount"
            ] = (

                row[
                    "target_amount"
                ]
                - row[
                    "actual_amount"
                ]

            )

        return (
            invested,
            cash_remaining,
        )

    def deploy(
        self,
        portfolio,
        capital,
        price_map,
    ):

        capital = self._safe_float(
            capital,
            0.0,
        )

        if capital <= 0:

            raise ValueError(
                "capital must be greater than zero"
            )

        clean = (
            self._validate_portfolio(
                portfolio
            )
        )

        if not clean:

            return {

                "status":
                    "EMPTY",

                "capital":
                    round(
                        capital,
                        2,
                    ),

                "position_count":
                    0,

                "allocations":
                    [],

                "invested_amount":
                    0.0,

                "cash_remaining":
                    round(
                        capital,
                        2,
                    ),

                "deployment_pct":
                    0.0,

            }

        prices = (
            self._prepare_prices(
                clean,
                price_map,
            )
        )

        total_target_weight = sum(

            item[
                "target_weight"
            ]

            for item in clean

        )

        rows = []

        # ==================================================
        # INITIAL WHOLE-SHARE ALLOCATION
        # ==================================================

        for item in clean:

            symbol = item[
                "symbol"
            ]

            price = prices[
                symbol
            ]

            normalized_target_weight = (

                item[
                    "target_weight"
                ]
                / total_target_weight
                * 100.0

            )

            target_amount = (

                capital
                * normalized_target_weight
                / 100.0

            )

            quantity = int(

                target_amount
                // price

            )

            actual_amount = (

                quantity
                * price

            )

            row = dict(
                item
            )

            row[
                "target_weight"
            ] = normalized_target_weight

            row[
                "target_amount"
            ] = target_amount

            row[
                "price"
            ] = price

            row[
                "quantity"
            ] = quantity

            row[
                "actual_amount"
            ] = actual_amount

            rows.append(
                row
            )

        invested, cash_remaining = (
            self._allocation_metrics(
                rows,
                capital,
            )
        )

        # ==================================================
        # FULL CAPITAL DEPLOYMENT (ZERO CASH DRAG RULE)
        #
        # Deploy 100% of available capital across whole shares.
        # Continuously allocate 1 additional share at a time
        # to the most underweight affordable position until
        # residual cash is less than the lowest-priced stock.
        # ==================================================

        while True:

            affordable = []

            for index, row in enumerate(
                rows
            ):

                price = row[
                    "price"
                ]

                if price > (
                    cash_remaining
                    + 1e-9
                ):

                    continue

                current_gap = (

                    row[
                        "target_amount"
                    ]
                    - row[
                        "actual_amount"
                    ]

                )

                current_gap_pct = (

                    row[
                        "target_weight"
                    ]
                    - row[
                        "actual_weight"
                    ]

                )

                affordable.append((

                    current_gap_pct,

                    current_gap,

                    row[
                        "portfolio_quality_score"
                    ]
                    if isinstance(
                        row.get(
                            "portfolio_quality_score"
                        ),
                        (
                            int,
                            float,
                        ),
                    )
                    else 0.0,

                    -price,

                    index,

                ))

            if not affordable:

                break

            affordable.sort(
                reverse=True
            )

            selected_index = (
                affordable[
                    0
                ][
                    -1
                ]
            )

            selected = rows[
                selected_index
            ]

            selected[
                "quantity"
            ] += 1

            selected[
                "actual_amount"
            ] += selected[
                "price"
            ]

            invested, cash_remaining = (
                self._allocation_metrics(
                    rows,
                    capital,
                )
            )

        # ==================================================
        # FINAL ROUNDING / DIAGNOSTICS
        # ==================================================

        invested, cash_remaining = (
            self._allocation_metrics(
                rows,
                capital,
            )
        )

        for row in rows:

            row[
                "target_weight"
            ] = round(
                row[
                    "target_weight"
                ],
                2,
            )

            row[
                "target_amount"
            ] = round(
                row[
                    "target_amount"
                ],
                2,
            )

            row[
                "price"
            ] = round(
                row[
                    "price"
                ],
                2,
            )

            row[
                "actual_amount"
            ] = round(
                row[
                    "actual_amount"
                ],
                2,
            )

            row[
                "actual_weight"
            ] = round(
                row[
                    "actual_weight"
                ],
                2,
            )

            row[
                "drift_pct"
            ] = round(
                row[
                    "drift_pct"
                ],
                2,
            )

            row[
                "target_gap_amount"
            ] = round(
                row[
                    "target_gap_amount"
                ],
                2,
            )

            row[
                "buyable"
            ] = (
                row[
                    "quantity"
                ]
                > 0
            )

        rows.sort(

            key=lambda row: (

                row.get(
                    "alpha12_rank",
                    row.get(
                        "rank",
                        999,
                    ),
                ),

                row[
                    "symbol"
                ],

            )

        )

        deployment_pct = (

            invested
            / capital
            * 100.0

        )

        unbuyable_symbols = [

            row[
                "symbol"
            ]

            for row in rows

            if row[
                "quantity"
            ] == 0

        ]

        return {

            "status":
                "OK",

            "capital":
                round(
                    capital,
                    2,
                ),

            "position_count":
                len(
                    rows
                ),

            "allocations":
                rows,

            "invested_amount":
                round(
                    invested,
                    2,
                ),

            "cash_remaining":
                round(
                    cash_remaining,
                    2,
                ),

            "deployment_pct":
                round(
                    deployment_pct,
                    2,
                ),

            "unbuyable_count":
                len(
                    unbuyable_symbols
                ),

            "unbuyable_symbols":
                unbuyable_symbols,

            "overshoot_tolerance_pct":
                self.overshoot_tolerance_pct,

        }


def deploy_capital(
    portfolio,
    capital,
    price_map,
    overshoot_tolerance_pct=0.75,
):

    service = CapitalDeploymentService(

        overshoot_tolerance_pct=
            overshoot_tolerance_pct

    )

    return service.deploy(

        portfolio=
            portfolio,

        capital=
            capital,

        price_map=
            price_map,

    )
