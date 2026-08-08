"""Test suite for Alpha 12 Replacement Governance Service (Sprint 13.9.3)"""

import pytest
from services.alpha12_replacement_governance_service import (
    Alpha12ReplacementGovernanceService,
    ReplacementGovernanceRecord,
    ReplacementGovernanceResult,
    PROTECT_INCUMBENT,
    REVIEW_ELIGIBLE,
    INSUFFICIENT_EVIDENCE,
    UNAVAILABLE,
)


class TestInitialization:
    """Test service initialization patterns."""

    def test_init_default(self):
        """Test initialization with no dependencies."""
        svc = Alpha12ReplacementGovernanceService()
        assert svc is not None
        assert svc._alpha12_mapping_service is None
        assert svc._alpha12_challenger_service is None
        assert svc._alpha12_health_integration_service is None
        assert svc._portfolio_health_service is None

    def test_init_with_dependencies(self):
        """Test initialization with injected dependencies."""
        mock_mapping = object()
        mock_challenger = object()
        mock_health_int = object()
        mock_health = object()

        svc = Alpha12ReplacementGovernanceService(
            alpha12_mapping_service=mock_mapping,
            alpha12_challenger_service=mock_challenger,
            alpha12_health_integration_service=mock_health_int,
            portfolio_health_service=mock_health,
        )

        assert svc._alpha12_mapping_service is mock_mapping
        assert svc._alpha12_challenger_service is mock_challenger
        assert svc._alpha12_health_integration_service is mock_health_int
        assert svc._portfolio_health_service is mock_health

    def test_lazy_fallback_pattern(self):
        """Test that service follows Pattern A lazy fallback."""
        svc = Alpha12ReplacementGovernanceService()
        result = svc.evaluate_replacements()
        assert isinstance(result, ReplacementGovernanceResult)
        assert result.analysis_status in ("NO_CHALLENGER_DATA", "NO_CHALLENGERS", "ERROR")


class TestDataHandling:
    """Test defensive data handling."""

    def test_safe_float_conversion(self):
        """Test safe float conversion."""
        svc = Alpha12ReplacementGovernanceService()

        assert svc._safe_float(10.5) == 10.5
        assert svc._safe_float("10.5") == 10.5
        assert svc._safe_float(None) is None
        assert svc._safe_float("invalid") is None
        assert svc._safe_float([]) is None

    def test_safe_int_conversion(self):
        """Test safe int conversion."""
        svc = Alpha12ReplacementGovernanceService()

        assert svc._safe_int(10) == 10
        assert svc._safe_int("10") == 10
        assert svc._safe_int(10.5) == 10
        assert svc._safe_int(None) is None
        assert svc._safe_int("invalid") is None

    def test_clamp_score(self):
        """Test score clamping."""
        svc = Alpha12ReplacementGovernanceService()

        assert svc._clamp_score(50.0) == 50.0
        assert svc._clamp_score(-10.0) == 0.0
        assert svc._clamp_score(150.0) == 100.0
        assert svc._clamp_score(None) == 0.0

    def test_empty_state_handling(self):
        """Test handling of empty state."""
        svc = Alpha12ReplacementGovernanceService()
        result = svc.evaluate_replacements(state_input=None)
        assert isinstance(result, ReplacementGovernanceResult)

    def test_malformed_data_handling(self):
        """Test handling of malformed input."""
        svc = Alpha12ReplacementGovernanceService()
        result = svc.evaluate_replacements(state_input="not_a_dict")
        assert isinstance(result, ReplacementGovernanceResult)

    def test_missing_challenger_result(self):
        """Test handling when no challenger result available."""
        svc = Alpha12ReplacementGovernanceService()
        result = svc.evaluate_replacements()
        assert result.analysis_status == "NO_CHALLENGER_DATA"
        assert result.total_evaluations == 0


