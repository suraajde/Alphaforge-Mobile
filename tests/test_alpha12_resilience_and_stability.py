"""tests/test_alpha12_resilience_and_stability.py - Sprint 1 Contract & Stability Suite."""
import os
import json
import pytest

from services.contracts import IAlpha12MappingService, IAlpha12StabilityService
from services.alpha12_mapping_service import (
    Alpha12MappingService,
    Alpha12HoldingMapping,
    Alpha12PortfolioMapping,
    Alpha12MappingResult
)
from services.alpha12_stability_service import (
    Alpha12StabilityService,
    Alpha12StabilityMetrics,
    Alpha12StabilityResult
)


def test_protocol_contracts_satisfied():
    """Verify concrete services satisfy runtime-checkable Protocol interfaces."""
    map_svc = Alpha12MappingService()
    stab_svc = Alpha12StabilityService(mapping_service=map_svc)

    assert isinstance(map_svc, IAlpha12MappingService)
    assert isinstance(stab_svc, IAlpha12StabilityService)


def test_dataclass_tolerance_and_aliases():
    """Verify models absorb extra/legacy kwargs and expose property aliases."""
    hm = Alpha12HoldingMapping(symbol="INFY", legacy_extra="val", mapping_status="MAPPED")
    assert hm.symbol == "INFY"
    assert hm.status == "MAPPED"
    assert hm.is_mapped is True

    port = Alpha12PortfolioMapping(
        mapping_status="MAPPED",
        mapping_coverage_pct=91.7,
        mapped_holdings=11,
        unmapped_holdings=1
    )
    assert port.status == "MAPPED"
    assert port.coverage == 91.7
    assert port.mapped_count == 11
    assert port.unmapped_count == 1

    stab = Alpha12StabilityMetrics(stability_score=97.9, stability_rating="VERY_STABLE")
    assert stab.score == 97.9
    assert stab.rating == "VERY_STABLE"


def test_empty_inputs_safety(tmp_path):
    """Verify empty input payloads return NO_DATA or UNAVAILABLE status safely."""
    storage = tmp_path / "map_history.json"
    map_svc = Alpha12MappingService(storage_path=str(storage))

    empty_res = map_svc.analyze(alpha12_input=[])
    assert empty_res.analysis_status == "NO_DATA"
    assert empty_res.portfolio.mapping_status == "NO_DATA"

    stab_svc = Alpha12StabilityService(mapping_service=map_svc)
    stab_res = stab_svc.get_stability(mapping_result=empty_res)
    assert stab_res.analysis_status == "UNAVAILABLE"


def test_atomic_persistence_and_timestamp_dedup(tmp_path):
    """Verify atomic snapshot writes and duplicate timestamp protection."""
    storage = tmp_path / "stab_history.json"
    stab_svc = Alpha12StabilityService(storage_path=str(storage))

    res = stab_svc.get_stability()
    stab_svc.save_snapshot(res)
    stab_svc.save_snapshot(res)  # Duplicate call

    history = stab_svc.load_history()
    assert history.total_entries == 1
    assert not (tmp_path / "stab_history.json.tmp").exists()
