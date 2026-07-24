from __future__ import annotations

from services.universe_service import UniverseService
from services.production_screen_service import ProductionScreenService
from services.production_scan_orchestrator import ProductionScanOrchestrator
from services.alpha12_selection_service import Alpha12SelectionService


class ProductionRadarPipeline:
    """
    AlphaForge End-to-End Production Research Radar Pipeline.

    Production pipeline:

        400-stock Production Universe
            ->
        Lightweight Market Pre-Screen
            ->
        Candidate Pool
            ->
        Resumable / Cache-Aware Deep Analysis
            ->
        Global Top-N Research Radar

    Responsibilities:
    - Load the official production universe.
    - Run the lightweight market pre-screen.
    - Preserve universe metadata such as MIDCAP / SMALLCAP.
    - Send only shortlisted candidates to deep analysis.
    - Reuse the resumable ProductionScanOrchestrator.
    - Enrich final Radar results with universe metadata.

    Testing:
    - stocks_override can supply a controlled stock list.
    - Normal production behavior is unchanged when
      stocks_override is None.

    This service does NOT duplicate:
    - fundamental analysis
    - technical analysis
    - composite scoring
    - eligibility rules
    - cache logic
    """

    def __init__(
        self,
        candidate_limit=120,
        radar_limit=30,
        screen_batch_size=100,
        deep_batch_size=10,
        alpha_target_count=12,
        alpha_reserve_count=8,
    ):

        self.candidate_limit = max(
            1,
            int(candidate_limit),
        )

        self.radar_limit = max(
            1,
            int(radar_limit),
        )

        self.alpha_target_count = max(
            1,
            int(alpha_target_count),
        )

        self.alpha_reserve_count = max(
            0,
            int(alpha_reserve_count),
        )

        self.universe_service = (
            UniverseService()
        )

        self.screen_service = (
            ProductionScreenService(
                batch_size=screen_batch_size,
                target_pool=self.candidate_limit,
            )
        )

        self.scan_orchestrator = (
            ProductionScanOrchestrator(
                batch_size=deep_batch_size,
            )
        )

    # ======================================================
    # LOAD PRODUCTION UNIVERSE
    # ======================================================

    def load_universe(
        self,
    ):

        result = (
            self.universe_service
            .get_enabled_stocks()
        )

        stocks = result.get(
            "stocks",
            [],
        )

        return {

            "stocks":
                stocks,

            "count":
                len(stocks),

            "errors":
                result.get(
                    "errors",
                    [],
                ),

            "invalid_rows":
                result.get(
                    "invalid_rows",
                    [],
                ),

        }

    # ======================================================
    # BUILD UNIVERSE METADATA MAP
    # ======================================================

    @staticmethod
    def _build_metadata_map(
        stocks,
    ):

        metadata = {}

        for stock in stocks:

            if not isinstance(
                stock,
                dict,
            ):

                continue

            symbol = str(
                stock.get(
                    "symbol",
                    "",
                )
            ).strip().upper()

            if not symbol:

                continue

            metadata[
                symbol
            ] = {

                "company":
                    stock.get(
                        "company",
                        "",
                    ),

                "category":
                    stock.get(
                        "category",
                        "",
                    ),

                "exchange":
                    stock.get(
                        "exchange",
                        "",
                    ),

                "source":
                    stock.get(
                        "source",
                        "",
                    ),

                "as_of_date":
                    stock.get(
                        "as_of_date",
                        "",
                    ),

            }

        return metadata

    # ======================================================
    # ENRICH ANALYSIS RESULT
    # ======================================================

    @staticmethod
    def _enrich_item(
        item,
        metadata_map,
        screen_map,
    ):

        if not isinstance(
            item,
            dict,
        ):

            return item

        symbol = str(
            item.get(
                "symbol",
                "",
            )
        ).strip().upper()

        metadata = (
            metadata_map.get(
                symbol,
                {},
            )
        )

        screen_data = (
            screen_map.get(
                symbol,
                {},
            )
        )

        enriched = dict(
            item
        )

        # --------------------------------------------------
        # UNIVERSE METADATA
        #
        # UniverseService is authoritative for market-cap
        # category membership.
        # --------------------------------------------------

        enriched[
            "universe_company"
        ] = metadata.get(
            "company",
            "",
        )

        enriched[
            "category"
        ] = metadata.get(
            "category",
            "",
        )

        enriched[
            "universe_exchange"
        ] = metadata.get(
            "exchange",
            "",
        )

        enriched[
            "universe_source"
        ] = metadata.get(
            "source",
            "",
        )

        enriched[
            "universe_as_of_date"
        ] = metadata.get(
            "as_of_date",
            "",
        )

        # --------------------------------------------------
        # LIGHTWEIGHT PRE-SCREEN DIAGNOSTICS
        # --------------------------------------------------

        enriched[
            "market_health_score"
        ] = screen_data.get(
            "market_health_score"
        )

        enriched[
            "screen_return_3m"
        ] = screen_data.get(
            "return_3m"
        )

        enriched[
            "screen_return_6m"
        ] = screen_data.get(
            "return_6m"
        )

        enriched[
            "screen_return_1y"
        ] = screen_data.get(
            "return_1y"
        )

        enriched[
            "screen_max_drawdown"
        ] = screen_data.get(
            "max_drawdown"
        )

        enriched[
            "screen_volatility"
        ] = screen_data.get(
            "volatility"
        )

        enriched[
            "screen_avg_volume_20d"
        ] = screen_data.get(
            "avg_volume_20d"
        )

        return enriched

    # ======================================================
    # RUN END-TO-END PIPELINE
    # ======================================================

    def run(
        self,
        force_refresh=False,
        resume=True,
        progress_callback=None,
        stocks_override=None,
    ):

        # --------------------------------------------------
        # STAGE 1
        # LOAD PRODUCTION UNIVERSE
        #
        # stocks_override exists only so controlled tests
        # can run through the exact production pipeline
        # without launching the full 400-stock universe.
        # --------------------------------------------------

        if progress_callback:

            progress_callback({

                "stage":
                    "UNIVERSE",

                "message":
                    "Loading production universe...",

            })

        if stocks_override is not None:

            stocks = list(
                stocks_override
            )

            universe = {

                "stocks":
                    stocks,

                "count":
                    len(stocks),

                "errors":
                    [],

                "invalid_rows":
                    [],

            }

        else:

            universe = (
                self.load_universe()
            )

            stocks = universe[
                "stocks"
            ]

        # --------------------------------------------------
        # EMPTY UNIVERSE PROTECTION
        # --------------------------------------------------

        if not stocks:

            return {

                "status":
                    "ERROR",

                "error":
                    "Production universe is empty.",

                "universe_count":
                    0,

                "candidate_count":
                    0,

                "processed_count":
                    0,

                "successful_count":
                    0,

                "eligible_count":
                    0,

                "review_count":
                    0,

                "error_count":
                    0,

                "ranked":
                    [],

                "review":
                    [],

                "errors":
                    [],

                "completed":
                    False,

            }

        metadata_map = (
            self._build_metadata_map(
                stocks
            )
        )

        # --------------------------------------------------
        # STAGE 2
        # MARKET PRE-SCREEN
        # --------------------------------------------------

        if progress_callback:

            progress_callback({

                "stage":
                    "PRE_SCREEN",

                "message":
                    (
                        "Running production "
                        "market pre-screen..."
                    ),

                "universe_count":
                    len(stocks),

            })

        screen_result = (
            self.screen_service.screen(

                stocks,

                target_pool=
                    min(
                        self.candidate_limit,
                        len(stocks),
                    ),

            )
        )

        selected = (
            screen_result.get(
                "selected",
                [],
            )
        )

        selected_symbols = (
            screen_result.get(
                "selected_symbols",
                [],
            )
        )

        screen_map = {

            str(
                item.get(
                    "symbol",
                    "",
                )
            ).strip().upper():
                item

            for item in selected

            if isinstance(
                item,
                dict,
            )
            and item.get(
                "symbol"
            )

        }

        # --------------------------------------------------
        # NO PRE-SCREEN CANDIDATES
        # --------------------------------------------------

        if not selected_symbols:

            return {

                "status":
                    "ERROR",

                "error":
                    (
                        "Production pre-screen "
                        "returned no candidates."
                    ),

                "universe_count":
                    len(stocks),

                "market_data_valid_count":
                    screen_result.get(
                        "market_data_valid_count",
                        0,
                    ),

                "candidate_count":
                    0,

                "candidate_midcap_count":
                    0,

                "candidate_smallcap_count":
                    0,

                "processed_count":
                    0,

                "successful_count":
                    0,

                "eligible_count":
                    0,

                "review_count":
                    0,

                "error_count":
                    0,

                "ranked":
                    [],

                "review":
                    [],

                "errors":
                    [],

                "screen_result":
                    screen_result,

                "completed":
                    False,

            }

        # --------------------------------------------------
        # STAGE 3
        # INSPECT EXISTING DEEP-SCAN CACHE
        # --------------------------------------------------

        cache_summary = (
            self.scan_orchestrator
            .inspect_cache(
                selected_symbols
            )
        )

        if progress_callback:

            progress_callback({

                "stage":
                    "DEEP_SCAN_START",

                "message":
                    (
                        "Starting deep Research "
                        "Radar analysis..."
                    ),

                "candidate_count":
                    len(
                        selected_symbols
                    ),

                "cache_fresh":
                    cache_summary.get(
                        "fresh_count",
                        0,
                    ),

                "cache_expired":
                    cache_summary.get(
                        "expired_count",
                        0,
                    ),

                "cache_missing":
                    cache_summary.get(
                        "missing_count",
                        0,
                    ),

            })

        # --------------------------------------------------
        # DEEP-SCAN PROGRESS ADAPTER
        # --------------------------------------------------

        def deep_progress(
            state,
        ):

            if not progress_callback:

                return

            payload = dict(
                state
            )

            payload[
                "stage"
            ] = "DEEP_SCAN"

            payload[
                "message"
            ] = (

                "Deep analysis: "
                f"{state.get('processed_count', 0)}"
                "/"
                f"{state.get('total_count', 0)}"

            )

            progress_callback(
                payload
            )

        # --------------------------------------------------
        # STAGE 4
        # RESUMABLE / CACHE-AWARE DEEP ANALYSIS
        # --------------------------------------------------

        deep_result = (
            self.scan_orchestrator.run(

                selected_symbols,

                limit=
                    min(
                        self.radar_limit,
                        len(
                            selected_symbols
                        ),
                    ),

                force_refresh=
                    force_refresh,

                resume=
                    resume,

                progress_callback=
                    deep_progress,

            )
        )

        # --------------------------------------------------
        # STAGE 5
        # ENRICH FINAL RESULTS
        # --------------------------------------------------

        ranked = [

            self._enrich_item(

                item,

                metadata_map,

                screen_map,

            )

            for item in deep_result.get(
                "ranked",
                [],
            )

        ]

        review = [

            self._enrich_item(

                item,

                metadata_map,

                screen_map,

            )

            for item in deep_result.get(
                "review",
                [],
            )

        ]

        errors = [

            self._enrich_item(

                item,

                metadata_map,

                screen_map,

            )

            for item in deep_result.get(
                "errors",
                [],
            )

        ]

        # --------------------------------------------------
        # STAGE 6
        # ALPHA 12 PORTFOLIO SELECTION
        #
        # IMPORTANT:
        # - Research Radar Top 30 remains unchanged.
        # - Alpha 12 is a downstream selection layer.
        # - Only enriched production-ranked candidates are
        #   supplied to the Alpha 12 engine.
        # - No upstream score or Radar rank is modified.
        # --------------------------------------------------

        alpha12_result = (
            Alpha12SelectionService(
                target_count=
                    self.alpha_target_count,
                reserve_count=
                    self.alpha_reserve_count,
            )
            .select(
                ranked
            )
        )

        alpha12 = alpha12_result.get(
            "selected",
            [],
        )

        alpha12_reserves = alpha12_result.get(
            "reserves",
            [],
        )

        # --------------------------------------------------
        # FINAL RESULT
        # --------------------------------------------------

        result = {

            "status":
                "OK",

            # ----------------------------------------------
            # UNIVERSE
            # ----------------------------------------------

            "universe_count":
                len(stocks),

            "universe_errors":
                universe.get(
                    "errors",
                    [],
                ),

            "universe_invalid_rows":
                universe.get(
                    "invalid_rows",
                    [],
                ),

            # ----------------------------------------------
            # PRE-SCREEN
            # ----------------------------------------------

            "market_data_valid_count":
                screen_result.get(
                    "market_data_valid_count",
                    0,
                ),

            "candidate_count":
                len(
                    selected_symbols
                ),

            "candidate_midcap_count":
                screen_result.get(
                    "selected_midcap_count",
                    0,
                ),

            "candidate_smallcap_count":
                screen_result.get(
                    "selected_smallcap_count",
                    0,
                ),

            # ----------------------------------------------
            # CACHE
            # ----------------------------------------------

            "cache_summary":
                cache_summary,

            # ----------------------------------------------
            # DEEP ANALYSIS
            # ----------------------------------------------

            "processed_count":
                deep_result.get(
                    "processed_count",
                    0,
                ),

            "successful_count":
                deep_result.get(
                    "successful_count",
                    0,
                ),

            "eligible_count":
                deep_result.get(
                    "eligible_count",
                    0,
                ),

            "review_count":
                deep_result.get(
                    "review_count",
                    0,
                ),

            "error_count":
                deep_result.get(
                    "error_count",
                    0,
                ),

            # ----------------------------------------------
            # FINAL RADAR POOLS
            # ----------------------------------------------

            "ranked":
                ranked,

            # ----------------------------------------------
            # ALPHA 12 PORTFOLIO SELECTION
            # ----------------------------------------------

            "alpha12":
                alpha12,

            "alpha12_reserves":
                alpha12_reserves,

            "alpha12_count":
                alpha12_result.get(
                    "selected_count",
                    0,
                ),

            "alpha12_reserve_count":
                alpha12_result.get(
                    "reserve_count",
                    0,
                ),

            "alpha12_midcap_count":
                alpha12_result.get(
                    "selected_midcap_count",
                    0,
                ),

            "alpha12_smallcap_count":
                alpha12_result.get(
                    "selected_smallcap_count",
                    0,
                ),

            "alpha12_sector_counts":
                alpha12_result.get(
                    "sector_counts",
                    {},
                ),

            "alpha12_selection_result":
                alpha12_result,

            "review":
                review,

            "errors":
                errors,

            # ----------------------------------------------
            # DIAGNOSTICS
            # ----------------------------------------------

            "screen_result":
                screen_result,

            "completed":
                deep_result.get(
                    "completed",
                    False,
                ),

        }

        # --------------------------------------------------
        # COMPLETE CALLBACK
        # --------------------------------------------------

        if progress_callback:

            progress_callback({

                "stage":
                    "COMPLETE",

                "message":
                    (
                        "Production Research "
                        "Radar complete."
                    ),

                "universe_count":
                    result[
                        "universe_count"
                    ],

                "candidate_count":
                    result[
                        "candidate_count"
                    ],

                "processed_count":
                    result[
                        "processed_count"
                    ],

                "ranked_count":
                    len(
                        ranked
                    ),

                "error_count":
                    result[
                        "error_count"
                    ],

            })

        return result


# ==========================================================
# PUBLIC PRODUCTION FUNCTION
# ==========================================================

def run_production_radar(
    candidate_limit=120,
    radar_limit=30,
    force_refresh=False,
    resume=True,
    progress_callback=None,
    stocks_override=None,
):

    pipeline = (
        ProductionRadarPipeline(

            candidate_limit=
                candidate_limit,

            radar_limit=
                radar_limit,

        )
    )

    return pipeline.run(

        force_refresh=
            force_refresh,

        resume=
            resume,

        progress_callback=
            progress_callback,

        stocks_override=
            stocks_override,

    )