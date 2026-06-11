import pytest

from rbvas.calculator import CostBreakdown, CostCalculator
from rbvas.models import DecisionOption, RiskAssessment


def test_cost_breakdown_properties():
    cb = CostBreakdown(100, 50, 0.3, 150.3)
    assert cb.direct_cost == 100
    assert cb.indirect_cost == 50
    assert cb.expected_loss == 0.3
    assert cb.total_risk_adjusted_cost == 150.3
    assert cb.mitigation_cost_ratio == 0.3 / 150


def test_cost_breakdown_zero_denominator():
    cb = CostBreakdown(0, 0, 0.5, 0.5)
    assert cb.mitigation_cost_ratio == float("inf")


class TestCostCalculator:
    def test_calculate_no_risk(self):
        opt = DecisionOption(name="test", direct_cost=100, indirect_cost=20)
        calc = CostCalculator()
        cb = calc.calculate(opt)
        assert cb.direct_cost == 100
        assert cb.indirect_cost == 20
        assert cb.expected_loss == 0.0
        assert cb.total_risk_adjusted_cost == 120.0

    def test_calculate_with_residual_risk(self):
        risk = RiskAssessment(probability=0.5, impact=0.8)
        opt = DecisionOption(
            name="mitigated", direct_cost=200, indirect_cost=50, residual_risk=risk
        )
        calc = CostCalculator()
        cb = calc.calculate(opt)
        assert cb.direct_cost == 200
        assert cb.indirect_cost == 50
        assert cb.expected_loss == 0.4
        assert cb.total_risk_adjusted_cost == 250.4

    def test_rank_by_cost(self):
        opts = [
            DecisionOption(name="A", direct_cost=100),
            DecisionOption(name="B", direct_cost=200),
            DecisionOption(name="C", direct_cost=50),
        ]
        calc = CostCalculator()
        ranked = calc.rank_by_cost(opts)
        names = [o.name for o, _ in ranked]
        assert names == ["C", "A", "B"]

    def test_calculate_with_base_risk(self):
        base = RiskAssessment(probability=0.3, impact=0.5)
        opt = DecisionOption(name="test", direct_cost=100)
        calc = CostCalculator()
        cb = calc.calculate(opt, base)
        assert cb.expected_loss == 0.15
        assert cb.total_risk_adjusted_cost == 100.15
