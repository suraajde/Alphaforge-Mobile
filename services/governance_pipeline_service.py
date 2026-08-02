"""Governance Pipeline Service (Sprint 13.1.0 Governance Evaluation Bridge)

Converts portfolio observations and GovernanceEvaluation dataclass instances (from PortfolioGovernanceService)
into structured GovernanceAction instances with decision-to-severity mapping:
- HOLD -> INFO
- REVIEW -> WARNING
- REPLACE -> WATCH
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from models.governance_action import GovernanceAction
from models.governance_severity import GovernanceSeverity
from services.portfolio_governance_service import GovernanceEvaluation


class GovernancePipelineService:
    """Service that transforms raw portfolio observations and GovernanceEvaluation objects into GovernanceAction objects."""

    def generate_actions_from_evaluations(
        self,
        evaluations: Optional[List[GovernanceEvaluation]] = None,
    ) -> List[GovernanceAction]:
        """Convert a list of GovernanceEvaluation dataclass objects into GovernanceAction instances.

        Args:
            evaluations: Optional list of GovernanceEvaluation instances.

        Returns:
            List of GovernanceAction objects.
        """
        if not evaluations:
            return []

        actions: List[GovernanceAction] = []
        severity_map = {
            "HOLD": GovernanceSeverity.INFO,
            "REVIEW": GovernanceSeverity.WARNING,
            "REPLACE": GovernanceSeverity.WATCH,
        }

        for ev in evaluations:
            if not isinstance(ev, GovernanceEvaluation):
                continue

            dec_upper = str(ev.decision).upper()
            severity = severity_map.get(dec_upper, GovernanceSeverity.INFO)

            curr = ev.current_symbol or "UNKNOWN"
            cand = ev.candidate_symbol or "None"
            title = f"Governance {dec_upper}: {curr} -> {cand}"

            # Build description incorporating guardrail breach flags and score metrics
            desc_parts: List[str] = []
            if ev.replacement_justification:
                desc_parts.append(ev.replacement_justification)
            else:
                desc_parts.append(
                    f"Holding {curr} (score {ev.current_score:.1f}) vs candidate {cand} (score {ev.candidate_score:.1f})."
                )

            if ev.sector_guardrail_breached:
                desc_parts.append("[Sector Guardrail Breached]")
            if ev.concentration_guardrail_breached:
                desc_parts.append("[Concentration Guardrail Breached]")

            description = " ".join(desc_parts)

            # Build recommendation from reasons or replacement_justification
            if ev.reasons:
                recommendation = "; ".join(ev.reasons)
            elif ev.replacement_justification:
                recommendation = ev.replacement_justification
            else:
                recommendation = f"Maintain governance policy constraints for {curr}."

            actions.append(
                GovernanceAction(
                    title=title,
                    description=description,
                    severity=severity,
                    recommendation=recommendation,
                )
            )

        return actions

    def generate_actions(
        self,
        observations: Optional[List[Union[Dict[str, Any], GovernanceEvaluation]]] = None,
    ) -> List[GovernanceAction]:
        """Generate a list of GovernanceAction objects from input observation dicts or GovernanceEvaluation objects.

        Args:
            observations: Optional list of observation dicts or GovernanceEvaluation instances.

        Returns:
            List of GovernanceAction dataclass instances.
        """
        if not observations:
            return []

        # Separate GovernanceEvaluation objects from dictionary observations
        eval_list: List[GovernanceEvaluation] = [
            item for item in observations if isinstance(item, GovernanceEvaluation)
        ]
        dict_list: List[Dict[str, Any]] = [
            item for item in observations if isinstance(item, dict)
        ]

        actions: List[GovernanceAction] = []

        if eval_list:
            actions.extend(self.generate_actions_from_evaluations(eval_list))

        for obs in dict_list:
            obs_type = str(obs.get("type", obs.get("observation_type", obs.get("metric", "")))).lower()
            severity_raw = str(obs.get("severity", "WARNING")).upper()

            try:
                severity = GovernanceSeverity[severity_raw]
            except KeyError:
                severity = GovernanceSeverity.WARNING

            if obs_type == "sector_concentration":
                sector = obs.get("sector", "Unassigned")
                exposure = float(obs.get("exposure_pct", obs.get("weight_pct", obs.get("allocation_percent", 0.0))))
                limit = float(obs.get("limit_pct", obs.get("threshold", 30.0)))

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
