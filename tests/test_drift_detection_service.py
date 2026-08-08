"""Tests for DriftDetectionService (Sprint 13.7.2)."""



import os

import pytest



from services.drift_detection_service import (

    DriftDetectionResult,

    DriftDetectionService,

    DriftHistory,

    DriftHistoryEntry,

    DriftMetric,

)

from services.rebalancing_service import (

    RebalancingPortfolio,

    RebalancingPosition,

    RebalancingState,

)





@pytest.fixture

def tmp_history_path(tmp_path):

    """Provide a temporary filepath for history persistence testing."""

    return str(tmp_path / "drift_history.json")





# ---------------------------------------------------------------------------

# Tests

# ---------------------------------------------------------------------------





def test_service_instantiation(tmp_history_path):

    """Verify DriftDetectionService instantiates without exception."""

    service = DriftDetectionService(history_path=tmp_history_path)

    assert service is not None





def test_empty_drift_result(tmp_history_path):

    """Verify empty input returns safe zeroed DriftDetectionResult."""

    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift()



    assert isinstance(result, DriftDetectionResult)

    assert result.total_positions == 0

    assert result.positions_with_target == 0

    assert result.positions_without_target == 0

    assert result.total_absolute_drift == 0.0

    assert result.average_absolute_drift == 0.0

    assert result.maximum_absolute_drift == 0.0

    assert result.metrics == []





def test_on_target_position(tmp_history_path):

    """Verify position matching target weight is classified as ON_TARGET."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 5000.0, 50.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.positions_with_target == 1

    assert len(result.metrics) == 1

    m = result.metrics[0]

    assert m.direction == "ON_TARGET"

    assert m.drift == 0.0

    assert m.absolute_drift == 0.0





def test_overweight_position(tmp_history_path):

    """Verify current_weight > target_weight is classified as OVERWEIGHT."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=40.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert len(result.metrics) == 1

    m = result.metrics[0]

    assert m.direction == "OVERWEIGHT"

    assert m.drift == 20.0

    assert m.absolute_drift == 20.0





def test_underweight_position(tmp_history_path):

    """Verify current_weight < target_weight is classified as UNDERWEIGHT."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 3000.0, 30.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert len(result.metrics) == 1

    m = result.metrics[0]

    assert m.direction == "UNDERWEIGHT"

    assert m.drift == -20.0

    assert m.absolute_drift == 20.0





def test_multiple_positions(tmp_history_path):

    """Verify multiple positions evaluate drift correctly."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=50.0)  # +10

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 4000.0, 40.0, target_weight=50.0)  # -10

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.total_positions == 2

    assert result.positions_with_target == 2

    assert len(result.metrics) == 2

    assert result.total_absolute_drift == 20.0





def test_positions_without_target(tmp_history_path):

    """Verify positions with target_weight=None are counted in positions_without_target."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=50.0)

    pos2 = RebalancingPosition("NVDA", "Nvidia", "EQUITY", 4000.0, 40.0, target_weight=None)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.total_positions == 2

    assert result.positions_with_target == 1

    assert result.positions_without_target == 1

    assert len(result.metrics) == 1

    assert result.metrics[0].name == "AAPL"





def test_drift_metrics(tmp_history_path):

    """Verify summary metrics total_absolute_drift and counts."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 7000.0, 70.0, target_weight=50.0)  # |20|

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 3000.0, 30.0, target_weight=50.0)  # |-20|

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.total_absolute_drift == 40.0





def test_average_absolute_drift(tmp_history_path):

    """Verify average_absolute_drift = total_absolute_drift / positions_with_target."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=50.0)  # |10|

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 4000.0, 40.0, target_weight=50.0)  # |-10|

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.average_absolute_drift == 10.0





def test_maximum_absolute_drift(tmp_history_path):

    """Verify maximum_absolute_drift finds max |drift| across target positions."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 7000.0, 70.0, target_weight=50.0)  # |20|

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 3000.0, 30.0, target_weight=50.0)  # |20|

    pos3 = RebalancingPosition("GOOGL", "Alphabet", "EQUITY", 0.0, 0.0, target_weight=5.0)  # |5|

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2, pos3]), 3, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.maximum_absolute_drift == 20.0





