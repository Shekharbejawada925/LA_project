"""CausalEdu: naive pre/post lesson estimates vs. A/B-test ATEs.

Run:  python -I analysis.py <data_dir> <out_dir>
Writes results/*.csv|json and figures/*.png under <out_dir>.
"""
import ast
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path(sys.argv[1])
OUT = Path(sys.argv[2])
(OUT / "results").mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(610)
GUESS = 0.25  # four answer options per question

plt.rcParams.update({"font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "font.family": "serif"})

# ------------------------------------------------------------------ load
ev = pd.read_csv(DATA / "checkins_lessons_checkouts_training.csv", parse_dates=["Timestamp"])
stu = pd.read_csv(DATA / "student_metadata.csv")
ates = pd.read_csv(DATA / "construct_experiments_ates_test.csv")
c2c = pd.read_csv(DATA / "checkin_to_checkout.csv")
pre = pd.read_csv(DATA / "construct_prerequisites_test.csv")

# ------------------------------------------------------------------ learner history from the event log
ev = ev.merge(stu[["UserId", "YearGroup"]], on="UserId", how="left")
ev = ev.sort_values(["UserId", "Timestamp"])
first = ev[ev.Type == "Checkin"].copy()
g = first.groupby("UserId").IsCorrect
first["prior_n"] = g.cumcount()
first["prior_acc"] = g.transform(lambda s: s.shift().expanding().mean())
# learners with no history get the global mean (flagged by prior_n == 0)
first["prior_acc"] = first["prior_acc"].fillna(first.IsCorrect.mean())

# one row per (session, sequence) slot: check-in, retry, lesson, check-out
key = ["QuizSessionId", "QuestionSequence"]
w = first[key + ["UserId", "ConstructId", "YearGroup", "IsCorrect", "prior_acc", "prior_n"]].rename(
    columns={"IsCorrect": "ci"})
for typ, col in [("CheckinRetry", "retry"), ("Checkout", "co")]:
    w = w.merge(ev[ev.Type == typ][key + ["IsCorrect"]].rename(columns={"IsCorrect": col}),
                on=key, how="left")
w["lesson"] = w.set_index(key).index.isin(ev[ev.Type == "Lesson"].set_index(key).index)
w["co"] = w["co"].astype(float)

# ------------------------------------------------------------------ construct-level covariates (no A/B information)
cs = w.groupby("ConstructId").agg(
    q_ci_acc=("ci", "mean"), q_prior=("prior_acc", "mean"), q_n=("ci", "size"))
wrong = w[w.ci == 0]
cs["q_retry_rec"] = wrong.groupby("ConstructId").retry.mean()           # recovery with no lesson at all
cs["q_lesson_gain"] = wrong[wrong.lesson & wrong.co.notna()].groupby("ConstructId").co.mean()
cs["q_lesson_uptake"] = wrong.groupby("ConstructId").lesson.mean()
cy = w.groupby(["ConstructId", "YearGroup"]).agg(qy_ci_acc=("ci", "mean"), qy_n=("ci", "size")).reset_index()
glob = {c: cs[c].mean() for c in cs.columns}

# ------------------------------------------------------------------ prerequisite graph
G = nx.DiGraph()
for _, r in pre.dropna(subset=["PrerequisiteConstructIds"]).iterrows():
    for p in ast.literal_eval(r.PrerequisiteConstructIds.replace("{", "[").replace("}", "]")):
        G.add_edge(int(p), int(r.ConstructId))        # prerequisite -> dependent
U = G.to_undirected()
NOPATH = 7


def closeness(lesson, q):
    if lesson in G and q in G and nx.has_path(G, lesson, q):
        return min(nx.shortest_path_length(G, lesson, q), 6), 1
    if lesson in U and q in U and nx.has_path(U, lesson, q):
        return min(nx.shortest_path_length(U, lesson, q), 6), 0   # related but not a directed prerequisite
    return NOPATH, 0


# ------------------------------------------------------------------ analysis table (88 experiments)
d = ates.merge(c2c, left_on=["TreatmentLessonConstructId", "QuestionConstructId"],
               right_on=["LessonConstructId", "QuestionConstructId"], how="left", validate="m:1")
assert d.n01.notna().all() and len(d) == 88
d["naive_p"], d["naive_k"] = d.p010_m, d.k010_m
# one pair (2563 -> 2593) has n00 = n01 = 0, so p010_m is undefined; fall back to the k-version value there
d["naive_p"] = d.naive_p.fillna(d.naive_k)
d["bias_p"], d["bias_k"] = d.naive_p - d.ate_p_1__, d.naive_k - d.ate_k_1__
d["gc_p"] = (d.naive_p - GUESS) / (1 - GUESS)          # analytic guess correction
d["gc_k"] = (d.naive_k - GUESS) / (1 - GUESS)
d["n10_share"] = d.n10 / d.Count
d["n00_share"] = d.n00 / d.Count
d["pre_acc"] = (d.n10 + d.n11) / d.Count
d["post_acc"] = (d.n01 + d.n11) / d.Count
d["gain"] = d.post_acc - d.pre_acc                       # plain pre/post gain
d = d.join(d.apply(lambda r: pd.Series(closeness(r.LessonConstructId, r.QuestionConstructId),
                                       index=["dist", "directed"]), axis=1))
d = d.merge(cs.reset_index().rename(columns={"ConstructId": "QuestionConstructId"}),
            on="QuestionConstructId", how="left")
d = d.merge(cy.rename(columns={"ConstructId": "QuestionConstructId", "YearGroup": "Year"}),
            on=["QuestionConstructId", "Year"], how="left")
for c in list(cs.columns):
    d[c] = d[c].fillna(glob[c])
d["qy_ci_acc"] = d.qy_ci_acc.fillna(d.q_ci_acc)
d["qy_n"] = d.qy_n.fillna(0)
# lesson-type statistic: mean naive rate over the lesson's *other* pairs in the check-in/check-out file
c2c["naive_p"] = c2c.p010_m.fillna(c2c.k010_m)
ls = c2c.groupby("LessonConstructId").naive_p.agg(["sum", "count"])


def lesson_loo(r):
    s = ls.loc[r.TreatmentLessonConstructId]
    return (s["sum"] - r.naive_p) / (s["count"] - 1) if s["count"] > 1 else c2c.naive_p.mean()


d["lesson_mean_p"] = d.apply(lesson_loo, axis=1)
d["lesson_n_pairs"] = d.TreatmentLessonConstructId.map(ls["count"])
d["log_n"] = np.log(d.Count)
d["near"] = (d.dist <= 2).astype(int)
d.to_csv(OUT / "results" / "analysis_table.csv", index=False)

# ------------------------------------------------------------------ H1: the gap
H1 = []
for name, nv, at in [("p", "naive_p", "ate_p_1__"), ("k", "naive_k", "ate_k_1__")]:
    b = d[nv] - d[at]
    t = stats.ttest_1samp(b, 0)
    w_ = stats.wilcoxon(b)
    boot = [RNG.choice(b, len(b)).mean() for _ in range(5000)]
    H1.append(dict(estimator=name, naive_mean=d[nv].mean(), ate_mean=d[at].mean(), mean_bias=b.mean(),
                   ci_lo=np.percentile(boot, 2.5), ci_hi=np.percentile(boot, 97.5), t=t.statistic,
                   p_t=t.pvalue, p_wilcoxon=w_.pvalue, share_over=(b > 0).mean(),
                   cohens_dz=b.mean() / b.std(ddof=1), corr=np.corrcoef(d[nv], d[at])[0, 1],
                   spearman=stats.spearmanr(d[nv], d[at])[0]))
H1 = pd.DataFrame(H1)
H1.to_csv(OUT / "results" / "h1_gap.csv", index=False)

# ------------------------------------------------------------------ H2: corrected, covariate-adjusted estimator
FEATS = ["naive_p", "n10_share", "n00_share", "log_n", "Year", "dist", "directed", "qy_ci_acc",
         "q_ci_acc", "q_prior", "q_retry_rec", "q_lesson_gain", "q_lesson_uptake", "lesson_mean_p"]
FEATS_K = ["naive_k" if f == "naive_p" else f for f in FEATS]


def make_models():
    return {
        "Ridge (all features)": lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 30))),
        "Gradient boosting": lambda: GradientBoostingRegressor(n_estimators=120, max_depth=2, learning_rate=0.05,
                                                              subsample=0.8, random_state=0),
    }


