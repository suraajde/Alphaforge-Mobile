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
        largest_weight = self._safe_float(getattr(snapshot, "largest_position_weight_pct", 0.0), 0.0)
        cash_pct = self._safe_float(getattr(snapshot, "cash_allocation_pct", 0.0), 0.0)

        # 1. Position Count Score (40 pts)
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
        if pos_count >= 10:
            strengths.append("Good diversification")
        if largest_weight <= 10.0:
            strengths.append("Low concentration risk")
        if cash_pct <= 10.0:
            strengths.append("Healthy cash allocation")

        # Generate Weaknesses
        weaknesses = []
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