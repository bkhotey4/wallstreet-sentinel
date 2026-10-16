"""12 個月破產機率：logistic hazard model trained on SEC filings (tools/bankruptcy/), applied to the radar's balance sheets.

Label = an 8-K item 1.03 (bankruptcy or receivership) filed within 365 days of the snapshot.  Inputs are exactly the
fields wsb.data.distress_data.parse_balance produces, so training and live use share one code path (features()).
No prices: delisted companies have none in our sources, so a price-based model could not be trained without
survivorship bias.  Banks (deposits > 40 % of assets) are outside the training sample and get no probability.
The parameters in bankruptcy_model.json are fitted, not chosen; its "oos" block holds the out-of-sample validation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

MODEL_FILE = Path(__file__).with_name("bankruptcy_model.json")
FEATS = ["wc_ta", "re_ta", "ebit_ta", "ni_ta", "eq_tl", "tl_ta", "cash_ta", "debt_ta", "int_ta", "cov", "fcf_ta", "runway",
         "dgrowth", "log_ta", "lag", "neg_eq", "m_wc", "m_cov", "m_fcf", "annualized"]
COLS = ("assets", "liab", "cur_assets", "cur_liab", "re", "equity", "cash", "ltd", "ltd_nc", "ltd_cur", "debt_cur", "fin_lease",
        "deposits", "ebit_ttm", "rev_ttm", "interest_ttm", "ocf_ttm", "capex_ttm", "da_ttm", "ni_ttm", "ltd_yago")


def is_bank(b: Dict) -> bool:
    return bool(b.get("deposits") and b.get("assets") and b["deposits"] / b["assets"] > 0.4)


def row(b: Dict, lag_days: int) -> Dict:
    """One balance sheet (parse_balance output) → the panel row the model was trained on."""
    return {**{k: b.get(k) for k in COLS}, "lag": lag_days, "annualized": len(b.get("annualized") or [])}


def features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.astype({k: float for k in COLS if k in df}).copy()
    ta = df["assets"]
    tl = df["liab"].fillna(ta - df["equity"])
    debt = df["ltd"].fillna(df["ltd_nc"].fillna(0) + df["ltd_cur"].fillna(0)) + df["debt_cur"].fillna(0) + df["fin_lease"].fillna(0)
    fcf = df["ocf_ttm"] - df["capex_ttm"].fillna(0)
    it = df["interest_ttm"]
    f = pd.DataFrame(index=df.index)
    f["wc_ta"] = (df["cur_assets"] - df["cur_liab"]) / ta
    f["re_ta"] = df["re"] / ta
    f["ebit_ta"] = df["ebit_ttm"] / ta
    f["ni_ta"] = df["ni_ttm"] / ta
    f["eq_tl"] = df["equity"] / tl
    f["tl_ta"] = tl / ta
    f["cash_ta"] = df["cash"] / ta
    f["debt_ta"] = debt / ta
    f["int_ta"] = it / ta
    f["cov"] = np.where(it > 0, (df["ebit_ttm"] / it).clip(-5, 20), np.where(df["ebit_ttm"].notna(), 20.0, np.nan))
    f["fcf_ta"] = fcf / ta
    f["runway"] = np.where(fcf < 0, (df["cash"] / (-fcf / 12)).clip(0, 60), np.where(fcf.notna(), 60.0, np.nan))
    f["dgrowth"] = (df["ltd"] / df["ltd_yago"] - 1).clip(-1, 5)
    f["log_ta"] = np.log10(ta)
    f["lag"] = df["lag"] / 365
    f["neg_eq"] = (df["equity"] < 0).astype(float)
    f["m_wc"] = f["wc_ta"].isna().astype(float)
    f["m_cov"] = f["cov"].isna().astype(float)
    f["m_fcf"] = f["fcf_ta"].isna().astype(float)
    f["annualized"] = (df["annualized"] > 0).astype(float)
    return f.replace([np.inf, -np.inf], np.nan)[FEATS]


class Prep:
    """Winsorise at the training 1st / 99th percentile, standardise, fill missing with the training mean (0)."""
    def fit(self, X: pd.DataFrame) -> "Prep":
        self.lo, self.hi = X.quantile(0.01), X.quantile(0.99)
        Xc = X.clip(self.lo, self.hi, axis=1)
        self.mu, self.sd = Xc.mean(), Xc.std().replace(0, 1)
        return self

    def tf(self, X: pd.DataFrame) -> np.ndarray:
        return ((X.clip(self.lo, self.hi, axis=1) - self.mu) / self.sd).fillna(0).to_numpy()

    def dump(self) -> Dict[str, List[float]]:
        return {k: [float(x) for x in getattr(self, k).reindex(FEATS).fillna(0)] for k in ("lo", "hi", "mu", "sd")}

    @classmethod
    def load(cls, d: Dict[str, List[float]]) -> "Prep":
        p = cls()
        for k in ("lo", "hi", "mu", "sd"):
            setattr(p, k, pd.Series(d[k], index=FEATS))
        return p


_MODEL: Optional[Dict] = None


def model() -> Optional[Dict]:
    global _MODEL
    if _MODEL is None:
        try:
            _MODEL = json.loads(MODEL_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            _MODEL = {}
    return _MODEL or None


def prob(b: Dict, today: date) -> Optional[float]:
    """Calibrated probability of a bankruptcy filing within 12 months, or None (bank, no data, no model)."""
    m = model()
    if not m or not b or not b.get("assets") or b["assets"] <= 0 or is_bank(b) or not b.get("end"):
        return None
    lag = (today - date.fromisoformat(b["end"])).days
    X = features(pd.DataFrame([row(b, lag)]))
    z = Prep.load(m["prep"]).tf(X)
    w = np.array(m["w"])
    p = 1.0 / (1.0 + np.exp(-np.clip(w[0] + z @ w[1:], -30, 30)))
    return float(np.interp(p, m["cal"][0], m["cal"][1])[0])


def model_age_days(today: date) -> Optional[int]:
    m = model()
    return (today - date.fromisoformat(m["trained"])).days if m and m.get("trained") else None
