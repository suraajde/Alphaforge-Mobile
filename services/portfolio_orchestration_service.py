from __future__ import annotations

from copy import deepcopy

from services.portfolio_construction_service import (
    build_alpha12_portfolio,
)
from services.capital_deployment_service import (
    deploy_capital,
)
from services.smart_sip_service import (
    build_smart_sip,
)
from services.portfolio_state_service import (
    PortfolioStateService,
)
from services.portfolio_analytics_service import (
    PortfolioAnalyticsService,
    PortfolioHolding,
)
from services.portfolio_health_service import (
    PortfolioHealthService,
)
from services.recommendation_engine import (
    RecommendationEngine,
)
from services.decision_engine import (
    DecisionEngine,
)


class PortfolioOrchestrationService:
    """
    AlphaForge Portfolio Orchestration Engine.

    Coordinates the validated Sprint 11.4 portfolio services:

        Alpha 12
            ->
        Portfolio Construction
            ->
        Initial Capital Deployment
            ->
        User Confirmation
            ->
        Persistent Portfolio State
            ->
        Smart SIP
            ->
        User Confirmation
            ->
        Updated Persistent State

    Architectural rule:

    PREPARATION methods are read-only recommendations.

    CONFIRMATION methods are the only methods allowed to
    mutate portfolio state.

    This service does NOT duplicate:
    - Alpha 12 selection
    - portfolio weighting
    - whole-share deployment
    - Smart SIP allocation
    - accounting / average-cost calculations
    """

    def __init__(
        self,
        max_stock_weight=10.0,
        sector_soft_limit=25.0,
        overshoot_tolerance_pct=0.75,
        state_service=None,
        analytics_service=None,
        health_service=None,
        recommendation_engine=None,
        decision_engine=None,
    ):

        self.max_stock_weight = float(
            max_stock_weight
        )

        self.sector_soft_limit = float(
            sector_soft_limit
        )

        self.overshoot_tolerance_pct = float(
            overshoot_tolerance_pct
        )

        self.state_service = (
            state_service
            if state_service is not None
            else PortfolioStateService()
        )

        self.analytics_service = (
            analytics_service
            if analytics_service is not None
            else PortfolioAnalyticsService()
        )

        self.health_service = (
            health_service
            if health_service is not None
            else PortfolioHealthService()
        )

        self.recommendation_engine = (
            recommendation_engine
            if recommendation_engine is not None
            else RecommendationEngine()
        )

        self.decision_engine = (
            decision_engine
            if decision_engine is not None
            else DecisionEngine()
        )

    # ======================================================
    # HELPERS
    # ======================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

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
    def _require_ok(
        result,
        operation,
    ):

        if not isinstance(
            result,
            dict,
        ):

            raise ValueError(
                f"{operation} returned invalid result"
            )

        status = result.get(
            "status"
        )

        if status != "OK":

            raise ValueError(
                f"{operation} failed with status: "
                f"{status}"
            )

        return result

    # ======================================================
    # PREPARE TARGET PORTFOLIO
    #
    # READ ONLY
    # ======================================================

    def prepare_target_portfolio(
        self,
        alpha12,
    ):

        result = build_alpha12_portfolio(

            selected=
                alpha12,

            max_stock_weight=
                self.max_stock_weight,

            sector_soft_limit=
                self.sector_soft_limit,

        )

        self._require_ok(
            result,
            "Portfolio construction",
        )

        return result

    # ======================================================
    # PREPARE INITIAL INVESTMENT
    #
    # READ ONLY
    #
    # This method must never create holdings or transactions.
    # ======================================================

    def prepare_initial_investment(
        self,
        alpha12,
        capital,
        price_map,
    ):

        capital = self._safe_float(
            capital,
            0.0,
        )

        if capital <= 0:

            raise ValueError(
                "Initial capital must be greater than zero"
            )

        portfolio_result = (
            self.prepare_target_portfolio(
                alpha12
            )
        )

        portfolio = portfolio_result.get(
            "portfolio",
            [],
        )

        deployment = deploy_capital(

            portfolio=
                portfolio,

            capital=
                capital,

            price_map=
                price_map,

            overshoot_tolerance_pct=
                self.overshoot_tolerance_pct,

        )

        self._require_ok(
            deployment,
            "Capital deployment",
        )

        return {

            "status":
                "OK",

            "mode":
                "INITIAL_INVESTMENT_RECOMMENDATION",

            "confirmed":
                False,

            "portfolio_result":
                portfolio_result,

            "portfolio":
                deepcopy(
                    portfolio
                ),

            "capital":
                deployment.get(
                    "capital",
                    capital,
                ),

            "allocations":
                deepcopy(
                    deployment.get(
                        "allocations",
                        [],
                    )
                ),

            "invested_amount":
                deployment.get(
                    "invested_amount",
                    0.0,
                ),

            "cash_remaining":
                deployment.get(
                    "cash_remaining",
                    capital,
                ),

            "deployment_pct":
                deployment.get(
                    "deployment_pct",
                    0.0,
                ),

            "unbuyable_symbols":
                deepcopy(
                    deployment.get(
                        "unbuyable_symbols",
                        [],
                    )
                ),

        }

    # ======================================================
    # CONFIRM INITIAL INVESTMENT
    #
    # STATE CHANGING
    #
    # A recommendation becomes real portfolio state only here.
    # ======================================================

    def confirm_initial_investment(
        self,
        recommendation,
        confirmed_buys=None,
        transaction_date=None,
        save=True,
        path=None,
    ):

        self._require_ok(
            recommendation,
            "Initial investment recommendation",
        )

        if recommendation.get(
            "mode"
        ) != "INITIAL_INVESTMENT_RECOMMENDATION":

            raise ValueError(
                "Invalid initial investment recommendation"
            )

        portfolio = deepcopy(
            recommendation.get(
                "portfolio",
                [],
            )
        )

        capital = self._safe_float(
            recommendation.get(
                "capital",
                0.0,
            ),
            0.0,
        )

        if not portfolio:

            raise ValueError(
                "Recommendation contains no portfolio"
            )

        if capital <= 0:

            raise ValueError(
                "Recommendation contains invalid capital"
            )

        if confirmed_buys is None:

            confirmed_buys = deepcopy(
                recommendation.get(
                    "allocations",
                    [],
                )
            )

        if not isinstance(
            confirmed_buys,
            list,
        ):

            raise TypeError(
                "confirmed_buys must be a list"
            )

        # Initial capital first exists as portfolio cash.
        # Confirmed purchases then consume actual cash.
        state = self.state_service.create_state(

            portfolio=
                portfolio,

            cash_balance=
                capital,

        )

        state = (
            self.state_service
            .apply_confirmed_buys(

                state=
                    state,

                buys=
                    confirmed_buys,

                transaction_date=
                    transaction_date,

                source=
                    "INITIAL_DEPLOYMENT",

            )
        )

        save_result = None

        if save:

            save_result = (
                self.state_service
                .save_state(

                    state=
                        state,

                    path=
                        path,

                )
            )

        return {

            "status":
                "OK",

            "mode":
                "INITIAL_INVESTMENT_CONFIRMED",

            "confirmed":
                True,

            "state":
                state,

            "save_result":
                save_result,

        }

    # ======================================================
    # CORRECT CONFIRMED BUY
    #
    # CONTROLLED WRITE OPERATION
    #
    # Corrects one specific historical BUY execution and
    # persists the resulting authoritative portfolio state.
    #
    # This is an accounting correction only.
    # It is NOT a rebalance, SIP, BUY or SELL decision.
    # ======================================================

    def correct_confirmed_buy(
        self,
        transaction_index,
        quantity,
        price,
        correction_date=None,
        reason="DATA_ENTRY_CORRECTION",
        save=True,
        path=None,
    ):

        load_result = (
            self.state_service
            .load_state(
                path=
                    path
            )
        )

        if not isinstance(
            load_result,
            dict,
        ):

            raise ValueError(
                "Invalid portfolio state load result"
            )

        if load_result.get(
            "status"
        ) != "OK":

            raise ValueError(
                load_result.get(
                    "error",
                    "No active portfolio state found",
                )
            )

        state = load_result.get(
            "state"
        )

        if not isinstance(
            state,
            dict,
        ):

            raise ValueError(
                "No valid portfolio state found"
            )

        updated_state = (
            self.state_service
            .correct_confirmed_buy(

                state=
                    state,

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

            )
        )

        save_result = None

        if save:

            save_result = (
                self.state_service
                .save_state(

                    state=
                        updated_state,

                    path=
                        path,

                )
            )

        return {

            "status":
                "OK",

            "mode":
                "PURCHASE_ENTRY_CORRECTION",

            "corrected":
                True,

            "transaction_index":
                int(
                    transaction_index
                ),

            "state":
                updated_state,

            "save_result":
                save_result,

        }


    # ======================================================
    # PREPARE SMART SIP
    #
    # READ ONLY
    #
    # Existing cash balance is passed only as carry-forward
    # for recommendation calculation.
    # ======================================================

    def prepare_sip(
        self,
        state,
        sip_amount,
        price_map,
    ):

        if not isinstance(
            state,
            dict,
        ):

            raise TypeError(
                "state must be a dictionary"
            )

        sip_amount = self._safe_float(
            sip_amount,
            0.0,
        )

        if sip_amount <= 0:

            raise ValueError(
                "SIP amount must be greater than zero"
            )

        portfolio = deepcopy(
            state.get(
                "portfolio",
                []
            )
        )

        # Compatibility fallback:
        # portfolio state may preserve target rows through
        # positions rather than a top-level portfolio list.
        if not portfolio:

            positions = state.get(
                "positions",
                {},
            )

            if isinstance(
                positions,
                dict,
            ):

                portfolio = [

                    deepcopy(
                        position
                    )

                    for position
                    in positions.values()

                    if isinstance(
                        position,
                        dict,
                    )

                ]

        if not portfolio:

            raise ValueError(
                "Portfolio state contains no target portfolio"
            )

        holdings = (
            self.state_service
            .holdings_for_smart_sip(
                state
            )
        )

        carry_forward_cash = (
            self._safe_float(
                state.get(
                    "cash_balance",
                    0.0,
                ),
                0.0,
            )
        )

        sip_result = build_smart_sip(

            portfolio=
                portfolio,

            holdings=
                holdings,

            sip_amount=
                sip_amount,

            price_map=
                price_map,

            carry_forward_cash=
                carry_forward_cash,

            overshoot_tolerance_pct=
                self.overshoot_tolerance_pct,

        )

        self._require_ok(
            sip_result,
            "Smart SIP allocation",
        )

        return {

            "status":
                "OK",

            "mode":
                "SMART_SIP_RECOMMENDATION",

            "confirmed":
                False,

            "sip_amount":
                round(
                    sip_amount,
                    2,
                ),

            "carry_forward_cash":
                round(
                    carry_forward_cash,
                    2,
                ),

            "available_cash":
                sip_result.get(
                    "available_cash",
                    round(
                        sip_amount
                        + carry_forward_cash,
                        2,
                    ),
                ),

            "current_portfolio_value":
                sip_result.get(
                    "current_portfolio_value",
                    0.0,
                ),

            "sip_invested":
                sip_result.get(
                    "sip_invested",
                    0.0,
                ),

            "cash_remaining":
                sip_result.get(
                    "cash_remaining",
                    0.0,
                ),

            "allocations":
                deepcopy(
                    sip_result.get(
                        "allocations",
                        [],
                    )
                ),

            "smart_sip_result":
                sip_result,

        }

    # ======================================================
    # CONFIRM SMART SIP
    #
    # STATE CHANGING
    #
    # IMPORTANT:
    # Only NEW SIP cash is added.
    # Existing carry-forward cash is already in state.
    # ======================================================

    def confirm_sip(
        self,
        state,
        recommendation,
        confirmed_buys=None,
        transaction_date=None,
        snapshot_label=None,
        save=True,
        path=None,
    ):

        if not isinstance(
            state,
            dict,
        ):

            raise TypeError(
                "state must be a dictionary"
            )

        self._require_ok(
            recommendation,
            "Smart SIP recommendation",
        )

        if recommendation.get(
            "mode"
        ) != "SMART_SIP_RECOMMENDATION":

            raise ValueError(
                "Invalid Smart SIP recommendation"
            )

        sip_amount = self._safe_float(
            recommendation.get(
                "sip_amount",
                0.0,
            ),
            0.0,
        )

        if sip_amount <= 0:

            raise ValueError(
                "Recommendation contains invalid SIP amount"
            )

        if confirmed_buys is None:

            # --------------------------------------------------
            # SMART SIP EXECUTION CONTRACT
            #
            # Recommendation allocation rows may contain both:
            #
            # - existing/current portfolio quantity fields
            # - incremental "sip_quantity" recommended this month
            #
            # PortfolioStateService.apply_confirmed_buys() accepts
            # "quantity" as an execution quantity, so passing the
            # full recommendation rows directly could incorrectly
            # interpret an existing holding quantity as a new buy.
            #
            # Build a clean execution-only payload using ONLY the
            # incremental Smart SIP quantity.
            # --------------------------------------------------

            confirmed_buys = []

            for allocation in recommendation.get(
                "allocations",
                [],
            ):

                if not isinstance(
                    allocation,
                    dict,
                ):

                    continue

                sip_quantity = int(
                    self._safe_float(
                        allocation.get(
                            "sip_quantity",
                            0,
                        ),
                        0.0,
                    )
                )

                if sip_quantity <= 0:

                    continue

                confirmed_buys.append({

                    "symbol":
                        allocation.get(
                            "symbol"
                        ),

                    "quantity":
                        sip_quantity,

                    "price":
                        allocation.get(
                            "price",
                            0.0,
                        ),

                })

        if not isinstance(
            confirmed_buys,
            list,
        ):

            raise TypeError(
                "confirmed_buys must be a list"
            )

        updated = deepcopy(
            state
        )

        # Add NEW monthly contribution only.
        # Existing carry-forward cash already exists in state.
        updated = (
            self.state_service
            .add_cash(

                state=
                    updated,

                amount=
                    sip_amount,

                source=
                    "SIP",

                transaction_date=
                    transaction_date,

            )
        )

        updated = (
            self.state_service
            .apply_confirmed_buys(

                state=
                    updated,

                buys=
                    confirmed_buys,

                transaction_date=
                    transaction_date,

                source=
                    "SMART_SIP",

            )
        )

        snapshot = None

        if snapshot_label is not None:

            snapshot = (
                self.state_service
                .create_snapshot(

                    state=
                        updated,

                    label=
                        snapshot_label,

                )
            )

            # create_snapshot may either mutate/return state
            # or return a snapshot payload depending on the
            # state-service contract. Preserve only a returned
            # full state object.
            if (
                isinstance(
                    snapshot,
                    dict,
                )
                and "positions"
                in snapshot
                and "cash_balance"
                in snapshot
            ):

                updated = snapshot

        save_result = None

        if save:

            save_result = (
                self.state_service
                .save_state(

                    state=
                        updated,

                    path=
                        path,

                )
            )

        return {

            "status":
                "OK",

            "mode":
                "SMART_SIP_CONFIRMED",

            "confirmed":
                True,

            "state":
                updated,

            "save_result":
                save_result,

        }

    # ======================================================
    # REFRESH / MARK TO MARKET
    #
    # Does not create trades.
    # ======================================================

    def refresh_portfolio(
        self,
        state,
        price_map,
        snapshot_label=None,
        save=False,
        path=None,
    ):

        if not isinstance(
            state,
            dict,
        ):

            raise TypeError(
                "state must be a dictionary"
            )

        updated = (
            self.state_service
            .mark_to_market(

                state=
                    deepcopy(
                        state
                    ),

                price_map=
                    price_map,

            )
        )

        if snapshot_label is not None:

            snapshot_result = (
                self.state_service
                .create_snapshot(

                    state=
                        updated,

                    label=
                        snapshot_label,

                )
            )

            if (
                isinstance(
                    snapshot_result,
                    dict,
                )
                and "positions"
                in snapshot_result
                and "cash_balance"
                in snapshot_result
            ):

                updated = snapshot_result

        save_result = None

        if save:

            save_result = (
                self.state_service
                .save_state(

                    state=
                        updated,

                    path=
                        path,

                )
            )

        return {

            "status":
                "OK",

            "mode":
                "PORTFOLIO_REFRESH",

            "state":
                updated,

            "save_result":
                save_result,

        }

    # ======================================================
    # PORTFOLIO INTELLIGENCE ORCHESTRATION
    #
    # READ ONLY
    #
    # Synthesizes PortfolioAnalyticsService,
    # PortfolioHealthService, RecommendationEngine, and
    # DecisionEngine into a single intelligence output.
    # ======================================================

    def get_portfolio_intelligence(
        self,
        state,
        price_map=None,
    ):
        if not isinstance(
            state,
            dict,
        ):
            raise TypeError(
                "state must be a dictionary"
            )

        current_state = state

        if price_map is not None:
            refresh_result = (
                self.refresh_portfolio(
                    state=state,
                    price_map=price_map,
                    save=False,
                )
            )

            if (
                isinstance(
                    refresh_result,
                    dict,
                )
                and refresh_result.get("status") == "OK"
            ):
                current_state = refresh_result.get(
                    "state",
                    state,
                )

        holdings = []

        positions = current_state.get(
            "positions",
            {},
        )

        if (
            isinstance(
                positions,
                dict,
            )
            and positions
        ):
            for symbol, pos in positions.items():
                if not isinstance(
                    pos,
                    dict,
                ):
                    continue

                norm_symbol = (
                    self.state_service._normalize_symbol(
                        pos.get(
                            "symbol",
                            symbol,
                        )
                    )
                )

                weight = pos.get("actual_weight")

                if weight is None:
                    weight = pos.get(
                        "target_weight",
                        pos.get(
                            "weight",
                            0.0,
                        ),
                    )

                weight = self._safe_float(
                    weight,
                    0.0,
                )

                if norm_symbol:
                    holdings.append(
                        PortfolioHolding(
                            symbol=norm_symbol,
                            weight=weight,
                        )
                    )

        elif (
            isinstance(
                current_state.get("portfolio"),
                list,
            )
            and current_state.get("portfolio")
        ):
            for item in current_state.get("portfolio", []):
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                norm_symbol = (
                    self.state_service._normalize_symbol(
                        item.get("symbol")
                    )
                )

                weight = self._safe_float(
                    item.get(
                        "target_weight",
                        item.get(
                            "weight",
                            0.0,
                        ),
                    ),
                    0.0,
                )

                if norm_symbol:
                    holdings.append(
                        PortfolioHolding(
                            symbol=norm_symbol,
                            weight=weight,
                        )
                    )

        analytics = (
            self.analytics_service.analyze(
                holdings
            )
        )

        health = (
            self.health_service.evaluate(
                analytics
            )
        )

        recommendations = (
            self.recommendation_engine.generate(
                analytics,
                health,
            )
        )

        decisions = (
            self.decision_engine.generate(
                recommendations
            )
        )

        return {
            "status":
                "OK",

            "mode":
                "PORTFOLIO_INTELLIGENCE",

            "state":
                deepcopy(
                    current_state
                ),

            "analytics":
                analytics,

            "health":
                health,

            "recommendations":
                recommendations,

            "decisions":
                decisions,
        }

    # ======================================================
    # PERSISTENCE CONVENIENCE
    # ======================================================

    def load_state(
        self,
        path=None,
    ):

        return (
            self.state_service
            .load_state(
                path=path
            )
        )

    def save_state(
        self,
        state,
        path=None,
    ):

        return (
            self.state_service
            .save_state(
                state=state,
                path=path,
            )
        )


def create_portfolio_orchestrator(
    max_stock_weight=10.0,
    sector_soft_limit=25.0,
    overshoot_tolerance_pct=0.75,
):

    return PortfolioOrchestrationService(

        max_stock_weight=
            max_stock_weight,

        sector_soft_limit=
            sector_soft_limit,

        overshoot_tolerance_pct=
            overshoot_tolerance_pct,

    )
