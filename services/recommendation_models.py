from dataclasses import dataclass, field


@dataclass
class Recommendation:

    category: str
    priority: str

    action: str

    confidence: int

    target: str

    title: str

    reasons: list[str] = field(default_factory=list)

    suggested_action: str = ""

    # Computed by RecommendationScoringService
    score: int = 0


@dataclass
class RecommendationReport:

    portfolio_recommendations: list[Recommendation] = field(
        default_factory=list
    )

    holding_recommendations: list[Recommendation] = field(
        default_factory=list
    )

    risk_recommendations: list[Recommendation] = field(
        default_factory=list
    )

    cash_recommendations: list[Recommendation] = field(
        default_factory=list
    )

    monitoring_recommendations: list[Recommendation] = field(
        default_factory=list
    )

    @property
    def all_recommendations(self) -> list[Recommendation]:

        recommendations = []

        recommendations.extend(
            self.portfolio_recommendations
        )

        recommendations.extend(
            self.holding_recommendations
        )

        recommendations.extend(
            self.risk_recommendations
        )

        recommendations.extend(
            self.cash_recommendations
        )

        recommendations.extend(
            self.monitoring_recommendations
        )

        return recommendations