import pytest

from rbvas.models import RiskAssessment, RiskLevel
from rbvas.resource_allocator import (
    AllocationResult,
    AllocationStrategy,
    ResourceAllocation,
    ResourceAllocator,
    ResourceType,
)


class TestResourceAllocatorInit:
    def test_valid_creation(self):
        allocator = ResourceAllocator(
            total_resources=1000.0,
            resource_type=ResourceType.TIME,
            min_allocation=10.0,
        )
        assert allocator.total_resources == 1000.0
        assert allocator.resource_type == ResourceType.TIME
        assert allocator.min_allocation == 10.0

    def test_negative_resources_raises(self):
        with pytest.raises(ValueError):
            ResourceAllocator(total_resources=-1)

    def test_default_resource_type_is_budget(self):
        allocator = ResourceAllocator(total_resources=500)
        assert allocator.resource_type == ResourceType.BUDGET

    def test_default_min_allocation_is_zero(self):
        allocator = ResourceAllocator(total_resources=500)
        assert allocator.min_allocation == 0.0


class TestAllocateByRisk:
    def test_empty_assessments(self):
        allocator = ResourceAllocator(total_resources=1000)
        result = allocator.allocate_by_risk({})
        assert result.allocations == []
        assert result.unallocated == 1000.0
        assert result.strategy == AllocationStrategy.PROPORTIONAL

    def test_proportional_distribution(self):
        assessments = {
            "item_a": RiskAssessment(probability=0.5, impact=0.8),
            "item_b": RiskAssessment(probability=0.3, impact=0.4),
        }
        allocator = ResourceAllocator(total_resources=1000)
        result = allocator.allocate_by_risk(assessments)
        assert len(result.allocations) == 2
        assert result.strategy == AllocationStrategy.PROPORTIONAL

        ev_a = 0.5 * 0.8
        ev_b = 0.3 * 0.4
        total_ev = ev_a + ev_b
        expected_a = round((ev_a / total_ev) * 1000, 2)
        expected_b = round((ev_b / total_ev) * 1000, 2)

        alloc_a = next(a for a in result.allocations if a.item_name == "item_a")
        alloc_b = next(a for a in result.allocations if a.item_name == "item_b")
        assert alloc_a.allocated_amount == expected_a
        assert alloc_b.allocated_amount == expected_b
        assert result.allocated_total == expected_a + expected_b

    def test_zero_risk_scores_equal_split(self):
        assessments = {
            "a": RiskAssessment(probability=0.0, impact=0.0),
            "b": RiskAssessment(probability=0.0, impact=0.0),
        }
        allocator = ResourceAllocator(total_resources=100)
        result = allocator.allocate_by_risk(assessments)
        assert len(result.allocations) == 2
        for alloc in result.allocations:
            assert alloc.allocated_amount == 50.0

    def test_allocation_uses_resource_type(self):
        assessments = {
            "item": RiskAssessment(probability=0.5, impact=0.5),
        }
        allocator = ResourceAllocator(
            total_resources=100, resource_type=ResourceType.PERSONNEL,
        )
        result = allocator.allocate_by_risk(assessments)
        assert result.allocations[0].resource_type == ResourceType.PERSONNEL

    def test_min_allocation_enforced_when_feasible(self):
        assessments = {
            "low_risk": RiskAssessment(probability=0.1, impact=0.1),
            "high_risk": RiskAssessment(probability=0.9, impact=0.9),
        }
        allocator = ResourceAllocator(
            total_resources=1000, min_allocation=10.0,
        )
        result = allocator.allocate_by_risk(assessments)
        for alloc in result.allocations:
            assert alloc.allocated_amount >= 10.0

    def test_single_item_gets_all(self):
        assessments = {
            "only": RiskAssessment(probability=0.8, impact=0.7),
        }
        allocator = ResourceAllocator(total_resources=500)
        result = allocator.allocate_by_risk(assessments)
        assert result.allocations[0].allocated_amount == 500.0
        assert result.unallocated == 0.0


class TestAllocateByThreshold:
    def test_empty_assessments(self):
        allocator = ResourceAllocator(total_resources=1000)
        result = allocator.allocate_by_threshold({}, RiskLevel.HIGH)
        assert result.allocations == []
        assert result.unallocated == 1000.0

    def test_no_items_above_threshold(self):
        assessments = {
            "low": RiskAssessment(probability=0.1, impact=0.1),
            "medium": RiskAssessment(probability=0.3, impact=0.3),
        }
        allocator = ResourceAllocator(total_resources=1000)
        result = allocator.allocate_by_threshold(
            assessments, RiskLevel.HIGH,
        )
        assert result.allocations == []
        assert result.unallocated == 1000.0

    def test_only_above_threshold_get_resources(self):
        assessments = {
            "low": RiskAssessment(probability=0.1, impact=0.1),
            "critical": RiskAssessment(probability=0.9, impact=0.9),
        }
        allocator = ResourceAllocator(total_resources=600)
        result = allocator.allocate_by_threshold(
            assessments, RiskLevel.HIGH,
        )
        names = [a.item_name for a in result.allocations]
        assert "low" not in names
        assert "critical" in names
        assert len(result.allocations) == 1
        assert result.allocations[0].allocated_amount == 600.0

    def test_threshold_distribution(self):
        assessments = {
            "high_a": RiskAssessment(probability=0.8, impact=0.8),
            "high_b": RiskAssessment(probability=0.75, impact=0.85),
            "low": RiskAssessment(probability=0.1, impact=0.1),
        }
        allocator = ResourceAllocator(total_resources=1000)
        result = allocator.allocate_by_threshold(
            assessments, RiskLevel.HIGH,
        )
        assert len(result.allocations) == 2
        for alloc in result.allocations:
            assert alloc.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert result.allocated_total <= 1000.0

    def test_threshold_zero_risk_above(self):
        assessments = {
            "a": RiskAssessment(probability=0.0, impact=0.0),
            "b": RiskAssessment(probability=0.0, impact=0.0),
        }
        allocator = ResourceAllocator(total_resources=200)
        result = allocator.allocate_by_threshold(
            assessments, RiskLevel.LOW,
        )
        assert len(result.allocations) == 2
        for alloc in result.allocations:
            assert alloc.allocated_amount == 100.0


class TestAllocationResult:
    def test_allocated_total_property(self):
        alloc1 = ResourceAllocation(
            "a", 100.0, ResourceType.BUDGET, RiskLevel.HIGH,
        )
        alloc2 = ResourceAllocation(
            "b", 200.0, ResourceType.BUDGET, RiskLevel.MEDIUM,
        )
        result = AllocationResult(
            total_resources=500,
            allocations=[alloc1, alloc2],
            unallocated=200.0,
            strategy=AllocationStrategy.PROPORTIONAL,
        )
        assert result.allocated_total == 300.0
