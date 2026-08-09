"""Portfolio Risk Intelligence Service (Sprint 13.8.4)

Provides a structured, factual, deterministic Portfolio Risk Intelligence layer for AlphaForge portfolios.
Measures portfolio concentration, allocation imbalance, diversification structure, and drift severity
from existing repository data.

IMPORTANT SCOPE BOUNDARY & ANALYTICAL BOUNDARY:
- Strictly an analytical intelligence layer only.
- A risk score is an analytical measurement only. It is NEVER presented as a probability of loss, expected return, investment recommendation, or trading conviction.
- NO buy, sell, hold, replacement, or rebalancing recommendations.
- NO portfolio mutations, SIP modifications, trade execution, or broker integrations.
- NO unsupported predictive market modeling or Monte Carlo forecasts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Optional


@dataclass
class RiskAssessment:
    """Factual record representing a single portfolio risk assessment."""

    risk_id: str
    symbol: str
    name: str
    asset_type: str
    risk_type: str  # CONCENTRATION, ALLOCATION, DIVERSIFICATION, DRIFT, STRUCTURE
    risk_score: float = 0.0
    risk_level: str = "UNAVAILABLE"  # HIGH, MEDIUM, LOW, INFO, UNAVAILABLE
    assessment_status: str = "UNAVAILABLE"  # ASSESSED, UNAVAILABLE, UNSUPPORTED
    current_weight: float = 0.0
    target_weight: float = 0.0
    drift: float = 0.0
    evidence: list[str] = field(default_factory=list)
    rationale: str = ""
    source: str = ""  # PORTFOLIO_STATE, REBALANCING_SERVICE, ALLOCATION_ANALYSIS, DRIFT_DETECTION, HOLDING_QUALITY


@dataclass
class PortfolioRiskSummary:
    """Summary metrics container for portfolio risk intelligence."""

    total_assessments: int = 0
    assessed_count: int = 0
    unavailable_count: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    info_count: int = 0
    average_risk_score: float = 0.0
    highest_risk_score: float = 0.0
    largest_position_weight: float = 0.0
    position_count: int = 0
    diversification_status: str = "UNAVAILABLE"  # DIVERSIFIED, MODERATE, CONCENTRATED, UNAVAILABLE


@dataclass
class RiskHistoryEntry:
    """Factual historical snapshot entry for portfolio risk tracking."""

    timestamp: str
    average_risk_score: float = 0.0
    highest_risk_score: float = 0.0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    position_count: int = 0
    largest_position_weight: float = 0.0


@dataclass
class RiskHistory:
    """Historical collection container for risk tracking entries."""

    total_entries: int = 0
    earliest_timestamp: Optional[str] = None
    latest_timestamp: Optional[str] = None
    entries: list[RiskHistoryEntry] = field(default_factory=list)


@dataclass
class PortfolioRiskResult:
    """Container for complete portfolio risk intelligence analysis."""

    analysis_status: str = "UNAVAILABLE"  # ANALYZED, NO_DATA, UNAVAILABLE, ERROR
    summary: PortfolioRiskSummary = field(default_factory=PortfolioRiskSummary)
    assessments: list[RiskAssessment] = field(default_factory=list)
    history: Optional[RiskHistory] = None
    latest_timestamp: Optional[str] = None
    rationale: str = ""


def _empty_summary(status: str = "UNAVAILABLE") -> PortfolioRiskSummary:
    """Return a safe empty summary."""
    return PortfolioRiskSummary(
        total_assessments=0,
        assessed_count=0,
        unavailable_count=0,
        high_risk_count=0,
        medium_risk_count=0,
        low_risk_count=0,
        info_count=0,
        average_risk_score=0.0,
        highest_risk_score=0.0,
        largest_position_weight=0.0,
        position_count=0,
        diversification_status=status,
    )


def _empty_result(status: str = "UNAVAILABLE", rationale: str = "") -> PortfolioRiskResult:
    """Return a safe empty result."""
    return PortfolioRiskResult(
        analysis_status=status,
        summary=_empty_summary(status=status),
        assessments=[],
        history=RiskHistory(),
        latest_timestamp=None,
        rationale=rationale,
    )


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


from config.path_config import get_data_path


class PortfolioRiskIntelligenceService:
    """Service layer for performing factual risk assessment, scoring, and history tracking."""

    _DEFAULT_STORAGE = get_data_path("intelligence/portfolio_risk_history.json")

    def __init__(
        self,
        portfolio_intelligence_service: Optional[Any] = None,
        holding_quality_service: Optional[Any] = None,
        rebalancing_service: Optional[Any] = None,
        allocation_analysis_service: Optional[Any] = None,
        drift_detection_service: Optional[Any] = None,
        storage_path: Optional[Any] = None,
    ) -> None:
        """Initialize PortfolioRiskIntelligenceService with Pattern A optional dependencies."""
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._holding_quality_service = holding_quality_service
        self._rebalancing_service = rebalancing_service
        self._allocation_analysis_service = allocation_analysis_service
        self._drift_detection_service = drift_detection_service
        self._storage_path = Path(storage_path) if storage_path is not None else self._DEFAULT_STORAGE

    def _get_portfolio_state(self) -> Optional[dict]:
        """Safely load portfolio state dictionary."""
        try:
            from services.portfolio_state_service import PortfolioStateService
            state_svc = PortfolioStateService()
            return state_svc.load_state()
        except Exception:
            return None

    def _get_rebalancing_state(self) -> Optional[Any]:
        """Safely retrieve rebalancing state."""
        if self._rebalancing_service is not None and hasattr(self._rebalancing_service, "get_rebalancing_state"):
            try:
                return self._rebalancing_service.get_rebalancing_state()
            except Exception:
                pass
        try:
            from services.rebalancing_service import RebalancingService
            reb_svc = RebalancingService()
            return reb_svc.get_rebalancing_state()
        except Exception:
            return None

    def _get_allocation_analysis(self) -> Optional[Any]:
        """Safely retrieve allocation analysis result."""
        if self._allocation_analysis_service is not None and hasattr(self._allocation_analysis_service, "analyze_allocation"):
            try:
                return self._allocation_analysis_service.analyze_allocation()
            except Exception:
                pass
        try:
            from services.allocation_analysis_service import AllocationAnalysisService
            alloc_svc = AllocationAnalysisService()
            return alloc_svc.analyze_allocation()
        except Exception:
            return None

    def _get_drift_result(self) -> Optional[Any]:
        """Safely retrieve drift detection result."""
        if self._drift_detection_service is not None and hasattr(self._drift_detection_service, "detect_drift"):
            try:
                return self._drift_detection_service.detect_drift()
            except Exception:
                pass
        try:
            from services.drift_detection_service import DriftDetectionService
            drift_svc = DriftDetectionService()
            return drift_svc.detect_drift()
        except Exception:
            return None

    def _get_holding_quality_result(self) -> Optional[Any]:
        """Safely retrieve holding quality result."""
        if self._holding_quality_service is not None and hasattr(self._holding_quality_service, "assess_holdings"):
            try:
                return self._holding_quality_service.assess_holdings()
            except Exception:
                pass
        try:
            from services.holding_quality_service import HoldingQualityService
            hq_svc = HoldingQualityService()
            return hq_svc.assess_holdings()
        except Exception:
            return None

    def _score_risk(
        self,
        risk_type: str,
        current_weight: float,
        target_weight: float,
        drift: float,
        extra_val: float = 0.0,
    ) -> float:
        """Compute transparent, deterministic 0-100 risk score based only on factual repository evidence."""
        raw_score = 0.0

        if risk_type == "CONCENTRATION":
            # Concentration score scales with position weight: <10% low, 10-20% medium, >=20% high
            if current_weight >= 20.0:
                raw_score = 70.0 + min((current_weight - 20.0) * 1.5, 30.0)
            elif current_weight >= 10.0:
                raw_score = 40.0 + ((current_weight - 10.0) / 10.0) * 29.0
            else:
                raw_score = min(current_weight * 3.5, 39.0)

        elif risk_type == "ALLOCATION":
            # Allocation gap severity relative to target
            abs_drift = abs(drift)
            raw_score = min(abs_drift * 7.5 + (current_weight * 1.5), 100.0)

        elif risk_type == "DIVERSIFICATION":
            # Diversification risk scales inversely with position count / category count
            # low position count (e.g. < 5) produces higher risk score
            pos_count = extra_val
            if pos_count < 5:
                raw_score = 75.0 + max(0.0, (5 - pos_count) * 5.0)
            elif pos_count < 10:
                raw_score = 45.0 + ((10 - pos_count) / 5.0) * 24.0
            else:
                raw_score = max(5.0, 35.0 - (pos_count - 10) * 2.0)

        elif risk_type == "DRIFT":
            # Upstream drift severity
            abs_drift = abs(drift)
            raw_score = min(abs_drift * 8.0, 100.0)

        elif risk_type == "STRUCTURE":
            # Composition / concentration risk factor
            raw_score = min(max(0.0, extra_val), 100.0)

        else:
            raw_score = 25.0

        return max(0.0, min(100.0, round(float(raw_score), 2)))

    def _classify_risk_level(self, risk_score: float, status: str = "ASSESSED") -> str:
        """Classify deterministic risk level from score: HIGH (>=70), MEDIUM (40-69), LOW (<40), INFO, UNAVAILABLE."""
        if status != "ASSESSED":
            return "UNAVAILABLE"
        if risk_score >= 70.0:
            return "HIGH"
        elif risk_score >= 40.0:
            return "MEDIUM"
        else:
            return "LOW"

    def _sort_assessments(self, assessments: list[RiskAssessment]) -> list[RiskAssessment]:
        """Deterministically sort assessments: Risk Level desc, Score desc, Symbol asc, Risk ID asc."""
        level_map = {"HIGH": 5, "MEDIUM": 4, "LOW": 3, "INFO": 2, "UNAVAILABLE": 1}

        def sort_key(item: RiskAssessment):
            l_val = level_map.get(str(item.risk_level).upper(), 0)
            return (-l_val, -item.risk_score, item.symbol.upper(), item.risk_id.upper())

        return sorted(assessments, key=sort_key)

    def _assess_concentration(self, positions_dict: dict) -> list[RiskAssessment]:
        """Assess position concentration risk across portfolio holdings."""
        assessments: list[RiskAssessment] = []
        if not isinstance(positions_dict, dict) or not positions_dict:
            return assessments

        for symbol, pos in positions_dict.items():
            if not isinstance(pos, dict):
                continue
            c_weight = _safe_float(pos.get("actual_weight", pos.get("current_weight")), 0.0)
            t_weight = _safe_float(pos.get("target_weight"), 0.0)
            drift = _safe_float(pos.get("drift_pct", c_weight - t_weight), 0.0)
            name = str(pos.get("company_name", pos.get("name", symbol))).strip()
            atype = str(pos.get("category", pos.get("asset_type", "EQUITY"))).strip()

            # Create concentration assessment if current weight >= 5.0%
            if c_weight >= 5.0:
                score = self._score_risk("CONCENTRATION", c_weight, t_weight, drift)
                level = self._classify_risk_level(score, status="ASSESSED")

                ev = [
                    f"Current position weight: {c_weight:.2f}%",
                    f"Target weight: {t_weight:.2f}%",
                    f"Concentration category: {level} risk threshold",
                ]
                rat = f"Position {symbol} holds {c_weight:.2f}% of total portfolio value."

                assessments.append(
                    RiskAssessment(
                        risk_id=f"RISK_CONC_{symbol.upper()}",
                        symbol=symbol.upper(),
                        name=name,
                        asset_type=atype,
                        risk_type="CONCENTRATION",
                        risk_score=score,
                        risk_level=level,
                        assessment_status="ASSESSED",
                        current_weight=round(c_weight, 4),
                        target_weight=round(t_weight, 4),
                        drift=round(drift, 4),
                        evidence=ev,
                        rationale=rat,
                        source="PORTFOLIO_STATE",
                    )
                )

        return assessments

    def _assess_allocation(
        self,
        positions_dict: dict,
        alloc_res: Optional[Any],
    ) -> list[RiskAssessment]:
        """Assess allocation concentration/imbalance from positions and AllocationAnalysisResult."""
        assessments: list[RiskAssessment] = []
        if not isinstance(positions_dict, dict):
            return assessments

        for symbol, pos in positions_dict.items():
            if not isinstance(pos, dict):
                continue
            c_weight = _safe_float(pos.get("actual_weight", pos.get("current_weight")), 0.0)
            t_weight = _safe_float(pos.get("target_weight"), 0.0)
            drift = _safe_float(pos.get("drift_pct", c_weight - t_weight), 0.0)

            # Allocation risk if target > 0 and drift >= 3.0%
            if t_weight > 0 and abs(drift) >= 3.0:
                name = str(pos.get("company_name", pos.get("name", symbol))).strip()
                atype = str(pos.get("category", pos.get("asset_type", "EQUITY"))).strip()
                direction = "OVERWEIGHT" if drift > 0 else "UNDERWEIGHT"

                score = self._score_opportunity_risk = self._score_risk("ALLOCATION", c_weight, t_weight, drift)
                level = self._classify_risk_level(score, status="ASSESSED")

                ev = [
                    f"Current weight is {c_weight:.2f}% versus configured target {t_weight:.2f}%",
                    f"Allocation drift: {drift:+.2f}% ({direction})",
                ]
                rat = f"Factual allocation imbalance of {drift:+.2f}% observed for {symbol}."

                assessments.append(
                    RiskAssessment(
                        risk_id=f"RISK_ALLOC_{symbol.upper()}",
                        symbol=symbol.upper(),
                        name=name,
                        asset_type=atype,
                        risk_type="ALLOCATION",
                        risk_score=score,
                        risk_level=level,
                        assessment_status="ASSESSED",
                        current_weight=round(c_weight, 4),
                        target_weight=round(t_weight, 4),
                        drift=round(drift, 4),
                        evidence=ev,
                        rationale=rat,
                        source="ALLOCATION_ANALYSIS",
                    )
                )

        return assessments

    def _assess_diversification(self, positions_dict: dict) -> list[RiskAssessment]:
        """Assess overall portfolio diversification based on position count and value spread."""
        assessments: list[RiskAssessment] = []
        if not isinstance(positions_dict, dict) or not positions_dict:
            return assessments

        pos_count = len(positions_dict)
        top_weight = max((_safe_float(p.get("actual_weight", p.get("current_weight"))) for p in positions_dict.values() if isinstance(p, dict)), default=0.0)

        score = self._score_risk("DIVERSIFICATION", top_weight, 0.0, 0.0, extra_val=float(pos_count))
        level = self._classify_risk_level(score, status="ASSESSED")

        ev = [
            f"Total portfolio position count: {pos_count}",
            f"Largest single position weight: {top_weight:.2f}%",
            f"Diversification status: {'CONCENTRATED' if pos_count < 5 else 'MODERATE' if pos_count < 10 else 'DIVERSIFIED'}",
        ]
        rat = f"Portfolio contains {pos_count} positions with top position representing {top_weight:.2f}%."

        assessments.append(
            RiskAssessment(
                risk_id="RISK_DIVERSIFICATION_PORTFOLIO",
                symbol="PORTFOLIO",
                name="Overall Portfolio",
                asset_type="PORTFOLIO",
                risk_type="DIVERSIFICATION",
                risk_score=score,
                risk_level=level,
                assessment_status="ASSESSED",
                current_weight=100.0,
                target_weight=100.0,
                drift=0.0,
                evidence=ev,
                rationale=rat,
                source="PORTFOLIO_STATE",
            )
        )

        return assessments

    def _assess_drift(
        self,
        positions_dict: dict,
        drift_res: Optional[Any],
    ) -> list[RiskAssessment]:
        """Assess drift severity using DriftDetectionResult metrics."""
        assessments: list[RiskAssessment] = []
        if drift_res is None or not hasattr(drift_res, "metrics"):
            return assessments

        metrics = getattr(drift_res, "metrics", [])
        if not isinstance(metrics, list):
            return assessments

        for dm in metrics:
            if not hasattr(dm, "name"):
                continue
            name = str(getattr(dm, "name", "")).strip()
            c_weight = _safe_float(getattr(dm, "current_weight", 0.0))
            t_weight = _safe_float(getattr(dm, "target_weight", 0.0))
            drift = _safe_float(getattr(dm, "drift", 0.0))
            abs_drift = _safe_float(getattr(dm, "absolute_drift", abs(drift)))
            direction = str(getattr(dm, "direction", "ON_TARGET"))

            if abs_drift >= 2.0:
                score = self._score_risk("DRIFT", c_weight, t_weight, drift)
                level = self._classify_risk_level(score, status="ASSESSED")

                ev = [
                    f"Measured absolute drift: {abs_drift:.2f}%",
                    f"Direction: {direction}",
                    f"Current weight: {c_weight:.2f}% | Target weight: {t_weight:.2f}%",
                ]
                rat = f"Holding {name} exhibits factual target drift of {drift:+.2f}% ({direction})."

                assessments.append(
                    RiskAssessment(
                        risk_id=f"RISK_DRIFT_{name.upper().replace(' ', '_')}",
                        symbol=name.upper(),
                        name=name,
                        asset_type="EQUITY",
                        risk_type="DRIFT",
                        risk_score=score,
                        risk_level=level,
                        assessment_status="ASSESSED",
                        current_weight=round(c_weight, 4),
                        target_weight=round(t_weight, 4),
                        drift=round(drift, 4),
                        evidence=ev,
                        rationale=rat,
                        source="DRIFT_DETECTION",
                    )
                )

        return assessments

    def _assess_structure(
        self,
        positions_dict: dict,
    ) -> list[RiskAssessment]:
        """Assess broad structural portfolio characteristics (e.g. category concentration)."""
        assessments: list[RiskAssessment] = []
        if not isinstance(positions_dict, dict) or not positions_dict:
            return assessments

        cat_weights: dict[str, float] = {}
        for pos in positions_dict.values():
            if isinstance(pos, dict):
                cat = str(pos.get("category", "UNKNOWN")).strip().upper()
                w = _safe_float(pos.get("actual_weight", pos.get("current_weight")), 0.0)
                cat_weights[cat] = cat_weights.get(cat, 0.0) + w

        top_cat, top_cat_weight = max(cat_weights.items(), key=lambda x: x[1], default=("UNKNOWN", 0.0))

        if top_cat_weight >= 30.0:
            score = self._score_risk("STRUCTURE", top_cat_weight, 0.0, 0.0, extra_val=top_cat_weight)
            level = self._classify_risk_level(score, status="ASSESSED")

            ev = [
                f"Dominant asset category: {top_cat}",
                f"Category weight concentration: {top_cat_weight:.2f}%",
                f"Total categories present: {len(cat_weights)}",
            ]
            rat = f"Category '{top_cat}' represents {top_cat_weight:.2f}% of overall portfolio composition."

            assessments.append(
                RiskAssessment(
                    risk_id=f"RISK_STRUCT_{top_cat}",
                    symbol=top_cat,
                    name=f"Category {top_cat}",
                    asset_type="CATEGORY",
                    risk_type="STRUCTURE",
                    risk_score=score,
                    risk_level=level,
                    assessment_status="ASSESSED",
                    current_weight=round(top_cat_weight, 4),
                    target_weight=0.0,
                    drift=0.0,
                    evidence=ev,
                    rationale=rat,
                    source="PORTFOLIO_STATE",
                )
            )

        return assessments

    def build_summary(
        self,
        assessments: list[RiskAssessment],
        position_count: int = 0,
        largest_position_weight: float = 0.0,
    ) -> PortfolioRiskSummary:
        """Compute summary statistics for risk assessments."""
        if not isinstance(assessments, list) or not assessments:
            div_status = "CONCENTRATED" if position_count < 5 else "MODERATE" if position_count < 10 else "DIVERSIFIED" if position_count > 0 else "UNAVAILABLE"
            return PortfolioRiskSummary(
                total_assessments=0,
                assessed_count=0,
                unavailable_count=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                info_count=0,
                average_risk_score=0.0,
                highest_risk_score=0.0,
                largest_position_weight=round(largest_position_weight, 2),
                position_count=position_count,
                diversification_status=div_status,
            )

        total = len(assessments)
        assessed = sum(1 for a in assessments if str(getattr(a, "assessment_status", "")).upper() == "ASSESSED")
        unavail = total - assessed

        high = sum(1 for a in assessments if str(getattr(a, "risk_level", "")).upper() == "HIGH")
        med = sum(1 for a in assessments if str(getattr(a, "risk_level", "")).upper() == "MEDIUM")
        low = sum(1 for a in assessments if str(getattr(a, "risk_level", "")).upper() == "LOW")
        info = sum(1 for a in assessments if str(getattr(a, "risk_level", "")).upper() == "INFO")

        scores = [_safe_float(getattr(a, "risk_score", 0.0)) for a in assessments]
        avg_score = (sum(scores) / total) if total > 0 else 0.0
        hi_score = max(scores, default=0.0)

        div_status = "CONCENTRATED" if position_count < 5 else "MODERATE" if position_count < 10 else "DIVERSIFIED"

        return PortfolioRiskSummary(
            total_assessments=total,
            assessed_count=assessed,
            unavailable_count=unavail,
            high_risk_count=high,
            medium_risk_count=med,
            low_risk_count=low,
            info_count=info,
            average_risk_score=round(avg_score, 2),
            highest_risk_score=round(hi_score, 2),
            largest_position_weight=round(largest_position_weight, 2),
            position_count=position_count,
            diversification_status=div_status,
        )

    def analyze_risk(
        self,
        state_input: Optional[Any] = None,
    ) -> PortfolioRiskResult:
        """Main entry point to perform portfolio risk intelligence analysis defensively."""
        try:
            state = None
            if isinstance(state_input, dict):
                state = state_input
            elif state_input is not None and hasattr(state_input, "get") and callable(state_input.get):
                state = state_input
            else:
                state = self._get_portfolio_state()

            if not isinstance(state, dict) or not state:
                return _empty_result(
                    status="UNAVAILABLE",
                    rationale="No valid portfolio state available for Risk Intelligence analysis.",
                )

            raw_positions = state.get("positions")
            if not isinstance(raw_positions, dict):
                return _empty_result(
                    status="NO_DATA",
                    rationale="Portfolio contains no position dictionary to analyze.",
                )

            positions_dict = {k: v for k, v in raw_positions.items() if isinstance(v, dict)}
            if not positions_dict:
                return _empty_result(
                    status="NO_DATA",
                    rationale="Portfolio contains no valid position entries to analyze.",
                )

            alloc_res = self._get_allocation_analysis()
            drift_res = self._get_drift_result()

            raw_assessments: list[RiskAssessment] = []
            raw_assessments.extend(self._assess_concentration(positions_dict))
            raw_assessments.extend(self._assess_allocation(positions_dict, alloc_res))
            raw_assessments.extend(self._assess_diversification(positions_dict))
            raw_assessments.extend(self._assess_drift(positions_dict, drift_res))
            raw_assessments.extend(self._assess_structure(positions_dict))

            # Deduplicate by risk_id
            seen = set()
            unique_assessments = []
            for item in raw_assessments:
                if item.risk_id not in seen:
                    seen.add(item.risk_id)
                    unique_assessments.append(item)

            sorted_assessments = self._sort_assessments(unique_assessments)

            pos_count = len(positions_dict)
            top_w = max((_safe_float(p.get("actual_weight", p.get("current_weight"))) for p in positions_dict.values() if isinstance(p, dict)), default=0.0)

            summary = self.build_summary(
                sorted_assessments,
                position_count=pos_count,
                largest_position_weight=top_w,
            )

            now_str = datetime.now(timezone.utc).isoformat()
            status = "ANALYZED" if sorted_assessments else "NO_DATA"
            rat = (
                f"Evaluated {len(sorted_assessments)} risk assessments across {pos_count} positions."
                if sorted_assessments
                else "No risk assessments generated."
            )

            result = PortfolioRiskResult(
                analysis_status=status,
                summary=summary,
                assessments=sorted_assessments,
                history=None,  # Will be attached below after recording
                latest_timestamp=now_str,
                rationale=rat,
            )

            # Record snapshot entry in history and attach
            self.record_history(result=result, timestamp=now_str)
            result.history = self.load_history()

            return result

        except Exception as exc:
            return _empty_result(
                status="ERROR",
                rationale=f"Error performing risk intelligence analysis: {str(exc)}",
            )

    def get_risk(
        self,
        state_input: Optional[Any] = None,
    ) -> PortfolioRiskResult:
        """Alias interface for fetching portfolio risk intelligence result."""
        return self.analyze_risk(state_input=state_input)

    def load_history(self) -> RiskHistory:
        """Safely load risk history snapshot entries from storage in chronological order (OLDEST -> NEWEST)."""
        try:
            if not self._storage_path.exists():
                return RiskHistory()
            content = self._storage_path.read_text(encoding="utf-8").strip()
            if not content:
                return RiskHistory()
            data = json.loads(content)
            if not isinstance(data, list):
                return RiskHistory()

            entries: list[RiskHistoryEntry] = []
            for item in data:
                if isinstance(item, dict) and "timestamp" in item:
                    entries.append(
                        RiskHistoryEntry(
                            timestamp=str(item.get("timestamp")),
                            average_risk_score=_safe_float(item.get("average_risk_score")),
                            highest_risk_score=_safe_float(item.get("highest_risk_score")),
                            high_risk_count=_safe_int(item.get("high_risk_count")),
                            medium_risk_count=_safe_int(item.get("medium_risk_count")),
                            low_risk_count=_safe_int(item.get("low_risk_count")),
                            position_count=_safe_int(item.get("position_count")),
                            largest_position_weight=_safe_float(item.get("largest_position_weight")),
                        )
                    )

            # Ensure chronological sorting: OLDEST -> NEWEST
            entries.sort(key=lambda e: e.timestamp)

            if not entries:
                return RiskHistory()

            return RiskHistory(
                total_entries=len(entries),
                earliest_timestamp=entries[0].timestamp,
                latest_timestamp=entries[-1].timestamp,
                entries=entries,
            )

        except Exception:
            return RiskHistory()

    def save_history(self, history: Any) -> bool:
        """Safely write RiskHistory container or list to disk."""
        try:
            entries = []
            if isinstance(history, RiskHistory):
                entries = [asdict(e) for e in history.entries]
            elif isinstance(history, list):
                for item in history:
                    if isinstance(item, RiskHistoryEntry):
                        entries.append(asdict(item))
                    elif isinstance(item, dict):
                        entries.append(item)

            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._storage_path.with_suffix(self._storage_path.suffix + ".tmp")
            temp_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
            temp_path.replace(self._storage_path)

            return True

        except Exception:
            return False

    def record_history(
        self,
        result: Optional[Any] = None,
        timestamp: Optional[str] = None,
    ) -> bool:
        """Record snapshot entry to risk history defensively, preventing duplicate timestamps."""
        try:
            if result is None or not hasattr(result, "summary"):
                return False

            summary = getattr(result, "summary", None)
            if summary is None:
                return False

            ts = timestamp or getattr(result, "latest_timestamp", None) or datetime.now(timezone.utc).isoformat()

            existing_history = self.load_history()
            existing_entries = list(existing_history.entries)

            # Prevent duplicate timestamp entries
            if any(e.timestamp == ts for e in existing_entries):
                return True

            new_entry = RiskHistoryEntry(
                timestamp=ts,
                average_risk_score=_safe_float(getattr(summary, "average_risk_score", 0.0)),
                highest_risk_score=_safe_float(getattr(summary, "highest_opportunity_score", getattr(summary, "highest_risk_score", 0.0))),
                high_risk_count=_safe_int(getattr(summary, "high_risk_count", 0)),
                medium_risk_count=_safe_int(getattr(summary, "medium_risk_count", 0)),
                low_risk_count=_safe_int(getattr(summary, "low_risk_count", 0)),
                position_count=_safe_int(getattr(summary, "position_count", 0)),
                largest_position_weight=_safe_float(getattr(summary, "largest_position_weight", 0.0)),
            )

            existing_entries.append(new_entry)
            updated_history = RiskHistory(
                total_entries=len(existing_entries),
                earliest_timestamp=existing_entries[0].timestamp,
                latest_timestamp=existing_entries[-1].timestamp,
                entries=existing_entries,
            )

            return self.save_history(updated_history)

        except Exception:
            return False
