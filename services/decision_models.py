from dataclasses import dataclass, field


class DecisionPriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionType:
    MONITOR = "MONITOR"
    REVIEW_STRUCTURE = "REVIEW_STRUCTURE"
    REVIEW_POSITION_SIZES = "REVIEW_POSITION_SIZES"
    REDUCE_CONCENTRATION = "REDUCE_CONCENTRATION"
    REBALANCE = "REBALANCE"


@dataclass
class Decision:
    decision_type: str
    priority: str
    score: int

    title: str
    description: str

    source_recommendation: str


@dataclass
class DecisionReport:

    decisions: list[Decision] = field(
        default_factory=list
    )

    @property
    def total_decisions(self) -> int:
        return len(self.decisions)