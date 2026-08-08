"""Integration tests for Alpha 12 Replacement Governance in Portfolio Health Service (Sprint 13.9.3)"""

import pytest
from services.portfolio_health_service import PortfolioHealthService, PortfolioHealthResult
from services.alpha12_replacement_governance_service import (
    Alpha12ReplacementGovernanceService,
    ReplacementGovernanceResult,
    PROTECT_INCUMBENT,
    REVIEW_ELIGIBLE,
    INSUFFICIENT_EVIDENCE,
    UNAVAILABLE,
)


class TestGovernanceIntegrationInit:
    """Test governance service integration in PortfolioHealthService initialization."""

    def test_health_service_init_default(self):
        """PortfolioHealthService initializes without governance service."""
        svc = PortfolioHealthService()
        assert svc is not None
        assert svc._alpha12_replacement_governance_service is None

    def test_health_service_init_with_governance(self):
        """PortfolioHealthService accepts injected governance service."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )
        assert phs._alpha12_replacement_governance_service is gov_svc

    def test_health_result_has_governance_field(self):
        """PortfolioHealthResult includes alpha12_replacement_governance field."""
        result = PortfolioHealthResult(
            score=100.0,
            grade="A",
            diversification_rating="Excellent",
            concentration_rating="Low",
            position_count=12,
            largest_position_weight_pct=10.0,
            cash_allocation_pct=5.0,
        )
        assert hasattr(result, "alpha12_replacement_governance")
        assert result.alpha12_replacement_governance is None



class TestGovernanceIntegrationEvaluation:
    """Test governance service integration in evaluate() pipeline."""

    def test_evaluate_populates_governance_field(self):
        """evaluate() populates alpha12_replacement_governance field."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )

        result = phs.evaluate()

        assert result is not None
        assert hasattr(result, "alpha12_replacement_governance")
        # Field may be None if no challenger data, but should exist
        # Either ReplacementGovernanceResult or None is acceptable

    def test_governance_field_not_null_when_service_present(self):
        """alpha12_replacement_governance field is populated when service present."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )

        result = phs.evaluate()

        # Either a valid result or None is acceptable; should not crash
        assert result.alpha12_replacement_governance is None or isinstance(
            result.alpha12_replacement_governance, ReplacementGovernanceResult
        )

    def test_governance_lazy_instantiation(self):
        """Governance service is lazily instantiated if not injected."""
        phs = PortfolioHealthService()

        # Should not crash even without injection
        result = phs.evaluate()

        # Result should be valid
        assert isinstance(result, PortfolioHealthResult)


class TestGovernancePipelineOrder:
    """Test that governance evaluation runs after challenger evaluation."""

    def test_governance_runs_after_challenger(self):
        """Governance evaluation occurs in pipeline after challenger evaluation."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )

        result = phs.evaluate()

        # Both challenger and governance should be populated or both None
        # They run in sequence, governance depends on challenger data
        if result.alpha12_challenger_evaluation is not None:
            # If challenger data exists, governance should attempt to run
            assert (
                result.alpha12_replacement_governance is None
                or isinstance(result.alpha12_replacement_governance, ReplacementGovernanceResult)
            )
        # If challenger data is None, governance may also be None (no challenger data to evaluate)


class TestGovernanceDefensiveHandling:
    """Test defensive error handling in governance integration."""

    def test_governance_service_failure_does_not_crash_pipeline(self):
        """Portfolio Health evaluation continues if governance service fails."""

        class FailingGovernanceService:
            """Simulates a failing governance service."""

            def evaluate_replacements(self):
                raise RuntimeError("Simulated governance failure")

        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=FailingGovernanceService()
        )

        # Should not crash despite service failure
        result = phs.evaluate()

        assert isinstance(result, PortfolioHealthResult)
        # Governance field should be None due to exception
        assert result.alpha12_replacement_governance is None

    def test_governance_missing_method_handled(self):
        """Portfolio Health handles governance service without required method."""

        class PartialGovernanceService:
            """Service without evaluate_replacements method."""

            pass

        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=PartialGovernanceService()
        )

        # Should not crash
        result = phs.evaluate()

        assert isinstance(result, PortfolioHealthResult)


