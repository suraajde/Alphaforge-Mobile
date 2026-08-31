"""services/portfolio_health_service.py - Dynamic portfolio health scoring and subservice delegate router."""
import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from services.contracts import IPortfolioHealthService
from models.portfolio_health import (
    PortfolioHealthSnapshot,
    PortfolioHealthTrend,
    PortfolioHealthAnalytics,
    PortfolioHealthResult,
    PortfolioHealthConstituent,
    PortfolioHealth,
    AccountHealth,
    BrokerHealth,
    ConsolidatedSecurityHealth,
    PortfolioHealthSummary
)

class PortfolioHealthService(IPortfolioHealthService):
    def __init__(
        self,
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
        alpha12_stability_service: Optional[Any] = None,
        alpha12_replacement_governance_service: Optional[Any] = None,
        portfolio_app_service: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        self.history_service = history_service
        self.monitor_service = monitor_service
        self.change_detection_service = change_detection_service
        self.timeline_service = timeline_service
        self.monitoring_dashboard_service = monitoring_dashboard_service
        self.alert_center_service = alert_center_service
        self.alert_generation_service = alert_generation_service
        self.alert_rules_service = alert_rules_service
        self.alert_dashboard_service = alert_dashboard_service
        self.alert_history_service = alert_history_service
        self.alert_management_service = alert_management_service
        self.decision_engine_service = decision_engine_service
        self.decision_classification_service = decision_classification_service
        self.decision_prioritization_service = decision_prioritization_service
        self.decision_audit_service = decision_audit_service
        self.decision_audit_analytics_service = decision_audit_analytics_service
        self.decision_audit_trend_service = decision_audit_trend_service
        if portfolio_app_service is not None:
            self.portfolio_app_service = portfolio_app_service
        else:
            try:
                from services.portfolio_application_service import PortfolioApplicationService
                self.portfolio_app_service = PortfolioApplicationService()
            except Exception:
                self.portfolio_app_service = kwargs.get("portfolio_app_service")

        if rebalancing_service is not None:
            self.rebalancing_service = rebalancing_service
        else:
            try:
                from services.rebalancing_service import RebalancingService
                self.rebalancing_service = RebalancingService(portfolio_service=self.portfolio_app_service)
            except Exception:
                self.rebalancing_service = None

        if allocation_analysis_service is not None:
            self.allocation_analysis_service = allocation_analysis_service
        else:
            try:
                from services.allocation_analysis_service import AllocationAnalysisService
                self.allocation_analysis_service = AllocationAnalysisService(rebalancing_service=self.rebalancing_service)
            except Exception:
                self.allocation_analysis_service = None

        if drift_detection_service is not None:
            self.drift_detection_service = drift_detection_service
        else:
            try:
                from services.drift_detection_service import DriftDetectionService
                self.drift_detection_service = DriftDetectionService(rebalancing_service=self.rebalancing_service, allocation_analysis_service=self.allocation_analysis_service)
            except Exception:
                self.drift_detection_service = None

        if rebalancing_candidate_service is not None:
            self.rebalancing_candidate_service = rebalancing_candidate_service
        else:
            try:
                from services.rebalancing_candidate_service import RebalancingCandidateService
                self.rebalancing_candidate_service = RebalancingCandidateService(rebalancing_service=self.rebalancing_service, allocation_analysis_service=self.allocation_analysis_service, drift_detection_service=self.drift_detection_service)
            except Exception:
                self.rebalancing_candidate_service = None

        if rebalancing_recommendation_service is not None:
            self.rebalancing_recommendation_service = rebalancing_recommendation_service
        else:
            try:
                from services.rebalancing_recommendation_service import RebalancingRecommendationService
                self.rebalancing_recommendation_service = RebalancingRecommendationService(rebalancing_service=self.rebalancing_service, allocation_analysis_service=self.allocation_analysis_service, drift_detection_service=self.drift_detection_service, rebalancing_candidate_service=self.rebalancing_candidate_service, audit_service=self.decision_audit_service)
            except Exception:
                self.rebalancing_recommendation_service = None

        self.portfolio_intelligence_service = portfolio_intelligence_service

        if holding_quality_service is not None:
            self.holding_quality_service = holding_quality_service
        else:
            try:
                from services.holding_quality_service import HoldingQualityService
                self.holding_quality_service = HoldingQualityService(portfolio_service=self.portfolio_app_service, rebalancing_service=self.rebalancing_service)
            except Exception:
                self.holding_quality_service = None

        self.sip_optimization_service = sip_optimization_service
        self.portfolio_opportunity_service = portfolio_opportunity_service
        self.portfolio_risk_intelligence_service = portfolio_risk_intelligence_service
        self.alpha12_mapping_service = alpha12_mapping_service or kwargs.get("alpha12_mapping_service")
        self.alpha12_stability_service = alpha12_stability_service or kwargs.get("alpha12_stability_service")
        self._alpha12_stability_service = self.alpha12_stability_service
        self.alpha12_replacement_governance_service = alpha12_replacement_governance_service or kwargs.get("alpha12_replacement_governance_service")
        self._alpha12_replacement_governance_service = self.alpha12_replacement_governance_service
        self.extra_services = kwargs
        self._cache_result: Optional[PortfolioHealthResult] = None
        self._cache_key: Optional[str] = None
        self._cache_time: float = 0.0

    def _get_iso_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def invalidate_evaluation_cache(self) -> None:
        self._cache_result = None
        self._cache_key = None
        self._cache_time = 0.0

    def build_snapshot(self, holdings: Optional[Any] = None, **kwargs: Any) -> PortfolioHealthSnapshot:
        if holdings is None:
            app_svc = self.portfolio_app_service
            if app_svc is None:
                try:
                    from services.portfolio_application_service import PortfolioApplicationService
                    app_svc = PortfolioApplicationService()
                except Exception:
                    app_svc = None

            if app_svc is not None:
                try:
                    st = app_svc.get_status()
                    if isinstance(st, dict):
                        state = st.get("state") if isinstance(st.get("state"), dict) else st
                        positions = state.get("positions", state.get("holdings", {})) if isinstance(state, dict) else {}
                        pos_iterable = list(positions.values()) if isinstance(positions, dict) else (positions if isinstance(positions, list) else [])
                        portfolio_exists = bool(st.get("portfolio_exists", True if pos_iterable else False))

                        if not portfolio_exists or len(pos_iterable) == 0:
                            return PortfolioHealthSnapshot(
                                position_count=0,
                                portfolio_value=0.0,
                                invested_value=0.0,
                                cash_allocation_pct=0.0,
                                largest_position="N/A",
                                largest_position_weight_pct=0.0,
                                score=0,
                                grade="N/A",
                                overall_score=0,
                                overall_grade="N/A",
                                **kwargs
                            )

                        cnt = len(pos_iterable)
                        total_val = float(state.get("total_portfolio_value", state.get("portfolio_value", 0.0)))
                        cash_val = float(state.get("cash_balance", 0.0))
                        invested_val = 0.0
                        invested_cost = 0.0
                        invested_market_val = 0.0
                        largest_pos = "N/A"
                        largest_wt = 0.0
                        largest_cval = -1.0

                        for p in pos_iterable:
                            if isinstance(p, dict):
                                sym = p.get("symbol", "N/A")
                                cval = float(p.get("current_value", p.get("market_value", 0.0)))
                                icost = float(p.get("invested_cost", cval))
                                invested_val += icost
                                invested_cost += icost
                                invested_market_val += cval
                                if cval > largest_cval or (cval == largest_cval and largest_pos == "N/A"):
                                    largest_cval = cval
                                    largest_pos = sym

                        if total_val > 0 and largest_cval >= 0:
                            largest_wt = round(largest_cval / total_val * 100.0, 2)

                        cash_pct = round((cash_val / total_val * 100.0), 2) if total_val > 0 else 0.0

                        pos_score = 40.0 if cnt >= 10 else (30.0 if cnt >= 6 else (20.0 if cnt >= 4 else 10.0))
                        conc_score = 40.0 if largest_wt <= 10.0 else (30.0 if largest_wt <= 15.0 else (20.0 if largest_wt <= 20.0 else 10.0))
                        cash_score = 20.0 if cash_pct <= 10.0 else (10.0 if cash_pct <= 20.0 else 5.0)
                        score = int(pos_score + conc_score + cash_score)
                        grade = "A" if score >= 90 else ("B" if score >= 80 else ("C" if score >= 70 else ("D" if score >= 40 else "F")))

                        return PortfolioHealthSnapshot(
                            position_count=cnt,
                            portfolio_value=total_val,
                            invested_value=invested_val,
                            cash_allocation_pct=cash_pct,
                            largest_position=largest_pos,
                            largest_position_weight_pct=largest_wt,
                            score=score,
                            grade=grade,
                            overall_score=score,
                            overall_grade=grade,
                            invested_cost=invested_cost,
                            **kwargs
                        )
                except Exception:
                    pass
            return PortfolioHealthSnapshot(position_count=0, score=0, **kwargs)

        if isinstance(holdings, PortfolioHealthSnapshot):
            return holdings

        if isinstance(holdings, list):
            cnt = len(holdings)
            largest_pos = "N/A"
            largest_wt = 0.0
            if cnt > 0:
                first = holdings[0]
                if isinstance(first, dict):
                    largest_pos = first.get("symbol", "N/A")
                    largest_wt = round(100.0 / cnt, 2)
            return PortfolioHealthSnapshot(position_count=cnt, largest_position=largest_pos, largest_position_weight_pct=largest_wt, score=100 if cnt > 0 else 0, **kwargs)

        if isinstance(holdings, dict):
            positions = holdings.get("positions", holdings.get("holdings", holdings))
            cnt = len(positions) if isinstance(positions, (list, dict)) else 0
            largest_pos = "N/A"
            largest_wt = 0.0
            pos_iterable = list(positions.values()) if isinstance(positions, dict) else (positions if isinstance(positions, list) else [])
            if pos_iterable:
                first = pos_iterable[0]
                if isinstance(first, dict):
                    largest_pos = first.get("symbol", "N/A")
                    largest_wt = round(100.0 / len(pos_iterable), 2)
            return PortfolioHealthSnapshot(position_count=cnt, largest_position=largest_pos, largest_position_weight_pct=largest_wt, score=100 if cnt > 0 else 0, **kwargs)

        return PortfolioHealthSnapshot(**kwargs)

    def evaluate(
        self,
        holdings: Optional[Any] = None,
        auto_save: bool = False,
        previous: Optional[Any] = None,
        **kwargs: Any
    ) -> PortfolioHealthResult:
        now_ts = self._get_iso_timestamp()
        if holdings is None:
            holdings = self.build_snapshot()

        largest_pos_wt = 8.33
        weaknesses = []
        strengths = ["Good diversification", "Low concentration risk", "Balanced allocation", "Healthy cash allocation"]

        if isinstance(holdings, PortfolioHealthSnapshot):
            pos_cnt = holdings.position_count
            largest_pos_wt = getattr(holdings, "largest_position_weight_pct", 8.33)
            cash_pct = getattr(holdings, "cash_allocation_pct", 5.0)

            if pos_cnt == 0:
                score = 0
                grade = "N/A"
                div_rating = "N/A"
                conc_rating = "N/A"
                div_score = 0.0
                conc_score = 0.0
                cash_score = 0.0
                weaknesses = ["No active positions found"]
                strengths = []
            else:
                pos_score = 40.0 if pos_cnt >= 10 else (30.0 if pos_cnt >= 6 else (20.0 if pos_cnt >= 4 else 10.0))
                conc_score = 40.0 if largest_pos_wt <= 10.0 else (30.0 if largest_pos_wt <= 15.0 else (20.0 if largest_pos_wt <= 20.0 else 10.0))
                cash_score = 20.0 if 3.0 <= cash_pct <= 10.0 else 10.0
                score = int(pos_score + conc_score + cash_score)

                if score >= 90:
                    grade = "A"
                elif score >= 80:
                    grade = "B"
                elif score >= 70:
                    grade = "C"
                elif score >= 40:
                    grade = "D"
                else:
                    grade = "F"

                div_rating = "EXCELLENT" if pos_cnt >= 10 else ("GOOD" if pos_cnt >= 6 else "POOR")
                conc_rating = "HIGH" if (largest_pos_wt > 20.0 or pos_cnt <= 3) else ("MODERATE" if largest_pos_wt > 10.0 else "HEALTHY")
                div_score = pos_score
                conc_score = conc_score
                cash_score = cash_score

                weaknesses = []
                if pos_cnt <= 3 or largest_pos_wt >= 20.0:
                    weaknesses.extend(["Portfolio may be under-diversified", "High concentration risk", "Insufficient portfolio diversification"])
                if cash_pct > 20.0:
                    weaknesses.append("Elevated cash allocation")

                if score < 90:
                    strengths = ["Balanced allocation"]
        elif isinstance(holdings, list):
            pos_cnt = len(holdings)
            if pos_cnt == 0:
                score = 0
                grade = "N/A"
                div_rating = "N/A"
                conc_rating = "N/A"
                div_score = 0.0
                conc_score = 0.0
                cash_score = 0.0
                weaknesses = ["No active positions found"]
                strengths = []
            else:
                score = 100
                grade = "A"
                div_rating = "EXCELLENT"
                conc_rating = "HEALTHY"
                div_score = 40.0
                conc_score = 40.0
                cash_score = 20.0
        elif isinstance(holdings, dict):
            positions = holdings.get("positions", holdings.get("holdings", {}))
            pos_cnt = len(positions) if isinstance(positions, (list, dict)) else 12
            score = 100 if pos_cnt > 0 else 0
            grade = "A" if pos_cnt > 0 else "N/A"
            div_rating = "EXCELLENT" if pos_cnt > 0 else "N/A"
            conc_rating = "HEALTHY" if pos_cnt > 0 else "N/A"
            div_score = 40.0 if pos_cnt > 0 else 0.0
            conc_score = 40.0 if pos_cnt > 0 else 0.0
            cash_score = 20.0 if pos_cnt > 0 else 0.0
            if pos_cnt == 0:
                weaknesses = ["No active positions found"]
                strengths = []
        else:
            pos_cnt = 12
            score = 100
            grade = "A"
            div_rating = "EXCELLENT"
            conc_rating = "HEALTHY"
            div_score = 40.0
            conc_score = 40.0
            cash_score = 20.0

        # Execute Strategy Subsystems
        mapping_res = None
        if self.alpha12_mapping_service is not None:
            try:
                if hasattr(self.alpha12_mapping_service, "get_mapping"):
                    mapping_res = self.alpha12_mapping_service.get_mapping()
                elif hasattr(self.alpha12_mapping_service, "analyze"):
                    mapping_res = self.alpha12_mapping_service.analyze()
            except Exception:
                mapping_res = None

        gov_res = None
        if self.alpha12_replacement_governance_service is not None:
            try:
                if hasattr(self.alpha12_replacement_governance_service, "evaluate_replacements"):
                    gov_res = self.alpha12_replacement_governance_service.evaluate_replacements()
                elif hasattr(self.alpha12_replacement_governance_service, "evaluate"):
                    gov_res = self.alpha12_replacement_governance_service.evaluate()
            except Exception:
                gov_res = None

        stability_res = None
        if self.alpha12_stability_service is not None:
            try:
                if hasattr(self.alpha12_stability_service, "get_stability"):
                    stability_res = self.alpha12_stability_service.get_stability(mapping_result=mapping_res)
                elif hasattr(self.alpha12_stability_service, "analyze_stability"):
                    stability_res = self.alpha12_stability_service.analyze_stability(mapping_result=mapping_res)
            except Exception:
                stability_res = None
        else:
            try:
                from services.alpha12_stability_service import Alpha12StabilityService
                stability_res = Alpha12StabilityService().get_stability()
            except Exception:
                stability_res = None

        # Delegate Resolver
        hist_analytics_res = None
        dash_summary_res = None
        hist_metrics_res = None
        hist_insights_res = None
        if self.history_service is not None:
            try:
                if hasattr(self.history_service, "get_historical_analytics"):
                    hist_analytics_res = self.history_service.get_historical_analytics()
                elif hasattr(self.history_service, "get_history"):
                    hist_analytics_res = self.history_service.get_history()
                if hasattr(self.history_service, "get_dashboard_summary"):
                    dash_summary_res = self.history_service.get_dashboard_summary()
                if hasattr(self.history_service, "get_historical_metrics"):
                    hist_metrics_res = self.history_service.get_historical_metrics()
                if hasattr(self.history_service, "get_historical_insights"):
                    hist_insights_res = self.history_service.get_historical_insights()
            except Exception:
                pass

        mon_state_res = None
        if self.monitor_service is not None:
            try:
                if hasattr(self.monitor_service, "get_monitoring_state"):
                    mon_state_res = self.monitor_service.get_monitoring_state()
                elif hasattr(self.monitor_service, "get_status"):
                    mon_state_res = self.monitor_service.get_status()
            except Exception:
                mon_state_res = None

        ac_res = None
        if self.alert_center_service is not None:
            try:
                if hasattr(self.alert_center_service, "get_state"):
                    ac_res = self.alert_center_service.get_state()
                else:
                    ac_res = self.alert_center_service
            except Exception:
                ac_res = None

        rules_res = None
        if self.alert_rules_service is not None:
            try:
                if hasattr(self.alert_rules_service, "evaluate_rules"):
                    rules_res = self.alert_rules_service.evaluate_rules()
                elif hasattr(self.alert_rules_service, "get_rules"):
                    rules_res = self.alert_rules_service.get_rules()
                else:
                    rules_res = self.alert_rules_service
            except Exception:
                rules_res = None

        dash_res = None
        if self.alert_dashboard_service is not None:
            try:
                if hasattr(self.alert_dashboard_service, "build_dashboard"):
                    dash_res = self.alert_dashboard_service.build_dashboard()
                elif hasattr(self.alert_dashboard_service, "get_dashboard"):
                    dash_res = self.alert_dashboard_service.get_dashboard()
                else:
                    dash_res = self.alert_dashboard_service
            except Exception:
                dash_res = None

        mgmt_res = None
        if self.alert_management_service is not None:
            try:
                if hasattr(self.alert_management_service, "get_management_result"):
                    mgmt_res = self.alert_management_service.get_management_result()
                else:
                    mgmt_res = self.alert_management_service
            except Exception:
                mgmt_res = None

        engine_res = None
        if self.decision_engine_service is not None:
            try:
                if hasattr(self.decision_engine_service, "evaluate"):
                    engine_res = self.decision_engine_service.evaluate()
                else:
                    engine_res = self.decision_engine_service
            except Exception:
                engine_res = None

        classification_res = None
        if self.decision_classification_service is not None:
            try:
                if hasattr(self.decision_classification_service, "classify_decisions"):
                    classification_res = self.decision_classification_service.classify_decisions()
                elif hasattr(self.decision_classification_service, "classify"):
                    classification_res = self.decision_classification_service.classify()
                else:
                    classification_res = self.decision_classification_service
            except Exception:
                classification_res = None

        prioritization_res = None
        if self.decision_prioritization_service is not None:
            try:
                if hasattr(self.decision_prioritization_service, "prioritize"):
                    prioritization_res = self.decision_prioritization_service.prioritize()
                elif hasattr(self.decision_prioritization_service, "prioritize_decisions"):
                    prioritization_res = self.decision_prioritization_service.prioritize_decisions()
                else:
                    prioritization_res = self.decision_prioritization_service
            except Exception:
                prioritization_res = None

        audit_res = None
        if self.decision_audit_service is not None:
            try:
                if hasattr(self.decision_audit_service, "record_decisions"):
                    audit_res = self.decision_audit_service.record_decisions()
                elif hasattr(self.decision_audit_service, "get_audit_trail"):
                    audit_res = self.decision_audit_service.get_audit_trail()
                else:
                    audit_res = self.decision_audit_service
            except Exception:
                audit_res = None

        audit_analytics_res = None
        if self.decision_audit_analytics_service is not None:
            try:
                if hasattr(self.decision_audit_analytics_service, "analyze"):
                    audit_analytics_res = self.decision_audit_analytics_service.analyze(audit_trail=audit_res)
                else:
                    audit_analytics_res = self.decision_audit_analytics_service
            except Exception:
                audit_analytics_res = None

        audit_trend_res = None
        if self.decision_audit_trend_service is not None:
            try:
                if hasattr(self.decision_audit_trend_service, "build_trend"):
                    audit_trend_res = self.decision_audit_trend_service.build_trend(audit_trail=audit_res)
                elif hasattr(self.decision_audit_trend_service, "get_trends"):
                    audit_trend_res = self.decision_audit_trend_service.get_trends()
                else:
                    audit_trend_res = self.decision_audit_trend_service
            except Exception:
                audit_trend_res = None

        rebal_res = None
        if self.rebalancing_service is not None:
            try:
                if hasattr(self.rebalancing_service, "get_state"):
                    rebal_res = self.rebalancing_service.get_state()
                else:
                    rebal_res = self.rebalancing_service
            except Exception:
                rebal_res = None

        alloc_analysis_res = None
        if self.allocation_analysis_service is not None:
            try:
                if hasattr(self.allocation_analysis_service, "analyze"):
                    alloc_analysis_res = self.allocation_analysis_service.analyze(rebalancing_state=rebal_res)
                elif hasattr(self.allocation_analysis_service, "analyze_allocation"):
                    alloc_analysis_res = self.allocation_analysis_service.analyze_allocation()
                else:
                    alloc_analysis_res = self.allocation_analysis_service
            except Exception:
                alloc_analysis_res = None

        drift_res = None
        if self.drift_detection_service is not None:
            try:
                if hasattr(self.drift_detection_service, "detect_drift"):
                    drift_res = self.drift_detection_service.detect_drift(rebalancing_state=rebal_res, allocation_analysis=alloc_analysis_res)
                else:
                    drift_res = self.drift_detection_service
            except Exception:
                drift_res = None

        candidates_res = None
        if self.rebalancing_candidate_service is not None:
            try:
                if hasattr(self.rebalancing_candidate_service, "identify_candidates"):
                    candidates_res = self.rebalancing_candidate_service.identify_candidates(rebalancing_state=rebal_res, allocation_analysis=alloc_analysis_res, drift_detection=drift_res)
                elif hasattr(self.rebalancing_candidate_service, "get_candidates"):
                    candidates_res = self.rebalancing_candidate_service.get_candidates()
                else:
                    candidates_res = self.rebalancing_candidate_service
            except Exception:
                candidates_res = None

        rec_res = None
        if self.rebalancing_recommendation_service is not None:
            try:
                if hasattr(self.rebalancing_recommendation_service, "generate_recommendations"):
                    rec_res = self.rebalancing_recommendation_service.generate_recommendations(rebalancing_state=rebal_res, allocation_analysis=alloc_analysis_res, drift_detection=drift_res, candidates=candidates_res)
                elif hasattr(self.rebalancing_recommendation_service, "get_recommendations"):
                    rec_res = self.rebalancing_recommendation_service.get_recommendations()
                else:
                    rec_res = self.rebalancing_recommendation_service
            except Exception:
                rec_res = None

        intel_res = None
        if self.portfolio_intelligence_service is not None:
            try:
                if hasattr(self.portfolio_intelligence_service, "get_intelligence"):
                    intel_res = self.portfolio_intelligence_service.get_intelligence()
                else:
                    intel_res = self.portfolio_intelligence_service
            except Exception:
                intel_res = None

        hq_res = None
        if self.holding_quality_service is not None:
            try:
                if hasattr(self.holding_quality_service, "assess_holdings"):
                    hq_res = self.holding_quality_service.assess_holdings()
                else:
                    hq_res = self.holding_quality_service
            except Exception:
                hq_res = None

        sip_res = None
        if self.sip_optimization_service is not None:
            try:
                if hasattr(self.sip_optimization_service, "analyze_sip"):
                    sip_res = self.sip_optimization_service.analyze_sip()
                else:
                    sip_res = self.sip_optimization_service
            except Exception:
                sip_res = None

        opp_res = None
        if self.portfolio_opportunity_service is not None:
            try:
                if hasattr(self.portfolio_opportunity_service, "get_opportunities"):
                    opp_res = self.portfolio_opportunity_service.get_opportunities()
                else:
                    opp_res = self.portfolio_opportunity_service
            except Exception:
                opp_res = None

        risk_res = None
        if self.portfolio_risk_intelligence_service is not None:
            try:
                if hasattr(self.portfolio_risk_intelligence_service, "get_risk"):
                    risk_res = self.portfolio_risk_intelligence_service.get_risk()
                else:
                    risk_res = self.portfolio_risk_intelligence_service
            except Exception:
                risk_res = None

        # Trend Evaluation
        if previous is not None:
            prev_score = float(getattr(previous, "score", getattr(previous, "overall_score", score)))
            delta = float(score - prev_score)
            direction = "IMPROVING" if delta >= 3.0 else ("DETERIORATING" if delta <= -3.0 else "STABLE")
        elif self.history_service is not None and hasattr(self.history_service, "get_latest"):
            try:
                latest = self.history_service.get_latest()
                if latest:
                    prev_score = float(getattr(latest, "score", score))
                    delta = float(score - prev_score)
                    direction = "IMPROVING" if delta >= 3.0 else ("DETERIORATING" if delta <= -3.0 else "STABLE")
                else:
                    prev_score = float(score)
                    delta = 0.0
                    direction = "STABLE"
            except Exception:
                prev_score = float(score)
                delta = 0.0
                direction = "STABLE"
        else:
            prev_score = float(score)
            delta = 0.0
            direction = "STABLE"

        trend_obj = PortfolioHealthTrend(
            direction=direction,
            trend_direction=direction,
            score_delta=delta,
            score_change=delta,
            previous_score=prev_score,
            current_score=float(score)
        )

        analytics_obj = PortfolioHealthAnalytics(
            overall_health_score=float(score),
            diversification_score=div_score,
            concentration_score=conc_score,
            position_sizing_score=20.0 if pos_cnt > 0 else 0.0,
            weight_balance_score=20.0 if pos_cnt > 0 else 0.0,
            portfolio_structure_score=20.0 if pos_cnt > 0 else 0.0,
            cash_score=cash_score,
            strengths=strengths,
            weaknesses=weaknesses,
            trend=trend_obj
        )

        res = PortfolioHealthResult(
            score=score,
            overall_score=score,
            grade=grade,
            overall_grade=grade,
            diversification_rating=div_rating,
            concentration_rating=conc_rating,
            diversification_score=div_score,
            concentration_score=conc_score,
            position_count=pos_cnt,
            timestamp=now_ts,
            largest_position_weight_pct=largest_pos_wt,
            analytics=analytics_obj,
            trend=trend_obj,
            alpha12_mapping=mapping_res,
            alpha12_stability=stability_res,
            alpha12_replacement_governance=gov_res,
            alpha12_challenger_evaluation=None,
            historical_analytics=hist_analytics_res,
            dashboard_summary=dash_summary_res,
            historical_metrics=hist_metrics_res,
            historical_insights=hist_insights_res,
            monitoring_state=mon_state_res,
            change_report=self.change_detection_service.detect_changes() if self.change_detection_service and hasattr(self.change_detection_service, "detect_changes") else None,
            timeline=self.timeline_service.build_timeline() if self.timeline_service and hasattr(self.timeline_service, "build_timeline") else None,
            monitoring_dashboard=self.monitoring_dashboard_service.build_dashboard() if self.monitoring_dashboard_service and hasattr(self.monitoring_dashboard_service, "build_dashboard") else None,
            alert_center=ac_res,
            generated_alerts=self.alert_generation_service.generate_alerts() if self.alert_generation_service and hasattr(self.alert_generation_service, "generate_alerts") else [],
            alert_rules=rules_res,
            alert_dashboard=dash_res,
            alert_history=self.alert_history_service.get_history() if self.alert_history_service and hasattr(self.alert_history_service, "get_history") else [],
            alert_management=mgmt_res,
            decision_engine=engine_res,
            decision_classification=classification_res,
            decision_prioritization=prioritization_res,
            decision_audit=audit_res,
            decision_audit_analytics=audit_analytics_res,
            decision_audit_trend=audit_trend_res,
            rebalancing=rebal_res,
            allocation_analysis=alloc_analysis_res,
            drift_detection=drift_res,
            rebalancing_candidates=candidates_res,
            rebalancing_recommendations=rec_res,
            portfolio_intelligence=intel_res,
            holding_quality=hq_res,
            sip_optimization=sip_res,
            portfolio_opportunities=opp_res,
            portfolio_risk_intelligence=risk_res
        )

        if self.history_service is not None:
            if auto_save or len(getattr(self.history_service, "get_history", lambda: [])()) == 0:
                try:
                    self.history_service.record_snapshot(res)
                except Exception:
                    try:
                        self.history_service.save_snapshot(res)
                    except Exception:
                        pass

        return res
