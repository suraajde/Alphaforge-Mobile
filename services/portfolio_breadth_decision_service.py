from dataclasses import dataclass


@dataclass
class PortfolioBreadthInput:
    candidate_count: int
    minimum_portfolio_size: int = 8
    maximum_portfolio_size: int = 20
    target_portfolio_size: int | None = None
    average_composite_score: float = 0.0


@dataclass
class PortfolioBreadthDecision:
    recommended_size: int
    confidence: float
    reason: str


class PortfolioBreadthDecisionService:
    """
    Determines the recommended portfolio size.

    This service decides HOW MANY stocks should be included.
    It does NOT decide WHICH stocks to select.
    """

    def recommend(
        self,
        request: PortfolioBreadthInput,
    ) -> PortfolioBreadthDecision:

        # User explicitly selected a target size
        if request.target_portfolio_size is not None:
            size = max(
                request.minimum_portfolio_size,
                min(request.target_portfolio_size, request.maximum_portfolio_size),
            )

            return PortfolioBreadthDecision(
                recommended_size=size,
                confidence=1.0,
                reason="User configured portfolio size.",
            )

        # Automatic recommendation
        recommended = min(
            max(request.candidate_count, request.minimum_portfolio_size),
            request.maximum_portfolio_size,
        )

        return PortfolioBreadthDecision(
            recommended_size=recommended,
            confidence=0.80,
            reason="Automatically determined from available qualified candidates.",
        )