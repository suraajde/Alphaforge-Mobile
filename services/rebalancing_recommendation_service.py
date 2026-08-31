"""Rebalancing Recommendation Framework Service (Sprint 13.7.4)















Generates structured, explainable, and audit-integrated rebalancing recommendations







for user review from Rebalancing Candidate Engine outputs.















IMPORTANT: This service ONLY generates descriptive recommendations for review.







It NEVER places orders, executes transactions, modifies holdings, or connects to brokers.







"""







from __future__ import annotations















from dataclasses import dataclass, field







from datetime import datetime, timezone







import hashlib







from typing import Any, Optional























@dataclass







class RebalancingRecommendation:







    """Represents a structured, review-only rebalancing recommendation."""















    recommendation_id: str







    symbol: str







    name: str







    asset_type: str















    current_weight: float







    target_weight: float







    drift: float







    absolute_drift: float







    direction: str















    impact_value: float















    recommended_action: str  # "INCREASE", "DECREASE", "MAINTAIN"







    recommended_weight: float  # equals target_weight







    weight_change: float  # target_weight - current_weight















    priority: str  # "HIGH", "MEDIUM", "LOW"







    rationale: str















    candidate_score: float







    candidate_rank: int























@dataclass







class RebalancingRecommendationResult:







    """Container for complete rebalancing recommendation summary and list."""















    total_recommendations: int















    increase_count: int







    decrease_count: int







    maintain_count: int















    high_priority_count: int







    medium_priority_count: int







    low_priority_count: int















    total_impact_value: float















    recommendations: list[RebalancingRecommendation] = field(default_factory=list)























def _empty_result() -> RebalancingRecommendationResult:







    """Return a safe empty RebalancingRecommendationResult."""







    return RebalancingRecommendationResult(







        total_recommendations=0,







        increase_count=0,







        decrease_count=0,







        maintain_count=0,







        high_priority_count=0,







        medium_priority_count=0,







        low_priority_count=0,







        total_impact_value=0.0,







        recommendations=[],







    )























def _safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:







    """Safely convert value to float or return default."""







    if val is None:







        return default







    try:







        return float(val)







    except (TypeError, ValueError):







        return default























def _generate_recommendation_id(symbol: str, current_weight: float, target_weight: float, action: str) -> str:







    """Generate a deterministic sha256 hash recommendation ID."""







    raw = f"{symbol}:{current_weight:.2f}:{target_weight:.2f}:{action}"







    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]























