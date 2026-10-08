"""Feature-lab tests: a planted real signal must be adopted; pure noise must NOT be (no false 'improvements')."""
import numpy as np
import pandas as pd

from wsb.analytics import lab as L


def world(seed=7, n=4200):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2000-01-03", periods=n)
    r = rng.normal(0.0003, 0.008, n)
    sig = rng.normal(0, 1, n)                      # leading indicator (noisy) – rises in the 50 days before each crash
    for k in range(300, n - 200, 420):
        sig[k - 50:k] += 2.0
        r[k:k + 30] = -0.006
        r[k + 30:k + 90] = 0.0035
    close = pd.Series(100 * np.exp(np.cumsum(r)), index=idx)
    ssi = pd.Series(rng.uniform(20, 80, n), index=idx)          # deliberately uninformative baseline
    noise = {f"noise{i}": pd.Series(np.cumsum(rng.normal(0, 1, n)) * 0.0 + pd.Series(rng.normal(0, 1, n)).ewm(span=20).mean().values, index=idx)
             for i in range(5)}
    return idx, close, ssi, pd.Series(sig, index=idx), noise


def main():
    # logistic regression recovers a known relationship
    rng = np.random.default_rng(1)
    X = rng.normal(size=(5000, 2))
    y = (rng.uniform(size=5000) < L._sig(-1.0 + 1.5 * X[:, 0])).astype(float)
    w = L.fit_logit(X, y, l2=1.0)
    assert abs(w[1] - 1.5) < 0.25 and abs(w[2]) < 0.2 and abs(w[0] + 1.0) < 0.2, w

    idx, close, ssi, sig, noise = world()
    cands = {"signal": {"label": "真訊號", "series": sig.ewm(span=10).mean()}}
    cands.update({k: {"label": k, "series": v} for k, v in noise.items()})
    rep = L.run_horizon(pd.DataFrame(index=idx), ssi, close, 63, 0.10, cands)
    top = rep["features"][0]
    assert top["name"] == "signal" and top["adopt"] and top["d_auc"] > 0.1, top
    assert "signal" in rep["adopted"] and not any(a.startswith("noise") for a in rep["adopted"]), rep["adopted"]
    assert rep["ensemble"] and rep["ensemble"]["accepted"] and rep["ensemble"]["d_auc"] > 0.1, rep["ensemble"]
    assert rep["calibration"] and rep["now"]["p_enh"] is not None
    # calibration should be roughly honest: predicted ≈ actual in each populated bin
    # raw logistic output is over-confident here → the isotonic calibrator must pull the current estimate toward reality
    assert 0 <= rep["now"]["p_enh_cal"] <= 100
    xs = np.array([0.1, 0.2, 0.3])
    cal = L.isotonic(np.array([0.1] * 100 + [0.2] * 100 + [0.3] * 100), np.array([0] * 90 + [1] * 10 + [0] * 70 + [1] * 30 + [0] * 40 + [1] * 60))
    assert np.allclose(L.apply_iso(cal, xs), [0.1, 0.3, 0.6], atol=1e-6), L.apply_iso(cal, xs)
    ps = np.random.default_rng(2).uniform(size=500); ys = (np.random.default_rng(3).uniform(size=500) < ps).astype(float)
    c2 = L.isotonic(ps, ys)
    assert np.all(np.diff(c2[1]) >= -1e-12)                              # monotone

    # all-noise candidates → nothing adopted, no accepted ensemble
    cands2 = {k: {"label": k, "series": v} for k, v in noise.items()}
    rep2 = L.run_horizon(pd.DataFrame(index=idx), ssi, close, 63, 0.10, cands2)
    assert not rep2["adopted"] and (rep2["ensemble"] is None or not rep2["ensemble"]["accepted"]), rep2["adopted"]
    assert rep2["now"] and rep2["now"]["p_enh"] is None
    print("  lab: signal d_auc %.2f adopted=%s | noise adopted=%s" % (top["d_auc"], rep["adopted"], rep2["adopted"]))
    print("LAB TESTS PASSED ✅")


if __name__ == "__main__":
    main()
