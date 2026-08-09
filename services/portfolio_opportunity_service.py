"""Portfolio Opportunity Engine Service (Sprint 13.8.3)

Provides a structured, factual, deterministic analytical layer that identifies potentially notable
portfolio opportunities from information already available inside AlphaForge.

CRITICAL SCOPE BOUNDARY & ANALYTICAL BOUNDARY:
- Strictly an analytical intelligence layer only.
- An "opportunity" is a factual analytical observation, NOT an instruction to buy, sell, hold, replace, or rebalance.
- NO buy, sell, hold, or replacement recommendations.
- NO automatic portfolio or SIP changes.
- NO trade execution, broker integration, price targets, or AI-generated investment decisions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Optional


@dataclass
class OpportunityRecord:
    """Factual analytical record representing a single portfolio opportunity observation."""

    opportunity_id: str
    symbol: str
    name: str
    asset_type: str
    opportunity_type: str  # ALLOCATION_GAP, QUALITY_ALIGNMENT, SIP_COVERAGE, PORTFOLIO_STRUCTURE
    opportunity_score: float = 0.0
    opportunity_status: str = "UNAVAILABLE"  # IDENTIFIED, UNAVAILABLE
    priority: str = "LOW"  # HIGH, MEDIUM, LOW
    evidence: list[str] = field(default_factory=list)
    rationale: str = ""
    source: str = ""  # PORTFOLIO_STATE, HOLDING_QUALITY, SIP_OPTIMIZATION, DRIFT_DETECTION, ALLOCATION_ANALYSIS
    current_weight: float = 0.0
    target_weight: float = 0.0
    drift: float = 0.0
    quality_score: float = 0.0
    sip_coverage: float = 0.0


@dataclass
class PortfolioOpportunitySummary:
    """Summary metrics container for identified portfolio opportunities."""

    total_opportunities: int = 0
    high_priority_count: int = 0
    medium_priority_count: int = 0
    low_priority_count: int = 0
    assessed_count: int = 0
    unavailable_count: int = 0
    average_opportunity_score: float = 0.0
    highest_opportunity_score: float = 0.0


@dataclass
class PortfolioOpportunityResult:
    """Container for complete portfolio opportunity analysis."""

    analysis_status: str = "UNAVAILABLE"  # ANALYZED, NO_DATA, UNAVAILABLE, ERROR
    summary: PortfolioOpportunitySummary = field(default_factory=PortfolioOpportunitySummary)
    opportunities: list[OpportunityRecord] = field(default_factory=list)
    latest_timestamp: Optional[str] = None
    rationale: str = ""


@dataclass
class OpportunityTrackingRecord:
    """Historical observation tracking entry for portfolio opportunities."""

    timestamp: str
    opportunity_id: str
    symbol: str
    opportunity_type: str
    score: float
    priority: str
    status: str


def _empty_summary(status: str = "UNAVAILABLE") -> PortfolioOpportunitySummary:
    """Return a safe empty summary."""
    return PortfolioOpportunitySummary(
        total_opportunities=0,
        high_priority_count=0,
        medium_priority_count=0,
        low_priority_count=0,
        assessed_count=0,
        unavailable_count=0,
        average_opportunity_score=0.0,
        highest_opportunity_score=0.0,
    )


def _empty_result(status: str = "UNAVAILABLE", rationale: str = "") -> PortfolioOpportunityResult:
    """Return a safe empty result."""
    return PortfolioOpportunityResult(
        analysis_status=status,
        summary=_empty_summary(status=status),
        opportunities=[],
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


class PortfolioOpportunityService:
    """Service layer for identifying, scoring, and tracking factual portfolio opportunities."""

    _DEFAULT_STORAGE = get_data_path("intelligence/portfolio_opportunity_history.json")

    def __init__(
        self,
        portfolio_intelligence_service: Optional[Any] = None,
        holding_quality_service: Optional[Any] = None,
        sip_optimization_service: Optional[Any] = None,
        rebalancing_service: Optional[Any] = None,
        allocation_analysis_service: Optional[Any] = None,
        drift_detection_service: Optional[Any] = None,
        storage_path: Optional[Any] = None,
    ) -> None:
        """Initialize PortfolioOpportunityService with optional dependencies (Pattern A)."""
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._holding_quality_service = holding_quality_service
        self._sip_optimization_service = sip_optimization_service
        self._rebalancing_service = rebalancing_service
        self._allocation_analysis_service = allocation_analysis_service
        self._drift_detection_service = drift_detection_service
        self._storage_path = Path(storage_path) if storage_path is not None else self._DEFAULT_STORAGE

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

    def _get_sip_optimization_result(self) -> Optional[Any]:
        """Safely retrieve SIP optimization result."""
        if self._sip_optimization_service is not None and hasattr(self._sip_optimization_service, "analyze_sip"):
            try:
                return self._sip_optimization_service.analyze_sip()
            except Exception:
                pass
        try:
            from services.sip_optimization_service import SIPOptimizationService
            sip_svc = SIPOptimizationService()
            return sip_svc.analyze_sip()
        except Exception:
            return None

    def _get_portfolio_state(self) -> Optional[dict]:
        """Safely retrieve portfolio state dictionary."""
        try:
            from services.portfolio_state_service import PortfolioStateService
            state_svc = PortfolioStateService()
            return state_svc.load_state()
        except Exception:
            return None

    def _score_opportunity(
        self,
        opportunity_type: str,
        current_weight: float,
        target_weight: float,
        drift: float,
        quality_score: float = 0.0,
        sip_coverage: float = 0.0,
        extra_factor: float = 0.0,
    ) -> tuple[float, str]:
        """Compute transparent, deterministic 0-100 opportunity score and priority classification."""
        raw_score = 0.0

        if opportunity_type == "ALLOCATION_GAP":
            # Underweight positions with configured targets produce higher gap scores
            abs_drift = abs(drift)
            drift_component = min(abs_drift * 8.0, 50.0)
            underweight_bonus = 20.0 if drift < 0 else 5.0
            target_bonus = min(target_weight * 2.0, 30.0)
            raw_score = drift_component + underweight_bonus + target_bonus

        elif opportunity_type == "QUALITY_ALIGNMENT":
            # High assessed quality scores produce quality alignment relevance
            quality_component = max(0.0, min(quality_score, 100.0)) * 0.6
            gap_component = min(abs(drift) * 5.0, 20.0)
            target_component = min(target_weight * 2.0, 20.0)
            raw_score = quality_component + gap_component + target_component

        elif opportunity_type == "SIP_COVERAGE":
            # Positions lacking SIP transactions or under-covered SIP relative to target
            coverage_gap = max(0.0, 100.0 - sip_coverage) * 0.4
            target_component = min(target_weight * 3.0, 30.0)
            drift_component = min(abs(drift) * 6.0, 30.0)
            raw_score = coverage_gap + target_component + drift_component

        elif opportunity_type == "PORTFOLIO_STRUCTURE":
            # Structural balance observations (concentration, group allocation)
            raw_score = min(max(0.0, extra_factor), 100.0)

        else:
            raw_score = 30.0

        score = max(0.0, min(100.0, round(float(raw_score), 2)))

        if score >= 70.0:
            priority = "HIGH"
        elif score >= 40.0:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return score, priority

    def _identify_allocation_gap_opportunities(
        self,
        positions_dict: dict,
    ) -> list[OpportunityRecord]:
        """Identify factual ALLOCATION_GAP opportunities from position target & drift data."""
        records: list[OpportunityRecord] = []
        if not isinstance(positions_dict, dict):
            return records

        for symbol, pos in positions_dict.items():
            if not isinstance(pos, dict):
                continue
            t_weight = _safe_float(pos.get("target_weight"), 0.0)
            c_weight = _safe_float(pos.get("actual_weight", pos.get("current_weight")), 0.0)
            drift = _safe_float(pos.get("drift_pct", c_weight - t_weight), 0.0)

            # Significant allocation gap: target > 0 and abs(drift) >= 1.0%
            if t_weight > 0 and abs(drift) >= 1.0:
                name = str(pos.get("company_name", pos.get("name", symbol))).strip()
                atype = str(pos.get("category", pos.get("asset_type", "EQUITY"))).strip()
                direction = "UNDERWEIGHT" if drift < 0 else "OVERWEIGHT"

                ev = [
                    f"Configured target weight: {t_weight:.2f}%",
                    f"Current actual weight: {c_weight:.2f}%",
                    f"Allocation drift: {drift:+.2f}% ({direction})",
                ]
                rat = f"Position {symbol} shows measurable allocation gap of {drift:+.2f}% from target weight."

                score, priority = self._score_opportunity(
                    opportunity_type="ALLOCATION_GAP",
                    current_weight=c_weight,
                    target_weight=t_weight,
                    drift=drift,
                )

                records.append(
                    OpportunityRecord(
                        opportunity_id=f"OPP_ALLOC_{symbol.upper()}",
                        symbol=symbol.upper(),
                        name=name,
                        asset_type=atype,
                        opportunity_type="ALLOCATION_GAP",
                        opportunity_score=score,
                        opportunity_status="IDENTIFIED",
                        priority=priority,
                        evidence=ev,
                        rationale=rat,
                        source="PORTFOLIO_STATE",
                        current_weight=round(c_weight, 4),
                        target_weight=round(t_weight, 4),
                        drift=round(drift, 4),
                    )
                )

        return records

    def _identify_quality_alignment_opportunities(
        self,
        positions_dict: dict,
        hq_res: Optional[Any],
    ) -> list[OpportunityRecord]:
        """Identify factual QUALITY_ALIGNMENT opportunities from HoldingQuality data."""
        records: list[OpportunityRecord] = []
        if hq_res is None or not hasattr(hq_res, "holdings"):
            return records

        hq_holdings = getattr(hq_res, "holdings", [])
        if not isinstance(hq_holdings, list):
            return records

        hq_map = {getattr(h, "symbol", "").upper(): h for h in hq_holdings if hasattr(h, "symbol")}

        for symbol, pos in positions_dict.items():
            if not isinstance(pos, dict):
                continue
            sym_upper = symbol.upper()
            if sym_upper not in hq_map:
                continue

            hq = hq_map[sym_upper]
            q_score = _safe_float(getattr(hq, "quality_score", 0.0), 0.0)
            q_status = str(getattr(hq, "assessment_status", "UNAVAILABLE"))
            q_grade = str(getattr(hq, "quality_grade", "N/A"))

            if q_status == "ASSESSED" and q_score >= 60.0:
                name = str(pos.get("company_name", pos.get("name", getattr(hq, "name", symbol)))).strip()
                atype = str(getattr(hq, "asset_type", pos.get("category", "MUTUAL_FUND"))).strip()
                t_weight = _safe_float(pos.get("target_weight"), 0.0)
                c_weight = _safe_float(pos.get("actual_weight", pos.get("current_weight")), 0.0)
                drift = _safe_float(pos.get("drift_pct", c_weight - t_weight), 0.0)

                ev = [
                    f"Quality Score: {q_score:.1f} (Grade: {q_grade})",
                    f"Assessment status: {q_status}",
                    f"Current weight: {c_weight:.2f}% | Target weight: {t_weight:.2f}%",
                ]
                hq_ev = getattr(hq, "evidence", [])
                if isinstance(hq_ev, list) and hq_ev:
                    ev.extend([str(e) for e in hq_ev[:2]])

                rat = f"Holding {symbol} exhibits assessed high quality score ({q_score:.1f}/100, Grade {q_grade})."

                score, priority = self._score_opportunity(
                    opportunity_type="QUALITY_ALIGNMENT",
                    current_weight=c_weight,
                    target_weight=t_weight,
                    drift=drift,
                    quality_score=q_score,
                )

                records.append(
                    OpportunityRecord(
                        opportunity_id=f"OPP_QUAL_{sym_upper}",
                        symbol=sym_upper,
                        name=name,
                        asset_type=atype,
                        opportunity_type="QUALITY_ALIGNMENT",
                        opportunity_score=score,
                        opportunity_status="IDENTIFIED",
                        priority=priority,
                        evidence=ev,
                        rationale=rat,
                        source="HOLDING_QUALITY",
                        current_weight=round(c_weight, 4),
                        target_weight=round(t_weight, 4),
                        drift=round(drift, 4),
                        quality_score=round(q_score, 2),
                    )
                )

        return records

    def _identify_sip_coverage_opportunities(
        self,
        positions_dict: dict,
        sip_res: Optional[Any],
    ) -> list[OpportunityRecord]:
        """Identify factual SIP_COVERAGE opportunities from SIPOptimization data."""
        records: list[OpportunityRecord] = []
        if sip_res is None or not hasattr(sip_res, "holdings"):
            return records

        sip_holdings = getattr(sip_res, "holdings", [])
        if not isinstance(sip_holdings, list):
            return records

        sip_map = {getattr(s, "symbol", "").upper(): s for s in sip_holdings if hasattr(s, "symbol")}
        dist = getattr(sip_res, "distribution", None)
        sip_cov_pct = _safe_float(getattr(dist, "sip_coverage_pct", 0.0)) if dist else 0.0

        for symbol, pos in positions_dict.items():
            if not isinstance(pos, dict):
                continue
            sym_upper = symbol.upper()
            t_weight = _safe_float(pos.get("target_weight"), 0.0)
            c_weight = _safe_float(pos.get("actual_weight", pos.get("current_weight")), 0.0)
            drift = _safe_float(pos.get("drift_pct", c_weight - t_weight), 0.0)

            # Opportunity if position has a target weight (> 0) and is in SIP analysis
            if sym_upper in sip_map and t_weight > 0:
                sh = sip_map[sym_upper]
                tx_count = _safe_int(getattr(sh, "sip_transaction_count", 0))
                tx_amt = _safe_float(getattr(sh, "sip_invested_amount", 0.0))
                name = str(pos.get("company_name", pos.get("name", getattr(sh, "name", symbol)))).strip()
                atype = str(pos.get("category", pos.get("asset_type", "EQUITY"))).strip()

                if tx_count == 0:
                    ev = [
                        f"Position has configured target weight ({t_weight:.2f}%) but zero recorded SIP transactions",
                        f"Current drift: {drift:+.2f}%",
                    ]
                    rat = f"Position {symbol} has no SIP history recorded in portfolio transactions."
                else:
                    ev = [
                        f"SIP transaction count: {tx_count}",
                        f"Total SIP invested: ₹{tx_amt:,.2f}",
                        f"Current weight: {c_weight:.2f}% | Target weight: {t_weight:.2f}%",
                    ]
                    rat = f"Position {symbol} has {tx_count} confirmed SIP transactions totaling ₹{tx_amt:,.2f}."

                score, priority = self._score_opportunity(
                    opportunity_type="SIP_COVERAGE",
                    current_weight=c_weight,
                    target_weight=t_weight,
                    drift=drift,
                    sip_coverage=sip_cov_pct,
                )

                records.append(
                    OpportunityRecord(
                        opportunity_id=f"OPP_SIP_{sym_upper}",
                        symbol=sym_upper,
                        name=name,
                        asset_type=atype,
                        opportunity_type="SIP_COVERAGE",
                        opportunity_score=score,
                        opportunity_status="IDENTIFIED",
                        priority=priority,
                        evidence=ev,
                        rationale=rat,
                        source="SIP_OPTIMIZATION",
                        current_weight=round(c_weight, 4),
                        target_weight=round(t_weight, 4),
                        drift=round(drift, 4),
                        sip_coverage=round(sip_cov_pct, 2),
                    )
                )

        return records

    def _identify_portfolio_structure_opportunities(
        self,
        positions_dict: dict,
    ) -> list[OpportunityRecord]:
        """Identify factual PORTFOLIO_STRUCTURE observations (e.g., top position concentration)."""
        records: list[OpportunityRecord] = []
        if not isinstance(positions_dict, dict) or not positions_dict:
            return records

        # Check for top weight position
        top_pos = max(
            positions_dict.items(),
            key=lambda item: _safe_float(item[1].get("actual_weight", item[1].get("current_weight")))
            if isinstance(item[1], dict)
            else 0.0,
            default=None,
        )

        if top_pos and isinstance(top_pos[1], dict):
            symbol, pos = top_pos
            c_weight = _safe_float(pos.get("actual_weight", pos.get("current_weight")), 0.0)
            t_weight = _safe_float(pos.get("target_weight"), 0.0)
            drift = _safe_float(pos.get("drift_pct", c_weight - t_weight), 0.0)

            if c_weight >= 15.0:
                name = str(pos.get("company_name", pos.get("name", symbol))).strip()
                atype = str(pos.get("category", pos.get("asset_type", "EQUITY"))).strip()
                ev = [
                    f"Largest portfolio holding by weight: {c_weight:.2f}%",
                    f"Configured target weight: {t_weight:.2f}%",
                    f"Position concentration factor: {c_weight:.1f}% of total portfolio value",
                ]
                rat = f"Position {symbol} represents the highest concentration in the portfolio ({c_weight:.2f}%)."

                score, priority = self._score_opportunity(
                    opportunity_type="PORTFOLIO_STRUCTURE",
                    current_weight=c_weight,
                    target_weight=t_weight,
                    drift=drift,
                    extra_factor=min(c_weight * 3.5, 95.0),
                )

                records.append(
                    OpportunityRecord(
                        opportunity_id=f"OPP_STRUCT_{symbol.upper()}",
                        symbol=symbol.upper(),
                        name=name,
                        asset_type=atype,
                        opportunity_type="PORTFOLIO_STRUCTURE",
                        opportunity_score=score,
                        opportunity_status="IDENTIFIED",
                        priority=priority,
                        evidence=ev,
                        rationale=rat,
                        source="PORTFOLIO_STATE",
                        current_weight=round(c_weight, 4),
                        target_weight=round(t_weight, 4),
                        drift=round(drift, 4),
                    )
                )

        return records

    def _sort_opportunities(
        self,
        opportunities: list[OpportunityRecord],
    ) -> list[OpportunityRecord]:
        """Deterministically sort opportunities: Priority desc (HIGH > MEDIUM > LOW), Score desc, Symbol asc, ID asc."""
        priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

        def sort_key(rec: OpportunityRecord):
            p_val = priority_map.get(rec.priority.upper(), 0)
            return (-p_val, -rec.opportunity_score, rec.symbol.upper(), rec.opportunity_id.upper())

        return sorted(opportunities, key=sort_key)

    def identify_opportunities(
        self,
        state: Optional[dict] = None,
        hq_res: Optional[Any] = None,
        sip_res: Optional[Any] = None,
    ) -> list[OpportunityRecord]:
        """Public method to identify all factual opportunity records from available services."""
        try:
            if not isinstance(state, dict):
                state = self._get_portfolio_state()

            if not isinstance(state, dict) or not state:
                return []

            positions_dict = state.get("positions", {})
            if not isinstance(positions_dict, dict) or not positions_dict:
                return []

            if hq_res is None:
                hq_res = self._get_holding_quality_result()

            if sip_res is None:
                sip_res = self._get_sip_optimization_result()

            opps: list[OpportunityRecord] = []
            opps.extend(self._identify_allocation_gap_opportunities(positions_dict))
            opps.extend(self._identify_quality_alignment_opportunities(positions_dict, hq_res))
            opps.extend(self._identify_sip_coverage_opportunities(positions_dict, sip_res))
            opps.extend(self._identify_portfolio_structure_opportunities(positions_dict))

            # Deduplicate by opportunity_id
            seen = set()
            unique_opps = []
            for rec in opps:
                if rec.opportunity_id not in seen:
                    seen.add(rec.opportunity_id)
                    unique_opps.append(rec)

            return self._sort_opportunities(unique_opps)

        except Exception:
            return []

    def score_opportunities(
        self,
        opportunities: list[OpportunityRecord],
    ) -> list[OpportunityRecord]:
        """Score and classify priority for a list of opportunities deterministically."""
        if not isinstance(opportunities, list):
            return []

        scored = []
        for rec in opportunities:
            if not isinstance(rec, OpportunityRecord):
                continue
            score, priority = self._score_opportunity(
                opportunity_type=rec.opportunity_type,
                current_weight=rec.current_weight,
                target_weight=rec.target_weight,
                drift=rec.drift,
                quality_score=rec.quality_score,
                sip_coverage=rec.sip_coverage,
            )
            rec.opportunity_score = score
            rec.priority = priority
            scored.append(rec)

        return self._sort_opportunities(scored)

    def build_summary(
        self,
        opportunities: list[OpportunityRecord],
    ) -> PortfolioOpportunitySummary:
        """Compute summary statistics for identified opportunities."""
        if not isinstance(opportunities, list) or not opportunities:
            return _empty_summary(status="NO_DATA")

        total = len(opportunities)
        high = sum(1 for o in opportunities if str(getattr(o, "priority", "")).upper() == "HIGH")
        med = sum(1 for o in opportunities if str(getattr(o, "priority", "")).upper() == "MEDIUM")
        low = sum(1 for o in opportunities if str(getattr(o, "priority", "")).upper() == "LOW")
        assessed = sum(1 for o in opportunities if str(getattr(o, "opportunity_status", "")).upper() == "IDENTIFIED")
        unavail = total - assessed

        scores = [_safe_float(getattr(o, "opportunity_score", 0.0)) for o in opportunities]
        avg_score = (sum(scores) / total) if total > 0 else 0.0
        hi_score = max(scores, default=0.0)

        return PortfolioOpportunitySummary(
            total_opportunities=total,
            high_priority_count=high,
            medium_priority_count=med,
            low_priority_count=low,
            assessed_count=assessed,
            unavailable_count=unavail,
            average_opportunity_score=round(avg_score, 2),
            highest_opportunity_score=round(hi_score, 2),
        )

    def get_opportunities(
        self,
        state_input: Optional[Any] = None,
    ) -> PortfolioOpportunityResult:
        """Main entry point to perform complete portfolio opportunity evaluation safely."""
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
                    rationale="No valid portfolio state available for opportunity engine.",
                )

            positions_dict = state.get("positions", {})
            if not isinstance(positions_dict, dict) or not positions_dict:
                return _empty_result(
                    status="NO_DATA",
                    rationale="Portfolio contains no positions to evaluate.",
                )

            hq_res = self._get_holding_quality_result()
            sip_res = self._get_sip_optimization_result()

            raw_opps = self.identify_opportunities(state=state, hq_res=hq_res, sip_res=sip_res)
            sorted_opps = self.score_opportunities(raw_opps)
            summary = self.build_summary(sorted_opps)

            now_str = datetime.now(timezone.utc).isoformat()
            status = "ANALYZED" if sorted_opps else "NO_DATA"
            rat = (
                f"Identified {len(sorted_opps)} portfolio opportunities."
                if sorted_opps
                else "No notable portfolio opportunities identified based on current evidence."
            )

            result = PortfolioOpportunityResult(
                analysis_status=status,
                summary=summary,
                opportunities=sorted_opps,
                latest_timestamp=now_str,
                rationale=rat,
            )

            # Persist tracking observation defensively
            self.record_tracking(result)

            return result

        except Exception as exc:
            return _empty_result(
                status="ERROR",
                rationale=f"Error performing portfolio opportunity analysis: {str(exc)}",
            )

    def record_tracking(self, result: Any) -> bool:
        """Persist factual opportunity observations to storage defensively without duplicate records."""
        try:
            if result is None or not hasattr(result, "opportunities"):
                return False

            opps = getattr(result, "opportunities", [])
            if not isinstance(opps, list) or not opps:
                return False

            timestamp = getattr(result, "latest_timestamp", None) or datetime.now(timezone.utc).isoformat()

            existing_history = self.load_tracking_history()

            # Prevent duplicates by (timestamp, opportunity_id)
            existing_keys = {
                (str(rec.get("timestamp", "")), str(rec.get("opportunity_id", "")))
                for rec in existing_history
                if isinstance(rec, dict)
            }

            new_entries = []
            for rec in opps:
                opp_id = str(getattr(rec, "opportunity_id", ""))
                key = (timestamp, opp_id)
                if key not in existing_keys:
                    existing_keys.add(key)
                    track_rec = OpportunityTrackingRecord(
                        timestamp=timestamp,
                        opportunity_id=opp_id,
                        symbol=str(getattr(rec, "symbol", "")),
                        opportunity_type=str(getattr(rec, "opportunity_type", "")),
                        score=_safe_float(getattr(rec, "opportunity_score", 0.0)),
                        priority=str(getattr(rec, "priority", "")),
                        status=str(getattr(rec, "opportunity_status", "")),
                    )
                    new_entries.append(asdict(track_rec))

            if not new_entries:
                return True

            updated_history = existing_history + new_entries

            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._storage_path.with_suffix(self._storage_path.suffix + ".tmp")
            temp_path.write_text(json.dumps(updated_history, indent=2, ensure_ascii=False), encoding="utf-8")
            temp_path.replace(self._storage_path)

            return True

        except Exception:
            return False

    def load_tracking_history(self) -> list[dict]:
        """Safely load historical opportunity tracking records from storage."""
        try:
            if not self._storage_path.exists():
                return []
            content = self._storage_path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            data = json.loads(content)
            if not isinstance(data, list):
                return []
            valid = [item for item in data if isinstance(item, dict)]
            return valid
        except Exception:
            return []
