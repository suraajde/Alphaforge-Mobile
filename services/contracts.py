"""services/contracts.py - Abstract service contracts and runtime-checkable Protocol interfaces."""
from typing import Protocol, Optional, List, Dict, Any, Union, runtime_checkable


@runtime_checkable
class IAlpha12MappingService(Protocol):
    """Protocol interface for Alpha 12 portfolio and universe mapping."""

    def analyze(
        self,
        holdings: Optional[List[Dict[str, Any]]] = None,
        alpha12_input: Optional[List[Dict[str, Any]]] = None,
        state_input: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any: ...

    def get_mapping(self) -> Any: ...

    def load_history(self) -> List[Any]: ...

    def record_history(self, *args: Any, **kwargs: Any) -> None: ...


@runtime_checkable
class IAlpha12StabilityService(Protocol):
    """Protocol interface for Alpha 12 strategy stability and tenure governance."""

    def get_stability(
        self,
        mapping_result: Optional[Any] = None,
        alpha12_mapping: Optional[Any] = None,
        auto_save: bool = False,
        **kwargs: Any
    ) -> Any: ...

    def analyze_stability(self, *args: Any, **kwargs: Any) -> Any: ...

    def load_history(self) -> Any: ...

    def save_snapshot(self, result: Any) -> None: ...

    def record_history(self, *args: Any, **kwargs: Any) -> None: ...


@runtime_checkable
class IPortfolioHealthService(Protocol):
    """Protocol interface for portfolio health, structural balance, and trend scoring."""

    def evaluate(
        self,
        holdings: Optional[Any] = None,
        auto_save: bool = False,
        previous: Optional[Any] = None,
        **kwargs: Any
    ) -> Any: ...

    def build_snapshot(self, holdings: Optional[Any] = None, **kwargs: Any) -> Any: ...

import antigravity

class IAlpha12EmergencyService:
    pass