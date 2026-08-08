"""Tests for DecisionAuditAnalyticsService (Sprint 16.0.5)."""



import pytest



from services.decision_audit_analytics_service import (

    DecisionAuditAnalytics,

    DecisionAuditAnalyticsService,

    DecisionAuditAnalyticsSummary,

)

from services.decision_audit_service import DecisionAuditEntry, DecisionAuditTrail





class _FakeEntry:

    """Mimics a DecisionAuditEntry or dynamic object for testing."""



    def __init__(

        self,

        decision_id="DEC-001",

        category="HEALTH",

        classification_status="CLASSIFIED",

        priority="HIGH",

        source="decision_pipeline",

    ):

        self.decision_id = decision_id

        self.category = category

        self.classification_status = classification_status

        self.priority = priority

        self.source = source





# ---------------------------------------------------------------------------

# Tests

# ---------------------------------------------------------------------------





def test_service_instantiation():

    """Verify DecisionAuditAnalyticsService instantiates without exception."""

    service = DecisionAuditAnalyticsService()

    assert service is not None





def test_empty_analytics():

    """Verify empty input produces safe zeroed summary and empty dictionaries."""

    service = DecisionAuditAnalyticsService()

    analytics = service.analyze(DecisionAuditTrail(0, None, None, []))



    assert isinstance(analytics, DecisionAuditAnalytics)

    assert isinstance(analytics.summary, DecisionAuditAnalyticsSummary)

    assert analytics.summary.total_entries == 0

    assert analytics.summary.unique_decisions == 0

    assert analytics.summary.classified_entries == 0

    assert analytics.summary.unclassified_entries == 0

    assert analytics.category_counts == {}

    assert analytics.priority_counts == {}

    assert analytics.classification_counts == {}

    assert analytics.source_counts == {}





def test_summary_counts():

    """Verify build_summary computes summary fields correctly."""

    service = DecisionAuditAnalyticsService()

    entries = [

        _FakeEntry("DEC-001", "HEALTH", "CLASSIFIED", "HIGH"),

        _FakeEntry("DEC-002", "MONITORING", "UNCLASSIFIED", "MEDIUM"),

        _FakeEntry("DEC-003", "ALERT", "CLASSIFIED", "CRITICAL"),

    ]

    summary = service.build_summary(entries)



    assert summary.total_entries == 3

    assert summary.unique_decisions == 3

    assert summary.classified_entries == 2

    assert summary.unclassified_entries == 1

    assert summary.high_priority_entries == 1

    assert summary.medium_priority_entries == 1

    assert summary.critical_priority_entries == 1

    assert summary.low_priority_entries == 0

    assert summary.info_priority_entries == 0





def test_unique_decision_count():

    """Verify duplicate decision_id entries are deduplicated in unique_decisions metric."""

    service = DecisionAuditAnalyticsService()

    entries = [

        _FakeEntry("DEC-001", "HEALTH", "CLASSIFIED", "HIGH"),

        _FakeEntry("DEC-001", "HEALTH", "CLASSIFIED", "HIGH"),

        _FakeEntry("DEC-002", "HEALTH", "CLASSIFIED", "LOW"),

    ]

    summary = service.build_summary(entries)



    assert summary.total_entries == 3

    assert summary.unique_decisions == 2





def test_classification_counts():

    """Verify classification_counts aggregates classified vs unclassified correctly."""

    service = DecisionAuditAnalyticsService()

    trail = DecisionAuditTrail(

        total_entries=3,

        latest_timestamp="2026-01-01",

        earliest_timestamp="2026-01-01",

        entries=[

            _FakeEntry("DEC-001", classification_status="CLASSIFIED"),

            _FakeEntry("DEC-002", classification_status="UNCLASSIFIED"),

            _FakeEntry("DEC-003", classification_status="CLASSIFIED"),

        ],

    )

    analytics = service.analyze(trail)



    assert analytics.classification_counts.get("CLASSIFIED") == 2

    assert analytics.classification_counts.get("UNCLASSIFIED") == 1

    assert list(analytics.classification_counts.keys())[:2] == ["CLASSIFIED", "UNCLASSIFIED"]





def test_priority_counts():

    """Verify priority_counts aggregates priority distribution correctly."""

    service = DecisionAuditAnalyticsService()

    trail = DecisionAuditTrail(

        total_entries=4,

        latest_timestamp=None,

        earliest_timestamp=None,

        entries=[

            _FakeEntry("DEC-001", priority="CRITICAL"),

            _FakeEntry("DEC-002", priority="HIGH"),

            _FakeEntry("DEC-003", priority="MEDIUM"),

            _FakeEntry("DEC-004", priority="INFO"),

        ],

    )

    analytics = service.analyze(trail)



    assert analytics.priority_counts.get("CRITICAL") == 1

    assert analytics.priority_counts.get("HIGH") == 1

    assert analytics.priority_counts.get("MEDIUM") == 1

    assert analytics.priority_counts.get("INFO") == 1





