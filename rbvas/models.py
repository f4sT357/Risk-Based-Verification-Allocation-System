from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def score(self) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]

    @classmethod
    def from_score(cls, score: float) -> RiskLevel:
        if score <= 1.5:
            return cls.LOW
        elif score <= 2.5:
            return cls.MEDIUM
        elif score <= 3.5:
            return cls.HIGH
        else:
            return cls.CRITICAL


@dataclass(frozen=True)
class RiskAssessment:
    probability: float
    impact: float
    description: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError(f"probability must be in [0, 1], got {self.probability}")
        if not 0.0 <= self.impact <= 1.0:
            raise ValueError(f"impact must be in [0, 1], got {self.impact}")

    @property
    def expected_value(self) -> float:
        return self.probability * self.impact

    @property
    def level(self) -> RiskLevel:
        raw = self.expected_value * 4
        return RiskLevel.from_score(raw)

    def __str__(self) -> str:
        return (
            f"RiskAssessment(prob={self.probability:.2f}, "
            f"impact={self.impact:.2f}, "
            f"EV={self.expected_value:.3f}, "
            f"level={self.level.value})"
        )


@dataclass
class DecisionOption:
    name: str
    direct_cost: float = 0.0
    indirect_cost: float = 0.0
    residual_risk: Optional[RiskAssessment] = None
    description: str = ""

    @property
    def total_direct_cost(self) -> float:
        return self.direct_cost + self.indirect_cost

    def __str__(self) -> str:
        return (
            f"DecisionOption(name={self.name!r}, "
            f"direct={self.direct_cost}, "
            f"indirect={self.indirect_cost})"
        )


@dataclass
class DecisionResult:
    selected_option: DecisionOption
    total_cost: float
    cost_breakdown: "CostBreakdown"
    criteria: "DecisionCriteria"
    alternative_options: List[DecisionOption] = field(default_factory=list)
