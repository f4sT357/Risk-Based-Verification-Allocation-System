from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import DecisionOption, RiskAssessment


@dataclass
class CostBreakdown:
    direct_cost: float
    indirect_cost: float
    expected_loss: float
    total_risk_adjusted_cost: float

    @property
    def mitigation_cost_ratio(self) -> float:
        denominator = self.direct_cost + self.indirect_cost
        if denominator == 0:
            return float("inf")
        return self.expected_loss / denominator

    def __str__(self) -> str:
        return (
            f"CostBreakdown(\n"
            f"  direct={self.direct_cost:.2f},\n"
            f"  indirect={self.indirect_cost:.2f},\n"
            f"  expected_loss={self.expected_loss:.4f},\n"
            f"  risk_adjusted={self.total_risk_adjusted_cost:.4f},\n"
            f"  ratio={self.mitigation_cost_ratio:.4f}\n"
            f")"
        )


class CostCalculator:
    def calculate(
        self, option: DecisionOption, base_risk: RiskAssessment | None = None
    ) -> CostBreakdown:
        direct = option.direct_cost
        indirect = option.indirect_cost

        residual = option.residual_risk or base_risk
        expected_loss = residual.expected_value if residual else 0.0

        total = direct + indirect + expected_loss

        return CostBreakdown(
            direct_cost=direct,
            indirect_cost=indirect,
            expected_loss=expected_loss,
            total_risk_adjusted_cost=total,
        )

    def rank_by_cost(
        self,
        options: List[DecisionOption],
        base_risk: RiskAssessment | None = None,
    ) -> List[tuple[DecisionOption, CostBreakdown]]:
        scored = [
            (opt, self.calculate(opt, base_risk)) for opt in options
        ]
        scored.sort(key=lambda x: x[1].total_risk_adjusted_cost)
        return scored
