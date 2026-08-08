"""Alpha12 Health Integration Service (Sprint 13.9.1)

Read-only integration layer that overlays Alpha 12 mapping with existing
portfolio health, quality, and risk intelligence outputs.

Defensive, deterministic, and read-only. Does not fabricate or mutate data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from services.alpha12_mapping_service import (
    Alpha12MappingResult,
    Alpha12HoldingMapping,
)


@dataclass
class Alpha12HealthOverlay:
    symbol: str
    name: str
    alpha12_rank: Optional[int] = None
    alpha12_weight: Optional[float] = None

    current_weight: float = 0.0
    current_value: float = 0.0

    health_score: Optional[float] = None
    health_grade: str = "N/A"

    quality_score: Optional[float] = None
    quality_grade: str = "N/A"

    risk_score: Optional[float] = None
    risk_level: str = "UNAVAILABLE"

    mapping_status: str = "UNAVAILABLE"
    health_status: str = "UNAVAILABLE"

    evidence: List[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class Alpha12PortfolioHealthComparison:
    alpha12_total_holdings: int = 0
    mapped_holdings: int = 0
    unmapped_holdings: int = 0

    mapped_coverage_pct: float = 0.0

    average_health_score: float = 0.0
    average_quality_score: float = 0.0
    average_risk_score: float = 0.0

    healthy_count: int = 0
    watch_count: int = 0
    attention_count: int = 0
    unavailable_count: int = 0

    current_portfolio_value: float = 0.0
    alpha12_mapped_value: float = 0.0

    comparison_status: str = "UNAVAILABLE"

    overlays: List[Alpha12HealthOverlay] = field(default_factory=list)


@dataclass
class Alpha12HealthSynchronization:
    alpha12_ranked_count: int = 0
    mapped_count: int = 0
    unmapped_count: int = 0
    health_available_count: int = 0
    health_unavailable_count: int = 0

    synchronization_status: str = "UNAVAILABLE"

    latest_timestamp: Optional[str] = None
    rationale: str = ""


@dataclass
class Alpha12HealthIntegrationResult:
    analysis_status: str = "UNAVAILABLE"

    comparison: Alpha12PortfolioHealthComparison = field(
        default_factory=Alpha12PortfolioHealthComparison
    )

    synchronization: Alpha12HealthSynchronization = field(
        default_factory=Alpha12HealthSynchronization
    )

    overlays: List[Alpha12HealthOverlay] = field(default_factory=list)

    latest_timestamp: Optional[str] = None

    rationale: str = ""


class Alpha12HealthIntegrationService:
    """Integration service that builds overlays, comparisons, and synchronization reports."""

    def __init__(
        self,
        alpha12_mapping_service: Optional[Any] = None,
        portfolio_health_service: Optional[Any] = None,
        portfolio_intelligence_service: Optional[Any] = None,
        holding_quality_service: Optional[Any] = None,
        portfolio_risk_intelligence_service: Optional[Any] = None,
    ) -> None:
        self._alpha12_mapping_service = alpha12_mapping_service
        self._portfolio_health_service = portfolio_health_service
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._holding_quality_service = holding_quality_service
        self._portfolio_risk_intelligence_service = portfolio_risk_intelligence_service

    def _safe_float(self, v: Optional[float]) -> float:
        try:
            if v is None:
                return 0.0
            return float(v)
        except Exception:
            return 0.0

    def _deterministic_health_status(self, health_score: Optional[float]) -> str:
        # Deterministic informational classification based only on provided score
        if health_score is None:
            return "UNAVAILABLE"
        try:
            hs = float(health_score)
        except Exception:
            return "UNAVAILABLE"
        if hs >= 80.0:
            return "HEALTHY"
        if hs >= 60.0:
            return "WATCH"
        return "ATTENTION"

    def build_health_overlay(
        self,
        mapping_item: Alpha12HoldingMapping,
        portfolio_health: Optional[Any] = None,
        holding_quality: Optional[Any] = None,
        portfolio_risk: Optional[Any] = None,
    ) -> Alpha12HealthOverlay:
        """Build a single overlay entry deterministically and defensively."""
        if mapping_item is None:
            return Alpha12HealthOverlay(symbol="", name="")

        symbol = getattr(mapping_item, "symbol", "") or ""
        name = getattr(mapping_item, "name", symbol) or symbol

        current_weight = self._safe_float(getattr(mapping_item, "current_weight", 0.0))
        current_value = self._safe_float(getattr(mapping_item, "current_value", 0.0))

        # Pull quality/risk if provided as dicts keyed by symbol
        q_score = None
        if isinstance(holding_quality, dict):
            q = holding_quality.get(symbol)
            try:
                q_score = float(q) if q is not None else None
            except Exception:
                q_score = None

        r_score = None
        if isinstance(portfolio_risk, dict):
            r = portfolio_risk.get(symbol)
            try:
                r_score = float(r) if r is not None else None
            except Exception:
                r_score = None

        # Health score: attempt to derive from portfolio_health if it exposes per-symbol scores
        h_score = None
        if portfolio_health is not None:
            # Look for a dict of instrument_evaluations or instrument_health indexed by symbol
            instr = getattr(portfolio_health, "instrument_health", None) or getattr(portfolio_health, "instrument_evaluations", None)
            if isinstance(instr, dict) and symbol in instr:
                try:
                    h_score = instr.get(symbol, {}).get("health_score")
                except Exception:
                    h_score = None

        overlay = Alpha12HealthOverlay(
            symbol=symbol,
            name=name,
            alpha12_rank=getattr(mapping_item, "alpha12_rank", None),
            alpha12_weight=getattr(mapping_item, "alpha12_weight", None),
            current_weight=current_weight,
            current_value=current_value,
            health_score=(None if h_score is None else float(h_score)),
            health_grade=("N/A" if h_score is None else ("A" if h_score >= 90 else "B" if h_score >= 75 else "C" if h_score >= 60 else "D")),
            quality_score=q_score,
            quality_grade=("N/A" if q_score is None else ("A" if q_score >= 90 else "B" if q_score >= 75 else "C" if q_score >= 60 else "D")),
            risk_score=r_score,
            risk_level=("UNAVAILABLE" if r_score is None else ("LOW" if r_score < 30 else "MODERATE" if r_score < 60 else "HIGH")),
            mapping_status=getattr(mapping_item, "mapping_status", "UNAVAILABLE"),
            health_status=self._deterministic_health_status(h_score),
            evidence=list(getattr(mapping_item, "evidence", []) or []),
            rationale=str(getattr(mapping_item, "rationale", "") or ""),
        )

        return overlay

    def compare_portfolio_health(
        self,
        mapping_result: Optional[Alpha12MappingResult],
        overlays: List[Alpha12HealthOverlay],
    ) -> Alpha12PortfolioHealthComparison:
        comp = Alpha12PortfolioHealthComparison()
        try:
            total = 0
            mapped = 0
            unmapped = 0
            sum_health = 0.0
            sum_quality = 0.0
            sum_risk = 0.0
            health_count = 0
            quality_count = 0
            risk_count = 0
            healthy = watch = attention = unavailable = 0

            if mapping_result is None or not getattr(mapping_result, "portfolio", None):
                return comp

            total = int(getattr(mapping_result.portfolio, "total_alpha12_holdings", 0) or 0)

            for ov in overlays:
                if getattr(ov, "mapping_status", "").upper() == "MAPPED":
                    mapped += 1
                else:
                    unmapped += 1

                if ov.health_score is not None:
                    sum_health += float(ov.health_score)
                    health_count += 1
                if ov.quality_score is not None:
                    sum_quality += float(ov.quality_score)
                    quality_count += 1
                if ov.risk_score is not None:
                    sum_risk += float(ov.risk_score)
                    risk_count += 1

                if ov.health_status == "HEALTHY":
                    healthy += 1
                elif ov.health_status == "WATCH":
                    watch += 1
                elif ov.health_status == "ATTENTION":
                    attention += 1
                else:
                    unavailable += 1

            comp.alpha12_total_holdings = total
            comp.mapped_holdings = mapped
            comp.unmapped_holdings = unmapped
            comp.mapped_coverage_pct = (mapped / total * 100.0) if total > 0 else 0.0
            comp.average_health_score = (sum_health / health_count) if health_count > 0 else 0.0
            comp.average_quality_score = (sum_quality / quality_count) if quality_count > 0 else 0.0
            comp.average_risk_score = (sum_risk / risk_count) if risk_count > 0 else 0.0
            comp.healthy_count = healthy
            comp.watch_count = watch
            comp.attention_count = attention
            comp.unavailable_count = unavailable
            comp.overlays = list(overlays)
            comp.current_portfolio_value = 0.0
            comp.alpha12_mapped_value = 0.0
            comp.comparison_status = "PARTIAL" if mapped > 0 else "UNAVAILABLE"
        except Exception:
            pass
        return comp

    def build_synchronization(
        self,
        mapping_result: Optional[Alpha12MappingResult],
        overlays: List[Alpha12HealthOverlay],
    ) -> Alpha12HealthSynchronization:
        sync = Alpha12HealthSynchronization()
        try:
            total = int(getattr(mapping_result.portfolio, "total_alpha12_holdings", 0) or 0) if mapping_result else 0
            mapped = sum(1 for o in overlays if getattr(o, "mapping_status", "").upper() == "MAPPED")
            unmapped = total - mapped if total >= 0 else 0
            health_available = sum(1 for o in overlays if o.health_score is not None)
            health_unavailable = len(overlays) - health_available

            sync.alpha12_ranked_count = total
            sync.mapped_count = mapped
            sync.unmapped_count = unmapped
            sync.health_available_count = health_available
            sync.health_unavailable_count = health_unavailable
            sync.latest_timestamp = datetime.now(timezone.utc).isoformat()
            if total > 0 and mapped == total and health_available == mapped:
                sync.synchronization_status = "SYNCHRONIZED"
            elif mapped > 0:
                sync.synchronization_status = "PARTIAL"
            else:
                sync.synchronization_status = "UNAVAILABLE"
        except Exception:
            pass
        return sync

    def analyze(
        self,
        alpha12_mapping: Optional[Alpha12MappingResult],
        portfolio_health: Optional[Any] = None,
        holding_quality: Optional[Any] = None,
        portfolio_risk: Optional[Any] = None,
    ) -> Alpha12HealthIntegrationResult:
        """Top-level analysis entrypoint. Defensive and read-only."""
        result = Alpha12HealthIntegrationResult()
        try:
            if alpha12_mapping is None or not getattr(alpha12_mapping, "portfolio", None):
                result.analysis_status = "UNAVAILABLE"
                result.overlays = []
                result.comparison = Alpha12PortfolioHealthComparison()
                result.synchronization = Alpha12HealthSynchronization()
                result.latest_timestamp = datetime.now(timezone.utc).isoformat()
                return result

            overlays = []
            for h in getattr(alpha12_mapping.portfolio, "holdings", []) or []:
                overlays.append(self.build_health_overlay(h, portfolio_health, holding_quality, portfolio_risk))

            comparison = self.compare_portfolio_health(alpha12_mapping, overlays)
            synchronization = self.build_synchronization(alpha12_mapping, overlays)

            result.analysis_status = "ANALYZED"
            result.overlays = overlays
            result.comparison = comparison
            result.synchronization = synchronization
            result.latest_timestamp = datetime.now(timezone.utc).isoformat()
        except Exception:
            result.analysis_status = "ERROR"
            result.rationale = "Exception during analysis"
        return result

    # Alias
    def get_health_integration(self, *args, **kwargs):
        return self.analyze(*args, **kwargs)
