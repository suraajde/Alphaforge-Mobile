"""Tests for DecisionAuditService (Sprint 16.0.4)."""

import json

import os

import shutil

import tempfile



import pytest



from services.decision_audit_service import (

    DecisionAuditEntry,

    DecisionAuditService,

    DecisionAuditTrail,

)





# ---------------------------------------------------------------------------

# Fixtures & helpers

# ---------------------------------------------------------------------------



@pytest.fixture

def scratch_dir():

    """Create a temporary directory for test storage, cleaned up after use."""

    d = tempfile.mkdtemp()

    yield d

    shutil.rmtree(d, ignore_errors=True)





def _make_service(scratch_dir):

    """Create a DecisionAuditService pointing at a temp file."""

    path = os.path.join(scratch_dir, "decision_audit.json")

    return DecisionAuditService(storage_path=path)





class _FakePriority:

    """Mimics DecisionPriority for testing."""



    def __init__(self, decision_id, category, priority, description):

        self.decision_id = decision_id

        self.category = category

        self.priority = priority

        self.description = description





class _FakeClassification:

    """Mimics DecisionClassification for testing."""



    def __init__(self, decision_id, classification_status):

        self.decision_id = decision_id

        self.classification_status = classification_status





# ---------------------------------------------------------------------------

# Tests

# ---------------------------------------------------------------------------





def test_service_instantiation():

    """Verify DecisionAuditService instantiates without exception."""

    service = DecisionAuditService()

    assert service is not None





def test_empty_audit_trail(scratch_dir):

    """Verify default trail is empty with None timestamps."""

    service = _make_service(scratch_dir)

    trail = service.get_audit_trail()

    assert isinstance(trail, DecisionAuditTrail)

    assert trail.total_entries == 0

    assert trail.latest_timestamp is None

    assert trail.earliest_timestamp is None

    assert trail.entries == []





def test_audit_entry_creation():

    """Verify DecisionAuditEntry fields are populated correctly."""

    entry = DecisionAuditEntry(

        audit_id="abc123",

        timestamp="2026-01-01T00:00:00",

        decision_id="DEC-001",

        category="HEALTH",

        classification_status="CLASSIFIED",

        priority="HIGH",

        description="Test decision",

        source="decision_pipeline",

    )

    assert entry.audit_id == "abc123"

    assert entry.timestamp == "2026-01-01T00:00:00"

    assert entry.decision_id == "DEC-001"

    assert entry.category == "HEALTH"

    assert entry.classification_status == "CLASSIFIED"

    assert entry.priority == "HIGH"

    assert entry.description == "Test decision"

    assert entry.source == "decision_pipeline"





def test_save_load_round_trip(scratch_dir):

    """Verify persistence round-trip: save then load recovers entries."""

    service = _make_service(scratch_dir)

    decisions = [_FakePriority("DEC-001", "HEALTH", "HIGH", "Test decision")]

    classifications = [_FakeClassification("DEC-001", "CLASSIFIED")]



    trail = service.record_decisions(

        decisions=decisions,

        classifications=classifications,

        priorities=decisions,

    )

    assert trail.total_entries == 1



    loaded = service.load_audit()

    assert loaded.total_entries == 1

    assert loaded.entries[0].decision_id == "DEC-001"

    assert loaded.entries[0].classification_status == "CLASSIFIED"

    assert loaded.entries[0].priority == "HIGH"

    assert loaded.entries[0].source == "decision_pipeline"





def test_chronological_ordering(scratch_dir):

    """Verify entries are sorted chronologically."""

    service = _make_service(scratch_dir)



    d1 = [_FakePriority("DEC-001", "HEALTH", "HIGH", "First")]

    service.record_decisions(decisions=d1, classifications=[], priorities=d1)



    d2 = [_FakePriority("DEC-002", "MONITORING", "MEDIUM", "Second")]

    trail = service.record_decisions(decisions=d2, classifications=[], priorities=d2)



    assert trail.total_entries == 2

    assert trail.entries[0].timestamp <= trail.entries[1].timestamp





def test_latest_entry(scratch_dir):

    """Verify get_latest_entry returns the most recent entry."""

    service = _make_service(scratch_dir)



    d1 = [_FakePriority("DEC-001", "HEALTH", "HIGH", "First")]

    service.record_decisions(decisions=d1, classifications=[], priorities=d1)



    d2 = [_FakePriority("DEC-002", "MONITORING", "MEDIUM", "Second")]

    service.record_decisions(decisions=d2, classifications=[], priorities=d2)



    latest = service.get_latest_entry()

    assert latest is not None

    assert latest.decision_id == "DEC-002"





def test_previous_entry(scratch_dir):

    """Verify get_previous_entry returns the second-most-recent entry."""

    service = _make_service(scratch_dir)



    d1 = [_FakePriority("DEC-001", "HEALTH", "HIGH", "First")]

    service.record_decisions(decisions=d1, classifications=[], priorities=d1)



    d2 = [_FakePriority("DEC-002", "MONITORING", "MEDIUM", "Second")]

    service.record_decisions(decisions=d2, classifications=[], priorities=d2)



    prev = service.get_previous_entry()

    assert prev is not None

    assert prev.decision_id == "DEC-001"





