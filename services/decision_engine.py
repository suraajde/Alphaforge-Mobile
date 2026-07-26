from services.decision_models import (
    Decision,
    DecisionReport,
    DecisionType,
)

from services.recommendation_models import (
    RecommendationReport,
)

from services.recommendation_constants import (
    RecommendationAction,
)


class DecisionEngine:
    """
    Converts recommendations into
    actionable portfolio decisions.
    """

    ACTION_MAPPING = {
        RecommendationAction.MONITOR:
            DecisionType.MONITOR,

        RecommendationAction.REBALANCE:
            DecisionType.REBALANCE,

        RecommendationAction.REVIEW_STRUCTURE:
            DecisionType.REVIEW_STRUCTURE,

        RecommendationAction.REVIEW_POSITION_SIZES:
            DecisionType.REVIEW_POSITION_SIZES,

        RecommendationAction.REDUCE_CONCENTRATION:
            DecisionType.REDUCE_CONCENTRATION,
    }

    def generate(
        self,
        recommendations: RecommendationReport,
    ) -> DecisionReport:

        report = DecisionReport()

        for recommendation in recommendations.all_recommendations:

            decision_type = self.ACTION_MAPPING.get(
                recommendation.action,
                DecisionType.MONITOR,
            )

            report.decisions.append(
                Decision(
                    decision_type=decision_type,
                    priority=recommendation.priority,
                    score=recommendation.score,
                    title=recommendation.title,
                    description=recommendation.suggested_action,
                    source_recommendation=recommendation.category,
                )
            )

        report.decisions.sort(
            key=lambda decision: decision.score,
            reverse=True,
        )

        return report