def test_zero_target_safety(tmp_history_path):

    """Verify zero target_weight is handled safely."""

    pos = RebalancingPosition("CASH", "Cash", "CASH", 1000.0, 10.0, target_weight=0.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.positions_with_target == 1

    assert result.metrics[0].drift == 10.0

    assert result.metrics[0].direction == "OVERWEIGHT"





def test_missing_fields_safety(tmp_history_path):

    """Verify position with missing attributes is handled safely without crashing."""



    class PartialPosition:

        def __init__(self):

            self.symbol = "NVDA"

            # Missing target_weight and current_weight



    state = RebalancingState("READY", RebalancingPortfolio(1000.0, [PartialPosition()]), 1, 1000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.total_positions == 1

    assert result.positions_without_target == 1





def test_none_input_safety(tmp_history_path):

    """Verify passing None to detect_drift returns safe empty result."""

    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(None)



    assert isinstance(result, DriftDetectionResult)

    assert result.total_positions == 0





def test_malformed_position_safety(tmp_history_path):

    """Verify non-record malformed items in position list are safely ignored."""

    positions = [None, "invalid_string", 456, RebalancingPosition("AAPL", "Apple", "EQUITY", 5000.0, 50.0, target_weight=50.0)]

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, positions), 1, 10000.0)



    service = DriftDetectionService(history_path=tmp_history_path)

    result = service.detect_drift(state)



    assert result.total_positions == 1

    assert result.positions_with_target == 1





def test_defensive_exception_handling(tmp_history_path):

    """Verify service methods never propagate exceptions."""



    class FaultyRebalancingService:

        def get_state(self):

            raise RuntimeError("Database connection failure")



    service = DriftDetectionService(rebalancing_service=FaultyRebalancingService(), history_path=tmp_history_path)

    result = service.get_drift()



    assert isinstance(result, DriftDetectionResult)

    assert result.total_positions == 0





def test_history_empty(tmp_history_path):

    """Verify empty history file returns empty DriftHistory."""

    service = DriftDetectionService(history_path=tmp_history_path)

    hist = service.load_history()



    assert isinstance(hist, DriftHistory)

    assert hist.total_entries == 0

    assert hist.earliest_timestamp is None

    assert hist.latest_timestamp is None





def test_history_save_load(tmp_history_path):

    """Verify saving and loading DriftHistory persists entries correctly."""

    entry = DriftHistoryEntry("2026-08-08T00:00:00Z", 20.0, 10.0, 20.0, 2)

    hist = DriftHistory(1, "2026-08-08T00:00:00Z", "2026-08-08T00:00:00Z", [entry])



    service = DriftDetectionService(history_path=tmp_history_path)

    service.save_history(hist)



    loaded = service.load_history()

    assert loaded.total_entries == 1

    assert loaded.earliest_timestamp == "2026-08-08T00:00:00Z"

    assert loaded.entries[0].total_absolute_drift == 20.0





def test_history_recording(tmp_history_path):

    """Verify record_history creates new history entry."""

    res = DriftDetectionResult(2, 2, 0, 20.0, 10.0, 20.0, [])

    service = DriftDetectionService(history_path=tmp_history_path)

    hist = service.record_history(res, timestamp="2026-08-08T10:00:00Z")



    assert hist.total_entries == 1

    assert hist.latest_timestamp == "2026-08-08T10:00:00Z"





def test_history_duplicate_prevention(tmp_history_path):

    """Verify duplicate timestamp entries are prevented."""

    res = DriftDetectionResult(2, 2, 0, 20.0, 10.0, 20.0, [])

    service = DriftDetectionService(history_path=tmp_history_path)

    service.record_history(res, timestamp="2026-08-08T10:00:00Z")

    hist = service.record_history(res, timestamp="2026-08-08T10:00:00Z")



    assert hist.total_entries == 1





def test_history_chronological_order(tmp_history_path):

    """Verify history entries are sorted chronologically."""

    res = DriftDetectionResult(1, 1, 0, 10.0, 10.0, 10.0, [])

    service = DriftDetectionService(history_path=tmp_history_path)

    service.record_history(res, timestamp="2026-08-08T12:00:00Z")

    service.record_history(res, timestamp="2026-08-08T08:00:00Z")



    loaded = service.load_history()

    assert loaded.total_entries == 2

    assert loaded.earliest_timestamp == "2026-08-08T08:00:00Z"

    assert loaded.latest_timestamp == "2026-08-08T12:00:00Z"

    assert loaded.entries[0].timestamp == "2026-08-08T08:00:00Z"





def test_corrupt_history_safety(tmp_history_path):

    """Verify corrupt JSON file does not crash load_history."""

    os.makedirs(os.path.dirname(tmp_history_path), exist_ok=True)

    with open(tmp_history_path, "w", encoding="utf-8") as f:

        f.write("{corrupt json content...")



    service = DriftDetectionService(history_path=tmp_history_path)

    loaded = service.load_history()



    assert isinstance(loaded, DriftHistory)

    assert loaded.total_entries == 0





def test_empty_history_file_safety(tmp_history_path):

    """Verify empty 0-byte history file returns empty DriftHistory."""

    os.makedirs(os.path.dirname(tmp_history_path), exist_ok=True)

    with open(tmp_history_path, "w", encoding="utf-8") as f:

        f.write("")



    service = DriftDetectionService(history_path=tmp_history_path)

    loaded = service.load_history()



    assert isinstance(loaded, DriftHistory)

    assert loaded.total_entries == 0
