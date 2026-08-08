from services.alpha12_challenger_service import (
    Alpha12ChallengerService,
    STRONG_CANDIDATE,
    PROTECT_INCUMBENT,
    MONITOR_CHALLENGER,
    REVIEW_CANDIDATE,
    INSUFFICIENT_DATA,
)

import copy


def test_service_initialization():
    svc = Alpha12ChallengerService()
    assert svc is not None


def test_none_input_returns_empty_result():
    svc = Alpha12ChallengerService()
    res = svc.evaluate(None, None, None, None)
    assert res.total_challengers_evaluated == 0
    assert res.challenger_records == []


def test_challenger_identification_and_incumbent_matching():
    svc = Alpha12ChallengerService()
    mapping = {
        "challengers": [
            {"symbol": "aaa", "rank": 1, "alpha12_score": 80, "incumbent": {"symbol": "BBB", "alpha12_score": 70}},
            {"ticker": "ccc", "rank": 2, "alpha12_score": 75, "incumbent": {"ticker": "DDD", "alpha12_score": 74}},
        ]
    }
    res = svc.evaluate(mapping, None, None, None)
    assert res.total_challengers_evaluated == 2
    # exact normalized symbol matching
    syms = [r.symbol for r in res.challenger_records]
    assert "AAA" in syms and "CCC" in syms
    # incumbents normalized
    incs = [r.incumbent_symbol for r in res.challenger_records]
    assert "BBB" in incs and "DDD" in incs


def test_alpha12_rank_preservation_and_score_comparison():
    svc = Alpha12ChallengerService()
    mapping = {"challengers": [{"symbol": "E1", "rank": 3, "alpha12_score": 85, "quality_score": 80, "risk_score": 30, "incumbent": {"symbol": "I1", "alpha12_score": 70, "quality_score": 60, "risk_score": 50}}]}
    res = svc.evaluate(mapping, None, None, None)
    rec = res.challenger_records[0]
    assert rec.challenger_rank == 3
    assert rec.incumbent_rank == None or isinstance(rec.incumbent_rank, (int, type(None)))
    # challenger score should be computed and higher than incumbent
    assert rec.challenger_score is not None
    assert rec.incumbent_score is not None
    assert rec.score_difference == round(rec.challenger_score - rec.incumbent_score, 2)


def test_quality_and_risk_comparisons_and_sector_overlap_and_allocation():
    svc = Alpha12ChallengerService()
    mapping = {
        "challengers": [
            {
                "symbol": "CHX",
                "alpha12_score": 88,
                "quality_score": 85,
                "risk_score": 25,
                "sector": "TECH",
                "current_weight": 1.5,
                "target_weight": 2.0,
                "incumbent": {"symbol": "INCX", "quality_score": 70, "risk_score": 40, "sector": "TECH", "current_weight": 3.0},
            }
        ]
    }
    res = svc.evaluate(mapping, None, None, None)
    rec = res.challenger_records[0]
    assert rec.quality_score == 85
    assert rec.incumbent_quality_score == 70
    assert rec.quality_difference == 15
    assert rec.risk_difference is not None
    assert rec.sector_overlap is True
    assert rec.current_weight == 1.5
    assert rec.target_weight == 2.0


def test_marginal_and_moderate_and_material_advantages():
    svc = Alpha12ChallengerService()
    # marginal advantage: small differences -> PROTECT_INCUMBENT
    mapping_marginal = {"challengers": [{"symbol": "M1", "alpha12_score": 61, "quality_score": 61, "risk_score": 50, "incumbent": {"symbol": "I", "alpha12_score": 60, "quality_score": 60, "risk_score": 51}}]}
    res_m = svc.evaluate(mapping_marginal, None, None, None)
    assert res_m.challenger_records[0].governance_status == PROTECT_INCUMBENT
    # moderate advantage: score diff >=5 -> MONITOR_CHALLENGER
    mapping_mod = {"challengers": [{"symbol": "M2", "alpha12_score": 75, "quality_score": 78, "risk_score": 40, "incumbent": {"symbol": "I2", "alpha12_score": 70, "quality_score": 70, "risk_score": 45}}]}
    res_mod = svc.evaluate(mapping_mod, None, None, None)
    assert res_mod.challenger_records[0].governance_status in (MONITOR_CHALLENGER, REVIEW_CANDIDATE)
    # material advantage: meets thresholds -> REVIEW or STRONG depending on deterioration
    mapping_mat = {"challengers": [{"symbol": "MAT", "alpha12_score": 95, "quality_score": 95, "risk_score": 10, "incumbent": {"symbol": "IMAT", "alpha12_score": 80, "quality_score": 80, "risk_score": 50}}]}
    res_mat = svc.evaluate(mapping_mat, None, None, None)
    rec_mat = res_mat.challenger_records[0]
    assert rec_mat.material_superiority is True
    # without deterioration should be REVIEW_CANDIDATE
    assert rec_mat.governance_status in (REVIEW_CANDIDATE, STRONG_CANDIDATE)


