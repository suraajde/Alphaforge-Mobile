"""Domain models for Alpha 12 Stability & Churn Governance."""
import os
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

@dataclass
class Alpha12StabilityMetrics:
    stability_score: float = 0.0
    stability_rating: str = "UNSTABLE"
    churn_risk: str = "LOW"
    turnover_rate: float = 0.0
    turnover_efficiency: float = 1.0
    churn_prevention_ratio: float = 0.0
    unnecessary_swaps_blocked: int = 0
    unnecessary_swap_prevention: int = 0
    average_holding_tenure: float = 0.0
    average_holding_tenure_months: float = 0.0
    persistent_holdings: int = 0
    persistence_count: int = 0
    assessment_status: str = "ANALYZED"
    rationale: str = ""
    evidence: List[str] = field(default_factory=list)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.stability_score = 0.0
        self.stability_rating = "UNSTABLE"
        self.churn_risk = "LOW"
        self.turnover_rate = 0.0
        self.turnover_efficiency = 1.0
        self.churn_prevention_ratio = 0.0
        self.unnecessary_swaps_blocked = 0
        self.unnecessary_swap_prevention = 0
        self.average_holding_tenure = 0.0
        self.average_holding_tenure_months = 0.0
        self.persistent_holdings = 0
        self.persistence_count = 0
        self.assessment_status = "ANALYZED"
        self.rationale = ""
        self.evidence = []

        attrs = [
            "stability_score", "stability_rating", "turnover_rate",
            "churn_prevention_ratio", "unnecessary_swaps_blocked",
            "average_holding_tenure", "persistent_holdings"
        ]
        if args:
            for idx, arg in enumerate(args):
                if idx < len(attrs):
                    setattr(self, attrs[idx], arg)
        for k, v in kwargs.items():
            setattr(self, k, v)
        if "score" in kwargs:
            self.stability_score = kwargs["score"]
        if "rating" in kwargs:
            self.stability_rating = kwargs["rating"]
        if "status" in kwargs:
            self.assessment_status = kwargs["status"]
        if "unnecessary_swap_prevention" not in kwargs and "unnecessary_swaps_blocked" in kwargs:
            self.unnecessary_swap_prevention = self.unnecessary_swaps_blocked
        if "unnecessary_swaps_blocked" not in kwargs and "unnecessary_swap_prevention" in kwargs:
            self.unnecessary_swaps_blocked = int(self.unnecessary_swap_prevention)

    @property
    def score(self) -> float:
        return self.stability_score

    @property
    def rating(self) -> str:
        return self.stability_rating

    @property
    def status(self) -> str:
        return self.assessment_status

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Alpha12StabilityMetrics":
        if not isinstance(data, dict):
            return cls()
        return cls(**data)

@dataclass
class Alpha12StabilityResult:
    analysis_status: str = "ANALYZED"
    stability_metrics: Alpha12StabilityMetrics = field(default_factory=Alpha12StabilityMetrics)
    rationale: str = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.analysis_status = "ANALYZED"
        self.stability_metrics = Alpha12StabilityMetrics()
        self.rationale = ""
        if args:
            if len(args) >= 1:
                self.analysis_status = args[0]
            if len(args) >= 2:
                self.stability_metrics = args[1] if isinstance(args[1], Alpha12StabilityMetrics) else Alpha12StabilityMetrics(**args[1]) if isinstance(args[1], dict) else Alpha12StabilityMetrics()
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
            "analysis_status": self.analysis_status,
            "stability_metrics": self.stability_metrics.to_dict() if hasattr(self.stability_metrics, "to_dict") else asdict(self.stability_metrics),
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Alpha12StabilityResult":
        if not isinstance(data, dict):
            return cls(analysis_status="UNAVAILABLE", rationale="Invalid data payload")
        m_raw = data.get("stability_metrics")
        metrics = Alpha12StabilityMetrics.from_dict(m_raw) if isinstance(m_raw, dict) else Alpha12StabilityMetrics()
        return cls(analysis_status=data.get("analysis_status", "ANALYZED"), stability_metrics=metrics, rationale=data.get("rationale", ""))

@dataclass
class Alpha12PersistenceEntry:
    timestamp: str = ""
    stability_score: float = 0.0
    stability_rating: str = "UNSTABLE"
    turnover_rate: float = 0.0
    churn_prevention_ratio: float = 0.0
    mapped_holdings: int = 0
    total_alpha12_holdings: int = 12

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.timestamp = ""
        self.stability_score = 0.0
        self.stability_rating = "UNSTABLE"
        self.turnover_rate = 0.0
        self.churn_prevention_ratio = 0.0
        self.mapped_holdings = 0
        self.total_alpha12_holdings = 12
        attrs = ["timestamp", "stability_score", "stability_rating", "turnover_rate", "churn_prevention_ratio", "mapped_holdings", "total_alpha12_holdings"]
        if args:
            for idx, arg in enumerate(args):
                if idx < len(attrs):
                    setattr(self, attrs[idx], arg)
        for k, v in kwargs.items():
            setattr(self, k, v)

@dataclass
class Alpha12PersistenceHistory:
    total_entries: int = 0
    earliest_timestamp: Optional[str] = None
    latest_timestamp: Optional[str] = None
    entries: List[Alpha12PersistenceEntry] = field(default_factory=list)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.total_entries = 0
        self.earliest_timestamp = None
        self.latest_timestamp = None
        self.entries = []
        attrs = ["total_entries", "earliest_timestamp", "latest_timestamp", "entries"]
        if args:
            for idx, arg in enumerate(args):
                if idx < len(attrs):
                    setattr(self, attrs[idx], arg)
        for k, v in kwargs.items():
            setattr(self, k, v)