def test_category_counts():

    """Verify category_counts aggregates actual categories correctly."""

    service = DecisionAuditAnalyticsService()

    trail = DecisionAuditTrail(

        total_entries=3,

        latest_timestamp=None,

        earliest_timestamp=None,

        entries=[

            _FakeEntry("DEC-001", category="HEALTH"),

            _FakeEntry("DEC-002", category="MONITORING"),

            _FakeEntry("DEC-003", category="HEALTH"),

        ],

    )

    analytics = service.analyze(trail)



    assert analytics.category_counts == {"HEALTH": 2, "MONITORING": 1}





def test_source_counts():

    """Verify source_counts aggregates sources correctly."""

    service = DecisionAuditAnalyticsService()

    trail = DecisionAuditTrail(

        total_entries=2,

        latest_timestamp=None,

        earliest_timestamp=None,

        entries=[

            _FakeEntry("DEC-001", source="decision_pipeline"),

            _FakeEntry("DEC-002", source="manual_audit"),

        ],

    )

    analytics = service.analyze(trail)



    assert analytics.source_counts == {"decision_pipeline": 1, "manual_audit": 1}





def test_multiple_entries():

    """Verify complex multiple entries produce accurate aggregations."""

    service = DecisionAuditAnalyticsService()

    entries = [

        _FakeEntry("DEC-001", "HEALTH", "CLASSIFIED", "HIGH", "srcA"),

        _FakeEntry("DEC-002", "ALERT", "CLASSIFIED", "CRITICAL", "srcB"),

        _FakeEntry("DEC-003", "HEALTH", "UNCLASSIFIED", "LOW", "srcA"),

    ]

    trail = DecisionAuditTrail(3, None, None, entries)

    analytics = service.analyze(trail)



    assert analytics.summary.total_entries == 3

    assert analytics.summary.unique_decisions == 3

    assert analytics.summary.classified_entries == 2

    assert analytics.summary.unclassified_entries == 1

    assert analytics.category_counts == {"ALERT": 1, "HEALTH": 2}

    assert analytics.source_counts == {"srcA": 2, "srcB": 1}





def test_priority_ordering():

    """Verify priority_counts dictionary adheres to CRITICAL -> HIGH -> MEDIUM -> LOW -> INFO ordering."""

    service = DecisionAuditAnalyticsService()

    entries = [

        _FakeEntry("DEC-001", priority="LOW"),

        _FakeEntry("DEC-002", priority="CRITICAL"),

        _FakeEntry("DEC-003", priority="MEDIUM"),

        _FakeEntry("DEC-004", priority="HIGH"),

        _FakeEntry("DEC-005", priority="INFO"),

    ]

    trail = DecisionAuditTrail(5, None, None, entries)

    analytics = service.analyze(trail)



    keys = list(analytics.priority_counts.keys())

    assert keys == ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]





def test_none_input_safety():

    """Verify analyze handles None audit_trail safely."""

    service = DecisionAuditAnalyticsService()

    analytics = service.analyze(None)

    assert isinstance(analytics, DecisionAuditAnalytics)

    assert analytics.summary.total_entries == 0





def test_missing_entries_safety():

    """Verify analyze handles audit_trail objects missing the entries attribute."""

    service = DecisionAuditAnalyticsService()



    class EmptyTrail:

        pass



    analytics = service.analyze(EmptyTrail())

    assert isinstance(analytics, DecisionAuditAnalytics)

    assert analytics.summary.total_entries == 0





def test_malformed_entry_safety():

    """Verify service safely skips malformed entry objects."""

    service = DecisionAuditAnalyticsService()

    entries = [

        None,

        "not_an_entry",

        123,

        _FakeEntry("DEC-001", "HEALTH", "CLASSIFIED", "HIGH"),

    ]

    summary = service.build_summary(entries)

    assert summary.total_entries == 1

    assert summary.unique_decisions == 1





def test_corrupt_input_safety():

    """Verify corrupt/unexpected types passed into analyze or build_summary do not raise exceptions."""

    service = DecisionAuditAnalyticsService()

    analytics1 = service.analyze("corrupt_string")

    assert isinstance(analytics1, DecisionAuditAnalytics)



    summary2 = service.build_summary({"invalid": "dictionary"})

    assert isinstance(summary2, DecisionAuditAnalyticsSummary)

    assert summary2.total_entries == 0





def test_defensive_exception_handling():

    """Verify service methods never propagate unexpected exceptions."""



    class FaultyAuditService:

        def get_audit_trail(self):

            raise RuntimeError("Database error")



    service = DecisionAuditAnalyticsService(audit_service=FaultyAuditService())

    analytics = service.get_analytics()

    assert isinstance(analytics, DecisionAuditAnalytics)

    assert analytics.summary.total_entries == 0
