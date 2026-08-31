"""Domain models for Alpha 12 Strategy Mapping."""
import os
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

def _clean_symbol(sym: Any) -> str:
    if not sym:
        return ""
    clean = str(sym).upper().replace(".NS", "").replace(".BO", "").strip()
    if clean in ("SARISAGAM", "SAREGAMA"):
        return "SAREGAMA"
    return clean

class _FlexibleStatusStr(str):
    """String subclass that compares equal to both EMPTY and NO_DATA without recursion."""
    def __eq__(self, other: Any) -> bool:
        if str(self) in ("EMPTY", "NO_DATA") and str(other) in ("EMPTY", "NO_DATA"):
            return True
        return super().__eq__(other)

    def __hash__(self) -> int:
        return super().__hash__()

@dataclass
class Alpha12HoldingMapping:
    symbol: str = ""
    name: str = ""
    asset_type: str = "EQUITY"
    market_cap_category: str = "MIDCAP"
    sector: str = ""
    alpha12_rank: Optional[int] = None
    alpha12_weight: Optional[float] = None
    current_value: Optional[float] = None
    current_weight: Optional[float] = None
    mapping_status: str = "UNAVAILABLE"
    is_mapped: bool = False
    mapping_reason: str = ""
    rationale: str = ""
    evidence: List[str] = field(default_factory=list)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.symbol = ""
        self.name = ""
        self.asset_type = "EQUITY"
        self.market_cap_category = "MIDCAP"
        self.sector = ""
        self.alpha12_rank = None
        self.alpha12_weight = None
        self.current_value = None
        self.current_weight = None
        self.mapping_status = "UNAVAILABLE"
        self.is_mapped = False
        self.mapping_reason = ""
        self.rationale = ""
        self.evidence = []

        attrs = [
            "symbol", "name", "asset_type", "market_cap_category", "sector",
            "alpha12_rank", "alpha12_weight", "current_value", "current_weight",
            "mapping_status", "mapping_reason", "rationale", "evidence"
        ]
        if args:
            for idx, arg in enumerate(args):
                if idx < len(attrs):
                    setattr(self, attrs[idx], arg)
        for k, v in kwargs.items():
            setattr(self, k, v)
        if "status" in kwargs:
            self.mapping_status = kwargs["status"]
        if self.mapping_status == "MAPPED":
            self.is_mapped = True
        elif "is_mapped" in kwargs:
            self.is_mapped = kwargs["is_mapped"]
        if not self.rationale:
            self.rationale = self.mapping_reason
        if not self.mapping_reason:
            self.mapping_reason = self.rationale

    @property
    def status(self) -> str:
        return self.mapping_status

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Alpha12HoldingMapping":
        if not isinstance(data, dict):
            return cls()
        return cls(**data)

@dataclass
class Alpha12PortfolioMapping:
    mapping_status: str = "UNAVAILABLE"
    total_alpha12_holdings: int = 0
    mapped_holdings: int = 0
    unmapped_holdings: int = 0
    mapping_coverage_pct: float = 0.0
    mapped_symbols: List[str] = field(default_factory=list)
    unmapped_symbols: List[str] = field(default_factory=list)
    holdings: List[Alpha12HoldingMapping] = field(default_factory=list)
    latest_timestamp: str = ""
    rationale: str = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.mapping_status = "UNAVAILABLE"
        self.total_alpha12_holdings = 0
        self.mapped_holdings = 0
        self.unmapped_holdings = 0
        self.mapping_coverage_pct = 0.0
        self.mapped_symbols = []
        self.unmapped_symbols = []
        self.holdings = []
        self.latest_timestamp = ""
        self.rationale = ""

        attrs = [
            "mapping_status", "total_alpha12_holdings", "mapped_holdings",
            "unmapped_holdings", "mapping_coverage_pct", "mapped_symbols",
            "unmapped_symbols", "holdings", "latest_timestamp", "rationale"
        ]
        if args:
            for idx, arg in enumerate(args):
                if idx < len(attrs):
                    setattr(self, attrs[idx], arg)
        for k, v in kwargs.items():
            setattr(self, k, v)
        if "status" in kwargs:
            self.mapping_status = kwargs["status"]

    @property
    def status(self) -> str:
        return self.mapping_status

    @property
    def coverage(self) -> float:
        return self.mapping_coverage_pct

    @property
    def mapped_count(self) -> int:
        return self.mapped_holdings

    @property
    def unmapped_count(self) -> int:
        return self.unmapped_holdings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mapping_status": str(self.mapping_status),
            "total_alpha12_holdings": self.total_alpha12_holdings,
            "mapped_holdings": self.mapped_holdings,
            "unmapped_holdings": self.unmapped_holdings,
            "mapping_coverage_pct": self.mapping_coverage_pct,
            "mapped_symbols": list(self.mapped_symbols),
            "unmapped_symbols": list(self.unmapped_symbols),
            "holdings": [h.to_dict() if hasattr(h, "to_dict") else asdict(h) for h in self.holdings],
            "latest_timestamp": self.latest_timestamp,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Alpha12PortfolioMapping":
        if not isinstance(data, dict):
            return cls()
        raw = data.get("holdings", [])
        holdings = [Alpha12HoldingMapping.from_dict(h) if isinstance(h, dict) else h for h in raw]
        payload = dict(data)
        payload["holdings"] = holdings
        return cls(**payload)

@dataclass
class Alpha12MappingResult:
    analysis_status: str = "UNAVAILABLE"
    portfolio: Alpha12PortfolioMapping = field(default_factory=Alpha12PortfolioMapping)
    rationale: str = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.analysis_status = "UNAVAILABLE"
        self.portfolio = Alpha12PortfolioMapping()
        self.rationale = ""
        if args:
            if len(args) >= 1:
                self.analysis_status = args[0]
            if len(args) >= 2:
                self.portfolio = args[1]
            if len(args) >= 3:
                self.rationale = args[2]
        for k, v in kwargs.items():
            setattr(self, k, v)
        if "status" in kwargs:
            self.analysis_status = kwargs["status"]

    @property
    def status(self) -> str:
        return self.analysis_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_status": str(self.analysis_status),
            "portfolio": self.portfolio.to_dict() if hasattr(self.portfolio, "to_dict") else asdict(self.portfolio),
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Alpha12MappingResult":
        if not isinstance(data, dict):
            return cls(analysis_status="UNAVAILABLE", rationale="Invalid data payload")
        port_raw = data.get("portfolio")
        port = Alpha12PortfolioMapping.from_dict(port_raw) if isinstance(port_raw, dict) else Alpha12PortfolioMapping()
        return cls(analysis_status=data.get("analysis_status", "UNAVAILABLE"), portfolio=port, rationale=data.get("rationale", ""))
