from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)

from services.portfolio_health_service import (
    PortfolioHealth,
)

from services.recommendation_models import (
    RecommendationReport,
)

from services.recommendation_scoring_service import (
    RecommendationScoringService,
)

from services.rules.portfolio_health_rule import (
    PortfolioHealthRule,
)

from services.rules.concentration_rule import (
    ConcentrationRule,
)

from services.rules.diversification_rule import (
    DiversificationRule,
)

from services.rules.position_sizing_rule import (
    PositionSizingRule,
)

from services.rules.portfolio_structure_rule import (
    PortfolioStructureRule,
)


class RecommendationEngine:
    """
    AlphaForge Recommendation Engine.

    Orchestrates independent recommendation rules,
    then prioritises recommendations using the
    Recommendation Scoring Service.
    """

    def __init__(self):

        self._rules = [
            PortfolioHealthRule(),
            ConcentrationRule(),
            DiversificationRule(),
            PositionSizingRule(),
            PortfolioStructureRule(),
        ]

        self._scoring_service = (
            RecommendationScoringService()
        )

    def generate(
        self,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> RecommendationReport:

        report = RecommendationReport()

        pos_count = getattr(analytics, "position_count", getattr(analytics, "holding_count", 0))
        if pos_count == 0:
            from services.recommendation_models import Recommendation
            empty_rec = Recommendation(
                category="PORTFOLIO",
                priority="N/A",
                action="NONE",
                confidence=0,
                target="N/A",
                title="No active portfolio to evaluate",
                reasons=["No active portfolio positions are available for analysis."],
                suggested_action="Create or import a portfolio.",
                score=0,
            )
            report.portfolio_recommendations.append(empty_rec)
            return report

        for rule in self._rules:

            rule.apply(
                report,
                analytics,
                health,
            )

        self._scoring_service.score_report(
            report
        )

        return report