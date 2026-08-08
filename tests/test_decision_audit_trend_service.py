"""Tests for DecisionAuditTrendService (Sprint 16.0.6)."""



import pytest



from services.decision_audit_service import DecisionAuditEntry, DecisionAuditTrail

from services.decision_audit_trend_service import (

    DecisionAuditTrend,

    DecisionAuditTrendPoint,

    DecisionAuditTrendService,

)





class _FakeEntry:

    """Mimics DecisionAuditEntry or dynamic object for testing."""



    def __init__(

        self,

        decision_id="DEC-001",

        timestamp="2026-01-01T00:00:00",

        category="HEALTH",

        classification_status="CLASSIFIED",

        priority="HIGH",

        source="decision_pipeline",

    ):

        self.decision_id = decision_id

        self.timestamp = timestamp

        self.category = category

        self.classification_status = classification_status

        self.priority = priority

        self.source = source





# ---------------------------------------------------------------------------

# Tests

# ---------------------------------------------------------------------------





def test_service_instantiation():

    """Verify DecisionAuditTrendService instantiates without exception."""

    service = DecisionAuditTrendService()

    assert service is not None





def test_empty_trend():

    """Verify empty input returns a safe empty DecisionAuditTrend."""

    service = DecisionAuditTrendService()

    trend = service.build_trend(DecisionAuditTrail(0, None, None, []))



    assert isinstance(trend, DecisionAuditTrend)

    assert trend.total_points == 0

    assert trend.earliest_timestamp is None

    assert trend.latest_timestamp is None

    assert trend.direction == "STABLE"

    assert trend.points == []





def test_single_timestamp():

    """Verify a single timestamp entry produces 1 trend point with STABLE direction."""

    service = DecisionAuditTrendService()

    entries = [_FakeEntry("DEC-001", "2026-01-01T10:00:00", "HEALTH", "CLASSIFIED", "HIGH")]

    trail = DecisionAuditTrail(1, "2026-01-01T10:00:00", "2026-01-01T10:00:00", entries)



    trend = service.build_trend(trail)

    assert trend.total_points == 1

    assert trend.direction == "STABLE"

    assert trend.earliest_timestamp == "2026-01-01T10:00:00"

    assert trend.latest_timestamp == "2026-01-01T10:00:00"

    assert trend.points[0].total_entries == 1





def test_multiple_timestamps():

    """Verify multiple timestamps produce distinct trend points in order."""

    service = DecisionAuditTrendService()

    entries = [

        _FakeEntry("DEC-001", "2026-01-01T10:00:00"),

        _FakeEntry("DEC-002", "2026-01-02T10:00:00"),

    ]

    trail = DecisionAuditTrail(2, "2026-01-01T10:00:00", "2026-01-02T10:00:00", entries)



    trend = service.build_trend(trail)

    assert trend.total_points == 2

    assert trend.points[0].timestamp == "2026-01-01T10:00:00"

    assert trend.points[1].timestamp == "2026-01-02T10:00:00"





