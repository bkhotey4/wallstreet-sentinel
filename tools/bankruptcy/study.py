"""Step 3/3. Bankruptcy study: walk-forward logistic hazard model vs Altman Z'' and the radar's points, out of sample.
Usage: python -m tools.bankruptcy.study <panel.pkl> wsb/analytics/bankruptcy_model.json <report.json>"""
import json
import sys
from datetime import date

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from wsb.analytics.lab import apply_iso, fit_logit, isotonic, predict  # noqa: E402
from wsb.analytics.shock import auc  # noqa: E402

from wsb.analytics.bankruptcy import FEATS, Prep, features  # noqa: E402  (one code path for training and live use)


def topk(score: pd.Series, y: pd.Series, d: pd.Series, q: float):
    """Pick the top q of each snapshot by score; recall (share of bankruptcies caught) and precision."""
    r = score.groupby(d).rank(pct=True, ascending=False)
    sel = r <= q
    return {"recall": float(y[sel].sum() / max(1, y.sum())), "precision": float(y[sel].mean()) if sel.any() else None,
            "n_flag": int(sel.sum())}


def main():
    panel, mout, rout = sys.argv[1:4]
    df = pd.read_pickle(panel)
    df = df[~((df["deposits"].fillna(0) / df["assets"]) > 0.4)].reset_index(drop=True)        # banks: separate model
    F = features(df)
    df["dd"] = pd.to_datetime(df["d"])
    df["yr"] = df["dd"].dt.year
    print("rows", len(df), "companies", df["cik"].nunique(), "positives", int(df["y"].sum()), "base rate %.3f%%" % (df["y"].mean() * 100))
    oos = []
    for Y in range(2013, 2026):
        te = df["yr"] == Y
        tr = df["dd"] <= pd.Timestamp(date(Y - 1, 1, 1))          # labels of these rows ended before year Y began
        if te.sum() == 0 or df.loc[tr, "y"].sum() < 30:
            continue
        pr = Prep().fit(F[tr])
        w = fit_logit(pr.tf(F[tr]), df.loc[tr, "y"].to_numpy().astype(float))
        p = predict(w, pr.tf(F[te]))
        oos.append(pd.DataFrame({"i": df.index[te], "p": p}))
    o = pd.concat(oos).set_index("i")
    t = df.loc[o.index].copy()
    t["p"] = o["p"]
    t["negz"] = -t["z2"].fillna(t["z2"].median())
    t.to_pickle(mout.replace(".json", "_oos.pkl"))
    rep = {"rows_oos": int(len(t)), "pos_oos": int(t["y"].sum()), "base_rate_pct": float(t["y"].mean() * 100), "groups": {}}
    late = (t["yr"] >= 2015).to_numpy()          # at least four years of training history
    for nm, m in (("all", np.ones(len(t), bool)), ("assets_1B_plus", (t["assets"] >= 1e9).to_numpy()),
                  ("2015plus", late), ("2015plus_1B", late & (t["assets"] >= 1e9).to_numpy())):
        s = t[m]
        g = {"n": int(len(s)), "pos": int(s["y"].sum())}
        for sc in ("p", "negz", "pts"):
            g[sc] = {"auc": auc(s[sc], s["y"]), "top5": topk(s[sc], s["y"], s["d"], 0.05), "top10": topk(s[sc], s["y"], s["d"], 0.10),
                     "top1": topk(s[sc], s["y"], s["d"], 0.01)}
        yrs = {}
        for Y, s2 in s.groupby("yr"):
            if s2["y"].sum() >= 5:
                yrs[int(Y)] = {"n_pos": int(s2["y"].sum()), "model": auc(s2["p"], s2["y"]), "negz": auc(s2["negz"], s2["y"]),
                               "pts": auc(s2["pts"], s2["y"])}
        g["years"] = yrs
        g["model_beats_z_years"] = f"{sum(v['model'] > v['negz'] for v in yrs.values())}/{len(yrs)}"
        rep["groups"][nm] = g
    # isotonic map from the walk-forward predictions of the years with >= 4 years of training history (what live use applies)
    t15 = t[t["yr"] >= 2015]
    cal = isotonic(t15["p"].to_numpy(), t15["y"].to_numpy())
    pc = apply_iso(cal, t15["p"].to_numpy())
    yy = t15["y"].to_numpy()
    bins = [0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 1.01]
    rep["calibration"] = [{"lo": lo, "hi": hi, "n": int(((pc >= lo) & (pc < hi)).sum()),
                           "pred_pct": float(pc[(pc >= lo) & (pc < hi)].mean() * 100) if ((pc >= lo) & (pc < hi)).any() else None,
                           "actual_pct": float(yy[(pc >= lo) & (pc < hi)].mean() * 100) if ((pc >= lo) & (pc < hi)).any() else None}
                          for lo, hi in zip(bins[:-1], bins[1:])]
    # final model on every labelled row
    pr = Prep().fit(F)
    w = fit_logit(pr.tf(F), df["y"].to_numpy().astype(float))
    g = rep["groups"]["2015plus"]
    g1 = rep["groups"]["2015plus_1B"]
    q = {k: float(np.quantile(pc, v)) for k, v in (("top1", 0.99), ("top5", 0.95), ("top10", 0.90))}
    model = {"trained": date.today().isoformat(), "sample": f"{df['d'].min()}..{df['d'].max()}", "rows": int(len(df)),
             "bankruptcies": int(df["y"].sum()), "features": FEATS, "prep": pr.dump(), "w": [float(x) for x in w],
             "cal": [[float(x) for x in cal[0]], [float(x) for x in cal[1]]],
             "eval_years": "2015-2025 (test years with at least four years of training history; 2013-14 had 1-2 years and "
                           "failed: AUC 0.50 / 0.29)",
             "oos": {"auc": g["p"]["auc"], "auc_z": g["negz"]["auc"], "auc_pts": g["pts"]["auc"], "auc_1b": g1["p"]["auc"],
                     "auc_all_years": rep["groups"]["all"]["p"]["auc"], "beats_z_years": g["model_beats_z_years"],
                     "top1_recall": g["p"]["top1"]["recall"], "top1_precision": g["p"]["top1"]["precision"],
                     "top5_recall": g["p"]["top5"]["recall"], "top5_precision": g["p"]["top5"]["precision"],
                     "top10_recall": g["p"]["top10"]["recall"], "top5_recall_z": g["negz"]["top5"]["recall"],
                     "base_rate_pct": float(t15["y"].mean() * 100), "n_bankrupt": int(t15["y"].sum()), "n_rows": int(len(t15))},
             "cutoffs": q,
             "calibration": rep["calibration"]}
    rep["coef"] = {f: round(float(c), 3) for f, c in zip(["const"] + FEATS, w)}
    json.dump(model, open(mout, "w", encoding="utf-8"), indent=1)
    json.dump(rep, open(rout, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rep.items() if k != "groups"}, ensure_ascii=False, indent=1)[:3000])
    for nm, g in rep["groups"].items():
        print("==", nm, "n", g["n"], "pos", g["pos"], "model beats Z'' in", g["model_beats_z_years"], "years")
        for sc in ("p", "negz", "pts"):
            x = g[sc]
            print(f"  {sc:5s} AUC {x['auc']:.3f} | top1% recall {x['top1']['recall']:.2f} prec {x['top1']['precision'] or 0:.3f}"
                  f" | top5% recall {x['top5']['recall']:.2f} prec {x['top5']['precision'] or 0:.3f} | top10% recall {x['top10']['recall']:.2f}")
        for Y, v in g["years"].items():
            print(f"    {Y} pos {v['n_pos']:3d}  model {v['model']:.2f}  Z'' {v['negz']:.2f}  pts {v['pts']:.2f}")


if __name__ == "__main__":
    main()
