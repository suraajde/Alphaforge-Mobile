"""Portfolio Health Service Foundation (Sprint 13.3.0B.1)

Provides a single source of truth service layer for calculating basic Portfolio Health metrics

and returning a PortfolioHealthSnapshot.

"""

from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Optional

from services.decision_classification_service import DecisionClassificationResult

from services.decision_prioritization_service import DecisionPrioritizationResult

from services.decision_engine_service import DecisionEngineResult

from services.decision_audit_service import DecisionAuditTrail

from services.decision_audit_analytics_service import DecisionAuditAnalytics

from services.decision_audit_trend_service import DecisionAuditTrend

from services.rebalancing_service import RebalancingState

from services.allocation_analysis_service import AllocationAnalysisResult

from services.drift_detection_service import DriftDetectionResult

from services.rebalancing_candidate_service import RebalancingCandidateResult

from services.rebalancing_recommendation_service import RebalancingRecommendationResult
from services.portfolio_intelligence_service import PortfolioIntelligenceResult
from services.holding_quality_service import HoldingQualityResult
from services.sip_optimization_service import SIPOptimizationResult
from services.portfolio_opportunity_service import PortfolioOpportunityResult
from services.portfolio_risk_intelligence_service import PortfolioRiskResult
from services.alpha12_mapping_service import Alpha12MappingResult
from services.alpha12_replacement_governance_service import ReplacementGovernanceResult
from services.alpha12_stability_service import Alpha12StabilityResult

from services.decision_dashboard_service import DecisionDashboardResult

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

@dataclass

class PortfolioHealthSnapshot:

    position_count: int

    portfolio_value: float

    invested_value: float

    cash_allocation_pct: float

    largest_position: str

    largest_position_weight_pct: float

@dataclass

class PortfolioHealthAnalytics:

    diversification_score: int

    concentration_score: int

    cash_score: int

    strengths: list[str]

    weaknesses: list[str]

@dataclass

class PortfolioHealthTrend:

    current_score: int

    previous_score: int

    score_change: int

    current_grade: str

    previous_grade: str

    trend_direction: str

@dataclass

class PortfolioHealthResult:

    score: int

    grade: str

    diversification_rating: str

    concentration_rating: str

    position_count: int

    largest_position_weight_pct: float

    cash_allocation_pct: float

    analytics: Optional[PortfolioHealthAnalytics] = None

    trend: Optional[PortfolioHealthTrend] = None

    historical_analytics: Optional[Any] = None

    dashboard_summary: Optional[Any] = None

    historical_metrics: Optional[Any] = None

    historical_insights: Optional[Any] = None

    monitoring_state: Optional[Any] = None

    change_report: Optional[Any] = None

    timeline: Optional[Any] = None

    monitoring_dashboard: Optional[Any] = None

    alert_center: Optional[Any] = None

    generated_alerts: Optional[Any] = None

    alert_rules: Optional[Any] = None

    alert_dashboard: Optional[Any] = None

    alert_history: Optional[Any] = None

    alert_management: Optional[Any] = None

    decision_engine: Optional[DecisionEngineResult] = None

    decision_classification: Optional[DecisionClassificationResult] = None

    decision_prioritization: Optional[DecisionPrioritizationResult] = None

    decision_dashboard: Optional[DecisionDashboardResult] = None

    decision_audit: Optional[DecisionAuditTrail] = None

    decision_audit_analytics: Optional[DecisionAuditAnalytics] = None

    decision_audit_trend: Optional[DecisionAuditTrend] = None

    rebalancing: Optional[RebalancingState] = None

    allocation_analysis: Optional[AllocationAnalysisResult] = None

    drift_detection: Optional[DriftDetectionResult] = None

    rebalancing_candidates: Optional[RebalancingCandidateResult] = None

    rebalancing_recommendations: Optional[RebalancingRecommendationResult] = None
    portfolio_intelligence: Optional[PortfolioIntelligenceResult] = None
    holding_quality: Optional[HoldingQualityResult] = None
    sip_optimization: Optional[SIPOptimizationResult] = None
    portfolio_opportunities: Optional[PortfolioOpportunityResult] = None
    portfolio_risk_intelligence: Optional[PortfolioRiskResult] = None
    alpha12_mapping: Optional[Alpha12MappingResult] = None
    alpha12_challenger_evaluation: Optional[Any] = None
    alpha12_replacement_governance: Optional[ReplacementGovernanceResult] = None
    alpha12_stability: Optional[Alpha12StabilityResult] = None