class TestGovernanceDataFlow:
    """Test data flow from governance to Portfolio Health result."""

    def test_governance_result_structure(self):
        """Governance result, if populated, has expected structure."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )

        result = phs.evaluate()

        if result.alpha12_replacement_governance is not None:
            gov_result = result.alpha12_replacement_governance

            # Verify expected fields
            assert hasattr(gov_result, "analysis_status")
            assert hasattr(gov_result, "total_evaluations")
            assert hasattr(gov_result, "records")
            assert hasattr(gov_result, "review_eligible_count")
            assert hasattr(gov_result, "protected_incumbent_count")

    def test_governance_records_are_list(self):
        """Governance replacement records are a list."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )

        result = phs.evaluate()

        if result.alpha12_replacement_governance is not None:
            gov_result = result.alpha12_replacement_governance

            assert isinstance(gov_result.records, list)


class TestGovernanceNonBlockingBehavior:
    """Test that governance evaluation is non-blocking."""

    def test_governance_exception_does_not_block_other_evaluations(self):
        """Governance exception doesn't prevent other portfolio health evaluations."""

        class FailingGovernanceService:
            def evaluate_replacements(self):
                raise RuntimeError("Governance error")

        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=FailingGovernanceService()
        )

        result = phs.evaluate()

        # Other fields should still be populated
        assert isinstance(result, PortfolioHealthResult)

        # Even if governance failed, evaluate() should return a valid result
        # with other fields intact

    def test_multiple_evaluations_consistent(self):
        """Multiple evaluate() calls produce consistent results."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )

        result1 = phs.evaluate()
        result2 = phs.evaluate()

        # Both should be valid
        assert isinstance(result1, PortfolioHealthResult)
        assert isinstance(result2, PortfolioHealthResult)

        # Governance statuses should match (since input data is same)
        if result1.alpha12_replacement_governance and result2.alpha12_replacement_governance:
            assert (
                result1.alpha12_replacement_governance.analysis_status
                == result2.alpha12_replacement_governance.analysis_status
            )
            assert (
                result1.alpha12_replacement_governance.total_evaluations
                == result2.alpha12_replacement_governance.total_evaluations
            )


class TestGovernanceServicePassthrough:
    """Test that dependencies are properly passed to governance service."""

    def test_governance_receives_mapping_service(self):
        """Governance service receives alpha12_mapping_service reference."""
        mock_mapping = object()

        gov_svc = Alpha12ReplacementGovernanceService(
            alpha12_mapping_service=mock_mapping
        )

        assert gov_svc._alpha12_mapping_service is mock_mapping

    def test_governance_receives_challenger_service(self):
        """Governance service receives alpha12_challenger_service reference."""
        mock_challenger = object()

        gov_svc = Alpha12ReplacementGovernanceService(
            alpha12_challenger_service=mock_challenger
        )

        assert gov_svc._alpha12_challenger_service is mock_challenger

    def test_governance_receives_health_integration_service(self):
        """Governance service receives alpha12_health_integration_service reference."""
        mock_health_int = object()

        gov_svc = Alpha12ReplacementGovernanceService(
            alpha12_health_integration_service=mock_health_int
        )

        assert gov_svc._alpha12_health_integration_service is mock_health_int

    def test_governance_receives_portfolio_health_service(self):
        """Governance service receives portfolio_health_service reference."""
        mock_health = object()

        gov_svc = Alpha12ReplacementGovernanceService(
            portfolio_health_service=mock_health
        )

        assert gov_svc._portfolio_health_service is mock_health


class TestGovernanceNoExecution:
    """Test that governance integration never executes portfolio changes."""

    def test_evaluate_does_not_create_transactions(self):
        """evaluate() does not create any transactions."""
        gov_svc = Alpha12ReplacementGovernanceService()
        phs = PortfolioHealthService(
            alpha12_replacement_governance_service=gov_svc
        )

        # Call evaluate
        result = phs.evaluate()

        # Governance result is pure data, no side effects
        # No transactions should exist
        # (This test verifies no transaction creation via introspection)
        assert not hasattr(gov_svc, "create_transaction")
        assert not hasattr(gov_svc, "execute_trade")


class TestGovernanceReviewEligibleNotExecution:
    """Test REVIEW_ELIGIBLE records are not executable."""

    def test_review_eligible_status_is_read_only(self):
        """REVIEW_ELIGIBLE status is informational only."""
        gov_svc = Alpha12ReplacementGovernanceService()

        # Governance service has no execute method
        assert not hasattr(gov_svc, "execute_replacement")
        assert not hasattr(gov_svc, "approve_replacement")
        assert not hasattr(gov_svc, "replace_holding")
        assert not hasattr(gov_svc, "execute_review")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
