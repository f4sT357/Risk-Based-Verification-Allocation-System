import pytest

from rbvas.models import DecisionOption, RiskAssessment, RiskLevel


class TestRiskLevel:
    def test_score(self):
        assert RiskLevel.LOW.score() == 1
        assert RiskLevel.MEDIUM.score() == 2
        assert RiskLevel.HIGH.score() == 3
        assert RiskLevel.CRITICAL.score() == 4

    def test_from_score(self):
        assert RiskLevel.from_score(0.5) == RiskLevel.LOW
        assert RiskLevel.from_score(1.5) == RiskLevel.LOW
        assert RiskLevel.from_score(1.6) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(2.5) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(2.6) == RiskLevel.HIGH
        assert RiskLevel.from_score(3.5) == RiskLevel.HIGH
        assert RiskLevel.from_score(3.6) == RiskLevel.CRITICAL


class TestRiskAssessment:
    def test_valid_creation(self):
        r = RiskAssessment(probability=0.3, impact=0.7, description="test")
        assert r.probability == 0.3
        assert r.impact == 0.7
        assert r.description == "test"

    def test_invalid_probability(self):
        with pytest.raises(ValueError):
            RiskAssessment(probability=1.5, impact=0.5)

    def test_invalid_impact(self):
        with pytest.raises(ValueError):
            RiskAssessment(probability=0.5, impact=-0.1)

    def test_expected_value(self):
        r = RiskAssessment(probability=0.4, impact=0.5)
        assert r.expected_value == 0.2

    def test_level(self):
        assert RiskAssessment(0.1, 0.1).level == RiskLevel.LOW
        assert RiskAssessment(0.7, 0.7).level == RiskLevel.MEDIUM
        assert RiskAssessment(0.9, 0.9).level == RiskLevel.HIGH
        assert RiskAssessment(1.0, 1.0).level == RiskLevel.CRITICAL


class TestDecisionOption:
    def test_total_direct_cost(self):
        opt = DecisionOption(name="opt", direct_cost=100, indirect_cost=30)
        assert opt.total_direct_cost == 130

    def test_total_direct_cost_zero_indirect(self):
        opt = DecisionOption(name="opt", direct_cost=100)
        assert opt.total_direct_cost == 100