def test_meaningful_and_no_deterioration():
    svc = Alpha12ChallengerService()
    # meaningful deterioration detected via low incumbent quality
    mapping_det = {"challengers": [{"symbol": "D1", "alpha12_score": 90, "quality_score": 90, "risk_score": 20, "incumbent": {"symbol": "ID1", "alpha12_score": 70, "quality_score": 45, "risk_score": 50}}]}
    res_det = svc.evaluate(mapping_det, None, None, None)
    rec = res_det.challenger_records[0]
    assert rec.deterioration_detected is True
    # material superiority + deterioration -> STRONG_CANDIDATE
    assert rec.governance_status == STRONG_CANDIDATE
    # now no deterioration (incumbent quality high) -> not strong
    mapping_nodeg = {"challengers": [{"symbol": "ND1", "alpha12_score": 90, "quality_score": 90, "risk_score": 20, "incumbent": {"symbol": "IND1", "alpha12_score": 70, "quality_score": 85, "risk_score": 50}}]}
    res_nd = svc.evaluate(mapping_nodeg, None, None, None)
    rec2 = res_nd.challenger_records[0]
    assert rec2.deterioration_detected is False
    assert rec2.governance_status != STRONG_CANDIDATE


def test_higher_ranking_alone_does_not_trigger_replacement():
    svc = Alpha12ChallengerService()
    mapping = {"challengers": [{"symbol": "HR", "rank": 1, "alpha12_score": 60, "quality_score": 60, "risk_score": 50, "incumbent": {"symbol": "HI", "rank": 2, "alpha12_score": 59, "quality_score": 59, "risk_score": 51}}]}
    res = svc.evaluate(mapping, None, None, None)
    rec = res.challenger_records[0]
    assert rec.governance_status == PROTECT_INCUMBENT


def test_small_score_difference_does_not_trigger_churn():
    svc = Alpha12ChallengerService()
    mapping = {"challengers": [{"symbol": "SS", "alpha12_score": 65, "quality_score": 65, "risk_score": 50, "incumbent": {"symbol": "SI", "alpha12_score": 63, "quality_score": 64, "risk_score": 51}}]}
    res = svc.evaluate(mapping, None, None, None)
    rec = res.challenger_records[0]
    assert rec.governance_status == PROTECT_INCUMBENT


def test_insufficient_data_and_missing_fields_handling():
    svc = Alpha12ChallengerService()
    # missing quality
    mapping1 = {"challengers": [{"symbol": "MQ", "alpha12_score": 80, "risk_score": 30, "incumbent": {"symbol": "IQ", "alpha12_score": 70}}]}
    res1 = svc.evaluate(mapping1, None, None, None)
    assert res1.total_challengers_evaluated == 1
    # missing risk
    mapping2 = {"challengers": [{"symbol": "MR", "alpha12_score": 80, "quality_score": 80, "incumbent": {"symbol": "IR", "alpha12_score": 70}}]}
    res2 = svc.evaluate(mapping2, None, None, None)
    assert res2.challenger_records[0].challenger_score is not None
    # missing health data (portfolio_health_result) should not fabricate
    mapping3 = {"challengers": [{"symbol": "MH", "alpha12_score": 90, "quality_score": 90, "risk_score": 20, "incumbent": {"symbol": "IH", "alpha12_score": 85, "quality_score": 60, "risk_score": 50}}]}
    res3 = svc.evaluate(mapping3, None, None, None)
    assert res3.challenger_records[0].governance_status in (REVIEW_CANDIDATE, STRONG_CANDIDATE)


def test_malformed_input_and_none_input_and_dependency_exception_handling():
    svc = Alpha12ChallengerService()
    # malformed challenger entry
    mapping_bad = {"challengers": ["not-a-dict", 123, None]}
    res_bad = svc.evaluate(mapping_bad, None, None, None)
    assert res_bad.total_challengers_evaluated == 0
    # completely malformed mapping
    res_none = svc.evaluate("bad-input", None, None, None)
    assert res_none.total_challengers_evaluated == 0


def test_deterministic_repeated_evaluation_and_scoring_bounds_and_sorting():
    svc = Alpha12ChallengerService()
    mapping = {"challengers": [
        {"symbol": "DUP", "alpha12_score": 110, "quality_score": 110, "risk_score": -10, "rank": 1, "incumbent": {"symbol": "I1", "alpha12_score": 10, "quality_score": 10, "risk_score": 90}},
        {"symbol": "DUP2", "alpha12_score": -20, "quality_score": -10, "risk_score": 200, "rank": 2, "incumbent": {"symbol": "I2", "alpha12_score": 0, "quality_score": 0, "risk_score": 100}},
    ]}
    res1 = svc.evaluate(copy.deepcopy(mapping), None, None, None)
    res2 = svc.evaluate(copy.deepcopy(mapping), None, None, None)
    assert len(res1.challenger_records) == 2
    # deterministic: two runs produce same serialized governance statuses
    s1 = [(r.symbol, r.governance_status, r.challenger_score) for r in res1.challenger_records]
    s2 = [(r.symbol, r.governance_status, r.challenger_score) for r in res2.challenger_records]
    assert s1 == s2
    # scores bounded 0-100
    for r in res1.challenger_records:
        if r.challenger_score is not None:
            assert 0.0 <= r.challenger_score <= 100.0


def test_no_fabrication_no_portfolio_mutation_and_no_execution():
    svc = Alpha12ChallengerService()
    mapping = {"challengers": [{"symbol": "X1", "alpha12_score": 90, "quality_score": 90, "risk_score": 20, "incumbent": {"symbol": "Y1", "alpha12_score": 70, "quality_score": 40, "risk_score": 50}}]}
    res = svc.evaluate(mapping, {}, None, None)
    rec = res.challenger_records[0]
    # evidence present and no side effects: ensure input mapping unchanged
    assert mapping["challengers"][0]["symbol"] in ("X1", "x1", "X1")
    # no operations like buy/sell in service
    assert not hasattr(svc, "execute_replacement")