class RebalancingRecommendationService:







    """Service for generating structured rebalancing recommendations for review.















    Operates purely as a recommendation generation and audit integration engine.







    Does NOT execute trades, modify portfolios, or interface with brokers.







    """















    def __init__(







        self,







        rebalancing_service: Optional[Any] = None,







        allocation_analysis_service: Optional[Any] = None,







        drift_detection_service: Optional[Any] = None,







        rebalancing_candidate_service: Optional[Any] = None,







        audit_service: Optional[Any] = None,







    ) -> None:







        """Initialize RebalancingRecommendationService with optional dependent services."""







        self._rebalancing_service = rebalancing_service







        self._allocation_analysis_service = allocation_analysis_service







        self._drift_detection_service = drift_detection_service







        self._rebalancing_candidate_service = rebalancing_candidate_service







        self._audit_service = audit_service















    def _get_candidate_service(self) -> Optional[Any]:







        """Safely retrieve or instantiate the RebalancingCandidateService."""







        if self._rebalancing_candidate_service is not None:







            return self._rebalancing_candidate_service







        try:







            from services.rebalancing_candidate_service import RebalancingCandidateService















            return RebalancingCandidateService(







                rebalancing_service=self._rebalancing_service,







                allocation_analysis_service=self._allocation_analysis_service,







                drift_detection_service=self._drift_detection_service,







            )







        except Exception:







            return None















    def _get_audit_service(self) -> Optional[Any]:







        """Safely retrieve injected DecisionAuditService."""







        return self._audit_service























    def generate_recommendations(







        self,







        rebalancing_state: Optional[Any] = None,







        allocation_analysis: Optional[Any] = None,







        drift_detection: Optional[Any] = None,







        candidates: Optional[Any] = None,







        timestamp: Optional[str] = None,







    ) -> RebalancingRecommendationResult:







        """Generate structured rebalancing recommendations from candidate records."""







        try:







            if candidates is None:







                return _empty_result()

















            cand_list = getattr(candidates, "candidates", []) if hasattr(candidates, "candidates") else []







            if not isinstance(cand_list, list) or not cand_list:







                return _empty_result()















            valid_candidates = [c for c in cand_list if c is not None and not isinstance(c, (str, int, float, bool))]







            if not valid_candidates:







                return _empty_result()















            recommendations: list[RebalancingRecommendation] = []







            inc_count = 0







            dec_count = 0







            maint_count = 0







            high_count = 0







            med_count = 0







            low_count = 0















            for c in valid_candidates:







                try:







                    t_wt = _safe_float(getattr(c, "target_weight", None), None)







                    if t_wt is None:







                        continue















                    sym = str(getattr(c, "symbol", "") or "").strip()







                    nm = str(getattr(c, "name", "") or sym or "Recommendation").strip()







                    atype = str(getattr(c, "asset_type", "") or "EQUITY").strip()







                    c_wt = _safe_float(getattr(c, "current_weight", None), 0.0) or 0.0







                    drift = _safe_float(getattr(c, "drift", None), c_wt - t_wt) or (c_wt - t_wt)







                    abs_drift = _safe_float(getattr(c, "absolute_drift", None), abs(drift)) or abs(drift)







                    direction = str(getattr(c, "direction", "") or "").strip().upper()







                    impact_val = _safe_float(getattr(c, "impact_value", None), 0.0) or 0.0







                    cand_score = _safe_float(getattr(c, "candidate_score", None), abs_drift) or abs_drift







                    cand_rank = int(getattr(c, "rank", 0) or 0)















                    # Action mapping







                    if direction == "UNDERWEIGHT":







                        action = "INCREASE"







                        inc_count += 1







                        rationale = f"Current allocation ({c_wt:.2f}%) is below configured target ({t_wt:.2f}%)."







                    elif direction == "OVERWEIGHT":
                        if c_wt < 30.0:
                            action = "MAINTAIN"
                            maint_count += 1
                            impact_val = 0.0
                            rationale = f"Current allocation ({c_wt:.2f}%) is in positive drift but below 30.0% trim ceiling; winner is allowed to run."
                        else:
                            action = "DECREASE"
                            dec_count += 1
                            rationale = f"Current allocation ({c_wt:.2f}%) exceeds 30.0% trim ceiling; partial trim to baseline target ({t_wt:.2f}%)."















                    else:







                        action = "MAINTAIN"







                        maint_count += 1







                        rationale = f"Current allocation ({c_wt:.2f}%) matches configured target ({t_wt:.2f}%)."















                    rec_wt = t_wt







                    wt_change = t_wt - c_wt















                    # Priority classification







                    if abs_drift >= 10.0:







                        priority = "HIGH"







                        high_count += 1







                    elif abs_drift >= 5.0:







                        priority = "MEDIUM"







                        med_count += 1







                    else:







                        priority = "LOW"







                        low_count += 1















                    rec_id = _generate_recommendation_id(sym, c_wt, t_wt, action)















                    recommendations.append(







                        RebalancingRecommendation(







                            recommendation_id=rec_id,







                            symbol=sym or nm,







                            name=nm,







                            asset_type=atype,







                            current_weight=round(c_wt, 2),







                            target_weight=round(t_wt, 2),







                            drift=round(drift, 2),







                            absolute_drift=round(abs_drift, 2),







                            direction=direction or "ON_TARGET",







                            impact_value=round(impact_val, 2),







                            recommended_action=action,







                            recommended_weight=round(rec_wt, 2),







                            weight_change=round(wt_change, 2),







                            priority=priority,







                            rationale=rationale,







                            candidate_score=round(cand_score, 2),







                            candidate_rank=cand_rank,







                        )







                    )







                except Exception:







                    continue















            if not recommendations:







                return _empty_result()















            # Priority map for sorting







            prio_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}







            recommendations.sort(key=lambda r: (prio_order.get(r.priority, 3), -r.candidate_score, r.symbol))















            tot_impact = round(sum(r.impact_value for r in recommendations), 2)















            res = RebalancingRecommendationResult(







                total_recommendations=len(recommendations),







                increase_count=inc_count,







                decrease_count=dec_count,







                maintain_count=maint_count,







                high_priority_count=high_count,







                medium_priority_count=med_count,







                low_priority_count=low_count,







                total_impact_value=tot_impact,







                recommendations=recommendations,







            )















            # Record audit representation







            self.record_audit(res, timestamp=timestamp)















            return res







        except Exception:







            return _empty_result()















    def get_recommendations(self) -> RebalancingRecommendationResult:







        """Fetch upstream candidates and generate recommendations safely."""







        try:







            cand_svc = self._get_candidate_service()







            if cand_svc is not None and hasattr(cand_svc, "get_candidates"):







                cands = cand_svc.get_candidates()







                return self.generate_recommendations(candidates=cands)







            return _empty_result()







        except Exception:







            return _empty_result()















    def record_audit(







        self,







        recommendation_result: Optional[RebalancingRecommendationResult],







        timestamp: Optional[str] = None,







    ) -> None:







        """Integrate recommendations into the Decision Audit Trail architecture safely."""







        try:







            if recommendation_result is None or not recommendation_result.recommendations:







                return















            audit_svc = self._get_audit_service()







            if audit_svc is None or not hasattr(audit_svc, "load_audit") or not hasattr(audit_svc, "save_audit"):







                return















            trail = audit_svc.load_audit()







            if trail is None or not hasattr(trail, "entries"):







                return















            ts = timestamp or datetime.now(timezone.utc).isoformat()







            existing_ids = {getattr(e, "audit_id", "") for e in trail.entries if hasattr(e, "audit_id")}















            from services.decision_audit_service import DecisionAuditEntry















            new_entries: list[DecisionAuditEntry] = []







            for rec in recommendation_result.recommendations:







                audit_id = f"aud_rec_{rec.recommendation_id}"







                if audit_id in existing_ids:







                    continue















                entry = DecisionAuditEntry(







                    audit_id=audit_id,







                    timestamp=ts,







                    decision_id=rec.recommendation_id,







                    category="REBALANCING_RECOMMENDATION",







                    classification_status=f"ACTION_{rec.recommended_action}",







                    priority=rec.priority,







                    description=f"Recommendation for {rec.symbol} ({rec.name}): {rec.recommended_action}. {rec.rationale}",







                    source="RebalancingRecommendationService",







                )







                new_entries.append(entry)















            if new_entries:







                trail.entries.extend(new_entries)







                trail.entries.sort(key=lambda e: e.timestamp)







                trail.total_entries = len(trail.entries)







                trail.earliest_timestamp = trail.entries[0].timestamp if trail.entries else None







                trail.latest_timestamp = trail.entries[-1].timestamp if trail.entries else None







                audit_svc.save_audit(trail)







        except Exception:







            pass