class PortfolioHealthService:

    """Service layer for computing portfolio health metrics and snapshots safely."""

    def __init__(

        self,

        portfolio_app_service: Optional[Any] = None,

        history_service: Optional[Any] = None,

        monitor_service: Optional[Any] = None,

        change_detection_service: Optional[Any] = None,

        timeline_service: Optional[Any] = None,

        monitoring_dashboard_service: Optional[Any] = None,

        alert_center_service: Optional[Any] = None,

        alert_generation_service: Optional[Any] = None,

        alert_rules_service: Optional[Any] = None,

        alert_dashboard_service: Optional[Any] = None,

        alert_history_service: Optional[Any] = None,

        alert_management_service: Optional[Any] = None,

        decision_engine_service: Optional[Any] = None,

        decision_classification_service: Optional[Any] = None,

        decision_prioritization_service: Optional[Any] = None,

        decision_dashboard_service: Optional[Any] = None,

        decision_audit_service: Optional[Any] = None,

        decision_audit_analytics_service: Optional[Any] = None,

        decision_audit_trend_service: Optional[Any] = None,

        rebalancing_service: Optional[Any] = None,

        allocation_analysis_service: Optional[Any] = None,

        drift_detection_service: Optional[Any] = None,

        rebalancing_candidate_service: Optional[Any] = None,

        rebalancing_recommendation_service: Optional[Any] = None,
        portfolio_intelligence_service: Optional[Any] = None,
        holding_quality_service: Optional[Any] = None,
        sip_optimization_service: Optional[Any] = None,
        portfolio_opportunity_service: Optional[Any] = None,
        portfolio_risk_intelligence_service: Optional[Any] = None,
        alpha12_mapping_service: Optional[Any] = None,
        alpha12_health_integration_service: Optional[Any] = None,
        alpha12_challenger_service: Optional[Any] = None,
        alpha12_replacement_governance_service: Optional[Any] = None,
        alpha12_stability_service: Optional[Any] = None,
        time_provider: Optional[Any] = None,
    ) -> None:

        """Initialize PortfolioHealthService."""

        self._portfolio_app_service = portfolio_app_service

        self._history_service = history_service

        self._monitor_service = monitor_service

        self._change_detection_service = change_detection_service

        self._timeline_service = timeline_service

        self._monitoring_dashboard_service = monitoring_dashboard_service

        self._alert_center_service = alert_center_service

        self._alert_generation_service = alert_generation_service

        self._alert_rules_service = alert_rules_service

        self._alert_dashboard_service = alert_dashboard_service

        self._alert_history_service = alert_history_service

        self._alert_management_service = alert_management_service

        self._decision_engine_service = decision_engine_service

        self._decision_classification_service = decision_classification_service

        self._decision_prioritization_service = decision_prioritization_service

        self._decision_dashboard_service = decision_dashboard_service

        self._decision_audit_service = decision_audit_service

        self._decision_audit_analytics_service = decision_audit_analytics_service

        self._decision_audit_trend_service = decision_audit_trend_service

        self._rebalancing_service = rebalancing_service

        self._allocation_analysis_service = allocation_analysis_service

        self._drift_detection_service = drift_detection_service

        self._rebalancing_candidate_service = rebalancing_candidate_service

        self._rebalancing_recommendation_service = rebalancing_recommendation_service
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._holding_quality_service = holding_quality_service
        self._sip_optimization_service = sip_optimization_service
        self._portfolio_opportunity_service = portfolio_opportunity_service
        self._portfolio_risk_intelligence_service = portfolio_risk_intelligence_service
        self._alpha12_mapping_service = alpha12_mapping_service
        self._alpha12_health_integration_service = alpha12_health_integration_service
        self._alpha12_challenger_service = alpha12_challenger_service
        self._alpha12_replacement_governance_service = alpha12_replacement_governance_service
        self._alpha12_stability_service = alpha12_stability_service

        import time
        self._time_provider = time_provider if time_provider is not None else time.monotonic
        self._evaluation_cache: Optional[PortfolioHealthResult] = None
        self._evaluation_cache_key: Optional[str] = None
        self._evaluation_cache_time: float = 0.0
        self._evaluation_cache_ttl: float = 5.0

    def invalidate_evaluation_cache(self) -> None:
        """Explicitly invalidate the portfolio health evaluation cache."""
        self._evaluation_cache = None
        self._evaluation_cache_key = None
        self._evaluation_cache_time = 0.0

    def build_snapshot(self) -> PortfolioHealthSnapshot:

        """Build and return a portfolio health snapshot safely without exceptions.

        Returns:

            PortfolioHealthSnapshot containing calculated portfolio metrics.

        """

        try:

            return self._calculate_snapshot()

        except Exception:

            # Defensive fallback ensuring no uncaught exceptions

            return PortfolioHealthSnapshot(

                position_count=0,

                portfolio_value=0.0,

                invested_value=0.0,

                cash_allocation_pct=0.0,

                largest_position="N/A",

                largest_position_weight_pct=0.0,

            )

    def _calculate_snapshot(self) -> PortfolioHealthSnapshot:

        app_service = self._get_app_service()

        if app_service is None:

            return PortfolioHealthSnapshot(

                position_count=0,

                portfolio_value=0.0,

                invested_value=0.0,

                cash_allocation_pct=0.0,

                largest_position="N/A",

                largest_position_weight_pct=0.0,

            )

        status_res = getattr(app_service, "get_status", lambda: {})()

        if not isinstance(status_res, dict) or status_res.get("status") != "OK":

            return PortfolioHealthSnapshot(

                position_count=0,

                portfolio_value=0.0,

                invested_value=0.0,

                cash_allocation_pct=0.0,

                largest_position="N/A",

                largest_position_weight_pct=0.0,

            )

        state = status_res.get("state")

        if not isinstance(state, dict):

            pos_count = self._safe_int(status_res.get("position_count"), 0)

            port_val = self._safe_float(status_res.get("portfolio_value"), 0.0)

            inv_val = self._safe_float(status_res.get("invested_market_value"), 0.0)

            cash_bal = self._safe_float(status_res.get("cash_balance"), 0.0)

            cash_pct = (cash_bal / port_val * 100.0) if port_val > 0 else 0.0

            return PortfolioHealthSnapshot(

                position_count=pos_count,

                portfolio_value=round(port_val, 2),

                invested_value=round(inv_val, 2),

                cash_allocation_pct=round(cash_pct, 2),

                largest_position="N/A",

                largest_position_weight_pct=0.0,

            )

        positions = state.get("positions", {})

        if not isinstance(positions, dict):

            positions = {}

        cash_balance = self._safe_float(state.get("cash_balance"), 0.0)

        active_positions = []

        total_invested_value = 0.0

        total_current_market_value = 0.0

        for symbol_key, pos_data in positions.items():

            if not isinstance(pos_data, dict):

                continue

            symbol = str(pos_data.get("symbol", symbol_key)).strip().upper()

            if not symbol:

                continue

            qty = self._safe_float(pos_data.get("quantity"), 0.0)

            price = self._safe_float(pos_data.get("current_price"), 0.0)

            invested_cost = self._safe_float(pos_data.get("invested_cost"), 0.0)

            current_val = self._safe_float(pos_data.get("current_value"), 0.0)

            if current_val <= 0 and price > 0 and qty > 0:

                current_val = qty * price

            val = current_val if current_val > 0 else invested_cost

            total_invested_value += invested_cost

            total_current_market_value += current_val

            if qty > 0 or val > 0:

                active_positions.append({

                    "symbol": symbol,

                    "quantity": qty,

                    "value": val,

                    "actual_weight": self._safe_float(pos_data.get("actual_weight"), 0.0),

                })

        total_portfolio_value = self._safe_float(

            state.get("total_portfolio_value", state.get("portfolio_value")),

            total_current_market_value + cash_balance,

        )

        if total_portfolio_value <= 0:

            total_portfolio_value = total_invested_value + cash_balance

        position_count = len(active_positions)

        if total_portfolio_value > 0:

            cash_pct = (cash_balance / total_portfolio_value) * 100.0

        else:

            cash_pct = 0.0

        largest_position = "N/A"

        largest_weight_pct = 0.0

        if active_positions:

            active_positions.sort(key=lambda p: p["value"], reverse=True)

            top = active_positions[0]

            largest_position = top["symbol"]

            if total_portfolio_value > 0:

                largest_weight_pct = (top["value"] / total_portfolio_value) * 100.0

            elif top["actual_weight"] > 0:

                largest_weight_pct = top["actual_weight"]

        return PortfolioHealthSnapshot(

            position_count=position_count,

            portfolio_value=round(total_portfolio_value, 2),

            invested_value=round(total_invested_value, 2),

            cash_allocation_pct=round(cash_pct, 2),

            largest_position=largest_position,

            largest_position_weight_pct=round(largest_weight_pct, 2),

        )

    def evaluate_trend(

        self,

        current: PortfolioHealthResult,

        previous: Optional[PortfolioHealthResult] = None,

    ) -> PortfolioHealthTrend:

        """Evaluates trend by comparing current PortfolioHealthResult vs previous result."""

        current_score = getattr(current, "score", 0) if current else 0

        current_grade = getattr(current, "grade", "D") if current else "D"

        if previous is None:

            previous_score = current_score

            previous_grade = current_grade

            score_change = 0

            trend_direction = "STABLE"

        else:

            previous_score = getattr(previous, "score", current_score)

            previous_grade = getattr(previous, "grade", current_grade)

            score_change = current_score - previous_score

            if score_change >= 3:

                trend_direction = "IMPROVING"

            elif score_change <= -3:

                trend_direction = "DETERIORATING"

            else:

                trend_direction = "STABLE"

        return PortfolioHealthTrend(

            current_score=current_score,

            previous_score=previous_score,

            score_change=score_change,

            current_grade=current_grade,

            previous_grade=previous_grade,

            trend_direction=trend_direction,

        )

    def evaluate(

        self,

        snapshot: Optional[PortfolioHealthSnapshot] = None,

        previous: Optional[PortfolioHealthResult] = None,

    ) -> PortfolioHealthResult:

        """Calculates portfolio health score framework and returns PortfolioHealthResult.

        Scoring Factors (Max = 100):

        - Position Count (40 pts)

        - Concentration (40 pts)

        - Cash Allocation (20 pts)

        """

        try:

            if snapshot is None or not isinstance(snapshot, PortfolioHealthSnapshot):

                snapshot = self.build_snapshot()

        except Exception:

            snapshot = PortfolioHealthSnapshot(

                position_count=0,

                portfolio_value=0.0,

                invested_value=0.0,

                cash_allocation_pct=0.0,

                largest_position="N/A",

                largest_position_weight_pct=0.0,

            )

        pos_count = self._safe_int(getattr(snapshot, "position_count", 0), 0)
        port_val = self._safe_float(getattr(snapshot, "portfolio_value", 0.0), 0.0)
        inv_val = self._safe_float(getattr(snapshot, "invested_value", 0.0), 0.0)
        largest_weight = self._safe_float(getattr(snapshot, "largest_position_weight_pct", 0.0), 0.0)
        cash_pct = self._safe_float(getattr(snapshot, "cash_allocation_pct", 0.0), 0.0)
        largest_pos = str(getattr(snapshot, "largest_position", "N/A"))

        if previous is not None:
            prev_score = self._safe_int(getattr(previous, "score", 0), 0)
            prev_grade = str(getattr(previous, "grade", ""))
            prev_div = str(getattr(previous, "diversification_rating", ""))
            prev_conc = str(getattr(previous, "concentration_rating", ""))
            prev_fp = f"{prev_score}_{prev_grade}_{prev_div}_{prev_conc}"
        else:
            prev_fp = "none"

        import os
        hist_mtime = 0.0
        if self._history_service is not None:
            storage_path = getattr(self._history_service, "storage_path", None)
            if storage_path and os.path.exists(storage_path):
                try:
                    hist_mtime = os.path.getmtime(storage_path)
                except Exception:
                    hist_mtime = 0.0

        cache_key = f"{pos_count}_{port_val:.2f}_{inv_val:.2f}_{cash_pct:.2f}_{largest_pos}_{largest_weight:.2f}_{prev_fp}_{hist_mtime}"
        now = self._time_provider()

        if (
            self._evaluation_cache is not None
            and self._evaluation_cache_key == cache_key
            and (now - self._evaluation_cache_time) < self._evaluation_cache_ttl
        ):
            return self._evaluation_cache

        # 1. Position Count Score (40 pts)
        if pos_count == 0:
            pos_score = 0
            conc_score = 0
            cash_score = 0
            total_score = 0
            grade = "N/A"
            diversification_rating = "N/A"
            concentration_rating = "N/A"
        else:
            if pos_count >= 10:
                pos_score = 40
            elif pos_count >= 7:
                pos_score = 30
            elif pos_count >= 4:
                pos_score = 20
            else:
                pos_score = 10

            # 2. Concentration Score (40 pts)
            if largest_weight <= 10.0:
                conc_score = 40
            elif largest_weight <= 15.0:
                conc_score = 30
            elif largest_weight <= 20.0:
                conc_score = 20
            else:
                conc_score = 10

            # 3. Cash Allocation Score (20 pts)
            if cash_pct <= 10.0:
                cash_score = 20
            elif cash_pct <= 20.0:
                cash_score = 15
            elif cash_pct <= 30.0:
                cash_score = 10
            else:
                cash_score = 5

            total_score = pos_score + conc_score + cash_score

            # Grade Mapping
            if total_score >= 90:
                grade = "A"
            elif total_score >= 80:
                grade = "B"
            elif total_score >= 70:
                grade = "C"
            else:
                grade = "D"

            # Diversification Rating
            if pos_count >= 10:
                diversification_rating = "GOOD"
            elif pos_count >= 6:
                diversification_rating = "MODERATE"
            else:
                diversification_rating = "POOR"

            # Concentration Rating
            if largest_weight <= 10.0:
                concentration_rating = "LOW"
            elif largest_weight <= 20.0:
                concentration_rating = "MODERATE"
            else:
                concentration_rating = "HIGH"

        # Generate Strengths
        strengths = []
        weaknesses = []

        if pos_count == 0:
            weaknesses.append("No active portfolio positions found. Create or import a portfolio.")
        else:
            if pos_count >= 10:
                strengths.append("Good diversification")
            if largest_weight <= 10.0:
                strengths.append("Low concentration risk")
            if cash_pct <= 10.0:
                strengths.append("Healthy cash allocation")

            if pos_count < 6:
                weaknesses.append("Portfolio may be under-diversified")
            if largest_weight > 20.0:
                weaknesses.append("High concentration risk")
            if cash_pct > 20.0:
                weaknesses.append("Elevated cash allocation")

        analytics = PortfolioHealthAnalytics(

            diversification_score=pos_score,

            concentration_score=conc_score,

            cash_score=cash_score,

            strengths=strengths,

            weaknesses=weaknesses,

        )

        res = PortfolioHealthResult(

            score=total_score,

            grade=grade,

            diversification_rating=diversification_rating,

            concentration_rating=concentration_rating,

            position_count=pos_count,

            largest_position_weight_pct=largest_weight,

            cash_allocation_pct=cash_pct,

            analytics=analytics,

        )

        if previous is None and self._history_service is not None:

            try:

                latest = self._history_service.get_latest()

                if latest is not None:

                    previous = PortfolioHealthResult(

                        score=latest.score,

                        grade=latest.grade,

                        diversification_rating=latest.diversification_rating,

                        concentration_rating=latest.concentration_rating,

                        position_count=latest.position_count,

                        largest_position_weight_pct=latest.largest_position_weight_pct,

                        cash_allocation_pct=latest.cash_allocation_pct,

                    )

            except Exception:

                previous = None

        res.trend = self.evaluate_trend(res, previous=previous)

        if self._history_service is not None and hasattr(self._history_service, "get_historical_analytics"):

            try:

                res.historical_analytics = self._history_service.get_historical_analytics()

            except Exception:

                res.historical_analytics = None

        if self._history_service is not None and hasattr(self._history_service, "get_dashboard_summary"):

            try:

                res.dashboard_summary = self._history_service.get_dashboard_summary()

            except Exception:

                res.dashboard_summary = None

        if self._history_service is not None and hasattr(self._history_service, "get_historical_metrics"):

            try:

                res.historical_metrics = self._history_service.get_historical_metrics()

            except Exception:

                res.historical_metrics = None

        if self._history_service is not None and hasattr(self._history_service, "get_historical_insights"):

            try:

                res.historical_insights = self._history_service.get_historical_insights()

            except Exception:

                res.historical_insights = None

        if self._monitor_service is not None and hasattr(self._monitor_service, "get_monitoring_state"):

            try:

                res.monitoring_state = self._monitor_service.get_monitoring_state()

            except Exception:

                res.monitoring_state = None

        else:

            try:

                from services.portfolio_health_monitor_service import PortfolioHealthMonitorService

                mon_svc = PortfolioHealthMonitorService(history_service=self._history_service)

                res.monitoring_state = mon_svc.get_monitoring_state()

            except Exception:

                res.monitoring_state = None

        if self._change_detection_service is not None and hasattr(self._change_detection_service, "detect_changes"):

            try:

                res.change_report = self._change_detection_service.detect_changes()

            except Exception:

                res.change_report = None

        else:

            try:

                from services.portfolio_health_change_detection_service import PortfolioHealthChangeDetectionService

                cd_svc = PortfolioHealthChangeDetectionService(history_service=self._history_service)

                res.change_report = cd_svc.detect_changes()

            except Exception:

                res.change_report = None

        if self._timeline_service is not None and hasattr(self._timeline_service, "build_timeline"):

            try:

                res.timeline = self._timeline_service.build_timeline()

            except Exception:

                res.timeline = None

        else:

            try:

                from services.portfolio_health_timeline_service import PortfolioHealthTimelineService

                tl_svc = PortfolioHealthTimelineService(

                    history_service=self._history_service,

                    change_detection_service=self._change_detection_service,

                )

                res.timeline = tl_svc.build_timeline()

            except Exception:

                res.timeline = None

        if self._monitoring_dashboard_service is not None and hasattr(self._monitoring_dashboard_service, "build_dashboard"):

            try:

                res.monitoring_dashboard = self._monitoring_dashboard_service.build_dashboard()

            except Exception:

                res.monitoring_dashboard = None

        else:

            try:

                from services.portfolio_health_monitor_dashboard_service import PortfolioHealthMonitoringDashboardService

                dash_svc = PortfolioHealthMonitoringDashboardService(

                    history_service=self._history_service,

                    monitor_service=self._monitor_service,

                    change_detection_service=self._change_detection_service,

                    timeline_service=self._timeline_service,

                )

                res.monitoring_dashboard = dash_svc.build_dashboard()

            except Exception:

                res.monitoring_dashboard = None

        if self._alert_center_service is not None and hasattr(self._alert_center_service, "get_state"):

            try:

                res.alert_center = self._alert_center_service.get_state()

            except Exception:

                res.alert_center = None

        else:

            try:

                from services.alert_center_service import AlertCenterService

                ac_svc = AlertCenterService()

                res.alert_center = ac_svc.get_state()

            except Exception:

                res.alert_center = None

        if self._alert_generation_service is not None and hasattr(self._alert_generation_service, "generate_alerts"):

            try:

                res.generated_alerts = self._alert_generation_service.generate_alerts(

                    monitoring_state=res.monitoring_state,

                    change_report=res.change_report,

                    timeline=res.timeline,

                    monitoring_dashboard=res.monitoring_dashboard,

                )

            except Exception:

                res.generated_alerts = None

        else:

            try:

                from services.alert_generation_service import AlertGenerationService

                gen_svc = AlertGenerationService(

                    history_service=self._history_service,

                    monitor_service=self._monitor_service,

                    change_detection_service=self._change_detection_service,

                    timeline_service=self._timeline_service,

                    dashboard_service=self._monitoring_dashboard_service,

                )

                res.generated_alerts = gen_svc.generate_alerts(

                    monitoring_state=res.monitoring_state,

                    change_report=res.change_report,

                    timeline=res.timeline,

                    monitoring_dashboard=res.monitoring_dashboard,

                )

            except Exception:

                res.generated_alerts = None

        # Phase: Alert Rules Engine

        if self._alert_rules_service is not None and hasattr(self._alert_rules_service, "evaluate_rules"):

            try:

                res.alert_rules = self._alert_rules_service.evaluate_rules(

                    monitoring_state=res.monitoring_state,

                    change_report=res.change_report,

                    timeline=res.timeline,

                    monitoring_dashboard=res.monitoring_dashboard,

                )

            except Exception:

                res.alert_rules = None

        else:

            try:

                from services.alert_rules_service import AlertRulesService

                rules_svc = AlertRulesService()

                res.alert_rules = rules_svc.evaluate_rules(

                    monitoring_state=res.monitoring_state,

                    change_report=res.change_report,

                    timeline=res.timeline,

                    monitoring_dashboard=res.monitoring_dashboard,

                )

            except Exception:

                res.alert_rules = None

        # Phase: Alert Dashboard

        if self._alert_dashboard_service is not None and hasattr(self._alert_dashboard_service, "build_dashboard"):

            try:

                res.alert_dashboard = self._alert_dashboard_service.build_dashboard(

                    alert_center_state=res.alert_center,

                    generated_alerts=res.generated_alerts,

                    alert_rules_result=res.alert_rules,

                )

            except Exception:

                res.alert_dashboard = None

        else:

            try:

                from services.alert_dashboard_service import AlertDashboardService

                dash_svc = AlertDashboardService(

                    alert_center_service=self._alert_center_service,

                    alert_generation_service=self._alert_generation_service,

                    alert_rules_service=self._alert_rules_service,

                )

                res.alert_dashboard = dash_svc.build_dashboard(

                    alert_center_state=res.alert_center,

                    generated_alerts=res.generated_alerts,

                    alert_rules_result=res.alert_rules,

                )

            except Exception:

                res.alert_dashboard = None

        # Phase: Alert History

        if self._alert_history_service is not None and hasattr(self._alert_history_service, "get_history"):

            try:

                if res.alert_dashboard is not None and hasattr(self._alert_history_service, "save_history"):

                    try:

                        self._alert_history_service.save_history(getattr(res.alert_dashboard, "alerts", []))

                    except Exception:

                        pass

                res.alert_history = self._alert_history_service.get_history()

            except Exception:

                res.alert_history = None

        else:

            try:

                from services.alert_history_service import AlertHistoryService

                hist_svc = AlertHistoryService()

                if res.alert_dashboard is not None:

                    try:

                        hist_svc.save_history(getattr(res.alert_dashboard, "alerts", []))

                    except Exception:

                        pass

                res.alert_history = hist_svc.get_history()

            except Exception:

                res.alert_history = None

        # Phase: Alert Management

        if self._alert_management_service is not None and hasattr(self._alert_management_service, "get_management_result"):

            try:

                res.alert_management = self._alert_management_service.get_management_result()

            except Exception:

                res.alert_management = None

        else:

            try:

                from services.alert_management_service import AlertManagementService

                mgmt_svc = AlertManagementService(

                    alert_center_service=self._alert_center_service,

                    alert_history_service=self._alert_history_service,

                    alert_dashboard_service=self._alert_dashboard_service,

                )

                res.alert_management = mgmt_svc.get_management_result()

            except Exception:

                res.alert_management = None

        # Phase: Decision Engine

        if self._decision_engine_service is not None and hasattr(self._decision_engine_service, "evaluate"):

            try:

                res.decision_engine = self._decision_engine_service.evaluate(

                    portfolio_health_result=res,

                    alert_management_result=res.alert_management,

                )

            except Exception:

                res.decision_engine = None

        else:

            try:

                from services.decision_engine_service import DecisionEngineService

                dec_svc = DecisionEngineService()

                res.decision_engine = dec_svc.evaluate(

                    portfolio_health_result=res,

                    alert_management_result=res.alert_management,

                )

            except Exception:

                res.decision_engine = None

        # Phase: Decision Classification

        if self._decision_classification_service is not None and hasattr(self._decision_classification_service, "classify"):

            try:

                res.decision_classification = self._decision_classification_service.classify(

                    decision_engine_result=res.decision_engine,

                    portfolio_health_result=res,

                    alert_management_result=res.alert_management,

                )

            except Exception:

                res.decision_classification = None

        else:

            try:

                from services.decision_classification_service import DecisionClassificationService

                cls_svc = DecisionClassificationService()

                res.decision_classification = cls_svc.classify(

                    decision_engine_result=res.decision_engine,

                    portfolio_health_result=res,

                    alert_management_result=res.alert_management,

                )

            except Exception:

                res.decision_classification = None

        # Phase: Decision Prioritization

        if self._decision_prioritization_service is not None and hasattr(self._decision_prioritization_service, "prioritize"):

            try:

                cls_items = getattr(res.decision_classification, "classifications", None) if res.decision_classification else None

                res.decision_prioritization = self._decision_prioritization_service.prioritize(

                    classifications=cls_items,

                )

            except Exception:

                res.decision_prioritization = None

        else:

            try:

                from services.decision_prioritization_service import DecisionPrioritizationService

                prio_svc = DecisionPrioritizationService(

                    decision_classification_service=self._decision_classification_service,

                    decision_engine_service=self._decision_engine_service,

                )

                cls_items = getattr(res.decision_classification, "classifications", None) if res.decision_classification else None

                res.decision_prioritization = prio_svc.prioritize(

                    classifications=cls_items,

                )

            except Exception:

                res.decision_prioritization = None

        if self._decision_dashboard_service is not None and hasattr(self._decision_dashboard_service, "get_dashboard"):

            try:

                res.decision_dashboard = self._decision_dashboard_service.get_dashboard()

            except Exception:

                res.decision_dashboard = None

        # Decision Audit Trail

        if self._decision_audit_service is not None and hasattr(self._decision_audit_service, "record_decisions"):

            try:

                priorities = getattr(res.decision_prioritization, "priorities", []) if res.decision_prioritization else []

                classifications = getattr(res.decision_classification, "classifications", []) if res.decision_classification else []

                res.decision_audit = self._decision_audit_service.record_decisions(

                    decisions=priorities,

                    classifications=classifications,

                    priorities=priorities,

                )

            except Exception:

                res.decision_audit = None

        else:

            try:

                from services.decision_audit_service import DecisionAuditService

                audit_svc = DecisionAuditService()

                priorities = getattr(res.decision_prioritization, "priorities", []) if res.decision_prioritization else []

                classifications = getattr(res.decision_classification, "classifications", []) if res.decision_classification else []

                res.decision_audit = audit_svc.record_decisions(

                    decisions=priorities,

                    classifications=classifications,

                    priorities=priorities,

                )

            except Exception:

                res.decision_audit = None

        # Decision Audit Analytics

        if self._decision_audit_analytics_service is not None and hasattr(self._decision_audit_analytics_service, "analyze"):

            try:

                res.decision_audit_analytics = self._decision_audit_analytics_service.analyze(res.decision_audit)

            except Exception:

                res.decision_audit_analytics = None

        else:

            try:

                from services.decision_audit_analytics_service import DecisionAuditAnalyticsService

                analytics_svc = DecisionAuditAnalyticsService()

                res.decision_audit_analytics = analytics_svc.analyze(res.decision_audit)

            except Exception:

                res.decision_audit_analytics = None

        # Decision Audit Trend

        if self._decision_audit_trend_service is not None and hasattr(self._decision_audit_trend_service, "build_trend"):

            try:

                res.decision_audit_trend = self._decision_audit_trend_service.build_trend(res.decision_audit)

            except Exception:

                res.decision_audit_trend = None

        else:

            try:

                from services.decision_audit_trend_service import DecisionAuditTrendService

                trend_svc = DecisionAuditTrendService()

                res.decision_audit_trend = trend_svc.build_trend(res.decision_audit)

            except Exception:

                res.decision_audit_trend = None

        # Rebalancing Foundation

        if self._rebalancing_service is not None and hasattr(self._rebalancing_service, "get_state"):
            try:
                res.rebalancing = self._rebalancing_service.get_state()
            except Exception:
                res.rebalancing = None
        else:
            try:
                from services.rebalancing_service import RebalancingService

                rebal_svc = RebalancingService(portfolio_service=self._get_app_service())
                res.rebalancing = rebal_svc.get_state()
            except Exception:
                res.rebalancing = None

        # Allocation Analysis Engine
        if self._allocation_analysis_service is not None and hasattr(self._allocation_analysis_service, "analyze"):
            try:
                res.allocation_analysis = self._allocation_analysis_service.analyze(res.rebalancing)
            except Exception:
                res.allocation_analysis = None
        else:
            try:
                from services.allocation_analysis_service import AllocationAnalysisService
                alloc_svc = AllocationAnalysisService()
                res.allocation_analysis = alloc_svc.analyze(res.rebalancing)
            except Exception:
                res.allocation_analysis = None

        # Drift Detection Engine
        if self._drift_detection_service is not None and hasattr(self._drift_detection_service, "detect_drift"):
            try:
                res.drift_detection = self._drift_detection_service.detect_drift(res.rebalancing, res.allocation_analysis)
            except Exception:
                res.drift_detection = None
        else:
            try:
                from services.drift_detection_service import DriftDetectionService
                drift_svc = DriftDetectionService()
                res.drift_detection = drift_svc.detect_drift(res.rebalancing, res.allocation_analysis)
            except Exception:
                res.drift_detection = None

        # Rebalancing Candidate Engine
        if self._rebalancing_candidate_service is not None and hasattr(self._rebalancing_candidate_service, "identify_candidates"):
            try:
                res.rebalancing_candidates = self._rebalancing_candidate_service.identify_candidates(res.rebalancing, res.allocation_analysis, res.drift_detection)
            except Exception:
                res.rebalancing_candidates = None
        else:
            try:
                from services.rebalancing_candidate_service import RebalancingCandidateService
                cand_svc = RebalancingCandidateService()
                res.rebalancing_candidates = cand_svc.identify_candidates(res.rebalancing, res.allocation_analysis, res.drift_detection)
            except Exception:
                res.rebalancing_candidates = None

        # Rebalancing Recommendation Framework
        if self._rebalancing_recommendation_service is not None and hasattr(self._rebalancing_recommendation_service, "generate_recommendations"):
            try:
                res.rebalancing_recommendations = self._rebalancing_recommendation_service.generate_recommendations(res.rebalancing, res.allocation_analysis, res.drift_detection, res.rebalancing_candidates)
            except Exception:
                res.rebalancing_recommendations = None
        else:
            try:
                from services.rebalancing_recommendation_service import RebalancingRecommendationService
                rec_svc = RebalancingRecommendationService()
                res.rebalancing_recommendations = rec_svc.generate_recommendations(res.rebalancing, res.allocation_analysis, res.drift_detection, res.rebalancing_candidates)
            except Exception:
                res.rebalancing_recommendations = None

        # Portfolio Intelligence Layer
        if self._portfolio_intelligence_service is not None and hasattr(self._portfolio_intelligence_service, "get_intelligence"):
            try:
                res.portfolio_intelligence = self._portfolio_intelligence_service.get_intelligence()
            except Exception:
                res.portfolio_intelligence = None
        else:
            try:
                from services.portfolio_intelligence_service import PortfolioIntelligenceService
                intel_svc = PortfolioIntelligenceService()
                res.portfolio_intelligence = intel_svc.get_intelligence()
            except Exception:
                res.portfolio_intelligence = None

        # Holding Quality Engine
        if self._holding_quality_service is not None and hasattr(self._holding_quality_service, "assess_holdings"):
            try:
                res.holding_quality = self._holding_quality_service.assess_holdings()
            except Exception:
                res.holding_quality = None
        else:
            try:
                from services.holding_quality_service import HoldingQualityService
                hq_svc = HoldingQualityService()
                res.holding_quality = hq_svc.assess_holdings()
            except Exception:
                res.holding_quality = None

        # SIP Optimization Engine
        if self._sip_optimization_service is not None and hasattr(self._sip_optimization_service, "analyze_sip"):
            try:
                res.sip_optimization = self._sip_optimization_service.analyze_sip()
            except Exception:
                res.sip_optimization = None
        else:
            try:
                from services.sip_optimization_service import SIPOptimizationService
                sip_svc = SIPOptimizationService()
                res.sip_optimization = sip_svc.analyze_sip()
            except Exception:
                res.sip_optimization = None

        # Portfolio Opportunity Engine
        if self._portfolio_opportunity_service is not None and hasattr(self._portfolio_opportunity_service, "get_opportunities"):
            try:
                res.portfolio_opportunities = self._portfolio_opportunity_service.get_opportunities()
            except Exception:
                res.portfolio_opportunities = None
        else:
            try:
                from services.portfolio_opportunity_service import PortfolioOpportunityService
                opp_svc = PortfolioOpportunityService()
                res.portfolio_opportunities = opp_svc.get_opportunities()
            except Exception:
                res.portfolio_opportunities = None

        # Portfolio Risk Intelligence
        if self._portfolio_risk_intelligence_service is not None and hasattr(self._portfolio_risk_intelligence_service, "get_risk"):
            try:
                res.portfolio_risk_intelligence = self._portfolio_risk_intelligence_service.get_risk()
            except Exception:
                res.portfolio_risk_intelligence = None
        else:
            try:
                from services.portfolio_risk_intelligence_service import PortfolioRiskIntelligenceService
                risk_svc = PortfolioRiskIntelligenceService()
                res.portfolio_risk_intelligence = risk_svc.get_risk()
            except Exception:
                res.portfolio_risk_intelligence = None

        # Alpha 12 Portfolio Mapping
        if self._alpha12_mapping_service is not None and hasattr(self._alpha12_mapping_service, "get_mapping"):
            try:
                res.alpha12_mapping = self._alpha12_mapping_service.get_mapping()
            except Exception:
                res.alpha12_mapping = None
        else:
            try:
                from services.alpha12_mapping_service import Alpha12MappingService
                map_svc = Alpha12MappingService()
                res.alpha12_mapping = map_svc.get_mapping()
            except Exception:
                res.alpha12_mapping = None

        # Alpha12 Health Integration (non-blocking: defensive)
        try:
            if self._alpha12_health_integration_service is not None and hasattr(self._alpha12_health_integration_service, "get_health_integration"):
                try:
                    res.alpha12_health_integration = self._alpha12_health_integration_service.get_health_integration(
                        res.alpha12_mapping,
                        res,
                        getattr(res, "holding_quality", None),
                        getattr(res, "portfolio_risk_intelligence", None),
                    )
                except Exception:
                    res.alpha12_health_integration = None
            else:
                try:
                    from services.alpha12_health_integration_service import Alpha12HealthIntegrationService
                    int_svc = Alpha12HealthIntegrationService(
                        alpha12_mapping_service=self._alpha12_mapping_service,
                        portfolio_health_service=self,
                        portfolio_intelligence_service=self._portfolio_intelligence_service,
                        holding_quality_service=self._holding_quality_service,
                        portfolio_risk_intelligence_service=self._portfolio_risk_intelligence_service,
                    )
                    res.alpha12_health_integration = int_svc.get_health_integration(
                        res.alpha12_mapping,
                        res,
                        getattr(res, "holding_quality", None),
                        getattr(res, "portfolio_risk_intelligence", None),
                    )
                except Exception:
                    res.alpha12_health_integration = None
        except Exception:
            res.alpha12_health_integration = None

        # Alpha12 Challenger Evaluation (non-blocking: defensive)
        try:
            if self._alpha12_challenger_service is not None and hasattr(self._alpha12_challenger_service, "evaluate"):
                try:
                    res.alpha12_challenger_evaluation = self._alpha12_challenger_service.evaluate(
                        res.alpha12_mapping,
                        res,
                        getattr(res, "holding_quality", None),
                        getattr(res, "portfolio_risk_intelligence", None),
                    )
                except Exception:
                    res.alpha12_challenger_evaluation = None
            else:
                try:
                    from services.alpha12_challenger_service import Alpha12ChallengerService
                    ch_svc = Alpha12ChallengerService(
                        alpha12_mapping_service=self._alpha12_mapping_service,
                        alpha12_health_integration_service=self._alpha12_health_integration_service,
                        holding_quality_service=self._holding_quality_service,
                        portfolio_risk_intelligence_service=self._portfolio_risk_intelligence_service,
                    )
                    res.alpha12_challenger_evaluation = ch_svc.evaluate(
                        res.alpha12_mapping,
                        res,
                        getattr(res, "holding_quality", None),
                        getattr(res, "portfolio_risk_intelligence", None),
                    )
                except Exception:
                    res.alpha12_challenger_evaluation = None
        except Exception:
            res.alpha12_challenger_evaluation = None

        # Alpha 12 Replacement Governance (non-blocking: defensive)
        try:
            if self._alpha12_replacement_governance_service is not None and hasattr(self._alpha12_replacement_governance_service, "evaluate_replacements"):
                try:
                    res.alpha12_replacement_governance = self._alpha12_replacement_governance_service.evaluate_replacements()
                except Exception:
                    res.alpha12_replacement_governance = None
            else:
                try:
                    from services.alpha12_replacement_governance_service import Alpha12ReplacementGovernanceService
                    gov_svc = Alpha12ReplacementGovernanceService(
                        alpha12_mapping_service=self._alpha12_mapping_service,
                        alpha12_challenger_service=self._alpha12_challenger_service,
                        alpha12_health_integration_service=self._alpha12_health_integration_service,
                        portfolio_health_service=self,
                    )
                    res.alpha12_replacement_governance = gov_svc.evaluate_replacements()
                except Exception:
                    res.alpha12_replacement_governance = None
        except Exception:
            res.alpha12_replacement_governance = None

        # Stage 18: Alpha 12 Long-Term Portfolio Stability Engine (non-blocking: defensive)
        try:
            if self._alpha12_stability_service is not None and hasattr(self._alpha12_stability_service, "get_stability"):
                try:
                    res.alpha12_stability = self._alpha12_stability_service.get_stability(
                        alpha12_mapping=res.alpha12_mapping,
                        governance_result=getattr(res, "alpha12_replacement_governance", None),
                        health_result=res,
                    )
                except Exception:
                    res.alpha12_stability = None
            else:
                try:
                    from services.alpha12_stability_service import Alpha12StabilityService

                    stab_svc = Alpha12StabilityService(
                        alpha12_mapping_service=self._alpha12_mapping_service,
                        alpha12_replacement_governance_service=self._alpha12_replacement_governance_service,
                        portfolio_health_service=self,
                    )
                    res.alpha12_stability = stab_svc.get_stability(
                        alpha12_mapping=res.alpha12_mapping,
                        governance_result=getattr(res, "alpha12_replacement_governance", None),
                        health_result=res,
                    )
                except Exception:
                    res.alpha12_stability = None
        except Exception:
            res.alpha12_stability = None

        self._evaluation_cache = res
        self._evaluation_cache_key = cache_key
        self._evaluation_cache_time = now

        return res

    def _get_app_service(self) -> Optional[Any]:

        if self._portfolio_app_service is not None:

            return self._portfolio_app_service

        try:

            from services.portfolio_application_service import (

                create_portfolio_application_service,

            )

            return create_portfolio_application_service()

        except Exception:

            try:

                from services.portfolio_application_service import (

                    PortfolioApplicationService,

                )

                return PortfolioApplicationService()

            except Exception:

                return None

    @staticmethod

    def _safe_float(val: Any, default: float = 0.0) -> float:

        try:

            if val is None:

                return default

            return float(val)

        except (TypeError, ValueError):

            return default

    @staticmethod

    def _safe_int(val: Any, default: int = 0) -> int:

        try:

            if val is None:

                return default

            return int(val)

        except (TypeError, ValueError):

            return default