def test_duplicate_prevention(scratch_dir):

    """Verify same decision_id + timestamp does not create duplicate entries."""

    service = _make_service(scratch_dir)



    # Two items with the same decision_id in one batch get the same timestamp

    items = [

        _FakePriority("DEC-001", "HEALTH", "HIGH", "Test"),

        _FakePriority("DEC-001", "HEALTH", "HIGH", "Test"),

    ]



    trail = service.record_decisions(decisions=items, classifications=[], priorities=items)

    assert trail.total_entries == 1  # duplicate prevented





def test_multiple_decision_records(scratch_dir):

    """Verify multiple distinct decisions are all recorded."""

    service = _make_service(scratch_dir)

    decisions = [

        _FakePriority("DEC-001", "HEALTH", "HIGH", "Decision 1"),

        _FakePriority("DEC-002", "MONITORING", "MEDIUM", "Decision 2"),

        _FakePriority("DEC-003", "ALERT", "LOW", "Decision 3"),

    ]

    classifications = [

        _FakeClassification("DEC-001", "CLASSIFIED"),

        _FakeClassification("DEC-002", "CLASSIFIED"),

        _FakeClassification("DEC-003", "UNCLASSIFIED"),

    ]



    trail = service.record_decisions(

        decisions=decisions,

        classifications=classifications,

        priorities=decisions,

    )

    assert trail.total_entries == 3

    ids = {e.decision_id for e in trail.entries}

    assert ids == {"DEC-001", "DEC-002", "DEC-003"}





def test_missing_audit_file(scratch_dir):

    """Verify graceful fallback when audit file does not exist."""

    non_existent = os.path.join(scratch_dir, "nonexistent", "audit.json")

    service = DecisionAuditService(storage_path=non_existent)

    trail = service.load_audit()

    assert isinstance(trail, DecisionAuditTrail)

    assert trail.total_entries == 0





def test_empty_audit_file(scratch_dir):

    """Verify graceful fallback for a zero-byte file."""

    path = os.path.join(scratch_dir, "empty_audit.json")

    with open(path, "w") as fh:

        fh.write("")

    service = DecisionAuditService(storage_path=path)

    trail = service.load_audit()

    assert isinstance(trail, DecisionAuditTrail)

    assert trail.total_entries == 0





def test_corrupt_json(scratch_dir):

    """Verify graceful fallback for invalid JSON content."""

    path = os.path.join(scratch_dir, "corrupt.json")

    with open(path, "w") as fh:

        fh.write("{not valid json!!!")

    service = DecisionAuditService(storage_path=path)

    trail = service.load_audit()

    assert isinstance(trail, DecisionAuditTrail)

    assert trail.total_entries == 0





def test_malformed_records(scratch_dir):

    """Verify graceful handling of malformed records in entries list."""

    path = os.path.join(scratch_dir, "malformed.json")

    data = {

        "total_entries": 3,

        "entries": [

            "not a dict",

            {"audit_id": "abc", "timestamp": "", "decision_id": ""},

            123,

        ],

    }

    with open(path, "w") as fh:

        json.dump(data, fh)

    service = DecisionAuditService(storage_path=path)

    trail = service.load_audit()

    assert isinstance(trail, DecisionAuditTrail)

    # Only the dict entry should parse; non-dict entries are skipped

    assert trail.total_entries == 1





def test_missing_fields_in_input(scratch_dir):

    """Verify handling of input items with missing attributes."""

    service = _make_service(scratch_dir)



    class PartialItem:

        def __init__(self):

            self.decision_id = "DEC-001"

            # Missing: category, priority, description



    items = [PartialItem()]

    trail = service.record_decisions(

        decisions=items,

        classifications=[],

        priorities=items,

    )

    assert isinstance(trail, DecisionAuditTrail)

    assert trail.total_entries == 1

    assert trail.entries[0].decision_id == "DEC-001"

    assert trail.entries[0].category == ""  # safe default





def test_defensive_exception_handling(scratch_dir):

    """Verify service never propagates exceptions to caller."""

    service = _make_service(scratch_dir)



    # None inputs should not crash

    trail = service.record_decisions(decisions=None, classifications=None, priorities=None)

    assert isinstance(trail, DecisionAuditTrail)



    # get_audit_trail should never crash

    trail = service.get_audit_trail()

    assert isinstance(trail, DecisionAuditTrail)



    # get_latest_entry should return None safely

    entry = service.get_latest_entry()

    assert entry is None



    # get_previous_entry should return None safely

    entry = service.get_previous_entry()

    assert entry is None





def test_deterministic_audit_id():

    """Verify same inputs produce the same audit_id."""

    id1 = DecisionAuditService._generate_audit_id("DEC-001", "2026-01-01T00:00:00")

    id2 = DecisionAuditService._generate_audit_id("DEC-001", "2026-01-01T00:00:00")

    assert id1 == id2



    # Different decision_id produces different audit_id

    id3 = DecisionAuditService._generate_audit_id("DEC-002", "2026-01-01T00:00:00")

    assert id1 != id3
