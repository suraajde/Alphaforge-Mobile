from services.alpha12_health_integration_service import (
    Alpha12HealthIntegrationService,
    Alpha12HealthIntegrationResult,
)
from services.alpha12_mapping_service import (
    Alpha12MappingResult,
    Alpha12PortfolioMapping,
    Alpha12HoldingMapping,
)


def test_service_initialization():
    svc = Alpha12HealthIntegrationService()
    assert svc is not None


def test_empty_mapping_returns_unavailable():
    svc = Alpha12HealthIntegrationService()
    res = svc.get_health_integration(None, None)
    assert isinstance(res, Alpha12HealthIntegrationResult)
    assert res.analysis_status == "UNAVAILABLE"
    assert res.overlays == []


def test_simple_mapped_overlay_generation():
    svc = Alpha12HealthIntegrationService()

    holding = Alpha12HoldingMapping(
        symbol="ABC",
        name="Company ABC",
        alpha12_rank=1,
        alpha12_weight=5.0,
        current_weight=4.5,
        current_value=10000.0,
        mapping_status="MAPPED",
        evidence=["Exact symbol match"],
        rationale="Test mapping",
    )

    portfolio = Alpha12PortfolioMapping(
        mapping_status="MAPPED",
        total_alpha12_holdings=1,
        mapped_holdings=1,
        unmapped_holdings=0,
        mapping_coverage_pct=100.0,
        holdings=[holding],
    )

    mapping_result = Alpha12MappingResult(analysis_status="ANALYZED", portfolio=portfolio)

    res = svc.get_health_integration(mapping_result, None)

    assert isinstance(res, Alpha12HealthIntegrationResult)
    assert res.analysis_status == "ANALYZED"
    assert len(res.overlays) == 1
    ov = res.overlays[0]
    assert ov.symbol == "ABC"
    assert ov.mapping_status == "MAPPED"
    assert ov.current_weight == 4.5
    assert res.comparison.mapped_holdings == 1
    assert res.synchronization.mapped_count == 1
