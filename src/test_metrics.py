"""Sanity tests for metrics.py (pytest)."""
import numpy as np
import pandas as pd

from metrics import qwk, bootstrap_ci, consensus_and_bds, roc_calibrate


def test_qwk_perfect_agreement():
    h = np.array([1, 2, 3, 4, 5] * 10)
    assert qwk(h, h) == 1.0


def test_qwk_symmetric():
    h = np.array([1, 2, 3, 4, 5] * 10)
    m = np.array([2, 2, 3, 4, 4] * 10)
    assert abs(qwk(h, m) - qwk(m, h)) < 1e-12


def test_bootstrap_ci_brackets_point():
    rng = np.random.default_rng(0)
    h = rng.integers(1, 10, 200)
    m = np.clip(h + rng.integers(-1, 2, 200), 1, 9)
    point, lo, hi = bootstrap_ci(h, m, n_boot=500)
    assert lo <= point <= hi


def test_bds_zero_when_agents_agree():
    df = pd.DataFrame({
        "essay_id": ["e1"] * 3, "cohort": ["sea"] * 3,
        "model": ["m"] * 3, "condition": ["k3"] * 3,
        "agent": ["a", "b", "c"], "score": [5.0, 5.0, 5.0]})
    out = consensus_and_bds(df)
    assert out.bds.iloc[0] == 0.0
    assert out.consensus.iloc[0] == 5.0


def test_bds_weighted_consensus():
    df = pd.DataFrame({
        "essay_id": ["e1"] * 2, "cohort": ["sea"] * 2,
        "model": ["m"] * 2, "condition": ["k3"] * 2,
        "agent": ["a", "b"], "score": [4.0, 8.0]})
    out = consensus_and_bds(df, weights={"a": 3.0, "b": 1.0})
    assert out.consensus.iloc[0] == 5.0  # (3*4 + 1*8)/4


def test_roc_calibrate_separable():
    bds = np.array([0.1, 0.2, 0.15, 0.9, 1.1, 1.0])
    contested = np.array([0, 0, 0, 1, 1, 1])
    tau, area = roc_calibrate(bds, contested)
    assert area == 1.0
    assert 0.2 < tau <= 0.9