def cv_predict(df, feats, target, model_fn, seed):
    """Grouped K-fold: all experiments on one question construct stay in the same fold."""
    rs = np.random.default_rng(seed)
    grp = df.QuestionConstructId.map(dict(zip(df.QuestionConstructId.unique(),
                                              rs.permutation(df.QuestionConstructId.nunique()))))
    pred = np.zeros(len(df))
    for tr, te in GroupKFold(n_splits=8).split(df, groups=grp):
        m = model_fn()
        m.fit(df.iloc[tr][feats], df.iloc[tr][target])
        pred[te] = m.predict(df.iloc[te][feats])
    return pred


def metrics(y, p):
    return dict(MAE=np.mean(np.abs(p - y)), RMSE=np.sqrt(np.mean((p - y) ** 2)),
                r=np.corrcoef(p, y)[0, 1] if np.std(p) > 0 else np.nan)


REPS = 30
rows, preds = [], {}
for tag, nv, feats, tgt in [("p", "naive_p", FEATS, "ate_p_1__"), ("k", "naive_k", FEATS_K, "ate_k_1__")]:
    y = d[tgt].values
    cand = {"Naive (raw)": [d[nv].values] * REPS,
            "Guess-corrected (analytic)": [d["gc_" + tag].values] * REPS,
            "Plain pre/post gain": [d.gain.values] * REPS}
    # constant baseline: training-fold mean of the ATEs
    cand["Mean-ATE baseline"] = [cv_predict(d, ["Year"], tgt,
                                            lambda: __import__("sklearn.dummy", fromlist=["x"]).DummyRegressor(), s)
                                 for s in range(REPS)]
    # guess-corrected + adjusted: linear recalibration of the corrected estimate only
    cand["Recalibrated correction"] = [cv_predict(d, ["gc_" + tag], tgt, make_models()["Ridge (all features)"], s)
                                       for s in range(REPS)]
    for mname, mf in make_models().items():
        cand[mname] = [cv_predict(d, feats, tgt, mf, s) for s in range(REPS)]
    for mname, plist in cand.items():
        ms = pd.DataFrame([metrics(y, p) for p in plist])
        rows.append(dict(estimator=tag, model=mname, MAE=ms.MAE.mean(), RMSE=ms.RMSE.mean(), r=ms.r.mean(),
                         MAE_sd=ms.MAE.std(), RMSE_sd=ms.RMSE.std()))
        preds[(tag, mname)] = (np.mean([np.abs(p - y) for p in plist], axis=0),
                                np.mean([(p - y) ** 2 for p in plist], axis=0))
