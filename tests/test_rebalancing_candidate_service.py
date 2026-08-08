"""Tests for RebalancingCandidateService (Sprint 13.7.3)."""



import pytest



from services.rebalancing_candidate_service import (

    RebalancingCandidate,

    RebalancingCandidateResult,

    RebalancingCandidateService,

)

from services.rebalancing_service import (

    RebalancingPortfolio,

    RebalancingPosition,

    RebalancingState,

)





class _FakeRebalancingService:

    """Mimics RebalancingService for testing."""



    def __init__(self, state=None):

        self._state = state



    def get_state(self):

        if self._state is not None:

            return self._state

        return RebalancingState("EMPTY", RebalancingPortfolio(0.0, []), 0, 0.0)





# ---------------------------------------------------------------------------

# Tests

# ---------------------------------------------------------------------------





def test_service_instantiation():

    """Verify RebalancingCandidateService instantiates without exception."""

    service = RebalancingCandidateService()

    assert service is not None





def test_empty_candidate_result():

    """Verify empty input returns safe zeroed RebalancingCandidateResult."""

    service = RebalancingCandidateService()

    result = service.identify_candidates()



    assert isinstance(result, RebalancingCandidateResult)

    assert result.total_candidates == 0

    assert result.overweight_candidates == 0

    assert result.underweight_candidates == 0

    assert result.on_target_candidates == 0

    assert result.total_impact_value == 0.0

    assert result.candidates == []





def test_candidate_identification():

    """Verify candidate is identified for position with valid target weight."""

    pos = RebalancingPosition("AAPL", "Apple Inc.", "EQUITY", 6000.0, 60.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_candidates == 1

    assert len(result.candidates) == 1

    cand = result.candidates[0]

    assert cand.symbol == "AAPL"

    assert cand.target_weight == 50.0

    assert cand.rank == 1





def test_overweight_candidate():

    """Verify current_weight > target_weight candidate is classified as OVERWEIGHT."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 7000.0, 70.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.overweight_candidates == 1

    assert result.candidates[0].direction == "OVERWEIGHT"





def test_underweight_candidate():

    """Verify current_weight < target_weight candidate is classified as UNDERWEIGHT."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 3000.0, 30.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.underweight_candidates == 1

    assert result.candidates[0].direction == "UNDERWEIGHT"





def test_on_target_candidate():

    """Verify position matching target weight is classified as ON_TARGET candidate."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 5000.0, 50.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.on_target_candidates == 1

    assert result.candidates[0].direction == "ON_TARGET"





def test_positions_without_target_excluded():

    """Verify positions with target_weight=None are excluded from candidates list."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=50.0)

    pos2 = RebalancingPosition("NVDA", "Nvidia", "EQUITY", 4000.0, 40.0, target_weight=None)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_candidates == 1

    assert result.candidates[0].symbol == "AAPL"





def test_impact_value_calculation():

    """Verify impact_value = abs(drift) / 100.0 * total_portfolio_value."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 7000.0, 70.0, target_weight=50.0)  # drift = +20%

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.candidates[0].impact_value == 2000.0  # 20% of $10,000





def test_scenario_weight():

    """Verify scenario_weight matches target_weight."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 7000.0, 70.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.candidates[0].scenario_weight == 50.0





def test_scenario_delta():

    """Verify scenario_delta = target_weight - current_weight."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 7000.0, 70.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.candidates[0].scenario_delta == -20.0





def test_candidate_score():

    """Verify candidate_score equals absolute_drift."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 3000.0, 30.0, target_weight=50.0)  # |drift| = 20

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos]), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.candidates[0].candidate_score == 20.0





