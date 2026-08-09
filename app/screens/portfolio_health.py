from typing import Any, Optional

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (

    QWidget,

    QVBoxLayout,

    QGridLayout,

    QLabel,

    QFrame,

    QScrollArea,

)

from services.alert_center_service import AlertCenterService

from services.alert_generation_service import AlertGenerationService

from services.alert_rules_service import AlertRulesService

from services.alert_dashboard_service import AlertDashboardService

from services.alert_history_service import AlertHistoryService

from services.alert_management_service import AlertManagementService

from services.decision_audit_service import DecisionAuditService

from services.decision_audit_analytics_service import DecisionAuditAnalyticsService

from services.decision_audit_trend_service import DecisionAuditTrendService

from services.rebalancing_service import RebalancingService

from services.allocation_analysis_service import AllocationAnalysisService

from services.drift_detection_service import DriftDetectionService

from services.rebalancing_candidate_service import RebalancingCandidateService

from services.rebalancing_recommendation_service import RebalancingRecommendationService
from services.portfolio_intelligence_service import PortfolioIntelligenceService
from services.holding_quality_service import HoldingQualityService
from services.sip_optimization_service import SIPOptimizationService
from services.portfolio_opportunity_service import PortfolioOpportunityService
from services.portfolio_risk_intelligence_service import PortfolioRiskIntelligenceService
from services.alpha12_mapping_service import Alpha12MappingService
from services.alpha12_stability_service import Alpha12StabilityService

from services.decision_classification_service import DecisionClassificationService

from services.decision_prioritization_service import DecisionPrioritizationService

from services.decision_engine_service import DecisionEngineService

from services.portfolio_health_change_detection_service import PortfolioHealthChangeDetectionService

from services.portfolio_health_history_service import PortfolioHealthHistoryService

from services.portfolio_health_monitor_dashboard_service import PortfolioHealthMonitoringDashboardService

from services.portfolio_health_monitor_service import PortfolioHealthMonitorService

from services.portfolio_health_service import (

    PortfolioHealthResult,

    PortfolioHealthService,

    PortfolioHealthSnapshot,

)

from services.portfolio_health_timeline_service import PortfolioHealthTimelineService

