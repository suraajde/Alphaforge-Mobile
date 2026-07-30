"""Portfolio Action Service

Transforms a RecommendationReport into UI-friendly action buckets.

Read-only service: does not analyze or modify recommendations.
"""
from __future__ import annotations

from typing import Dict, List

from services.recommendation_models import (
    Recommendation,
    RecommendationReport,
)


class PortfolioActionService:
    """Service that converts RecommendationReport into action buckets for the UI.

    The service exposes a single public method `build_actions` and a small
    internal helper `_convert_recommendation`.
    """

    def build_actions(self, report: RecommendationReport) -> Dict[str, List[Dict]]:
        """Build action buckets from a RecommendationReport.

        Args:
            report: RecommendationReport - the source recommendations.

        Returns:
            A dictionary with keys: status, buy, reduce, hold, watch.

        Raises:
            TypeError: if report is not a RecommendationReport instance.
        """
        if not isinstance(report, RecommendationReport):
            raise TypeError("report must be a RecommendationReport")

        buckets: Dict[str, List[Dict]] = {
            "status": "OK",
            "buy": [],
            "reduce": [],
            "hold": [],
            "watch": [],
        }

        # Map action values (case-insensitive) to bucket names
        mapping = {
            "BUY": "buy",
            "INCREASE": "buy",
            "REDUCE": "reduce",
            "SELL": "reduce",
            "HOLD": "hold",
            "WATCH": "watch",
            "MONITOR": "watch",
        }

        for rec in report.all_recommendations:
            bucket_name = mapping.get((rec.action or "").upper(), "watch")
            item = self._convert_recommendation(rec)
            buckets[bucket_name].append(item)

        # Sort each bucket by score desc, then confidence desc
        for key in ("buy", "reduce", "hold", "watch"):
            buckets[key].sort(key=lambda r: (-int(r.get("score", 0)), -int(r.get("confidence", 0))))

        return buckets

    def _convert_recommendation(self, recommendation: Recommendation) -> Dict:
        """Convert a Recommendation into the UI action item dict.

        The conversion is intentionally light-weight and does not perform any
        domain analysis.
        """
        return {
            "target": recommendation.target,
            "title": recommendation.title,
            "priority": recommendation.priority,
            "confidence": recommendation.confidence,
            "score": recommendation.score,
            "reasons": list(recommendation.reasons or []),
            "suggested_action": recommendation.suggested_action,
        }
