from dataclasses import dataclass
import math


@dataclass
class PortfolioHolding:
    symbol: str
    weight: float


@dataclass
class PortfolioAnalytics:
    holding_count: int
    total_weight: float

    equal_weight: float
    average_weight: float

    largest_weight: float
    smallest_weight: float
    weight_range: float

    concentration_score: float
    diversification_score: float

    overweight_positions: int
    underweight_positions: int

    hhi: float
    effective_holdings: float

    top3_weight: float
    top5_weight: float

    concentration_risk: str
    diversification_grade: str

    warnings: list[str]


class PortfolioAnalyticsService:
    """
    Portfolio Analytics Engine

    Analyses the completed portfolio and returns useful portfolio statistics.

    This service does NOT modify the portfolio.
    """

    def analyze(
        self,
        holdings: list[PortfolioHolding],
    ) -> PortfolioAnalytics:

        warnings: list[str] = []

        if not holdings:
            return PortfolioAnalytics(
                holding_count=0,
                total_weight=0.0,
                equal_weight=0.0,
                average_weight=0.0,
                largest_weight=0.0,
                smallest_weight=0.0,
                weight_range=0.0,
                concentration_score=0.0,
                diversification_score=0.0,
                overweight_positions=0,
                underweight_positions=0,
                hhi=0.0,
                effective_holdings=0.0,
                top3_weight=0.0,
                top5_weight=0.0,
                concentration_risk="N/A",
                diversification_grade="N/A",
                warnings=["Portfolio is empty."],
            )

        weights = [holding.weight for holding in holdings]

        holding_count = len(weights)
        total_weight = sum(weights)

        equal_weight = 100.0 / holding_count
        average_weight = total_weight / holding_count

        largest_weight = max(weights)
        smallest_weight = min(weights)

        weight_range = largest_weight - smallest_weight

        concentration_score = largest_weight
        diversification_score = 100.0 - concentration_score

        overweight_positions = sum(
            1 for weight in weights
            if weight > equal_weight
        )

        underweight_positions = sum(
            1 for weight in weights
            if weight < equal_weight
        )

        sorted_weights = sorted(
            weights,
            reverse=True,
        )

        top3_weight = sum(sorted_weights[:3])
        top5_weight = sum(sorted_weights[:5])

        hhi = sum(
            (weight / 100.0) ** 2
            for weight in weights
        )

        effective_holdings = (
            1.0 / hhi
            if hhi > 0
            else 0.0
        )

        if hhi < 0.12:
            concentration_risk = "Low"
            diversification_grade = "A"
        elif hhi < 0.18:
            concentration_risk = "Moderate"
            diversification_grade = "B"
        elif hhi < 0.25:
            concentration_risk = "High"
            diversification_grade = "C"
        else:
            concentration_risk = "Very High"
            diversification_grade = "D"

        if abs(total_weight - 100.0) > 0.01:
            warnings.append(
                f"Portfolio weights total {total_weight:.2f}% instead of 100%."
            )

        return PortfolioAnalytics(
            holding_count=holding_count,
            total_weight=total_weight,
            equal_weight=equal_weight,
            average_weight=average_weight,
            largest_weight=largest_weight,
            smallest_weight=smallest_weight,
            weight_range=weight_range,
            concentration_score=concentration_score,
            diversification_score=diversification_score,
            overweight_positions=overweight_positions,
            underweight_positions=underweight_positions,
            hhi=hhi,
            effective_holdings=effective_holdings,
            top3_weight=top3_weight,
            top5_weight=top5_weight,
            concentration_risk=concentration_risk,
            diversification_grade=diversification_grade,
            warnings=warnings,
        )