def test_candidate_ranking():

    """Verify candidates are ranked by score descending."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=50.0)  # score = 10

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 1000.0, 10.0, target_weight=50.0)  # score = 40

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.candidates[0].symbol == "MSFT"

    assert result.candidates[0].rank == 1

    assert result.candidates[1].symbol == "AAPL"

    assert result.candidates[1].rank == 2





def test_deterministic_ranking():

    """Verify equal scores break ties deterministically by symbol ascending."""

    pos1 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 7000.0, 70.0, target_weight=50.0)  # score = 20

    pos2 = RebalancingPosition("AAPL", "Apple", "EQUITY", 7000.0, 70.0, target_weight=50.0)  # score = 20

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.candidates[0].symbol == "AAPL"

    assert result.candidates[0].rank == 1

    assert result.candidates[1].symbol == "MSFT"

    assert result.candidates[1].rank == 2





def test_multiple_candidates():

    """Verify multiple candidates are evaluated and ranked correctly."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 5000.0, 50.0, target_weight=50.0)  # score = 0

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 3000.0, 30.0, target_weight=10.0)  # score = 20

    pos3 = RebalancingPosition("BND", "Bond", "FIXED_INCOME", 2000.0, 20.0, target_weight=40.0)  # score = 20

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2, pos3]), 3, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_candidates == 3

    # BND and MSFT both have score=20, BND comes first alphabetically

    symbols = [c.symbol for c in result.candidates]

    assert symbols == ["BND", "MSFT", "AAPL"]





def test_candidate_summary_counts():

    """Verify overweight, underweight, and on_target candidate counts."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=50.0)  # OW

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 2000.0, 20.0, target_weight=30.0)  # UW

    pos3 = RebalancingPosition("BND", "Bond", "FIXED_INCOME", 2000.0, 20.0, target_weight=20.0)  # ON

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2, pos3]), 3, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_candidates == 3

    assert result.overweight_candidates == 1

    assert result.underweight_candidates == 1

    assert result.on_target_candidates == 1





def test_total_impact_value():

    """Verify total_impact_value equals sum of candidate impact values."""

    pos1 = RebalancingPosition("AAPL", "Apple", "EQUITY", 6000.0, 60.0, target_weight=50.0)  # impact = 1000

    pos2 = RebalancingPosition("MSFT", "Microsoft", "EQUITY", 4000.0, 40.0, target_weight=50.0)  # impact = 1000

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, [pos1, pos2]), 2, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_impact_value == 2000.0





def test_missing_fields_safety():

    """Verify position with missing attributes is handled safely."""



    class PartialPosition:

        def __init__(self):

            self.symbol = "NVDA"

            # Missing target_weight attribute



    state = RebalancingState("READY", RebalancingPortfolio(1000.0, [PartialPosition()]), 1, 1000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_candidates == 0





def test_malformed_position_safety():

    """Verify non-record malformed items in position list are safely skipped."""

    positions = [None, "invalid_string", 456, RebalancingPosition("AAPL", "Apple", "EQUITY", 5000.0, 50.0, target_weight=50.0)]

    state = RebalancingState("READY", RebalancingPortfolio(10000.0, positions), 1, 10000.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_candidates == 1





def test_zero_portfolio_value_safety():

    """Verify zero portfolio value calculates 0.0 impact_value safely."""

    pos = RebalancingPosition("AAPL", "Apple", "EQUITY", 0.0, 0.0, target_weight=50.0)

    state = RebalancingState("READY", RebalancingPortfolio(0.0, [pos]), 1, 0.0)



    service = RebalancingCandidateService()

    result = service.identify_candidates(state)



    assert result.total_candidates == 1

    assert result.candidates[0].impact_value == 0.0





def test_none_input_safety():

    """Verify passing None to identify_candidates returns safe empty result."""

    service = RebalancingCandidateService()

    result = service.identify_candidates(None)



    assert isinstance(result, RebalancingCandidateResult)

    assert result.total_candidates == 0





def test_defensive_exception_handling():

    """Verify service methods never propagate exceptions."""



    class FaultyRebalancingService:

        def get_state(self):

            raise RuntimeError("Database connection failure")



    service = RebalancingCandidateService(rebalancing_service=FaultyRebalancingService())

    result = service.get_candidates()



    assert isinstance(result, RebalancingCandidateResult)

    assert result.total_candidates == 0