H2 = pd.DataFrame(rows)
H2.to_csv(OUT / "results" / "h2_cv_metrics.csv", index=False)

# paired bootstrap over experiments: best adjusted model vs. naive (absolute error difference)
PB = []
for tag, tgt in [("p", "ate_p_1__"), ("k", "ate_k_1__")]:
    y = d[tgt].values
    sub = H2[(H2.estimator == tag) & ~H2.model.isin(["Naive (raw)", "Guess-corrected (analytic)", "Plain pre/post gain",
                                                      "Mean-ATE baseline"])]
    best = sub.sort_values("RMSE").model.iloc[0]
    for ref in ["Naive (raw)", "Guess-corrected (analytic)", "Mean-ATE baseline"]:
        (ab_a, ea), (ab_b, eb) = preds[(tag, best)], preds[(tag, ref)]   # per-experiment errors, mean over CV repeats
        idx = [RNG.integers(0, len(y), len(y)) for _ in range(5000)]
        dm = [ab_a[i].mean() - ab_b[i].mean() for i in idx]
        dr = [np.sqrt(ea[i].mean()) - np.sqrt(eb[i].mean()) for i in idx]
        PB.append(dict(estimator=tag, best=best, vs=ref, dMAE=np.mean(dm), dMAE_lo=np.percentile(dm, 2.5),
                       dMAE_hi=np.percentile(dm, 97.5), dRMSE=np.mean(dr), dRMSE_lo=np.percentile(dr, 2.5),
                       dRMSE_hi=np.percentile(dr, 97.5)))
pd.DataFrame(PB).to_csv(OUT / "results" / "h2_paired_bootstrap.csv", index=False)

# permutation importance-free summary: standardized ridge coefficients on full data (descriptive only)
sc = StandardScaler().fit(d[FEATS])
rg = RidgeCV(alphas=np.logspace(-2, 3, 30)).fit(sc.transform(d[FEATS]), d.ate_p_1__)
pd.Series(rg.coef_, index=FEATS).sort_values(key=abs, ascending=False).to_csv(OUT / "results" / "ridge_coefs_p.csv")

