"""Governance Pipeline Service (Sprint 13.0.0 Phase 1)

Converts portfolio observation dictionaries (sector concentration, position concentration, etc.)
into structured GovernanceAction instances.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from models.governance_action import GovernanceAction
from models.governance_severity import GovernanceSeverity


class GovernancePipelineService:
    """Service that transforms raw portfolio observations into actionable GovernanceAction objects."""

    def generate_actions(
        self,
        observations: Optional[List[Dict[str, Any]]] = None,
    ) -> List[GovernanceAction]:
        """Generate a list of GovernanceAction objects from input observation dicts.

        Args:
            observations: Optional list of observation dictionaries.

        Returns:
            List of GovernanceAction dataclass instances.
        """
        if not observations:
            return []

        actions: List[GovernanceAction] = []

        for obs in observations:
            if not isinstance(obs, dict):
                continue

            obs_type = str(obs.get("type", obs.get("observation_type", obs.get("metric", "")))).lower()
            severity_raw = str(obs.get("severity", "WARNING")).upper()

            # Parse GovernanceSeverity enum
            try:
                severity = GovernanceSeverity[severity_raw]
            except KeyError:
                severity = GovernanceSeverity.WARNING

            if obs_type == "sector_concentration":
                sector = obs.get("sector", "Unassigned")
                exposure = float(obs.get("exposure_pct", obs.get("weight_pct", 0.0)))
                limit = float(obs.get("limit_pct", 30.0))

                title = obs.get("title") or f"Sector Concentration: {sector}"
                description = obs.get("description") or (
                    f"Sector '{sector}' exposure is at {exposure:.1f}%, exceeding the maximum threshold of {limit:.1f}%."
                )
                recommendation = obs.get("recommendation") or (
                    f"Trim positions in {sector} to bring overall sector allocation below {limit:.1f}%."
                )

                actions.append(
                    GovernanceAction(
                        title=title,
                        description=description,
                        severity=severity,
                        recommendation=recommendation,
                    )
                )

            elif obs_type == "position_concentration":
                symbol = obs.get("symbol", "UNKNOWN")
                weight = float(obs.get("weight_pct", obs.get("exposure_pct", 0.0)))
                limit = float(obs.get("limit_pct", 25.0))

                title = obs.get("title") or f"Position Concentration: {symbol}"
                description = obs.get("description") or (
                    f"Position '{symbol}' weight is at {weight:.1f}%, exceeding single position limit of {limit:.1f}%."
                )
                recommendation = obs.get("recommendation") or (
                    f"Rebalance '{symbol}' to reduce position weight below {limit:.1f}%."
                )

                actions.append(
                    GovernanceAction(
                        title=title,
                        description=description,
                        severity=severity,
                        recommendation=recommendation,
                    )
                )

            else:
                title = obs.get("title")
                description = obs.get("description")
                recommendation = obs.get("recommendation")

                if title and description and recommendation:
                    actions.append(
                        GovernanceAction(
                            title=str(title),
                            description=str(description),
                            severity=severity,
                            recommendation=str(recommendation),
                        )
                    )

        return actions