def test_chronological_ordering():

    """Verify trend points are sorted chronologically OLDEST -> NEWEST even if inputs are unsorted."""

    service = DecisionAuditTrendService()

    entries = [

        _FakeEntry("DEC-002", "2026-01-03T00:00:00"),

        _FakeEntry("DEC-001", "2026-01-01T00:00:00"),

        _FakeEntry("DEC-003", "2026-01-02T00:00:00"),

    ]

    trail = DecisionAuditTrail(3, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.total_points == 3

    assert trend.points[0].timestamp == "2026-01-01T00:00:00"

    assert trend.points[1].timestamp == "2026-01-02T00:00:00"

    assert trend.points[2].timestamp == "2026-01-03T00:00:00"





def test_cumulative_total_entries():

    """Verify total_entries accumulates across timestamps."""

    service = DecisionAuditTrendService()

    entries = [

        _FakeEntry("DEC-001", "2026-01-01T00:00:00"),

        _FakeEntry("DEC-002", "2026-01-01T00:00:00"),

        _FakeEntry("DEC-003", "2026-01-02T00:00:00"),

    ]

    trail = DecisionAuditTrail(3, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.total_points == 2

    assert trend.points[0].total_entries == 2

    assert trend.points[1].total_entries == 3





def test_classified_and_unclassified_counts():

    """Verify classified_entries and unclassified_entries accumulate cumulatively."""

    service = DecisionAuditTrendService()

    entries = [

        _FakeEntry("DEC-001", "2026-01-01T00:00:00", classification_status="CLASSIFIED"),

        _FakeEntry("DEC-002", "2026-01-02T00:00:00", classification_status="UNCLASSIFIED"),

    ]

    trail = DecisionAuditTrail(2, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.points[0].classified_entries == 1

    assert trend.points[0].unclassified_entries == 0

    assert trend.points[1].classified_entries == 1

    assert trend.points[1].unclassified_entries == 1





def test_priority_counts():

    """Verify priority distribution metrics accumulate cumulatively across points."""

    service = DecisionAuditTrendService()

    entries = [

        _FakeEntry("DEC-001", "2026-01-01T00:00:00", priority="CRITICAL"),

        _FakeEntry("DEC-002", "2026-01-02T00:00:00", priority="HIGH"),

    ]

    trail = DecisionAuditTrail(2, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.points[0].critical_priority_entries == 1

    assert trend.points[0].high_priority_entries == 0

    assert trend.points[1].critical_priority_entries == 1

    assert trend.points[1].high_priority_entries == 1





def test_trend_direction_increasing():

    """Verify direction is INCREASING when latest total > first total."""

    service = DecisionAuditTrendService()

    entries = [

        _FakeEntry("DEC-001", "2026-01-01T00:00:00"),

        _FakeEntry("DEC-002", "2026-01-02T00:00:00"),

    ]

    trail = DecisionAuditTrail(2, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.direction == "INCREASING"





def test_trend_direction_stable():

    """Verify direction is STABLE when points have single point or equal totals."""

    service = DecisionAuditTrendService()

    entries = [_FakeEntry("DEC-001", "2026-01-01T00:00:00")]

    trail = DecisionAuditTrail(1, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.direction == "STABLE"





def test_none_input_safety():

    """Verify build_trend handles None audit_trail safely."""

    service = DecisionAuditTrendService()

    trend = service.build_trend(None)

    assert isinstance(trend, DecisionAuditTrend)

    assert trend.total_points == 0





def test_missing_entries_safety():

    """Verify build_trend handles objects missing the entries attribute."""

    service = DecisionAuditTrendService()



    class EmptyTrail:

        pass



    trend = service.build_trend(EmptyTrail())

    assert isinstance(trend, DecisionAuditTrend)

    assert trend.total_points == 0





def test_malformed_entry_safety():

    """Verify service safely ignores non-record malformed entry elements."""

    service = DecisionAuditTrendService()

    entries = [

        None,

        "not_an_entry",

        123,

        _FakeEntry("DEC-001", "2026-01-01T00:00:00"),

    ]

    trail = DecisionAuditTrail(4, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.total_points == 1

    assert trend.points[0].total_entries == 1





def test_missing_timestamp_safety():

    """Verify entries with missing or empty timestamps are safely skipped."""

    service = DecisionAuditTrendService()

    entries = [

        _FakeEntry("DEC-001", timestamp=""),

        _FakeEntry("DEC-002", timestamp="2026-01-01T00:00:00"),

    ]

    trail = DecisionAuditTrail(2, None, None, entries)

    trend = service.build_trend(trail)



    assert trend.total_points == 1

    assert trend.points[0].timestamp == "2026-01-01T00:00:00"





def test_defensive_exception_handling():

    """Verify service methods never propagate exceptions."""



    class FaultyAuditService:

        def get_audit_trail(self):

            raise RuntimeError("DB error")



    service = DecisionAuditTrendService(audit_service=FaultyAuditService())

    trend = service.get_trend()

    assert isinstance(trend, DecisionAuditTrend)

    assert trend.total_points == 0
