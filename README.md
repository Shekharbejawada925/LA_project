# CausalEdu | Learning Analytics & Causal Inference

**Naive Pre/Post Lesson Estimates Overstate Learning Gains: Evidence from the CausalEdu A/B Tests**

An empirical learning analytics research project comparing observational check-in/check-out improvement statistics with randomized average treatment effects (ATEs) in mathematics education.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Research](https://img.shields.io/badge/Research-Learning%20Analytics-6f42c1)](#research-overview)
[![Methods](https://img.shields.io/badge/Methods-Causal%20Inference-0969da)](#methodology)
[![Status](https://img.shields.io/badge/Status-Academic%20Project-brightgreen)](#project-status)

> **ET601 Final Project · Indian Institute of Technology Bombay · October 2026**

## Research overview

Educational platforms often measure lesson effectiveness by comparing a student's answers before and after an instructional intervention. However, pre/post differences do not necessarily identify *causal* learning effects. This project evaluates how observational lesson-improvement measures differ from randomized treatment effects using the public [CausalEdu dataset](https://github.com/Eedi/CausalEdu).

### Research questions and hypotheses

- **H1 — Overestimation:** Do naive check-in/check-out estimates systematically exceed experimental ATEs?
- **H2 — Correcting estimates:** Can guessing correction and covariate-based models predict ATEs more accurately than naive estimates?
- **H3 — Heterogeneity:** Does the observational-to-experimental gap depend on student year group and lesson/question prerequisite distance?

## Key findings

Results reported in the submitted final report (88 experiments):

| Measure | p-version | k-version |
|---|---:|---:|
| Mean naive estimate | 0.34 | 0.26 |
| Mean randomized ATE | 0.057 | 0.056 |
| Mean gap (naive − ATE) | 0.283 | 0.203 |
| Experiments with positive gap | 92% | 90% |
| Naive estimator RMSE | 0.375 | 0.275 |
| Gradient boosting RMSE | 0.198 | 0.175 |

**Interpretation.** H1 is supported: naive pre/post improvement is markedly higher than randomized ATEs. For H2, adjusted models improve error compared with naive and guessing-corrected estimates, but do **not** demonstrate statistically clear improvement over the constant mean-ATE benchmark. For H3, year group is associated with the gap, while prerequisite distance shows no clear association.

**Important qualification:** Naive conditional success rates and randomized ATEs are different estimands. Therefore, the numerical gap should not be interpreted as solely causal bias.

## Methodology

1. Build learner-history, construct-difficulty, and lesson-related features from event logs.
2. Link observational lesson/question pairs to 88 randomized experiments.
3. Evaluate H1 using paired differences, confidence intervals, and hypothesis tests.
4. Compare raw estimates, analytical guessing correction, mean-ATE baseline, ridge regression, and gradient boosting with grouped cross-validation.
5. Analyze year-group and prerequisite-graph variation; examine prior-mastery profiles.

**Stack:** Python, pandas, NumPy, SciPy, scikit-learn, statsmodels, NetworkX, Matplotlib, ReportLab, PyMuPDF and Pillow.

## Project files

```text
LA_project/
├── README.md                  # Project description and reproduction guide
├── requirements.txt           # Python dependencies
├── .gitignore                 # Excludes large/raw/generated data
├── code/
│   ├── analysis.py            # H1–H3 experiments, evaluation, plots
│   └── build_report.py        # Generate the PDF from analysis outputs
├── final_report.pdf           # Academic research report
├── data/                      # Download separately; not tracked
├── results/                   # Generated tables, CSV, JSON
└── figures/                   # Generated figures
```

**Publication note:** The source scripts and report are part of the submission archive. Their presence in the repository should be verified before treating this clone as a complete runnable release.

## Reproduce the analysis

**Requirements:** Python 3.11 and the public CausalEdu data files.

```bash
git clone https://github.com/Shekharbejawada925/LA_project.git
cd LA_project

python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Download the original data from [Eedi/CausalEdu](https://github.com/Eedi/CausalEdu), and place the required CSV files under `data/`:

```text
data/
├── checkins_lessons_checkouts_training.csv
├── student_metadata.csv
├── construct_experiments_ates_test.csv
├── checkin_to_checkout.csv
└── construct_prerequisites_test.csv
```

Then, once the project source scripts are in place, run from the repository root:

```bash
python -I code/analysis.py data .
python -I code/build_report.py .
```

The analysis produces `results/` CSV/JSON outputs and `figures/` PNG visualizations; the report builder produces `final_report.pdf`. The analysis fixes its random seed for repeatable experiments. Exact results may still vary with dependency versions.

## Limitations

- Only 88 experiments; many are linked through shared constructs or lesson/question pairs.
- The randomized treatment effects have sampling uncertainty.
- Observational pre/post measures are not the same estimand as randomized treatment effects.
- The experimental file does not provide learner-level treatment records for estimating individual treatment effects.
- Year-group differences should be interpreted cautiously because lesson coverage varies between groups.

## Repository maintainer

**Bejawada Shekhar** · [@Shekharbejawada925](https://github.com/Shekharbejawada925)

This repository is maintained and presented by Bejawada Shekhar. The original academic report retains its own authorship and contribution credits.

## Data attribution

Dataset and associated research: [Eedi / CausalEdu](https://github.com/Eedi/CausalEdu). Please consult the original dataset repository for usage conditions, data documentation, and scholarly citation guidance.

## Project status

Academic research submission (October 2026). This repository is intended to preserve the report, reproducible analysis code and methodological documentation. It is not a production system. No license is granted by default; original dataset rights remain with their owners.
