from dataclasses import dataclass
from enum import Enum


class WeightStrategy(str, Enum):
    EQUAL = "equal"
    LINEAR = "linear"
    TIERED = "tiered"


@dataclass
class ConvictionInput:
    score: float


class ConvictionWeightEngine:
    """
    Converts conviction scores into weighting factors.

    This engine returns relative weight multipliers.
    PortfolioConstructionService remains responsible
    for final normalization to 100%.
    """

    def weight(
        self,
        request: ConvictionInput,
        strategy: WeightStrategy = WeightStrategy.LINEAR,
    ) -> float:

        score = max(0.0, min(100.0, float(request.score)))

        if strategy == WeightStrategy.EQUAL:
            return 1.0

        if strategy == WeightStrategy.LINEAR:
            return score

        if strategy == WeightStrategy.TIERED:

            if score >= 90:
                return 1.40

            if score >= 80:
                return 1.25

            if score >= 70:
                return 1.10

            return 1.00

        return score