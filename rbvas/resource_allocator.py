from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from .models import RiskAssessment, RiskLevel


class ResourceType(Enum):
    BUDGET = "budget"
    TIME = "time"
    PERSONNEL = "personnel"


class AllocationStrategy(Enum):
    PROPORTIONAL = "proportional"
    THRESHOLD = "threshold"


@dataclass(frozen=True)
class ResourceAllocation:
    item_name: str
    allocated_amount: float
    resource_type: ResourceType
    risk_level: RiskLevel
    rationale: str = ""


@dataclass
class AllocationResult:
    total_resources: float
    allocations: List[ResourceAllocation]
    unallocated: float
    strategy: AllocationStrategy

    @property
    def allocated_total(self) -> float:
        return sum(a.allocated_amount for a in self.allocations)


class ResourceAllocator:
    def __init__(
        self,
        total_resources: float,
        resource_type: ResourceType = ResourceType.BUDGET,
        min_allocation: float = 0.0,
    ):
        if total_resources < 0:
            raise ValueError(
                f"total_resources must be >= 0, got {total_resources}"
            )
        self.total_resources = total_resources
        self.resource_type = resource_type
        self.min_allocation = min_allocation

    def allocate_by_risk(
        self,
        assessments: Dict[str, RiskAssessment],
    ) -> AllocationResult:
        if not assessments:
            return AllocationResult(
                total_resources=self.total_resources,
                allocations=[],
                unallocated=self.total_resources,
                strategy=AllocationStrategy.PROPORTIONAL,
            )

        total_score = sum(a.expected_value for a in assessments.values())
        if total_score == 0:
            return self._equal_split(assessments, AllocationStrategy.PROPORTIONAL)

        raw: Dict[str, float] = {}
        for name, a in assessments.items():
            amount = (a.expected_value / total_score) * self.total_resources
            if amount < self.min_allocation:
                amount = self.min_allocation
            raw[name] = amount

        raw = self._scale_if_over(raw)
        allocations = self._build_allocations(
            assessments, raw, "proportional to risk EV",
        )
        unallocated = round(
            self.total_resources - sum(a.allocated_amount for a in allocations), 2
        )

        return AllocationResult(
            total_resources=self.total_resources,
            allocations=allocations,
            unallocated=unallocated,
            strategy=AllocationStrategy.PROPORTIONAL,
        )

    def allocate_by_threshold(
        self,
        assessments: Dict[str, RiskAssessment],
        threshold: RiskLevel,
    ) -> AllocationResult:
        if not assessments:
            return AllocationResult(
                total_resources=self.total_resources,
                allocations=[],
                unallocated=self.total_resources,
                strategy=AllocationStrategy.THRESHOLD,
            )

        above = {
            n: a
            for n, a in assessments.items()
            if a.level.score() >= threshold.score()
        }
        if not above:
            return AllocationResult(
                total_resources=self.total_resources,
                allocations=[],
                unallocated=self.total_resources,
                strategy=AllocationStrategy.THRESHOLD,
            )

        total_score = sum(a.expected_value for a in above.values())
        if total_score == 0:
            return self._equal_split(above, AllocationStrategy.THRESHOLD)

        raw: Dict[str, float] = {}
        for name, a in above.items():
            amount = (a.expected_value / total_score) * self.total_resources
            if amount < self.min_allocation:
                amount = self.min_allocation
            raw[name] = amount

        raw = self._scale_if_over(raw)
        allocations = self._build_allocations(
            above, raw, f"above {threshold.value} threshold",
        )
        unallocated = round(
            self.total_resources - sum(a.allocated_amount for a in allocations), 2
        )

        return AllocationResult(
            total_resources=self.total_resources,
            allocations=allocations,
            unallocated=unallocated,
            strategy=AllocationStrategy.THRESHOLD,
        )

    def _equal_split(
        self,
        assessments: Dict[str, RiskAssessment],
        strategy: AllocationStrategy,
    ) -> AllocationResult:
        equal_share = round(self.total_resources / len(assessments), 2)
        allocations = [
            ResourceAllocation(
                item_name=name,
                allocated_amount=equal_share,
                resource_type=self.resource_type,
                risk_level=a.level,
                rationale="equal split (zero risk scores)",
            )
            for name, a in assessments.items()
        ]
        total_allocated = sum(a.allocated_amount for a in allocations)
        return AllocationResult(
            total_resources=self.total_resources,
            allocations=allocations,
            unallocated=round(self.total_resources - total_allocated, 2),
            strategy=strategy,
        )

    def _scale_if_over(self, raw: Dict[str, float]) -> Dict[str, float]:
        total = sum(raw.values())
        if total <= self.total_resources:
            return raw
        scale = self.total_resources / total
        return {k: round(v * scale, 2) for k, v in raw.items()}

    def _build_allocations(
        self,
        assessments: Dict[str, RiskAssessment],
        amounts: Dict[str, float],
        rationale_prefix: str,
    ) -> List[ResourceAllocation]:
        return [
            ResourceAllocation(
                item_name=name,
                allocated_amount=round(amounts[name], 2),
                resource_type=self.resource_type,
                risk_level=assessments[name].level,
                rationale=f"{rationale_prefix} ({assessments[name].expected_value:.3f})",
            )
            for name in assessments
        ]
