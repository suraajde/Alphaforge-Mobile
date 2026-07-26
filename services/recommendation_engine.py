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