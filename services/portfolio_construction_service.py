from __future__ import annotations

from collections import Counter, defaultdict


class PortfolioConstructionService:
    """
    AlphaForge Alpha 12 Portfolio Construction Engine.

    Converts the selected Alpha 12 universe into deterministic
    target portfolio weights.

    Design principles:
    - Alpha 12 selection remains authoritative for stock inclusion.
    - Portfolio weighting is downstream and independent.
    - Higher Alpha quality may receive moderately higher weight.
    - No stock may exceed the configured hard maximum.
    - Sector concentration receives a portfolio-level adjustment.
    - Final target weights sum to exactly 100%.
    """

    def __init__(
        self,
        max_stock_weight=10.0,
        sector_soft_limit=25.0,
    ):
        self.max_stock_weight = float(
            max_stock_weight
        )

        self.sector_soft_limit = float(
            sector_soft_limit
        )

        if self.max_stock_weight <= 0:
            raise ValueError(
                "max_stock_weight must be positive"
            )

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):
        try:
            if value is None:
                return float(default)

            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return float(default)

    def _quality_score(
        self,
        item,
    ):
        """
        Use the final Alpha 12 selection score when available.

        Fall back safely to base/composite scores so the portfolio
        service remains robust to partial historical contracts.
        """

        score = item.get(
            "alpha12_selection_score"
        )

        if score is None:
            score = item.get(
                "selection_score"
            )

        if score is None:
            score = item.get(
                "alpha12_base_score"
            )

        if score is None:
            score = item.get(
                "composite_score"
            )

        return max(
            0.0,
            self._safe_float(
                score,
                0.0,
            ),
        )

    def _available_score(
        self,
        item,
        keys,
    ):
        """
        Return the first valid non-negative score found.

        Allows portfolio construction to consume richer AlphaForge
        scoring contracts while remaining backward-compatible with
        historical selection payloads.
        """

        for key in keys:

            value = item.get(
                key
            )

            if value is None:
                continue

            return max(
                0.0,
                min(
                    100.0,
                    self._safe_float(
                        value,
                        0.0,
                    ),
                ),
            )

        return None

    def _investment_quality_score(
        self,
        item,
    ):
        """
        Build direct long-term investment quality evidence.

        Granular business factors are preferred when sufficient
        evidence is available:

        - profitability: 30%
        - growth: 30%
        - financial strength: 25%
        - valuation: 15%

        Valuation is intentionally a restraint rather than the
        dominant factor so an exceptional compounder is not
        mechanically suppressed solely because it trades at a
        premium valuation.

        When fewer than two granular factors are available, the
        aggregate fundamental score is used as a backward-compatible
        fallback.
        """
        legacy = self._available_score(
            item,
            (
                "investment_quality",
                "investment_quality_score",
                "fundamental_score",
                "portfolio_fundamental_score",
            ),
        )

        if legacy is not None:
            return legacy

        profitability = self._available_score(
            item,
            (
                "profitability_score",
                "portfolio_profitability_score",
            ),
        )

        growth = self._available_score(
            item,
            (
                "growth_score",
                "portfolio_growth_score",
            ),
        )

        financial_strength = self._available_score(
            item,
            (
                "financial_strength_score",
                "portfolio_financial_strength_score",
            ),
        )

        valuation = self._available_score(
            item,
            (
                "valuation_score",
                "portfolio_valuation_score",
            ),
        )

        granular = [
            (
                profitability,
                0.30,
            ),
            (
                growth,
                0.30,
            ),
            (
                financial_strength,
                0.25,
            ),
            (
                valuation,
                0.15,
            ),
        ]

        available = [
            (
                score,
                weight,
            )
            for score, weight in granular
            if score is not None
        ]

        if len(available) >= 2:

            total_weight = sum(
                weight
                for _, weight in available
            )

            return sum(
                score * weight
                for score, weight in available
            ) / total_weight

        return self._available_score(
            item,
            (
                "fundamental_score",
                "portfolio_fundamental_score",
            ),
        )
    def _conviction_score(
        self,
        item,
    ):
        """
        Build an investment-oriented portfolio conviction score.

        Alpha 12 selection strength remains the anchor so portfolio
        construction does not become a second independent stock
        selection engine.

        Direct investment quality materially influences capital
        sizing. Risk resilience is meaningful but secondary, while
        readiness remains a small timing influence.

        Architecture:

        - selection strength: 50%
        - direct investment quality: 40%
        - risk resilience: 7%
        - readiness: 3%

        Available components are dynamically renormalized for
        backward compatibility with historical payloads.
        """

        selection = self._quality_score(
            item
        )

        investment_quality = (
            self._investment_quality_score(
                item
            )
        )

        risk = self._available_score(
            item,
            (
    "portfolio_risk",
    "risk_score",
    "portfolio_risk_score",
)
        )

        readiness = self._available_score(
            item,
           (
    "portfolio_readiness",
    "readiness_score",
    "portfolio_readiness_score",
)
        )

        components = [
            (
                selection,
                0.50,
            ),
        ]

        if investment_quality is not None:

            components.append(
                (
                    investment_quality,
                    0.40,
                )
            )

        if risk is not None:

            components.append(
                (
                    risk,
                    0.07,
                )
            )

        if readiness is not None:

            components.append(
                (
                    readiness,
                    0.03,
                )
            )

        total_weight = sum(
            weight
            for _, weight in components
        )

        if total_weight <= 0:
            return 0.0

        return sum(
            score * weight
            for score, weight in components
        ) / total_weight
    def _sector_adjusted_scores(
        self,
        selected,
    ):
        """
        Apply a mild portfolio-level sector adjustment.

        This does NOT redo Alpha 12 selection.

        It only prevents a sector with several selected names from
        automatically receiving excessive portfolio capital.
        """

        sector_counts = Counter(

            str(
                item.get(
                    "sector",
                    "UNKNOWN",
                )
            ).strip()
            or "UNKNOWN"

            for item in selected

        )

        adjusted = []

        for item in selected:

            sector = (
                str(
                    item.get(
                        "sector",
                        "UNKNOWN",
                    )
                ).strip()
                or "UNKNOWN"
            )

            quality = self._conviction_score(
                item
            )

            count = sector_counts[
                sector
            ]

            if count <= 2:
                multiplier = 1.0

            elif count == 3:
                multiplier = 0.97

            else:
                multiplier = 0.94

            adjusted.append({

                "item":
                    item,

                "quality_score":
                    quality,

                "sector_multiplier":
                    multiplier,

                "allocation_score":
                    quality
                    * multiplier,

            })

        return adjusted

    def _normalize_with_cap(
        self,
        raw_weights,
    ):
        """
        Normalize weights to 100% while enforcing the hard stock cap.

        Uses iterative redistribution so excess weight from capped
        positions is redistributed only to uncapped positions.
        """

        count = len(
            raw_weights
        )

        if count == 0:
            return []

        if (
            self.max_stock_weight
            * count
            < 100.0
        ):
            raise ValueError(
                "max_stock_weight is too low for "
                f"{count} portfolio positions"
            )

        total_raw = sum(
            raw_weights
        )

        if total_raw <= 0:

            weights = [
                100.0 / count
                for _ in raw_weights
            ]

        else:

            weights = [

                (
                    value
                    / total_raw
                )
                * 100.0

                for value in raw_weights

            ]

        fixed = {}
        active = set(
            range(
                count
            )
        )

        while active:

            capped_now = [

                index

                for index in active

                if weights[
                    index
                ]
                > self.max_stock_weight
                + 1e-12

            ]

            if not capped_now:
                break

            for index in capped_now:

                fixed[
                    index
                ] = (
                    self.max_stock_weight
                )

                active.remove(
                    index
                )

            remaining_weight = (
                100.0
                - sum(
                    fixed.values()
                )
            )

            if not active:
                break

            active_raw_total = sum(

                raw_weights[
                    index
                ]

                for index in active

            )

            if active_raw_total <= 0:

                equal_remaining = (
                    remaining_weight
                    / len(
                        active
                    )
                )

                for index in active:

                    weights[
                        index
                    ] = (
                        equal_remaining
                    )

            else:

                for index in active:

                    weights[
                        index
                    ] = (

                        raw_weights[
                            index
                        ]
                        / active_raw_total
                        * remaining_weight

                    )

        for (
            index,
            value,
        ) in fixed.items():

            weights[
                index
            ] = value

        return weights

    @staticmethod
    def _round_to_100(
        weights,
        decimals=2,
    ):
        """
        Round display weights while preserving an exact 100% total.
        """

        if not weights:
            return []

        rounded = [

            round(
                value,
                decimals,
            )

            for value in weights

        ]

        difference = round(

            100.0
            - sum(
                rounded
            ),

            decimals,

        )

        if difference:

            index = max(

                range(
                    len(
                        rounded
                    )
                ),

                key=lambda i:
                    rounded[
                        i
                    ],

            )

            rounded[
                index
            ] = round(

                rounded[
                    index
                ]
                + difference,

                decimals,

            )

        return rounded

    def build(
        self,
        selected,
    ):
        """
        Build target portfolio weights from Alpha 12 selected stocks.
        """

        if not isinstance(
            selected,
            list,
        ):
            raise TypeError(
                "selected must be a list"
            )

        clean = [

            dict(
                item
            )

            for item in selected

            if isinstance(
                item,
                dict,
            )
            and str(
                item.get(
                    "symbol",
                    "",
                )
            ).strip()

        ]

        if not clean:

            return {

                "status":
                    "EMPTY",

                "position_count":
                    0,

                "portfolio":
                    [],

                "total_target_weight":
                    0.0,

                "sector_weights":
                    {},

                "category_weights":
                    {},

            }

        scored = (
            self._sector_adjusted_scores(
                clean
            )
        )

        raw_scores = [

            row[
                "allocation_score"
            ]

            for row in scored

        ]

        weights = (
            self._normalize_with_cap(
                raw_scores
            )
        )

        weights = (
            self._round_to_100(
                weights,
                decimals=2,
            )
        )

        portfolio = []

        sector_weights = defaultdict(
            float
        )

        category_weights = defaultdict(
            float
        )

        for (
            row,
            target_weight,
        ) in zip(
            scored,
            weights,
        ):

            source = dict(
                row[
                    "item"
                ]
            )

            sector = (
                str(
                    source.get(
                        "sector",
                        "UNKNOWN",
                    )
                ).strip()
                or "UNKNOWN"
            )

            category = (
                str(
                    source.get(
                        "category",
                        "UNKNOWN",
                    )
                ).strip()
                or "UNKNOWN"
            )

            source[
                "portfolio_quality_score"
            ] = round(

                row[
                    "quality_score"
                ],

                4,

            )

            source[
                "portfolio_sector_multiplier"
            ] = row[
                "sector_multiplier"
            ]

            source[
                "portfolio_allocation_score"
            ] = round(

                row[
                    "allocation_score"
                ],

                4,

            )

            source[
                "target_weight"
            ] = target_weight

            portfolio.append(
                source
            )

            sector_weights[
                sector
            ] += target_weight

            category_weights[
                category
            ] += target_weight

        for item in portfolio:

            item[
                "sector_target_weight"
            ] = round(

                sector_weights[
                    str(
                        item.get(
                            "sector",
                            "UNKNOWN",
                        )
                    ).strip()
                    or "UNKNOWN"
                ],

                2,

            )

        return {

            "status":
                "OK",

            "position_count":
                len(
                    portfolio
                ),

            "portfolio":
                portfolio,

            "total_target_weight":
                round(
                    sum(
                        item[
                            "target_weight"
                        ]
                        for item in portfolio
                    ),
                    2,
                ),

            "max_stock_weight":
                self.max_stock_weight,

            "sector_soft_limit":
                self.sector_soft_limit,

            "sector_weights": {

                key:
                    round(
                        value,
                        2,
                    )

                for (
                    key,
                    value,
                )
                in sector_weights.items()

            },

            "category_weights": {

                key:
                    round(
                        value,
                        2,
                    )

                for (
                    key,
                    value,
                )
                in category_weights.items()

            },

        }


def build_alpha12_portfolio(
    selected,
    max_stock_weight=10.0,
    sector_soft_limit=25.0,
):

    service = (
        PortfolioConstructionService(

            max_stock_weight=
                max_stock_weight,

            sector_soft_limit=
                sector_soft_limit,

        )
    )

    return service.build(
        selected
    )
