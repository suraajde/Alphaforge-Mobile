from abc import ABC
from abc import abstractmethod

from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)

from services.portfolio_health_service import (
    PortfolioHealth,
)

from services.recommendation_models import (
    RecommendationReport,
)


class RecommendationRule(ABC):
    """
    Base class for all recommendation rules.
    """

    @abstractmethod
    def apply(
        self,
        report: RecommendationReport,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> None:
        """
        Add recommendations to the report.
        """
        raise NotImplementedError