from dataclasses import dataclass

from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)


@dataclass
class PortfolioHealth:

    overall_score: int
    overall_grade: str

    diversification_score: int
    concentration_score: int
    position_sizing_score: int
    weight_balance_score: int
    portfolio_structure_score: int

    recommendation: str


class PortfolioHealthService:
    """
    Converts PortfolioAnalytics into
    a portfolio health assessment.

    This service never changes the portfolio.
    It only evaluates its quality.
    """

    def evaluate(
        self,
        analytics: PortfolioAnalytics,
    ) -> PortfolioHealth:

        diversification_score = 20
        concentration_score = 20
        position_sizing_score = 20
        weight_balance_score = 20
        portfolio_structure_score = 20

        # Diversification
        if analytics.diversification_grade == "B":
            diversification_score = 18
        elif analytics.diversification_grade == "C":
            diversification_score = 15
        elif analytics.diversification_grade == "D":
            diversification_score = 10

        # Concentration
        if analytics.concentration_risk == "Moderate":
            concentration_score = 18
        elif analytics.concentration_risk == "High":
            concentration_score = 15
        elif analytics.concentration_risk == "Very High":
            concentration_score = 10

        # Position sizing
        if analytics.largest_weight > 20:
            position_sizing_score -= 2

        if analytics.largest_weight > 25:
            position_sizing_score -= 3

        if analytics.largest_weight > 30:
            position_sizing_score -= 5

        # Weight balance
        if analytics.weight_range > 15:
            weight_balance_score -= 2

        if analytics.weight_range > 20:
            weight_balance_score -= 3

        if analytics.weight_range > 30:
            weight_balance_score -= 5

        # Portfolio structure
        if analytics.holding_count < 10:
            portfolio_structure_score = 17

        if analytics.holding_count < 8:
            portfolio_structure_score = 15

        if analytics.holding_count < 6:
            portfolio_structure_score = 12

        overall_score = (
            diversification_score
            + concentration_score
            + position_sizing_score
            + weight_balance_score
            + portfolio_structure_score
        )

        if overall_score >= 90:
            overall_grade = "A"
            recommendation = (
                "Healthy portfolio. "
                "No immediate rebalance required."
            )
        elif overall_score >= 80:
            overall_grade = "B"
            recommendation = (
                "Good portfolio. "
                "Minor optimisation recommended."
            )
        elif overall_score >= 70:
            overall_grade = "C"
            recommendation = (
                "Portfolio should be reviewed."
            )
        else:
            overall_grade = "D"
            recommendation = (
                "Portfolio requires rebalancing."
            )

        return PortfolioHealth(
            overall_score=overall_score,
            overall_grade=overall_grade,
            diversification_score=diversification_score,
            concentration_score=concentration_score,
            position_sizing_score=position_sizing_score,
            weight_balance_score=weight_balance_score,
            portfolio_structure_score=portfolio_structure_score,
            recommendation=recommendation,
        )