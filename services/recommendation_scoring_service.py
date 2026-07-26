from services.recommendation_models import (
    Recommendation,
    RecommendationReport,
)

from services.recommendation_constants import (
    RecommendationPriority,
)


class RecommendationScoringService:
    """
    Calculates recommendation scores and
    sorts recommendations by importance.
    """

    PRIORITY_WEIGHTS = {
        RecommendationPriority.CRITICAL: 40,
        RecommendationPriority.HIGH: 30,
        RecommendationPriority.MEDIUM: 20,
        RecommendationPriority.LOW: 10,
    }

    def score_report(
        self,
        report: RecommendationReport,
    ) -> RecommendationReport:

        for recommendation in report.all_recommendations:

            recommendation.score = self._calculate_score(
                recommendation
            )

        report.portfolio_recommendations.sort(
            key=lambda r: r.score,
            reverse=True,
        )

        report.holding_recommendations.sort(
            key=lambda r: r.score,
            reverse=True,
        )

        report.risk_recommendations.sort(
            key=lambda r: r.score,
            reverse=True,
        )

        report.cash_recommendations.sort(
            key=lambda r: r.score,
            reverse=True,
        )

        report.monitoring_recommendations.sort(
            key=lambda r: r.score,
            reverse=True,
        )

        return report

    def _calculate_score(
        self,
        recommendation: Recommendation,
    ) -> int:

        priority_weight = self.PRIORITY_WEIGHTS.get(
            recommendation.priority,
            0,
        )

        score = priority_weight + recommendation.confidence

        return min(score, 100)