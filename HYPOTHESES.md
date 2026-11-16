# Research Questions, Hypotheses and Conclusions

**Study:** Naive Pre/Post Lesson Estimates Overstate Learning Gains: Evidence from the CausalEdu A/B Tests

**Repository maintainer:** Bejawada Shekhar. This revised portfolio uses the sole-author credit confirmed by Bejawada Shekhar.

## Problem statement

Observed increases in correct answers after a lesson are easy to calculate but cannot, on their own, establish what would have happened without the lesson. CausalEdu enables a comparison between observational check-in/check-out summary rates and experimentally estimated effects.

**Research question:** How do observed pre/post gains differ from randomized lesson effects, and can experimental differences be predicted from lesson and learner-related attributes?

## H1 — Do naive lesson gains overstate randomized treatment effects?

**Hypothesis:** The published naive check-in/check-out rates (`p010_m` and `k010_m`) systematically exceed the corresponding A/B-test average treatment effects.

**Evidence:** Across 88 experiments, naive minus experimental ATE averaged **0.283** (95% CI 0.230–0.336) for p and **0.203** (95% CI 0.163–0.241) for k. Positive gaps occurred in **92%** and **90%** of experiments.

**Decision:** **Supported** as a descriptive gap between these measures. The two measures have different estimands, so the gap cannot be interpreted entirely as bias.

## H2 — Can covariate adjustment and guessing correction improve prediction?

**Hypothesis:** Adjustments accounting for guessing, prior history, year group, and related construct characteristics will reduce MAE/RMSE and improve correlation against experimental ATEs compared with naive rates.

| Cross-validated estimator | p RMSE | k RMSE |
|---|---:|---:|
| Naive (raw) | 0.375 | 0.275 |
| Analytic guessing correction | 0.292 | 0.220 |
| Mean-ATE baseline | 0.219 | 0.192 |
| Ridge | 0.227 | 0.188 |
| Gradient boosting | **0.198** | **0.175** |

**Decision:** **Partially supported.** Gradient boosting improves over the naive and guess-corrected rates, but the advantage over predicting the mean ATE is **not statistically clear**. For k, correlation did not improve over the naive estimate.

## H3 — Do effects and gaps differ by year and prerequisite distance?

**Hypothesis:** Learning-related estimates differ by student year group and graph distance between the lesson and the assessed construct.

| Year group | n | p naive–ATE gap |
|---|---:|---:|
| 5–6 | 7 | 0.40 |
| 7 | 42 | 0.22 |
| 8 | 25 | 0.40 |
| 9–10 | 14 | 0.21 |

The year-group terms were jointly significant for the gap (p = .009 for p and p < .001 for k); prerequisite distance showed no clear association (Spearman rho = −0.03, p = .78 for p-gap).

**Decision:** **Partially supported:** clear year-group pattern in these experiments, no clear prerequisite-distance pattern. Lesson assignment to year groups is not uniform, so year differences are not independently causal.

## Supporting descriptive analysis

Among observations with at least five earlier check-ins, prior-mastery terciles showed first-attempt accuracy of roughly **0.48**, **0.65**, and **0.78**, respectively. Learners' no-lesson retry accuracy after a wrong answer was **0.49**, **0.62**, and **0.69** across these groups, illustrating that second attempts may improve without a lesson.

## Limitations

- Only 88 randomized experiments; ATE measurement uncertainty is appreciable.
- Several experiments reuse the same observational lesson-question pair.
- Naive conditional success rates and randomized average treatment effects are different estimands.
- No learner-level randomized treatment records are available in the analyzed experiment file.
- Year-group results may reflect which lessons were offered to each group.
- This is exploratory academic analysis, **not** a validated causal-effect predictor for deployment.

**Source:** Original academic report provided in the uploaded submission archive.