# ------------------------------------------------------------------ H3: who and which lessons
H3 = {}
d["yearband"] = pd.cut(d.Year, [0, 6, 7, 8, 11], labels=["5-6", "7", "8", "9-10"])
d["distband"] = pd.cut(d.dist, [0, 1, 2, 8], labels=["1", "2", "3+"])
for lab, col in [("year", "yearband"), ("closeness", "distband")]:
    t = d.groupby(col, observed=True).agg(n=("bias_p", "size"), naive=("naive_p", "mean"), ate=("ate_p_1__", "mean"),
                                         bias=("bias_p", "mean"), bias_sd=("bias_p", "std"),
                                         ate_k=("ate_k_1__", "mean"), bias_k=("bias_k", "mean"))
    t.to_csv(OUT / "results" / f"h3_by_{lab}.csv")
cl = {"groups": d.QuestionConstructId}
mods = {}
for tag in ["p", "k"]:
    for out, nm in [("bias_" + tag, "bias"), ("ate_" + tag + "_1__", "ate")]:
        f = f"{out} ~ C(yearband) + dist + directed + qy_ci_acc + log_n"
        m = smf.ols(f, d).fit(cov_type="cluster", cov_kwds=cl)
        mods[f"{tag}_{nm}"] = m
        H3[f"{tag}_{nm}"] = dict(r2=m.rsquared, n=int(m.nobs),
                                 coef=m.params.round(4).to_dict(), se=m.bse.round(4).to_dict(),
                                 p=m.pvalues.round(4).to_dict())
# joint test for year group, and for closeness
for key, m in mods.items():
    names = list(m.params.index)
    yr = [i for i, n_ in enumerate(names) if "yearband" in n_]
    R = np.zeros((len(yr), len(names)))
    for j, i in enumerate(yr):
        R[j, i] = 1
    H3[key]["wald_year_p"] = float(m.wald_test(R, scalar=True).pvalue)
rho = {n: dict(zip(["rho", "p"], stats.spearmanr(d.dist, d[n]))) for n in ["bias_p", "ate_p_1__", "bias_k", "ate_k_1__"]}
H3["spearman_dist"] = rho
json.dump(H3, open(OUT / "results" / "h3_models.json", "w"), indent=1, default=float)

# ------------------------------------------------------------------ supporting: prior-mastery profiles (descriptive)
w["mastery"] = pd.cut(w.prior_acc, [-.01, .55, .75, 1.01], labels=["low", "mid", "high"])
w["has_hist"] = w.prior_n >= 5
sp = w[w.has_hist].groupby("mastery", observed=True).apply(lambda x: pd.Series(dict(
    slots=len(x), checkin_acc=x.ci.mean(), wrong=(x.ci == 0).sum(),
    retry_rec=x[x.ci == 0].retry.mean(), lesson_rate=x[x.ci == 0].lesson.mean(),
    gain=x[(x.ci == 0) & x.lesson].co.mean(), co_acc_if_no_lesson=x[(x.ci == 0) & ~x.lesson].co.mean())))
sp.to_csv(OUT / "results" / "support_mastery.csv")
spy = w[w.has_hist & w.YearGroup.between(5, 10)].groupby("YearGroup").apply(lambda x: pd.Series(dict(
    slots=len(x), checkin_acc=x.ci.mean(), mean_prior=x.prior_acc.mean(),
    gain=x[(x.ci == 0) & x.lesson].co.mean())))
spy.to_csv(OUT / "results" / "support_year.csv")
summ = dict(events=len(ev), users=int(ev.UserId.nunique()), sessions=int(ev.QuizSessionId.nunique()),
            constructs=int(ev.ConstructId.nunique()), slots=len(w),
            retry_recovery=float(wrong.retry.mean()), n_experiments=len(d),
            n_lessons=int(d.TreatmentLessonConstructId.nunique()), n_questions=int(d.QuestionConstructId.nunique()),
            frac_near=float(d.near.mean()), frac_nopath=float((d.dist == NOPATH).mean()),
            frac_directed=float(d.directed.mean()), graph_edges=G.number_of_edges())
json.dump(summ, open(OUT / "results" / "summary.json", "w"), indent=1)

