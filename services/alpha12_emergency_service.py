"""services/alpha12_emergency_service.py - Emergency risk, market-cap volatility, and fundamental triage."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from services.contracts import IAlpha12EmergencyService

@dataclass
class HoldingEmergencyStatus:
    symbol: str
    market_cap_category: str = "MIDCAP"
    current_price: float = 0.0
    entry_or_peak_price: float = 0.0
    drawdown_pct: float = 0.0
    drawdown_tolerance_pct: float = 12.0
    drawdown_breached: bool = False
    fundamental_status: str = "INTACT"   # INTACT or DEGRADED
    fundamental_reasons: List[str] = field(default_factory=list)
    alpha_rank: Optional[int] = None
    emergency_level: str = "NORMAL"      # NORMAL, VOLATILITY_DIP, WARNING, CRITICAL_EXIT
    action_required: str = "HOLD"        # HOLD, MONITOR, IMMEDIATE_EXIT
    triggers: List[str] = field(default_factory=list)

@dataclass
class EmergencyAnalysisResult:
    analysis_status: str = "NORMAL"      # NORMAL, WARNING, CRITICAL
    critical_count: int = 0
    warning_count: int = 0
    volatility_dip_count: int = 0
    holdings_status: List[HoldingEmergencyStatus] = field(default_factory=list)
    timestamp: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_status": self.analysis_status,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "volatility_dip_count": self.volatility_dip_count,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "holdings_status": [asdict(h) for h in self.holdings_status]
        }

class Alpha12EmergencyService(IAlpha12EmergencyService):
    """
    Market-cap aware volatility thresholds:
    - Large Cap: 8%
    - Mid Cap: 12%
    - Small Cap: 16%
    
    2D Matrix:
    - INTACT + Normal Price    => NORMAL (HOLD)
    - INTACT + Drawdown Breach => VOLATILITY_DIP (HOLD / Retain tenure)
    - DEGRADED + Normal Price  => WARNING (MONITOR / Scheduled replace)
    - DEGRADED + Breach        => CRITICAL_EXIT (IMMEDIATE_EXIT)
    """
    DEFAULT_CAP_THRESHOLDS = {
        "LARGECAP": 8.0,
        "MIDCAP": 12.0,
        "SMALLCAP": 16.0
    }

    def __init__(self, rank_floor: int = 30, thresholds: Optional[Dict[str, float]] = None):
        self.rank_floor = rank_floor
        self.thresholds = thresholds or self.DEFAULT_CAP_THRESHOLDS

    def _get_drawdown_tolerance(self, category: str) -> float:
        cat_clean = str(category).upper().replace(" ", "").replace("-", "")
        if "LARGE" in cat_clean:
            return self.thresholds.get("LARGECAP", 8.0)
        elif "SMALL" in cat_clean or "MICRO" in cat_clean:
            return self.thresholds.get("SMALLCAP", 16.0)
        return self.thresholds.get("MIDCAP", 12.0)

    def evaluate_holdings(
        self,
        active_holdings: List[Dict[str, Any]],
        candidate_ranks: Optional[Dict[str, int]] = None
    ) -> EmergencyAnalysisResult:
        candidate_ranks = candidate_ranks or {}
        statuses: List[HoldingEmergencyStatus] = []
        critical_alerts = 0
        warning_alerts = 0
        volatility_dips = 0

        for h in active_holdings:
            sym = str(h.get("symbol", "")).upper().replace(".NS", "").replace(".BO", "").strip()
            cat = str(h.get("market_cap_category", "MIDCAP")).upper()
            tolerance = self._get_drawdown_tolerance(cat)

            curr_price = float(h.get("current_price", 0.0) or 0.0)
            peak_price = float(h.get("peak_price") or h.get("entry_price") or curr_price or 1.0)

            # Drawdown calculation
            dd_pct = ((curr_price - peak_price) / peak_price * 100.0) if peak_price > 0 else 0.0
            is_dd_breached = dd_pct <= -tolerance

            # Fundamental assessment
            fund_status = str(h.get("fundamental_status", "INTACT")).upper()
            fund_reasons = h.get("fundamental_reasons", [])
            rank = candidate_ranks.get(sym, h.get("alpha12_rank"))

            triggers = []
            if is_dd_breached:
                triggers.append(f"Drawdown breach: {dd_pct:.1f}% (Threshold: -{tolerance:.1f}%)")
            if rank and rank > self.rank_floor:
                fund_status = "DEGRADED"
                triggers.append(f"Rank floor collapsed to #{rank} (> #{self.rank_floor})")

            # 2D Decision Matrix
            if fund_status == "INTACT" and not is_dd_breached:
                level = "NORMAL"
                action = "HOLD"
            elif fund_status == "INTACT" and is_dd_breached:
                level = "VOLATILITY_DIP"
                action = "HOLD"
                volatility_dips += 1
                triggers.append(f"Small/Midcap volatility dip tolerated: Fundamentals intact.")
            elif fund_status == "DEGRADED" and not is_dd_breached:
                level = "WARNING"
                action = "MONITOR"
                warning_alerts += 1
                triggers.append("Fundamental degradation detected. Flagged for rebalance review.")
            else:  # DEGRADED + is_dd_breached
                level = "CRITICAL_EXIT"
                action = "IMMEDIATE_EXIT"
                critical_alerts += 1
                triggers.append("CRITICAL: Structural breakdown and price collapse confirmed.")

            statuses.append(HoldingEmergencyStatus(
                symbol=sym,
                market_cap_category=cat,
                current_price=curr_price,
                entry_or_peak_price=peak_price,
                drawdown_pct=round(dd_pct, 2),
                drawdown_tolerance_pct=tolerance,
                drawdown_breached=is_dd_breached,
                fundamental_status=fund_status,
                fundamental_reasons=fund_reasons,
                alpha_rank=rank,
                emergency_level=level,
                action_required=action,
                triggers=triggers
            ))

        now_ts = datetime.now(timezone.utc).isoformat()
        if critical_alerts > 0:
            analysis_status = "CRITICAL"
        elif warning_alerts > 0:
            analysis_status = "WARNING"
        else:
            analysis_status = "NORMAL"

        summary = f"{critical_alerts} critical exits, {warning_alerts} warnings, {volatility_dips} tolerated dips." if (critical_alerts or warning_alerts or volatility_dips) else "All holdings operating within safe parameters."

        return EmergencyAnalysisResult(
            analysis_status=analysis_status,
            critical_count=critical_alerts,
            warning_count=warning_alerts,
            volatility_dip_count=volatility_dips,
            holdings_status=statuses,
            timestamp=now_ts,
            summary=summary
        )
