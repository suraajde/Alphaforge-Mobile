from dataclasses import dataclass
from typing import Dict, List, Optional

from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)
from services.portfolio_health_service import (
    PortfolioHealth,
)


@dataclass
class PortfolioIntelligenceScore:
    overall_score: float
    component_scores: Dict[str, float]
    investment_grade: str
    strengths: List[str]
    weaknesses: List[str]
    warnings: List[str]
    summary: str


class PortfolioIntelligenceScoreService:
    """
    Computes a human-friendly, extensible Portfolio Intelligence Score.

    Design goals:
    - Extensible component-based scoring (component_scores dict).
    - Uses only PortfolioAnalytics and PortfolioHealth today.
    - Public API is score(analytics, health, recommendations=None, decisions=None)
      so RecommendationEngine / DecisionEngine may be passed later without
      changing the interface.
    - Returns PortfolioIntelligenceScore (0..100) with grade, strengths,
      weaknesses, warnings and a short summary.
    """

    # Component weighting (sums to 1.0)
    COMPONENT_WEIGHTS = {
        "health_overall": 0.50,
        "diversification": 0.15,
        "concentration": 0.10,
        "position_sizing": 0.08,
        "weight_balance": 0.07,
        "structure": 0.10,
    }

    def score(
        self,
        analytics: Optional[PortfolioAnalytics],
        health: Optional[PortfolioHealth],
        recommendations: Optional[object] = None,
        decisions: Optional[object] = None,
    ) -> PortfolioIntelligenceScore:

        warnings: List[str] = []
        strengths: List[str] = []
        weaknesses: List[str] = []

        # Validate inputs
        if analytics is None:
            warnings.append("Missing portfolio analytics.")
        if health is None:
            warnings.append("Missing portfolio health evaluation.")

        if analytics is None or health is None:
            # Return safe default
            component_scores = {k: 0.0 for k in self.COMPONENT_WEIGHTS.keys()}
            overall = 0.0
            grade = "N/A"
            summary = (
                "Portfolio Intelligence: N/A. Insufficient data to score portfolio."
            )
            return PortfolioIntelligenceScore(
                overall_score=overall,
                component_scores=component_scores,
                investment_grade=grade,
                strengths=strengths,
                weaknesses=weaknesses,
                warnings=warnings,
                summary=summary,
            )

        if getattr(health, "overall_grade", "") == "N/A" or getattr(health, "overall_score", 0) == 0:
            component_scores = {k: 0.0 for k in self.COMPONENT_WEIGHTS.keys()}
            overall = 0.0
            grade = "N/A"
            summary = "No active portfolio positions found. Create or import a portfolio."
            weaknesses.append("No active portfolio positions found. Create or import a portfolio.")
            return PortfolioIntelligenceScore(
                overall_score=overall,
                component_scores=component_scores,
                investment_grade=grade,
                strengths=strengths,
                weaknesses=weaknesses,
                warnings=warnings,
                summary=summary,
            )


        # Build component scores scaled to 0-100
        # health.overall_score is already 0-100
        health_overall = float(max(0.0, min(100.0, health.overall_score)))

        # The health service also exposes 5 component scores (0-20). Scale each by 5.
        diversification = float(max(0.0, min(20.0, health.diversification_score))) * 5.0
        concentration = float(max(0.0, min(20.0, health.concentration_score))) * 5.0
        position_sizing = float(max(0.0, min(20.0, health.position_sizing_score))) * 5.0
        weight_balance = float(max(0.0, min(20.0, health.weight_balance_score))) * 5.0
        structure = float(max(0.0, min(20.0, health.portfolio_structure_score))) * 5.0

        component_scores = {
            "health_overall": round(health_overall, 2),
            "diversification": round(diversification, 2),
            "concentration": round(concentration, 2),
            "position_sizing": round(position_sizing, 2),
            "weight_balance": round(weight_balance, 2),
            "structure": round(structure, 2),
        }

        # Weighted aggregation
        overall = 0.0
        for key, weight in self.COMPONENT_WEIGHTS.items():
            score_value = component_scores.get(key, 0.0)
            overall += score_value * weight

        overall = float(max(0.0, min(100.0, overall)))

        # Investment grade
        grade = self._grade_from_score(overall)

        # Strengths / Weaknesses heuristics (simple, clear rules)
        # Strengths (positive signals)
        if diversification >= 75:
            strengths.append("Well diversified")
        if concentration <= 25:
            strengths.append("Low concentration risk")
        if position_sizing >= 70:
            strengths.append("Healthy position sizing")
        if weight_balance >= 65:
            strengths.append("Balanced weights across holdings")
        if structure >= 65:
            strengths.append("Reasonable portfolio structure and count")
        if health_overall >= 85:
            strengths.append("Strong overall health")

        # Weaknesses (negative signals)
        # Use analytics details for further signals
        try:
            largest = getattr(analytics, "largest_weight", None)
            top3 = getattr(analytics, "top3_weight", None)
            holding_count = getattr(analytics, "holding_count", None)
        except Exception:
            largest = None
            top3 = None
            holding_count = None

        if largest is not None and largest >= 25:
            weaknesses.append("Large single holding — possible concentration")
        if top3 is not None and top3 >= 60:
            weaknesses.append("Top 3 holdings dominate portfolio")
        if holding_count is not None and holding_count < 6:
            weaknesses.append("Too few holdings for long-term diversification")

        # If no strengths identified, add neutral note
        if not strengths:
            strengths.append("No clear strengths identified — review metrics")

        # If no weaknesses, add neutral note
        if not weaknesses:
            weaknesses.append("No immediate structural weaknesses detected")

        # Merge warnings from analytics if available
        try:
            analytics_warnings = getattr(analytics, "warnings", []) or []
            if analytics_warnings:
                warnings.extend(analytics_warnings)
        except Exception:
            pass

        # Build human readable summary
        summary_parts = [
            f"Overall score {overall:.1f}/100 ({grade})",
        ]

        if strengths:
            summary_parts.append(f"Strengths: {', '.join(strengths[:3])}")
        if weaknesses:
            summary_parts.append(f"Weaknesses: {', '.join(weaknesses[:3])}")

        summary = ". ".join(summary_parts) + "."

        return PortfolioIntelligenceScore(
            overall_score=round(overall, 2),
            component_scores=component_scores,
            investment_grade=grade,
            strengths=strengths,
            weaknesses=weaknesses,
            warnings=warnings,
            summary=summary,
        )

    def _grade_from_score(self, score: float) -> str:
        # A+ (>=97), A (>=90), B+ (>=80), B (>=70), C (>=60), D (<60)
        if score >= 97.0:
            return "A+"
        if score >= 90.0:
            return "A"
        if score >= 80.0:
            return "B+"
        if score >= 70.0:
            return "B"
        if score >= 60.0:
            return "C"
        return "D"