class PortfolioHealth(QWidget):

    def __init__(

        self,

        service: Optional[PortfolioHealthService] = None,

        history_service: Optional[PortfolioHealthHistoryService] = None,

        monitor_service: Optional[PortfolioHealthMonitorService] = None,

        change_detection_service: Optional[PortfolioHealthChangeDetectionService] = None,

        timeline_service: Optional[PortfolioHealthTimelineService] = None,

        monitoring_dashboard_service: Optional[PortfolioHealthMonitoringDashboardService] = None,

        alert_center_service: Optional[AlertCenterService] = None,

        alert_generation_service: Optional[AlertGenerationService] = None,

        alert_rules_service: Optional[AlertRulesService] = None,

        alert_dashboard_service: Optional[AlertDashboardService] = None,

        alert_history_service: Optional[AlertHistoryService] = None,

        alert_management_service: Optional[AlertManagementService] = None,

        decision_engine_service: Optional[DecisionEngineService] = None,

        decision_classification_service: Optional[DecisionClassificationService] = None,

        decision_prioritization_service: Optional[DecisionPrioritizationService] = None,

        decision_audit_service: Optional[DecisionAuditService] = None,

        decision_audit_analytics_service: Optional[DecisionAuditAnalyticsService] = None,

        decision_audit_trend_service: Optional[DecisionAuditTrendService] = None,

        rebalancing_service: Optional[RebalancingService] = None,

        allocation_analysis_service: Optional[AllocationAnalysisService] = None,

        drift_detection_service: Optional[DriftDetectionService] = None,

        rebalancing_candidate_service: Optional[RebalancingCandidateService] = None,

        rebalancing_recommendation_service: Optional[RebalancingRecommendationService] = None,

        portfolio_intelligence_service: Optional[PortfolioIntelligenceService] = None,
        holding_quality_service: Optional[HoldingQualityService] = None,
        sip_optimization_service: Optional[SIPOptimizationService] = None,
        portfolio_opportunity_service: Optional[PortfolioOpportunityService] = None,
        portfolio_risk_intelligence_service: Optional[PortfolioRiskIntelligenceService] = None,
        alpha12_mapping_service: Optional[Alpha12MappingService] = None,
        alpha12_stability_service: Optional[Alpha12StabilityService] = None,
        parent: Optional[QWidget] = None,

    ) -> None:

        super().__init__(parent)

        self.history_service = history_service if history_service is not None else PortfolioHealthHistoryService()

        self.monitor_service = monitor_service if monitor_service is not None else PortfolioHealthMonitorService(history_service=self.history_service)

        self.change_detection_service = change_detection_service if change_detection_service is not None else PortfolioHealthChangeDetectionService(history_service=self.history_service)

        self.timeline_service = timeline_service if timeline_service is not None else PortfolioHealthTimelineService(

            history_service=self.history_service,

            change_detection_service=self.change_detection_service,

        )

        self.monitoring_dashboard_service = monitoring_dashboard_service if monitoring_dashboard_service is not None else PortfolioHealthMonitoringDashboardService(

            history_service=self.history_service,

            monitor_service=self.monitor_service,

            change_detection_service=self.change_detection_service,

            timeline_service=self.timeline_service,

        )

        self.alert_center_service = alert_center_service if alert_center_service is not None else AlertCenterService()

        self.alert_generation_service = alert_generation_service if alert_generation_service is not None else AlertGenerationService(

            history_service=self.history_service,

            monitor_service=self.monitor_service,

            change_detection_service=self.change_detection_service,

            timeline_service=self.timeline_service,

            dashboard_service=self.monitoring_dashboard_service,

        )

        self.alert_rules_service = alert_rules_service if alert_rules_service is not None else AlertRulesService()

        self.alert_dashboard_service = alert_dashboard_service if alert_dashboard_service is not None else AlertDashboardService(

            alert_center_service=self.alert_center_service,

            alert_generation_service=self.alert_generation_service,

            alert_rules_service=self.alert_rules_service,

        )

        self.alert_history_service = alert_history_service if alert_history_service is not None else AlertHistoryService()

        self.alert_management_service = alert_management_service if alert_management_service is not None else AlertManagementService(

            alert_center_service=self.alert_center_service,

            alert_history_service=self.alert_history_service,

            alert_dashboard_service=self.alert_dashboard_service,

        )

        self.decision_engine_service = decision_engine_service if decision_engine_service is not None else DecisionEngineService()

        self.decision_classification_service = decision_classification_service if decision_classification_service is not None else DecisionClassificationService()

        self.decision_prioritization_service = decision_prioritization_service if decision_prioritization_service is not None else DecisionPrioritizationService()

        self.decision_audit_service = decision_audit_service if decision_audit_service is not None else DecisionAuditService()

        self.decision_audit_analytics_service = decision_audit_analytics_service if decision_audit_analytics_service is not None else DecisionAuditAnalyticsService(audit_service=self.decision_audit_service)

        self.decision_audit_trend_service = decision_audit_trend_service if decision_audit_trend_service is not None else DecisionAuditTrendService(audit_service=self.decision_audit_service)

        self.rebalancing_service = rebalancing_service if rebalancing_service is not None else RebalancingService()

        self.allocation_analysis_service = allocation_analysis_service if allocation_analysis_service is not None else AllocationAnalysisService(rebalancing_service=self.rebalancing_service)

        self.drift_detection_service = drift_detection_service if drift_detection_service is not None else DriftDetectionService(rebalancing_service=self.rebalancing_service, allocation_analysis_service=self.allocation_analysis_service)

        self.rebalancing_candidate_service = rebalancing_candidate_service if rebalancing_candidate_service is not None else RebalancingCandidateService(rebalancing_service=self.rebalancing_service, allocation_analysis_service=self.allocation_analysis_service, drift_detection_service=self.drift_detection_service)

        self.rebalancing_recommendation_service = rebalancing_recommendation_service if rebalancing_recommendation_service is not None else RebalancingRecommendationService(rebalancing_service=self.rebalancing_service, allocation_analysis_service=self.allocation_analysis_service, drift_detection_service=self.drift_detection_service, rebalancing_candidate_service=self.rebalancing_candidate_service, audit_service=decision_audit_service)

        self.portfolio_intelligence_service = portfolio_intelligence_service if portfolio_intelligence_service is not None else PortfolioIntelligenceService()
        self.holding_quality_service = holding_quality_service if holding_quality_service is not None else HoldingQualityService()
        self.sip_optimization_service = sip_optimization_service if sip_optimization_service is not None else SIPOptimizationService()
        self.portfolio_opportunity_service = portfolio_opportunity_service if portfolio_opportunity_service is not None else PortfolioOpportunityService()
        self.portfolio_risk_intelligence_service = portfolio_risk_intelligence_service if portfolio_risk_intelligence_service is not None else PortfolioRiskIntelligenceService()
        self.alpha12_mapping_service = alpha12_mapping_service if alpha12_mapping_service is not None else Alpha12MappingService()
        self.alpha12_stability_service = alpha12_stability_service if alpha12_stability_service is not None else Alpha12StabilityService()

        self.service = service if service is not None else PortfolioHealthService(

            history_service=self.history_service,

            monitor_service=self.monitor_service,

            change_detection_service=self.change_detection_service,

            timeline_service=self.timeline_service,

            monitoring_dashboard_service=self.monitoring_dashboard_service,

            alert_center_service=self.alert_center_service,

            alert_generation_service=self.alert_generation_service,

            alert_rules_service=self.alert_rules_service,

            alert_dashboard_service=self.alert_dashboard_service,

            alert_history_service=self.alert_history_service,

            alert_management_service=self.alert_management_service,

            decision_engine_service=self.decision_engine_service,

            decision_classification_service=self.decision_classification_service,

            decision_prioritization_service=self.decision_prioritization_service,

            decision_audit_service=self.decision_audit_service,

            decision_audit_analytics_service=self.decision_audit_analytics_service,

            decision_audit_trend_service=self.decision_audit_trend_service,

            rebalancing_service=self.rebalancing_service,

            allocation_analysis_service=self.allocation_analysis_service,

            drift_detection_service=self.drift_detection_service,

            rebalancing_candidate_service=self.rebalancing_candidate_service,

            rebalancing_recommendation_service=self.rebalancing_recommendation_service,

            portfolio_intelligence_service=self.portfolio_intelligence_service,

            holding_quality_service=self.holding_quality_service,

            sip_optimization_service=self.sip_optimization_service,

            portfolio_opportunity_service=self.portfolio_opportunity_service,

            portfolio_risk_intelligence_service=self.portfolio_risk_intelligence_service,

            alpha12_mapping_service=self.alpha12_mapping_service,
            alpha12_stability_service=self.alpha12_stability_service,

        )

        self._build_ui()

        self.refresh_data()

    def refresh_data(self) -> None:

        """Fetch and bind live portfolio health snapshot, evaluation, and history data."""

        if self.service is not None:

            snapshot = None

            if hasattr(self.service, "build_snapshot"):

                try:

                    snapshot = self.service.build_snapshot()

                    self.load_snapshot(snapshot)

                except Exception:

                    pass

            if hasattr(self.service, "evaluate"):

                try:

                    result = self.service.evaluate(snapshot)

                    self.load_result(result)

                except Exception:

                    pass

        self.load_history()

        self.load_monitoring()

        self.load_change_detection()

        self.load_timeline()

        self.load_monitoring_dashboard()

        self.load_alert_center()

        self.load_generated_alerts()

        self.load_alert_rules()

        self.load_alert_dashboard()

        self.load_alert_history()

        self.load_alert_management()

        self.load_decision_engine()

        self.load_decision_classification()

        self.load_decision_prioritization()

        self.load_decision_audit()

        self.load_decision_audit_analytics()

        self.load_decision_audit_trend()

        self.load_rebalancing()

        self.load_allocation_analysis()

        self.load_drift_detection()

        self.load_rebalancing_candidates()

        self.load_rebalancing_recommendations()

        self.load_portfolio_intelligence()

        self.load_holding_quality()

        self.load_sip_optimization()

        self.load_portfolio_opportunities()

        self.load_portfolio_risk_intelligence()

        self.load_alpha12_mapping()
        self.load_alpha12_stability()

    def load_decision_prioritization(self) -> None:

        """Bind live decision prioritization result to UI."""

        if getattr(self, "decision_prioritization_service", None) is None:

            return

        try:

            res = self.decision_prioritization_service.prioritize()

            self._update_decision_prioritization_ui(res)

        except Exception:

            pass

    def _update_decision_prioritization_ui(self, result: Any) -> None:

        if result is None:

            return

        if hasattr(self, "lbl_dp_total"):

            self.lbl_dp_total.setText(f"Total Prioritized: {getattr(result, 'total_prioritized', 0)}")

        if hasattr(self, "lbl_dp_critical"):

            self.lbl_dp_critical.setText(f"Critical: {getattr(result, 'critical_count', 0)}")

        if hasattr(self, "lbl_dp_high"):

            self.lbl_dp_high.setText(f"High: {getattr(result, 'high_count', 0)}")

        if hasattr(self, "lbl_dp_medium"):

            self.lbl_dp_medium.setText(f"Medium: {getattr(result, 'medium_count', 0)}")

        if hasattr(self, "lbl_dp_low"):

            self.lbl_dp_low.setText(f"Low: {getattr(result, 'low_count', 0)}")

        if hasattr(self, "lbl_dp_info"):

            self.lbl_dp_info.setText(f"Info: {getattr(result, 'info_count', 0)}")

        if hasattr(self, "decision_prioritization_list_container"):

            self._clear_layout(self.decision_prioritization_list_container)

            priorities = getattr(result, "priorities", [])

            if priorities:

                for item in priorities:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    d_id = getattr(item, "decision_id", "")

                    cat = getattr(item, "category", "")

                    prio = getattr(item, "priority", "")

                    desc = getattr(item, "description", "")

                    id_lbl = QLabel(f"Decision ID: {d_id}")

                    id_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    cat_lbl = QLabel(f"Category: {cat}")

                    cat_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    prio_color = "#dc2626" if prio in ["CRITICAL", "HIGH"] else "#d97706" if prio == "MEDIUM" else "#16a34a" if prio == "LOW" else "#2563eb"

                    prio_lbl = QLabel(f"Priority: {prio}")

                    prio_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {prio_color};")

                    desc_lbl = QLabel(f"Description: {desc}")

                    desc_lbl.setStyleSheet("font-size: 14px; color: #1e293b;")

                    lyt.addWidget(id_lbl)

                    lyt.addWidget(cat_lbl)

                    lyt.addWidget(prio_lbl)

                    lyt.addWidget(desc_lbl)

                    self.decision_prioritization_list_container.addWidget(card)

            else:

                lbl = QLabel("No prioritized decisions available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.decision_prioritization_list_container.addWidget(lbl)

    def load_rebalancing_recommendations(self) -> None:

        """Bind live rebalancing recommendations to UI."""

        if getattr(self, "rebalancing_recommendation_service", None) is None:

            return

        try:

            res = self.rebalancing_recommendation_service.get_recommendations()

            self._update_rebalancing_recommendations_ui(res)

        except Exception:

            pass

    def _update_rebalancing_recommendations_ui(self, result: Any) -> None:

        if result is None:

            return

        tot_rec = getattr(result, "total_recommendations", 0) or 0

        inc_c = getattr(result, "increase_count", 0) or 0

        dec_c = getattr(result, "decrease_count", 0) or 0

        maint_c = getattr(result, "maintain_count", 0) or 0

        high_c = getattr(result, "high_priority_count", 0) or 0

        med_c = getattr(result, "medium_priority_count", 0) or 0

        low_c = getattr(result, "low_priority_count", 0) or 0

        tot_impact = getattr(result, "total_impact_value", 0.0) or 0.0

        if hasattr(self, "lbl_rr_total_recommendations"):

            self.lbl_rr_total_recommendations.setText(f"Total Recommendations: {tot_rec}")

        if hasattr(self, "lbl_rr_increase_count"):

            self.lbl_rr_increase_count.setText(f"Increase: {inc_c}")

        if hasattr(self, "lbl_rr_decrease_count"):

            self.lbl_rr_decrease_count.setText(f"Decrease: {dec_c}")

        if hasattr(self, "lbl_rr_maintain_count"):

            self.lbl_rr_maintain_count.setText(f"Maintain: {maint_c}")

        if hasattr(self, "lbl_rr_high_priority_count"):

            self.lbl_rr_high_priority_count.setText(f"High Priority: {high_c}")

        if hasattr(self, "lbl_rr_medium_priority_count"):

            self.lbl_rr_medium_priority_count.setText(f"Medium Priority: {med_c}")

        if hasattr(self, "lbl_rr_low_priority_count"):

            self.lbl_rr_low_priority_count.setText(f"Low Priority: {low_c}")

        if hasattr(self, "lbl_rr_total_impact_val"):

            self.lbl_rr_total_impact_val.setText(f"Total Impact Value: ${tot_impact:,.2f}")

        if hasattr(self, "rebalancing_recommendations_container"):

            self._clear_layout(self.rebalancing_recommendations_container)

            recs = getattr(result, "recommendations", []) or []

            if recs:

                for r in recs:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    rec_id = getattr(r, "recommendation_id", "")

                    sym = getattr(r, "symbol", "")

                    nm = getattr(r, "name", "")

                    atype = getattr(r, "asset_type", "")

                    c_wt = getattr(r, "current_weight", 0.0)

                    t_wt = getattr(r, "target_weight", 0.0)

                    drift = getattr(r, "drift", 0.0)

                    action = getattr(r, "recommended_action", "MAINTAIN")

                    rec_wt = getattr(r, "recommended_weight", 0.0)

                    wt_chg = getattr(r, "weight_change", 0.0)

                    prio = getattr(r, "priority", "LOW")

                    score = getattr(r, "candidate_score", 0.0)

                    rank = getattr(r, "candidate_rank", 0)

                    rationale = getattr(r, "rationale", "")

                    hdr_lbl = QLabel(f"[{prio}] Action: {action} — {sym} ({nm}) [{atype}]")

                    hdr_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")

                    det_lbl = QLabel(f"Current: {c_wt:.2f}% → Target/Rec: {rec_wt:.2f}% (Change: {wt_chg:+.2f}%, Drift: {drift:+.2f}%)")

                    det_lbl.setStyleSheet("font-size: 13px; color: #334155;")

                    meta_lbl = QLabel(f"Rec ID: {rec_id} | Priority: {prio} | Candidate Score: {score:.2f} (Rank #{rank})")

                    meta_lbl.setStyleSheet("font-size: 12px; color: #475569;")

                    rat_lbl = QLabel(f"Rationale: {rationale}")

                    rat_lbl.setStyleSheet("font-size: 13px; color: #1e293b; font-style: italic; padding-top: 2px;")

                    lyt.addWidget(hdr_lbl)

                    lyt.addWidget(det_lbl)

                    lyt.addWidget(meta_lbl)

                    lyt.addWidget(rat_lbl)

                    self.rebalancing_recommendations_container.addWidget(card)

            else:

                lbl = QLabel("No rebalancing recommendations available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.rebalancing_recommendations_container.addWidget(lbl)

    def load_portfolio_intelligence(self) -> None:

        """Bind live portfolio intelligence data to UI."""

        if getattr(self, "portfolio_intelligence_service", None) is None:

            return

        try:

            res = self.portfolio_intelligence_service.get_intelligence()

            self._update_portfolio_intelligence_ui(res)

        except Exception:

            pass

    def _update_portfolio_intelligence_ui(self, result: Any) -> None:

        if hasattr(self, "portfolio_intelligence_container"):

            self._clear_layout(self.portfolio_intelligence_container)

            if result is None or getattr(result, "summary", None) is None:

                lbl = QLabel("No portfolio intelligence data available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.portfolio_intelligence_container.addWidget(lbl)

            else:

                summary = getattr(result, "summary")

                total_holdings = getattr(summary, "total_holdings", getattr(summary, "holding_count", 0))

                val_lbl = QLabel(f"Portfolio Value: ${summary.total_value:,.2f} | Holdings: {total_holdings} | Accounts: {summary.account_count}")

                val_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")

                self.portfolio_intelligence_container.addWidget(val_lbl)

                snapshots = getattr(result, "snapshots", getattr(result, "history", []))

                if snapshots:

                    hist_lbl = QLabel(f"Historical Snapshots Recorded: {len(snapshots)}")

                    hist_lbl.setStyleSheet("font-size: 13px; color: #475569; margin-top: 4px;")

                    self.portfolio_intelligence_container.addWidget(hist_lbl)

                else:

                    empty_hist = QLabel("No historical snapshots recorded yet.")

                    empty_hist.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic; margin-top: 4px;")

                    self.portfolio_intelligence_container.addWidget(empty_hist)

    def load_holding_quality(self) -> None:

        """Bind live holding quality assessment data to UI."""

        if getattr(self, "holding_quality_service", None) is None:

            return

        try:

            res = self.holding_quality_service.get_quality()

            self._update_holding_quality_ui(res)

        except Exception:

            pass

    def _update_holding_quality_ui(self, result: Any) -> None:

        if hasattr(self, "holding_quality_container"):

            self._clear_layout(self.holding_quality_container)

            if result is None or getattr(result, "total_holdings", 0) == 0:

                lbl = QLabel("No holding quality data available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.holding_quality_container.addWidget(lbl)

            else:

                tot = getattr(result, "total_holdings", 0)

                assessed = getattr(result, "assessed_holdings", 0)

                unassessed = getattr(result, "unassessed_holdings", 0)

                avg_score = getattr(result, "average_quality_score", 0.0)

                hi_score = getattr(result, "highest_quality_score", 0.0)

                lo_score = getattr(result, "lowest_quality_score", 0.0)

                summary_str = (

                    f"Total Holdings: {tot} | Assessed Holdings: {assessed} | Unassessed Holdings: {unassessed}\n"

                    f"Average Quality Score: {avg_score:.1f} | Highest Quality Score: {hi_score:.1f} | Lowest Quality Score: {lo_score:.1f}"

                )

                summ_lbl = QLabel(summary_str)

                summ_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 8px;")

                self.holding_quality_container.addWidget(summ_lbl)

                holdings = getattr(result, "holdings", [])

                if holdings:

                    scroll_area = QScrollArea()

                    scroll_area.setWidgetResizable(True)

                    scroll_area.setMaximumHeight(300)

                    scroll_widget = QWidget()

                    list_layout = QVBoxLayout(scroll_widget)

                    list_layout.setSpacing(6)

                    for h in holdings:

                        sym = getattr(h, "symbol", "N/A")

                        nm = getattr(h, "name", "N/A")

                        atype = getattr(h, "asset_type", "N/A")

                        score = getattr(h, "quality_score", 0.0)

                        grade = getattr(h, "quality_grade", "N/A")

                        status = getattr(h, "assessment_status", "UNAVAILABLE")

                        rationale = getattr(h, "rationale", "")

                        h_text = f"• {sym} ({nm}) | Type: {atype} | Score: {score:.1f} | Grade: {grade} | Status: {status}"

                        if rationale:

                            h_text += f"\n  Rationale: {rationale}"

                        h_lbl = QLabel(h_text)

                        h_lbl.setStyleSheet("font-size: 12px; color: #334155; padding: 4px; background-color: #f8fafc; border-radius: 4px;")

                        list_layout.addWidget(h_lbl)

                    scroll_area.setWidget(scroll_widget)

                    self.holding_quality_container.addWidget(scroll_area)

    def load_sip_optimization(self) -> None:

        """Bind live SIP optimization analysis data to UI."""

        if getattr(self, "sip_optimization_service", None) is None:

            return

        try:

            res = self.sip_optimization_service.get_sip_analysis()

            self._update_sip_optimization_ui(res)

        except Exception:

            pass

    def _update_sip_optimization_ui(self, result: Any) -> None:

        if hasattr(self, "sip_optimization_container"):

            self._clear_layout(self.sip_optimization_container)

            if result is None or getattr(result, "analysis_status", "UNAVAILABLE") in ("UNAVAILABLE", "NO_DATA", "EMPTY"):

                rat = getattr(result, "rationale", "") if result is not None else ""

                msg = f"No SIP optimization data available. ({rat})" if rat else "No SIP optimization data available."

                lbl = QLabel(msg)

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.sip_optimization_container.addWidget(lbl)

            else:

                tot_pos = getattr(result, "total_positions", 0)

                tot_invested = getattr(result, "total_sip_invested", 0.0)

                tot_txns = getattr(result, "total_sip_transactions", 0)

                dist = getattr(result, "distribution", None)

                eff = getattr(result, "efficiency", None)

                cov_pct = getattr(dist, "sip_coverage_pct", 0.0) if dist else 0.0

                top_conc = getattr(dist, "sip_concentration_top_pct", 0.0) if dist else 0.0

                obs_summary = getattr(eff, "observation_summary", "") if eff else ""

                summary_str = (

                    f"Total Positions: {tot_pos} | SIP Invested Capital: ₹{tot_invested:,.2f} | SIP Transactions: {tot_txns}\n"

                    f"SIP Coverage: {cov_pct:.1f}% | Top Recipient Concentration: {top_conc:.1f}%"

                )

                if obs_summary:

                    summary_str += f"\nObservation: {obs_summary}"

                summ_lbl = QLabel(summary_str)

                summ_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 8px;")

                self.sip_optimization_container.addWidget(summ_lbl)

                holdings = getattr(result, "holdings", [])

                if holdings:

                    scroll_area = QScrollArea()

                    scroll_area.setWidgetResizable(True)

                    scroll_area.setMaximumHeight(300)

                    scroll_widget = QWidget()

                    list_layout = QVBoxLayout(scroll_widget)

                    list_layout.setSpacing(6)

                    for h in holdings:

                        sym = getattr(h, "symbol", "N/A")

                        nm = getattr(h, "name", "N/A")

                        target_w = getattr(h, "target_weight", 0.0)

                        actual_w = getattr(h, "actual_weight", 0.0)

                        drift = getattr(h, "drift_pct", 0.0)

                        tx_cnt = getattr(h, "sip_transaction_count", 0)

                        tx_amt = getattr(h, "sip_invested_amount", 0.0)

                        sched_amt = getattr(h, "sip_amount_per_schedule", "UNAVAILABLE")

                        freq = getattr(h, "sip_frequency", "UNAVAILABLE")

                        h_text = (

                            f"• {sym} ({nm}) | Target: {target_w:.1f}% | Actual: {actual_w:.1f}% | Drift: {drift:+.1f}%\n"

                            f"  SIP Tx Count: {tx_cnt} | SIP Invested: ₹{tx_amt:,.2f} | Schedule Amount: {sched_amt} | Frequency: {freq}"

                        )

                        h_lbl = QLabel(h_text)

                        h_lbl.setStyleSheet("font-size: 12px; color: #334155; padding: 4px; background-color: #f8fafc; border-radius: 4px;")

                        list_layout.addWidget(h_lbl)

                    scroll_area.setWidget(scroll_widget)

                    self.sip_optimization_container.addWidget(scroll_area)

    def load_portfolio_opportunities(self) -> None:

        """Bind live portfolio opportunity analysis data to UI."""

        if getattr(self, "portfolio_opportunity_service", None) is None:

            return

        try:

            res = self.portfolio_opportunity_service.get_opportunities()

            self._update_portfolio_opportunities_ui(res)

        except Exception:

            pass

    def _update_portfolio_opportunities_ui(self, result: Any) -> None:

        if hasattr(self, "portfolio_opportunity_container"):

            self._clear_layout(self.portfolio_opportunity_container)

            if result is None or getattr(result, "analysis_status", "UNAVAILABLE") in ("UNAVAILABLE", "NO_DATA", "EMPTY"):

                lbl = QLabel("No portfolio opportunities available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.portfolio_opportunity_container.addWidget(lbl)

            else:

                summary = getattr(result, "summary", None)

                tot = getattr(summary, "total_opportunities", 0) if summary else 0

                hi = getattr(summary, "high_priority_count", 0) if summary else 0

                med = getattr(summary, "medium_priority_count", 0) if summary else 0

                low = getattr(summary, "low_priority_count", 0) if summary else 0

                assessed = getattr(summary, "assessed_count", 0) if summary else 0

                unavail = getattr(summary, "unavailable_count", 0) if summary else 0

                avg_score = getattr(summary, "average_opportunity_score", 0.0) if summary else 0.0

                hi_score = getattr(summary, "highest_opportunity_score", 0.0) if summary else 0.0

                status = getattr(result, "analysis_status", "UNAVAILABLE")

                summary_str = (

                    f"Status: {status} | Total Opportunities: {tot} | High: {hi} | Medium: {med} | Low: {low}\n"

                    f"Assessed: {assessed} | Unavailable: {unavail} | Average Score: {avg_score:.1f} | Highest Score: {hi_score:.1f}"

                )

                summ_lbl = QLabel(summary_str)

                summ_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 8px;")

                self.portfolio_opportunity_container.addWidget(summ_lbl)

                opportunities = getattr(result, "opportunities", [])

                if opportunities:

                    scroll_area = QScrollArea()

                    scroll_area.setWidgetResizable(True)

                    scroll_area.setMaximumHeight(300)

                    scroll_widget = QWidget()

                    list_layout = QVBoxLayout(scroll_widget)

                    list_layout.setSpacing(6)

                    for opp in opportunities:

                        opp_id = getattr(opp, "opportunity_id", "N/A")

                        sym = getattr(opp, "symbol", "N/A")

                        nm = getattr(opp, "name", "N/A")

                        atype = getattr(opp, "asset_type", "N/A")

                        op_type = getattr(opp, "opportunity_type", "N/A")

                        score = getattr(opp, "opportunity_score", 0.0)

                        priority = getattr(opp, "priority", "LOW")

                        op_status = getattr(opp, "opportunity_status", "UNAVAILABLE")

                        rat = getattr(opp, "rationale", "")

                        src = getattr(opp, "source", "")

                        ev_list = getattr(opp, "evidence", [])

                        ev_str = " | ".join(ev_list) if isinstance(ev_list, list) else str(ev_list)

                        opp_text = (

                            f"• [{opp_id}] {sym} ({nm}) | Type: {op_type} | Category: {atype}\n"

                            f"  Score: {score:.1f}/100 | Priority: {priority} | Status: {op_status} | Source: {src}\n"

                            f"  Rationale: {rat}"

                        )

                        if ev_str:

                            opp_text += f"\n  Evidence: {ev_str}"

                        opp_lbl = QLabel(opp_text)

                        opp_lbl.setStyleSheet("font-size: 12px; color: #334155; padding: 6px; background-color: #f8fafc; border-radius: 4px;")

                        list_layout.addWidget(opp_lbl)

                    scroll_area.setWidget(scroll_widget)

                    self.portfolio_opportunity_container.addWidget(scroll_area)

                else:

                    empty_lbl = QLabel("No portfolio opportunities available.")

                    empty_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")

                    self.portfolio_opportunity_container.addWidget(empty_lbl)

    def load_portfolio_risk_intelligence(self) -> None:

        """Bind live portfolio risk intelligence data to UI."""

        if getattr(self, "portfolio_risk_intelligence_service", None) is None:

            return

        try:

            res = self.portfolio_risk_intelligence_service.get_risk()

            self._update_portfolio_risk_intelligence_ui(res)

        except Exception:

            pass

    def _update_portfolio_risk_intelligence_ui(self, result: Any) -> None:

        if hasattr(self, "portfolio_risk_container"):

            self._clear_layout(self.portfolio_risk_container)

            if result is None or getattr(result, "analysis_status", "UNAVAILABLE") in ("UNAVAILABLE", "NO_DATA", "EMPTY", "ERROR"):

                lbl = QLabel("No portfolio risk intelligence data available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.portfolio_risk_container.addWidget(lbl)

            else:

                summary = getattr(result, "summary", None)

                tot = getattr(summary, "total_assessments", 0) if summary else 0

                assessed = getattr(summary, "assessed_count", 0) if summary else 0

                unavail = getattr(summary, "unavailable_count", 0) if summary else 0

                hi_risk = getattr(summary, "high_risk_count", 0) if summary else 0

                med_risk = getattr(summary, "medium_risk_count", 0) if summary else 0

                low_risk = getattr(summary, "low_risk_count", 0) if summary else 0

                info_cnt = getattr(summary, "info_count", 0) if summary else 0

                avg_score = getattr(summary, "average_risk_score", 0.0) if summary else 0.0

                hi_score = getattr(summary, "highest_risk_score", 0.0) if summary else 0.0

                top_weight = getattr(summary, "largest_position_weight", 0.0) if summary else 0.0

                pos_cnt = getattr(summary, "position_count", 0) if summary else 0

                div_status = getattr(summary, "diversification_status", "UNAVAILABLE") if summary else "UNAVAILABLE"

                status = getattr(result, "analysis_status", "UNAVAILABLE")

                summary_str = (

                    f"Analysis Status: {status} | Total Assessments: {tot} | Assessed: {assessed} | Unavailable: {unavail}\n"

                    f"High Risk: {hi_risk} | Medium Risk: {med_risk} | Low Risk: {low_risk} | Info: {info_cnt}\n"

                    f"Average Risk Score: {avg_score:.1f} | Highest Risk Score: {hi_score:.1f} | Largest Weight: {top_weight:.1f}%\n"

                    f"Position Count: {pos_cnt} | Diversification Status: {div_status}"

                )

                summ_lbl = QLabel(summary_str)

                summ_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 8px;")

                self.portfolio_risk_container.addWidget(summ_lbl)

                assessments = getattr(result, "assessments", [])

                if assessments:

                    scroll_area = QScrollArea()

                    scroll_area.setWidgetResizable(True)

                    scroll_area.setMaximumHeight(280)

                    scroll_widget = QWidget()

                    list_layout = QVBoxLayout(scroll_widget)

                    list_layout.setSpacing(6)

                    for a in assessments:

                        r_id = getattr(a, "risk_id", "N/A")

                        sym = getattr(a, "symbol", "N/A")

                        nm = getattr(a, "name", "N/A")

                        atype = getattr(a, "asset_type", "N/A")

                        rtype = getattr(a, "risk_type", "N/A")

                        score = getattr(a, "risk_score", 0.0)

                        level = getattr(a, "risk_level", "UNAVAILABLE")

                        astatus = getattr(a, "assessment_status", "UNAVAILABLE")

                        c_w = getattr(a, "current_weight", 0.0)

                        t_w = getattr(a, "target_weight", 0.0)

                        drift = getattr(a, "drift", 0.0)

                        rat = getattr(a, "rationale", "")

                        src = getattr(a, "source", "")

                        ev_list = getattr(a, "evidence", [])

                        ev_str = " | ".join(ev_list) if isinstance(ev_list, list) else str(ev_list)

                        a_text = (

                            f"• [{r_id}] {sym} ({nm}) | Risk Type: {rtype} | Category: {atype}\n"

                            f"  Risk Score: {score:.1f}/100 | Risk Level: {level} | Status: {astatus} | Source: {src}\n"

                            f"  Current Weight: {c_w:.1f}% | Target Weight: {t_w:.1f}% | Drift: {drift:+.1f}%\n"

                            f"  Rationale: {rat}"

                        )

                        if ev_str:

                            a_text += f"\n  Evidence: {ev_str}"

                        a_lbl = QLabel(a_text)

                        a_lbl.setStyleSheet("font-size: 12px; color: #334155; padding: 6px; background-color: #f8fafc; border-radius: 4px;")

                        list_layout.addWidget(a_lbl)

                    scroll_area.setWidget(scroll_widget)

                    self.portfolio_risk_container.addWidget(scroll_area)

                # Risk History Subsection (Chronological: OLDEST -> NEWEST)

                hist_lbl = QLabel("PORTFOLIO RISK HISTORY (OLDEST → NEWEST)")

                hist_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #475569; margin-top: 10px; margin-bottom: 4px;")

                self.portfolio_risk_container.addWidget(hist_lbl)

                history = getattr(result, "history", None)

                entries = getattr(history, "entries", []) if history else []

                if entries:

                    h_summary_str = (

                        f"Total History Entries: {getattr(history, 'total_entries', len(entries))} | "

                        f"Earliest: {getattr(history, 'earliest_timestamp', 'N/A')} | "

                        f"Latest: {getattr(history, 'latest_timestamp', 'N/A')}"

                    )

                    h_sum_lbl = QLabel(h_summary_str)

                    h_sum_lbl.setStyleSheet("font-size: 12px; color: #475569; font-style: italic; margin-bottom: 4px;")

                    self.portfolio_risk_container.addWidget(h_sum_lbl)

                    h_scroll = QScrollArea()

                    h_scroll.setWidgetResizable(True)

                    h_scroll.setMaximumHeight(180)

                    h_widget = QWidget()

                    h_layout = QVBoxLayout(h_widget)

                    h_layout.setSpacing(4)

                    for entry in entries:

                        ts = getattr(entry, "timestamp", "N/A")

                        avg_s = getattr(entry, "average_risk_score", 0.0)

                        hi_s = getattr(entry, "highest_risk_score", 0.0)

                        h_cnt = getattr(entry, "high_risk_count", 0)

                        m_cnt = getattr(entry, "medium_risk_count", 0)

                        l_cnt = getattr(entry, "low_risk_count", 0)

                        p_cnt = getattr(entry, "position_count", 0)

                        w_top = getattr(entry, "largest_position_weight", 0.0)

                        entry_text = (

                            f"[{ts}] Avg Score: {avg_s:.1f} | Peak Score: {hi_s:.1f} | "

                            f"High Risk: {h_cnt} | Medium Risk: {m_cnt} | Low Risk: {l_cnt} | Positions: {p_cnt} | Top Weight: {w_top:.1f}%"

                        )

                        e_lbl = QLabel(entry_text)

                        e_lbl.setStyleSheet("font-size: 11px; color: #475569; padding: 3px; background-color: #f1f5f9; border-radius: 3px;")

                        h_layout.addWidget(e_lbl)

                    h_scroll.setWidget(h_widget)

                    self.portfolio_risk_container.addWidget(h_scroll)

                else:

                    no_h_lbl = QLabel("No portfolio risk history available.")

                    no_h_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-style: italic;")

                    self.portfolio_risk_container.addWidget(no_h_lbl)

    def load_alpha12_mapping(self) -> None:

        """Bind live Alpha 12 portfolio mapping result to UI."""

        if getattr(self, "alpha12_mapping_service", None) is None:

            return

        try:

            res = self.alpha12_mapping_service.get_mapping()

            self._update_alpha12_mapping_ui(res)

        except Exception:

            pass

    def _update_alpha12_mapping_ui(self, result: Any) -> None:

        if hasattr(self, "alpha12_mapping_container"):

            self._clear_layout(self.alpha12_mapping_container)

            if result is None or getattr(result, "analysis_status", "UNAVAILABLE") in ("UNAVAILABLE", "ERROR"):

                lbl = QLabel("Alpha 12 portfolio source is unavailable.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.alpha12_mapping_container.addWidget(lbl)

            elif getattr(result, "analysis_status", "UNAVAILABLE") == "NO_DATA":

                lbl = QLabel("No Alpha 12 portfolio mapping data available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.alpha12_mapping_container.addWidget(lbl)

            else:

                port = getattr(result, "portfolio", None)

                tot = getattr(port, "total_alpha12_holdings", 0) if port else 0

                mapped = getattr(port, "mapped_holdings", 0) if port else 0

                unmapped = getattr(port, "unmapped_holdings", 0) if port else 0

                coverage = getattr(port, "mapping_coverage_pct", 0.0) if port else 0.0

                m_status = getattr(port, "mapping_status", "UNAVAILABLE") if port else "UNAVAILABLE"

                a_status = getattr(result, "analysis_status", "UNAVAILABLE")

                ts = getattr(port, "latest_timestamp", None) or "N/A"

                summary_str = (

                    f"Mapping Status: {m_status} | Analysis Status: {a_status}\n"

                    f"Total Alpha 12 Holdings: {tot} | Mapped Holdings: {mapped} | Unmapped Holdings: {unmapped}\n"

                    f"Mapping Coverage: {coverage:.1f}% | Latest Snapshot: {ts}"

                )

                summ_lbl = QLabel(summary_str)

                summ_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 8px;")

                self.alpha12_mapping_container.addWidget(summ_lbl)

                holdings = getattr(port, "holdings", []) if port else []

                if holdings:

                    scroll_area = QScrollArea()

                    scroll_area.setWidgetResizable(True)

                    scroll_area.setMaximumHeight(280)

                    scroll_widget = QWidget()

                    list_layout = QVBoxLayout(scroll_widget)

                    list_layout.setSpacing(6)

                    for h in holdings:

                        sym = getattr(h, "symbol", "N/A")

                        nm = getattr(h, "name", "N/A")

                        rank = getattr(h, "alpha12_rank", None)

                        rank_str = f"#{rank}" if rank is not None else "Unranked"

                        a_w = getattr(h, "alpha12_weight", None)

                        a_w_str = f"{a_w:.2f}%" if a_w is not None else "N/A"

                        c_w = getattr(h, "current_weight", None)

                        c_w_str = f"{c_w:.2f}%" if c_w is not None else "N/A"

                        c_v = getattr(h, "current_value", None)

                        c_v_str = f"₹{c_v:,.2f}" if c_v is not None else "N/A"

                        atype = getattr(h, "asset_type", "EQUITY")

                        h_status = getattr(h, "mapping_status", "UNAVAILABLE")

                        rat = getattr(h, "rationale", "")

                        src = getattr(h, "source", "")

                        ev_list = getattr(h, "evidence", [])

                        ev_str = " | ".join(ev_list) if isinstance(ev_list, list) else str(ev_list)

                        h_text = (

                            f"• [{h_status}] {sym} ({nm}) | Rank: {rank_str} | Asset Type: {atype} | Source: {src}\n"

                            f"  Alpha 12 Weight: {a_w_str} | Current Weight: {c_w_str} | Current Value: {c_v_str}\n"

                            f"  Rationale: {rat}"

                        )

                        if ev_str:

                            h_text += f"\n  Evidence: {ev_str}"

                        h_lbl = QLabel(h_text)

                        h_lbl.setStyleSheet("font-size: 12px; color: #334155; padding: 6px; background-color: #f8fafc; border-radius: 4px;")

                        list_layout.addWidget(h_lbl)

                    scroll_area.setWidget(scroll_widget)

                    self.alpha12_mapping_container.addWidget(scroll_area)

                else:

                    empty_h_lbl = QLabel("No Alpha 12 portfolio mapping data available.")

                    empty_h_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")

                    self.alpha12_mapping_container.addWidget(empty_h_lbl)

    def load_alpha12_stability(self) -> None:
        """Bind live Alpha 12 portfolio stability analysis to UI."""
        if getattr(self, "alpha12_stability_service", None) is None:
            return
        try:
            res = self.alpha12_stability_service.get_stability()
            self._update_alpha12_stability_ui(res)
        except Exception:
            pass

    def _update_alpha12_stability_ui(self, result: Any) -> None:
        if hasattr(self, "alpha12_stability_container"):
            self._clear_layout(self.alpha12_stability_container)
            if result is None or getattr(result, "analysis_status", "UNAVAILABLE") in ("UNAVAILABLE", "ERROR", "INSUFFICIENT_EVIDENCE"):
                lbl = QLabel("No Alpha 12 stability data available.")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.alpha12_stability_container.addWidget(lbl)
            else:
                metrics = getattr(result, "stability_metrics", None)
                if metrics is None or getattr(metrics, "assessment_status", "UNAVAILABLE") in ("UNAVAILABLE", "INSUFFICIENT_EVIDENCE"):
                    lbl = QLabel("No Alpha 12 stability data available.")
                    lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                    self.alpha12_stability_container.addWidget(lbl)
                else:
                    score = getattr(metrics, "stability_score", 0.0)
                    rating = getattr(metrics, "stability_rating", "MODERATE")
                    turnover = getattr(metrics, "turnover_rate", 0.0)
                    prevention = getattr(metrics, "churn_prevention_ratio", 0.0)
                    swaps_prev = getattr(metrics, "unnecessary_swap_prevention", 0)
                    risk = getattr(metrics, "churn_risk", "LOW")
                    eff = getattr(metrics, "turnover_efficiency", 1.0)
                    tenure = getattr(metrics, "average_holding_tenure_months", 0.0)
                    pers_cnt = getattr(metrics, "persistence_count", 0)
                    status = getattr(metrics, "assessment_status", "STABLE")
                    rat = getattr(metrics, "rationale", "")

                    summary_str = (
                        f"Stability Status: {status} | Stability Rating: {rating} | Score: {score:.1f}/100\n"
                        f"Turnover Rate: {turnover:.1f}% | Churn Risk: {risk} | Churn Prevention Ratio: {prevention:.1f}%\n"
                        f"Unnecessary Swaps Prevented: {swaps_prev} | Turnover Efficiency Ratio: {eff:.2f}\n"
                        f"Average Holding Tenure: {tenure:.1f} months | Persistent Holdings: {pers_cnt}\n"
                        f"Rationale: {rat}"
                    )
                    summ_lbl = QLabel(summary_str)
                    summ_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 8px;")
                    self.alpha12_stability_container.addWidget(summ_lbl)

                    # Persistence History Section
                    hist = getattr(result, "persistence_history", None)
                    entries = getattr(hist, "entries", []) if hist else []
                    if entries:
                        hist_title = QLabel("STABILITY PERSISTENCE HISTORY")
                        hist_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155; margin-top: 6px;")
                        self.alpha12_stability_container.addWidget(hist_title)
                        for e in entries:
                            ts = getattr(e, "timestamp", "N/A")
                            e_score = getattr(e, "stability_score", 0.0)
                            e_rating = getattr(e, "stability_rating", "MODERATE")
                            e_turn = getattr(e, "turnover_rate", 0.0)
                            e_lbl = QLabel(f"• {ts} — Score: {e_score:.1f} ({e_rating}) | Turnover: {e_turn:.1f}%")
                            e_lbl.setStyleSheet("font-size: 12px; color: #475569; padding-left: 6px;")
                            self.alpha12_stability_container.addWidget(e_lbl)
                    else:
                        hist_lbl = QLabel("No Alpha 12 stability history available.")
                        hist_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
                        self.alpha12_stability_container.addWidget(hist_lbl)

    def load_rebalancing_candidates(self) -> None:

        """Bind live rebalancing candidate engine data to UI."""

        if getattr(self, "rebalancing_candidate_service", None) is None:

            return

        try:

            res = self.rebalancing_candidate_service.get_candidates()

            self._update_rebalancing_candidates_ui(res)

        except Exception:

            pass

    def _update_rebalancing_candidates_ui(self, result: Any) -> None:

        if result is None:

            return

        tot_cand = getattr(result, "total_candidates", 0) or 0

        ow_cand = getattr(result, "overweight_candidates", 0) or 0

        uw_cand = getattr(result, "underweight_candidates", 0) or 0

        ot_cand = getattr(result, "on_target_candidates", 0) or 0

        tot_impact = getattr(result, "total_impact_value", 0.0) or 0.0

        if hasattr(self, "lbl_rc_total_candidates"):

            self.lbl_rc_total_candidates.setText(f"Total Candidates: {tot_cand}")

        if hasattr(self, "lbl_rc_overweight_candidates"):

            self.lbl_rc_overweight_candidates.setText(f"Overweight Candidates: {ow_cand}")

        if hasattr(self, "lbl_rc_underweight_candidates"):

            self.lbl_rc_underweight_candidates.setText(f"Underweight Candidates: {uw_cand}")

        if hasattr(self, "lbl_rc_on_target_candidates"):

            self.lbl_rc_on_target_candidates.setText(f"On Target Candidates: {ot_cand}")

        if hasattr(self, "lbl_rc_total_impact_val"):

            self.lbl_rc_total_impact_val.setText(f"Total Impact Value: ${tot_impact:,.2f}")

        if hasattr(self, "rebalancing_candidates_container"):

            self._clear_layout(self.rebalancing_candidates_container)

            cands = getattr(result, "candidates", []) or []

            if cands:

                for c in cands:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    rank = getattr(c, "rank", 0)

                    sym = getattr(c, "symbol", "")

                    nm = getattr(c, "name", "")

                    atype = getattr(c, "asset_type", "")

                    c_wt = getattr(c, "current_weight", 0.0)

                    t_wt = getattr(c, "target_weight", 0.0)

                    drift = getattr(c, "drift", 0.0)

                    abs_drift = getattr(c, "absolute_drift", 0.0)

                    direction = getattr(c, "direction", "ON_TARGET")

                    impact = getattr(c, "impact_value", 0.0)

                    sc_wt = getattr(c, "scenario_weight", 0.0)

                    sc_dl = getattr(c, "scenario_delta", 0.0)

                    score = getattr(c, "candidate_score", 0.0)

                    title_lbl = QLabel(f"Rank #{rank}: {sym} - {nm} ({atype})")

                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")

                    wt_lbl = QLabel(f"Current: {c_wt:.2f}% | Target: {t_wt:.2f}% | Drift: {drift:+.2f}% (|Drift|: {abs_drift:.2f}%) [{direction}]")

                    wt_lbl.setStyleSheet("font-size: 13px; color: #1f2937;")

                    eval_lbl = QLabel(f"Impact Value: ${impact:,.2f} | Scenario Target: {sc_wt:.2f}% (Delta: {sc_dl:+.2f}%) | Candidate Score: {score:.2f}")

                    eval_lbl.setStyleSheet("font-size: 13px; color: #173b67; font-weight: 600;")

                    lyt.addWidget(title_lbl)

                    lyt.addWidget(wt_lbl)

                    lyt.addWidget(eval_lbl)

                    self.rebalancing_candidates_container.addWidget(card)

            else:

                lbl = QLabel("No rebalancing candidates available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.rebalancing_candidates_container.addWidget(lbl)

    def load_drift_detection(self) -> None:

        """Bind live drift detection and history to UI."""

        if getattr(self, "drift_detection_service", None) is None:

            return

        try:

            res = self.drift_detection_service.get_drift()

            hist = self.drift_detection_service.load_history()

            self._update_drift_detection_ui(res, hist)

        except Exception:

            pass

    def _update_drift_detection_ui(self, result: Any, history: Any = None) -> None:

        if result is None:

            return

        tot_pos = getattr(result, "total_positions", 0) or 0

        pos_wt = getattr(result, "positions_with_target", 0) or 0

        pos_wot = getattr(result, "positions_without_target", 0) or 0

        tot_drift = getattr(result, "total_absolute_drift", 0.0) or 0.0

        avg_drift = getattr(result, "average_absolute_drift", 0.0) or 0.0

        max_drift = getattr(result, "maximum_absolute_drift", 0.0) or 0.0

        if hasattr(self, "lbl_dd_total_pos"):

            self.lbl_dd_total_pos.setText(f"Total Positions: {tot_pos}")

        if hasattr(self, "lbl_dd_pos_with_target"):

            self.lbl_dd_pos_with_target.setText(f"Positions With Target: {pos_wt}")

        if hasattr(self, "lbl_dd_pos_without_target"):

            self.lbl_dd_pos_without_target.setText(f"Positions Without Target: {pos_wot}")

        if hasattr(self, "lbl_dd_total_abs_drift"):

            self.lbl_dd_total_abs_drift.setText(f"Total Absolute Drift: {tot_drift:.2f}%")

        if hasattr(self, "lbl_dd_avg_abs_drift"):

            self.lbl_dd_avg_abs_drift.setText(f"Average Absolute Drift: {avg_drift:.2f}%")

        if hasattr(self, "lbl_dd_max_abs_drift"):

            self.lbl_dd_max_abs_drift.setText(f"Maximum Absolute Drift: {max_drift:.2f}%")

        if hasattr(self, "drift_metrics_container"):

            self._clear_layout(self.drift_metrics_container)

            metrics = getattr(result, "metrics", []) or []

            if metrics:

                for m in metrics:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    nm = getattr(m, "name", "")

                    c_wt = getattr(m, "current_weight", 0.0)

                    t_wt = getattr(m, "target_weight", 0.0)

                    drift = getattr(m, "drift", 0.0)

                    abs_drift = getattr(m, "absolute_drift", 0.0)

                    direction = getattr(m, "direction", "ON_TARGET")

                    nm_lbl = QLabel(f"{nm}")

                    nm_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")

                    val_lbl = QLabel(f"Current: {c_wt:.2f}% | Target: {t_wt:.2f}% | Drift: {drift:+.2f}% (|Drift|: {abs_drift:.2f}%)")

                    val_lbl.setStyleSheet("font-size: 13px; color: #1f2937;")

                    dir_lbl = QLabel(f"Direction: {direction}")

                    dir_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #173b67;")

                    lyt.addWidget(nm_lbl)

                    lyt.addWidget(val_lbl)

                    lyt.addWidget(dir_lbl)

                    self.drift_metrics_container.addWidget(card)

            else:

                lbl = QLabel("No drift analysis available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.drift_metrics_container.addWidget(lbl)

        # Update History UI

        if history is not None and hasattr(self, "drift_history_container"):

            self._clear_layout(self.drift_history_container)

            tot_h = getattr(history, "total_entries", 0) or 0

            earliest = getattr(history, "earliest_timestamp", None) or "None"

            latest = getattr(history, "latest_timestamp", None) or "None"

            entries = getattr(history, "entries", []) or []

            if hasattr(self, "lbl_dh_total_entries"):

                self.lbl_dh_total_entries.setText(f"Total History Entries: {tot_h}")

            if hasattr(self, "lbl_dh_earliest"):

                self.lbl_dh_earliest.setText(f"Earliest Timestamp: {earliest}")

            if hasattr(self, "lbl_dh_latest"):

                self.lbl_dh_latest.setText(f"Latest Timestamp: {latest}")

            if entries:

                for e in entries:

                    ts = getattr(e, "timestamp", "")

                    tot_d = getattr(e, "total_absolute_drift", 0.0)

                    avg_d = getattr(e, "average_absolute_drift", 0.0)

                    max_d = getattr(e, "maximum_absolute_drift", 0.0)

                    lbl = QLabel(f"{ts} — Total |Drift|: {tot_d:.2f}% | Avg |Drift|: {avg_d:.2f}% | Max |Drift|: {max_d:.2f}%")

                    lbl.setStyleSheet("font-size: 12px; color: #475569; padding-left: 6px;")

                    self.drift_history_container.addWidget(lbl)

            else:

                lbl = QLabel("No drift history available.")

                lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")

                self.drift_history_container.addWidget(lbl)

    def load_allocation_analysis(self) -> None:

        """Bind live allocation analysis to UI."""

        if getattr(self, "allocation_analysis_service", None) is None:

            return

        try:

            res = self.allocation_analysis_service.get_analysis()

            self._update_allocation_analysis_ui(res)

        except Exception:

            pass

    def _update_allocation_analysis_ui(self, result: Any) -> None:

        if result is None:

            return

        total_val = getattr(result, "total_value", 0.0) or 0.0

        if hasattr(self, "lbl_aa_total_val"):

            self.lbl_aa_total_val.setText(f"Total Portfolio Value: ${total_val:,.2f}")

        if hasattr(self, "allocation_analysis_container"):

            self._clear_layout(self.allocation_analysis_container)

            asset_allocs = getattr(result, "asset_allocations", []) or []

            fund_allocs = getattr(result, "fund_allocations", []) or []

            etf_allocs = getattr(result, "etf_allocations", []) or []

            if not asset_allocs and not fund_allocs and not etf_allocs:

                lbl = QLabel("No allocation analysis available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.allocation_analysis_container.addWidget(lbl)

                return

            if asset_allocs:

                hdr = QLabel("ASSET ALLOCATION")

                hdr.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67; padding-top: 6px;")

                self.allocation_analysis_container.addWidget(hdr)

                for cat in asset_allocs:

                    nm = getattr(cat, "name", "")

                    val = getattr(cat, "current_value", 0.0)

                    wt = getattr(cat, "current_weight", 0.0)

                    cnt = getattr(cat, "position_count", 0)

                    lbl = QLabel(f"{nm}: ${val:,.2f} ({wt:.2f}%) — {cnt} position(s)")

                    lbl.setStyleSheet("font-size: 13px; color: #1f2937; padding-left: 8px;")

                    self.allocation_analysis_container.addWidget(lbl)

            if fund_allocs:

                hdr = QLabel("FUND ALLOCATION")

                hdr.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67; padding-top: 6px;")

                self.allocation_analysis_container.addWidget(hdr)

                for cat in fund_allocs:

                    nm = getattr(cat, "name", "")

                    val = getattr(cat, "current_value", 0.0)

                    wt = getattr(cat, "current_weight", 0.0)

                    cnt = getattr(cat, "position_count", 0)

                    lbl = QLabel(f"{nm}: ${val:,.2f} ({wt:.2f}%) — {cnt} position(s)")

                    lbl.setStyleSheet("font-size: 13px; color: #1f2937; padding-left: 8px;")

                    self.allocation_analysis_container.addWidget(lbl)

            if etf_allocs:

                hdr = QLabel("ETF ALLOCATION")

                hdr.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67; padding-top: 6px;")

                self.allocation_analysis_container.addWidget(hdr)

                for cat in etf_allocs:

                    nm = getattr(cat, "name", "")

                    val = getattr(cat, "current_value", 0.0)

                    wt = getattr(cat, "current_weight", 0.0)

                    cnt = getattr(cat, "position_count", 0)

                    lbl = QLabel(f"{nm}: ${val:,.2f} ({wt:.2f}%) — {cnt} position(s)")

                    lbl.setStyleSheet("font-size: 13px; color: #1f2937; padding-left: 8px;")

                    self.allocation_analysis_container.addWidget(lbl)

    def load_rebalancing(self) -> None:

        """Bind live rebalancing state to UI."""

        if getattr(self, "rebalancing_service", None) is None:

            return

        try:

            res = self.rebalancing_service.get_state()

            self._update_rebalancing_ui(res)

        except Exception:

            pass

    def _update_rebalancing_ui(self, result: Any) -> None:

        if result is None:

            return

        status = getattr(result, "status", "EMPTY") or "EMPTY"

        total_val = getattr(result, "total_value", 0.0) or 0.0

        total_pos = getattr(result, "total_positions", 0) or 0

        if hasattr(self, "lbl_reb_status"):

            self.lbl_reb_status.setText(f"Rebalancing Status: {status}")

        if hasattr(self, "lbl_reb_total_val"):

            self.lbl_reb_total_val.setText(f"Total Portfolio Value: ${total_val:,.2f}")

        if hasattr(self, "lbl_reb_total_pos"):

            self.lbl_reb_total_pos.setText(f"Total Positions: {total_pos}")

        if hasattr(self, "rebalancing_positions_container"):

            self._clear_layout(self.rebalancing_positions_container)

            portfolio = getattr(result, "portfolio", None)

            positions = getattr(portfolio, "positions", []) if portfolio else []

            if positions:

                for pos in positions:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    sym = getattr(pos, "symbol", "")

                    name = getattr(pos, "name", "")

                    atype = getattr(pos, "asset_type", "")

                    c_val = getattr(pos, "current_value", 0.0)

                    c_wt = getattr(pos, "current_weight", 0.0)

                    sym_lbl = QLabel(f"{sym} - {name}")

                    sym_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")

                    type_lbl = QLabel(f"Asset Type: {atype}")

                    type_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    val_lbl = QLabel(f"Current Value: ${c_val:,.2f} | Current Weight: {c_wt:.2f}%")

                    val_lbl.setStyleSheet("font-size: 13px; color: #1f2937;")

                    tgt_lbl = QLabel("Target Weight: Not configured")

                    tgt_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")

                    lyt.addWidget(sym_lbl)

                    lyt.addWidget(type_lbl)

                    lyt.addWidget(val_lbl)

                    lyt.addWidget(tgt_lbl)

                    self.rebalancing_positions_container.addWidget(card)

            else:

                lbl = QLabel("No rebalancing portfolio data available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.rebalancing_positions_container.addWidget(lbl)

    def load_decision_audit_trend(self) -> None:

        """Bind live decision audit trend to UI."""

        if getattr(self, "decision_audit_trend_service", None) is None:

            return

        try:

            res = self.decision_audit_trend_service.get_trend()

            self._update_decision_audit_trend_ui(res)

        except Exception:

            pass

    def _update_decision_audit_trend_ui(self, result: Any) -> None:

        if result is None:

            return

        total_points = getattr(result, "total_points", 0)

        earliest_ts = getattr(result, "earliest_timestamp", None) or "N/A"

        latest_ts = getattr(result, "latest_timestamp", None) or "N/A"

        direction = getattr(result, "direction", "STABLE")

        if hasattr(self, "lbl_dat_total_points"):

            self.lbl_dat_total_points.setText(f"Total Points: {total_points}")

        if hasattr(self, "lbl_dat_earliest"):

            self.lbl_dat_earliest.setText(f"Earliest Timestamp: {earliest_ts}")

        if hasattr(self, "lbl_dat_latest"):

            self.lbl_dat_latest.setText(f"Latest Timestamp: {latest_ts}")

        if hasattr(self, "lbl_dat_direction"):

            self.lbl_dat_direction.setText(f"Direction: {direction}")

        if hasattr(self, "decision_audit_trend_container"):

            self._clear_layout(self.decision_audit_trend_container)

            points = getattr(result, "points", [])

            if points:

                for pt in points:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    ts = getattr(pt, "timestamp", "")

                    total = getattr(pt, "total_entries", 0)

                    cls = getattr(pt, "classified_entries", 0)

                    uncls = getattr(pt, "unclassified_entries", 0)

                    crit = getattr(pt, "critical_priority_entries", 0)

                    high = getattr(pt, "high_priority_entries", 0)

                    med = getattr(pt, "medium_priority_entries", 0)

                    low = getattr(pt, "low_priority_entries", 0)

                    info = getattr(pt, "info_priority_entries", 0)

                    ts_lbl = QLabel(f"Timestamp: {ts}")

                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    total_lbl = QLabel(f"Total Entries: {total}")

                    total_lbl.setStyleSheet("font-size: 13px; color: #1f2937; font-weight: 600;")

                    cls_lbl = QLabel(f"Classified: {cls} | Unclassified: {uncls}")

                    cls_lbl.setStyleSheet("font-size: 13px; color: #475569;")

                    prio_lbl = QLabel(f"Critical: {crit} | High: {high} | Medium: {med} | Low: {low} | Info: {info}")

                    prio_lbl.setStyleSheet("font-size: 13px; color: #475569;")

                    lyt.addWidget(ts_lbl)

                    lyt.addWidget(total_lbl)

                    lyt.addWidget(cls_lbl)

                    lyt.addWidget(prio_lbl)

                    self.decision_audit_trend_container.addWidget(card)

            else:

                lbl = QLabel("No decision audit trend available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.decision_audit_trend_container.addWidget(lbl)

    def load_decision_audit_analytics(self) -> None:

        """Bind live decision audit analytics to UI."""

        if getattr(self, "decision_audit_analytics_service", None) is None:

            return

        try:

            res = self.decision_audit_analytics_service.get_analytics()

            self._update_decision_audit_analytics_ui(res)

        except Exception:

            pass

    def _update_decision_audit_analytics_ui(self, result: Any) -> None:

        if result is None:

            return

        summary = getattr(result, "summary", None)

        total_entries = getattr(summary, "total_entries", 0) if summary else 0

        if hasattr(self, "lbl_daa_total"):

            self.lbl_daa_total.setText(f"Total Entries: {total_entries}")

        if hasattr(self, "lbl_daa_unique"):

            self.lbl_daa_unique.setText(f"Unique Decisions: {getattr(summary, 'unique_decisions', 0) if summary else 0}")

        if hasattr(self, "lbl_daa_classified"):

            self.lbl_daa_classified.setText(f"Classified: {getattr(summary, 'classified_entries', 0) if summary else 0}")

        if hasattr(self, "lbl_daa_unclassified"):

            self.lbl_daa_unclassified.setText(f"Unclassified: {getattr(summary, 'unclassified_entries', 0) if summary else 0}")

        if hasattr(self, "lbl_daa_critical"):

            self.lbl_daa_critical.setText(f"Critical: {getattr(summary, 'critical_priority_entries', 0) if summary else 0}")

        if hasattr(self, "lbl_daa_high"):

            self.lbl_daa_high.setText(f"High: {getattr(summary, 'high_priority_entries', 0) if summary else 0}")

        if hasattr(self, "lbl_daa_medium"):

            self.lbl_daa_medium.setText(f"Medium: {getattr(summary, 'medium_priority_entries', 0) if summary else 0}")

        if hasattr(self, "lbl_daa_low"):

            self.lbl_daa_low.setText(f"Low: {getattr(summary, 'low_priority_entries', 0) if summary else 0}")

        if hasattr(self, "lbl_daa_info"):

            self.lbl_daa_info.setText(f"Info: {getattr(summary, 'info_priority_entries', 0) if summary else 0}")

        if hasattr(self, "decision_audit_analytics_container"):

            self._clear_layout(self.decision_audit_analytics_container)

            if not summary or total_entries == 0:

                lbl = QLabel("No decision audit analytics available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.decision_audit_analytics_container.addWidget(lbl)

                return

            cat_counts = getattr(result, "category_counts", {}) or {}

            prio_counts = getattr(result, "priority_counts", {}) or {}

            cls_counts = getattr(result, "classification_counts", {}) or {}

            if cat_counts:

                cat_hdr = QLabel("CATEGORY DISTRIBUTION")

                cat_hdr.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67; padding-top: 6px;")

                self.decision_audit_analytics_container.addWidget(cat_hdr)

                for cat_name, count in cat_counts.items():

                    lbl = QLabel(f"{cat_name} → {count}")

                    lbl.setStyleSheet("font-size: 13px; color: #1f2937; padding-left: 8px;")

                    self.decision_audit_analytics_container.addWidget(lbl)

            if prio_counts:

                prio_hdr = QLabel("PRIORITY DISTRIBUTION")

                prio_hdr.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67; padding-top: 6px;")

                self.decision_audit_analytics_container.addWidget(prio_hdr)

                prio_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

                displayed_prio = []

                for p in prio_order:

                    if p in prio_counts:

                        displayed_prio.append((p, prio_counts[p]))

                for p, count in prio_counts.items():

                    if p not in prio_order:

                        displayed_prio.append((p, count))

                for p_name, count in displayed_prio:

                    lbl = QLabel(f"{p_name}: {count}")

                    lbl.setStyleSheet("font-size: 13px; color: #1f2937; padding-left: 8px;")

                    self.decision_audit_analytics_container.addWidget(lbl)

            if cls_counts:

                cls_hdr = QLabel("CLASSIFICATION DISTRIBUTION")

                cls_hdr.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67; padding-top: 6px;")

                self.decision_audit_analytics_container.addWidget(cls_hdr)

                cls_order = ["CLASSIFIED", "UNCLASSIFIED"]

                displayed_cls = []

                for c in cls_order:

                    if c in cls_counts:

                        displayed_cls.append((c, cls_counts[c]))

                for c, count in cls_counts.items():

                    if c not in cls_order:

                        displayed_cls.append((c, count))

                for c_name, count in displayed_cls:

                    lbl = QLabel(f"{c_name}: {count}")

                    lbl.setStyleSheet("font-size: 13px; color: #1f2937; padding-left: 8px;")

                    self.decision_audit_analytics_container.addWidget(lbl)

    def load_decision_audit(self) -> None:

        """Bind live decision audit trail to UI."""

        if getattr(self, "decision_audit_service", None) is None:

            return

        try:

            res = self.decision_audit_service.get_audit_trail()

            self._update_decision_audit_ui(res)

        except Exception:

            pass

    def _update_decision_audit_ui(self, result: Any) -> None:

        if result is None:

            return

        if hasattr(self, "lbl_da_total"):

            self.lbl_da_total.setText(f"Total Entries: {getattr(result, 'total_entries', 0)}")

        if hasattr(self, "lbl_da_earliest"):

            val = getattr(result, "earliest_timestamp", None) or "N/A"

            self.lbl_da_earliest.setText(f"Earliest Entry: {val}")

        if hasattr(self, "lbl_da_latest"):

            val = getattr(result, "latest_timestamp", None) or "N/A"

            self.lbl_da_latest.setText(f"Latest Entry: {val}")

        if hasattr(self, "decision_audit_list_container"):

            self._clear_layout(self.decision_audit_list_container)

            entries = getattr(result, "entries", [])

            if entries:

                for entry in entries:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    ts = getattr(entry, "timestamp", "")

                    d_id = getattr(entry, "decision_id", "")

                    cat = getattr(entry, "category", "")

                    cls_status = getattr(entry, "classification_status", "")

                    prio = getattr(entry, "priority", "")

                    desc = getattr(entry, "description", "")

                    src = getattr(entry, "source", "")

                    ts_lbl = QLabel(f"Timestamp: {ts}")

                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    id_lbl = QLabel(f"Decision ID: {d_id}")

                    id_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    cat_lbl = QLabel(f"Category: {cat}")

                    cat_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    cls_lbl = QLabel(f"Classification Status: {cls_status}")

                    cls_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    prio_color = "#dc2626" if prio in ["CRITICAL", "HIGH"] else "#d97706" if prio == "MEDIUM" else "#16a34a" if prio == "LOW" else "#2563eb"

                    prio_lbl = QLabel(f"Priority: {prio}")

                    prio_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {prio_color};")

                    desc_lbl = QLabel(f"Description: {desc}")

                    desc_lbl.setStyleSheet("font-size: 14px; color: #1e293b;")

                    src_lbl = QLabel(f"Source: {src}")

                    src_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    lyt.addWidget(ts_lbl)

                    lyt.addWidget(id_lbl)

                    lyt.addWidget(cat_lbl)

                    lyt.addWidget(cls_lbl)

                    lyt.addWidget(prio_lbl)

                    lyt.addWidget(desc_lbl)

                    lyt.addWidget(src_lbl)

                    self.decision_audit_list_container.addWidget(card)

            else:

                lbl = QLabel("No decision audit entries available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.decision_audit_list_container.addWidget(lbl)

    def load_decision_classification(self) -> None:

        """Bind live decision classification result to UI."""

        if getattr(self, "decision_classification_service", None) is None:

            return

        try:

            res = self.decision_classification_service.classify()

            self._update_decision_classification_ui(res)

        except Exception:

            pass

    def _update_decision_classification_ui(self, result: Any) -> None:

        if result is None:

            return

        if hasattr(self, "lbl_dc_total"):

            self.lbl_dc_total.setText(f"Total Classifications: {getattr(result, 'total_classifications', 0)}")

        if hasattr(self, "lbl_dc_classified"):

            self.lbl_dc_classified.setText(f"Classified: {getattr(result, 'classified', 0)}")

        if hasattr(self, "lbl_dc_unclassified"):

            self.lbl_dc_unclassified.setText(f"Unclassified: {getattr(result, 'unclassified', 0)}")

        if hasattr(self, "decision_classification_list_container"):

            self._clear_layout(self.decision_classification_list_container)

            classifications = getattr(result, "classifications", [])

            if classifications:

                for item in classifications:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    lbl = QLabel(str(item))

                    lbl.setStyleSheet("font-size: 14px; color: #1e293b;")

                    lyt.addWidget(lbl)

                    self.decision_classification_list_container.addWidget(card)

            else:

                lbl = QLabel("No classifications available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.decision_classification_list_container.addWidget(lbl)

    def load_decision_engine(self) -> None:

        """Bind live decision engine result to UI."""

        if getattr(self, "decision_engine_service", None) is None:

            return

        try:

            res = self.decision_engine_service.evaluate()

            self._update_decision_engine_ui(res)

        except Exception:

            pass

    def _update_decision_engine_ui(self, result: Any) -> None:

        if result is None:

            return

        summary = getattr(result, "summary", None)

        if summary is not None:

            if hasattr(self, "lbl_de_status"):

                self.lbl_de_status.setText(f"Engine Status: {getattr(summary, 'engine_status', 'UNAVAILABLE')}")

            if hasattr(self, "lbl_de_total"):

                self.lbl_de_total.setText(f"Total Decisions: {getattr(summary, 'total_decisions', 0)}")

            if hasattr(self, "lbl_de_pending"):

                self.lbl_de_pending.setText(f"Pending Decisions: {getattr(summary, 'pending_decisions', 0)}")

            if hasattr(self, "lbl_de_informational"):

                self.lbl_de_informational.setText(f"Informational Decisions: {getattr(summary, 'informational_decisions', 0)}")

        if hasattr(self, "decision_engine_list_container"):

            self._clear_layout(self.decision_engine_list_container)

            decisions = getattr(result, "decisions", [])

            if decisions:

                for decision in decisions:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    lbl = QLabel(str(decision))

                    lbl.setStyleSheet("font-size: 14px; color: #1e293b;")

                    lyt.addWidget(lbl)

                    self.decision_engine_list_container.addWidget(card)

            else:

                lbl = QLabel("No decisions available.")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.decision_engine_list_container.addWidget(lbl)

    def load_alert_management(self) -> None:

        """Bind live alert management summary to UI."""

        if getattr(self, "alert_management_service", None) is None:

            return

        try:

            res = self.alert_management_service.get_management_result()

            self._update_alert_management_ui(res)

        except Exception:

            pass

    def _update_alert_management_ui(self, mgmt_result: Any) -> None:

        if mgmt_result is None:

            return

        summary = getattr(mgmt_result, "summary", None)

        if summary is not None:

            if hasattr(self, "lbl_am_total"):

                self.lbl_am_total.setText(f"Total Alerts: {getattr(summary, 'total_alerts', 0)}")

            if hasattr(self, "lbl_am_active"):

                self.lbl_am_active.setText(f"Active: {getattr(summary, 'active_alerts', 0)}")

            if hasattr(self, "lbl_am_acknowledged"):

                self.lbl_am_acknowledged.setText(f"Acknowledged: {getattr(summary, 'acknowledged_alerts', 0)}")

            if hasattr(self, "lbl_am_dismissed"):

                self.lbl_am_dismissed.setText(f"Dismissed: {getattr(summary, 'dismissed_alerts', 0)}")

            if hasattr(self, "lbl_am_last_updated"):

                updated = getattr(summary, "last_updated", "N/A") or "N/A"

                self.lbl_am_last_updated.setText(f"Last Updated: {updated}")

        if hasattr(self, "alert_management_list_container"):

            self._clear_layout(self.alert_management_list_container)

            alerts = getattr(mgmt_result, "alerts", [])

            if alerts:

                for alert in alerts:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    id_lbl = QLabel(f"Alert ID: {getattr(alert, 'alert_id', '')}")

                    id_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    sev = getattr(alert, 'severity', 'INFO')

                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"

                    sev_lbl = QLabel(f"[{sev}]")

                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    title_lbl = QLabel(getattr(alert, 'title', ''))

                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(f"Current Status: {getattr(alert, 'status', 'ACTIVE')}")

                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))

                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    lyt.addWidget(id_lbl)

                    lyt.addWidget(sev_lbl)

                    lyt.addWidget(title_lbl)

                    lyt.addWidget(status_lbl)

                    lyt.addWidget(ts_lbl)

                    self.alert_management_list_container.addWidget(card)

            else:

                lbl = QLabel("No managed alerts")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.alert_management_list_container.addWidget(lbl)

    def load_alert_history(self) -> None:

        """Bind live alert history summary to UI."""

        if getattr(self, "alert_history_service", None) is None:

            return

        try:

            res = self.alert_history_service.get_history()

            self._update_alert_history_ui(res)

        except Exception:

            pass

    def _update_alert_history_ui(self, history: Any) -> None:

        if history is None:

            return

        if hasattr(self, "lbl_ah_total"):

            self.lbl_ah_total.setText(f"Total Entries: {getattr(history, 'total_entries', 0)}")

        if hasattr(self, "lbl_ah_latest"):

            latest = getattr(history, "latest_timestamp", "N/A") or "N/A"

            self.lbl_ah_latest.setText(f"Latest: {latest}")

        if hasattr(self, "lbl_ah_earliest"):

            earliest = getattr(history, "earliest_timestamp", "N/A") or "N/A"

            self.lbl_ah_earliest.setText(f"Earliest: {earliest}")

        if hasattr(self, "alert_history_list_container"):

            self._clear_layout(self.alert_history_list_container)

            entries = getattr(history, "entries", [])

            if entries:

                for entry in entries:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    ts_lbl = QLabel(getattr(entry, 'timestamp', ''))

                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    sev = getattr(entry, 'severity', 'INFO')

                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"

                    sev_lbl = QLabel(f"[{sev}]")

                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    type_lbl = QLabel(f"Type: {getattr(entry, 'alert_type', '')}")

                    type_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    title_lbl = QLabel(getattr(entry, 'title', ''))

                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(f"Status: {getattr(entry, 'status', 'ACTIVE')}")

                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    lyt.addWidget(ts_lbl)

                    lyt.addWidget(sev_lbl)

                    lyt.addWidget(type_lbl)

                    lyt.addWidget(title_lbl)

                    lyt.addWidget(status_lbl)

                    self.alert_history_list_container.addWidget(card)

            else:

                lbl = QLabel("No alert history")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.alert_history_list_container.addWidget(lbl)

    def load_alert_dashboard(self) -> None:

        """Bind live alert dashboard summary to UI."""

        if getattr(self, "alert_dashboard_service", None) is None:

            return

        try:

            res = self.alert_dashboard_service.build_dashboard()

            self._update_alert_dashboard_ui(res)

        except Exception:

            pass

    def _update_alert_dashboard_ui(self, dashboard: Any) -> None:

        if dashboard is None:

            return

        summary = getattr(dashboard, "summary", None)

        if summary is not None:

            if hasattr(self, "lbl_ad_total"):

                self.lbl_ad_total.setText(f"Total Alerts: {getattr(summary, 'total_alerts', 0)}")

            if hasattr(self, "lbl_ad_active"):

                self.lbl_ad_active.setText(f"Active: {getattr(summary, 'active_alerts', 0)}")

            if hasattr(self, "lbl_ad_acknowledged"):

                self.lbl_ad_acknowledged.setText(f"Acknowledged: {getattr(summary, 'acknowledged_alerts', 0)}")

            if hasattr(self, "lbl_ad_dismissed"):

                self.lbl_ad_dismissed.setText(f"Dismissed: {getattr(summary, 'dismissed_alerts', 0)}")

            if hasattr(self, "lbl_ad_info"):

                self.lbl_ad_info.setText(f"INFO: {getattr(summary, 'info_alerts', 0)}")

            if hasattr(self, "lbl_ad_low"):

                self.lbl_ad_low.setText(f"LOW: {getattr(summary, 'low_alerts', 0)}")

            if hasattr(self, "lbl_ad_medium"):

                self.lbl_ad_medium.setText(f"MEDIUM: {getattr(summary, 'medium_alerts', 0)}")

            if hasattr(self, "lbl_ad_high"):

                self.lbl_ad_high.setText(f"HIGH: {getattr(summary, 'high_alerts', 0)}")

            if hasattr(self, "lbl_ad_critical"):

                self.lbl_ad_critical.setText(f"CRITICAL: {getattr(summary, 'critical_alerts', 0)}")

        if hasattr(self, "alert_dashboard_list_container"):

            self._clear_layout(self.alert_dashboard_list_container)

            alerts = getattr(dashboard, "alerts", [])

            if alerts:

                for alert in alerts:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    sev = getattr(alert, 'severity', 'INFO')

                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"

                    sev_lbl = QLabel(f"[{sev}]")

                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    type_lbl = QLabel(f"Type: {getattr(alert, 'alert_type', '')}")

                    type_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    title_lbl = QLabel(getattr(alert, 'title', ''))

                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(f"Status: {getattr(alert, 'status', 'ACTIVE')}")

                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))

                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    lyt.addWidget(sev_lbl)

                    lyt.addWidget(type_lbl)

                    lyt.addWidget(title_lbl)

                    lyt.addWidget(status_lbl)

                    lyt.addWidget(ts_lbl)

                    self.alert_dashboard_list_container.addWidget(card)

            else:

                lbl = QLabel("No dashboard alerts")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.alert_dashboard_list_container.addWidget(lbl)

    def load_alert_rules(self) -> None:

        """Bind live alert rules evaluation to UI."""

        if getattr(self, "alert_rules_service", None) is None:

            return

        try:

            res = self.alert_rules_service.evaluate_rules()

            self._update_alert_rules_ui(res)

        except Exception:

            pass

    def _update_alert_rules_ui(self, rules_result: Any) -> None:

        if rules_result is None:

            return

        if hasattr(self, "lbl_alert_rules_total"):

            self.lbl_alert_rules_total.setText(f"Total Rules: {getattr(rules_result, 'total_rules', 0)}")

        if hasattr(self, "lbl_alert_rules_triggered"):

            self.lbl_alert_rules_triggered.setText(f"Triggered Rules: {getattr(rules_result, 'triggered_rules', 0)}")

        if hasattr(self, "alert_rules_list_container"):

            self._clear_layout(self.alert_rules_list_container)

            rules = getattr(rules_result, "rules", [])

            if rules:

                for rule in rules:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    name_lbl = QLabel(getattr(rule, 'rule_name', ''))

                    name_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    sev = getattr(rule, 'severity', 'INFO')

                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"

                    sev_lbl = QLabel(f"Severity: {sev}")

                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    triggered = getattr(rule, 'triggered', False)

                    triggered_text = "YES" if triggered else "NO"

                    triggered_color = "#16a34a" if triggered else "#64748b"

                    triggered_lbl = QLabel(f"Triggered: {triggered_text}")

                    triggered_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {triggered_color};")

                    desc_lbl = QLabel(getattr(rule, 'description', ''))

                    desc_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    lyt.addWidget(name_lbl)

                    lyt.addWidget(sev_lbl)

                    lyt.addWidget(triggered_lbl)

                    lyt.addWidget(desc_lbl)

                    self.alert_rules_list_container.addWidget(card)

            else:

                lbl = QLabel("No alert rules evaluated")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.alert_rules_list_container.addWidget(lbl)

    def load_generated_alerts(self) -> None:

        """Bind live generated alerts report to UI."""

        if getattr(self, "alert_generation_service", None) is None:

            return

        try:

            res = self.alert_generation_service.generate_alerts()

            self._update_generated_alerts_ui(res)

        except Exception:

            pass

    def _update_generated_alerts_ui(self, gen_result: Any) -> None:

        if gen_result is None:

            return

        if hasattr(self, "lbl_gen_alerts_count"):

            self.lbl_gen_alerts_count.setText(f"Generated Alerts: {getattr(gen_result, 'generated_alerts', 0)}")

        if hasattr(self, "generated_alerts_container"):

            self._clear_layout(self.generated_alerts_container)

            alerts = getattr(gen_result, "alerts", [])

            if alerts:

                for alert in alerts:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    sev = getattr(alert, 'severity', 'INFO')

                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#2563eb"

                    sev_lbl = QLabel(f"[{sev}]")

                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    type_lbl = QLabel(f"Type: {getattr(alert, 'alert_type', '')}")

                    type_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))

                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    title_lbl = QLabel(getattr(alert, 'title', ''))

                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(getattr(alert, 'status', 'ACTIVE'))

                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    lyt.addWidget(sev_lbl)

                    lyt.addWidget(type_lbl)

                    lyt.addWidget(ts_lbl)

                    lyt.addWidget(title_lbl)

                    lyt.addWidget(status_lbl)

                    self.generated_alerts_container.addWidget(card)

            else:

                lbl = QLabel("No generated alerts")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.generated_alerts_container.addWidget(lbl)

    def load_alert_center(self) -> None:

        """Bind live alert center state to UI."""

        if getattr(self, "alert_center_service", None) is None:

            return

        try:

            state = self.alert_center_service.get_state()

            self._update_alert_center_ui(state)

        except Exception:

            pass

    def _update_alert_center_ui(self, state: Any) -> None:

        if state is None:

            return

        if hasattr(self, "lbl_ac_total"):

            self.lbl_ac_total.setText(f"Total Alerts: {getattr(state, 'total_alerts', 0)}")

        if hasattr(self, "lbl_ac_active"):

            self.lbl_ac_active.setText(f"Active: {getattr(state, 'active_alerts', 0)}")

        if hasattr(self, "lbl_ac_acknowledged"):

            self.lbl_ac_acknowledged.setText(f"Acknowledged: {getattr(state, 'acknowledged_alerts', 0)}")

        if hasattr(self, "lbl_ac_dismissed"):

            self.lbl_ac_dismissed.setText(f"Dismissed: {getattr(state, 'dismissed_alerts', 0)}")

        if hasattr(self, "alerts_list_container"):

            self._clear_layout(self.alerts_list_container)

            alerts = getattr(state, "alerts", [])

            if alerts:

                for alert in alerts:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    sev = getattr(alert, 'severity', 'INFO')

                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#2563eb"

                    sev_lbl = QLabel(f"[{sev}]")

                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))

                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    title_lbl = QLabel(getattr(alert, 'title', ''))

                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(getattr(alert, 'status', 'ACTIVE'))

                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    lyt.addWidget(sev_lbl)

                    lyt.addWidget(ts_lbl)

                    lyt.addWidget(title_lbl)

                    lyt.addWidget(status_lbl)

                    self.alerts_list_container.addWidget(card)

            else:

                lbl = QLabel("No alerts recorded")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.alerts_list_container.addWidget(lbl)

    def load_monitoring_dashboard(self) -> None:

        """Bind live portfolio health monitoring dashboard to UI."""

        if getattr(self, "monitoring_dashboard_service", None) is None:

            return

        try:

            dashboard = self.monitoring_dashboard_service.build_dashboard()

            self._update_monitoring_dashboard_ui(dashboard)

        except Exception:

            pass

    def _update_monitoring_dashboard_ui(self, dashboard: Any) -> None:

        if dashboard is None:

            return

        if hasattr(self, "lbl_mon_dash_status"):

            self.lbl_mon_dash_status.setText(f"Monitoring Status: {getattr(dashboard, 'monitoring_status', 'UNAVAILABLE')}")

        if hasattr(self, "lbl_mon_dash_enabled"):

            enabled = getattr(dashboard, 'monitoring_enabled', False)

            self.lbl_mon_dash_enabled.setText(f"Monitoring Enabled: {'YES' if enabled else 'NO'}")

        if hasattr(self, "lbl_mon_dash_latest_score"):

            self.lbl_mon_dash_latest_score.setText(f"Latest Score: {getattr(dashboard, 'latest_score', 0)}")

        if hasattr(self, "lbl_mon_dash_latest_grade"):

            self.lbl_mon_dash_latest_grade.setText(f"Latest Grade: {getattr(dashboard, 'latest_grade', '-')}")

        if hasattr(self, "lbl_mon_dash_latest_snapshot"):

            snap_time = getattr(dashboard, 'latest_snapshot_time', "N/A") or "N/A"

            self.lbl_mon_dash_latest_snapshot.setText(f"Latest Snapshot: {snap_time}")

        if hasattr(self, "lbl_mon_dash_total_snapshots"):

            self.lbl_mon_dash_total_snapshots.setText(f"Total Snapshots: {getattr(dashboard, 'total_snapshots', 0)}")

        if hasattr(self, "lbl_mon_dash_timeline_entries"):

            self.lbl_mon_dash_timeline_entries.setText(f"Timeline Entries: {getattr(dashboard, 'timeline_entries', 0)}")

        if hasattr(self, "lbl_mon_dash_latest_change_count"):

            self.lbl_mon_dash_latest_change_count.setText(f"Latest Change Count: {getattr(dashboard, 'latest_change_count', 0)}")

        if hasattr(self, "lbl_mon_dash_total_detected_changes"):

            self.lbl_mon_dash_total_detected_changes.setText(f"Total Detected Changes: {getattr(dashboard, 'total_detected_changes', 0)}")

    def load_timeline(self) -> None:

        """Bind live portfolio health timeline report to UI."""

        if getattr(self, "timeline_service", None) is None:

            return

        try:

            timeline = self.timeline_service.build_timeline()

            self._update_timeline_ui(timeline)

        except Exception:

            pass

    def _update_timeline_ui(self, timeline: Any) -> None:

        if timeline is None:

            return

        if hasattr(self, "lbl_tl_entries"):

            self.lbl_tl_entries.setText(f"Entries: {getattr(timeline, 'total_entries', 0)}")

        if hasattr(self, "lbl_tl_earliest"):

            earliest = getattr(timeline, "earliest_timestamp", "N/A") or "N/A"

            self.lbl_tl_earliest.setText(f"Earliest: {earliest}")

        if hasattr(self, "lbl_tl_latest"):

            latest = getattr(timeline, "latest_timestamp", "N/A") or "N/A"

            self.lbl_tl_latest.setText(f"Latest: {latest}")

        if hasattr(self, "timeline_list_container"):

            self._clear_layout(self.timeline_list_container)

            entries = getattr(timeline, "entries", [])

            if entries:

                for entry in entries:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    ts_lbl = QLabel(f"#{getattr(entry, 'sequence', '')}  {getattr(entry, 'timestamp', '')}")

                    ts_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67;")

                    score_lbl = QLabel(f"Score: {getattr(entry, 'score', 0)}")

                    score_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

                    grade_lbl = QLabel(f"Grade: {getattr(entry, 'grade', '-')}")

                    grade_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

                    trend = getattr(entry, "trend_direction", "STABLE")

                    t_color = "#16a34a" if trend == "IMPROVING" else "#dc2626" if trend == "DETERIORATING" else "#64748b"

                    trend_lbl = QLabel(f"Trend: {trend}")

                    trend_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t_color};")

                    changes_lbl = QLabel(f"Changes: {getattr(entry, 'change_count', 0)}")

                    changes_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

                    lyt.addWidget(ts_lbl)

                    lyt.addWidget(score_lbl)

                    lyt.addWidget(grade_lbl)

                    lyt.addWidget(trend_lbl)

                    lyt.addWidget(changes_lbl)

                    self.timeline_list_container.addWidget(card)

            else:

                lbl = QLabel("No timeline entries available")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.timeline_list_container.addWidget(lbl)

    def load_change_detection(self) -> None:

        """Bind live portfolio health change detection report to UI."""

        if getattr(self, "change_detection_service", None) is None:

            return

        try:

            report = self.change_detection_service.detect_changes()

            self._update_change_detection_ui(report)

        except Exception:

            pass

    def _update_change_detection_ui(self, report: Any) -> None:

        if report is None:

            return

        if hasattr(self, "lbl_cd_snapshots_compared"):

            self.lbl_cd_snapshots_compared.setText(f"Snapshots Compared: {getattr(report, 'snapshot_count', 0)}")

        if hasattr(self, "lbl_cd_changes_detected"):

            has_chg = getattr(report, 'has_changes', False)

            self.lbl_cd_changes_detected.setText(f"Changes Detected: {'YES' if has_chg else 'NO'}")

        if hasattr(self, "lbl_cd_total_changes"):

            self.lbl_cd_total_changes.setText(f"Total Changes: {getattr(report, 'total_changes', 0)}")

        if hasattr(self, "changes_list_container"):

            self._clear_layout(self.changes_list_container)

            changes = getattr(report, "changes", [])

            changed_items = [c for c in changes if getattr(c, "change_type", "UNCHANGED") != "UNCHANGED"]

            if changed_items:

                for item in changed_items:

                    card = QFrame()

                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px;")

                    lyt = QVBoxLayout(card)

                    lyt.setSpacing(4)

                    fname_lbl = QLabel(getattr(item, "field_name", ""))

                    fname_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67;")

                    val_lbl = QLabel(f"{getattr(item, 'previous_value', '')} → {getattr(item, 'current_value', '')}")

                    val_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

                    ctype = getattr(item, "change_type", "")

                    color = "#16a34a" if ctype == "INCREASED" else "#dc2626" if ctype == "DECREASED" else "#2563eb"

                    type_lbl = QLabel(ctype)

                    type_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {color};")

                    lyt.addWidget(fname_lbl)

                    lyt.addWidget(val_lbl)

                    lyt.addWidget(type_lbl)

                    self.changes_list_container.addWidget(card)

            else:

                lbl = QLabel("No changes detected")

                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                self.changes_list_container.addWidget(lbl)

    def load_monitoring(self) -> None:

        """Bind live portfolio health monitoring metrics to UI."""

        if getattr(self, "monitor_service", None) is None:

            return

        try:

            state = self.monitor_service.get_monitoring_state()

            if state is not None:

                if hasattr(self, "lbl_mon_enabled"):

                    enabled_str = "YES" if state.monitoring_enabled else "NO"

                    self.lbl_mon_enabled.setText(f"Monitoring Enabled: {enabled_str}")

                if hasattr(self, "lbl_mon_status"):

                    self.lbl_mon_status.setText(f"Monitoring Status: {state.monitoring_status}")

                if hasattr(self, "lbl_mon_snapshots"):

                    self.lbl_mon_snapshots.setText(f"Snapshots Available: {state.snapshot_count}")

                if hasattr(self, "lbl_mon_latest_snapshot"):

                    time_str = state.latest_snapshot_time if state.latest_snapshot_time else "N/A"

                    self.lbl_mon_latest_snapshot.setText(f"Latest Snapshot: {time_str}")

                if hasattr(self, "lbl_mon_latest_score"):

                    self.lbl_mon_latest_score.setText(f"Latest Score: {state.latest_score}")

                if hasattr(self, "lbl_mon_latest_grade"):

                    self.lbl_mon_latest_grade.setText(f"Latest Grade: {state.latest_grade}")

        except Exception:

            pass

    def load_history(self) -> None:

        """Bind live portfolio health history metrics to UI."""

        if getattr(self, "history_service", None) is None:

            return

        try:

            history = self.history_service.get_history()

            count = len(history) if history else 0

            latest = history[-1] if history else None

            if hasattr(self, "lbl_history_entries"):

                self.lbl_history_entries.setText(f"History Entries: {count}")

            if hasattr(self, "lbl_history_latest_score"):

                score_str = str(latest.score) if latest else "N/A"

                self.lbl_history_latest_score.setText(f"Latest Score: {score_str}")

            if hasattr(self, "lbl_history_latest_grade"):

                grade_str = str(latest.grade) if latest else "N/A"

                self.lbl_history_latest_grade.setText(f"Latest Grade: {grade_str}")

        except Exception:

            pass

    def load_snapshot(self, snapshot: Optional[PortfolioHealthSnapshot] = None) -> None:
        """Bind live snapshot metrics to the metric cards."""
        if snapshot is None:
            return

        pos_cnt = getattr(snapshot, "position_count", 0)

        if hasattr(self, "empty_banner"):
            if pos_cnt == 0:
                self.empty_banner.show()
            else:
                self.empty_banner.hide()

        if "Position Count" in self.cards:
            self.cards["Position Count"].setText(str(pos_cnt))

        if "Cash Allocation" in self.cards:
            if pos_cnt == 0:
                self.cards["Cash Allocation"].setText("N/A")
            else:
                val = snapshot.cash_allocation_pct
                val_str = f"{val:.1f}%" if (val % 1 != 0) else f"{int(val)}%"
                self.cards["Cash Allocation"].setText(val_str)

        if "Largest Position" in self.cards:
            if pos_cnt == 0:
                self.cards["Largest Position"].setText("N/A")
            else:
                self.cards["Largest Position"].setText(str(snapshot.largest_position))

    def load_result(self, result: Optional[PortfolioHealthResult] = None) -> None:
        """Bind live PortfolioHealthResult metrics to score, diversification, concentration, and analytics sections."""
        if result is None:
            return

        pos_cnt = getattr(result, "position_count", 0)
        grade = getattr(result, "grade", "")

        if "Overall Health Score" in self.cards:
            if pos_cnt == 0 or grade == "N/A":
                self.cards["Overall Health Score"].setText("N/A")
            else:
                grade_suffix = f" ({grade})" if grade else ""
                self.cards["Overall Health Score"].setText(f"{result.score} / 100{grade_suffix}")

        if "Diversification" in self.cards:
            if pos_cnt == 0 or grade == "N/A":
                self.cards["Diversification"].setText("N/A")
            else:
                self.cards["Diversification"].setText(str(result.diversification_rating))

        if "Concentration" in self.cards:
            if pos_cnt == 0 or grade == "N/A":
                self.cards["Concentration"].setText("N/A")
            else:
                self.cards["Concentration"].setText(str(result.concentration_rating))

        analytics = getattr(result, "analytics", None)

        if analytics is not None:

            if hasattr(self, "lbl_breakdown_div"):

                self.lbl_breakdown_div.setText(f"Diversification: {analytics.diversification_score} / 40")

            if hasattr(self, "lbl_breakdown_conc"):

                self.lbl_breakdown_conc.setText(f"Concentration: {analytics.concentration_score} / 40")

            if hasattr(self, "lbl_breakdown_cash"):

                self.lbl_breakdown_cash.setText(f"Cash Allocation: {analytics.cash_score} / 20")

            if hasattr(self, "strengths_container"):

                self._clear_layout(self.strengths_container)

                if analytics.strengths:

                    for item in analytics.strengths:

                        lbl = QLabel(f"• {item}")

                        lbl.setStyleSheet("font-size: 14px; color: #16a34a; font-weight: 500;")

                        self.strengths_container.addWidget(lbl)

                else:

                    lbl = QLabel("None identified")

                    lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                    self.strengths_container.addWidget(lbl)

            if hasattr(self, "weaknesses_container"):

                self._clear_layout(self.weaknesses_container)

                if analytics.weaknesses:

                    for item in analytics.weaknesses:

                        lbl = QLabel(f"• {item}")

                        lbl.setStyleSheet("font-size: 14px; color: #dc2626; font-weight: 500;")

                        self.weaknesses_container.addWidget(lbl)

                else:

                    lbl = QLabel("None identified")

                    lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")

                    self.weaknesses_container.addWidget(lbl)

        trend = getattr(result, "trend", None)

        if trend is not None:

            if hasattr(self, "lbl_trend_current"):

                self.lbl_trend_current.setText(f"Current Score: {trend.current_score}")

            if hasattr(self, "lbl_trend_previous"):

                self.lbl_trend_previous.setText(f"Previous Score: {trend.previous_score}")

            if hasattr(self, "lbl_trend_change"):

                change_str = f"+{trend.score_change}" if trend.score_change > 0 else str(trend.score_change)

                self.lbl_trend_change.setText(f"Score Change: {change_str}")

            if hasattr(self, "lbl_trend_direction"):

                self.lbl_trend_direction.setText(f"Trend: {trend.trend_direction}")

        hist_analytics = getattr(result, "historical_analytics", None)

        if hist_analytics is not None:

            if hasattr(self, "lbl_hist_entries"):

                self.lbl_hist_entries.setText(f"History Entries: {hist_analytics.history_count}")

            if hasattr(self, "lbl_hist_best"):

                self.lbl_hist_best.setText(f"Best Score: {hist_analytics.best_score}")

            if hasattr(self, "lbl_hist_worst"):

                self.lbl_hist_worst.setText(f"Worst Score: {hist_analytics.worst_score}")

            if hasattr(self, "lbl_hist_avg"):

                self.lbl_hist_avg.setText(f"Average Score: {hist_analytics.average_score}")

            if hasattr(self, "lbl_hist_curr"):

                self.lbl_hist_curr.setText(f"Current Score: {hist_analytics.current_score}")

            if hasattr(self, "lbl_hist_trend"):

                self.lbl_hist_trend.setText(f"Overall Trend: {hist_analytics.overall_trend}")

        summary = getattr(result, "dashboard_summary", None)

        if summary is not None:

            if hasattr(self, "lbl_dash_curr_score"):

                self.lbl_dash_curr_score.setText(f"Current Score: {summary.current_score}")

            if hasattr(self, "lbl_dash_curr_grade"):

                self.lbl_dash_curr_grade.setText(f"Current Grade: {summary.current_grade}")

            if hasattr(self, "lbl_dash_best_score"):

                self.lbl_dash_best_score.setText(f"Best Historical Score: {summary.best_score}")

            if hasattr(self, "lbl_dash_best_grade"):

                self.lbl_dash_best_grade.setText(f"Best Historical Grade: {summary.best_grade}")

            if hasattr(self, "lbl_dash_worst_score"):

                self.lbl_dash_worst_score.setText(f"Worst Historical Score: {summary.worst_score}")

            if hasattr(self, "lbl_dash_worst_grade"):

                self.lbl_dash_worst_grade.setText(f"Worst Historical Grade: {summary.worst_grade}")

            if hasattr(self, "lbl_dash_avg_score"):

                self.lbl_dash_avg_score.setText(f"Average Historical Score: {summary.average_score}")

            if hasattr(self, "lbl_dash_total_snapshots"):

                self.lbl_dash_total_snapshots.setText(f"Total Snapshots: {summary.total_snapshots}")

            if hasattr(self, "lbl_highlight_highest"):

                self.lbl_highlight_highest.setText(f"Highest Score Achieved: {summary.best_score}")

            if hasattr(self, "lbl_highlight_lowest"):

                self.lbl_highlight_lowest.setText(f"Lowest Score Achieved: {summary.worst_score}")

            if hasattr(self, "lbl_highlight_vs_avg"):

                diff = round(summary.current_score - summary.average_score, 1)

                diff_str = f"+{diff}" if diff > 0 else str(diff)

                self.lbl_highlight_vs_avg.setText(f"Current Score vs Average: {diff_str}")

        metrics = getattr(result, "historical_metrics", None)

        if metrics is not None:

            if hasattr(self, "lbl_metrics_range"):

                self.lbl_metrics_range.setText(f"Score Range: {metrics.score_range}")

            if hasattr(self, "lbl_metrics_volatility"):

                self.lbl_metrics_volatility.setText(f"Volatility Score: {metrics.volatility_score}")

            if hasattr(self, "lbl_metrics_improving"):

                self.lbl_metrics_improving.setText(f"Improving Periods: {metrics.improving_periods}")

            if hasattr(self, "lbl_metrics_deteriorating"):

                self.lbl_metrics_deteriorating.setText(f"Deteriorating Periods: {metrics.deteriorating_periods}")

            if hasattr(self, "lbl_metrics_stability"):

                self.lbl_metrics_stability.setText(f"Stability Rating: {metrics.stability_rating}")

        insights = getattr(result, "historical_insights", None)

        if insights is not None:

            if hasattr(self, "lbl_insights_improvement"):

                self.lbl_insights_improvement.setText(f"Improvement Percentage: {insights.improvement_percentage}%")

            if hasattr(self, "lbl_insights_deterioration"):

                self.lbl_insights_deterioration.setText(f"Deterioration Percentage: {insights.deterioration_percentage}%")

            if hasattr(self, "lbl_insights_neutral"):

                self.lbl_insights_neutral.setText(f"Neutral Percentage: {insights.neutral_percentage}%")

            if hasattr(self, "lbl_insights_consistency"):

                self.lbl_insights_consistency.setText(f"Consistency Score: {insights.consistency_score}")

            if hasattr(self, "lbl_insights_quality"):

                self.lbl_insights_quality.setText(f"Quality Rating: {insights.quality_rating}")

            if hasattr(self, "lbl_insights_direction"):

                self.lbl_insights_direction.setText(f"Direction Rating: {insights.direction_rating}")

        mon_state = getattr(result, "monitoring_state", None)

        if mon_state is not None:

            if hasattr(self, "lbl_mon_enabled"):

                enabled_str = "YES" if mon_state.monitoring_enabled else "NO"

                self.lbl_mon_enabled.setText(f"Monitoring Enabled: {enabled_str}")

            if hasattr(self, "lbl_mon_status"):

                self.lbl_mon_status.setText(f"Monitoring Status: {mon_state.monitoring_status}")

            if hasattr(self, "lbl_mon_snapshots"):

                self.lbl_mon_snapshots.setText(f"Snapshots Available: {mon_state.snapshot_count}")

            if hasattr(self, "lbl_mon_latest_snapshot"):

                time_str = mon_state.latest_snapshot_time if mon_state.latest_snapshot_time else "N/A"

                self.lbl_mon_latest_snapshot.setText(f"Latest Snapshot: {time_str}")

            if hasattr(self, "lbl_mon_latest_score"):

                self.lbl_mon_latest_score.setText(f"Latest Score: {mon_state.latest_score}")

            if hasattr(self, "lbl_mon_latest_grade"):

                self.lbl_mon_latest_grade.setText(f"Latest Grade: {mon_state.latest_grade}")

        cd_report = getattr(result, "change_report", None)

        if cd_report is not None:

            self._update_change_detection_ui(cd_report)

        timeline = getattr(result, "timeline", None)

        if timeline is not None:

            self._update_timeline_ui(timeline)

        mon_dash = getattr(result, "monitoring_dashboard", None)

        if mon_dash is not None:

            self._update_monitoring_dashboard_ui(mon_dash)

        ac_state = getattr(result, "alert_center", None)

        if ac_state is not None:

            self._update_alert_center_ui(ac_state)

        gen_res = getattr(result, "generated_alerts", None)

        if gen_res is not None:

            self._update_generated_alerts_ui(gen_res)

        dp_res = getattr(result, "decision_prioritization", None)

        if dp_res is not None:

            self._update_decision_prioritization_ui(dp_res)

    def _clear_layout(self, layout: QVBoxLayout) -> None:

        while layout.count():

            child = layout.takeAt(0)

            if child.widget():

                child.widget().deleteLater()

    def _build_ui(self):

        self.setStyleSheet("""

            QWidget {

                background-color: #f5f7fb;

                color: #1f2937;

                font-family: Segoe UI;

            }

            QLabel#pageTitle {

                font-size: 28px;

                font-weight: 700;

                color: #173b67;

            }

            QLabel#pageSubtitle {

                font-size: 14px;

                color: #64748b;

            }

            QFrame#metricCard {

                background-color: white;

                border: 1px solid #dce3ed;

                border-radius: 10px;

            }

            QLabel#cardTitle {

                font-size: 12px;

                font-weight: 600;

                color: #64748b;

            }

            QLabel#cardValue {

                font-size: 22px;

                font-weight: 700;

                color: #173b67;

            }

            QLabel#sectionHeader {

                font-size: 16px;

                font-weight: 700;

                color: #173b67;

            }

        """)

        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(0, 0, 0, 0)

        outer_layout.setSpacing(0)

        scroll = QScrollArea(self)

        scroll.setWidgetResizable(True)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content_widget = QWidget()

        root_layout = QVBoxLayout(content_widget)

        root_layout.setContentsMargins(24, 20, 24, 20)

        root_layout.setSpacing(20)

        # Header Title

        title_box = QVBoxLayout()

        header_title = QLabel("Portfolio Health")

        header_title.setObjectName("pageTitle")

        header_subtitle = QLabel("Overview of key health and risk metrics for your portfolio")

        header_subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(header_title)

        title_box.addWidget(header_subtitle)

        root_layout.addLayout(title_box)

        # Empty State Banner
        self.empty_banner = QFrame()
        self.empty_banner.setObjectName("metricCard")
        self.empty_banner.setStyleSheet("QFrame#metricCard { background-color: #eff6ff; border: 1px solid #93c5fd; border-radius: 8px; }")
        empty_banner_layout = QVBoxLayout(self.empty_banner)
        empty_banner_layout.setContentsMargins(16, 12, 16, 12)
        lbl_empty_hdr = QLabel("No active portfolio data")
        lbl_empty_hdr.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e3a8a;")
        lbl_empty_sub = QLabel("Create or import a portfolio to evaluate portfolio health.")
        lbl_empty_sub.setStyleSheet("font-size: 13px; color: #3b82f6;")
        empty_banner_layout.addWidget(lbl_empty_hdr)
        empty_banner_layout.addWidget(lbl_empty_sub)
        self.empty_banner.hide()
        root_layout.addWidget(self.empty_banner)

        # Metric Cards Grid Layout

        cards_grid = QGridLayout()

        cards_grid.setSpacing(16)

        cards_spec = [

            ("Overall Health Score", "85 / 100", 0, 0),

            ("Diversification", "GOOD", 0, 1),

            ("Concentration", "MODERATE", 0, 2),

            ("Position Count", "12", 1, 0),

            ("Cash Allocation", "5%", 1, 1),

            ("Largest Position", "KPITTECH", 1, 2),

        ]

        self.cards = {}

        for title, value, row, col in cards_spec:

            card_frame, val_lbl = self._create_metric_card(title, value)

            cards_grid.addWidget(card_frame, row, col)

            self.cards[title] = val_lbl

        root_layout.addLayout(cards_grid)

        # Analytics Sections: Health Score Breakdown

        breakdown_card = QFrame()

        breakdown_card.setObjectName("metricCard")

        breakdown_layout = QVBoxLayout(breakdown_card)

        breakdown_layout.setContentsMargins(16, 14, 16, 14)

        breakdown_layout.setSpacing(8)

        lbl_breakdown_header = QLabel("Health Score Breakdown")

        lbl_breakdown_header.setObjectName("sectionHeader")

        breakdown_layout.addWidget(lbl_breakdown_header)

        self.lbl_breakdown_div = QLabel("Diversification: - / 40")

        self.lbl_breakdown_div.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_breakdown_conc = QLabel("Concentration: - / 40")

        self.lbl_breakdown_conc.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_breakdown_cash = QLabel("Cash Allocation: - / 20")

        self.lbl_breakdown_cash.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        breakdown_layout.addWidget(self.lbl_breakdown_div)

        breakdown_layout.addWidget(self.lbl_breakdown_conc)

        breakdown_layout.addWidget(self.lbl_breakdown_cash)

        root_layout.addWidget(breakdown_card)

        # Strengths Section

        strengths_card = QFrame()

        strengths_card.setObjectName("metricCard")

        strengths_layout = QVBoxLayout(strengths_card)

        strengths_layout.setContentsMargins(16, 14, 16, 14)

        strengths_layout.setSpacing(8)

        lbl_strengths_header = QLabel("Strengths")

        lbl_strengths_header.setObjectName("sectionHeader")

        strengths_layout.addWidget(lbl_strengths_header)

        self.strengths_container = QVBoxLayout()

        strengths_layout.addLayout(self.strengths_container)

        root_layout.addWidget(strengths_card)

        # Weaknesses Section

        weaknesses_card = QFrame()

        weaknesses_card.setObjectName("metricCard")

        weaknesses_layout = QVBoxLayout(weaknesses_card)

        weaknesses_layout.setContentsMargins(16, 14, 16, 14)

        weaknesses_layout.setSpacing(8)

        lbl_weaknesses_header = QLabel("Weaknesses")

        lbl_weaknesses_header.setObjectName("sectionHeader")

        weaknesses_layout.addWidget(lbl_weaknesses_header)

        self.weaknesses_container = QVBoxLayout()

        weaknesses_layout.addLayout(self.weaknesses_container)

        root_layout.addWidget(weaknesses_card)

        # Portfolio Health Trend Section

        trend_card = QFrame()

        trend_card.setObjectName("metricCard")

        trend_layout = QVBoxLayout(trend_card)

        trend_layout.setContentsMargins(16, 14, 16, 14)

        trend_layout.setSpacing(8)

        lbl_trend_header = QLabel("Portfolio Health Trend")

        lbl_trend_header.setObjectName("sectionHeader")

        trend_layout.addWidget(lbl_trend_header)

        self.lbl_trend_current = QLabel("Current Score: -")

        self.lbl_trend_current.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_trend_previous = QLabel("Previous Score: -")

        self.lbl_trend_previous.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_trend_change = QLabel("Score Change: -")

        self.lbl_trend_change.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_trend_direction = QLabel("Trend: -")

        self.lbl_trend_direction.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        trend_layout.addWidget(self.lbl_trend_current)

        trend_layout.addWidget(self.lbl_trend_previous)

        trend_layout.addWidget(self.lbl_trend_change)

        trend_layout.addWidget(self.lbl_trend_direction)

        root_layout.addWidget(trend_card)

        # Portfolio Health History Section

        history_card = QFrame()

        history_card.setObjectName("metricCard")

        history_layout = QVBoxLayout(history_card)

        history_layout.setContentsMargins(16, 14, 16, 14)

        history_layout.setSpacing(8)

        lbl_history_header = QLabel("Portfolio Health History")

        lbl_history_header.setObjectName("sectionHeader")

        history_layout.addWidget(lbl_history_header)

        self.lbl_history_entries = QLabel("History Entries: 0")

        self.lbl_history_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_history_latest_score = QLabel("Latest Score: N/A")

        self.lbl_history_latest_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_history_latest_grade = QLabel("Latest Grade: N/A")

        self.lbl_history_latest_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        history_layout.addWidget(self.lbl_history_entries)

        history_layout.addWidget(self.lbl_history_latest_score)

        history_layout.addWidget(self.lbl_history_latest_grade)

        root_layout.addWidget(history_card)

        # Portfolio Health Historical Analytics Section

        hist_card = QFrame()

        hist_card.setObjectName("metricCard")

        hist_layout = QVBoxLayout(hist_card)

        hist_layout.setContentsMargins(16, 14, 16, 14)

        hist_layout.setSpacing(8)

        lbl_hist_header = QLabel("Portfolio Health Historical Analytics")

        lbl_hist_header.setObjectName("sectionHeader")

        hist_layout.addWidget(lbl_hist_header)

        self.lbl_hist_entries = QLabel("History Entries: 0")

        self.lbl_hist_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_hist_best = QLabel("Best Score: 0")

        self.lbl_hist_best.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_hist_worst = QLabel("Worst Score: 0")

        self.lbl_hist_worst.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_hist_avg = QLabel("Average Score: 0.0")

        self.lbl_hist_avg.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_hist_curr = QLabel("Current Score: 0")

        self.lbl_hist_curr.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_hist_trend = QLabel("Overall Trend: STABLE")

        self.lbl_hist_trend.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        hist_layout.addWidget(self.lbl_hist_entries)

        hist_layout.addWidget(self.lbl_hist_best)

        hist_layout.addWidget(self.lbl_hist_worst)

        hist_layout.addWidget(self.lbl_hist_avg)

        hist_layout.addWidget(self.lbl_hist_curr)

        hist_layout.addWidget(self.lbl_hist_trend)

        root_layout.addWidget(hist_card)

        # Portfolio Health Dashboard Summary Section

        dash_card = QFrame()

        dash_card.setObjectName("metricCard")

        dash_layout = QVBoxLayout(dash_card)

        dash_layout.setContentsMargins(16, 14, 16, 14)

        dash_layout.setSpacing(8)

        lbl_dash_header = QLabel("Portfolio Health Dashboard Summary")

        lbl_dash_header.setObjectName("sectionHeader")

        dash_layout.addWidget(lbl_dash_header)

        self.lbl_dash_curr_score = QLabel("Current Score: 0")

        self.lbl_dash_curr_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dash_curr_grade = QLabel("Current Grade: -")

        self.lbl_dash_curr_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dash_best_score = QLabel("Best Historical Score: 0")

        self.lbl_dash_best_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dash_best_grade = QLabel("Best Historical Grade: -")

        self.lbl_dash_best_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dash_worst_score = QLabel("Worst Historical Score: 0")

        self.lbl_dash_worst_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dash_worst_grade = QLabel("Worst Historical Grade: -")

        self.lbl_dash_worst_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dash_avg_score = QLabel("Average Historical Score: 0.0")

        self.lbl_dash_avg_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dash_total_snapshots = QLabel("Total Snapshots: 0")

        self.lbl_dash_total_snapshots.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dash_layout.addWidget(self.lbl_dash_curr_score)

        dash_layout.addWidget(self.lbl_dash_curr_grade)

        dash_layout.addWidget(self.lbl_dash_best_score)

        dash_layout.addWidget(self.lbl_dash_best_grade)

        dash_layout.addWidget(self.lbl_dash_worst_score)

        dash_layout.addWidget(self.lbl_dash_worst_grade)

        dash_layout.addWidget(self.lbl_dash_avg_score)

        dash_layout.addWidget(self.lbl_dash_total_snapshots)

        # Historical Highlights Subsection

        lbl_highlights_header = QLabel("Historical Highlights")

        lbl_highlights_header.setObjectName("sectionHeader")

        lbl_highlights_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #173b67; margin-top: 6px;")

        dash_layout.addWidget(lbl_highlights_header)

        self.lbl_highlight_highest = QLabel("Highest Score Achieved: 0")

        self.lbl_highlight_highest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_highlight_lowest = QLabel("Lowest Score Achieved: 0")

        self.lbl_highlight_lowest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_highlight_vs_avg = QLabel("Current Score vs Average: 0.0")

        self.lbl_highlight_vs_avg.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dash_layout.addWidget(self.lbl_highlight_highest)

        dash_layout.addWidget(self.lbl_highlight_lowest)

        dash_layout.addWidget(self.lbl_highlight_vs_avg)

        root_layout.addWidget(dash_card)

        # Portfolio Health Historical Metrics Section

        metrics_card = QFrame()

        metrics_card.setObjectName("metricCard")

        metrics_layout = QVBoxLayout(metrics_card)

        metrics_layout.setContentsMargins(16, 14, 16, 14)

        metrics_layout.setSpacing(8)

        lbl_metrics_header = QLabel("Portfolio Health Historical Metrics")

        lbl_metrics_header.setObjectName("sectionHeader")

        metrics_layout.addWidget(lbl_metrics_header)

        self.lbl_metrics_range = QLabel("Score Range: 0")

        self.lbl_metrics_range.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_metrics_volatility = QLabel("Volatility Score: 0.0")

        self.lbl_metrics_volatility.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_metrics_improving = QLabel("Improving Periods: 0")

        self.lbl_metrics_improving.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_metrics_deteriorating = QLabel("Deteriorating Periods: 0")

        self.lbl_metrics_deteriorating.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_metrics_stability = QLabel("Stability Rating: VERY_STABLE")

        self.lbl_metrics_stability.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        metrics_layout.addWidget(self.lbl_metrics_range)

        metrics_layout.addWidget(self.lbl_metrics_volatility)

        metrics_layout.addWidget(self.lbl_metrics_improving)

        metrics_layout.addWidget(self.lbl_metrics_deteriorating)

        metrics_layout.addWidget(self.lbl_metrics_stability)

        root_layout.addWidget(metrics_card)

        # Portfolio Health Historical Insights Section

        insights_card = QFrame()

        insights_card.setObjectName("metricCard")

        insights_layout = QVBoxLayout(insights_card)

        insights_layout.setContentsMargins(16, 14, 16, 14)

        insights_layout.setSpacing(8)

        lbl_insights_header = QLabel("Portfolio Health Historical Insights")

        lbl_insights_header.setObjectName("sectionHeader")

        insights_layout.addWidget(lbl_insights_header)

        self.lbl_insights_improvement = QLabel("Improvement Percentage: 0.0%")

        self.lbl_insights_improvement.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_insights_deterioration = QLabel("Deterioration Percentage: 0.0%")

        self.lbl_insights_deterioration.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_insights_neutral = QLabel("Neutral Percentage: 0.0%")

        self.lbl_insights_neutral.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_insights_consistency = QLabel("Consistency Score: 0.0")

        self.lbl_insights_consistency.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_insights_quality = QLabel("Quality Rating: MIXED")

        self.lbl_insights_quality.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_insights_direction = QLabel("Direction Rating: STABLE")

        self.lbl_insights_direction.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        insights_layout.addWidget(self.lbl_insights_improvement)

        insights_layout.addWidget(self.lbl_insights_deterioration)

        insights_layout.addWidget(self.lbl_insights_neutral)

        insights_layout.addWidget(self.lbl_insights_consistency)

        insights_layout.addWidget(self.lbl_insights_quality)

        insights_layout.addWidget(self.lbl_insights_direction)

        root_layout.addWidget(insights_card)

        # Portfolio Health Monitoring Section

        monitoring_card = QFrame()

        monitoring_card.setObjectName("metricCard")

        monitoring_layout = QVBoxLayout(monitoring_card)

        monitoring_layout.setContentsMargins(16, 14, 16, 14)

        monitoring_layout.setSpacing(8)

        lbl_monitoring_header = QLabel("Portfolio Health Monitoring")

        lbl_monitoring_header.setObjectName("sectionHeader")

        monitoring_layout.addWidget(lbl_monitoring_header)

        self.lbl_mon_enabled = QLabel("Monitoring Enabled: NO")

        self.lbl_mon_enabled.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_status = QLabel("Monitoring Status: UNAVAILABLE")

        self.lbl_mon_status.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_snapshots = QLabel("Snapshots Available: 0")

        self.lbl_mon_snapshots.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_latest_snapshot = QLabel("Latest Snapshot: N/A")

        self.lbl_mon_latest_snapshot.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_latest_score = QLabel("Latest Score: 0")

        self.lbl_mon_latest_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_latest_grade = QLabel("Latest Grade: -")

        self.lbl_mon_latest_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        monitoring_layout.addWidget(self.lbl_mon_enabled)

        monitoring_layout.addWidget(self.lbl_mon_status)

        monitoring_layout.addWidget(self.lbl_mon_snapshots)

        monitoring_layout.addWidget(self.lbl_mon_latest_snapshot)

        monitoring_layout.addWidget(self.lbl_mon_latest_score)

        monitoring_layout.addWidget(self.lbl_mon_latest_grade)

        root_layout.addWidget(monitoring_card)

        # Portfolio Health Change Detection Section

        cd_card = QFrame()

        cd_card.setObjectName("metricCard")

        cd_layout = QVBoxLayout(cd_card)

        cd_layout.setContentsMargins(16, 14, 16, 14)

        cd_layout.setSpacing(8)

        lbl_cd_header = QLabel("Portfolio Health Change Detection")

        lbl_cd_header.setObjectName("sectionHeader")

        cd_layout.addWidget(lbl_cd_header)

        self.lbl_cd_snapshots_compared = QLabel("Snapshots Compared: 0")

        self.lbl_cd_snapshots_compared.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_cd_changes_detected = QLabel("Changes Detected: NO")

        self.lbl_cd_changes_detected.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_cd_total_changes = QLabel("Total Changes: 0")

        self.lbl_cd_total_changes.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        cd_layout.addWidget(self.lbl_cd_snapshots_compared)

        cd_layout.addWidget(self.lbl_cd_changes_detected)

        cd_layout.addWidget(self.lbl_cd_total_changes)

        lbl_changes_subheader = QLabel("Changes")

        lbl_changes_subheader.setStyleSheet("font-size: 15px; font-weight: 700; color: #173b67; margin-top: 6px;")

        cd_layout.addWidget(lbl_changes_subheader)

        self.changes_list_container = QVBoxLayout()

        cd_layout.addLayout(self.changes_list_container)

        root_layout.addWidget(cd_card)

        # Portfolio Health Timeline Section

        tl_card = QFrame()

        tl_card.setObjectName("metricCard")

        tl_layout = QVBoxLayout(tl_card)

        tl_layout.setContentsMargins(16, 14, 16, 14)

        tl_layout.setSpacing(8)

        lbl_tl_header = QLabel("Portfolio Health Timeline")

        lbl_tl_header.setObjectName("sectionHeader")

        tl_layout.addWidget(lbl_tl_header)

        self.lbl_tl_entries = QLabel("Entries: 0")

        self.lbl_tl_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_tl_earliest = QLabel("Earliest: N/A")

        self.lbl_tl_earliest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_tl_latest = QLabel("Latest: N/A")

        self.lbl_tl_latest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        tl_layout.addWidget(self.lbl_tl_entries)

        tl_layout.addWidget(self.lbl_tl_earliest)

        tl_layout.addWidget(self.lbl_tl_latest)

        self.timeline_list_container = QVBoxLayout()

        tl_layout.addLayout(self.timeline_list_container)

        root_layout.addWidget(tl_card)

        # Portfolio Health Monitoring Dashboard Section

        mon_dash_card = QFrame()

        mon_dash_card.setObjectName("metricCard")

        mon_dash_layout = QVBoxLayout(mon_dash_card)

        mon_dash_layout.setContentsMargins(16, 14, 16, 14)

        mon_dash_layout.setSpacing(8)

        lbl_mon_dash_header = QLabel("Portfolio Health Monitoring Dashboard")

        lbl_mon_dash_header.setObjectName("sectionHeader")

        mon_dash_layout.addWidget(lbl_mon_dash_header)

        self.lbl_mon_dash_status = QLabel("Monitoring Status: UNAVAILABLE")

        self.lbl_mon_dash_status.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_enabled = QLabel("Monitoring Enabled: NO")

        self.lbl_mon_dash_enabled.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_latest_score = QLabel("Latest Score: 0")

        self.lbl_mon_dash_latest_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_latest_grade = QLabel("Latest Grade: -")

        self.lbl_mon_dash_latest_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_latest_snapshot = QLabel("Latest Snapshot: N/A")

        self.lbl_mon_dash_latest_snapshot.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_total_snapshots = QLabel("Total Snapshots: 0")

        self.lbl_mon_dash_total_snapshots.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_timeline_entries = QLabel("Timeline Entries: 0")

        self.lbl_mon_dash_timeline_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_latest_change_count = QLabel("Latest Change Count: 0")

        self.lbl_mon_dash_latest_change_count.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_mon_dash_total_detected_changes = QLabel("Total Detected Changes: 0")

        self.lbl_mon_dash_total_detected_changes.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        mon_dash_layout.addWidget(self.lbl_mon_dash_status)

        mon_dash_layout.addWidget(self.lbl_mon_dash_enabled)

        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_score)

        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_grade)

        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_snapshot)

        mon_dash_layout.addWidget(self.lbl_mon_dash_total_snapshots)

        mon_dash_layout.addWidget(self.lbl_mon_dash_timeline_entries)

        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_change_count)

        mon_dash_layout.addWidget(self.lbl_mon_dash_total_detected_changes)

        root_layout.addWidget(mon_dash_card)

        # Alert Center Section

        ac_card = QFrame()

        ac_card.setObjectName("metricCard")

        ac_layout = QVBoxLayout(ac_card)

        ac_layout.setContentsMargins(16, 14, 16, 14)

        ac_layout.setSpacing(8)

        lbl_ac_header = QLabel("Alert Center")

        lbl_ac_header.setObjectName("sectionHeader")

        ac_layout.addWidget(lbl_ac_header)

        self.lbl_ac_total = QLabel("Total Alerts: 0")

        self.lbl_ac_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ac_active = QLabel("Active: 0")

        self.lbl_ac_active.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ac_acknowledged = QLabel("Acknowledged: 0")

        self.lbl_ac_acknowledged.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ac_dismissed = QLabel("Dismissed: 0")

        self.lbl_ac_dismissed.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        ac_layout.addWidget(self.lbl_ac_total)

        ac_layout.addWidget(self.lbl_ac_active)

        ac_layout.addWidget(self.lbl_ac_acknowledged)

        ac_layout.addWidget(self.lbl_ac_dismissed)

        self.alerts_list_container = QVBoxLayout()

        ac_layout.addLayout(self.alerts_list_container)

        root_layout.addWidget(ac_card)

        # Generated Alerts Section

        gen_card = QFrame()

        gen_card.setObjectName("metricCard")

        gen_layout = QVBoxLayout(gen_card)

        gen_layout.setContentsMargins(16, 14, 16, 14)

        gen_layout.setSpacing(8)

        lbl_gen_header = QLabel("Generated Alerts")

        lbl_gen_header.setObjectName("sectionHeader")

        gen_layout.addWidget(lbl_gen_header)

        self.lbl_gen_alerts_count = QLabel("Generated Alerts: 0")

        self.lbl_gen_alerts_count.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        gen_layout.addWidget(self.lbl_gen_alerts_count)

        self.generated_alerts_container = QVBoxLayout()

        gen_layout.addLayout(self.generated_alerts_container)

        root_layout.addWidget(gen_card)

        # Alert Rules Section

        ar_card = QFrame()

        ar_card.setObjectName("metricCard")

        ar_layout = QVBoxLayout(ar_card)

        ar_layout.setContentsMargins(16, 14, 16, 14)

        ar_layout.setSpacing(8)

        lbl_ar_header = QLabel("Alert Rules")

        lbl_ar_header.setObjectName("sectionHeader")

        ar_layout.addWidget(lbl_ar_header)

        self.lbl_alert_rules_total = QLabel("Total Rules: 0")

        self.lbl_alert_rules_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_alert_rules_triggered = QLabel("Triggered Rules: 0")

        self.lbl_alert_rules_triggered.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        ar_layout.addWidget(self.lbl_alert_rules_total)

        ar_layout.addWidget(self.lbl_alert_rules_triggered)

        self.alert_rules_list_container = QVBoxLayout()

        ar_layout.addLayout(self.alert_rules_list_container)

        root_layout.addWidget(ar_card)

        # Alert Dashboard Section

        ad_card = QFrame()

        ad_card.setObjectName("metricCard")

        ad_layout = QVBoxLayout(ad_card)

        ad_layout.setContentsMargins(16, 14, 16, 14)

        ad_layout.setSpacing(8)

        lbl_ad_header = QLabel("Alert Dashboard")

        lbl_ad_header.setObjectName("sectionHeader")

        ad_layout.addWidget(lbl_ad_header)

        self.lbl_ad_total = QLabel("Total Alerts: 0")

        self.lbl_ad_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ad_active = QLabel("Active: 0")

        self.lbl_ad_active.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ad_acknowledged = QLabel("Acknowledged: 0")

        self.lbl_ad_acknowledged.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ad_dismissed = QLabel("Dismissed: 0")

        self.lbl_ad_dismissed.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ad_info = QLabel("INFO: 0")

        self.lbl_ad_info.setStyleSheet("font-size: 14px; color: #2563eb; font-weight: 600;")

        self.lbl_ad_low = QLabel("LOW: 0")

        self.lbl_ad_low.setStyleSheet("font-size: 14px; color: #16a34a; font-weight: 600;")

        self.lbl_ad_medium = QLabel("MEDIUM: 0")

        self.lbl_ad_medium.setStyleSheet("font-size: 14px; color: #d97706; font-weight: 600;")

        self.lbl_ad_high = QLabel("HIGH: 0")

        self.lbl_ad_high.setStyleSheet("font-size: 14px; color: #dc2626; font-weight: 600;")

        self.lbl_ad_critical = QLabel("CRITICAL: 0")

        self.lbl_ad_critical.setStyleSheet("font-size: 14px; color: #dc2626; font-weight: 600;")

        ad_layout.addWidget(self.lbl_ad_total)

        ad_layout.addWidget(self.lbl_ad_active)

        ad_layout.addWidget(self.lbl_ad_acknowledged)

        ad_layout.addWidget(self.lbl_ad_dismissed)

        ad_layout.addWidget(self.lbl_ad_info)

        ad_layout.addWidget(self.lbl_ad_low)

        ad_layout.addWidget(self.lbl_ad_medium)

        ad_layout.addWidget(self.lbl_ad_high)

        ad_layout.addWidget(self.lbl_ad_critical)

        self.alert_dashboard_list_container = QVBoxLayout()

        ad_layout.addLayout(self.alert_dashboard_list_container)

        root_layout.addWidget(ad_card)

        # Alert History Section

        ah_card = QFrame()

        ah_card.setObjectName("metricCard")

        ah_layout = QVBoxLayout(ah_card)

        ah_layout.setContentsMargins(16, 14, 16, 14)

        ah_layout.setSpacing(8)

        lbl_ah_header = QLabel("Alert History")

        lbl_ah_header.setObjectName("sectionHeader")

        ah_layout.addWidget(lbl_ah_header)

        self.lbl_ah_total = QLabel("Total Entries: 0")

        self.lbl_ah_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ah_latest = QLabel("Latest: N/A")

        self.lbl_ah_latest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ah_earliest = QLabel("Earliest: N/A")

        self.lbl_ah_earliest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        ah_layout.addWidget(self.lbl_ah_total)

        ah_layout.addWidget(self.lbl_ah_latest)

        ah_layout.addWidget(self.lbl_ah_earliest)

        self.alert_history_list_container = QVBoxLayout()

        ah_layout.addLayout(self.alert_history_list_container)

        root_layout.addWidget(ah_card)

        # Alert Management Section

        am_card = QFrame()

        am_card.setObjectName("metricCard")

        am_layout = QVBoxLayout(am_card)

        am_layout.setContentsMargins(16, 14, 16, 14)

        am_layout.setSpacing(8)

        lbl_am_header = QLabel("Alert Management")

        lbl_am_header.setObjectName("sectionHeader")

        am_layout.addWidget(lbl_am_header)

        self.lbl_am_total = QLabel("Total Alerts: 0")

        self.lbl_am_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_am_active = QLabel("Active: 0")

        self.lbl_am_active.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_am_acknowledged = QLabel("Acknowledged: 0")

        self.lbl_am_acknowledged.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_am_dismissed = QLabel("Dismissed: 0")

        self.lbl_am_dismissed.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_am_last_updated = QLabel("Last Updated: N/A")

        self.lbl_am_last_updated.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        am_layout.addWidget(self.lbl_am_total)

        am_layout.addWidget(self.lbl_am_active)

        am_layout.addWidget(self.lbl_am_acknowledged)

        am_layout.addWidget(self.lbl_am_dismissed)

        am_layout.addWidget(self.lbl_am_last_updated)

        self.alert_management_list_container = QVBoxLayout()

        am_layout.addLayout(self.alert_management_list_container)

        root_layout.addWidget(am_card)

        # Decision Engine Section

        de_card = QFrame()

        de_card.setObjectName("metricCard")

        de_layout = QVBoxLayout(de_card)

        de_layout.setContentsMargins(16, 14, 16, 14)

        de_layout.setSpacing(8)

        lbl_de_header = QLabel("Decision Engine")

        lbl_de_header.setObjectName("sectionHeader")

        de_layout.addWidget(lbl_de_header)

        self.lbl_de_status = QLabel("Engine Status: READY")

        self.lbl_de_status.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_de_total = QLabel("Total Decisions: 0")

        self.lbl_de_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_de_pending = QLabel("Pending Decisions: 0")

        self.lbl_de_pending.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_de_informational = QLabel("Informational Decisions: 0")

        self.lbl_de_informational.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        de_layout.addWidget(self.lbl_de_status)

        de_layout.addWidget(self.lbl_de_total)

        de_layout.addWidget(self.lbl_de_pending)

        de_layout.addWidget(self.lbl_de_informational)

        self.decision_engine_list_container = QVBoxLayout()

        de_layout.addLayout(self.decision_engine_list_container)

        root_layout.addWidget(de_card)

        # Decision Classification Section

        dc_card = QFrame()

        dc_card.setObjectName("metricCard")

        dc_layout = QVBoxLayout(dc_card)

        dc_layout.setContentsMargins(16, 14, 16, 14)

        dc_layout.setSpacing(8)

        lbl_dc_header = QLabel("Decision Classification")

        lbl_dc_header.setObjectName("sectionHeader")

        dc_layout.addWidget(lbl_dc_header)

        self.lbl_dc_total = QLabel("Total Classifications: 0")

        self.lbl_dc_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dc_classified = QLabel("Classified: 0")

        self.lbl_dc_classified.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dc_unclassified = QLabel("Unclassified: 0")

        self.lbl_dc_unclassified.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dc_layout.addWidget(self.lbl_dc_total)

        dc_layout.addWidget(self.lbl_dc_classified)

        dc_layout.addWidget(self.lbl_dc_unclassified)

        self.decision_classification_list_container = QVBoxLayout()

        dc_layout.addLayout(self.decision_classification_list_container)

        root_layout.addWidget(dc_card)

        # Decision Prioritization Section

        dp_card = QFrame()

        dp_card.setObjectName("metricCard")

        dp_layout = QVBoxLayout(dp_card)

        dp_layout.setContentsMargins(16, 14, 16, 14)

        dp_layout.setSpacing(8)

        lbl_dp_header = QLabel("Decision Prioritization")

        lbl_dp_header.setObjectName("sectionHeader")

        dp_layout.addWidget(lbl_dp_header)

        self.lbl_dp_total = QLabel("Total Prioritized: 0")

        self.lbl_dp_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dp_critical = QLabel("Critical: 0")

        self.lbl_dp_critical.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dp_high = QLabel("High: 0")

        self.lbl_dp_high.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dp_medium = QLabel("Medium: 0")

        self.lbl_dp_medium.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dp_low = QLabel("Low: 0")

        self.lbl_dp_low.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dp_info = QLabel("Info: 0")

        self.lbl_dp_info.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dp_layout.addWidget(self.lbl_dp_total)

        dp_layout.addWidget(self.lbl_dp_critical)

        dp_layout.addWidget(self.lbl_dp_high)

        dp_layout.addWidget(self.lbl_dp_medium)

        dp_layout.addWidget(self.lbl_dp_low)

        dp_layout.addWidget(self.lbl_dp_info)

        self.decision_prioritization_list_container = QVBoxLayout()

        dp_layout.addLayout(self.decision_prioritization_list_container)

        root_layout.addWidget(dp_card)

        # ── Decision Audit Trail ──

        da_card = QFrame()

        da_card.setObjectName("metricCard")

        da_layout = QVBoxLayout(da_card)

        da_layout.setContentsMargins(16, 14, 16, 14)

        da_layout.setSpacing(8)

        lbl_da_header = QLabel("Decision Audit Trail")

        lbl_da_header.setObjectName("sectionHeader")

        da_layout.addWidget(lbl_da_header)

        self.lbl_da_total = QLabel("Total Entries: 0")

        self.lbl_da_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_da_earliest = QLabel("Earliest Entry: N/A")

        self.lbl_da_earliest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_da_latest = QLabel("Latest Entry: N/A")

        self.lbl_da_latest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        da_layout.addWidget(self.lbl_da_total)

        da_layout.addWidget(self.lbl_da_earliest)

        da_layout.addWidget(self.lbl_da_latest)

        self.decision_audit_list_container = QVBoxLayout()

        da_layout.addLayout(self.decision_audit_list_container)

        root_layout.addWidget(da_card)

        # ── Decision Audit Analytics ──

        daa_card = QFrame()

        daa_card.setObjectName("metricCard")

        daa_layout = QVBoxLayout(daa_card)

        daa_layout.setContentsMargins(16, 14, 16, 14)

        daa_layout.setSpacing(8)

        lbl_daa_header = QLabel("Decision Audit Analytics")

        lbl_daa_header.setObjectName("sectionHeader")

        daa_layout.addWidget(lbl_daa_header)

        self.lbl_daa_total = QLabel("Total Entries: 0")

        self.lbl_daa_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_unique = QLabel("Unique Decisions: 0")

        self.lbl_daa_unique.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_classified = QLabel("Classified: 0")

        self.lbl_daa_classified.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_unclassified = QLabel("Unclassified: 0")

        self.lbl_daa_unclassified.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_critical = QLabel("Critical: 0")

        self.lbl_daa_critical.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_high = QLabel("High: 0")

        self.lbl_daa_high.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_medium = QLabel("Medium: 0")

        self.lbl_daa_medium.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_low = QLabel("Low: 0")

        self.lbl_daa_low.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_daa_info = QLabel("Info: 0")

        self.lbl_daa_info.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        daa_layout.addWidget(self.lbl_daa_total)

        daa_layout.addWidget(self.lbl_daa_unique)

        daa_layout.addWidget(self.lbl_daa_classified)

        daa_layout.addWidget(self.lbl_daa_unclassified)

        daa_layout.addWidget(self.lbl_daa_critical)

        daa_layout.addWidget(self.lbl_daa_high)

        daa_layout.addWidget(self.lbl_daa_medium)

        daa_layout.addWidget(self.lbl_daa_low)

        daa_layout.addWidget(self.lbl_daa_info)

        self.decision_audit_analytics_container = QVBoxLayout()

        daa_layout.addLayout(self.decision_audit_analytics_container)

        root_layout.addWidget(daa_card)

        # ── Decision Audit Trend ──

        dat_card = QFrame()

        dat_card.setObjectName("metricCard")

        dat_layout = QVBoxLayout(dat_card)

        dat_layout.setContentsMargins(16, 14, 16, 14)

        dat_layout.setSpacing(8)

        lbl_dat_header = QLabel("Decision Audit Trend")

        lbl_dat_header.setObjectName("sectionHeader")

        dat_layout.addWidget(lbl_dat_header)

        self.lbl_dat_total_points = QLabel("Total Points: 0")

        self.lbl_dat_total_points.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dat_earliest = QLabel("Earliest Timestamp: N/A")

        self.lbl_dat_earliest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dat_latest = QLabel("Latest Timestamp: N/A")

        self.lbl_dat_latest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dat_direction = QLabel("Direction: STABLE")

        self.lbl_dat_direction.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dat_layout.addWidget(self.lbl_dat_total_points)

        dat_layout.addWidget(self.lbl_dat_earliest)

        dat_layout.addWidget(self.lbl_dat_latest)

        dat_layout.addWidget(self.lbl_dat_direction)

        self.decision_audit_trend_container = QVBoxLayout()

        dat_layout.addLayout(self.decision_audit_trend_container)

        root_layout.addWidget(dat_card)

        # ── Rebalancing Foundation ──

        reb_card = QFrame()

        reb_card.setObjectName("metricCard")

        reb_layout = QVBoxLayout(reb_card)

        reb_layout.setContentsMargins(16, 14, 16, 14)

        reb_layout.setSpacing(8)

        lbl_reb_header = QLabel("Rebalancing")

        lbl_reb_header.setObjectName("sectionHeader")

        reb_layout.addWidget(lbl_reb_header)

        self.lbl_reb_status = QLabel("Rebalancing Status: EMPTY")

        self.lbl_reb_status.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_reb_total_val = QLabel("Total Portfolio Value: $0.00")

        self.lbl_reb_total_val.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_reb_total_pos = QLabel("Total Positions: 0")

        self.lbl_reb_total_pos.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        reb_layout.addWidget(self.lbl_reb_status)

        reb_layout.addWidget(self.lbl_reb_total_val)

        reb_layout.addWidget(self.lbl_reb_total_pos)

        lbl_reb_safety = QLabel("Rebalancing foundation displays current portfolio structure only. No rebalancing action is generated.")

        lbl_reb_safety.setStyleSheet("font-size: 13px; color: #475569; font-style: italic; padding-top: 4px; padding-bottom: 4px;")

        reb_layout.addWidget(lbl_reb_safety)

        self.rebalancing_positions_container = QVBoxLayout()

        reb_layout.addLayout(self.rebalancing_positions_container)

        root_layout.addWidget(reb_card)

        # ── Allocation Analysis Engine ──

        aa_card = QFrame()

        aa_card.setObjectName("metricCard")

        aa_layout = QVBoxLayout(aa_card)

        aa_layout.setContentsMargins(16, 14, 16, 14)

        aa_layout.setSpacing(8)

        lbl_aa_header = QLabel("Allocation Analysis")

        lbl_aa_header.setObjectName("sectionHeader")

        aa_layout.addWidget(lbl_aa_header)

        self.lbl_aa_total_val = QLabel("Total Portfolio Value: $0.00")

        self.lbl_aa_total_val.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        aa_layout.addWidget(self.lbl_aa_total_val)

        lbl_aa_safety = QLabel("Allocation analysis describes current portfolio composition. Target allocation and drift analysis are handled separately.")

        lbl_aa_safety.setStyleSheet("font-size: 13px; color: #475569; font-style: italic; padding-top: 4px; padding-bottom: 4px;")

        aa_layout.addWidget(lbl_aa_safety)

        self.allocation_analysis_container = QVBoxLayout()

        aa_layout.addLayout(self.allocation_analysis_container)

        root_layout.addWidget(aa_card)

        # ── Drift Detection Engine ──

        dd_card = QFrame()

        dd_card.setObjectName("metricCard")

        dd_layout = QVBoxLayout(dd_card)

        dd_layout.setContentsMargins(16, 14, 16, 14)

        dd_layout.setSpacing(8)

        lbl_dd_header = QLabel("Drift Detection")

        lbl_dd_header.setObjectName("sectionHeader")

        dd_layout.addWidget(lbl_dd_header)

        self.lbl_dd_total_pos = QLabel("Total Positions: 0")

        self.lbl_dd_total_pos.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dd_pos_with_target = QLabel("Positions With Target: 0")

        self.lbl_dd_pos_with_target.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dd_pos_without_target = QLabel("Positions Without Target: 0")

        self.lbl_dd_pos_without_target.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dd_total_abs_drift = QLabel("Total Absolute Drift: 0.00%")

        self.lbl_dd_total_abs_drift.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dd_avg_abs_drift = QLabel("Average Absolute Drift: 0.00%")

        self.lbl_dd_avg_abs_drift.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_dd_max_abs_drift = QLabel("Maximum Absolute Drift: 0.00%")

        self.lbl_dd_max_abs_drift.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dd_layout.addWidget(self.lbl_dd_total_pos)

        dd_layout.addWidget(self.lbl_dd_pos_with_target)

        dd_layout.addWidget(self.lbl_dd_pos_without_target)

        dd_layout.addWidget(self.lbl_dd_total_abs_drift)

        dd_layout.addWidget(self.lbl_dd_avg_abs_drift)

        dd_layout.addWidget(self.lbl_dd_max_abs_drift)

        lbl_dd_safety = QLabel("Drift detection compares current allocation with configured target weights. It does not generate rebalancing recommendations.")

        lbl_dd_safety.setStyleSheet("font-size: 13px; color: #475569; font-style: italic; padding-top: 4px; padding-bottom: 4px;")

        dd_layout.addWidget(lbl_dd_safety)

        self.drift_metrics_container = QVBoxLayout()

        dd_layout.addLayout(self.drift_metrics_container)

        # Drift History Subsection

        lbl_dh_header = QLabel("Drift History")

        lbl_dh_header.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67; padding-top: 10px;")

        dd_layout.addWidget(lbl_dh_header)

        self.lbl_dh_total_entries = QLabel("Total History Entries: 0")

        self.lbl_dh_total_entries.setStyleSheet("font-size: 13px; color: #1f2937;")

        self.lbl_dh_earliest = QLabel("Earliest Timestamp: None")

        self.lbl_dh_earliest.setStyleSheet("font-size: 13px; color: #1f2937;")

        self.lbl_dh_latest = QLabel("Latest Timestamp: None")

        self.lbl_dh_latest.setStyleSheet("font-size: 13px; color: #1f2937;")

        dd_layout.addWidget(self.lbl_dh_total_entries)

        dd_layout.addWidget(self.lbl_dh_earliest)

        dd_layout.addWidget(self.lbl_dh_latest)

        self.drift_history_container = QVBoxLayout()

        dd_layout.addLayout(self.drift_history_container)

        root_layout.addWidget(dd_card)

        # ── Rebalancing Candidate Engine ──

        rc_card = QFrame()

        rc_card.setObjectName("metricCard")

        rc_layout = QVBoxLayout(rc_card)

        rc_layout.setContentsMargins(16, 14, 16, 14)

        rc_layout.setSpacing(8)

        lbl_rc_header = QLabel("Rebalancing Candidates")

        lbl_rc_header.setObjectName("sectionHeader")

        rc_layout.addWidget(lbl_rc_header)

        self.lbl_rc_total_candidates = QLabel("Total Candidates: 0")

        self.lbl_rc_total_candidates.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_rc_overweight_candidates = QLabel("Overweight Candidates: 0")

        self.lbl_rc_overweight_candidates.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_rc_underweight_candidates = QLabel("Underweight Candidates: 0")

        self.lbl_rc_underweight_candidates.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_rc_on_target_candidates = QLabel("On Target Candidates: 0")

        self.lbl_rc_on_target_candidates.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_rc_total_impact_val = QLabel("Total Impact Value: $0.00")

        self.lbl_rc_total_impact_val.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        rc_layout.addWidget(self.lbl_rc_total_candidates)

        rc_layout.addWidget(self.lbl_rc_overweight_candidates)

        rc_layout.addWidget(self.lbl_rc_underweight_candidates)

        rc_layout.addWidget(self.lbl_rc_on_target_candidates)

        rc_layout.addWidget(self.lbl_rc_total_impact_val)

        lbl_rc_safety = QLabel("Candidates identify measurable allocation differences for further evaluation. No rebalancing action is generated here.")

        lbl_rc_safety.setStyleSheet("font-size: 13px; color: #475569; font-style: italic; padding-top: 4px; padding-bottom: 4px;")

        rc_layout.addWidget(lbl_rc_safety)

        self.rebalancing_candidates_container = QVBoxLayout()

        rc_layout.addLayout(self.rebalancing_candidates_container)

        root_layout.addWidget(rc_card)

        # ── Rebalancing Recommendation Framework ──

        rr_card = QFrame()

        rr_card.setObjectName("metricCard")

        rr_layout = QVBoxLayout(rr_card)

        rr_layout.setContentsMargins(16, 14, 16, 14)

        rr_layout.setSpacing(8)

        lbl_rr_header = QLabel("Rebalancing Recommendations")

        lbl_rr_header.setObjectName("sectionHeader")

        rr_layout.addWidget(lbl_rr_header)

        self.lbl_rr_total_recommendations = QLabel("Total Recommendations: 0")

        self.lbl_rr_total_recommendations.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_rr_increase_count = QLabel("Increase: 0")

        self.lbl_rr_increase_count.setStyleSheet("font-size: 14px; color: #1f2937;")

        self.lbl_rr_decrease_count = QLabel("Decrease: 0")

        self.lbl_rr_decrease_count.setStyleSheet("font-size: 14px; color: #1f2937;")

        self.lbl_rr_maintain_count = QLabel("Maintain: 0")

        self.lbl_rr_maintain_count.setStyleSheet("font-size: 14px; color: #1f2937;")

        self.lbl_rr_high_priority_count = QLabel("High Priority: 0")

        self.lbl_rr_high_priority_count.setStyleSheet("font-size: 14px; color: #1f2937;")

        self.lbl_rr_medium_priority_count = QLabel("Medium Priority: 0")

        self.lbl_rr_medium_priority_count.setStyleSheet("font-size: 14px; color: #1f2937;")

        self.lbl_rr_low_priority_count = QLabel("Low Priority: 0")

        self.lbl_rr_low_priority_count.setStyleSheet("font-size: 14px; color: #1f2937;")

        self.lbl_rr_total_impact_val = QLabel("Total Impact Value: $0.00")

        self.lbl_rr_total_impact_val.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        rr_layout.addWidget(self.lbl_rr_total_recommendations)

        rr_layout.addWidget(self.lbl_rr_increase_count)

        rr_layout.addWidget(self.lbl_rr_decrease_count)

        rr_layout.addWidget(self.lbl_rr_maintain_count)

        rr_layout.addWidget(self.lbl_rr_high_priority_count)

        rr_layout.addWidget(self.lbl_rr_medium_priority_count)

        rr_layout.addWidget(self.lbl_rr_low_priority_count)

        rr_layout.addWidget(self.lbl_rr_total_impact_val)

        lbl_rr_boundary = QLabel("Recommendations are for review only. No transaction has been executed.")

        lbl_rr_boundary.setStyleSheet("font-size: 13px; color: #b91c1c; font-weight: 700; font-style: italic; padding-top: 4px; padding-bottom: 4px;")

        rr_layout.addWidget(lbl_rr_boundary)

        self.rebalancing_recommendations_container = QVBoxLayout()

        rr_layout.addLayout(self.rebalancing_recommendations_container)

        root_layout.addWidget(rr_card)

        # Portfolio Intelligence Section
        pi_card = QFrame()
        pi_card.setObjectName("metricCard")
        pi_layout = QVBoxLayout(pi_card)
        pi_layout.setContentsMargins(16, 14, 16, 14)
        pi_layout.setSpacing(8)

        lbl_pi_title = QLabel("PORTFOLIO INTELLIGENCE")
        lbl_pi_title.setObjectName("cardTitle")
        pi_layout.addWidget(lbl_pi_title)

        lbl_pi_status = QLabel("Intelligence Status: Active")
        lbl_pi_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")
        pi_layout.addWidget(lbl_pi_status)

        lbl_pi_summary = QLabel("Summary: Factual Portfolio Intelligence Baseline")
        lbl_pi_summary.setStyleSheet("font-size: 13px; color: #475569;")
        pi_layout.addWidget(lbl_pi_summary)

        self.portfolio_intelligence_container = QVBoxLayout()
        pi_layout.addLayout(self.portfolio_intelligence_container)

        root_layout.addWidget(pi_card)

        # Holding Quality Section
        hq_card = QFrame()
        hq_card.setObjectName("metricCard")
        hq_layout = QVBoxLayout(hq_card)
        hq_layout.setContentsMargins(16, 14, 16, 14)
        hq_layout.setSpacing(8)

        lbl_hq_title = QLabel("HOLDING QUALITY")
        lbl_hq_title.setObjectName("cardTitle")
        hq_layout.addWidget(lbl_hq_title)

        lbl_hq_info = QLabel("Factual holding quality assessment layer (Informational only — does not imply buy/sell/replace actions)")
        lbl_hq_info.setStyleSheet("font-size: 13px; color: #475569; font-style: italic;")
        hq_layout.addWidget(lbl_hq_info)

        self.holding_quality_container = QVBoxLayout()
        hq_layout.addLayout(self.holding_quality_container)

        root_layout.addWidget(hq_card)

        # SIP Optimization Section
        sip_card = QFrame()
        sip_card.setObjectName("metricCard")
        sip_layout = QVBoxLayout(sip_card)
        sip_layout.setContentsMargins(16, 14, 16, 14)
        sip_layout.setSpacing(8)

        lbl_sip_title = QLabel("SIP OPTIMIZATION ANALYSIS")
        lbl_sip_title.setObjectName("cardTitle")
        sip_layout.addWidget(lbl_sip_title)

        lbl_sip_info = QLabel("Factual SIP configuration & efficiency analysis layer (Informational only — no execution instructions)")
        lbl_sip_info.setStyleSheet("font-size: 13px; color: #475569; font-style: italic;")
        sip_layout.addWidget(lbl_sip_info)

        self.sip_optimization_container = QVBoxLayout()
        sip_layout.addLayout(self.sip_optimization_container)

        root_layout.addWidget(sip_card)

        # Portfolio Opportunities Section
        opp_card = QFrame()
        opp_card.setObjectName("metricCard")
        opp_layout = QVBoxLayout(opp_card)
        opp_layout.setContentsMargins(16, 14, 16, 14)
        opp_layout.setSpacing(8)

        lbl_opp_title = QLabel("PORTFOLIO OPPORTUNITIES")
        lbl_opp_title.setObjectName("cardTitle")
        opp_layout.addWidget(lbl_opp_title)

        lbl_opp_info = QLabel("Portfolio opportunities are analytical observations only. No investment transaction or portfolio change is executed.")
        lbl_opp_info.setStyleSheet("font-size: 13px; color: #475569; font-style: italic;")
        opp_layout.addWidget(lbl_opp_info)

        self.portfolio_opportunity_container = QVBoxLayout()
        opp_layout.addLayout(self.portfolio_opportunity_container)

        root_layout.addWidget(opp_card)

        # Portfolio Risk Intelligence Section
        risk_card = QFrame()
        risk_card.setObjectName("metricCard")
        risk_layout = QVBoxLayout(risk_card)
        risk_layout.setContentsMargins(16, 14, 16, 14)
        risk_layout.setSpacing(8)

        lbl_risk_title = QLabel("PORTFOLIO RISK INTELLIGENCE")
        lbl_risk_title.setObjectName("cardTitle")
        risk_layout.addWidget(lbl_risk_title)

        lbl_risk_info = QLabel("Portfolio Risk Intelligence provides analytical risk observations only. It does not generate investment or transaction instructions.")
        lbl_risk_info.setStyleSheet("font-size: 13px; color: #475569; font-style: italic;")
        risk_layout.addWidget(lbl_risk_info)

        self.portfolio_risk_container = QVBoxLayout()
        risk_layout.addLayout(self.portfolio_risk_container)

        root_layout.addWidget(risk_card)

        # Alpha 12 Portfolio Mapping Section
        a12_card = QFrame()
        a12_card.setObjectName("metricCard")
        a12_layout = QVBoxLayout(a12_card)
        a12_layout.setContentsMargins(16, 14, 16, 14)
        a12_layout.setSpacing(8)

        lbl_a12_title = QLabel("ALPHA 12 PORTFOLIO MAPPING")
        lbl_a12_title.setObjectName("cardTitle")
        a12_layout.addWidget(lbl_a12_title)

        lbl_a12_info = QLabel("Alpha 12 Portfolio Mapping is a read-only informational mapping layer. No challenger, replacement, or rebalancing action is executed.")
        lbl_a12_info.setStyleSheet("font-size: 13px; color: #475569; font-style: italic;")
        a12_layout.addWidget(lbl_a12_info)

        self.alpha12_mapping_container = QVBoxLayout()
        a12_layout.addLayout(self.alpha12_mapping_container)

        root_layout.addWidget(a12_card)

        # Alpha 12 Portfolio Stability Section
        a12_stab_card = QFrame()
        a12_stab_card.setObjectName("metricCard")
        a12_stab_layout = QVBoxLayout(a12_stab_card)
        a12_stab_layout.setContentsMargins(16, 14, 16, 14)
        a12_stab_layout.setSpacing(8)

        lbl_a12_stab_title = QLabel("ALPHA 12 PORTFOLIO STABILITY")
        lbl_a12_stab_title.setObjectName("cardTitle")
        a12_stab_layout.addWidget(lbl_a12_stab_title)

        lbl_a12_stab_info = QLabel("Alpha 12 Portfolio Stability is an analytical measurement only. It does not generate investment, replacement, rebalancing, or transaction instructions.")
        lbl_a12_stab_info.setStyleSheet("font-size: 13px; color: #475569; font-style: italic;")
        a12_stab_layout.addWidget(lbl_a12_stab_info)

        self.alpha12_stability_container = QVBoxLayout()
        a12_stab_layout.addLayout(self.alpha12_stability_container)

        root_layout.addWidget(a12_stab_card)

        root_layout.addStretch()

        scroll.setWidget(content_widget)

        outer_layout.addWidget(scroll)

    def _create_metric_card(self, title: str, value: str):

        card = QFrame()

        card.setObjectName("metricCard")

        layout = QVBoxLayout(card)

        layout.setContentsMargins(16, 14, 16, 14)

        layout.setSpacing(8)

        t_lbl = QLabel(title.upper())

        t_lbl.setObjectName("cardTitle")

        val_lbl = QLabel(value)

        val_lbl.setObjectName("cardValue")

        layout.addWidget(t_lbl)

        layout.addWidget(val_lbl)

        return card, val_lbl