# ------------------------------------------------------------------ figures
fig, ax = plt.subplots(1, 2, figsize=(5.4, 2.6))
for a, (nv, at, ttl) in zip(ax, [("naive_p", "ate_p_1__", "p-version"), ("naive_k", "ate_k_1__", "k-version")]):
    a.scatter(d[nv], d[at], s=14, c="#2b5d8a", alpha=.75, edgecolor="none")
    a.plot([-.2, 1], [-.2, 1], ls="--", c="grey", lw=.8)
    a.axhline(0, c="k", lw=.4); a.axvline(GUESS, c="#b5483a", lw=.8, ls=":")
    a.set_xlabel(f"Naive estimate ({nv.split('_')[1]}010_m)"); a.set_ylabel("Experimental ATE"); a.set_title(ttl)
fig.tight_layout(); fig.savefig(OUT / "figures" / "fig1_naive_vs_ate.png"); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(5.4, 2.4))
for a, col, ttl in [(ax[0], "yearband", "Year group"), (ax[1], "distband", "Prerequisite distance")]:
    t = d.groupby(col, observed=True).bias_p.agg(["mean", "std", "size"])
    se = t["std"] / np.sqrt(t["size"])
    a.bar(range(len(t)), t["mean"], yerr=1.96 * se, color="#2b5d8a", capsize=3, width=.6)
    a.set_xticks(range(len(t))); a.set_xticklabels([f"{i}\n(n={n})" for i, n in zip(t.index, t["size"])])
    a.set_ylabel("Bias (naive - ATE)"); a.set_xlabel(ttl)
fig.tight_layout(); fig.savefig(OUT / "figures" / "fig2_bias_groups.png"); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(6.2, 2.5))
order = ["Naive (raw)", "Guess-corrected (analytic)", "Mean-ATE baseline", "Ridge (all features)", "Gradient boosting"]
for a, met in zip(ax, ["MAE", "RMSE"]):
    x = np.arange(len(order)); wd = .38
    for j, (tag, col) in enumerate([("p", "#2b5d8a"), ("k", "#c58b3a")]):
        v = [H2[(H2.estimator == tag) & (H2.model == o)][met].iloc[0] for o in order]
        a.bar(x + (j - .5) * wd, v, wd, color=col, label=f"{tag}-version")
    a.set_xticks(x); a.set_xticklabels(["Naive", "Guess\ncorr.", "Mean\nATE", "Ridge", "GBM"], fontsize=8.5)
    a.set_ylabel(met + " vs. ATE")
ax[0].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(OUT / "figures" / "fig3_cv_metrics.png"); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(5.4, 2.4))
ax[0].bar(np.arange(len(sp)) - .18, sp.gain, color="#2b5d8a", width=.36, label="check-out, after lesson")
ax[0].bar(np.arange(len(sp)) + .18, sp.retry_rec, color="#c58b3a", width=.36, label="check-in retry, no lesson")
ax[0].set_ylim(0, 0.95); ax[0].set_xticks(range(len(sp))); ax[0].set_xticklabels(sp.index); ax[0].set_xlabel("Prior mastery tercile")
ax[0].set_ylabel("P(correct | wrong check-in)"); ax[0].legend(frameon=False, fontsize=8)
ax[1].plot(spy.index, spy.mean_prior, marker="o", c="#2b5d8a", label="mean prior accuracy")
ax[1].plot(spy.index, spy.gain, marker="s", c="#c58b3a", label="check-out accuracy after lesson")
ax[1].set_ylim(0.4, 0.88); ax[1].set_xlabel("Year group"); ax[1].legend(frameon=False, fontsize=8, loc="upper center")
fig.tight_layout(); fig.savefig(OUT / "figures" / "fig4_prior_mastery.png"); plt.close(fig)

pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
print(json.dumps(summ, indent=1)); print(H1.round(3).T); print(H2.round(3))
print(pd.read_csv(OUT / "results" / "h2_paired_bootstrap.csv").round(3))
print(pd.read_csv(OUT / "results" / "h3_by_year.csv").round(3)); print(pd.read_csv(OUT / "results" / "h3_by_closeness.csv").round(3))
print(sp.round(3)); print(spy.round(3)); print(rho)
for k, v in H3.items():
    if k != "spearman_dist":
        print(k, round(v["r2"], 3), "wald_year_p", round(v["wald_year_p"], 3), {a: (b, v["p"][a]) for a, b in v["coef"].items()})
