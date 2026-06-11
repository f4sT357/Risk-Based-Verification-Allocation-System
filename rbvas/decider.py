from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .calculator import CostBreakdown, CostCalculator
from .models import DecisionOption, DecisionResult, RiskAssessment, RiskLevel


@dataclass
class DecisionCriteria:
    max_budget: float = float("inf")
    max_risk_level: RiskLevel = RiskLevel.CRITICAL
    max_cost_benefit_ratio: float = float("inf")
    require_mitigation: bool = False
    risk_tolerance: float = 1.0

    def is_acceptable(self, option: DecisionOption, breakdown: CostBreakdown) -> bool:
        total = breakdown.total_risk_adjusted_cost
        if total > self.max_budget:
            return False
        if option.residual_risk and option.residual_risk.level.score() > self.max_risk_level.score():
            return False
        if breakdown.mitigation_cost_ratio > self.max_cost_benefit_ratio:
            return False
        return True


class RiskBasedDecider:
    def __init__(
        self,
        criteria: Optional[DecisionCriteria] = None,
        calculator: Optional[CostCalculator] = None,
    ):
        self.criteria = criteria or DecisionCriteria()
        self.calculator = calculator or CostCalculator()

    def evaluate(
        self,
        options: List[DecisionOption],
        base_risk: Optional[RiskAssessment] = None,
    ) -> DecisionResult:
        breakdowns: Dict[str, CostBreakdown] = {}

        scored = []
        for opt in options:
            cb = self.calculator.calculate(opt, base_risk)
            breakdowns[opt.name] = cb
            acceptable = self.criteria.is_acceptable(opt, cb)
            scored.append((opt, cb, acceptable))

        acceptable_options = [(o, c) for o, c, a in scored if a]

        if acceptable_options:
            best = min(acceptable_options, key=lambda x: x[1].total_risk_adjusted_cost)
            selected_option, selected_breakdown = best
        else:
            selected_option = options[0]
            selected_breakdown = breakdowns[selected_option.name]

        alternatives = sorted(
            [o for o, _, _ in scored if o.name != selected_option.name],
            key=lambda o: breakdowns[o.name].total_risk_adjusted_cost,
        )

        return DecisionResult(
            selected_option=selected_option,
            total_cost=selected_breakdown.total_risk_adjusted_cost,
            cost_breakdown=selected_breakdown,
            criteria=self.criteria,
            alternative_options=alternatives,
        )

    def evaluate_with_sensitivity(
        self,
        options: List[DecisionOption],
        base_risk: RiskAssessment,
        risk_multipliers: List[float],
    ) -> Dict[float, DecisionResult]:
        results: Dict[float, DecisionResult] = {}
        for multiplier in sorted(risk_multipliers):
            adjusted = RiskAssessment(
                probability=min(base_risk.probability * multiplier, 1.0),
                impact=base_risk.impact,
                description=f"{base_risk.description} (x{multiplier})",
            )
            results[multiplier] = self.evaluate(options, adjusted)
        return results
