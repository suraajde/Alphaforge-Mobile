from services.stock_service import (
    get_stock_data,
)

from services.fundamental_service import (
    get_fundamental_metrics,
)

from services.sector_classifier_service import (
    classify_sector,
)

from services.sector_fundamental_score_service import (
    calculate_sector_aware_fundamental_score,
)

from services.data_quality_service import (
    calculate_data_quality,
)

from services.data_completeness_service import (
    analyze_data_completeness,
)

from services.data_caution_service import (
    evaluate_data_caution,
)

from services.scan_cache_service import (
    load_cached_analysis,
    save_cached_analysis,
)

from services.technical_service import (
    get_technical_metrics,
)

from services.technical_score_service import (
    calculate_technical_score,
)

from services.alpha_composite_service import (
    calculate_alpha_composite,
)


class ResearchRadarService:

    # ==================================================
    # ANALYZE ONE STOCK
    # ==================================================

    def analyze_stock(
        self,
        symbol,
    ):

        symbol = str(
            symbol
        ).strip().upper()

        result = {
            "symbol": symbol,
        }

        try:

            # --------------------------------------------------
            # COMPANY METADATA
            # --------------------------------------------------

            stock_data = get_stock_data(
                symbol
            )

            if (
                not stock_data
                or "error" in stock_data
            ):

                result.update({
                    "status":
                        "ERROR",

                    "error":
                        "Company data unavailable",
                })

                return result

            company_name = (
                stock_data.get(
                    "name"
                )
            )

            sector = (
                stock_data.get(
                    "sector"
                )
            )

            industry = (
                stock_data.get(
                    "industry"
                )
            )

            # --------------------------------------------------
            # SECTOR CLASSIFICATION
            # --------------------------------------------------

            classification = (
                classify_sector(

                    sector=sector,

                    industry=industry,

                    company_name=company_name,
                )
            )

            scoring_profile = (
                classification.get(
                    "profile",
                    "GENERAL",
                )
            )

            # --------------------------------------------------
            # FUNDAMENTAL DATA
            # --------------------------------------------------

            fundamental_data = (
                get_fundamental_metrics(
                    symbol
                )
            )

            if (
                not fundamental_data
                or "error" in fundamental_data
            ):

                result.update({
                    "status":
                        "ERROR",

                    "error":
                        "Fundamental data unavailable",
                })

                return result

            # --------------------------------------------------
            # RAW DATA QUALITY
            # --------------------------------------------------

            data_quality = (
                calculate_data_quality(
                    fundamental_data
                )
            )

            # --------------------------------------------------
            # DATA COMPLETENESS
            # --------------------------------------------------

            completeness = (
                analyze_data_completeness(
                    fundamental_data,
                    scoring_profile,
                )
            )

            # --------------------------------------------------
            # DATA CAUTION STATUS
            #
            # CLEAN
            # CAUTION
            # INSUFFICIENT
            #
            # Transparency layer only.
            # Does not alter investment scores.
            # --------------------------------------------------

            data_caution = (
                evaluate_data_caution(

                    data_quality=
                        data_quality,

                    completeness=
                        completeness,
                )
            )

            # --------------------------------------------------
            # SECTOR-AWARE FUNDAMENTAL SCORE
            # --------------------------------------------------

            fundamental_scores = (
                calculate_sector_aware_fundamental_score(

                    fundamental_data,

                    scoring_profile,
                )
            )

            profile_maturity = (
                fundamental_scores.get(
                    "profile_maturity",
                    "BASELINE",
                )
            )

            # --------------------------------------------------
            # TECHNICAL DATA
            # --------------------------------------------------

            technical_data = (
                get_technical_metrics(
                    symbol
                )
            )

            if (
                not technical_data
                or "error" in technical_data
            ):

                result.update({
                    "status":
                        "ERROR",

                    "error":
                        "Technical data unavailable",
                })

                return result

            technical_scores = (
                calculate_technical_score(
                    technical_data
                )
            )

            # --------------------------------------------------
            # ALPHA COMPOSITE
            # --------------------------------------------------

            alpha = (
                calculate_alpha_composite(

                    fundamental_scores,

                    technical_scores,

                    data_quality,
                )
            )

            # --------------------------------------------------
            # ORIGINAL GATE REASONS
            # --------------------------------------------------

            original_gate_reasons = list(
                alpha.get(
                    "gate_reasons",
                    [],
                )
            )

            # --------------------------------------------------
            # DATA-ONLY GATE REASONS
            #
            # These may be overridden by the newer
            # completeness resolver when sufficient
            # independent evidence exists.
            # --------------------------------------------------

            data_gate_reasons = {

                "Insufficient data quality",

                "Low data confidence",
            }

            non_data_gate_reasons = [

                reason

                for reason
                in original_gate_reasons

                if reason
                not in data_gate_reasons
            ]

            # --------------------------------------------------
            # COMPLETENESS READINESS
            # --------------------------------------------------

            completeness_ready = bool(
                completeness.get(
                    "ranking_data_ready",
                    False,
                )
            )

            # --------------------------------------------------
            # EFFECTIVE HARD GATE
            # --------------------------------------------------

            effective_hard_gate_pass = (

                completeness_ready

                and len(
                    non_data_gate_reasons
                ) == 0
            )

            effective_gate_reasons = list(
                non_data_gate_reasons
            )

            if not completeness_ready:

                effective_gate_reasons.extend(

                    completeness.get(
                        "blocking_reasons",
                        [],
                    )
                )

            # --------------------------------------------------
            # DATA WARNINGS
            # --------------------------------------------------

            data_warnings = list(
                completeness.get(
                    "warnings",
                    [],
                )
            )

            raw_confidence = (
                data_quality.get(
                    "confidence_score"
                )
            )

            if (
                raw_confidence is not None

                and raw_confidence < 75

                and completeness_ready
            ):

                data_warnings.append(
                    "Raw source data confidence is reduced"
                )

            # Remove duplicates.

            data_warnings = list(
                dict.fromkeys(
                    data_warnings
                )
            )

            # --------------------------------------------------
            # PRODUCTION ELIGIBILITY
            #
            # Provisional sector models remain outside
            # production ranking.
            # --------------------------------------------------

            production_eligible = (

                effective_hard_gate_pass

                and profile_maturity
                != "PROVISIONAL"
            )

            # --------------------------------------------------
            # RANKING NOTES
            # --------------------------------------------------

            ranking_notes = []

            ranking_notes.extend(
                effective_gate_reasons
            )

            if (
                profile_maturity
                == "PROVISIONAL"
            ):

                ranking_notes.append(
                    "Sector scoring profile is provisional"
                )

            ranking_notes.extend(
                data_warnings
            )

            ranking_notes = list(
                dict.fromkeys(
                    ranking_notes
                )
            )

            # --------------------------------------------------
            # EFFECTIVE CLASSIFICATION
            # --------------------------------------------------

            effective_classification = (
                alpha.get(
                    "classification"
                )
            )

            composite_score = (
                alpha.get(
                    "base_composite"
                )
            )

            # --------------------------------------------------
            # RECLASSIFY ONLY WHEN OLD DATA-QUALITY GATE
            # WAS THE REASON FOR REJECTION
            # --------------------------------------------------

            if (
                effective_hard_gate_pass

                and effective_classification
                == "REJECT / REVIEW"

                and composite_score is not None
            ):

                if composite_score >= 80:

                    effective_classification = (
                        "HIGH CONVICTION CANDIDATE"
                    )

                elif composite_score >= 70:

                    effective_classification = (
                        "STRONG RADAR CANDIDATE"
                    )

                elif composite_score >= 60:

                    effective_classification = (
                        "RADAR CANDIDATE"
                    )

                elif composite_score >= 50:

                    effective_classification = (
                        "MONITOR"
                    )

                else:

                    effective_classification = (
                        "REJECT / REVIEW"
                    )

            # --------------------------------------------------
            # FINAL STOCK ANALYSIS
            # --------------------------------------------------

            result.update({

                "status":
                    "OK",

                "company_name":
                    company_name,

                "sector":
                    sector,

                "industry":
                    industry,

                "scoring_profile":
                    scoring_profile,

                "profile_maturity":
                    profile_maturity,

                # ----------------------------------------------
                # SCORES
                # ----------------------------------------------

                "fundamental_score":
                    alpha.get(
                        "fundamental_score"
                    ),

                "profitability_score":
                    fundamental_scores.get(
                        "profitability_score"
                    ),

                "growth_score":
                    fundamental_scores.get(
                        "growth_score"
                    ),

                "financial_strength_score":
                    fundamental_scores.get(
                        "financial_strength_score"
                    ),

                "valuation_score":
                    fundamental_scores.get(
                        "valuation_score"
                    ),

                "technical_score":
                    alpha.get(
                        "technical_score"
                    ),

                "risk_score":
                    technical_scores.get(
                        "risk_score"
                    ),

                "composite_score":
                    composite_score,

                "readiness_score":
                    alpha.get(
                        "readiness_score"
                    ),

                # ----------------------------------------------
                # RAW DATA QUALITY
                # ----------------------------------------------

                "data_confidence":
                    alpha.get(
                        "data_confidence"
                    ),

                # ----------------------------------------------
                # DATA COMPLETENESS
                # ----------------------------------------------

                "coverage_score":
                    completeness.get(
                        "coverage_score"
                    ),

                "coverage_level":
                    completeness.get(
                        "coverage_level"
                    ),

                "ranking_data_ready":
                    completeness_ready,

                # ----------------------------------------------
                # DATA CAUTION
                # ----------------------------------------------

                "data_status":
                    data_caution.get(
                        "data_status"
                    ),

                "data_caution":
                    data_caution.get(
                        "data_caution"
                    ),

                "data_caution_reasons":
                    data_caution.get(
                        "reasons",
                        [],
                    ),

                "data_warnings":
                    data_warnings,

                # ----------------------------------------------
                # ORIGINAL ALPHA GATE
                # ----------------------------------------------

                "original_hard_gate_pass":
                    alpha.get(
                        "hard_gate_pass"
                    ),

                "original_gate_reasons":
                    original_gate_reasons,

                # ----------------------------------------------
                # EFFECTIVE PRODUCTION GATE
                # ----------------------------------------------

                "hard_gate_pass":
                    effective_hard_gate_pass,

                "gate_reasons":
                    effective_gate_reasons,

                "production_eligible":
                    production_eligible,

                # ----------------------------------------------
                # CLASSIFICATION
                # ----------------------------------------------

                "classification":
                    effective_classification,

                "technical_warnings":
                    alpha.get(
                        "technical_warnings",
                        [],
                    ),

                "ranking_notes":
                    ranking_notes,
            })

            return result

        except Exception as error:

            result.update({

                "status":
                    "ERROR",

                "error":
                    str(
                        error
                    ),
            })

            return result

    # ==================================================
    # RANK SYMBOLS
    #
    # Sprint 10.2:
    # Scan Cache Integration
    # ==================================================

    def rank_symbols(
        self,
        symbols,
        limit=30,
        force_refresh=False,
    ):

        results = []

        seen = set()

        # --------------------------------------------------
        # CACHE STATISTICS
        # --------------------------------------------------

        cache_hits = 0

        live_analyses = 0

        cache_saves = 0

        cache_save_failures = 0

        # --------------------------------------------------
        # PROCESS SYMBOLS
        # --------------------------------------------------

        for symbol in symbols:

            clean_symbol = str(
                symbol
            ).strip().upper()

            if not clean_symbol:

                continue

            if clean_symbol in seen:

                continue

            seen.add(
                clean_symbol
            )

            # --------------------------------------------------
            # CHECK CACHE
            # --------------------------------------------------

            cached = (
                load_cached_analysis(

                    clean_symbol,

                    force_refresh=
                        force_refresh,
                )
            )

            # --------------------------------------------------
            # CACHE HIT
            # --------------------------------------------------

            if cached.get(
                "cache_hit"
            ):

                print(
                    f"Loading {clean_symbol} "
                    f"from cache..."
                )

                analysis = (
                    cached.get(
                        "analysis"
                    )
                )

                # Defensive copy so current ranking
                # modifications do not affect the
                # in-memory cached dictionary.

                if isinstance(
                    analysis,
                    dict,
                ):

                    analysis = dict(
                        analysis
                    )

                cache_hits += 1

            # --------------------------------------------------
            # CACHE MISS / EXPIRED / FORCE REFRESH
            # --------------------------------------------------

            else:

                cache_status = (
                    cached.get(
                        "cache_status",
                        "MISS",
                    )
                )

                if (
                    cache_status
                    == "FORCE_REFRESH"
                ):

                    print(
                        f"Refreshing "
                        f"{clean_symbol}..."
                    )

                elif (
                    cache_status
                    == "EXPIRED"
                ):

                    print(
                        f"Cache expired for "
                        f"{clean_symbol}. "
                        f"Analyzing..."
                    )

                else:

                    print(
                        f"Analyzing "
                        f"{clean_symbol}..."
                    )

                # ----------------------------------------------
                # LIVE ANALYSIS
                # ----------------------------------------------

                analysis = (
                    self.analyze_stock(
                        clean_symbol
                    )
                )

                live_analyses += 1

                # ----------------------------------------------
                # SAVE ONLY SUCCESSFUL ANALYSIS
                # ----------------------------------------------

                if (
                    isinstance(
                        analysis,
                        dict,
                    )

                    and analysis.get(
                        "status"
                    ) == "OK"
                ):

                    save_result = (
                        save_cached_analysis(

                            clean_symbol,

                            analysis,
                        )
                    )

                    if save_result.get(
                        "saved"
                    ):

                        cache_saves += 1

                    else:

                        cache_save_failures += 1

            # --------------------------------------------------
            # STORE RESULT
            # --------------------------------------------------

            if analysis is None:

                analysis = {

                    "status":
                        "ERROR",

                    "symbol":
                        clean_symbol,

                    "error":
                        "No analysis result returned",
                }

            results.append(
                analysis
            )

        # --------------------------------------------------
        # SUCCESSFUL ANALYSES
        # --------------------------------------------------

        successful = [

            item

            for item in results

            if item.get(
                "status"
            ) == "OK"
        ]

        # --------------------------------------------------
        # PRODUCTION-ELIGIBLE POOL
        # --------------------------------------------------

        eligible = [

            item

            for item in successful

            if item.get(
                "production_eligible"
            )
        ]

        # --------------------------------------------------
        # REVIEW POOL
        # --------------------------------------------------

        review = [

            item

            for item in successful

            if not item.get(
                "production_eligible"
            )
        ]

        # --------------------------------------------------
        # RANKING KEY
        # --------------------------------------------------

        def ranking_key(
            item,
        ):

            return (

                item.get(
                    "composite_score"
                )

                if item.get(
                    "composite_score"
                ) is not None

                else -1,

                item.get(
                    "readiness_score"
                )

                if item.get(
                    "readiness_score"
                ) is not None

                else -1,

                item.get(
                    "fundamental_score"
                )

                if item.get(
                    "fundamental_score"
                ) is not None

                else -1,
            )

        # --------------------------------------------------
        # SORT POOLS
        # --------------------------------------------------

        eligible.sort(
            key=ranking_key,
            reverse=True,
        )

        review.sort(
            key=ranking_key,
            reverse=True,
        )

        # --------------------------------------------------
        # APPLY TOP-N LIMIT
        # --------------------------------------------------

        ranked = eligible[
            :limit
        ]

        # --------------------------------------------------
        # ASSIGN CURRENT-SCAN RANK
        #
        # Rank is assigned AFTER cache retrieval.
        # Rank is not used as cached source data.
        # --------------------------------------------------

        for index, item in enumerate(
            ranked,
            start=1,
        ):

            item[
                "rank"
            ] = index

        # --------------------------------------------------
        # ERRORS
        # --------------------------------------------------

        errors = [

            item

            for item in results

            if item.get(
                "status"
            ) != "OK"
        ]

        # --------------------------------------------------
        # FINAL RADAR RESULT
        # --------------------------------------------------

        return {

            "ranked":
                ranked,

            "review":
                review,

            "errors":
                errors,

            "analyzed_count":
                len(
                    results
                ),

            "successful_count":
                len(
                    successful
                ),

            "eligible_count":
                len(
                    eligible
                ),

            "review_count":
                len(
                    review
                ),

            # ----------------------------------------------
            # CACHE STATISTICS
            # ----------------------------------------------

            "cache_hits":
                cache_hits,

            "live_analyses":
                live_analyses,

            "cache_saves":
                cache_saves,

            "cache_save_failures":
                cache_save_failures,

            "force_refresh":
                force_refresh,
        }


# ==================================================
# PUBLIC RESEARCH RADAR FUNCTION
# ==================================================

def build_research_radar(
    symbols,
    limit=30,
    force_refresh=False,
):

    service = (
        ResearchRadarService()
    )

    return service.rank_symbols(

        symbols,

        limit=limit,

        force_refresh=
            force_refresh,
    )