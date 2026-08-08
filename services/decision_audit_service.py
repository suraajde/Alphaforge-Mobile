"""Decision Audit Trail Service (Sprint 16.0.4)



Records factual outputs from the Decision Engine pipeline into a persistent

chronological audit trail.

"""

from __future__ import annotations



import hashlib

import json

import os

from dataclasses import asdict, dataclass, field

from datetime import datetime, timezone

from typing import Any, Optional





@dataclass

class DecisionAuditEntry:

    """A single audit record capturing a decision pipeline output."""



    audit_id: str

    timestamp: str

    decision_id: str

    category: str

    classification_status: str

    priority: str

    description: str

    source: str





@dataclass

class DecisionAuditTrail:

    """Chronological collection of decision audit entries."""



    total_entries: int

    latest_timestamp: Optional[str]

    earliest_timestamp: Optional[str]

    entries: list[DecisionAuditEntry]





def _empty_trail() -> DecisionAuditTrail:

    """Return a safe empty audit trail."""

    return DecisionAuditTrail(

        total_entries=0,

        latest_timestamp=None,

        earliest_timestamp=None,

        entries=[],

    )





class DecisionAuditService:

    """Service for recording and persisting decision audit entries.



    Records factual outputs already produced by the Decision Engine pipeline.

    Never creates new decisions, modifies classifications, or alters priorities.

    """



    _DEFAULT_STORAGE = os.path.join("data", "decisions", "decision_audit.json")



    def __init__(self, storage_path: Optional[str] = None) -> None:

        """Initialize DecisionAuditService.



        Args:

            storage_path: Path to the JSON audit file. Defaults to

                ``data/decisions/decision_audit.json``.

        """

        self._storage_path = (

            storage_path if storage_path is not None else self._DEFAULT_STORAGE

        )



    # ------------------------------------------------------------------

    # Deterministic ID generation

    # ------------------------------------------------------------------



    @staticmethod

    def _generate_audit_id(decision_id: str, timestamp: str) -> str:

        """Generate a deterministic audit ID from decision_id and timestamp."""

        raw = f"{decision_id}:{timestamp}"

        return hashlib.sha256(raw.encode()).hexdigest()[:16]



    # ------------------------------------------------------------------

    # Persistence

    # ------------------------------------------------------------------



    def load_audit(self) -> DecisionAuditTrail:

        """Load the persisted audit trail from disk.



        Safely handles missing files, empty files, corrupt JSON, and

        malformed records.  Always returns a valid ``DecisionAuditTrail``.

        """

        try:

            if not os.path.exists(self._storage_path):

                return _empty_trail()



            with open(self._storage_path, "r", encoding="utf-8") as fh:

                content = fh.read()



            if not content.strip():

                return _empty_trail()



            data = json.loads(content)

            if not isinstance(data, dict):

                return _empty_trail()



            raw_entries = data.get("entries", [])

            if not isinstance(raw_entries, list):

                return _empty_trail()



            entries: list[DecisionAuditEntry] = []

            for raw in raw_entries:

                if not isinstance(raw, dict):

                    continue

                try:

                    entry = DecisionAuditEntry(

                        audit_id=str(raw.get("audit_id", "")),

                        timestamp=str(raw.get("timestamp", "")),

                        decision_id=str(raw.get("decision_id", "")),

                        category=str(raw.get("category", "")),

                        classification_status=str(

                            raw.get("classification_status", "")

                        ),

                        priority=str(raw.get("priority", "")),

                        description=str(raw.get("description", "")),

                        source=str(raw.get("source", "")),

                    )

                    entries.append(entry)

                except Exception:

                    continue



            entries.sort(key=lambda e: e.timestamp)

            return self._build_trail(entries)

        except Exception:

            return _empty_trail()



    def save_audit(self, trail: DecisionAuditTrail) -> None:

        """Persist the audit trail to disk.



        Creates parent directories as needed.  Silently absorbs I/O errors

        so the caller is never disrupted.

        """

        try:

            dir_path = os.path.dirname(self._storage_path)

            if dir_path:

                os.makedirs(dir_path, exist_ok=True)



            data = {

                "total_entries": trail.total_entries,

                "latest_timestamp": trail.latest_timestamp,

                "earliest_timestamp": trail.earliest_timestamp,

                "entries": [asdict(e) for e in trail.entries],

            }



            temp_path = self._storage_path + ".tmp"

            with open(temp_path, "w", encoding="utf-8") as fh:

                json.dump(data, fh, indent=2)

            os.replace(temp_path, self._storage_path)

        except Exception:

            pass



    # ------------------------------------------------------------------

    # Recording

    # ------------------------------------------------------------------



    def record_decisions(

        self,

        decisions: Optional[list] = None,

        classifications: Optional[list] = None,

        priorities: Optional[list] = None,

    ) -> DecisionAuditTrail:

        """Record factual decision outputs into the audit trail.



        Consumes existing pipeline outputs (priorities / classifications)

        and appends new audit entries.  Duplicate entries (same decision_id

        and timestamp) are silently skipped.



        Returns the updated ``DecisionAuditTrail``.

        """

        try:

            trail = self.load_audit()

            existing_ids: set[str] = {e.audit_id for e in trail.entries}



            # Build a classification lookup for cross-referencing

            cls_map: dict[str, str] = {}

            if classifications:

                for cls_item in classifications:

                    d_id = str(getattr(cls_item, "decision_id", ""))

                    status = str(

                        getattr(cls_item, "classification_status", "unclassified")

                    )

                    if d_id:

                        cls_map[d_id] = status



            now = datetime.now(timezone.utc).isoformat()



            items = priorities if priorities else (decisions if decisions else [])

            if not items:

                return trail



            new_entries: list[DecisionAuditEntry] = []

            for item in items:

                try:

                    decision_id = str(getattr(item, "decision_id", ""))

                    category = str(getattr(item, "category", ""))

                    priority = str(getattr(item, "priority", ""))

                    description = str(getattr(item, "description", ""))

                    timestamp = now



                    classification_status = cls_map.get(

                        decision_id, "unclassified"

                    )



                    audit_id = self._generate_audit_id(decision_id, timestamp)



                    if audit_id in existing_ids:

                        continue



                    entry = DecisionAuditEntry(

                        audit_id=audit_id,

                        timestamp=timestamp,

                        decision_id=decision_id,

                        category=category,

                        classification_status=classification_status,

                        priority=priority,

                        description=description,

                        source="decision_pipeline",

                    )

                    new_entries.append(entry)

                    existing_ids.add(audit_id)

                except Exception:

                    continue



            all_entries = trail.entries + new_entries

            all_entries.sort(key=lambda e: e.timestamp)

            result = self._build_trail(all_entries)

            self.save_audit(result)

            return result

        except Exception:

            return self.load_audit()



    # ------------------------------------------------------------------

    # Queries

    # ------------------------------------------------------------------



    def get_audit_trail(self) -> DecisionAuditTrail:

        """Return the current persisted audit trail."""

        try:

            return self.load_audit()

        except Exception:

            return _empty_trail()



    def get_latest_entry(self) -> Optional[DecisionAuditEntry]:

        """Return the most recent audit entry, or ``None``."""

        try:

            trail = self.load_audit()

            if trail.entries:

                return trail.entries[-1]

            return None

        except Exception:

            return None



    def get_previous_entry(self) -> Optional[DecisionAuditEntry]:

        """Return the second-most-recent audit entry, or ``None``."""

        try:

            trail = self.load_audit()

            if len(trail.entries) >= 2:

                return trail.entries[-2]

            return None

        except Exception:

            return None



    # ------------------------------------------------------------------

    # Helpers

    # ------------------------------------------------------------------



    @staticmethod

    def _build_trail(

        entries: list[DecisionAuditEntry],

    ) -> DecisionAuditTrail:

        """Construct a ``DecisionAuditTrail`` from a list of entries."""

        if not entries:

            return _empty_trail()

        return DecisionAuditTrail(

            total_entries=len(entries),

            latest_timestamp=entries[-1].timestamp,

            earliest_timestamp=entries[0].timestamp,

            entries=entries,

        )
