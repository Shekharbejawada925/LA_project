"""Builds report/final_report.pdf from results/ and figures/. Run: python -I build_report.py <final_dir>"""
import json
import sys
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (PageBreak, CondPageBreak, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(sys.argv[1])
R, F = ROOT / "results", ROOT / "figures"
(ROOT / "report").mkdir(exist_ok=True)

h1 = pd.read_csv(R / "h1_gap.csv").set_index("estimator")
h2 = pd.read_csv(R / "h2_cv_metrics.csv")
pb = pd.read_csv(R / "h2_paired_bootstrap.csv")
yr = pd.read_csv(R / "h3_by_year.csv")
ds = pd.read_csv(R / "h3_by_closeness.csv")
sp = pd.read_csv(R / "support_mastery.csv").set_index("mastery")
sm = json.load(open(R / "summary.json"))
h3 = json.load(open(R / "h3_models.json"))

BASE = "Times-Roman"
body = ParagraphStyle("b", fontName=BASE, fontSize=10.5, leading=13.4, alignment=TA_JUSTIFY, spaceAfter=5)
h = ParagraphStyle("h", fontName="Times-Roman", fontSize=11, leading=14, alignment=TA_CENTER, spaceBefore=10, spaceAfter=5)
title = ParagraphStyle("t", fontName="Times-Bold", fontSize=16, leading=19.5, alignment=TA_CENTER, spaceAfter=7)
auth = ParagraphStyle("a", fontName=BASE, fontSize=10.5, leading=13.5, alignment=TA_CENTER)
cap = ParagraphStyle("c", fontName="Times-Roman", fontSize=10.5, leading=12.6, alignment=TA_JUSTIFY, spaceAfter=7)
ref = ParagraphStyle("r", fontName=BASE, fontSize=10.5, leading=12.6, leftIndent=18, firstLineIndent=-18, spaceAfter=2.5)
abst = ParagraphStyle("ab", parent=body, fontName="Times-Bold")
capT = ParagraphStyle("ct", parent=cap, alignment=TA_CENTER)
big = ParagraphStyle("big", fontName="Times-Bold", fontSize=24, leading=30, alignment=TA_CENTER, spaceAfter=18)
sub = ParagraphStyle("sub", fontName="Times-Roman", fontSize=13, leading=18, alignment=TA_CENTER, spaceAfter=4)
cell = ParagraphStyle("cl", fontName=BASE, fontSize=10, leading=11.5)


def P(t, s=body):
    if s is h:
        return KeepTogether([CondPageBreak(3.2 * cm), Paragraph(t.upper(), s)])
    if s is cap and t.startswith("<b>TABLE"):
        s = capT
    return Paragraph(t, s)


def f2(x):
    return f"{x:.2f}"


def pf(x, d=2):
    return f"{x:.{d}f}".lstrip("0")


def f3(x):
    return f"{x:.3f}"


def table(rows, widths, bold_rows=()):
    t = Table(rows, colWidths=widths, hAlign="CENTER")
    st = [("FONT", (0, 0), (-1, -1), BASE, 10.5), ("FONT", (0, 0), (-1, 0), "Times-Bold", 10.5),
          ("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black), ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
          ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
          ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    for r in bold_rows:
        st.append(("FONT", (0, r), (-1, r), "Times-Bold", 10.5))
    t.setStyle(TableStyle(st))
    return t


def fig(name, w=15.2):
    from PIL import Image as PI
    iw, ih = PI.open(F / name).size
    return Image(str(F / name), width=w * cm, height=w * cm * ih / iw)


def M(tag, model, col):
    return h2[(h2.estimator == tag) & (h2.model == model)][col].iloc[0]


def PB(tag, vs, col):
    return pb[(pb.estimator == tag) & (pb.vs == vs)][col].iloc[0]


def ci(tag, vs, m):
    return f"{PB(tag, vs, 'd' + m):+.3f} [{PB(tag, vs, 'd' + m + '_lo'):+.3f}, {PB(tag, vs, 'd' + m + '_hi'):+.3f}]"


TEAM = [("Bejawada Shekhar", "26m1032")]
S = []
S += [Spacer(1, 5.5 * cm), P("Naive Pre/Post Lesson Estimates Overstate Learning Gains: Evidence from the CausalEdu A/B Tests", big),
      Spacer(1, 1.2 * cm), P("<b>Author</b>", sub), Spacer(1, 0.2 * cm)]
for nm, rn in TEAM:
    S.append(P(f"{nm} &nbsp;&nbsp;({rn})", sub))
S += [Spacer(1, 1.5 * cm), P("ET601 Final Project Report", sub), P("29 October 2026", sub), PageBreak()]

S.append(P(
    "<i>Abstract</i>—Platforms often judge a lesson by comparing a learner's check-in answer with their check-out "
    "answer. We ask how far this naive pre/post statistic is from the effect measured in randomized A/B tests. "
    f"We use the CausalEdu data from Eedi, which has {sm['events']:,} quiz events from {sm['users']:,} students "
    f"and {sm['n_experiments']} experiments with randomized ground-truth effects. The naive estimates are too high "
    f"in {h1.loc['p','share_over']*100:.0f}% of the experiments, by {h1.loc['p','mean_bias']:.2f} on average for the "
    f"p-version and {h1.loc['k','mean_bias']:.2f} for the k-version. A correction for guessing removes part of this "
    f"gap, and a gradient boosting model that adds construct difficulty, year group, prerequisite distance and "
    f"lesson statistics lowers the error further (cross-validated RMSE {M('p','Naive (raw)','RMSE'):.3f} to "
    f"{M('p','Gradient boosting','RMSE'):.3f} for the p-version). However, a constant guess equal to the mean ATE "
    "is almost as good, so the improvement over that baseline is not statistically clear. The bias depends strongly "
    "on year group but we found no relation to prerequisite distance. Eighty-eight experiments are few, and we "
    "treat all findings as exploratory.", abst))
S.append(P("<i>Index Terms</i>—causal inference, A/B testing, pre/post estimates, guessing correction, learning analytics, CausalEdu.", abst))

# ---------------------------------------------------------------- 1
S.append(P("I. Introduction and Literature Review", h))
S.append(P(
    "Adaptive learning platforms constantly decide which lessons work. The easiest signal to compute is the "
    "change in a learner's answer to the same kind of question before and after a lesson. That signal is cheap but "
    "it is not a causal effect. Learners who answer wrongly at check-in are a selected group, so some of them would "
    "answer correctly the second time without any lesson (regression to the mean; Barnett et al., 2005). On a "
    "four-option multiple-choice item a learner who knows nothing is still right a quarter of the time, so a "
    "correct check-out answer does not always mean something was learned (Corbett &amp; Anderson, 1994; Baker et "
    "al., 2008). Learners also differ in what they already know, which affects both who takes a lesson and how much "
    "they gain from it."))
S.append(P(
    "Pre/post designs without a comparison group have been criticised since Campbell and Stanley (1963). "
    "Evidence from the training-program and advertising literatures shows that non-experimental estimates can "
    "differ substantially from randomized ones, and that the difference cannot be fixed by adjustment alone "
    "(LaLonde, 1986; Gordon et al., 2019). Rubin (1974) gives the potential-outcomes definition of the effect that "
    "the randomized comparison recovers. In education data, most work on this question is about knowledge tracing "
    "and prediction, and relatively few datasets let one check an observational estimate against a randomized one."))
S.append(P(
    "CausalEdu (Gong et al., 2023) is such a dataset. It comes from Eedi's maths platform (Wang et al., 2020) for "
    "students aged 11 to 16, and it contains both the raw check-in/lesson/check-out log and A/B tests that give "
    "ground-truth average treatment effects (ATEs). The authors also publish two pre/post statistics, p010_m and "
    "k010_m, which they use to flag prerequisite relations between constructs. These statistics are the kind of "
    "naive estimate a platform would compute, and they sit in the same data as the randomized effects. As far as "
    "we could tell from the dataset paper and the literature we searched, nobody has measured how far they are "
    "from the A/B effects, or whether the gap can be predicted. We found this gap by reading the dataset paper, "
    "which defines both quantities but never compares them. This is our research gap. We test the following "
    "hypotheses."))
S.append(P(
    "<b>H1 (the gap).</b> The naive check-in/check-out estimates (p010_m, k010_m) are biased upward against the "
    "88 experimental ATEs. <b>H2 (the fix).</b> An estimator that corrects for guessing and adjusts for covariates "
    "gives lower MAE and RMSE, and higher correlation with the ATEs, than the naive estimate in cross-validation "
    "across the 88 experiments. <b>H3 (which learners and lessons).</b> The size of the bias, and the effect "
    "itself, depend on year group and on how close the lesson construct is to the question construct in the "
    "prerequisite graph. As supporting analysis we describe prior-mastery profiles from the event log."))

# ---------------------------------------------------------------- 2
S.append(P("II. Methodology", h))
S.append(P(
    "<b>Data.</b> We used the training log (one row per question attempt or lesson, February to September 2022), "
    "student metadata (year group), the expert prerequisite file (3,277 constructs), the check-in/check-out counts "
    f"(183 lesson-question pairs) and the 88 A/B experiments. The experiments cover {sm['n_lessons']} lesson "
    f"constructs and {sm['n_questions']} question constructs, mostly in years 7 and 8. Every experiment matched a "
    "row of the check-in/check-out file. Several experiments share a pair (same lesson and question, different "
    "year or control), so the naive value is repeated across them. For one pair (2563 to 2593) nobody failed the "
    "check-in, so p010_m is undefined and we used its k-version value."))
S.append(P(
    "<b>Estimands.</b> For a pair with counts n00, n01, n10, n11 (check-in then check-out, 1 = correct), the "
    "naive estimates are p010_m = n01/(n01+n00) and k010_m = n01/(n00+n01+n10). The A/B effects are the "
    "difference in check-out accuracy between treatment and control groups, using the p-style rate "
    "(n01+n11)/(n00+n01+n11) or the k-style rate (n01+n11)/(n00+n01+n10+n11) in each arm. We keep the two "
    "versions separate throughout. The bias of an estimate is naive minus ATE."))
S.append(P(
    "<b>Corrections.</b> Three corrections were tried. (i) Guess correction: if a learner who has not learned the "
    "construct answers correctly with probability 0.25, the observed rate is p = q + 0.25(1 - q), so we use "
    "q = (p - 0.25)/0.75. (ii) A covariate-adjusted model that predicts the ATE from the naive value plus the "
    "features below, fitted with ridge regression or gradient boosting (Hoerl &amp; Kennard, 1970; Friedman, "
    "2001; scikit-learn, Pedregosa et al., 2011). (iii) Two reference points: a plain pre/post gain "
    "(check-out accuracy minus check-in accuracy) and a constant equal to the mean ATE in the training folds."))
S.append(P(
    "<b>Features.</b> All features come from information that exists before or independently of the A/B "
    "outcome. From the pair counts: share of n10 (a guessing signal), share of n00, and log of the sample size. "
    "From the event log, for the question construct: first-attempt check-in accuracy (overall and in the year "
    "group of the experiment, a difficulty measure), the mean prior accuracy of the learners who met it (learner "
    "history, computed from each learner's earlier check-ins only), the recovery rate on the check-in retry among "
    "wrong first attempts (a regression-to-the-mean proxy, since no lesson comes between the two attempts), "
    "the post-lesson accuracy and lesson uptake rate. From the prerequisite graph (6,740 edges, built with "
    "networkx): the shortest directed path from the lesson to the question construct, capped at 6, and a flag "
    "for a directed prerequisite path. Lesson-type statistic: the mean naive rate of the same lesson in its other "
    "pairs, leaving the current pair out. Year group is also a feature."))
S.append(P(
    "<b>Validation.</b> Experiments on the same question construct are not independent, so we used grouped "
    "8-fold cross-validation where all experiments of a question construct stay in one fold, repeated 30 times "
    "with different group shuffles. We report MAE, RMSE and Pearson r against the ATE. Differences between "
    "estimators were assessed with a paired bootstrap over experiments (5,000 resamples; Efron &amp; Tibshirani, "
    "1993). For H1 we used a one-sample t test and a Wilcoxon test on the bias. For H3 we regressed bias and ATE "
    "on year-group band, prerequisite distance, directed-path flag, year-specific difficulty and log sample size, "
    "with standard errors clustered by question construct (Cameron &amp; Miller, 2015). The analysis was done in "
    "Python with pandas (McKinney, 2010), SciPy (Virtanen et al., 2020), statsmodels (Seabold &amp; Perktold, 2010), "
    "NetworkX (Hagberg et al., 2008) and matplotlib (Hunter, 2007); the code is in the submitted archive."))

# ---------------------------------------------------------------- 3
S.append(P("III. Results", h))
t1 = [["", "Naive", "ATE", "Bias [95% CI]", "t", "% over", "r"]]
for k in ["p", "k"]:
    r = h1.loc[k]
    t1.append([f"{k}-version", f2(r.naive_mean), f3(r.ate_mean), f"{r.mean_bias:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]",
               f"{r.t:.1f}", f"{r.share_over*100:.0f}", f2(r['corr'])])
S.append(P(
    "<b>H1.</b> Table I and Fig. 1 show the gap. The mean naive p-estimate is "
    f"{h1.loc['p','naive_mean']:.2f} while the mean ATE is {h1.loc['p','ate_mean']:.3f}. For the k-version the "
    f"values are {h1.loc['k','naive_mean']:.2f} and {h1.loc['k','ate_mean']:.3f}. The bias is positive in "
    f"{h1.loc['p','share_over']*100:.0f}% and {h1.loc['k','share_over']*100:.0f}% of experiments (t = "
    f"{h1.loc['p','t']:.1f} and {h1.loc['k','t']:.1f}, Wilcoxon p &lt; .001 for both). The standardized size "
    f"of the bias is large (d<sub>z</sub> = {h1.loc['p','cohens_dz']:.2f} and {h1.loc['k','cohens_dz']:.2f}). "
    "The naive value also ranks experiments poorly: Spearman correlations with the ATE are only "
    f"{h1.loc['p','spearman']:.2f} and {h1.loc['k','spearman']:.2f}. H1 is supported. Note that part of this gap "
    "is expected, because p010_m conditions on learners who failed the check-in and the ATE does not (see "
    "Section IV)."))
S.append(KeepTogether([P("<b>TABLE I.</b> Naive estimates against experimental ATEs (n = 88). % over = share of "
                         "experiments where naive &gt; ATE; r = Pearson correlation of naive with ATE.", cap),
                       table(t1, [2.4*cm, 1.7*cm, 1.7*cm, 4.6*cm, 1.4*cm, 1.7*cm, 1.4*cm])]))
S.append(KeepTogether([Spacer(1, 4),
                       fig("fig1_naive_vs_ate.png", 13.0),
                       P("<b>Fig. 1.</b> Naive estimate against ATE. Dashed line: equality; dotted line: 0.25 "
                         "guessing level. Almost all points lie to the right of the dashed line.", cap)]))

rows = [["Estimator", "MAE", "RMSE", "r", "MAE", "RMSE", "r"]]
order = ["Naive (raw)", "Guess-corrected (analytic)", "Plain pre/post gain", "Mean-ATE baseline",
         "Ridge (all features)", "Gradient boosting"]
for o in order:
    row = [o]
    for tag in ["p", "k"]:
        rr = "n/a" if o == "Mean-ATE baseline" else f2(M(tag, o, "r"))
        row += [f3(M(tag, o, "MAE")), f3(M(tag, o, "RMSE")), rr]
    rows.append(row)
S.append(P(
    "<b>H2.</b> Table II and Fig. 2 give the cross-validated errors. The guess correction alone lowers the p-version RMSE "
    f"from {M('p','Naive (raw)','RMSE'):.3f} to {M('p','Guess-corrected (analytic)','RMSE'):.3f}, but it cannot "
    "change the correlation because it is a linear rescaling. The gradient boosting model with covariates has the "
    f"lowest error for both versions (RMSE {M('p','Gradient boosting','RMSE'):.3f} and "
    f"{M('k','Gradient boosting','RMSE'):.3f}) and the highest p-version correlation "
    f"({M('p','Gradient boosting','r'):.2f}, against {M('p','Naive (raw)','r'):.2f} for the naive estimate). "
    "Against the naive estimate the paired bootstrap difference in MAE is "
    f"{ci('p','Naive (raw)','MAE')} for the p-version and {ci('k','Naive (raw)','MAE')} for the k-version; "
    f"against the guess-corrected estimate it is {ci('p','Guess-corrected (analytic)','MAE')} and "
    f"{ci('k','Guess-corrected (analytic)','MAE')}. For the k-version the correlation did not improve "
    f"({M('k','Gradient boosting','r'):.2f} against {M('k','Naive (raw)','r'):.2f}). The ridge model did not "
    "beat the constant baseline."))
S.append(P(
    "The result that needs the most care is the constant baseline. Predicting the training-fold mean ATE "
    f"gives an RMSE of {M('p','Mean-ATE baseline','RMSE'):.3f} (p) and {M('k','Mean-ATE baseline','RMSE'):.3f} (k). "
    "Gradient boosting is below this, but the paired bootstrap interval for the RMSE difference includes zero "
    f"({ci('p','Mean-ATE baseline','RMSE')} and {ci('k','Mean-ATE baseline','RMSE')}). So H2 is supported against "
    "the naive and guess-corrected estimates, and only weakly, with no clear significance, against a constant. "
    "A rough noise floor helps here: with about 34 and 40 learners per arm, the sampling standard error of one "
    "ATE is near 0.12, so even a perfect estimator would show an MAE of about 0.09 against the observed ATEs."))
S.append(KeepTogether([
    P("<b>TABLE II.</b> Grouped cross-validation results against the ATE (mean of 30 repeats). Left block: "
      "p-version; right block: k-version. r is undefined for the constant baseline because its out-of-fold "
      "predictions carry no information about the held-out value.", cap),
    table(rows, [5.2*cm, 1.55*cm, 1.55*cm, 1.4*cm, 1.55*cm, 1.55*cm, 1.4*cm], bold_rows=(6,))]))
S.append(KeepTogether([Spacer(1, 4), fig("fig3_cv_metrics.png", 14.6),
    P("<b>Fig. 2.</b> Cross-validated MAE and RMSE by estimator.", cap)]))

yrows = [["Year group", "n", "Naive p", "ATE p", "Bias p", "ATE k", "Bias k"]]
for _, r in yr.iterrows():
    yrows.append([r.yearband, int(r.n), f2(r.naive), f"{r.ate:+.3f}", f2(r.bias), f"{r.ate_k:+.3f}", f2(r.bias_k)])
drows = [["Prerequisite distance", "n", "Naive p", "ATE p", "Bias p", "ATE k", "Bias k"]]
for _, r in ds.iterrows():
    drows.append([r.distband, int(r.n), f2(r.naive), f"{r.ate:+.3f}", f2(r.bias), f"{r.ate_k:+.3f}", f2(r.bias_k)])
rho = h3["spearman_dist"]
S.append(P(
    "<b>H3.</b> Table III and Fig. 3 split the results by year group and by prerequisite distance. The naive "
    "estimate is about the same in every year group (0.30 to 0.36), but the ATE is not. It is near 0.09 to 0.12 in "
    "years 7 and 9-10 and slightly negative in years 5-6 and 8, so the bias is about 0.40 in years 5-6 and 8 and "
    f"about 0.21 in years 7 and 9-10. In the clustered regressions the year-group terms are jointly significant for "
    f"the bias (Wald p = {pf(h3['p_bias']['wald_year_p'], 3)} for the p-version, p &lt; .001 for the k-version) and for "
    f"the effect itself (p = {pf(h3['p_ate']['wald_year_p'], 3)} and p &lt; .001). Prerequisite distance shows no clear "
    f"relation: Spearman rho with the bias is {rho['bias_p']['rho']:.2f} (p = {pf(rho['bias_p']['p'])}) and with "
    f"the ATE {rho['ate_p_1__']['rho']:.2f} (p = {pf(rho['ate_p_1__']['p'])}), and its regression coefficients "
    "are not significant. H3 is therefore "
    "supported for year group and not supported for prerequisite closeness. The year pattern should be read with "
    "care, because each lesson was run in only some year groups."))
S.append(KeepTogether([
    P("<b>TABLE III.</b> Bias and ATE by year group (top) and prerequisite distance (bottom; shortest path from "
      "lesson to question construct, 3+ = three or more steps). Bias = naive minus ATE.", cap),
    table(yrows, [3.6*cm, 1.2*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm]), Spacer(1, 6),
    table(drows, [3.6*cm, 1.2*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm])]))
S.append(KeepTogether([Spacer(1, 6), fig("fig2_bias_groups.png", 12.6),
    P("<b>Fig. 3.</b> Mean bias of the p-version (naive minus ATE) with 95% intervals, by year group band and "
      "by prerequisite distance.", cap)]))
S.append(P(
    "<b>Supporting analysis.</b> (Fig. 4.) To describe who the learners are, we computed each learner's prior mastery as "
    "their accuracy on earlier first-attempt check-ins (only slots with at least five earlier check-ins, about "
    f"{int(sp.slots.sum()):,} slots). First-attempt check-in accuracy was "
    f"{sp.loc['low','checkin_acc']:.2f}, {sp.loc['mid','checkin_acc']:.2f} and {sp.loc['high','checkin_acc']:.2f} "
    "in the low, middle and high terciles. After a wrong check-in answer, learners got the retried question "
    f"right {sp.loc['low','retry_rec']:.2f}, {sp.loc['mid','retry_rec']:.2f} and {sp.loc['high','retry_rec']:.2f} "
    f"of the time with no lesson at all, and overall {sm['retry_recovery']:.2f}, far above the 0.25 guessing level. "
    "This is what we would expect if elimination and regression to the mean matter, and it is the reason we "
    "added the retry rate as a feature. Lesson uptake after a wrong answer fell as mastery rose "
    f"({sp.loc['low','lesson_rate']:.2f}, {sp.loc['mid','lesson_rate']:.2f}, {sp.loc['high','lesson_rate']:.2f}), "
    "so the learners who take lessons are not a random subset. These figures are descriptive only and do not "
    "estimate a lesson effect."))
S.append(KeepTogether([fig("fig4_prior_mastery.png", 13.2),
                       P("<b>Fig. 4.</b> Left: probability of a correct answer after a wrong check-in, by prior "
                         "mastery tercile, for the check-out after a lesson and for the check-in retry (no lesson). "
                         "Right: mean prior accuracy and post-lesson check-out accuracy by year group.", cap)]))

# ---------------------------------------------------------------- 4
S.append(P("IV. Discussion and Limitations", h))
S.append(P(
    "The main finding is that the naive pre/post statistics tell a very different story from the randomized "
    "experiments. An average naive value of 0.34 would suggest that a third of learners who failed the check-in "
    "learn from the lesson, whereas the average randomized effect is under six percentage points. A large part of "
    "the gap is probably guessing and retesting: the retry data show that about 59% of wrong first attempts become "
    "right with no lesson, and the 0.25 guess correction already removes about a third of the MAE. The remaining "
    "bias is not constant. It changes with year group, and the naive value cannot see this because it hardly "
    "moves across year groups. In practice this means that a platform ranking lessons by raw pre/post gain would "
    "mostly rank them by how often learners get a question right the second time."))
S.append(P(
    "On H2 our evidence is mixed and we want to state this clearly. The adjusted model clearly beats the naive and "
    "the guess-corrected estimate on MAE and RMSE, but a constant prediction is nearly as accurate, and the "
    "improvement over it is inside the bootstrap noise. Also, the k-version correlation did not improve. So "
    "most of the accuracy gain comes from shrinking the naive estimate toward a small average effect rather than "
    "from learning which lessons are better. A correlation of 0.4 for the p-version suggests that the features "
    "carry some signal, but with 88 experiments we cannot say which features matter, and the ridge coefficients "
    "were small. For H3, the year-group dependence agrees with the idea that the same lesson works "
    "differently for different learners, but the prerequisite-distance result is null. One reason may be that "
    "the experimenters chose lessons that experts already considered related, so there is little variation in "
    "distance (78% of experiments are within two steps)."))
S.append(P(
    "<b>Limitations.</b> (1) The sample is small: 88 experiments from 15 lessons and 75 questions, and the "
    "experimental ATEs are noisy (arms of roughly 30 to 40 learners). Our intervals treat experiments as "
    "independent, although some share a naive value and a lesson, so they are probably too narrow. (2) The naive "
    "statistic and the ATE are not the same estimand. p010_m is a rate among learners who failed the check-in, "
    "while the ATE is a treatment-control difference, so part of the 'bias' is a difference in definition and not "
    "only confounding. We did not separate these two parts. (3) The check-in/check-out counts are pooled over year "
    "groups, so year-group differences in bias come from the ATEs alone. (4) The A/B data has no learner-level "
    "rows, so we could not estimate individual-level treatment effects or check the learner-history covariates "
    "inside an experiment; learner history enters only as construct-level averages. (5) Prerequisite closeness "
    "relies on expert opinion, which the dataset authors say should give way to A/B results where they disagree. "
    "(6) Year-group effects are confounded with which lessons were tested in which year. (7) The training log and "
    "the experiments come from the same platform, but we do not know whether they overlap in time, and the "
    "results may not carry over to other subjects or platforms. We did not tune the models beyond fixed settings, "
    "to avoid overfitting to 88 points. These results should be seen as a first measurement of the gap, not a "
    "ready-made correction for production use."))

S.append(P("V. Author Contributions", h))
S.append(P("<b>Bejawada Shekhar (26m1032):</b> Project conception, research design, literature review, data processing, feature engineering, H1-H3 hypothesis testing, guessing correction, prediction models, cross-validation, visualizations, interpretation and report preparation."))
# ---------------------------------------------------------------- refs
S.append(P("References", h))
refs = [
    "Baker, R. S. J. d., Corbett, A. T., &amp; Aleven, V. (2008). More accurate student modeling through contextual "
    "estimation of slip and guess probabilities in Bayesian knowledge tracing. In <i>Intelligent Tutoring Systems</i> "
    "(pp. 406–415). Springer. https://doi.org/10.1007/978-3-540-69132-7_44",
    "Barnett, A. G., van der Pols, J. C., &amp; Dobson, A. J. (2005). Regression to the mean: What it is and how to "
    "deal with it. <i>International Journal of Epidemiology, 34</i>(1), 215–220. https://doi.org/10.1093/ije/dyh299",
    "Cameron, A. C., &amp; Miller, D. L. (2015). A practitioner's guide to cluster-robust inference. <i>Journal of "
    "Human Resources, 50</i>(2), 317–372. https://doi.org/10.3368/jhr.50.2.317",
    "Campbell, D. T., &amp; Stanley, J. C. (1963). <i>Experimental and quasi-experimental designs for research</i>. "
    "Rand McNally.",
    "Corbett, A. T., &amp; Anderson, J. R. (1994). Knowledge tracing: Modeling the acquisition of procedural "
    "knowledge. <i>User Modeling and User-Adapted Interaction, 4</i>(4), 253–278. https://doi.org/10.1007/BF01099821",
    "Efron, B., &amp; Tibshirani, R. J. (1993). <i>An introduction to the bootstrap</i>. Chapman &amp; Hall.",
    "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. <i>The Annals of "
    "Statistics, 29</i>(5), 1189–1232. https://doi.org/10.1214/aos/1013203451",
    "Gong, W., Smith, D., Wang, Z., Barton, C., Woodhead, S., Pawlowski, N., Jennings, J., &amp; Zhang, C. (2023). "
    "CausalEdu: A real-world education dataset for temporal causal discovery and inference. <i>CLeaR 2023 Datasets "
    "Track</i>. https://github.com/Eedi/CausalEdu",
    "Gordon, B. R., Zettelmeyer, F., Bhargava, N., &amp; Chapsky, D. (2019). A comparison of approaches to "
    "advertising measurement: Evidence from big field experiments at Facebook. <i>Marketing Science, 38</i>(2), "
    "193–225. https://doi.org/10.1287/mksc.2018.1135",
    "Hagberg, A. A., Schult, D. A., &amp; Swart, P. J. (2008). Exploring network structure, dynamics, and function "
    "using NetworkX. In G. Varoquaux, T. Vaught, &amp; J. Millman (Eds.), <i>Proceedings of the 7th Python in Science "
    "Conference</i> (pp. 11–15).",
    "Hoerl, A. E., &amp; Kennard, R. W. (1970). Ridge regression: Biased estimation for nonorthogonal problems. "
    "<i>Technometrics, 12</i>(1), 55–67. https://doi.org/10.1080/00401706.1970.10488634",
    "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. <i>Computing in Science &amp; Engineering, 9</i>(3), "
    "90–95. https://doi.org/10.1109/MCSE.2007.55",
    "LaLonde, R. J. (1986). Evaluating the econometric evaluations of training programs with experimental data. "
    "<i>The American Economic Review, 76</i>(4), 604–620.",
    "McKinney, W. (2010). Data structures for statistical computing in Python. In S. van der Walt &amp; J. Millman "
    "(Eds.), <i>Proceedings of the 9th Python in Science Conference</i> (pp. 56–61).",
    "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... Duchesnay, E. (2011). "
    "Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research, 12</i>, 2825–2830.",
    "Rubin, D. B. (1974). Estimating causal effects of treatments in randomized and nonrandomized studies. "
    "<i>Journal of Educational Psychology, 66</i>(5), 688–701. https://doi.org/10.1037/h0037350",
    "Seabold, S., &amp; Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. In S. van der "
    "Walt &amp; J. Millman (Eds.), <i>Proceedings of the 9th Python in Science Conference</i> (pp. 92–96).",
    "Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T., Cournapeau, D., ... SciPy 1.0 Contributors. "
    "(2020). SciPy 1.0: Fundamental algorithms for scientific computing in Python. <i>Nature Methods, 17</i>(3), "
    "261–272. https://doi.org/10.1038/s41592-019-0686-2",
    "Wang, Z., Lamb, A., Saveliev, E., Cameron, P., Zaykov, Y., Hernandez-Lobato, J. M., Turner, R. E., Baraniuk, "
    "R. G., Barton, C., Peyton Jones, S., Woodhead, S., &amp; Zhang, C. (2020). <i>Diagnostic questions: The NeurIPS "
    "2020 education challenge</i> (arXiv:2007.12061). arXiv. https://arxiv.org/abs/2007.12061",
]
S += [P(r, ref) for r in refs]


def footer(c, d):
    c.saveState()
    c.setFont(BASE, 10.5)
    c.drawCentredString(A4[0] / 2, 1.1 * cm, str(d.page))
    c.restoreState()


doc = SimpleDocTemplate(str(ROOT / "report" / "final_report.pdf"), pagesize=A4, leftMargin=2.1 * cm,
                        rightMargin=2.1 * cm, topMargin=1.9 * cm, bottomMargin=1.9 * cm,
                        title="Naive Pre/Post Lesson Estimates Overstate Learning Gains", author="Bejawada Shekhar")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
import pymupdf
print("pages:", len(pymupdf.open(ROOT / "report" / "final_report.pdf")))