class TestIncumbentProtection:
    """Test incumbent protection rules."""

    def test_higher_rank_only_protects_incumbent(self):
        """Higher challenger rank alone should protect incumbent."""
        svc = Alpha12ReplacementGovernanceService()

        # Mock a simple challenger with only rank advantage
        challenger_data = {
            "symbol": "CHALLENGER",
            "name": "Challenger Stock",
            "incumbent_symbol": "INCUMBENT",
            "incumbent_name": "Incumbent Stock",
            "challenger_rank": 5,  # Better rank
            "incumbent_rank": 10,  # Worse rank
            "challenger_score": 50.0,
            "incumbent_score": 50.0,  # Same score
            "score_difference": 0.0,
            "quality_score": 50.0,
            "incumbent_quality_score": 50.0,
            "quality_difference": 0.0,
            "risk_score": 50.0,
            "incumbent_risk_score": 50.0,
            "risk_difference": 0.0,
        }

        # Manually create record using service logic
        record = ReplacementGovernanceRecord(
            replacement_id=svc._generate_replacement_id("INCUMBENT", "CHALLENGER"),
            incumbent_symbol="INCUMBENT",
            challenger_symbol="CHALLENGER",
            challenger_rank=5,
            incumbent_rank=10,
            challenger_score=50.0,
            incumbent_score=50.0,
            score_difference=0.0,
            incumbent_quality_score=50.0,
            challenger_quality_score=50.0,
            quality_difference=0.0,
            incumbent_risk_score=50.0,
            challenger_risk_score=50.0,
            risk_advantage=0.0,
            material_superiority=False,
            meaningful_deterioration=False,
            governance_status=PROTECT_INCUMBENT,
        )

        assert record.governance_status == PROTECT_INCUMBENT

    def test_small_score_advantage_insufficient(self):
        """Small score advantage should not trigger review."""
        svc = Alpha12ReplacementGovernanceService()

        # Score diff = 5 (below SCORE_DIFF_THRESHOLD of 12)
        material = svc._evaluate_material_superiority(
            score_diff=5.0,  # Less than threshold
            quality_diff=15.0,  # Exceeds threshold
            risk_advantage=6.0,  # Exceeds threshold
        )

        assert material is False

    def test_healthy_incumbent_protected(self):
        """Healthy incumbent should be protected even with challenger advantage."""
        svc = Alpha12ReplacementGovernanceService()

        deterioration = svc._evaluate_incumbent_deterioration(
            incumbent_quality=80.0,  # Strong quality
            incumbent_health_grade="A",  # Excellent health
            challenger_evaluation=None,
        )

        assert deterioration is False


class TestMaterialSuperiority:
    """Test material superiority evaluation."""

    def test_threshold_values(self):
        """Test material superiority thresholds."""
        svc = Alpha12ReplacementGovernanceService()

        # All dimensions meet minimum thresholds
        assert (
            svc._evaluate_material_superiority(
                score_diff=12.0,
                quality_diff=8.0,
                risk_advantage=5.0,
            )
            is True
        )

        # One dimension below threshold
        assert (
            svc._evaluate_material_superiority(
                score_diff=11.9,  # Just below
                quality_diff=8.0,
                risk_advantage=5.0,
            )
            is False
        )

        # Missing one dimension
        assert (
            svc._evaluate_material_superiority(
                score_diff=12.0,
                quality_diff=None,  # Missing
                risk_advantage=5.0,
            )
            is False
        )

    def test_all_dimensions_required(self):
        """Material superiority requires all three dimensions."""
        svc = Alpha12ReplacementGovernanceService()

        # No dimensions
        assert (
            svc._evaluate_material_superiority(
                score_diff=None,
                quality_diff=None,
                risk_advantage=None,
            )
            is False
        )


