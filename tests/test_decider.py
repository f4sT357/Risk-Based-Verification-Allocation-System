import pytest

from rbvas.decider import DecisionCriteria, RiskBasedDecider
from rbvas.models import DecisionOption, RiskAssessment, RiskLevel


class TestDecisionCriteria:
    def test_accept_within_budget(self):
        criteria = DecisionCriteria(max_budget=500)
        opt = DecisionOption(name="test", direct_cost=100)
        cb = RiskBasedDecider().calculator.calculate(opt)
        assert criteria.is_acceptable(opt, cb)

    def test_reject_over_budget(self):
        criteria = DecisionCriteria(max_budget=50)
        opt = DecisionOption(name="test", direct_cost=100)
        cb = RiskBasedDecider().calculator.calculate(opt)
        assert not criteria.is_acceptable(opt, cb)


class TestRiskBasedDecider:
    def test_evaluate_selects_lowest_cost(self):
        opts = [
            DecisionOption(name="expensive", direct_cost=500),
            DecisionOption(name="cheap", direct_cost=50),
            DecisionOption(name="mid", direct_cost=200),
        ]
        decider = RiskBasedDecider()
        result = decider.evaluate(opts)
        assert result.selected_option.name == "cheap"

    def test_evaluate_respects_risk_level(self):
        critical_risk = RiskAssessment(probability=0.9, impact=0.9)
        low_risk = RiskAssessment(probability=0.1, impact=0.1)

        opts = [
            DecisionOption(
                name="risky", direct_cost=10, residual_risk=critical_risk
            ),
            DecisionOption(
                name="safe", direct_cost=200, residual_risk=low_risk
            ),
        ]
        criteria = DecisionCriteria(max_risk_level=RiskLevel.MEDIUM)
        decider = RiskBasedDecider(criteria=criteria)
        result = decider.evaluate(opts)
        assert result.selected_option.name == "safe"

    def test_evaluate_with_sensitivity(self):
        base_risk = RiskAssessment(probability=0.3, impact=0.5)
        opts = [
            DecisionOption(name="A", direct_cost=100),
            DecisionOption(name="B", direct_cost=200),
        ]
        decider = RiskBasedDecider()
        results = decider.evaluate_with_sensitivity(opts, base_risk, [0.5, 1.0, 2.0])
        assert set(results.keys()) == {0.5, 1.0, 2.0}
        for multiplier, result in results.items():
            assert result.selected_option.name is not None

    def test_evaluate_no_acceptable_options(self):
        opts = [
            DecisionOption(name="only_option", direct_cost=9999),
        ]
        criteria = DecisionCriteria(max_budget=100)
        decider = RiskBasedDecider(criteria=criteria)
        result = decider.evaluate(opts)
        assert result.selected_option.name == "only_option"

    def test_alternative_options_are_ranked(self):
        opts = [
            DecisionOption(name="best", direct_cost=50),
            DecisionOption(name="second", direct_cost=100),
            DecisionOption(name="worst", direct_cost=200),
        ]
        decider = RiskBasedDecider()
        result = decider.evaluate(opts)
        alt_names = [o.name for o in result.alternative_options]
        assert alt_names == ["second", "worst"]