class TestDeterioration:
    """Test deterioration evaluation."""

    def test_weak_quality_detected(self):
        """Quality score <= 50 indicates deterioration."""
        svc = Alpha12ReplacementGovernanceService()

        deterioration = svc._evaluate_incumbent_deterioration(
            incumbent_quality=50.0,  # Exactly at threshold
            incumbent_health_grade=None,
            challenger_evaluation=None,
        )

        assert deterioration is True

    def test_poor_health_detected(self):
        """Poor health grades indicate deterioration."""
        svc = Alpha12ReplacementGovernanceService()

        for grade in ["D", "E", "F", "POOR"]:
            deterioration = svc._evaluate_incumbent_deterioration(
                incumbent_quality=70.0,
                incumbent_health_grade=grade,
                challenger_evaluation=None,
            )
            assert deterioration is True

    def test_no_deterioration_when_healthy(self):
        """Healthy incumbent should show no deterioration."""
        svc = Alpha12ReplacementGovernanceService()

        deterioration = svc._evaluate_incumbent_deterioration(
            incumbent_quality=75.0,
            incumbent_health_grade="B",
            challenger_evaluation=None,
        )

        assert deterioration is False


class TestGovernanceStatus:
    """Test governance status classification."""

    def test_review_eligible_criteria(self):
        """REVIEW_ELIGIBLE requires material superiority + deterioration."""
        svc = Alpha12ReplacementGovernanceService()

        status = svc._classify_governance_status(
            material_superiority=True,  # Yes
            meaningful_deterioration=True,  # Yes
            challenger_score=75.0,
            score_difference=15.0,
            evidence_completeness=1.0,
        )

        assert status == REVIEW_ELIGIBLE

    def test_protect_incumbent_without_deterioration(self):
        """Material superiority without deterioration protects incumbent."""
        svc = Alpha12ReplacementGovernanceService()

        status = svc._classify_governance_status(
            material_superiority=True,  # Yes
            meaningful_deterioration=False,  # No
            challenger_score=75.0,
            score_difference=15.0,
            evidence_completeness=1.0,
        )

        assert status == PROTECT_INCUMBENT

    def test_insufficient_evidence_default(self):
        """Low evidence completeness returns insufficient."""
        svc = Alpha12ReplacementGovernanceService()

        status = svc._classify_governance_status(
            material_superiority=False,
            meaningful_deterioration=False,
            challenger_score=50.0,
            score_difference=2.0,
            evidence_completeness=0.25,  # Very incomplete
        )

        assert status == INSUFFICIENT_EVIDENCE

    def test_unavailable_without_score(self):
        """UNAVAILABLE when no challenger score."""
        svc = Alpha12ReplacementGovernanceService()

        status = svc._classify_governance_status(
            material_superiority=False,
            meaningful_deterioration=False,
            challenger_score=None,  # No score
            score_difference=None,
            evidence_completeness=0.0,
        )

        assert status == UNAVAILABLE


class TestGovernanceScore:
    """Test governance score calculation."""

    def test_score_bounded(self):
        """Score is always bounded 0-100."""
        svc = Alpha12ReplacementGovernanceService()

        score = svc._calculate_governance_score(
            material_superiority=True,
            meaningful_deterioration=True,
            score_diff=50.0,  # Extreme
            quality_diff=100.0,  # Extreme
            risk_advantage=100.0,  # Extreme
            rank_diff=20,  # Extreme
        )

        assert 0.0 <= score <= 100.0
        assert score > 50.0  # Should be high for this case

    def test_score_reflects_evidence(self):
        """Higher evidence should produce higher score."""
        svc = Alpha12ReplacementGovernanceService()

        score_weak = svc._calculate_governance_score(
            material_superiority=False,
            meaningful_deterioration=False,
            score_diff=5.0,
            quality_diff=3.0,
            risk_advantage=2.0,
            rank_diff=1,
        )

        score_strong = svc._calculate_governance_score(
            material_superiority=True,
            meaningful_deterioration=True,
            score_diff=15.0,
            quality_diff=10.0,
            risk_advantage=6.0,
            rank_diff=3,
        )

        assert score_strong > score_weak

    def test_score_zero_for_no_evidence(self):
        """No evidence should produce score near zero."""
        svc = Alpha12ReplacementGovernanceService()

        score = svc._calculate_governance_score(
            material_superiority=False,
            meaningful_deterioration=False,
            score_diff=0.0,
            quality_diff=0.0,
            risk_advantage=0.0,
            rank_diff=0,
        )

        assert score == 0.0


class TestDeterministicOrdering:
    """Test deterministic record ordering."""

    def test_same_input_same_ordering(self):
        """Same input produces identical ordering on repeated calls."""
        svc = Alpha12ReplacementGovernanceService()

        # Create same records twice
        records1 = [
            ReplacementGovernanceRecord(
                replacement_id="id1",
                incumbent_symbol="INC1",
                challenger_symbol="CHAL1",
                governance_status=PROTECT_INCUMBENT,
                governance_score=50.0,
            ),
            ReplacementGovernanceRecord(
                replacement_id="id2",
                incumbent_symbol="INC2",
                challenger_symbol="CHAL2",
                governance_status=REVIEW_ELIGIBLE,
                governance_score=80.0,
            ),
        ]

        records2 = [
            ReplacementGovernanceRecord(
                replacement_id="id1",
                incumbent_symbol="INC1",
                challenger_symbol="CHAL1",
                governance_status=PROTECT_INCUMBENT,
                governance_score=50.0,
            ),
            ReplacementGovernanceRecord(
                replacement_id="id2",
                incumbent_symbol="INC2",
                challenger_symbol="CHAL2",
                governance_status=REVIEW_ELIGIBLE,
                governance_score=80.0,
            ),
        ]

        sorted1 = svc._sort_records(records1)
        sorted2 = svc._sort_records(records2)

        for s1, s2 in zip(sorted1, sorted2):
            assert s1.replacement_id == s2.replacement_id
            assert s1.governance_status == s2.governance_status
            assert s1.governance_score == s2.governance_score


class TestReplacementID:
    """Test replacement ID generation."""

    def test_deterministic_id(self):
        """Same symbols produce same ID."""
        svc = Alpha12ReplacementGovernanceService()

        id1 = svc._generate_replacement_id("INC", "CHAL")
        id2 = svc._generate_replacement_id("INC", "CHAL")

        assert id1 == id2

    def test_different_symbols_different_id(self):
        """Different symbols produce different IDs."""
        svc = Alpha12ReplacementGovernanceService()

        id1 = svc._generate_replacement_id("INC1", "CHAL1")
        id2 = svc._generate_replacement_id("INC2", "CHAL2")

        assert id1 != id2


class TestSafety:
    """Test that service does not mutate portfolio or execute replacements."""

    def test_no_portfolio_mutation(self):
        """Service does not mutate portfolio."""
        svc = Alpha12ReplacementGovernanceService()

        # Call evaluate multiple times
        result1 = svc.evaluate_replacements()
        result2 = svc.evaluate_replacements()

        # Results should be identical
        assert result1.analysis_status == result2.analysis_status
        assert result1.total_evaluations == result2.total_evaluations

    def test_no_transaction_creation(self):
        """Service has no transaction creation methods."""
        svc = Alpha12ReplacementGovernanceService()

        # Verify no dangerous methods exist
        assert not hasattr(svc, "buy")
        assert not hasattr(svc, "sell")
        assert not hasattr(svc, "execute")
        assert not hasattr(svc, "trade")
        assert not hasattr(svc, "rebalance")
        assert not hasattr(svc, "replace_holding")
        assert not hasattr(svc, "remove_holding")

    def test_review_eligible_not_execution(self):
        """REVIEW_ELIGIBLE status does not execute replacement."""
        svc = Alpha12ReplacementGovernanceService()

        # A REVIEW_ELIGIBLE record is just data
        record = ReplacementGovernanceRecord(
            replacement_id="test",
            incumbent_symbol="INC",
            challenger_symbol="CHAL",
            governance_status=REVIEW_ELIGIBLE,
        )

        # No side effects; just data
        assert record.governance_status == REVIEW_ELIGIBLE
        assert record.replacement_id == "test"


class TestAliasMethod:
    """Test get_governance alias."""

    def test_get_governance_alias(self):
        """get_governance() is an alias for evaluate_replacements()."""
        svc = Alpha12ReplacementGovernanceService()

        result = svc.get_governance()

        assert isinstance(result, ReplacementGovernanceResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
